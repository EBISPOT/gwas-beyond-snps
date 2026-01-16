from __future__ import annotations

from typing import Annotated

from pydantic import BeforeValidator, Field, PositiveInt

from gwascatalog.sumstatlib.core.helpers import chromosome_to_integer

Chromosome = Annotated[
    int,
    Field(description="Chromosome where the variant is located", ge=1, le=25),
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

PValue = Annotated[
    float,
    Field(
        description="p-value of GWAS association",
        ge=0,
        le=1,
    ),
]

NegLog10pValue = Annotated[
    float,
    Field(
        description="Negative log10 p-value of the association statistic",
        ge=0,
    ),
]

ConfidenceIntervalUpper = Annotated[
    float,
    Field(
        description="Upper value of the confidence interval",
    ),
]

ConfidenceIntervalLower = Annotated[
    float,
    Field(
        description="Lower value of the confidence interval",
    ),
]

Info = Annotated[float, Field(description="Imputation information metric", ge=0, le=1)]

SampleSizePerVariant = Annotated[
    PositiveInt, Field(description="Sample size per variant")
]

BasePairStart = Annotated[
    int,
    Field(
        description="The start position of the CNV, using the "
        "coordinate system declared",
        ge=0,
    ),
]
BasePairEnd = Annotated[
    int,
    Field(
        description="The end position of the CNV, using the coordinate system declared",
        ge=0,
    ),
]
