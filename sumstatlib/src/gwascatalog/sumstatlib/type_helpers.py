from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Final

CHROMOSOME_MAP: Final[Mapping[str, int]] = {"X": 23, "Y": 24, "MT": 25}
DNA_NUCLEOTIDES: Final[frozenset[str]] = frozenset({"A", "C", "T", "G"})


def validate_actg_sequence(allele: str) -> str:
    """Ensure every nucleotide in the sequence is A, C, G, or T.

    Empty strings are accepted."""
    if bad_allele := set(allele) - DNA_NUCLEOTIDES:
        raise ValueError(f"Invalid allele: {bad_allele}")
    return allele


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
