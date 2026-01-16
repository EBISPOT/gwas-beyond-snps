import pytest
from gwascatalog.sumstatlib.core.sumstat_types import (
    BasePairEnd,
    BasePairStart,
    Chromosome,
)
from helpers import run_type_validation_test

chromosome_test_cases = [
    ("1", None),
    (2, None),
    (25, None),
    # automatically recoded
    ("X", None),
    ("MT", None),
    # invalid cases
    ("XY", "Invalid chromosome"),
    ("howdy", "Invalid chromosome"),
    (None, "Invalid chromosome"),
    (26, "Input should be less than or equal to 25"),
    (-1, "Input should be greater than or equal to 1"),
]


@pytest.mark.parametrize("input_data,expected_error", chromosome_test_cases)
def test_chromosome(input_data, expected_error):
    run_type_validation_test(Chromosome, input_data, expected_error)


base_pair_cases = [
    (0, None),
    (1, None),
    (-1, "Input should be greater than or equal to 0"),
    ("test", "Input should be a valid integer"),
    (1.5, "Input should be a valid integer"),
    (None, "Input should be a valid integer"),
]


@pytest.mark.parametrize("input_data,expected_error", base_pair_cases)
def test_base_pair_start(input_data, expected_error):
    run_type_validation_test(BasePairStart, input_data, expected_error)


@pytest.mark.parametrize("input_data,expected_error", base_pair_cases)
def test_base_pair_end(input_data, expected_error):
    run_type_validation_test(BasePairEnd, input_data, expected_error)
