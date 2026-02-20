"""
Helper functions for pydantic model and type validation.
"""

from __future__ import annotations

from typing import Any

from gwascatalog.sumstatlib.constants import CHROMOSOME_MAP


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
