from __future__ import annotations

import csv
import gzip
import logging
from functools import cached_property
from pathlib import Path
from typing import IO, TYPE_CHECKING, Literal, TypedDict

from gwascatalog.sumstatlib._pydantic import ValidationError
from gwascatalog.sumstatlib.core.sumstat_enums import GenomeAssembly  # noqa: TC001

if TYPE_CHECKING:
    from collections.abc import Generator, Iterable

    from gwascatalog.sumstatlib.core.models import BaseSumstatModel

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


class SumstatTable:
    MAX_ERRORS = 100

    def __init__(
        self,
        data_model: type[BaseSumstatModel],
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

    def _parse_csv(self, sample_size: int = 4096) -> Generator[dict, None, None]:
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
        for row in self._parse_csv():
            header = list(row.keys())
            break

        if header is None:
            raise ValueError("Can't read header")

        return header

    @cached_property
    def output_fieldnames(self) -> list[str]:
        """Determine output column order from the first valid row of the file."""
        for row in self._parse_csv():
            instance = self._data_model.model_validate(row, context=self._config)
            return instance.output_field_order()  # breaks the loop
        raise ValueError("No rows found to determine output column order")

    def validate_rows(self) -> Generator[dict, None, None]:
        """Validate all rows, storing errors in self._errors and yielding validated
        rows.
        """
        include_fields = set(self.output_fieldnames)
        for i, row in enumerate(self._parse_csv()):
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

    def errors(self) -> Iterable[SumstatError]:
        """Return all row errors encountered"""
        return self._errors
