"""Worker function for validating a single summary statistics file.

Kept in a standalone module so it is importable (and therefore picklable)
by :class:`~concurrent.futures.ProcessPoolExecutor`.
"""

from __future__ import annotations

import csv
import hashlib
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from gwascatalog.sumstatlib import (
    CNVSumstatModel,
    GeneSumstatModel,
    GenomeAssembly,
    SumstatConfig,
    SumstatTable,
)

if TYPE_CHECKING:
    from gwascatalog.sumstatlib import SumstatError

logger = logging.getLogger(__name__)


# ── Result type ───────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class FileResult:
    """Outcome of validating a single file."""

    input_path: Path
    output_path: Path | None
    error_path: Path | None
    rows_processed: int
    valid_count: int
    error_count: int
    elapsed_seconds: float
    md5_checksum: str | None
    fatal_error: str | None


# ── Helpers ───────────────────────────────────────────────────────


def _get_model(variation_type: str) -> type[CNVSumstatModel] | type[GeneSumstatModel]:
    """Return the Pydantic model class for the given variation type."""
    match variation_type:
        case "CNV":
            return CNVSumstatModel
        case "GENE":
            return GeneSumstatModel
        case _:
            raise ValueError(f"Unsupported variation type: {variation_type}")


def _write_error_report(error_path: Path, errors: list[SumstatError]) -> None:
    """Write validation errors to a human-readable TSV file."""
    dict_errors = [dict(e) for e in errors]

    with error_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, delimiter="\t", fieldnames=["row", "column", "msg"])
        writer.writeheader()
        writer.writerows(dict_errors)


def _compute_md5(path: Path) -> str:
    """Compute the MD5 checksum of a file."""
    md5 = hashlib.md5(usedforsecurity=False)
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            md5.update(chunk)
    return md5.hexdigest()


# ── Main worker ───────────────────────────────────────────────────


def validate_file(
    input_path: str,
    output_dir: str,
    variation_type: str,
    assembly: str | None,
    primary_effect_size: Literal["beta", "odds_ratio", "hazard_ratio", "z_score"]
    | None,
    allow_zero_pvalues: bool,
) -> FileResult:
    """Validate a single summary statistics file and write results.

    All arguments use primitive types so the function can be dispatched to a
    :class:`~concurrent.futures.ProcessPoolExecutor` without pickling issues.

    Returns:
        A :class:`FileResult` summarising the outcome.
    """
    inp = Path(input_path)
    out_dir = Path(output_dir)
    output_path = out_dir / f"validated_{inp.stem}.tsv.gz"
    error_path = out_dir / f"{inp.stem}.errors.tsv"

    if output_path.exists():
        raise FileExistsError(output_path)
    if error_path.exists():
        raise FileExistsError(error_path)

    start = time.monotonic()

    try:
        model = _get_model(variation_type)
        config = SumstatConfig(
            allow_zero_p_values=allow_zero_pvalues,
            assembly=GenomeAssembly(assembly) if assembly else None,
            primary_effect_size=primary_effect_size,
        )

        table = SumstatTable(data_model=model, input_path=inp, config=config)

        rows_processed = 0
        valid_count = 0
        writer = table.open_writer(output_path, compress=True)

        for row in writer:
            rows_processed += 1
            if row.is_valid:
                valid_count += 1

        elapsed = time.monotonic() - start

        # ── Validation failed: write error report ────────────────
        if table.has_validation_failed:
            _write_error_report(error_path, table.errors)
            output_path.unlink(missing_ok=True)
            return FileResult(
                input_path=inp,
                output_path=None,
                error_path=error_path,
                rows_processed=rows_processed,
                valid_count=valid_count,
                error_count=len(table.errors),
                elapsed_seconds=round(elapsed, 2),
                md5_checksum=None,
                fatal_error=None,
            )

        # ── Validation passed: compute checksum ──────────────────
        md5: str | None = None
        if output_path.exists():
            md5 = _compute_md5(output_path)
            md5_file = output_path.with_suffix(output_path.suffix + ".md5")
            md5_file.write_text(f"{md5}  {output_path.name}\n", encoding="utf-8")

        return FileResult(
            input_path=inp,
            output_path=output_path,
            error_path=None,
            rows_processed=rows_processed,
            valid_count=valid_count,
            error_count=0,
            elapsed_seconds=round(elapsed, 2),
            md5_checksum=md5,
            fatal_error=None,
        )

    except Exception as exc:  # noqa: BLE001 — report all failures back to the caller
        elapsed = time.monotonic() - start
        logger.debug("Fatal error validating %s", inp.name, exc_info=True)
        return FileResult(
            input_path=inp,
            output_path=None,
            error_path=None,
            rows_processed=0,
            valid_count=0,
            error_count=0,
            elapsed_seconds=round(elapsed, 2),
            md5_checksum=None,
            fatal_error=str(exc),
        )
