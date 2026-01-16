from __future__ import annotations

from typing import Annotated

from pydantic import Field

from gwascatalog.sumstatlib.snp.sumstat_enums import RefAlleleState

sequence_regex = r"^[ACGT]$"
SNPEffectAllele = Annotated[
    str,
    Field(
        description="The allele associated with the effect",
        min_length=1,
        pattern=sequence_regex,
    ),
]

OtherAllele = Annotated[
    str,
    Field(description="The non-effect allele", min_length=1, pattern=sequence_regex),
]

EffectAlleleFrequency = Annotated[
    float,
    Field(
        description="Frequency of the effect allele in the control population",
        ge=0,
        le=1,
    ),
]

VariantId = Annotated[
    str,
    Field(
        description="""
        An internal variant identifier in the form of:
         <chromosome>_<base_pair_location>_ <reference_allele>_<alternate_allele>""",
        pattern=r"^([0-9]{1,2}|X|Y|MT)_[0-9]+_[ACGT]+_[ACGT]+$",
    ),
]

RsID = Annotated[
    str,
    Field(description="The rsID of the variant", pattern=r"^rs[0-9]+$"),
]

RefAlleleField = Annotated[
    RefAlleleState,
    Field(
        description="State which of the alleles is the reference allele",
        examples=["EA"],
    ),
]
