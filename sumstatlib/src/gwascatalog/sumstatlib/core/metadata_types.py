from __future__ import annotations

from pathlib import Path
from typing import Annotated

from pydantic import (
    AfterValidator,
    Field,
    PositiveInt,
    StringConstraints,
)

from gwascatalog.sumstatlib.core.metadata_enums import (
    AncestryCategory,
    ArrayManufacturer,
    CoordinateSystem,
    GeneticVariation,
    GenomeAssembly,
    GenotypingTechnology,
    Sex,
    Stage,
)
from gwascatalog.sumstatlib.core.type_helpers import sumstat_path_validator

StudyTag = Annotated[
    str,
    Field(
        description="""
    Each genome-wide association study in the submission must have a unique free-text 
    label. You can use any string of characters that will help you identify each 
    individual GWAS
    """,
        examples=["WHR_unadj"],
    ),
]

ArrayInformation = Annotated[
    str,
    Field(
        description="""
    Additional information about the genotyping array. For example, for targeted 
    arrays, please provide the specific type of array.
    """,
        examples=["Immunochip"],
    ),
]

GenomeAssemblyField = Annotated[GenomeAssembly, Field(description="Genome assembly")]

Imputation = Annotated[
    bool, Field(description="Were SNPs imputed for the discovery GWAS?")
]

StatisticalModel = Annotated[
    str,
    Field(
        description="""A brief description of the statistical model used to determine 
        association significance. Important to distinguish studies that would otherwise 
        appear identical (e.g. the same trait analysed using additive, dominant and 
        recessive models).
        """,
        examples=["additive model", "recessive model", "dominant model"],
    ),
]

StudyDescription = Annotated[
    str,
    Field(description="Additional information about the study"),
]

VariantCount = Annotated[
    PositiveInt,
    Field(
        description="The number of variants analysed in the discovery stage (after QC)"
    ),
]

CoordinateSystemField = Annotated[
    CoordinateSystem, Field(description="Coordinate system")
]

ReportedTrait = Annotated[
    str,
    Field(
        description="""
    The trait under investigation. Please describe the trait concisely but with enough 
    detail to be clear to a non-specialist. Avoid use of abbreviations; if these are 
    necessary, please define them or their source in the readme file.
    """,
        examples=["Reticulocyte count"],
    ),
]

BackgroundTrait = Annotated[
    str,
    Field(
        description="""
        Any background trait(s) shared by all individuals in the GWAS (e.g. in both 
        cases and controls)
        """,
        examples=["Nicotine dependence"],
    ),
]
SampleSize = Annotated[PositiveInt, Field(description="Sample size")]

CaseCount = Annotated[
    PositiveInt, Field(description="Number of cases for a case/control study")
]

ControlCount = Annotated[
    PositiveInt, Field(description="Number of controls for a case/control study")
]

CaseControlStudy = Annotated[
    bool,
    Field(description="Flag whether the study is a case-control study", default=False),
]

SampleAncestry = Annotated[
    str,
    Field(
        description="""The most detailed available population descriptor(s) for the 
        sample""",
        examples=["Han Chinese"],
    ),
]

AncestryCategoryField = Annotated[
    AncestryCategory,
    Field(
        description="""
    An ancestry category label that is appropriate for the sample. For more information 
    about each category label, see Table 1, Morales et al., 2018.
    """
    ),
]

SummaryStatisticsFile = Annotated[
    Path,
    Field(
        description="""
    The name of the summary statistics file uploaded via Globus. Summary statistics 
    must be submitted for at least one study. Enter "NR" for any additional studies 
    without summary statistics.
    """,
        examples=["example.tsv"],
    ),
    AfterValidator(sumstat_path_validator),
]


Md5Sum = Annotated[
    str,
    StringConstraints(
        min_length=32,
        max_length=32,
        pattern=r"^[a-fA-F0-9]{32}$",
    ),
]

Readme = Annotated[
    str,
    Field(
        description="""
    The readme text that accompanies your analysis. If the same readme applies to all 
    studies in the submission, please copy the text into each row. Leave blank for any 
    studies without summary statistics
    """
    ),
]

isNeglog10pValue = Annotated[
    bool,
    Field(
        description="Are summary statistics p-values given in the negative log10 form?"
    ),
]

MAFLowerLimit = Annotated[
    float,
    Field(
        description="Lowest possible allele frequency given in summary statistics",
        gt=0,
        lt=1,
        examples=[0.0001],
    ),
]

Cohort = Annotated[
    str,
    Field(
        description="""
        Cohort represented in the discovery sample. Enter only if the specific named 
        cohorts are used in the analysis.
        """,
        examples=["UKBB", "FINRISK"],
    ),
]

CohortRef = Annotated[
    str,
    Field(
        description="""
        List of cohort specific identifier(s) issued to this research study. For 
        example, an ANID issued by UK Biobank.
        """,
        examples=["ANID45956"],
    ),
]

GenotypingTechnologyField = Annotated[
    GenotypingTechnology,
    Field(
        description="Genotyping technology used for analysis",
        examples=GenotypingTechnology._member_names_,
    ),
]

AnalysisSoftware = Annotated[
    str, Field(description="Software and version used for the association analysis")
]

ImputationPanel = Annotated[str, Field(description="Imputation panel")]

ImputationSoftware = Annotated[
    str, Field(description="Software and version used for imputation")
]

AncestryMethod = Annotated[
    str,
    Field(
        description="""
        Name the method used to determine sample ancestry. For consistency, we 
        recommend you choose between the terms “self-reported” or “genetically 
        determined” where appropriate, but other text is permissible if these do not 
        apply.        
        """,
        examples=["self-reported", "genetically determined"],
    ),
]

CountryOfRecruitment = Annotated[
    str,
    Field(
        description="Country where samples were recruited",
        examples=["Japan", "China"],
    ),
]

IsSorted = Annotated[
    bool, Field(description="Are the corresponding summary statistics are sorted?")
]

AdjustedCovariates = Annotated[
    str,
    Field(description="A covariate the GWAS is adjusted for", examples=["age", "sex"]),
]

OntologyMapping = Annotated[
    str, Field(description="Short form ontology terms describing the trait")
]

SexField = Annotated[
    Sex, Field(description="Indicate if and how the study was sex-stratified")
]

GeneticVariationField = Annotated[
    GeneticVariation,
    Field(description="Indicate what kind of genetic variation was studied"),
]

ArrayManufacturerField = Annotated[
    ArrayManufacturer,
    Field(
        description="Manufacturer of the genotyping array used for the discovery "
        "stage.",
        examples=["Illumina", "Affymetrix", "Perlegen"],
    ),
]

StageField = Annotated[
    Stage,
    Field(description="Stage of the experimental design"),
]

NumberOfIndividuals = Annotated[
    PositiveInt, Field(description="Number of individuals in this group")
]

SampleDescription = Annotated[
    str,
    Field(
        description="""Additional information required for the interpretation of 
    results, e.g. sex (males/females), age (adults/children), ordinal variables, or 
    multiple traits analysed together ("or" traits).

    Please do not enter ancestry information in this field (see other fields).
    """
    ),
]

FounderOrGeneticallyIsolatedPopulationDescriptor = Annotated[
    str,
    Field(
        description="For founder or genetically isolated population, provide "
        "description",
        examples=["Korculan(founder/genetic isolate)", "Vis(founder/genetic isolate)"],
    ),
]
