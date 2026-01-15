from __future__ import annotations

from collections.abc import Mapping
from typing import Final

CHROMOSOME_MAP: Final[Mapping[str, int]] = {"X": 23, "Y": 24, "MT": 25}

# the column order of mandatory fields
CNV_FIELD_INDICES: Final[Mapping[str, int]] = {
    "chromosome": 0,
    "base_pair_start": 1,
    "base_pair_end": 2,
    "effect_allele": 3,
    "effect_direction": 4,
    "p_value": 5,
    "neg_log_10_pvalue": 5,
    "model_type": 6,
}
