from __future__ import annotations

import math

from pydantic import BaseModel, ConfigDict, model_validator, computed_field

from gwascatalog.sumstatlib.cnv.sumstat_enums import EffectDirection, ModelType
from gwascatalog.sumstatlib.cnv.sumstat_types import BasePairEnd, BasePairStart
from gwascatalog.sumstatlib.core.sumstat_types import (
    Chromosome,
    pValue,
    negLog10pValue,
    N,
)


class CNVSumstatRow(BaseModel):
    model_config = ConfigDict(extra="allow")

    chromosome: Chromosome
    base_pair_start: BasePairStart
    base_pair_end: BasePairEnd
    effect_direction: EffectDirection
    # TODO: add effect allele?
    p_value: pValue | None
    neg_log10_pvalue: negLog10pValue | None
    model_type: ModelType
    n: N | None

    @computed_field
    @property
    def cnv_length(self) -> int:
        return self.base_pair_end - self.base_pair_start

    @model_validator(mode="after")
    def validate_and_fill_pvalues(self):
        if self.p_value is None and self.neg_log10_pvalue is None:
            raise ValueError("Missing p_value or neg_log10_pvalue")

        if self.p_value is not None and self.neg_log10_pvalue is not None:
            raise ValueError("Cannot set both p_value and neg_log10_pvalue")

        if self.p_value is None:
            self.p_value = math.pow(10, -self.neg_log10_pvalue)
        elif self.neg_log10_pvalue is None:
            self.neg_log10_pvalue = -math.log10(self.p_value)

        return self
