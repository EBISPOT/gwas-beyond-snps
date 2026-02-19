import pytest
from pydantic import ValidationError

from gwascatalog.sumstatlib.gene.models import GeneSumstatModel

# each test case is (input_data, context, expected_error, test_id)
test_cases = [
    # valid cases
    (
        {
            "ensembl_gene_id": "ENSG00000172183",
            "p_value": 0.0001,
        },
        {},
        None,
        "minimal_valid_ensembl_gene",
    ),
    (
        {
            "hgnc_symbol": "ISG20",
            "chromosome": 1,
            "base_pair_start": 2,
            "base_pair_end": 1000,
            "z_score": 1,
            "p_value": 0.0001,
        },
        {},
        None,
        "valid_hgnc_with_z_score",
    ),
    (
        {
            "ensembl_gene_id": "ENSG00000172183",
            "chromosome": 1,
            "base_pair_start": 2,
            "base_pair_end": 1000,
            "odds_ratio": 1,
            "p_value": 0.0001,
        },
        {},
        None,
        "valid_ensembl_with_odds_ratio",
    ),
    (
        {
            "hgnc_symbol": "ISG20",
            "chromosome": 1,
            "base_pair_start": 2,
            "base_pair_end": 1000,
            "z_score": 1,
            "p_value": 0.0001,
            "confidence_interval_upper": 2,
            "confidence_interval_lower": 0,
        },
        {},
        None,
        "valid_with_confidence_interval",
    ),
    # invalid cases
    (
        {
            "ensembl_gene_id": "ENSG00000172183",
            "hgnc_symbol": None,
            "z_score": None,
            "beta": 2,
            "odds_ratio": 1,
            "p_value": 0.0001,
        },
        {},
        "Provide only one value: z_score, odds_ratio, beta",
        "invalid_multiple_effect_sizes",
    ),
    (
        {
            "hgnc_symbol": "ISG20",
            "z_score": 3,
            "p_value": 0.0001,
            "confidence_interval_upper": 2,
            "confidence_interval_lower": 0,
        },
        {},
        "outside interval",
        "bad_confidence_interval",
    ),
    (
        {
            "hgnc_symbol": "ISG20",
            "z_score": 3,
            "p_value": 0.0001,
            "chromosome": 1,
            "base_pair_start": 1000,
            "base_pair_end": 100,
        },
        {},
        "base_pair_end must be greater than base_pair_start",
        "bad_location",
    ),
    (
        {
            "hgnc_symbol": "ISG20",
            "z_score": 3,
            "p_value": 0.0001,
            "base_pair_start": 1000,
            "base_pair_end": 100,
        },
        {},
        "Bad combination",
        "missing_chromosome",
    ),
]


@pytest.mark.parametrize(
    "input_data,context,expected_error,test_id",
    test_cases,
    ids=[tc[3] for tc in test_cases],
)
def test_genemodel(input_data, context, expected_error, test_id):
    if expected_error is None:
        _ = GeneSumstatModel.model_validate(input_data, context=context)
        assert True
    else:
        with pytest.raises(ValidationError) as exc_info:
            GeneSumstatModel.model_validate(input_data, context=context)
        assert expected_error in str(exc_info.value)
