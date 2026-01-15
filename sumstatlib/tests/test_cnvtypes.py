import pytest
from pydantic import TypeAdapter, ValidationError

from gwascatalog.sumstatlib.cnv.sumstat_types import (
    CNVEffectAllele,
    EffectDirectionField,
    ModelTypeField,
)


# reusable type test function
def _run_type_validation_test(type_to_test, input_data, expected_error):
    adapter = TypeAdapter(type_to_test)
    if expected_error is None:
        result = adapter.validate_python(input_data)
        assert isinstance(result, str)
    else:
        with pytest.raises(ValidationError) as exc_info:
            adapter.validate_python(input_data)
        assert expected_error in str(exc_info.value)


# Test cases for CNVEffectAllele
cnv_effect_allele_test_cases = [
    ("CNV", None),
    ("CN123", None),
    ("CN=1", None),
    ("CN3,CN8,CN10", None),
    ("CNV123", "String should match pattern"),
    ("CN", "String should match pattern"),
    ("howdy", "String should match pattern"),
    (0, "Input should be"),
    (None, "Input should be"),
]


@pytest.mark.parametrize("input_data,expected_error", cnv_effect_allele_test_cases)
def test_cnv_effect_allele(input_data, expected_error):
    _run_type_validation_test(CNVEffectAllele, input_data, expected_error)


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
    _run_type_validation_test(EffectDirectionField, input_data, expected_error)


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
    _run_type_validation_test(ModelTypeField, input_data, expected_error)
