"""
validate.py — PyScript entry point for browser-based validation.

Runs inside Pyodide (Python compiled to WebAssembly). This module:

  1. Imports sumstatlib (installed as a wheel via pyscript.toml)
  2. Reads file content passed from JavaScript (globalThis._fileContent)
  3. Reads wizard configuration from JavaScript (globalThis.wizardState)
  4. Parses the file as CSV/TSV rows
  5. Validates each row with the appropriate Pydantic model
  6. Reports results back to JavaScript for display

No direct DOM manipulation — all UI updates go through JS helper functions
exposed on globalThis (displayValidationResults, displayValidationError, etc.).
"""

from __future__ import annotations

import csv
import io
import logging
from typing import Any

from pydantic import ValidationError

from gwascatalog.sumstatlib import CNVSumstatModel, GeneSumstatModel

logger = logging.getLogger(__name__)

# Maximum number of errors to display in the UI to avoid overwhelming the user
MAX_DISPLAY_ERRORS = 200

# Batch size for row processing (yield control back to browser)
ROW_BATCH_SIZE = 5000


def _detect_delimiter(first_line: str) -> str:
    """Guess delimiter from the first line of a file."""
    tab_count = first_line.count("\t")
    comma_count = first_line.count(",")
    return "\t" if tab_count >= comma_count else ","


def _build_validation_context(state: dict[str, Any]) -> dict[str, Any]:
    """Build the Pydantic validation context dict from wizard state."""
    context: dict[str, Any] = {}

    if state.get("allowZeroPvalues"):
        context["allow_zero_pvalues"] = True

    variation = state.get("variationType")

    if variation == "CNV":
        assembly = state.get("assembly")
        if not assembly:
            raise ValueError("Genome assembly is required for CNV data")
        context["assembly"] = assembly

    elif variation == "GENE":
        effect = state.get("effectSize")
        if effect and effect != "none":
            context["primary_effect_size"] = effect
        else:
            # Gene-based GWAS allows no effect size; default to beta for
            # the model context (the model tolerates missing values)
            context["primary_effect_size"] = "beta"

    return context


def _get_model_class(variation_type: str) -> type:
    """Return the correct Pydantic model class for the variation type."""
    match variation_type:
        case "CNV":
            return CNVSumstatModel
        case "GENE":
            return GeneSumstatModel
        case _:
            raise ValueError(f"Unsupported variation type: {variation_type}")


def _normalise_header(header: str) -> str:
    """Lowercase and strip whitespace from a column header."""
    return header.strip().lower().replace(" ", "_")


def validate_file() -> None:
    """Main validation entry point, called from JavaScript.

    Reads globalThis._fileContent (str) and globalThis.wizardState (JsProxy),
    validates rows, and calls globalThis.displayValidationResults with results.
    """
    from js import globalThis  # type: ignore[import-untyped]

    try:
        file_content: str = globalThis._fileContent
        js_state = globalThis.wizardState

        # Convert JsProxy to plain dict
        state = {
            "variationType": str(js_state.variationType) if js_state.variationType else None,
            "assembly": str(js_state.assembly) if js_state.assembly else None,
            "effectSize": str(js_state.effectSize) if js_state.effectSize else None,
            "pValueType": str(js_state.pValueType) if js_state.pValueType else None,
            "allowZeroPvalues": bool(js_state.allowZeroPvalues),
        }

        if not state["variationType"]:
            raise ValueError("No variation type selected")

        if not file_content or not file_content.strip():
            raise ValueError("File is empty")

        model_class = _get_model_class(state["variationType"])
        context = _build_validation_context(state)

        # Parse the file
        lines = file_content.strip().split("\n")
        if len(lines) < 2:
            raise ValueError("File must have a header row and at least one data row")

        delimiter = _detect_delimiter(lines[0])
        reader = csv.DictReader(io.StringIO(file_content), delimiter=delimiter)

        # Normalise headers
        if reader.fieldnames:
            reader.fieldnames = [_normalise_header(h) for h in reader.fieldnames]

        errors: list[tuple[int, str]] = []
        valid_rows: list[dict[str, Any]] = []
        row_num = 0

        for row_num, row in enumerate(reader, start=2):  # row 1 is header
            # Strip whitespace from values; skip completely empty rows
            cleaned = {k: v.strip() if v else v for k, v in row.items()}
            if all(not v for v in cleaned.values()):
                continue

            # Convert empty strings to None (Pydantic expects None for optional)
            for key, val in cleaned.items():
                if val == "":
                    cleaned[key] = None

            try:
                model_class.model_validate(cleaned, context=context)
                valid_rows.append(cleaned)
            except ValidationError as exc:
                for err in exc.errors():
                    msg = err.get("msg", str(err))
                    loc = " → ".join(str(l) for l in err.get("loc", []))
                    errors.append((row_num, f"[{loc}] {msg}" if loc else msg))

                if len(errors) >= MAX_DISPLAY_ERRORS:
                    errors.append(
                        (0, f"… stopped after {MAX_DISPLAY_ERRORS} errors (more may exist)")
                    )
                    break
            except Exception as exc:
                errors.append((row_num, str(exc)))

        # Build HTML for error display
        error_html_parts: list[str] = []
        for rn, msg in errors:
            if rn > 0:
                error_html_parts.append(
                    f'<div class="validation-error-row">'
                    f'<span class="row-num">Row {rn}:</span> {_escape_html(msg)}'
                    f"</div>"
                )
            else:
                error_html_parts.append(
                    f'<div class="validation-error-row" style="color:#666;">'
                    f"{_escape_html(msg)}</div>"
                )

        error_html = "\n".join(error_html_parts)

        # Store validated content for potential download
        if valid_rows:
            output = io.StringIO()
            fieldnames = list(valid_rows[0].keys())
            writer = csv.DictWriter(output, fieldnames=fieldnames, delimiter="\t")
            writer.writeheader()
            writer.writerows(valid_rows)
            globalThis._validatedContent = output.getvalue()
        else:
            globalThis._validatedContent = None

        # Report results to JS
        globalThis.displayValidationResults(
            len(errors),
            error_html,
            len(valid_rows) > 0,
        )

    except Exception as exc:
        logger.exception("Validation failed")
        globalThis.displayValidationError(str(exc))


def _escape_html(text: str) -> str:
    """Minimal HTML escaping for display."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


# Expose the validation function to JavaScript
from js import globalThis  # type: ignore[import-untyped]  # noqa: E402

globalThis.validate_file = validate_file

# Signal that Python is ready
print("✅ Python environment loaded — sumstatlib ready")
