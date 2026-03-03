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
    cnvs = []
    # set the seed when generating the data
    random.seed(get_random_number())

    for i in range(200_000):
        cnvs.append(make_cnv_sumstat_row() | {"row_nr": i})

    cnv_file = tmp_path / "cnvs.txt"
    with cnv_file.open("wt") as f:
        writer = csv.DictWriter(f, fieldnames=cnvs[0].keys())
        writer.writeheader()
        writer.writerows(cnvs)

    return Path(cnv_file)


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
