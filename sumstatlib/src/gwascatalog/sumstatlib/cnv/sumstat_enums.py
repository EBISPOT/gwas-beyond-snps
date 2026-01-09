from __future__ import annotations

from enum import StrEnum


class EffectDirection(StrEnum):
    """Direction in which the CNV affects a trait"""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    AMBIGUOUS = "ambiguous"


class ModelType(StrEnum):
    """Genetic association model type"""

    ADDITIVE = "additive"
    RECESSIVE = "recessive"
    DOMINANT = "dominant"
    DOSAGE_SENSITIVE = "dosage-sensitive"
