import pytest
from pydantic import ValidationError

from gwascatalog.sumstatlib.cnv.models import CNVSumstatModel

# these test cases only cover model specific validation

test_cases = [
    # Valid input
    (
        {
            "chromosome": 1,
            "base_pair_start": 1,
            "base_pair_end": 2000,
            "effect_direction": "positive",
            "p_value": 0.2,
            "model_type": "additive",
            "n": 2,
        },
        {"assembly": "GRCh38"},
        None,
    ),
    # base_pair_end < base_pair_start
    (
        {
            "chromosome": "X",
            "base_pair_start": 1000,
            "base_pair_end": 1,
            "effect_direction": "positive",
            "p_value": 0.2,
            "model_type": "additive",
            "n": 2,
        },
        {"assembly": "GRCh38"},
        "base_pair_end must be greater than base_pair_start",
    ),
    # missing context
    (
        {
            "chromosome": "X",
            "base_pair_start": 1000,
            "base_pair_end": 1,
            "effect_direction": "positive",
            "p_value": 0.2,
            "model_type": "additive",
            "n": 2,
        },
        {},
        "genome assembly must be provided via validation context",
    ),
]


@pytest.mark.parametrize("input_data,context,expected_error", test_cases)
def test_cnvmodel(input_data, context, expected_error):
    if expected_error is None:
        model = CNVSumstatModel.model_validate(input_data, context=context)
        # simple check now that the model initialised
        assert (
            model.cnv_id
            == f"{input_data['chromosome']}:{input_data['base_pair_start']}"
            f"-{input_data['base_pair_end']}:"
            f"{context['assembly']}"
        )
    else:
        with pytest.raises(ValidationError) as exc_info:
            CNVSumstatModel.model_validate(input_data, context=context)

        # Check that the error string contains the expected snippet
        assert expected_error in str(exc_info.value)
