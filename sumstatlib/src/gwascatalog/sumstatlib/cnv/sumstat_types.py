from __future__ import annotations

from typing import Annotated

from gwascatalog.sumstatlib.cnv.sumstat_enums import EffectDirection, ModelType
from pydantic import Field

cnv_regex = r"^(CNV|CN=?\d+)(,(CNV|CN=?\d+))*$"

CNVEffectAllele = Annotated[
    str,
    Field(
        description="""
        The symbolic allele associated with the effect, optionally representing the 
        copy number.
        
        See how CNVs are represented at:
        
        https://www.ensembl.org/info/docs/tools/vep/vep_formats.html#sv
        """,
        pattern=cnv_regex,
        examples=["CNV", "CN=5", "CN2", "CN=0,CN=2,CN=4"],
    ),
]

EffectDirectionField = Annotated[
    EffectDirection,
    Field(
        description="Direction in which the CNV affects a trait",
        examples=["positive", "negative", "ambiguous"],
    ),
]

ModelTypeField = Annotated[
    ModelType,
    Field(
        description="Genetic association model type",
        examples=["additive", "recessive", "dominant", "dosage-sensitive"],
    ),
]
