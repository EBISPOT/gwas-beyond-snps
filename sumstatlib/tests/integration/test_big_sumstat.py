import time

import pytest

from gwascatalog.sumstatlib import CNVSumstatModel
from tests.test_sumstattable import make_cnv_sumstat_row

N_BIG_FILE_ROWS = 25_000_000


@pytest.fixture
def big_sumstat_file():
    return (make_cnv_sumstat_row() for _ in range(N_BIG_FILE_ROWS))


def test_pass(big_sumstat_file):
    start = time.perf_counter()
    i = 0
    for row in big_sumstat_file:
        i += 1
        _ = CNVSumstatModel.model_validate(
            row, context={"assembly": "GRCh38"}
        ).model_dump()

    end = time.perf_counter()
    print(f"{i} rows processed in {end - start} seconds ({i / end - start:0.2f})")
    assert True
