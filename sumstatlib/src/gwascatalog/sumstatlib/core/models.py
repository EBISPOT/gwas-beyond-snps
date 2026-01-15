from __future__ import annotations

from typing import Self

from pydantic import BaseModel, model_validator
from pydantic_core.core_schema import ValidationInfo

from gwascatalog.sumstatlib.core.sumstat_types import NegLog10pValue, PValue


class BaseSumstatModel(BaseModel):
    """
    Base class for all summary statistic models (every sumstat needs one p-value).

    Validation context must be passed via model_validate(..., context=...)

    Validation context keys:
      - allow_zero_pvalues (bool, optional):
        If False, p_value == 0 or neg_log10_p_value == 0 is rejected.
        Defaults to False if not provided.
    """

    p_value: PValue | None = None
    neg_log10_p_value: NegLog10pValue | None = None

    @model_validator(mode="after")
    def validate_pvalues(self, info: ValidationInfo) -> Self:
        # grab the validation context if it exists
        allow_zero = (
            info.context.get("allow_zero_pvalues", False) if info.context else False
        )

        match (self.p_value, self.neg_log10_p_value):
            case (float() as value, None) | (None, float() as value):
                if not allow_zero and value == 0:
                    raise ValueError("Zero p-values are not allowed")
                return self

            case (None, None):
                raise ValueError("Missing p-value and negative log-10 p-value")

            case (float(), float()):
                raise ValueError(
                    "Please provide only one p-value or negative log-10 p-value "
                    "(not both)"
                )

            case _:
                raise ValueError(
                    f"Invalid p-values: {self.p_value=}, {self.neg_log10_p_value=}"
                )

    @property
    def is_neg_log_10_p_value(self):
        return self.neg_log10_p_value is not None
