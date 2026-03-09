"""CLI for batch validation of GWAS summary statistics files.

Usage::

    gwascatalog beyondsnp validate INPUT [INPUT ...] --type {CNV,GENE} [OPTIONS]

Accepts a list of files. Run with ``--help`` for the full list of options.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from gwascatalog.sumstatlib import SumstatConfig

from gwascatalog.sumstatapp.cli._validate import FileResult, validate_file

if TYPE_CHECKING:
    from collections.abc import Sequence

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(module)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# ── Input resolution ──────────────────────────────────────────────


def _resolve_inputs(raw: list[str]) -> list[Path]:
    """Turn user-supplied paths into files."""
    resolved: list[Path] = []

    for entry in raw:
        p = Path(entry)
        if p.is_file():
            resolved.append(p.resolve())
        else:
            logger.warning(f"Skipping {entry}: not a file")

    # Deduplicate while preserving order
    seen: set[Path] = set()
    unique: list[Path] = []
    for f in resolved:
        if f not in seen:
            seen.add(f)
            unique.append(f)
    return unique


# ── Argument parsing ──────────────────────────────────────────────


def _add_validate_args(parser: argparse.ArgumentParser) -> None:
    """Register all arguments for the ``validate`` subcommand."""
    parser.add_argument(
        "inputs",
        nargs="+",
        metavar="INPUT",
        help="Files to validate",
    )
    parser.add_argument(
        "--type",
        required=True,
        choices=["CNV", "GENE"],
        dest="variation_type",
        help="Type of genetic variation (CNV or GENE)",
    )
    parser.add_argument(
        "--assembly",
        choices=["GRCh38", "GRCh37", "NCBI36", "NCBI35", "NCBI34"],
        default=None,
        help="Genome assembly (e.g. GRCh38)",
    )
    parser.add_argument(
        "--effect-size",
        choices=["beta", "odds_ratio", "hazard_ratio", "z_score"],
        default=None,
        dest="primary_effect_size",
        help="Primary effect size measure",
    )
    parser.add_argument(
        "--allow-zero-pvalues",
        action="store_true",
        default=False,
        help="Accept zero as a valid p-value",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path("validated"),
        help="Output directory for results (default: ./validated/)",
    )
    parser.set_defaults(func=_run_validate)


def _build_parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        prog="gwascatalog",
        description="GWAS Catalog data tools.",
    )
    root_sub = root.add_subparsers(dest="group", metavar="COMMAND")
    root_sub.required = True

    # ── beyondsnp group ───────────────────────────────────────
    beyondsnp = root_sub.add_parser(
        "beyondsnp",
        help="Tools for gene-based and CNV summary statistics.",
    )
    beyondsnp_sub = beyondsnp.add_subparsers(dest="subcommand", metavar="SUBCOMMAND")
    beyondsnp_sub.required = True

    validate_parser = beyondsnp_sub.add_parser(
        "validate",
        help="Validate summary statistics files for GWAS Catalog submission.",
        description=(
            "Validate GWAS summary statistics files for submission to the GWAS Catalog."
        ),
        epilog=(
            "Example: gwascatalog beyondsnp validate data/file.tsv "
            "--type GENE --assembly GRCh38"
        ),
    )
    _add_validate_args(validate_parser)

    return root


# ── Result display ────────────────────────────────────────────────


def _print_summary(results: list[FileResult]) -> None:
    """Print a human-readable summary to stdout."""
    passed = [r for r in results if r.fatal_error is None and r.error_count == 0]
    failed = [r for r in results if r.fatal_error is None and r.error_count > 0]
    fatal = [r for r in results if r.fatal_error is not None]

    width = 60
    print(f"\n{'=' * width}")
    print(
        f"Validated {len(results)} file(s): "
        f"{len(passed)} passed, {len(failed)} failed, {len(fatal)} error(s)"
    )
    print(f"{'=' * width}")

    for r in passed:
        print(
            f"  PASS  {r.input_path.name}  "
            f"({r.valid_count:,} rows, {r.elapsed_seconds}s)"
        )
        if r.output_path and r.md5_checksum:
            print(f"        -> {r.output_path.name}  [md5: {r.md5_checksum}]")

    for r in failed:
        print(
            f"  FAIL  {r.input_path.name}  "
            f"({r.error_count} error(s), "
            f"{r.valid_count:,}/{r.rows_processed:,} rows valid)"
        )
        if r.error_path:
            print(f"        -> errors: {r.error_path}")

    for r in fatal:
        print(f"  ERROR {r.input_path.name}: {r.fatal_error}")


# ── Subcommand handlers ───────────────────────────────────────────


def _run_validate(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    """Handler for ``gwascatalog beyondsnp validate``.

    Returns 0 on success, 1 if any file failed validation.
    """
    files = _resolve_inputs(args.inputs)
    if not files:
        parser.error("No input files found")

    output_dir: Path = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Validating {len(files)} file(s)")
    print(f"Output: {output_dir}\n")

    config = SumstatConfig(
        allow_zero_p_values=args.allow_zero_pvalues,
        primary_effect_size=args.primary_effect_size,
        assembly=args.assembly,
    )

    # ── Dispatch ──────────────────────────────────────────────
    results: list[FileResult] = []

    # Sequential — simple and easy to debug
    for f in files:
        print(f"  {f.name} ...", end=" ", flush=True)
        result = validate_file(
            input_path=str(f),
            config=config,
            output_dir=output_dir,
            variation_type=args.variation_type,
        )
        passed = not result.fatal_error and result.error_count == 0
        print("PASS" if passed else "FAIL")
        results.append(result)

    _print_summary(results)

    has_failures = any(r.error_count > 0 or r.fatal_error is not None for r in results)
    return 1 if has_failures else 0


# ── Main ──────────────────────────────────────────────────────────


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for the ``gwascatalog`` CLI."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.WARNING,
        format="%(levelname)s: %(message)s",
    )

    return args.func(args, parser)


if __name__ == "__main__":
    sys.exit(main())
