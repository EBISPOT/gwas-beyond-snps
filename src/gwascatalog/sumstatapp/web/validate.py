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

import contextlib
import csv
import gzip
import io
import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import ValidationError

from gwascatalog.sumstatlib import CNVSumstatModel, GeneSumstatModel

if TYPE_CHECKING:
    from typing import Any

logger = logging.getLogger(__name__)

# Maximum number of errors to collect before stopping (fail fast, but show a batch)
MAX_DISPLAY_ERRORS = 200

# VFS paths for temporary files (kept compressed to halve in-memory VFS usage)
_UPLOAD_PATH = Path("/tmp/sumstat_upload")
_OUTPUT_PATH = Path("/tmp/sumstat_validated.tsv.gz")


# ── Validation helpers ────────────────────────────────────────────


def _detect_delimiter(first_line: str) -> str:
    """Guess delimiter from the first line of a file."""
    return "\t" if first_line.count("\t") >= first_line.count(",") else ","


def _is_gzip(path: Path) -> bool:
    """Check whether *path* starts with the gzip magic bytes."""
    with path.open("rb") as f:
        return f.read(2) == b"\x1f\x8b"


@contextlib.contextmanager
def _open_input(path: Path):  # noqa: ANN202
    """Open an uploaded file for text reading, decompressing if gzip."""
    fh = (
        gzip.open(path, "rt", encoding="utf-8")  # noqa: SIM115
        if _is_gzip(path)
        else path.open("r", encoding="utf-8")
    )
    try:
        yield fh
    finally:
        fh.close()


@contextlib.contextmanager
def _open_output(path: Path):  # noqa: ANN202
    """Open a gzip-compressed text file for writing."""
    gz = gzip.open(path, "wb")  # noqa: SIM115
    tw = io.TextIOWrapper(gz, encoding="utf-8", newline="")
    try:
        yield tw
    finally:
        tw.close()


def _get_model_class(variation_type: str) -> type:
    """Return the correct Pydantic model class for the variation type."""
    match variation_type:
        case "CNV":
            return CNVSumstatModel
        case "GENE":
            return GeneSumstatModel
        case _:
            raise ValueError(f"Unsupported variation type: {variation_type}")


def _build_context(config: dict[str, Any]) -> dict[str, Any]:
    """Build Pydantic validation context from wizard config."""
    context: dict[str, Any] = {}

    if config.get("allowZeroPvalues"):
        context["allow_zero_pvalues"] = True

    match config.get("variationType"):
        case "CNV":
            assembly = config.get("assembly")
            if not assembly:
                raise ValueError("Genome assembly is required for CNV data")
            context["assembly"] = assembly
        case "GENE":
            effect = config.get("effectSize")
            context["primary_effect_size"] = (
                effect if effect and effect != "none" else "beta"
            )

    return context


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
    try:
        config = json.loads(config_json)

        variation_type = config.get("variationType")
        if not variation_type:
            raise ValueError("No variation type selected")

        if not _UPLOAD_PATH.exists():
            raise ValueError("No file uploaded")

        if _UPLOAD_PATH.stat().st_size == 0:
            raise ValueError("File is empty")

        model_class = _get_model_class(variation_type)
        context = _build_context(config)

        errors: list[dict[str, Any]] = []
        valid_count = 0

        with _open_input(_UPLOAD_PATH) as infile, _open_output(_OUTPUT_PATH) as outfile:
            # Peek at first line to detect delimiter
            first_line = infile.readline()
            if not first_line.strip():
                raise ValueError("File is empty")
            infile.seek(0)

            delimiter = _detect_delimiter(first_line)
            reader = csv.DictReader(infile, delimiter=delimiter)

            writer: csv.DictWriter | None = None  # type: ignore[type-arg]

            for row_num, row in enumerate(reader, start=2):  # row 1 is header
                try:
                    validated = model_class.model_validate(row, context=context)
                    row_dict = validated.model_dump()

                    # Lazily initialise writer with field names from first valid row
                    if writer is None:
                        fieldnames = list(row_dict.keys())
                        writer = csv.DictWriter(
                            outfile,
                            fieldnames=fieldnames,
                            delimiter="\t",
                        )
                        writer.writeheader()

                    writer.writerow(row_dict)
                    valid_count += 1

                except ValidationError as exc:
                    for err in exc.errors():
                        loc = " → ".join(str(part) for part in err.get("loc", []))
                        msg = err.get("msg", str(err))
                        errors.append(
                            {
                                "row": row_num,
                                "message": f"[{loc}] {msg}" if loc else msg,
                            }
                        )

                    if len(errors) >= MAX_DISPLAY_ERRORS:
                        errors.append(
                            {
                                "row": 0,
                                "message": (
                                    f"… stopped after {MAX_DISPLAY_ERRORS} errors "
                                    f"(more may exist)"
                                ),
                            }
                        )
                        break

                except Exception as exc:
                    errors.append({"row": row_num, "message": str(exc)})

        # Always delete input file to free VFS memory
        if _UPLOAD_PATH.exists():
            _UPLOAD_PATH.unlink()

        # If no valid rows were written, remove the empty output file
        if valid_count == 0 and _OUTPUT_PATH.exists():
            _OUTPUT_PATH.unlink()

        return json.dumps(
            {
                "errorCount": len(errors),
                "errors": errors,
                "validRowCount": valid_count,
                "hasOutput": valid_count > 0,
            }
        )

    except Exception as exc:
        logger.exception("Validation failed")
        # Clean up on failure
        if _UPLOAD_PATH.exists():
            _UPLOAD_PATH.unlink()
        return json.dumps(
            {
                "errorCount": 1,
                "errors": [{"row": 0, "message": str(exc)}],
                "validRowCount": 0,
                "hasOutput": False,
            }
        )


# ── Module loaded ─────────────────────────────────────────────────
print("✅ Python validation module loaded")
