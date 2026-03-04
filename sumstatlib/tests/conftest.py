import csv
import random
from pathlib import Path

import pytest


def get_random_number():
    return 4  # chosen by a fair dice roll. Guaranteed to be random.


@pytest.fixture
def cnv_file_with_rownums(tmp_path) -> Path:
    """An unsorted CNV file with row numbers that reflect generation order

    (unsorted by genomic coordinates)."""
    cnv_file = tmp_path / "valid_cnvs.txt"
    return make_cnv_file(path=cnv_file, is_valid=True)


@pytest.fixture
def invalid_cnv_file(tmp_path) -> Path:
    cnv_file = tmp_path / "invalid_cnvs.txt"
    return make_cnv_file(path=cnv_file, is_valid=False, n_rows=200_000)


def make_cnv_file(path: Path, is_valid: bool, n_rows: int = 200_000) -> Path:
    random.seed(get_random_number())
    cnvs = (make_cnv_sumstat_row(valid=is_valid) | {"row_nr": i} for i in range(n_rows))
    fieldnames = make_cnv_sumstat_row().keys() | {"row_nr"}

    with path.open("wt") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cnvs)

    return path


def make_cnv_sumstat_row(valid=True):
    if valid:
        chromosome = random.randint(1, 25)
        base_pair_start = random.randint(1, 100_000)
        base_pair_end = random.randint(200_000, 300_000)
        beta = random.random()
        standard_error = random.random()
        neg_log10_p_value = random.random()
        model_type = model_types[random.randint(0, 2)]
        n = random.randint(1, 100_000)
    else:
        chromosome = random.randint(1, 28)
        base_pair_start = random.randint(1, 100_000)
        base_pair_end = random.randint(1, 300_000)
        beta = random.random() - 5
        standard_error = random.random()
        neg_log10_p_value = random.random()
        model_type = model_types[random.randint(0, 2)]
        n = random.randint(-100_000, 0)

    return {
        "chromosome": chromosome,
        "base_pair_start": base_pair_start,
        "base_pair_end": base_pair_end,
        "beta": beta,
        "standard_error": standard_error,
        "neg_log10_p_value": neg_log10_p_value,
        "model_type": model_type,
        "n": n,
    }


model_types = ["additive", "dominant", "recessive"]
