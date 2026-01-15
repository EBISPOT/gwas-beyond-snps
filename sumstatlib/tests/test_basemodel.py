import pytest
from pydantic import ValidationError

from gwascatalog.sumstatlib.core.models import BaseSumstatModel

test_cases = [
    # valid p-value
    (
        {"p_value": 0.000001, "neg_log10_p_value": None},
        {"allow_zero_pvalues": False},
        None,
    ),
    # valid zero p-value (with context)
    (
        {"p_value": 0.0, "neg_log10_p_value": None},
        {"allow_zero_pvalues": True},
        None,
    ),
    # valid p-value with empty context (default false)
    ({"p_value": 0.1, "neg_log10_p_value": None}, {}, None),
    # valid neg_log_10_p_value with empty context (default false)
    ({"p_value": None, "neg_log10_p_value": 0.1}, {}, None),
    # validation error: both p-values present
    (
        {"p_value": 0.001, "neg_log10_p_value": 123},
        {"allow_zero_pvalues": False},
        "(not both)",
    ),
    # validation error: both p-values missing
    (
        {"p_value": None, "neg_log10_p_value": None},
        {},
        "Missing p-value and negative log-10 p-value",
    ),
    # validation error: zero value in p-value
    (
        {"p_value": 0.0, "neg_log10_p_value": None},
        {"allow_zero_pvalues": False},
        "Zero p-values are not allowed",
    ),
    # validation error: empty context (default false)
    (
        {"p_value": 0.0, "neg_log10_p_value": None},
        {},
        "Zero p-values are not allowed",
    ),
]


@pytest.mark.parametrize("input_data,context,expected_error", test_cases)
def test_basemodel(input_data, context, expected_error):
    if expected_error is None:
        model = BaseSumstatModel.model_validate(input_data, context=context)
        # simple check now that the model initialised
        assert list(model.__class__.model_fields.keys()) == [
            "p_value",
            "neg_log10_p_value",
        ]
    else:
        with pytest.raises(ValidationError) as exc_info:
            BaseSumstatModel.model_validate(input_data, context=context)

        # Check that the error string contains the expected snippet
        assert expected_error in str(exc_info.value)
