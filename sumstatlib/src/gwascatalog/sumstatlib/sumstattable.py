from __future__ import annotations

import csv
import gzip
import logging
from functools import cached_property
from pathlib import Path
from typing import IO, TYPE_CHECKING, Literal, NamedTuple, TypedDict

from gwascatalog.sumstatlib._pydantic import ValidationError

if TYPE_CHECKING:
    from collections.abc import Generator

    from gwascatalog.sumstatlib import CNVSumstatModel, GeneSumstatModel, GenomeAssembly

logger = logging.getLogger(__name__)


def _is_gzip(path: Path) -> bool:
    """Check whether path starts with the gzip magic bytes."""
    with path.open("rb") as f:
        return f.read(2) == b"\x1f\x8b"


class SumstatConfig(TypedDict):
    """Runtime configuration for validating summary stats"""

    allow_zero_p_values: bool
    assembly: GenomeAssembly
    primary_effect_size: Literal["beta", "odds_ratio", "hazard_ratio", "z_score"] | None


class SumstatError(TypedDict):
    """A parsed pydantic ValidationError"""

    row: int
    loc: int | None
    msg: str


class ValidatedRow(NamedTuple):
    """Lightweight progress info yielded per row during writing.

    Attributes:
        row_number: Zero-based index of the row in the data file (excluding header).
        is_valid: Whether the row passed Pydantic validation.
    """

    row_number: int
    is_valid: bool


class SumstatTable:
    MAX_ERRORS = 100

    def __init__(
        self,
        data_model: type[CNVSumstatModel | GeneSumstatModel],
        input_path: Path,
        config: SumstatConfig,
        min_records: int | None = None,
    ):
        self._data_model = data_model
        self._path = Path(input_path)
        self._config = config
        self._errors: list[SumstatError] = []

        if not self._path.exists():
            raise FileNotFoundError(self._path)

        if min_records is None:
            self._min_records = self._data_model.MIN_RECORDS
        else:
            self._min_records = min_records

        n_rows = self.n_rows
        if self._min_records is not None and n_rows < self._min_records:
            raise ValueError(f"Not enough rows in file: {n_rows=} {self._min_records=}")

        # Validate first row to check column structure — fail fast on bad columns
        _ = self.output_fieldnames

    def _open_sumstat(self) -> IO[str]:
        if _is_gzip(self._path):
            return gzip.open(self._path, "rt", encoding="utf-8")
        return self._path.open(mode="rt", encoding="utf-8")

    def parse_csv(self, sample_size: int = 4096) -> Generator[dict]:
        """Automatically detect CSV delimiter and yield each row as a dict"""
        with self._open_sumstat() as f:
            sample = f.read(sample_size)
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(sample, delimiters=",\t;| ")

            if not sniffer.has_header(sample):
                raise ValueError("file doesn't appear to contain a header")

            f.seek(0)  # reset to start of the file
            reader = csv.DictReader(f, dialect=dialect)
            yield from reader

    @cached_property
    def input_fieldnames(self) -> frozenset[str]:
        row = next(self.parse_csv())
        return frozenset(row.keys())

    @cached_property
    def output_fieldnames(self) -> list[str]:
        """Get output CSV column names in a standardised order.

        Validates the first data row to resolve aliases to canonical field
        names and determine which optional fields are present.

        Order: known fields sorted by FIELD_MAP index, then extra columns.
        Only non-null fields are included.

        Raises:
            ValidationError: If the first row fails validation, indicating
                an invalid column set (e.g. missing required columns).
        """
        first_row = next(self.parse_csv())
        try:
            instance = self._data_model.model_validate(first_row, context=self._config)
        except ValidationError as e:
            logger.critical(f"First row of {self._path.name} failed validation")
            logger.critical(f"{ValidationError}")
            msg = (
                f"The first row of {self._path.name} failed validation. "
                "This usually means the file has missing or incorrectly "
                "named columns. Valid column names include: "
                f"{self.data_model.VALID_FIELD_NAMES}"
            )
            raise ValueError(msg) from e

        present = list(instance.model_dump(exclude_none=True).keys())
        field_map = self._data_model.FIELD_MAP

        # get a list fields sorted by their field map index
        known = sorted(
            [(name, field_map[name]) for name in present if name in field_map],
            key=lambda pair: pair[1],
        )
        # user-specified fields
        extras = [name for name in present if name not in field_map]

        return [name for name, _ in known] + extras

    @property
    def has_validation_failed(self) -> bool:
        """Have any ValidationErrors been raised?"""
        return len(self._errors) > 0

    @cached_property
    def n_rows(self) -> int:
        with self._open_sumstat() as f:
            next(f, None)  # skip header
            return sum(1 for _ in f)

    def validate_rows(self) -> Generator[dict]:
        """Validate all rows, storing errors in self._errors and yielding validated
        rows.
        """
        for i, row in enumerate(self.parse_csv()):
            try:
                validated = self._data_model.model_validate(
                    row, context=self._config
                ).model_dump()
            except ValidationError as exc:
                for error in exc.errors():
                    location = int(error["loc"][0])
                    self._errors.append(
                        SumstatError(row=i, loc=location, msg=error["msg"])
                    )

                if len(self._errors) >= self.MAX_ERRORS:
                    logger.critical(
                        f"Stopped validation after {self.MAX_ERRORS} errors"
                    )
                    break
            else:
                yield validated

    @property
    def errors(self) -> list[SumstatError]:
        """Return all row errors encountered"""
        return self._errors

    def add_error(self, error: SumstatError) -> None:
        self._errors.append(error)

    def open_writer(
        self,
        output_path: Path,
        *,
        compress: bool | None = None,
    ) -> SumstatWriter:
        """Create a writer for streaming validated output."""
        return SumstatWriter(self, output_path, compress=compress)

    @property
    def data_model(self) -> type[CNVSumstatModel | GeneSumstatModel]:
        """The Pydantic data model used for validation"""
        return self._data_model

    @property
    def config(self):
        return self._config


class SumstatWriter:
    """Streaming writer for validated summary statistics.

    Validates each row against the data model. Guidelines for consumers:

    - Iterate to process rows
    - Iteration yields a ValidatedRow for every row which includes validation status
    - If you want to report progress, add a check inside the iteration (e.g. every
        10,000 rows send a message or print)
    - If you don't want to report progress, you can use the .run() convenience function

    IMPORTANT: The writer stops early after ``MAX_ERRORS`` (fail-fast-ish). Enough
    errors are collected for a single review pass without processing the entire file.
    """

    def __init__(
        self,
        table: SumstatTable,
        output_path: Path,
        *,
        compress: bool | None = None,
    ) -> None:
        self._table = table
        self._output_path = Path(output_path)
        self._compress = (
            compress if compress is not None else self._output_path.suffix == ".gz"
        )
        self._rows_processed = 0
        self._valid_count = 0
        self._sort_buffer: list[dict] = []

    def __iter__(self) -> Generator[ValidatedRow]:
        """Validate each row, buffer valid ones, sort by genomic position, write.

        Rows are sorted by ``(chromosome, base_pair_start)`` when those fields
        are present. Rows where either field is absent sort to the end.
        The output file is written only when all rows pass validation.

        Yields:
            A :class:`ValidatedRow` for every row in the input file.
        """
        fieldset = set(self._table.output_fieldnames)
        for i, row in enumerate(self._table.parse_csv()):
            self._rows_processed = i + 1
            try:
                instance = self._table.data_model.model_validate(
                    row, context=self._table.config
                )
            except ValidationError as exc:
                for error in exc.errors():
                    try:
                        location = int(error["loc"][0])
                    except IndexError:
                        location = None
                    self._table.add_error(
                        SumstatError(row=i, loc=location, msg=error["msg"])
                    )
                yield ValidatedRow(row_number=i, is_valid=False)

                if len(self._table.errors) >= self._table.MAX_ERRORS:
                    logger.critical(
                        f"Stopped validation after {self._table.MAX_ERRORS} errors"
                    )
                    break
            else:
                self._valid_count += 1
                self._sort_buffer.append(instance.model_dump(include=fieldset))
                yield ValidatedRow(row_number=i, is_valid=True)

        if not self.has_validation_failed and self._sort_buffer:
            _INF = float("inf")
            self._sort_buffer.sort(
                key=lambda row: (
                    row.get("chromosome") or _INF,
                    row.get("base_pair_start") or _INF,
                )
            )
            open_fn = gzip.open if self._compress else open
            with open_fn(self._output_path, "wt", encoding="utf-8", newline="") as fh:
                writer = csv.DictWriter(
                    fh,
                    fieldnames=self._table.output_fieldnames,
                    delimiter="\t",
                    extrasaction="raise",
                )
                writer.writeheader()
                writer.writerows(self._sort_buffer)
            self._sort_buffer.clear()

    def run(self):
        """Validate each row and write valid ones without progress reporting."""
        for _ in self:
            pass  # __iter__ does all the work

    @property
    def rows_processed(self) -> int:
        """Total number of rows processed so far (valid + invalid)."""
        return self._rows_processed

    @property
    def valid_count(self) -> int:
        """Number of valid rows written to the output."""
        return self._valid_count

    @property
    def error_count(self) -> int:
        """Number of validation errors encountered."""
        return len(self._table.errors)

    @property
    def has_validation_failed(self) -> bool:
        return self.error_count > 0
