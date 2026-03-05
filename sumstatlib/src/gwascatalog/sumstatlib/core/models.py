from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Annotated, Any, Literal, Self

from gwascatalog.sumstatlib._pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    PrivateAttr,
    model_validator,
)
from gwascatalog.sumstatlib.core.sumstat_types import (
    Beta,
    ConfidenceIntervalLower,
    ConfidenceIntervalUpper,
    HazardRatio,
    NegLog10pValue,
    OddsRatio,
    PValue,
    SampleSizePerVariant,
    StandardError,
    ZScore,
)

if TYPE_CHECKING:
    from gwascatalog.sumstatlib._pydantic import ValidationInfo


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

    model_config = ConfigDict(
        extra="allow",
        validate_by_name=True,
        validate_by_alias=True,
        serialize_by_alias=False,
        frozen=True,
    )

    p_value: Annotated[
        PValue | None,
        Field(
            default=None,
            validation_alias=AliasChoices("p", "p_value", "pvalue"),
            serialization_alias="p",
        ),
    ]
    neg_log10_p_value: Annotated[
        NegLog10pValue | None,
        Field(
            default=None,
            validation_alias=AliasChoices("neg_log10_p_value", "neg_log_10_p_value"),
            serialization_alias="neg_log10_p_value",
        ),
    ]

    # conditional fields which depend on each other
    z_score: Annotated[
        ZScore | None,
        Field(
            default=None,
            validation_alias=AliasChoices("z_score", "zscore", "z"),
            serialization_alias="z_score",
        ),
    ]
    odds_ratio: Annotated[
        OddsRatio | None,
        Field(
            default=None,
            validation_alias=AliasChoices("odds_ratio", "OR"),
            serialization_alias="odds_ratio",
        ),
    ]
    beta: Annotated[
        Beta | None,
        Field(
            default=None,
            validation_alias=AliasChoices("beta", "b"),
            serialization_alias="beta",
        ),
    ]
    hazard_ratio: Annotated[
        HazardRatio | None,
        Field(
            default=None,
            validation_alias=AliasChoices("hazard_ratio", "hr"),
            serialization_alias="hazard_ratio",
        ),
    ]
    standard_error: Annotated[
        StandardError | None,
        Field(
            default=None,
            validation_alias=AliasChoices("standard_error", "se"),
            serialization_alias="standard_error",
        ),
    ]

    confidence_interval_lower: Annotated[
        ConfidenceIntervalLower | None,
        Field(
            default=None,
            validation_alias=AliasChoices("confidence_interval_lower", "ci_lower"),
            serialization_alias="confidence_interval_lower",
        ),
    ]

    confidence_interval_upper: Annotated[
        ConfidenceIntervalUpper | None,
        Field(
            default=None,
            validation_alias=AliasChoices("confidence_interval_upper", "ci_upper"),
            serialization_alias="confidence_interval_upper",
        ),
    ]

    # optional fields
    n: Annotated[
        SampleSizePerVariant | None,
        Field(
            default=None, validation_alias=AliasChoices("n"), serialization_alias="n"
        ),
    ]

    # private attributes to avoid polluting the data model
    # adopting this pattern because metadata are provided by a payload or CLI flag at
    # runtime, so adding a field doesn't make sense
    _primary_effect_size: (
        Literal["beta", "z_score", "hazard_ratio", "odds_ratio"] | None
    ) = PrivateAttr()
    _allow_zero_pvalues: bool = PrivateAttr(default=False)

    def model_post_init(self, context: Any, /) -> None:
        self._allow_zero_pvalues = context.get("allow_zero_p_values", False)

        if "primary_effect_size" not in context:
            raise ValueError(
                "primary_effect_size must be provided via validation context"
            )
        self._primary_effect_size = context["primary_effect_size"]

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

    # pydantic model validation functions below
    @model_validator(mode="after")
    def check_p_values(self, info: ValidationInfo) -> Self:
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

            case _:  # pragma: no cover
                raise ValueError(
                    f"Invalid p-values: {self.p_value=}, {self.neg_log10_p_value=}"
                )

    @model_validator(mode="after")
    def se_mandatory_with_beta(self):
        """Standard error is mandatory if beta is set"""
        if self.beta is not None and self.standard_error is None:
            raise ValueError("Standard error is missing for beta")

        if self.beta is None and self.standard_error is not None:
            raise ValueError("Standard error requires beta to be set")

        return self

    @model_validator(mode="after")
    def check_confidence_interval(self) -> Self:
        lower = self.confidence_interval_lower
        upper = self.confidence_interval_upper

        # early return when there's no CI
        if self.odds_ratio is None and lower is None and upper is None:
            return self

        # Partial CI provided
        if lower is None or upper is None:
            raise ValueError(
                "confidence_interval_lower and confidence_interval_upper must be "
                "provided together"
            )

        # missing OR
        if self.odds_ratio is None:
            raise ValueError("Confidence interval provided but no odds ratio present")

        # Bound ordering
        if lower > upper:
            raise ValueError(
                "confidence_interval_lower must be <= confidence_interval_upper"
            )

        # Containment
        if not (lower <= self.odds_ratio <= upper):
            raise ValueError("Effect size must lie within the confidence interval")

        return self

    @model_validator(mode="after")
    def primary_effect_size_must_not_be_none(self):
        if self._primary_effect_size is not None:
            effect_size = getattr(self, self._primary_effect_size)
            if effect_size is None:
                raise ValueError(
                    f"Primary effect size {self._primary_effect_size} must not be None"
                )
        else:
            # no primary effect size provided
            count = sum(
                1
                for v in [self.beta, self.odds_ratio, self.hazard_ratio, self.z_score]
                if v is not None
            )
            if count > 1:
                raise ValueError(
                    "More than one effect size field is set no primary effect size"
                )

        return self
