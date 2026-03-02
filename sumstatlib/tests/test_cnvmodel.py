import pytest
from pydantic import ValidationError

from gwascatalog.sumstatlib.cnv.models import CNVSumstatModel

# these test cases only cover model specific validation

validation_context = {"assembly": "GRCh38", "primary_effect_size": "beta", "allow_zero_p_values": False}
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
            "beta": 0.1,
            "standard_error": 0.01,
        },
        validation_context,
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
            "beta": 0.1,
            "standard_error": 0.01,
        },
        validation_context,
        "base_pair_end must be greater than base_pair_start",
    ),
    # missing primary effect size context
    (
        {
            "chromosome": "X",
            "base_pair_start": 1000,
            "base_pair_end": 1,
            "effect_direction": "positive",
            "p_value": 0.2,
            "model_type": "additive",
            "n": 2,
            "beta": 0.1,
            "standard_error": 0.01,
        },
        {},
        "primary_effect_size must be provided via validation context",
    ),
    # missing assembly context
    (
        {
            "chromosome": "X",
            "base_pair_start": 1000,
            "base_pair_end": 1,
            "effect_direction": "positive",
            "p_value": 0.2,
            "model_type": "additive",
            "n": 2,
            "beta": 0.1,
            "standard_error": 0.01,
        },
        {"primary_effect_size": "beta"},
        "genome_assembly must be provided via validation context",
    ),
    # primary effect size is set but missing
    (
        {
            "chromosome": "X",
            "base_pair_start": 1000,
            "base_pair_end": 1,
            "effect_direction": "positive",
            "p_value": 0.2,
            "model_type": "additive",
            "n": 2,
            "odds_ratio": 0.1,
            "confidence_interval_upper": 0.2,
            "confidence_interval_lower": 0.0,
        },
        {"primary_effect_size": "beta", "assembly": "GRCh38"},
        "Primary effect size beta must not be None",
    ),
    # standard error requires beta
    (
        {
            "chromosome": "X",
            "base_pair_start": 1000,
            "base_pair_end": 1,
            "effect_direction": "positive",
            "p_value": 0.2,
            "model_type": "additive",
            "n": 2,
            "odds_ratio": 0.1,
            "confidence_interval_upper": 0.2,
            "confidence_interval_lower": 0.0,
            "standard_error": 0.0
        },
        {"primary_effect_size": "beta", "assembly": "GRCh38"},
        "Standard error requires beta to be set",
    ),
    # CI requires odds ratio
    (
        {
            "chromosome": "X",
            "base_pair_start": 1000,
            "base_pair_end": 1,
            "effect_direction": "positive",
            "p_value": 0.2,
            "model_type": "additive",
            "n": 2,
            "beta": 0.1,
            "standard_error": 0.01,
            "confidence_interval_upper": 0.2,
            "confidence_interval_lower": 0.0,
        },
        {"primary_effect_size": "beta", "assembly": "GRCh38"},
        "Confidence interval provided but no odds ratio present",
    ),
    # bad CI bounds
    (
        {
            "chromosome": "X",
            "base_pair_start": 1000,
            "base_pair_end": 1,
            "effect_direction": "positive",
            "p_value": 0.2,
            "model_type": "additive",
            "n": 2,
            "beta": 0.1,
            "standard_error": 0.01,
            "odds_ratio": 0.001,
            "confidence_interval_upper": 0.2,
            "confidence_interval_lower": 0.1,
        },
        {"primary_effect_size": "beta", "assembly": "GRCh38"},
        "Effect size must lie within the confidence interval",
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
