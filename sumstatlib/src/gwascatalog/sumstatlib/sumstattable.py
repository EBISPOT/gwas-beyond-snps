from __future__ import annotations

import csv
import gzip
from functools import cached_property
from pathlib import Path
from typing import IO, TYPE_CHECKING, Literal, TypedDict

from pydantic import ValidationError

from gwascatalog.sumstatlib.core.sumstat_enums import GenomeAssembly  # noqa: TC001

if TYPE_CHECKING:
    from collections.abc import Generator, Iterable

    from gwascatalog.sumstatlib.core.models import BaseSumstatModel


def _is_gzip(path: Path) -> bool:
    """Check whether *path* starts with the gzip magic bytes."""
    with path.open("rb") as f:
        return f.read(2) == b"\x1f\x8b"


class SumstatConfig(TypedDict):
    allow_zero_p_values: bool
    assembly: GenomeAssembly
    primary_effect_size: Literal["beta", "odds_ratio", "zscore"]


class SumstatTable:
    MAX_ERRORS = 200

    def __init__(
        self,
        data_model: type[BaseSumstatModel],
        input_path: Path,
        config: SumstatConfig,
    ):
        self._data_model = data_model
        self._path = Path(input_path)
        self._config = config
        self._errors: list[ErrorDetails] = []

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

    def validate_rows(self) -> None:
        """Validate all rows, storing errors in self._errors and yielding validated
        rows.
        """
        for row in self._parse_csv():
            try:
                _ = self._data_model.model_validate(row, context=self._config).model_dump(
                    include=set(self.output_fieldnames)
                )
            except ValidationError as exc:
                for error in exc.errors():
                    SumstatError(error.get("l"))

                pass

    def errors(self) -> Iterable[tuple[int, Exception]]:
        """Return all row errors encountered"""
        return self._errors

    def has_any_errors(self) -> bool:
        """Whether any errors occurred during row validation."""
        return bool(self._errors)
