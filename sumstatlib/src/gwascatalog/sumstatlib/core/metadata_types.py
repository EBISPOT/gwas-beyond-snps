"""
A limited set of metadata types for Pydantic models

Intentionally not comprehensive. Mostly useful for the application/CLI currently.
"""

from typing import Annotated

from pydantic import Field

from .metadata_enums import GeneticVariationType

GeneticVariationField = Annotated[
    GeneticVariationType,
    Field(
        description="What kind of genetic variation are you studying?",
        examples=["CNV", "GENE", "SNP"],
    ),
]
