from __future__ import annotations

from enum import StrEnum


class GeneticVariationType(StrEnum):
    CNV = "CNV"
    GENE = "GENE"
    SNP = "SNP"
