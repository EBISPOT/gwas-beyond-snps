from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, ClassVar, Self, final

from gwascatalog.sumstatlib._pydantic import (
    AliasChoices,
    Field,
    model_validator,
)
from gwascatalog.sumstatlib.constants import GENE_FIELD_INDEX_MAP, MIN_GENE_RECORDS
from gwascatalog.sumstatlib.core.models import BaseSumstatModel
from gwascatalog.sumstatlib.core.sumstat_types import (
    BasePairEnd,
    BasePairStart,
    Chromosome,
)
from gwascatalog.sumstatlib.gene.sumstat_types import (
    EnsemblGeneID,
    HGNCGeneSymbol,
)

if TYPE_CHECKING:
    from collections.abc import Mapping


@final
class GeneSumstatModel(BaseSumstatModel):
    """
    Gene-based GWAS summary statistic model.

    Never instantiate this model directly (e.g. GeneModel(hgnc_symbol=...))

    Always use GeneModel.model_validate and set a validation context
     via model_validate(..., context=...).

    See https://docs.pydantic.dev/latest/concepts/validators/#validation-data for more
        details.

    Validation context keys:
      - allow_zero_pvalues (bool, optional):
    """

    MIN_RECORDS: ClassVar[int] = MIN_GENE_RECORDS
    FIELD_MAP: ClassVar[Mapping[str, int]] = GENE_FIELD_INDEX_MAP
    VALID_FIELD_NAMES: ClassVar[list[str]] = list(GENE_FIELD_INDEX_MAP.keys())

    # at least one type of gene name is mandatory
    ensembl_gene_id: Annotated[
        EnsemblGeneID | None,
        Field(
            default=None,
            validation_alias=AliasChoices("ensembl_gene_id", "ensg"),
            serialization_alias="ensembl_gene_id",
        ),
    ]
    hgnc_symbol: Annotated[
        HGNCGeneSymbol | None,
        Field(
            default=None,
            validation_alias=AliasChoices("hgnc_symbol", "hgnc"),
            serialization_alias="hgnc_symbol",
        ),
    ]

    # optional coordinates for the field
    chromosome: Annotated[
        Chromosome | None,
        Field(
            default=None,
            validation_alias=AliasChoices("chromosome", "chrom"),
            serialization_alias="chromosome",
        ),
    ]
    base_pair_start: Annotated[
        BasePairStart | None,
        Field(
            default=None,
            validation_alias=AliasChoices("base_pair_start", "start"),
            serialization_alias="base_pair_start",
        ),
    ]
    base_pair_end: Annotated[
        BasePairEnd | None,
        Field(
            default=None,
            validation_alias=AliasChoices("base_pair_end", "end"),
            serialization_alias="base_pair_end",
        ),
    ]

    def validate_semantics(self):
        raise NotImplementedError

    @classmethod
    def valid_field_names(cls) -> list[str]:
        return list(GENE_FIELD_INDEX_MAP.keys())

    @model_validator(mode="after")
    def validate_location(self) -> Self:
        match (self.chromosome, self.base_pair_start, self.base_pair_end):
            case None, None, None:
                return self
            case int(), int() as start, int() as end:
                if end <= start:
                    raise ValueError(
                        "base_pair_end must be greater than base_pair_start"
                    )
                return self
            case _, int(), None | _, None, int():
                raise ValueError("Provide both values: base_pair_start, base_pair_end")
            case _:
                raise ValueError(
                    "Bad combination of chromosome, base_pair_start, base_pair_end"
                )

    @model_validator(mode="after")
    def check_gene_name_fields(self) -> Self:
        match (self.ensembl_gene_id, self.hgnc_symbol):
            case (None, None):
                raise ValueError("Missing ensembl_gene_id or hgnc_symbol")
            case _:
                return self

    @property
    def effect_size(self) -> float | None:
        effect_size = None
        if self.odds_ratio is not None:
            effect_size = self.odds_ratio
        elif self.beta is not None:
            effect_size = self.beta
        elif self.z_score is not None:
            effect_size = self.z_score

        return effect_size

    @property
    def has_confidence_intervals(self) -> bool:
        return (self.confidence_interval_lower is not None) or (
            self.confidence_interval_upper is not None
        )
