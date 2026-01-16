from __future__ import annotations

from typing import Literal, Self, final

from pydantic import ConfigDict, PrivateAttr, computed_field, model_validator
from pydantic_core.core_schema import ValidationInfo

from gwascatalog.sumstatlib.cnv.sumstat_types import (
    CNVEffectAllele,
    EffectDirectionField,
    ModelTypeField,
)
from gwascatalog.sumstatlib.core.models import BaseSumstatModel
from gwascatalog.sumstatlib.core.sumstat_enums import GenomeAssembly
from gwascatalog.sumstatlib.core.sumstat_types import (
    BasePairEnd,
    BasePairStart,
    Chromosome,
    NegLog10pValue,
    PValue,
    SampleSizePerVariant,
)

effect_allele_default: Literal["CNV"] = "CNV"


@final
class CNVModel(BaseSumstatModel):
    """
    Copy Number Variant (CNV) GWAS summary statistic model.

    Never instantiate this model directly (e.g. CNVModel(chromosome=1, ...))

    Always use CNVModel.model_validate and set a validation context
     via model_validate(..., context=...).

    See https://docs.pydantic.dev/latest/concepts/validators/#validation-data for more
        details.

    Validation context keys:
      - assembly (GenomeAssembly, mandatory)
      - allow_zero_pvalues (bool, optional):
    """

    model_config = ConfigDict(extra="allow")

    chromosome: Chromosome
    base_pair_start: BasePairStart
    base_pair_end: BasePairEnd
    effect_direction: EffectDirectionField
    effect_allele: CNVEffectAllele = effect_allele_default
    p_value: PValue | None = None
    neg_log10_pvalue: NegLog10pValue | None = None
    model_type: ModelTypeField
    n: SampleSizePerVariant | None = None

    # private attributes to avoid polluting the data model
    # adopting this pattern because metadata are provided by a payload or CLI flag at
    # runtime, so adding a field doesn't make sense
    _assembly: GenomeAssembly = PrivateAttr(default=None)

    def model_post_init(self, context: ValidationInfo) -> None:
        if "assembly" not in context:
            raise ValueError("genome assembly must be provided via validation context")

        self._assembly = GenomeAssembly(context["assembly"])

    def validate_semantics(self) -> None:
        raise NotImplementedError

    @computed_field
    @property
    def cnv_length(self) -> int:
        return self.base_pair_end - self.base_pair_start

    @model_validator(mode="after")
    def validate_location(self) -> Self:
        if self.base_pair_end <= self.base_pair_start:
            raise ValueError("base_pair_end must be greater than base_pair_start")

        return self

    @computed_field
    @property
    def cnv_id(self) -> str:
        if self._assembly is None:
            raise ValueError("Genome assembly was not provided via validation context")
        return (
            f"{self.chromosome}:"
            f"{self.base_pair_start}-"
            f"{self.base_pair_end}:"
            f"{self._assembly}"
        )
