import csv
from pathlib import Path

import pytest
from helpers import make_cnv_sumstat_row

from gwascatalog.sumstatlib import (
    CNVSumstatModel,
    SumstatConfig,
    SumstatTable,
    ValidatedRow,
)
from gwascatalog.sumstatlib.core.sumstat_enums import GenomeAssembly


def make_csv_file(out_path: Path, n_rows: int) -> Path:
    with out_path.open(mode="w", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=make_cnv_sumstat_row().keys())
        writer.writeheader()
        writer.writerows(make_cnv_sumstat_row() for _ in range(n_rows))
    return out_path


def make_mixed_csv_file(out_path: Path, n_valid: int, n_invalid: int) -> Path:
    """Create a CSV where some rows have invalid data (base_pair_end <
    base_pair_start)."""
    fieldnames = list(make_cnv_sumstat_row().keys())
    with out_path.open(mode="w", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for _ in range(n_valid):
            writer.writerow(make_cnv_sumstat_row())
        for _ in range(n_invalid):
            bad_row = make_cnv_sumstat_row()
            # Make base_pair_end <= base_pair_start to trigger validation error
            bad_row["base_pair_start"] = 300_000
            bad_row["base_pair_end"] = 100
            writer.writerow(bad_row)
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


# ── Writer tests ──────────────────────────────────────────────────


CNV_CONFIG = SumstatConfig(
    **{
        "primary_effect_size": "beta",
        "allow_zero_p_values": False,
        "assembly": GenomeAssembly.GRCH38,
    }
)


@pytest.fixture
def cnv_table(cnv_sumstat_file) -> SumstatTable:
    return SumstatTable(
        data_model=CNVSumstatModel,
        input_path=cnv_sumstat_file,
        config=CNV_CONFIG,
    )


@pytest.fixture
def mixed_cnv_file(tmp_path) -> Path:
    """A file with 100_001 valid rows + 50 invalid rows."""
    return make_mixed_csv_file(tmp_path / "mixed.csv", n_valid=100_001, n_invalid=50)


@pytest.fixture
def mixed_cnv_table(mixed_cnv_file) -> SumstatTable:
    return SumstatTable(
        data_model=CNVSumstatModel,
        input_path=mixed_cnv_file,
        config=CNV_CONFIG,
    )


class TestWriterCommit:
    """Writer creates the output file only on commit."""

    def test_commit_creates_output_file(self, cnv_table, tmp_path):
        output = tmp_path / "output.tsv"
        with cnv_table.open_writer(output) as writer:
            for _ in writer:
                pass

            assert not writer.has_validation_failed

        assert output.exists()
        assert not cnv_table.has_validation_failed

    def test_commit_creates_gzip_output(self, cnv_table, tmp_path):
        output = tmp_path / "output.tsv.gz"
        with cnv_table.open_writer(output) as writer:
            for _ in writer:
                pass

        assert output.exists()
        # Verify it's actually gzip by reading magic bytes
        with output.open("rb") as f:
            assert f.read(2) == b"\x1f\x8b"

    def test_commit_output_has_correct_row_count(self, cnv_table, cnv_n_rows, tmp_path):
        output = tmp_path / "output.tsv"
        with cnv_table.open_writer(output) as writer:
            for _ in writer:
                pass

        # Count data rows in the output (subtract 1 for header)
        with output.open(encoding="utf-8") as f:
            n_lines = sum(1 for _ in f) - 1  # -1 for header
        assert n_lines == cnv_n_rows


class TestWriterProgress:
    """Writer yields ValidatedRow for every row and tracks counts."""

    def test_yields_validated_rows(self, cnv_table, cnv_n_rows, tmp_path):
        output = tmp_path / "output.tsv"
        results = []
        with cnv_table.open_writer(output) as writer:
            for row in writer:
                assert isinstance(row, ValidatedRow)
                results.append(row)

        assert len(results) == cnv_n_rows
        assert all(r.is_valid for r in results)

        with output.open(encoding="utf-8") as f:
            # check the first few column names are standardised
            written_fieldnames = csv.DictReader(f, delimiter="\t").fieldnames[:6]
            assert set(written_fieldnames).issubset(
                cnv_table.data_model.VALID_FIELD_NAMES
            )

    def test_rows_processed_count(self, cnv_table, cnv_n_rows, tmp_path):
        output = tmp_path / "output.tsv"
        with cnv_table.open_writer(output) as writer:
            for _ in writer:
                pass
            assert writer.rows_processed == cnv_n_rows

    def test_valid_count(self, cnv_table, cnv_n_rows, tmp_path):
        output = tmp_path / "output.tsv"
        with cnv_table.open_writer(output) as writer:
            writer.run()
            assert writer.valid_count == cnv_n_rows


class TestWriterErrors:
    """Writer handles invalid rows and reports errors."""

    def test_mixed_valid_invalid(self, mixed_cnv_table, tmp_path):
        output = tmp_path / "output.tsv"
        with mixed_cnv_table.open_writer(output) as writer:
            writer.run()

        assert writer.has_validation_failed
        assert not output.exists()

    def test_commit_with_no_valid_rows_raises(self, tmp_path):
        bad_file = make_mixed_csv_file(
            tmp_path / "only_bad.csv", n_valid=0, n_invalid=100_001
        )

        with pytest.raises(ValueError, match="The first row"):
            _ = SumstatTable(
                data_model=CNVSumstatModel,
                input_path=bad_file,
                config=CNV_CONFIG,
            )

    def test_writer_without_context_manager_raises(self, cnv_table, tmp_path):
        output = tmp_path / "output.tsv"
        writer = cnv_table.open_writer(output)
        with pytest.raises(TypeError, match="context manager"):
            next(iter(writer))
