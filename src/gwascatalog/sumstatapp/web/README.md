# GWAS Catalog Web Validator

A browser-based summary statistics validator. All validation runs locally, no data leaves the browser.

Built with [Pyodide](https://pyodide.org) (Python compiled to WebAssembly) and the [EMBL Visual Framework](https://stable.visual-framework.dev).

## Development

**Prerequisites:** `uv` installed; run commands from the workspace root.

```bash
# Build the sumstatlib wheel and start a local dev server
uv run src/gwascatalog/sumstatapp/web/build.py --serve
# → http://localhost:8000

# Skip the wheel rebuild (HTML/JS/Python changes only)
uv run src/gwascatalog/sumstatapp/web/build.py --skip-build --serve
```

## File structure

```
web/
├── index.html           # Multi-step wizard UI (EMBL Visual Framework)
├── wizard.js            # Wizard navigation + File System Access API
├── validate.py          # Python validation bridge (runs inside Pyodide)
├── validation-worker.js # Web Worker: loads Pyodide off the main thread
├── build.py             # Wheel build + dev server script
├── static/              # Example input files and images
└── dist/                # Built sumstatlib wheel (git-ignored)
```

## How it works

`validation-worker.js` loads Pyodide in a Web Worker and installs the
`sumstatlib` wheel from `dist/`. The main thread sends the uploaded file as a
binary transfer to the Emscripten filesystem. The worker passes the file and
configuration captured from the HTML form through `validate.py`, which calls the
same Pydantic models used by the CLI. Results (errors + a validated output
file) are transferred back to the main thread and reported to the user.

## Deployment

The app is entirely static. Run `build.py` to produce the wheel, then serve
the `web/` directory from any HTTP host (GitHub Pages, S3, nginx, etc.).

```bash
# Copy built app into a target directory (e.g. for a Docusaurus site)
uv run build.py --copy-to path/to/target --base-path /validator/
```

## Browser support

All major browsers should be supported because the File System Access API
isn't used.