"""
validate.py — PyScript entry point for browser-based validation.

Runs inside Pyodide (Python compiled to WebAssembly). This module provides
a clean interface for validating GWAS summary statistics files, modelled on
the pandoc wasm app's approach (explicit function parameters, structured
return values, no DOM manipulation).

Interface:

    validate_file(file_text, config_json)

    - file_text is the raw text content of the summary statistics file.
    - config_json is a JSON string with keys:
        - variationType: "CNV" | "GENE"
        - assembly: "GRCh38" | "GRCh37" | ... (required for CNV)
        - effectSize: "beta" | "odds_ratio" | "z_score" | "none"
        - pValueType: "p_value" | "neg_log10"
        - allowZeroPvalues: bool

    Returns a JSON string with keys:
        - errorCount: number of validation errors found
        - errors: list of {row: int, message: str}
        - validRowCount: number of valid rows
        - output: TSV string of validated rows, or null

No direct DOM manipulation — all results are returned as structured data
for the JavaScript layer to display.
"""

from __future__ import annotations

import csv
import io
import json
import logging
from typing import Any

from pydantic import ValidationError

from gwascatalog.sumstatlib import CNVSumstatModel, GeneSumstatModel

logger = logging.getLogger(__name__)

# Maximum number of errors to collect before stopping (fail fast, but show a batch)
MAX_DISPLAY_ERRORS = 200


def _detect_delimiter(first_line: str) -> str:
    """Guess delimiter from the first line of a file."""
    return "\t" if first_line.count("\t") >= first_line.count(",") else ","


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


def validate_file(file_text: str, config_json: str) -> str:
    """Validate a summary statistics file.

    This is the main entry point, called from JavaScript via PyScript.
    Takes explicit parameters and returns a JSON result string — no
    globalThis reads, no DOM manipulation.

    Args:
        file_text: Raw text content of the uploaded file.
        config_json: JSON string with wizard configuration.

    Returns:
        JSON string with validation results.
    """
    try:
        config = json.loads(config_json)

        variation_type = config.get("variationType")
        if not variation_type:
            raise ValueError("No variation type selected")

        if not file_text or not file_text.strip():
            raise ValueError("File is empty")

        model_class = _get_model_class(variation_type)
        context = _build_context(config)

        lines = file_text.strip().split("\n")
        if len(lines) < 2:
            raise ValueError("File must have a header row and at least one data row")

        delimiter = _detect_delimiter(lines[0])
        reader = csv.DictReader(io.StringIO(file_text), delimiter=delimiter)

        # Normalise headers
        if reader.fieldnames:
            reader.fieldnames = [
                h.strip().lower().replace(" ", "_") for h in reader.fieldnames
            ]

        errors: list[dict[str, Any]] = []
        valid_rows: list[dict[str, Any]] = []

        for row_num, row in enumerate(reader, start=2):  # row 1 is header
            try:
                validated_row = model_class.model_validate(row, context=context).model_dump()
                valid_rows.append(validated_row)
            except ValidationError as exc:
                for err in exc.errors():
                    loc = " → ".join(str(part) for part in err.get("loc", []))
                    msg = err.get("msg", str(err))
                    errors.append({
                        "row": row_num,
                        "message": f"[{loc}] {msg}" if loc else msg,
                    })

                if len(errors) >= MAX_DISPLAY_ERRORS:
                    errors.append({
                        "row": 0,
                        "message": (
                            f"… stopped after {MAX_DISPLAY_ERRORS} errors "
                            f"(more may exist)"
                        ),
                    })
                    break
            except Exception as exc:
                errors.append({"row": row_num, "message": str(exc)})

        # Build TSV output from valid rows
        output = None
        if valid_rows:
            buf = io.StringIO()
            fieldnames = list(valid_rows[0].keys())
            writer = csv.DictWriter(buf, fieldnames=fieldnames, delimiter="\t")
            writer.writeheader()
            writer.writerows(valid_rows)
            output = buf.getvalue()

        return json.dumps({
            "errorCount": len(errors),
            "errors": errors,
            "validRowCount": len(valid_rows),
            "output": output,
        })

    except Exception as exc:
        logger.exception("Validation failed")
        return json.dumps({
            "errorCount": 1,
            "errors": [{"row": 0, "message": str(exc)}],
            "validRowCount": 0,
            "output": None,
        })


# ── Expose to JavaScript via globalThis ──────────────────────────
from js import globalThis  # type: ignore[import-untyped]  # noqa: E402

globalThis.validate_file = validate_file

print("✅ Python environment loaded — sumstatlib ready")
