from __future__ import annotations

import abc
from typing import Self

from pydantic import BaseModel, model_validator
from pydantic_core.core_schema import ValidationInfo

from gwascatalog.sumstatlib.core.sumstat_types import NegLog10pValue, PValue


class BaseSumstatModel(BaseModel, abc.ABC):
    """
    Abstract base class for all summary statistic models.

    When validating concrete classes a validation context must be passed via:

     model_validate(..., context=...)

    Validation context keys:
      - allow_zero_pvalues (bool, optional):
        If False, p_value == 0 or neg_log10_p_value == 0 is rejected.
        Defaults to False if not provided.
    """

    p_value: PValue | None = None
    neg_log10_p_value: NegLog10pValue | None = None

    @abc.abstractmethod
    def validate_semantics(self) -> None:
        """Does this data make sense in the context of the domain and the real world?

        Semantic validation is concerned with meaning (not structure). Pydantic only
        handles structural validation.

        Bioinformatics things you might want to check:

        - Does an ID exist in a reference DB? (e.g. HGNC symbol or GCST)
        - Is an rsID deprecated or merged?
        - Does a variant's position match in the reported genome build?
        - Does an ontology term match the reported phenotype?

        Note that doing semantic validation is probably out of scope for a lot of
        applications, and is currently done elsewhere (e.g. for SNPs the GWAS
        Catalog remapping pipeline checks rsIDs).

        Implementations must raise a ValueError when semantic validation fails.
        """
        # Subclasses must define this method, but it may do nothing (return None is OK)
        raise NotImplementedError

    @model_validator(mode="after")
    def validate_pvalues(self, info: ValidationInfo) -> Self:
        """
        Check that p-values are structurally OK and any zero values are valid
        """
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
    def is_neg_log_10_p_value(self) -> bool:
        """
        True if the model stores a negative log10 p-value instead of a raw p-value.
        """
        return self.neg_log10_p_value is not None
