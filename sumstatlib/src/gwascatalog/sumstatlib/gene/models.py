from __future__ import annotations

from typing import final

from pydantic import ConfigDict, model_validator

from gwascatalog.sumstatlib.core.models import BaseSumstatModel
from gwascatalog.sumstatlib.core.sumstat_types import (
    BasePairEnd,
    BasePairStart,
    Beta,
    ConfidenceIntervalLower,
    ConfidenceIntervalUpper,
    NegLog10pValue,
    OddsRatio,
    PValue,
)
from gwascatalog.sumstatlib.gene.sumstat_types import (
    EnsemblGeneID,
    HGNCGeneSymbol,
    ZScore,
)


@final
class GeneModel(BaseSumstatModel):
    """A row in a gene-based sumstat file"""

    model_config = ConfigDict(extra="allow")

    # at least one type of gene name is mandatory
    ensembl_gene_id: EnsemblGeneID | None
    hgnc_symbol: HGNCGeneSymbol | None

    # optional coordinates for the field
    base_pair_start: BasePairStart | None
    base_pair_end: BasePairEnd | None

    # p-values (one field is mandatory, two is an error)
    p_value: PValue
    neg_log_10_p_value: NegLog10pValue

    # TODO: only one field permitted
    z_score: ZScore | None
    odds_ratio: OddsRatio | None
    beta: Beta | None

    confidence_interval_lower: ConfidenceIntervalLower | None
    confidence_interval_upper: ConfidenceIntervalUpper | None

    @model_validator(mode="after")
    def check_gene_name(self):
        if self.ensembl_gene_id is None and self.hgnc_symbol is None:
            raise ValueError("Missing a gene name")
        return self

    @model_validator(mode="after")
    def check_p_value(self):
        # check_p_value(p_value=self.p_value, neg_log10_p_value=self.neg_log_10_p_value)
        return self

    @model_validator(mode="after")
    def check_confidence_intervals(self):
        # first check presence and range
        # check_confidence_intervals(
        #     ci_lower=self.confidence_interval_lower,
        #     ci_upper=self.confidence_interval_upper,
        # )
        # TODO: compare against effect size
        return self
