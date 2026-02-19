"""
validate.py — PyScript entry point for browser-based validation.

Runs inside Pyodide (Python compiled to WebAssembly).  Uses the Emscripten
virtual file system (VFS) for file I/O to minimise memory usage:

  1. JavaScript writes uploaded data to VFS in chunks via start_upload /
     write_chunk / finish_upload.
  2. validate_file() reads the VFS file row-by-row, validates each row,
     and streams valid rows to a new VFS file.
  3. JavaScript reads the validated file from VFS in chunks for download
     via get_output_size / read_output_chunk.

This design avoids holding the entire file in memory at once, keeping Wasm
heap usage well within the 4 GB limit even for ~1 GB input files.

Interface (all functions exposed on ``globalThis``):

  Chunked upload
    start_upload(filename)     → bool
    write_chunk(chunk)         → bool   (chunk is a JS Uint8Array)
    finish_upload()            → bool

  Validation
    validate_file(config_json) → JSON string   (errors only, no file content)

  Chunked download
    get_output_size()                → int
    read_output_chunk(offset, size)  → bytes  (call .toJs() on JS side)

  Cleanup
    cleanup()                  → bool

No direct DOM manipulation — all results are returned as structured data
for the JavaScript layer to display.
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
    from typing import Any, BinaryIO

logger = logging.getLogger(__name__)

# Maximum number of errors to collect before stopping (fail fast, but show a batch)
MAX_DISPLAY_ERRORS = 200

# VFS paths for temporary files (kept compressed to halve in-memory VFS usage)
_UPLOAD_PATH = Path("/tmp/sumstat_upload")
_OUTPUT_PATH = Path("/tmp/sumstat_validated.tsv.gz")

# Module-level state for chunked upload
_upload_fd: BinaryIO | None = None


# ── Chunked upload to VFS ─────────────────────────────────────────


def start_upload(filename: str) -> bool:
    """Begin a chunked file upload to the VFS.

    Opens a file for binary writing.  Subsequent ``write_chunk()`` calls
    append data.  Call ``finish_upload()`` when done.
    """
    global _upload_fd  # noqa: PLW0603

    # Clean up any previous session
    if _upload_fd is not None:
        _upload_fd.close()
    for path in (_UPLOAD_PATH, _OUTPUT_PATH):
        if path.exists():
            path.unlink()

    _upload_fd = _UPLOAD_PATH.open("wb")
    return True


def write_chunk(chunk: Any) -> bool:
    """Write a chunk of bytes to the upload file.

    Args:
        chunk: A JS ``Uint8Array`` (received as a Pyodide ``JsProxy``).
    """
    if _upload_fd is None:
        raise RuntimeError("No upload in progress — call start_upload() first")
    _upload_fd.write(chunk.to_py())
    return True


def finish_upload() -> bool:
    """Finalise the upload by closing the file."""
    global _upload_fd  # noqa: PLW0603
    if _upload_fd is not None:
        _upload_fd.close()
        _upload_fd = None
    return True


# ── Chunked download from VFS ─────────────────────────────────────


def get_output_size() -> int:
    """Return the byte size of the validated output file."""
    if not _OUTPUT_PATH.exists():
        return 0
    return _OUTPUT_PATH.stat().st_size


def read_output_chunk(offset: int, size: int) -> bytes:
    """Read a chunk of bytes from the validated output file.

    Args:
        offset: Byte offset to start reading from.
        size: Maximum number of bytes to read.

    Returns:
        ``bytes`` — the chunk data (returned as a ``PyProxy``; call
        ``.toJs()`` on the JS side to get a ``Uint8Array``).
    """
    with _OUTPUT_PATH.open("rb") as f:
        f.seek(offset)
        return f.read(size)


# ── Cleanup ───────────────────────────────────────────────────────


def cleanup() -> bool:
    """Remove temporary files from the VFS."""
    for path in (_UPLOAD_PATH, _OUTPUT_PATH):
        if path.exists():
            path.unlink()
    return True


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


# ── Expose to JavaScript via globalThis ──────────────────────────
from js import globalThis  # type: ignore[import-untyped]  # noqa: E402

globalThis.start_upload = start_upload
globalThis.write_chunk = write_chunk
globalThis.finish_upload = finish_upload
globalThis.validate_file = validate_file
globalThis.get_output_size = get_output_size
globalThis.read_output_chunk = read_output_chunk
globalThis.cleanup = cleanup

print("✅ Python environment loaded — sumstatlib ready")
