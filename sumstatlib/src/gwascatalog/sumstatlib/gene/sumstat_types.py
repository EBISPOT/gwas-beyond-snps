from __future__ import annotations

from typing import Annotated

from gwascatalog.sumstatlib._pydantic import Field, StringConstraints

# reject lowercase letters and any punctuation
# reject hyphens at the start and end of a symbol
hgnc_regex = r"^[A-Z0-9]+(?:-[A-Z0-9]+)*$"

HGNCGeneSymbol = Annotated[
    str,
    StringConstraints(pattern=hgnc_regex),
    Field(
        description="HGNC symbol",
        examples=["ISG20", "A2M", "A4GALT", "HLA-DRA", "MT-ND1"],
    ),
]

# human ensembl gene IDs:
# ENS
# no species prefix
# G: feature type prefix (genes)
# 11 digits
ensembl_regex = r"^ENSG\d{11}"
EnsemblGeneID = Annotated[
    str,
    StringConstraints(min_length=15, max_length=15, pattern=ensembl_regex),
    Field(
        description="Ensembl gene identifier",
        examples=["ENSG00000172183", "ENSG00000219481"],
    ),
]
