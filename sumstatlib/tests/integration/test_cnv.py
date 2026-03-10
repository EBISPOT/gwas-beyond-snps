import csv

from gwascatalog.sumstatlib import (
    CNVSumstatModel,
    GenomeAssembly,
    SumstatConfig,
    SumstatTable,
)


def check_cnv_structure(row):
    _ = int(row["chromosome"])  # ValueError not raised, remap correct
    assert int(row["base_pair_start"]) < int(row["base_pair_end"])
    _ = float(row["beta"])
    _ = float(row["standard_error"])
    assert float(row["n"]).is_integer()
    _ = float(row["neg_log10_p_value"])


def test_unsorted_input(tmp_path, cnv_file_with_rownums):
    """Validation should check the structure of CNVs and sort the output"""
    config = SumstatConfig(
        assembly=GenomeAssembly.GRCH38,
        allow_zero_p_values=False,
        primary_effect_size="beta",
    )

    table = SumstatTable(
        config=config,
        input_path=cnv_file_with_rownums,
        data_model=CNVSumstatModel,
    )

    out_path = tmp_path / "sumstat.tsv"
    writer = table.open_writer(output_path=out_path)
    writer.run()

    with cnv_file_with_rownums.open(mode="rt") as f:
        reader = csv.DictReader(f, delimiter=",")
        input_keys = [(int(r["chromosome"]), int(r["base_pair_start"])) for r in reader]
        # verify inputs are not sorted by genomic coordinates
        assert input_keys != sorted(input_keys)

    # verify outputs are sorted by genomic coordinates
    with out_path.open(mode="rt") as f:
        reader = csv.DictReader(f, delimiter="\t")

        prev_key = None
        seen_row_nrs = []

        for row in reader:
            # test the structure of each row
            check_cnv_structure(row)

            # check ordering is OK
            chromosome = int(row["chromosome"])
            start = int(row["base_pair_start"])
            key = (chromosome, start)

            if prev_key is not None:
                assert key >= prev_key, f"Output not sorted: {key} < {prev_key}"

            prev_key = key
            seen_row_nrs.append(int(row["row_nr"]))

        # verify no rows were lost or duplicated
        assert sorted(seen_row_nrs) == list(range(200_000))
