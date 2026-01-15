from __future__ import annotations

from collections.abc import Iterable

from pydantic import BaseModel


class SumstatTable:
    def __init__(self, data_model: type[BaseModel], input_path: str):
        self._data_model = data_model
        self._path = input_path
        self._errors: list[tuple[int, Exception]] = []

    def output_fieldnames(self) -> tuple[str, ...]:
        """Return output field names in a consistent order.

        Field names in the input_path may occur in any order, but data submitted to the
        GWAS Catalog must be ordered by:

        1) Mandatory columns, defined in concrete subclasses
        2) A reasonable number of extra columns, defined by authors
        """
        # default: all fields from Pydantic model
        ...

    def validate_rows(self) -> Iterable[dict[str, object]]:
        """Validate all rows, storing errors in self._errors and yielding validated
        rows.
        """
        ...

    def errors(self) -> Iterable[tuple[int, Exception]]:
        """Return all row errors encountered"""
        return self._errors

    def has_any_errors(self) -> bool:
        """Whether any errors occurred during row validation."""
        return bool(self._errors)
