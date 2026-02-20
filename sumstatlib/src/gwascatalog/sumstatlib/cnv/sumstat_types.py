from __future__ import annotations

from typing import Annotated

from gwascatalog.sumstatlib._pydantic import Field
from gwascatalog.sumstatlib.cnv.sumstat_enums import EffectDirection, ModelType

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
