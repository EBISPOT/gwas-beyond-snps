from __future__ import annotations

from typing import Annotated, Any, ClassVar, Self, final

from gwascatalog.sumstatlib._pydantic import (
    AliasChoices,
    Field,
    PrivateAttr,
    computed_field,
    model_validator,
)
from gwascatalog.sumstatlib.cnv.sumstat_types import (
    EffectDirectionField,
    ModelTypeField,
)
from gwascatalog.sumstatlib.constants import CNV_FIELD_INDEX_MAP, MIN_CNV_RECORDS
from gwascatalog.sumstatlib.core.models import BaseSumstatModel
from gwascatalog.sumstatlib.core.sumstat_enums import GenomeAssembly
from gwascatalog.sumstatlib.core.sumstat_types import (
    BasePairEnd,
    BasePairStart,
    Chromosome,
    PrimaryEffectSizeField,
)


@final
class CNVSumstatModel(BaseSumstatModel):
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

    MIN_RECORDS: ClassVar[int] = MIN_CNV_RECORDS

    chromosome: Annotated[
        Chromosome,
        Field(
            validation_alias=AliasChoices("chromosome", "chrom"),
            serialization_alias="chromosome",
        ),
    ]
    base_pair_start: Annotated[
        BasePairStart,
        Field(
            validation_alias=AliasChoices("base_pair_start", "start"),
            serialization_alias="base_pair_start",
        ),
    ]
    base_pair_end: Annotated[
        BasePairEnd,
        Field(
            validation_alias=AliasChoices("base_pair_end", "end"),
            serialization_alias="base_pair_end",
        ),
    ]
    effect_direction: Annotated[
        EffectDirectionField,
        Field(
            validation_alias=AliasChoices("effect_direction"),
            serialization_alias="effect_direction",
        ),
    ]
    model_type: Annotated[
        ModelTypeField,
        Field(
            validation_alias=AliasChoices("model_type", "model"),
            serialization_alias="model_type",
        ),
    ]

    # private attributes to avoid polluting the data model
    # adopting this pattern because metadata are provided by a payload or CLI flag at
    # runtime, so adding a field doesn't make sense
    _assembly: GenomeAssembly = PrivateAttr()
    _primary_effect_size: PrimaryEffectSizeField = PrivateAttr()

    def model_post_init(self, context: Any) -> None:
        if "assembly" not in context:
            raise ValueError("genome assembly must be provided via validation context")

        self._assembly = GenomeAssembly(context["assembly"])

        if "primary_effect_size" not in context:
            raise ValueError(
                "primary effect size field must be provided via validation context"
            )
        self._primary_effect_size = context["primary_effect_size"]

    def output_field_order(self) -> list[str]:
        order: list[str] = []

        for field, index in CNV_FIELD_INDEX_MAP.items():
            if getattr(self, field) is not None:
                order.insert(index, field)

        # Extra fields (extra="allow") — stable order from __pydantic_extra__
        extra = self.__pydantic_extra__ or {}

        order.extend(extra.keys())
        return order

    def validate_semantics(self) -> None:
        # validate start location is smaller than chromosome size?
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

    @model_validator(mode="after")
    def check_effect_size_fields(self) -> Self:
        """Only one effect size value can be provided."""
        match (self.z_score, self.odds_ratio, self.beta):
            case (float(), None, None) | (None, float(), None) | (None, None, float()):
                return self
            case None, None, None:
                raise ValueError("Provide one effect size value")
            case _:
                raise ValueError("Provide only one value: z_score, odds_ratio, beta")
