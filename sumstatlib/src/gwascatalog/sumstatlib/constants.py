from __future__ import annotations

from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from collections.abc import Mapping

# the maximum number of pydantic ValidationErrors that can be raised
# before terminating the validation process
MAX_VALIDATION_ERRORS = 100

CHROMOSOME_MAP: Final[Mapping[str, int]] = {"X": 23, "Y": 24, "MT": 25}

CNV_FIELD_INDEX_MAP: Final[Mapping[str, int]] = {
    "chromosome": 0,
    "base_pair_start": 1,
    "base_pair_end": 2,
    "cnv_length": 3,
    "cnv_id": 4,
    "p_value": 5,
    "neg_log10_p_value": 5,
    "beta": 6,
    "odds_ratio": 6,
    "z_score": 6,
    "standard_error": 7,
    "confidence_interval_lower": 8,
    "confidence_interval_upper": 9,
    "effect_direction": 10,
    "n": 11,
    "statistical_model_type": 12,
}

GENE_FIELD_INDEX_MAP: Final[Mapping[str, int]] = {
    "ensembl_gene_id": 0,
    "hgnc_symbol": 0,
    "p_value": 1,
    "neg_log10_p_value": 1,
    "beta": 2,
    "odds_ratio": 2,
    "z_score": 2,
    "standard_error": 3,
    "confidence_interval_lower": 4,
    "confidence_interval_upper": 5,
    "chromosome": 6,
    "base_pair_start": 7,
    "base_pair_end": 8,
    "n": 9,
}

# see decision docs for justification
MIN_GENE_RECORDS: Final[int] = 10_000
MIN_CNV_RECORDS: Final[int] = 100_000
