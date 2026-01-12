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
    NOT_REPORTED = "NR"


class Sex(StrEnum):
    """Types of sex-stratified analysis"""

    MALE = "M"
    FEMALE = "F"
    COMBINED = "combined"
    NOT_REPORTED = "NR"


class GeneticVariation(StrEnum):
    """Type of genetic variation recorded"""

    SNP = "SNP"
    CNV = "CNV"
    GENE = "gene-based"


class Stage(StrEnum):
    """Stage of the experimental design"""

    DISCOVERY = "discovery"
    REPLICATION = "replication"


class AncestryCategory(StrEnum):
    """
    An ancestry category label that is appropriate for the sample. For more information
    about each category label, see Table 1, Morales et al., 2018.
    """

    ABORIGINAL_AUSTRALIAN = "Aboriginal Australian"
    AFRICAN_AMERICAN_OR_AFRO_CARRIBEAN = "African American or Afro-Caribbean"
    AFRICAN_UNSPECIFIED = "African unspecified"
    ASIAN_UNSPECIFIED = "Asian unspecified"
    CENTRAL_ASIAN = "Central Asian"
    CIRCUMPOLAR_PEOPLES = "Circumpolar peoples"
    EAST_ASIAN = "East Asian"
    EUROPEAN = "European"
    GREATER_MIDDLE_EASTERN = (
        "Greater Middle Eastern (Middle Eastern, North African or Persian)"
    )
    HISPANIC_OR_LATIN_AMERICAN = "Hispanic or Latin American"
    NOT_REPORTED = "NR"
    OCEANIAN = "Oceanian"
    OTHER = "Other"
    OTHER_ADMIXED_ANCESTRY = "Other admixed ancestry"
    SOUTH_ASIAN = "South Asian"
    SOUTH_EAST_ASIAN = "South East Asian"
    SUB_SAHARAN_AFRICAN = "Sub-Saharan African"
