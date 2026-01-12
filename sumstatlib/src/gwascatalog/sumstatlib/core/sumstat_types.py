from __future__ import annotations

from typing import Annotated

from pydantic import AliasChoices, BeforeValidator, Field, PositiveInt

from gwascatalog.sumstatlib.type_helpers import chromosome_to_integer

Chromosome = Annotated[
    int,
    Field(description="Chromosome where the variant is located", ge=1, le=26),
    BeforeValidator(chromosome_to_integer),
]

BasePairLocation = Annotated[
    int,
    Field(
        description="The first position of the variant in the reference, using the "
        "coordinate system declared",
        ge=0,
    ),
]

Beta = Annotated[
    float,
    Field(
        description="Effect size as beta",
    ),
]

OddsRatio = Annotated[
    float,
    Field(
        description="Effect size as odds ratio",
        ge=0,
    ),
]

HazardRatio = Annotated[float, Field(description="Effect size as hazard ratio", ge=0)]

StandardError = Annotated[float, Field(description="Standard error of the effect")]

pValue = Annotated[
    float,
    Field(
        description="p-value of GWAS association",
        validation_alias=AliasChoices("p_value", "p-value", "pval", "P-value", "P"),
        ge=0,
        le=1,
    ),
]

negLog10pValue = Annotated[
    float,
    Field(
        description="Negative log10 p-value of the association statistic",
        validation_alias=AliasChoices("neg_log_10_p_value"),
        ge=0,
    ),
]

confidenceIntervalUpper = Annotated[
    float,
    Field(
        description="Upper value of the confidence interval",
        validation_alias=AliasChoices("ci_upper"),
    ),
]

confidenceIntervalLower = Annotated[
    float,
    Field(
        description="Lower value of the confidence interval",
        validation_alias=AliasChoices("ci_lower"),
    ),
]

Info = Annotated[float, Field(description="Imputation information metric", ge=0, le=1)]

sampleSizePerVariant = Annotated[
    PositiveInt, Field(description="Sample size per variant")
]
