import pytest
from helpers import run_type_validation_test

from gwascatalog.sumstatlib.gene.sumstat_types import (
    EnsemblGeneID,
    HGNCGeneSymbol,
    ZScore,
)

# Test cases for HGNCGeneSymbol
hgnc_symbol_test_cases = [
    ("SCAMP4", None),
    ("ISG20", None),
    ("STEAP3", None),
    ("scamp4", "String should match pattern"),
    ("my_favourite_gene", "String should match pattern"),
    ("_BAD_GENE_1", "String should match pattern"),
    ("BAD_GENE_2_", "String should match pattern"),
    (None, "Input should be a valid string"),
]


@pytest.mark.parametrize("input_data,expected_error", hgnc_symbol_test_cases)
def test_hgnc_symbol(input_data, expected_error):
    run_type_validation_test(HGNCGeneSymbol, input_data, expected_error)


ensembl_gene_id_test_cases = [
    ("ENSG00000172183", None),
    ("ENSG00000128886", None),
    ("STEAP3", "String should have at least 15 characters"),
    ("ensG00000128886", "String should match pattern"),
    (None, "Input should be a valid string"),
]


@pytest.mark.parametrize("input_data,expected_error", ensembl_gene_id_test_cases)
def test_ensembl_gene_id(input_data, expected_error):
    run_type_validation_test(EnsemblGeneID, input_data, expected_error)


z_score_test_cases = [
    (0, None),
    (1.0, None),
    (-1.0, None),
    ("howdy", "Input should be a valid number"),
    (None, "Input should be a valid number"),
]


@pytest.mark.parametrize("input_data,expected_error", z_score_test_cases)
def test_zscore(input_data, expected_error):
    run_type_validation_test(ZScore, input_data, expected_error)
