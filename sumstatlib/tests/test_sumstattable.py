import csv
import random
from pathlib import Path

import pytest

from gwascatalog.sumstatlib import CNVSumstatModel, SumstatTable
from gwascatalog.sumstatlib.core.sumstat_enums import GenomeAssembly


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


def make_csv_file(out_path: Path, n_rows: int) -> Path:
    with out_path.open(mode="w", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=make_cnv_sumstat_row().keys())
        writer.writeheader()
        writer.writerows(make_cnv_sumstat_row() for _ in range(n_rows))
    return out_path


@pytest.fixture
def small_cnv_sumstat_file(tmp_path):
    """Write a CNV sumstat file containing 10,000 rows"""
    out_path = tmp_path / "cnv_sumstat_file.csv"
    return make_csv_file(out_path, 10)


@pytest.fixture
def cnv_n_rows() -> int:
    return 100_001


@pytest.fixture
def cnv_sumstat_file(tmp_path, cnv_n_rows):
    """Write a CNV sumstat file containing 10,000 rows"""
    out_path = tmp_path / "cnv_sumstat_file.csv"
    return make_csv_file(out_path, cnv_n_rows)


def test_small_cnv_sumstat(small_cnv_sumstat_file):
    with pytest.raises(ValueError) as excinfo:
        SumstatTable(
            data_model=CNVSumstatModel,
            input_path=small_cnv_sumstat_file,
            config={
                "primary_effect_size": "beta",
                "allow_zero_p_values": False,
                "assembly": GenomeAssembly.GRCH38,
            },
        )
        assert "Not enough rows in file" in excinfo


@pytest.fixture
def important_cnv_fields():
    # a manually curated set of important CNV fields
    return [
        "chromosome",
        "base_pair_start",
        "base_pair_end",
        "beta",
        "standard_error",
        "cnv_id",
    ]


def test_cnv_sumstat(cnv_sumstat_file, cnv_n_rows, important_cnv_fields):
    table = SumstatTable(
        data_model=CNVSumstatModel,
        input_path=cnv_sumstat_file,
        config={
            "primary_effect_size": "beta",
            "allow_zero_p_values": False,
            "assembly": GenomeAssembly.GRCH38,
        },
    )

    assert table.n_rows == cnv_n_rows
    for i in table.validate_rows():
        assert all(x in i for x in important_cnv_fields)

    assert not table.has_validation_failed
