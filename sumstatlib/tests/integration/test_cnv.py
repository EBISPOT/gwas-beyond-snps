import csv
import pathlib

import pytest

from gwascatalog.sumstatlib import (
    CNVSumstatModel,
    GenomeAssembly,
    SumstatConfig,
    SumstatTable,
)
from tests.test_sumstattable import make_cnv_sumstat_row

N_BIG_FILE_ROWS = 25_000_000


@pytest.fixture
def big_sumstat_file():
    return (make_cnv_sumstat_row() for _ in range(N_BIG_FILE_ROWS))


@pytest.mark.parametrize(
    "cnv_file",
    [
        pathlib.Path(__file__).parent / "data" / "cnv.txt",
        pathlib.Path(__file__).parent / "data" / "cnv_alias.txt",
    ],
)
def test_validated_cnv(tmp_path, cnv_file):
    """Read, validate, and write a CNV sumstat file using high level library calls"""
    config = SumstatConfig(
        assembly=GenomeAssembly.GRCH38,
        allow_zero_p_values=False,
        primary_effect_size="beta",
    )
    table = SumstatTable(
        config=config, input_path=cnv_file, data_model=CNVSumstatModel, min_records=5
    )

    out_path = tmp_path / "sumstat.tsv"
    with table.open_writer(output_path=out_path) as writer:
        writer.run()
        writer.commit()

    # check the output fields
    with out_path.open(mode="rt") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            _ = int(row["chromosome"])  # ValueError not raised, remap correct
            assert row["base_pair_start"] < row["base_pair_end"]
            _ = float(row["beta"])
            _ = float(row["standard_error"])
            assert float(row["n"]).is_integer()
            _ = float(row["neg_log10_p_value"])
            assert row["extra_test_field"] == "test"
