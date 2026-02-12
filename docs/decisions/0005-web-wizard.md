# ADR 0005 — Web-based wizard using PyScript and the File System Access API

## Status

Accepted

## Context

The existing Textual TUI wizard (`sumstatapp`) requires users to install Python
and run a terminal command. Our primary users are senior researchers who may not
have Python installed or be comfortable with CLI tools. Portability and ease of
use are key goals for the MVP.

We need a deployment strategy that:

1. Runs in a browser (zero install for users)
2. Reuses `sumstatlib` validation models without rewriting them in JavaScript
3. Keeps user data local (no server-side processing)
4. Uses EMBL's Visual Framework for consistent branding
5. Minimises JavaScript — our team knows Python
6. Has no build step or complex toolchain

Technologies considered:

- **PyScript / Pyodide**: Runs CPython in the browser via WebAssembly. Can
  import pure-Python and many compiled packages (including Pydantic v2).
- **htmx**: Excellent for server-rendered hypermedia, but requires a server.
  Since our app is entirely client-side, htmx's model doesn't apply directly.
- **Flask/FastAPI + htmx**: Would require hosting a server and uploading user
  data, conflicting with the "data stays local" requirement.
- **Transcrypt / Brython**: Python-to-JS transpilers. Limited ecosystem support;
  Pydantic would not work.
- **Plain JavaScript rewrite**: Would duplicate all validation logic and require
  JS expertise the team lacks.

## Decision

Build a **single-page static web application** using:

- **PyScript (Pyodide)** to run `sumstatlib` in the browser
- **EMBL Visual Framework** (CDN) for styling
- **Standard HTML5 form elements** for the wizard UI
- **File System Access API** for reading input files and writing validated
  output to a local directory (with `<input type="file">` + download fallback
  for non-Chromium browsers)
- **Vanilla JavaScript** (~300 lines) only for wizard navigation and
  File System Access API calls

The wizard flow mirrors the existing TUI: Welcome → Variation Type → Effect
Size → P-value Type → Significance → File Picker → Validate.

All validation runs client-side. No server is required. The app can be deployed
to any static file host (GitHub Pages, S3, internal web server).

## Consequences

### Positive

- **Zero install**: users open a URL in their browser
- **Data stays local**: no upload, no server-side processing — important for
  pre-publication genomic data
- **Code reuse**: `sumstatlib` runs unmodified in the browser
- **Simple deployment**: static files, no server infrastructure
- **EMBL branding**: Visual Framework provides consistent look and feel
- **Maintainability**: ~90% of code is Python; the team can maintain it

### Negative

- **Initial load time**: Pyodide downloads ~15 MB on first visit (cached after).
  Users see a loading spinner for 10-20 seconds.
- **Large file limits**: very large files (>100 MB) may cause browser memory
  issues. The CLI remains the recommended tool for very large datasets.
- **Browser support**: File System Access API (read + write) is Chromium-only.
  Firefox/Safari fall back to `<input type="file">` (read) and download (write).
- **pydantic-core WASM**: Pydantic v2 depends on pydantic-core (compiled Rust).
  This must be available as a wasm32 wheel in Pyodide's package index. If a
  future Pydantic version breaks WASM compatibility, this is a risk.
- **No htmx**: Despite appreciating the htmx philosophy, the lack of a server
  makes htmx impractical. The htmx principles (HTML-first, declarative
  behaviour, progressive enhancement) are followed in spirit.
