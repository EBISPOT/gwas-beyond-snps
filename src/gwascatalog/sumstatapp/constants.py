from __future__ import annotations

from typing import Final

VALID_SUMSTAT_SUFFIXES: Final[frozenset[str]] = frozenset(
    [".tsv", ".tsv.gz", ".csv", ".csv.gz", ".txt", ".txt.gz"]
)
