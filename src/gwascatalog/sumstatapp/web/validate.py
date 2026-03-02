"""
validate.py — Python validation module for GWAS summary statistics.

Runs inside Pyodide (Python compiled to WebAssembly) in a Web Worker.
Loaded by ``validation-worker.js`` via ``pyodide.runPython()``.

The worker handles file I/O to the Emscripten VFS; this module only
needs to read/write files using standard ``pathlib``/``gzip`` APIs.

Data flow:

  1. Worker writes uploaded bytes to VFS at ``_UPLOAD_PATH``.
  2. ``validate_file()`` reads that file row-by-row, validates each row,
     and streams valid rows to ``_OUTPUT_PATH`` (gzip-compressed).
  3. Worker reads ``_OUTPUT_PATH`` and transfers it back to the main
     thread for download.

Interface:

  validate_file(config_json) → JSON string  (errors + counts, no file data)
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Literal, TypedDict

from gwascatalog.sumstatlib import (
    CNVSumstatModel,
    GeneSumstatModel,
    GenomeAssembly,
    SumstatConfig,
    SumstatTable,
)

# Detect Pyodide (WebAssembly) environment for progress reporting
try:
    import js  # type: ignore[import-not-found]
    from pyodide.ffi import to_js  # type: ignore[import-not-found]

    _IN_PYODIDE = True
except ImportError:
    _IN_PYODIDE = False


logger = logging.getLogger(__name__)

# Maximum number of errors to collect before stopping (fail fast, but show a batch)
MAX_DISPLAY_ERRORS = 200

# How often to post progress updates (in rows)
_PROGRESS_INTERVAL = 10_000

# VFS paths for temporary files (kept compressed to halve in-memory VFS usage)
_UPLOAD_PATH = Path("/tmp/sumstat_upload")
_OUTPUT_PATH = Path("/tmp/sumstat_validated.tsv.gz")


# ── Progress reporting ────────────────────────────────────────────


def _post_progress(
    *,
    rows_processed: int,
    valid_count: int,
    error_count: int,
    elapsed: float,
) -> None:
    """Post a progress message to the main thread (Pyodide only).

    In native Python this is a no-op.  In Pyodide the message is posted
    directly to the main thread via the Worker's ``postMessage()`` API,
    so the browser can update the UI while validation continues.
    """
    if not _IN_PYODIDE:
        return
    rate = rows_processed / elapsed if elapsed > 0 else 0
    msg = {
        "type": "progress",
        "rowsProcessed": rows_processed,
        "validCount": valid_count,
        "errorCount": error_count,
        "rowsPerSecond": round(rate),
        "elapsedSeconds": round(elapsed, 1),
    }
    js.postMessage(to_js(msg, dict_converter=js.Object.fromEntries))


# ── Validation helpers ────────────────────────────────────────────


def _get_model_class(
    variation_type: str,
) -> type[CNVSumstatModel] | type[GeneSumstatModel]:
    """Return the correct Pydantic model class for the variation type."""
    match variation_type:
        case "CNV":
            return CNVSumstatModel
        case "GENE":
            return GeneSumstatModel
        case _:
            raise ValueError(f"Unsupported variation type: {variation_type}")


def _get_validation_context(config: WizardConfig) -> SumstatConfig:
    """Build Pydantic validation context from wizard config."""
    allow_zero_p = config.get("allowZeroPvalues", False)

    if (asm := config.get("assembly", None)) is not None:
        assembly = GenomeAssembly(asm)
    else:
        assembly = None

    primary_effect_size = config.get("primaryEffectSize", None)

    return SumstatConfig(
        allow_zero_p_values=allow_zero_p,
        assembly=assembly,
        primary_effect_size=primary_effect_size,
    )


class WizardConfig(TypedDict):
    variationType: Literal["CNV", "GENE"]
    primaryEffectSize: Literal["beta", "hazard_ratio", "odds_ratio"] | None
    allowZeroPvalues: bool
    assembly: str


# ── Main validation entry point ───────────────────────────────────


def validate_file(config_json: str) -> str:
    """Validate a summary statistics file already written to the VFS.

    Reads the uploaded file row-by-row, validates each row against the
    appropriate Pydantic model, and streams valid rows to an output file.
    The input file is deleted after validation completes (regardless of
    errors) to free VFS memory.

    Args:
        config_json: JSON string with wizard configuration.

    Returns:
        JSON string with validation results (errors only — no file content).
    """
    if not _UPLOAD_PATH.exists():
        raise ValueError("No file uploaded")

    if _UPLOAD_PATH.stat().st_size == 0:
        raise ValueError("File is empty")

    try:
        config = WizardConfig(**json.loads(config_json))
        variation_type = config.get("variationType")
        context = _get_validation_context(config)
        validation_model = _get_model_class(variation_type)
        start_time = time.monotonic()

        sumstat_table = SumstatTable(
            data_model=validation_model, input_path=_UPLOAD_PATH, config=context
        )
        rows_processed: int = 0
        valid_count: int = 0

        with sumstat_table.open_writer(_OUTPUT_PATH) as writer:
            # __iter__ is responsible for side effects (writing out the new file)
            for row in writer:
                rows_processed += 1
                if row.is_valid:
                    valid_count += 1
                if rows_processed % _PROGRESS_INTERVAL == 0:
                    _post_progress(
                        rows_processed=rows_processed,
                        valid_count=valid_count,
                        error_count=len(sumstat_table.errors),
                        elapsed=time.monotonic() - start_time,
                    )

        has_output = valid_count > 0 and not sumstat_table.has_validation_failed
        elapsed = time.monotonic() - start_time
        rate = rows_processed / elapsed if elapsed > 0 else 0

        # Compute MD5 checksum of the validated output file
        md5_checksum: str | None = None
        if has_output and _OUTPUT_PATH.exists():
            md5 = hashlib.md5()
            with _OUTPUT_PATH.open("rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    md5.update(chunk)
            md5_checksum = md5.hexdigest()

        # Transform errors: SumstatError uses 'msg' key, but the JS
        # front-end expects 'message'.
        errors_for_display = [
            {"row": e["row"], "message": e["msg"]} for e in sumstat_table.errors
        ]

        return json.dumps(
            {
                "errorCount": len(sumstat_table.errors),
                "errors": errors_for_display,
                "validRowCount": valid_count,
                "hasOutput": has_output,
                "md5Checksum": md5_checksum,
                "elapsedSeconds": round(elapsed, 1),
                "rowsPerSecond": round(rate),
            }
        )
    except Exception as exc:
        logger.exception("Validation failed")
        return json.dumps(
            {
                "errorCount": 1,
                "errors": [{"row": 0, "message": str(exc)}],
                "validRowCount": 0,
                "hasOutput": False,
            }
        )
    finally:
        # Always delete input file to free VFS memory
        _UPLOAD_PATH.unlink()


# ── Module loaded ─────────────────────────────────────────────────
print("✅ Python validation module loaded")
