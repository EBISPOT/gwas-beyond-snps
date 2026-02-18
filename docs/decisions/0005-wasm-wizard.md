# Implement WebAssenbly (Wasm) wizard using PyScript

Date: 2026-02-17

## Status

Proposed

## Context

The new summary statistics validation application needs a front end Minimum Viable Product (MVP).

Portability and ease of use are key goals for the application.

The GWAS and PGS Catalogs have started to deploy user facing applications (e.g. ssf-morph, PGS scoring file validator) using WebAssembly. This repository will follow the same pattern. This is because WASM deployment:

1. Runs in a browser, zero install required for users
2. Reuses existing Python code without a full JavaScript rewrite (the bioinformatics team is fluent in Python)
3. Provides a graphical interface

The user persona for this application:

* A senior researcher or clinician who is a specialist in their disease/trait
* They understand the data well, but have limited CLI skills and no time or motivation to learn - they had a bioinformatician do the analysis for them
* They now want to share the data, but the bioinformatician is unavailable to help make the submission

## Decision

Build a **single-page static web application** using:

- **PyScript (Pyodide)** to run `sumstatlib` in the browser
- **Standard HTML5 form elements** for the wizard UI, with a strong preference for semantic HTML elements
- **EMBL Visual Framework** for styling
- **Minimal vanilla JavaScript** for PyScript glue and simple interactive elements

A gold standard application which implements this approach is the pandoc web app:

https://pandoc.org/app/

Source is available at https://github.com/jgm/pandoc/tree/main/wasm

This gold standard implements file upload using a standard file picker, not the File System Access API, which is exclusive to Chrome (not portable). Processed files are output using standard file download mechanisms.

The happy path of the application.

1. Progress through a wizard, gathering configuration one page at a time
2. Upload a file (less than 700MB typically) using a standard file picker. A pre-flight check must validate the file size and type is sensible (optionally compressed text file which is less than 1GB).
3. Process the file in Python using sumstatlib and the wizard configuration
4. Download the outputs of the Python process (a compressed text file)

If validation fails, `ValidationErrors` will be raised by Pydantic. A sample of errors should be collected and displayed visually to the user. Failing fast is important because the file may contain millions of rows.

## Consequences

### Positive

- **Zero install**: users open a URL in their browser
- **Code reuse**: `sumstatlib` runs unmodified in the browser
- **Simple deployment**: static files, no server infrastructure
- **Maintainability**: ~90% of code is Python, so the bioinformatics team can maintain it

### Negative

- **Slow start up time**: Downloading Python and associated dependencies can be slow. It's important to 1) keep dependencies minimal and 2) clearly communicate the loading state to users
- **Debugging is challenging**: Debugging a Pyodide session running in Wasm can be hard. Developers in the future might hate us if the application gets more complicated.
- **Large file limits**: very large files (>700 MB) may cause browser memory
  issues. The CLI remains the recommended tool for very large datasets or bulk data.


