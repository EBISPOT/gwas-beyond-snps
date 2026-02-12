#!/usr/bin/env python3
"""
Build script for the GWAS Catalog web validator.

Builds the sumstatlib wheel and copies it into the web app's dist/ directory,
then starts a local development server.

Usage:
    python build.py          # build only
    python build.py --serve  # build and start dev server on port 8000
"""

from __future__ import annotations

import argparse
import http.server
import shutil
import subprocess
import sys
from pathlib import Path

# Paths relative to this script
WEB_DIR = Path(__file__).parent
PROJECT_ROOT = WEB_DIR.parents[3]  # gwas-pysumstats/
SUMSTATLIB_DIR = PROJECT_ROOT / "sumstatlib"
DIST_DIR = WEB_DIR / "dist"

DEFAULT_PORT = 8000


def build_wheel() -> Path:
    """Build the sumstatlib wheel and return the path to the .whl file."""
    print("📦 Building sumstatlib wheel…")
    # uv build places wheels in <workspace-root>/dist/ by default
    subprocess.run(
        ["uv", "build", "--wheel", "--package", "gwascatalog-sumstatlib"],
        cwd=PROJECT_ROOT,
        check=True,
    )

    # Find the built wheel (uv puts it in project root dist/)
    wheels = list((PROJECT_ROOT / "dist").glob("gwascatalog_sumstatlib-*.whl"))
    if not wheels:
        print("❌ No wheel found in dist/", file=sys.stderr)
        sys.exit(1)

    wheel = sorted(wheels)[-1]  # latest by name
    print(f"   Built: {wheel.name}")
    return wheel


def copy_wheel(wheel: Path) -> None:
    """Copy the wheel into the web app's dist/ directory."""
    DIST_DIR.mkdir(exist_ok=True)

    # Remove old wheels
    for old in DIST_DIR.glob("gwascatalog_sumstatlib-*.whl"):
        old.unlink()

    dest = DIST_DIR / wheel.name
    shutil.copy2(wheel, dest)
    print(f"   Copied to: {dest.relative_to(PROJECT_ROOT)}")


def serve(port: int) -> None:
    """Start a local HTTP server for development."""
    print(f"\n🌐 Serving at http://localhost:{port}")
    print(f"   Root: {WEB_DIR}")
    print("   Press Ctrl+C to stop\n")

    handler = http.server.SimpleHTTPRequestHandler
    # Serve from the web directory
    import os

    os.chdir(WEB_DIR)

    with http.server.HTTPServer(("", port), handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Server stopped")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build and serve the web validator")
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Start a development server after building",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Port for the development server (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Skip building the wheel (use existing dist/)",
    )
    args = parser.parse_args()

    if not args.skip_build:
        wheel = build_wheel()
        copy_wheel(wheel)
        print("✅ Build complete\n")
    else:
        print("⏭️  Skipping build (using existing dist/)\n")

    if args.serve:
        serve(args.port)


if __name__ == "__main__":
    main()
