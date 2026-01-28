from __future__ import annotations

from typing import Self, final

from pydantic import ConfigDict, model_validator

from gwascatalog.sumstatlib.core.helpers import check_confidence_interval_structure
from gwascatalog.sumstatlib.core.models import BaseSumstatModel
from gwascatalog.sumstatlib.core.sumstat_types import (
    BasePairEnd,
    BasePairStart,
    Beta,
    Chromosome,
    ConfidenceIntervalLower,
    ConfidenceIntervalUpper,
    OddsRatio,
    StandardError, SampleSizePerVariant,
)
from gwascatalog.sumstatlib.gene.sumstat_types import (
    EnsemblGeneID,
    HGNCGeneSymbol,
    ZScore,
)


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

    model_config = ConfigDict(extra="allow")

    # at least one type of gene name is mandatory
    ensembl_gene_id: EnsemblGeneID | None = None
    hgnc_symbol: HGNCGeneSymbol | None = None

    # optional coordinates for the field
    chromosome: Chromosome | None = None
    base_pair_start: BasePairStart | None = None
    base_pair_end: BasePairEnd | None = None

    # only one type of effect size is allowed
    z_score: ZScore | None = None
    odds_ratio: OddsRatio | None = None
    beta: Beta | None = None
    standard_error: StandardError | None = None

    # encouraged
    confidence_interval_lower: ConfidenceIntervalLower | None = (
        None  # ci for odds ratio
    )
    confidence_interval_upper: ConfidenceIntervalUpper | None = None

    n: SampleSizePerVariant | None = None

    def validate_semantics(self):
        raise NotImplementedError

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
                raise ValueError("Bad combination of chromosome, base_pair_start,"
                                 " base_pair_end")

    @model_validator(mode="after")
    def check_gene_name_fields(self) -> Self:
        match (self.ensembl_gene_id, self.hgnc_symbol):
            case (None, None):
                raise ValueError("Missing ensembl_gene_id or hgnc_symbol")
            case _:
                return self

    @model_validator(mode="after")
    def check_confidence_interval_structure(self) -> Self:
        check_confidence_interval_structure(
            ci_lower=self.confidence_interval_lower,
            ci_upper=self.confidence_interval_upper,
        )
        return self

    @model_validator(mode="after")
    def check_effect_size_fields(self) -> Self:
        """Only one effect size value can be provided."""
        match (self.z_score, self.odds_ratio, self.beta):
            case None, None, None:
                return self
            case (float(), None, None) | (None, float(), None) | (None, None, float()):
                return self
            case _:
                raise ValueError("Provide only one value: z_score, odds_ratio, beta")

    @model_validator(mode="after")
    def check_effect_size_in_specified_interval(self) -> Self:
        """A provided effect size must be inside a provided confidence interval"""
        if self.effect_size is None:
            return self

        if (
            self.confidence_interval_lower is None
            or self.confidence_interval_upper is None
        ):
            return self

        if not (
            self.confidence_interval_lower
            <= self.effect_size
            <= self.confidence_interval_upper
        ):
            raise ValueError(
                f"{self.effect_size} is outside interval "
                f"{self.confidence_interval_lower} and {self.confidence_interval_upper}"
            )

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
