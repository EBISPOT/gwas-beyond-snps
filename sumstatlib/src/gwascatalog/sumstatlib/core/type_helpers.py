from __future__ import annotations

from pathlib import Path


def sumstat_path_validator(p: Path) -> Path:
    if p.suffix == ".tsv" or p.suffixes[-2:] == [".tsv", ".gz"]:
        return p
    raise ValueError(
        "Path must end with .tsv or .tsv.gz. Record missing paths using 'NR'"
    )
