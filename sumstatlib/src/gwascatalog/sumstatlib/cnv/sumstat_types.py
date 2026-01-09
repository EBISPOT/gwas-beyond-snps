from __future__ import annotations

from typing import Annotated

from pydantic import Field

BasePairStart = Annotated[
    int,
    Field(
        description="The start position of the CNV, using the "
        "coordinate system declared",
        ge=0,
    ),
]

BasePairEnd = Annotated[
    int,
    Field(
        description="The end position of the CNV, using the coordinate system declared",
        ge=0,
    ),
]
