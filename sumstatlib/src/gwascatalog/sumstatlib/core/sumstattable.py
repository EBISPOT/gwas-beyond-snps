from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

    from gwascatalog.sumstatlib._pydantic import BaseModel


class SumstatTable:
    def __init__(self, data_model: type[BaseModel], input_path: str):
        self._data_model = data_model
        self._path = input_path
        self._errors: list[tuple[int, Exception]] = []

    def output_fieldnames(self) -> None:
        """Return output field names in a consistent order.

        Field names in the input_path may occur in any order, but data submitted to the
        GWAS Catalog must be ordered by:

        1) Mandatory columns, defined in concrete subclasses
        2) A reasonable number of extra columns, defined by authors
        """
        raise NotImplementedError

    def validate_rows(self) -> None:
        """Validate all rows, storing errors in self._errors and yielding validated
        rows.
        """
        raise NotImplementedError

    def errors(self) -> Iterable[tuple[int, Exception]]:
        """Return all row errors encountered"""
        return self._errors

    def has_any_errors(self) -> bool:
        """Whether any errors occurred during row validation."""
        return bool(self._errors)
