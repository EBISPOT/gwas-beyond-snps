import pytest
from helpers import run_type_validation_test

from gwascatalog.sumstatlib.cnv.sumstat_types import (
    EffectDirectionField,
    ModelTypeField,
)

effect_direction_test_cases = [
    ("positive", None),
    ("negative", None),
    ("ambiguous", None),
    ("howdy", "Input should be"),
    (0, "Input should be"),
    (None, "Input should be"),
]


@pytest.mark.parametrize("input_data,expected_error", effect_direction_test_cases)
def test_effect_direction_field(input_data, expected_error):
    run_type_validation_test(EffectDirectionField, input_data, expected_error)


model_type_test_cases = [
    ("additive", None),
    ("recessive", None),
    ("dominant", None),
    ("dosage-sensitive", None),
    ("howdy", "Input should be"),
    (0, "Input should be"),
    (None, "Input should be"),
]


@pytest.mark.parametrize("input_data,expected_error", model_type_test_cases)
def test_model_type_field(input_data, expected_error):
    run_type_validation_test(ModelTypeField, input_data, expected_error)
