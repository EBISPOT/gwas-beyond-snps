import csv
import gzip
import shutil
import sys
from pathlib import Path

import pytest


@pytest.fixture
def invalid_test_cnv_file(tmp_path):
    cnv_test_path = tmp_path / "invalid_cnv.csv"
    test_cnv_file = (
        Path(__file__).parent.parent.parent
        / "src"
        / "gwascatalog"
        / "sumstatapp"
        / "web"
        / "static"
        / "examples"
        / "invalid-cnv.csv"
    )
    return shutil.copyfile(test_cnv_file, cnv_test_path)


@pytest.fixture
def valid_cnv_output_columns():
    return [
        "chromosome",
        "base_pair_start",
        "base_pair_end",
        "cnv_id",
        "neg_log10_p_value",
        "beta",
        "standard_error",
        "statistical_model_type",
        "extra_test_column",
    ]


@pytest.fixture
def invalid_cnv_errors():
    return {
        ("0", "chromosome", "Field required"),
        (
            "0",
            "base_pair_end",
            "Input should be a valid integer, unable to parse string as an integer",
        ),
        (
            "1",
            "standard_error",
            "Input should be a valid number, unable to parse string as a number",
        ),
        ("1", "chromosome", "Field required"),
    }


@pytest.fixture
def valid_test_cnv_file(tmp_path):
    cnv_test_path = tmp_path / "valid_cnv.csv"
    test_cnv_file = (
        Path(__file__).parent.parent.parent
        / "src"
        / "gwascatalog"
        / "sumstatapp"
        / "web"
        / "static"
        / "examples"
        / "valid-cnv.csv"
    )
    return shutil.copyfile(test_cnv_file, cnv_test_path)


def test_cli_cnv_valid(
    monkeypatch, valid_test_cnv_file, tmp_path, valid_cnv_output_columns
):
    in_path = valid_test_cnv_file
    out_dir = tmp_path / "test_cli_cnv_valid"
    out_dir.mkdir()

    args = [
        "gwascatalog",
        "beyondsnp",
        "validate",
        str(in_path),
        "--assembly",
        "GRCh38",
        "--type",
        "CNV",
        "--effect-size",
        "beta",
        "--output-dir",
        str(out_dir),
    ]

    # run the CLI
    monkeypatch.setattr(sys, "argv", args)
    from gwascatalog.sumstatapp.cli.__main__ import main

    main()

    # check the CLI ran OK
    out_path = out_dir / f"validated_{in_path.stem}.tsv.gz"
    assert out_path.exists()
    with gzip.open(out_path, mode="rt") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for i, row in enumerate(reader, start=1):
            assert list(row.keys()) == valid_cnv_output_columns
            assert row["extra_test_column"] == f"test{i}"


def test_cli_cnv_invalid(
    monkeypatch, invalid_test_cnv_file, tmp_path, invalid_cnv_errors
):
    in_path = invalid_test_cnv_file
    out_dir = tmp_path / "test_cli_cnv_valid"
    out_dir.mkdir()

    args = [
        "gwascatalog",
        "beyondsnp",
        "validate",
        str(in_path),
        "--assembly",
        "GRCh38",
        "--type",
        "CNV",
        "--effect-size",
        "beta",
        "--output-dir",
        str(out_dir),
    ]

    # run the CLI
    monkeypatch.setattr(sys, "argv", args)
    from gwascatalog.sumstatapp.cli.__main__ import main

    main()

    with (out_dir / f"{in_path.stem}.errors.tsv").open() as f:
        rows = set()
        for row in csv.DictReader(f, delimiter="\t"):
            rows.add(tuple(row.values()))
        assert rows == invalid_cnv_errors
