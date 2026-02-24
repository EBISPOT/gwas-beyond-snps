from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any, ClassVar, Self, final

from gwascatalog.sumstatlib._pydantic import (
    AliasChoices,
    Field,
    PrivateAttr,
    computed_field,
    model_validator,
)
from gwascatalog.sumstatlib.cnv.sumstat_enums import EffectDirection
from gwascatalog.sumstatlib.cnv.sumstat_types import (
    StatisticalModelTypeField,
)
from gwascatalog.sumstatlib.constants import CNV_FIELD_INDEX_MAP, MIN_CNV_RECORDS
from gwascatalog.sumstatlib.core.models import BaseSumstatModel
from gwascatalog.sumstatlib.core.sumstat_enums import GenomeAssembly
from gwascatalog.sumstatlib.core.sumstat_types import (
    BasePairEnd,
    BasePairStart,
    Chromosome,
    PrimaryEffectSizeField,
    SampleSizePerVariant,
)

if TYPE_CHECKING:
    from collections.abc import Mapping


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
    FIELD_MAP: ClassVar[Mapping[str, int]] = CNV_FIELD_INDEX_MAP
    VALID_FIELD_NAMES: ClassVar[list[str]] = list(CNV_FIELD_INDEX_MAP.keys())

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
    statistical_model_type: Annotated[
        StatisticalModelTypeField,
        Field(
            validation_alias=AliasChoices(
                "statistical_model_type", "model_type", "model"
            ),
            serialization_alias="model_type",
        ),
    ]

    n: Annotated[
        SampleSizePerVariant | None,
        Field(
            default=None, validation_alias=AliasChoices("n"), serialization_alias="n"
        ),
    ]

    # private attributes to avoid polluting the data model
    # adopting this pattern because metadata are provided by a payload or CLI flag at
    # runtime, so adding a field doesn't make sense
    _assembly: GenomeAssembly = PrivateAttr()

    def model_post_init(self, context: Any) -> None:
        if "assembly" not in context:
            raise ValueError("genome assembly must be provided via validation context")

        self._assembly = GenomeAssembly(context["assembly"])

    def validate_semantics(self) -> None:
        # validate start location is smaller than chromosome size?
        raise NotImplementedError

    @computed_field
    @property
    def cnv_length(self) -> int:
        return self.base_pair_end - self.base_pair_start

    @computed_field
    @property
    def effect_direction(self) -> EffectDirection:
        effect_size = self.effect_size
        if effect_size is None:
            raise ValueError("effect_size must not be None for CNVs")

        # Signed metrics (zero-centered)
        if self.effect_size_type in {"beta", "z_score"}:
            if effect_size > 0:
                return EffectDirection.POSITIVE
            if effect_size < 0:
                return EffectDirection.NEGATIVE
            return EffectDirection.AMBIGUOUS

        # Ratio metrics (one-centered)
        if self.effect_size_type in {"odds_ratio", "hazard_ratio"}:
            if effect_size > 1:
                return EffectDirection.POSITIVE
            if effect_size < 1:
                return EffectDirection.NEGATIVE
            return EffectDirection.AMBIGUOUS

        raise ValueError(f"Invalid effect_size_type: {self.effect_size_type}")

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
