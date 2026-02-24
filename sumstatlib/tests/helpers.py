import random

import pytest
from pydantic import TypeAdapter, ValidationError


# reusable type test function
def run_type_validation_test(type_to_test, input_data, expected_error):
    adapter = TypeAdapter(type_to_test)
    if expected_error is None:
        _ = adapter.validate_python(input_data)
        # exceptions will be raised by validate_python
    else:
        with pytest.raises(ValidationError) as exc_info:
            adapter.validate_python(input_data)
        assert expected_error in str(exc_info.value)


def make_cnv_sumstat_row():
    chromosome = random.randint(1, 25)
    base_pair_start = random.randint(1, 100_000)
    base_pair_end = random.randint(200_000, 300_000)
    beta = random.random()
    standard_error = random.random()
    neg_log10_p_value = random.random()
    effect_direction = "positive"
    model_type = "additive"
    n = random.randint(1, 100_000)
    return {
        "chromosome": chromosome,
        "base_pair_start": base_pair_start,
        "base_pair_end": base_pair_end,
        "beta": beta,
        "standard_error": standard_error,
        "neg_log10_p_value": neg_log10_p_value,
        "effect_direction": effect_direction,
        "model_type": model_type,
        "n": n,
    }
