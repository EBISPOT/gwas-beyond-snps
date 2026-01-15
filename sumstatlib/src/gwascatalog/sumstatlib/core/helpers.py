"""
Helper functions for pydantic model and type validation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from gwascatalog.sumstatlib.constants import CHROMOSOME_MAP


def sumstat_path_validator(p: Path) -> Path:
    if p.suffix == ".tsv" or p.suffixes[-2:] == [".tsv", ".gz"]:
        return p
    raise ValueError(
        "Path must end with .tsv or .tsv.gz. Record missing paths using 'NR'"
    )


def chromosome_to_integer(chromosome: Any) -> int:
    """Remap chromosomes to GWAS-SSF integers"""
    chrom_string = str(chromosome).strip()
    try:
        chrom = int(chrom_string)
    except ValueError:
        try:
            chrom = CHROMOSOME_MAP[chrom_string]
        except KeyError as bad_remap:
            raise ValueError(f"Invalid chromosome {chromosome}") from bad_remap

    return chrom


def check_confidence_intervals(
    *, ci_lower: float | None, ci_upper: float | None
) -> None:
    match (ci_lower, ci_upper):
        case (None, None):
            return  # both missing, don't validate
        case (float(), float()) if ci_lower <= ci_upper:
            return  # both floats, check ordering
        case (float(), float()):
            raise ValueError("ci_lower must be less than or equal to ci_upper")
        case (float() | None) | (None, float()):
            raise ValueError("Provide both ci_lower and ci_upper or neither")
        case _:
            # anything else raise a more generic exception
            raise ValueError(f"Invalid confidence intervals: {ci_lower=}, {ci_upper=}")
