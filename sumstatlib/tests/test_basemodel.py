import pytest
from pydantic import ValidationError

from gwascatalog.sumstatlib.core.models import BaseSumstatModel


# BaseSumstatModel is an abstract base class and shouldn't be directly instantiated
# implement a dummy concrete class to test p value handling
class DummySumstatModel(BaseSumstatModel):
    def validate_semantics(self) -> None:
        pass  # minimal implementation


# disallow should be default
disallow_context = {"allow_zero_pvalues": False, "primary_effect_size": None}
allow_context = {"allow_zero_pvalues": True, "primary_effect_size": None}

test_cases = [
    # valid p-value
    (
        {"p_value": 0.000001, "neg_log10_p_value": None},
        disallow_context,
        None,
    ),
    # valid zero p-value (with context)
    (
        {"p_value": 0.0, "neg_log10_p_value": None},
        allow_context,
        None,
    ),
    # validation error: both p-values present
    (
        {"p_value": 0.001, "neg_log10_p_value": 123},
        disallow_context,
        "(not both)",
    ),
    # validation error: both p-values missing
    (
        {"p_value": None, "neg_log10_p_value": None},
        disallow_context,
        "Missing p-value and negative log-10 p-value",
    ),
    # validation error: zero value in p-value
    (
        {"p_value": 0.0, "neg_log10_p_value": None},
        disallow_context,
        "Zero p-values are not allowed",
    ),
]


@pytest.mark.parametrize("input_data,context,expected_error", test_cases)
def test_basemodel(input_data, context, expected_error):
    if expected_error is None:
        model = DummySumstatModel.model_validate(input_data, context=context)
        # simple check now that the model initialised
        assert list(model.__class__.model_fields.keys()) == ['p_value', 'neg_log10_p_value', 'z_score', 'odds_ratio', 'beta', 'hazard_ratio', 'standard_error', 'confidence_interval_lower', 'confidence_interval_upper', 'n']
    else:
        with pytest.raises(ValidationError, match=expected_error):
            DummySumstatModel.model_validate(input_data, context=context)

