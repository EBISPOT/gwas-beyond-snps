from __future__ import annotations

import csv
import gzip
import logging
from functools import cached_property
from pathlib import Path
from typing import IO, TYPE_CHECKING, Literal, NamedTuple, Self, TypedDict

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
    primary_effect_size: Literal["beta", "odds_ratio", "zscore"]


class SumstatError(TypedDict):
    """A parsed pydantic ValidationError"""

    row: int
    loc: int
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
    ):
        self._data_model = data_model
        self._path = Path(input_path)
        self._config = config
        self._errors: list[SumstatError] = []

        if not self._path.exists():
            raise FileNotFoundError(self._path)

        self._min_records = getattr(self._data_model, "MIN_RECORDS", None)
        if self._min_records is None:
            raise TypeError(f"{self._data_model} must have MIN_RECORDS")
        n_rows = self.n_rows
        if n_rows < self._min_records:
            raise ValueError(f"Not enough rows in file: {n_rows=} {self._min_records=}")

    def _open_sumstat(self) -> IO[str]:
        if _is_gzip(self._path):
            return gzip.open(self._path, "rt", encoding="utf-8")
        return self._path.open(mode="rt", encoding="utf-8")

    def parse_csv(self, sample_size: int = 4096) -> Generator[dict, None, None]:
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

    @property
    def has_validation_failed(self) -> bool:
        """Have any ValidationErrors been raised?"""
        return len(self._errors) > 0

    @cached_property
    def n_rows(self) -> int:
        with self._open_sumstat() as f:
            next(f, None)  # skip header
            return sum(1 for _ in f)

    @cached_property
    def _column_names(self) -> list[str]:
        header = None
        for row in self.parse_csv():
            header = list(row.keys())
            break

        if header is None:
            raise ValueError("Can't read header")

        return header

    @cached_property
    def output_fieldnames(self) -> list[str]:
        """Determine output column order from the first valid row of the file."""
        try:
            row = next(self.parse_csv())
            instance = self._data_model.model_validate(row, context=self._config)
            return instance.output_field_order()
        except ValueError as e:
            raise ValueError("First row failed validation, failing fast") from e

    def validate_rows(self) -> Generator[dict, None, None]:
        """Validate all rows, storing errors in self._errors and yielding validated
        rows.
        """
        include_fields = set(self.output_fieldnames)
        for i, row in enumerate(self.parse_csv()):
            try:
                validated = self._data_model.model_validate(
                    row, context=self._config
                ).model_dump(include=include_fields)
            except ValidationError as exc:
                for error in exc.errors():
                    self._errors.append(
                        SumstatError(row=i, loc=error["loc"], msg=error["msg"])
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
        """Create a transactional writer for streaming validated output.

        Returns a context manager that validates rows, writes valid ones
        to a temporary file, and atomically renames on ``commit()``.
        If the context exits without ``commit()``, the temp file is deleted.

        Args:
            output_path: Final destination for the validated output file.
            compress: Gzip-compress the output.  Defaults to ``True`` if
                *output_path* ends with ``'.gz'``.

        Returns:
            A :class:`SumstatWriter` context manager.

        Example (web / Pyodide)::

            table = SumstatTable(model, path, config)
            with table.open_writer(output_path) as writer:
                for row in writer:
                    if row.row_number % 10_000 == 0:
                        post_progress(writer.rows_processed, writer.valid_count)
                if not table.has_validation_failed:
                    writer.commit()

        Example (CLI)::

            with table.open_writer(output_path) as writer:
                for _ in writer:
                    pass
                writer.commit()
        """
        return SumstatWriter(self, output_path, compress=compress)

    @property
    def data_model(self) -> type[CNVSumstatModel | GeneSumstatModel]:
        """The Pydantic data model used for validation"""
        return self._data_model

    @property
    def config(self):
        return self._config


class SumstatWriter:
    """Transactional streaming writer for validated summary statistics.

    Validates each row against the data model and writes valid rows to a
    temporary file. Guidelines for consumers:

    - _Always_ use this class as a context manager
    - Iterate to process rows
    - Iteration yields a ValidatedRow for every row which includes validation status
    - If you want to report progress, add a check inside the iteration (e.g. every
        10,000 rows send a message or print)
    - If you don't want to report progress, you can use the .run() convenience function
    - If the context exits with .commit() the temporary file is cleaned up automatically

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
        self._tmp_path = self._output_path.parent / (self._output_path.name + ".tmp")
        self._committed = False
        self._rows_processed = 0
        self._valid_count = 0
        self._fh: IO[str] | None = None
        self._csv_writer = None
        self._fieldnames = self._table.output_fieldnames

    def __enter__(self) -> Self:
        if self._compress:
            self._fh = gzip.open(self._tmp_path, "wt", encoding="utf-8", newline="")
        else:
            self._fh = self._tmp_path.open("w", encoding="utf-8", newline="")

        self._csv_writer = csv.DictWriter(
            self._fh,
            fieldnames=self._table.output_fieldnames,
            delimiter="\t",
            extrasaction="ignore",
        )
        self._csv_writer.writeheader()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        if self._fh is not None:
            self._fh.close()
            self._fh = None
            self._csv_writer = None

        # Rollback: delete temp file if not committed
        if not self._committed and self._tmp_path.exists():
            self._tmp_path.unlink()

    def __iter__(self) -> Generator[ValidatedRow, None, None]:
        """Validate each row, write valid ones, yield progress for all.

        Yields:
            A :class:`ValidatedRow` for every row in the input file.
        """
        if self._fh is None or self._csv_writer is None:
            raise TypeError(
                "SumstatWriter must be used as a context manager "
                "(use 'with table.open_writer(...) as writer:')"
            )

        for i, row in enumerate(self._table.parse_csv()):
            self._rows_processed = i + 1
            try:
                instance = self._table.data_model.model_validate(
                    row, context=self._table.config
                )
            except ValidationError as exc:
                for error in exc.errors():
                    self._table.add_error(
                        SumstatError(row=i, loc=error["loc"], msg=error["msg"])
                    )
                yield ValidatedRow(row_number=i, is_valid=False)

                if len(self._table.errors) >= self._table.MAX_ERRORS:
                    logger.critical(
                        f"Stopped validation after {self._table.MAX_ERRORS} errors"
                    )
                    # if you expect an exception here it's raised by .commit()
                    break
            else:
                self._valid_count += 1
                self._csv_writer.writerow(instance.model_dump())
                yield ValidatedRow(row_number=i, is_valid=True)

    def run(self):
        """Validate each row and write valid ones without progress reporting."""
        for _ in self:
            pass  # __iter__ does all the work

    def commit(self) -> None:
        """Atomically finalise the output file.

        Flushes all buffers, closes the temp file, and renames it to the
        final output path.

        Raises:
            RuntimeError: If already committed or any invalid rows were encountered.
        """
        if self._committed:
            raise RuntimeError("Already committed")

        if self._table.has_validation_failed:
            raise RuntimeError("Cannot commit: validation failed")

        # Close before rename to flush all buffers (including gzip trailer)
        if self._fh is not None:
            self._fh.close()
            self._fh = None

        self._tmp_path.rename(self._output_path)
        self._committed = True

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
    def is_committed(self) -> bool:
        """Whether the output file has been atomically finalized."""
        return self._committed
