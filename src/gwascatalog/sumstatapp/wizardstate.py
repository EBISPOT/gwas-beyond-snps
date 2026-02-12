from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from gwascatalog.sumstatlib.core.metadata_enums import GeneticVariationType
from gwascatalog.sumstatlib.core.sumstat_enums import GenomeAssembly


@dataclass
class WizardState:
    variation_type: GeneticVariationType
    input_sumstat_path: Path
    assembly: GenomeAssembly | None = None
    allow_zero_p_value: bool = False
