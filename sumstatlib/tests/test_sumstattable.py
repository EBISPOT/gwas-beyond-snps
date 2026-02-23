import csv
import random
from pathlib import Path

import pytest

from gwascatalog.sumstatlib import (
    CNVSumstatModel,
    SumstatConfig,
    SumstatTable,
    ValidatedRow,
)
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
            writer.commit()

        assert output.exists()
        assert writer.is_committed

    def test_commit_creates_gzip_output(self, cnv_table, tmp_path):
        output = tmp_path / "output.tsv.gz"
        with cnv_table.open_writer(output) as writer:
            for _ in writer:
                pass
            writer.commit()

        assert output.exists()
        # Verify it's actually gzip by reading magic bytes
        with output.open("rb") as f:
            assert f.read(2) == b"\x1f\x8b"

    def test_commit_output_has_correct_row_count(self, cnv_table, cnv_n_rows, tmp_path):
        output = tmp_path / "output.tsv"
        with cnv_table.open_writer(output) as writer:
            for _ in writer:
                pass
            writer.commit()

        # Count data rows in the output (subtract 1 for header)
        with output.open(encoding="utf-8") as f:
            n_lines = sum(1 for _ in f) - 1  # -1 for header
        assert n_lines == cnv_n_rows

    def test_double_commit_raises(self, cnv_table, tmp_path):
        output = tmp_path / "output.tsv"
        with (
            cnv_table.open_writer(output) as writer,
            pytest.raises(RuntimeError, match="Already committed"),
        ):
            for _ in writer:
                pass
            writer.commit()
            writer.commit()


class TestWriterRollback:
    """Writer cleans up temp file if not committed."""

    def test_no_commit_no_output(self, cnv_table, tmp_path):
        output = tmp_path / "output.tsv"
        with cnv_table.open_writer(output) as writer:
            for _ in writer:
                pass
            # deliberately no commit()

        assert not output.exists()

    def test_temp_file_deleted_on_exit(self, cnv_table, tmp_path):
        output = tmp_path / "output.tsv"
        tmp_file = output.parent / (output.name + ".tmp")
        with cnv_table.open_writer(output) as writer:
            for _ in writer:
                pass
            # tmp file exists while context is open
            # (don't assert — may have been written or not)

        # After context exit without commit, temp file is gone
        assert not tmp_file.exists()

    def test_temp_file_deleted_on_exception(self, cnv_table, tmp_path):
        output = tmp_path / "output.tsv"
        tmp_file = output.parent / (output.name + ".tmp")
        with (
            pytest.raises(RuntimeError, match="boom"),
            cnv_table.open_writer(output) as writer,
        ):
            for row in writer:
                if row.row_number == 5:
                    raise RuntimeError("boom")

        assert not output.exists()
        assert not tmp_file.exists()


class TestWriterProgress:
    """Writer yields ValidatedRow for every row and tracks counts."""

    def test_yields_validated_rows(self, cnv_table, cnv_n_rows, tmp_path):
        output = tmp_path / "output.tsv"
        results = []
        with cnv_table.open_writer(output) as writer:
            for row in writer:
                assert isinstance(row, ValidatedRow)
                results.append(row)
            writer.commit()

        assert len(results) == cnv_n_rows
        assert all(r.is_valid for r in results)

    def test_rows_processed_count(self, cnv_table, cnv_n_rows, tmp_path):
        output = tmp_path / "output.tsv"
        with cnv_table.open_writer(output) as writer:
            for _ in writer:
                pass
            assert writer.rows_processed == cnv_n_rows
            writer.commit()

    def test_valid_count(self, cnv_table, cnv_n_rows, tmp_path):
        output = tmp_path / "output.tsv"
        with cnv_table.open_writer(output) as writer:
            writer.run()
            assert writer.valid_count == cnv_n_rows
            writer.commit()


class TestWriterErrors:
    """Writer handles invalid rows and reports errors."""

    def test_mixed_valid_invalid(self, mixed_cnv_table, tmp_path):
        """When validation fails, don't commit the output file."""
        output = tmp_path / "output.tsv"
        valid_rows = []
        invalid_rows = []
        with (
            pytest.raises(RuntimeError, match="Cannot commit: validation failed"),
            mixed_cnv_table.open_writer(output) as writer,
        ):
            for row in writer:
                if row.is_valid:
                    valid_rows.append(row)
                else:
                    invalid_rows.append(row)
            writer.commit()

        assert not output.exists()

    def test_commit_with_no_valid_rows_raises(self, tmp_path):
        bad_file = make_mixed_csv_file(
            tmp_path / "only_bad.csv", n_valid=0, n_invalid=100_001
        )

        table = SumstatTable(
            data_model=CNVSumstatModel,
            input_path=bad_file,
            config=CNV_CONFIG,
        )

        output = tmp_path / "output.tsv"
        with (
            pytest.raises(ValueError, match="First row failed validation"),
            table.open_writer(output) as writer,
        ):
            writer.run()
            writer.commit()

    def test_writer_without_context_manager_raises(self, cnv_table, tmp_path):
        output = tmp_path / "output.tsv"
        writer = cnv_table.open_writer(output)
        with pytest.raises(TypeError, match="context manager"):
            next(iter(writer))
