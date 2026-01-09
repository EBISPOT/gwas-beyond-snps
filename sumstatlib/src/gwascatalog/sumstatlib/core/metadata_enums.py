from __future__ import annotations

from enum import StrEnum


class CoordinateSystem(StrEnum):
    """Coordinate system used for the summary statistics"""

    ONE_BASED = "1-based"
    ZERO_BASED = "0-based"


class GenotypingTechnology(StrEnum):
    """Method used to genotype variants in the discovery stage."""

    GENOME_WIDE_ARRAY = "Genome-wide genotyping array"
    TARGETED_ARRAY = "Targeted genotyping array"
    EXOME_ARRAY = "Exome genotyping array"
    WGS = "Whole genome sequencing"
    WES = "Exome-wide sequencing"


class ArrayManufacturer(StrEnum):
    """Manufacturer of the genotyping array used for the discovery stage"""

    ILLUMINA = "Illumina"
    AFFYMETRIX = "Affymetrix"
    PERLEGEN = "Perlegen"


class GenomeAssembly(StrEnum):
    """Genome assembly for the summary statistics"""

    GRCh38 = "GRCh38"
    GRCh37 = "GRCh37"
    NCBI36 = "NCBI36"
    NCBI35 = "NCBI35"
    NCBI34 = "NCBI34"
