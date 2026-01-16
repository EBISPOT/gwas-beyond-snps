from __future__ import annotations

from gwascatalog.sumstatlib.core.sumstat_types import (
    BasePairLocation,
    Beta,
    Chromosome,
    ConfidenceIntervalLower,
    ConfidenceIntervalUpper,
    HazardRatio,
    Info,
    NegLog10pValue,
    OddsRatio,
    PValue,
    SampleSizePerVariant,
    StandardError,
)
from gwascatalog.sumstatlib.snp.sumstat_types import (
    EffectAlleleFrequency,
    OtherAllele,
    RefAlleleField,
    RsID,
    SNPEffectAllele,
    VariantId,
)
from pydantic import BaseModel


class SNPSumStat(BaseModel):
    """A single row in a SNP summary statistics table."""

    chromosome: Chromosome
    base_pair_location: BasePairLocation
    effect_allele: SNPEffectAllele
    other_allele: OtherAllele
    beta: Beta | None
    odds_ratio: OddsRatio | None
    hazard_ratio: HazardRatio | None
    standard_error: StandardError | None
    effect_allele_frequency: EffectAlleleFrequency
    p_value: PValue | None
    neg_log_10_p_value: NegLog10pValue | None
    variant_id: VariantId | None
    rsid: RsID | None
    info: Info | None
    ci_lower: ConfidenceIntervalLower | None
    ci_upper: ConfidenceIntervalUpper | None
    ref_allele: RefAlleleField | None
    n: SampleSizePerVariant | None
