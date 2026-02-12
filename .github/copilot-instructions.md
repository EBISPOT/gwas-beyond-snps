# Copilot Instructions — gwas-pysumstats

## Project overview

A **uv workspace** for validating GWAS summary statistics (Gene-based, CNV) before submission to the [GWAS Catalog](https://ebi.ac.uk/gwas). Two packages share the `gwascatalog` namespace:

- **`sumstatlib`** (`sumstatlib/`) — Pydantic v2 validation library. The canonical data models live here.
- **`sumstatapp`** (`src/gwascatalog/sumstatapp/`) — Textual TUI wizard that collects metadata and drives validation using sumstatlib.

The application is a scientific workflow for:

1) validating user data and highlighting errors with clear messages and actionable guidance, and
2) simplifying submission to the GWAS Catalog by generating a compliant summary statistics file and checksums

Input data will regularly contain up to tens of millions of rows. Assume streaming or chunked processing may be required.

Failing fast is good, but the user should be able to review a batch of errors in one go, not just the first one encountered. Consider a design where validation errors are collected and displayed in a scrollable panel for user review.

SNP validation is **out of scope** — users are directed to `gwas-sumstats-tools`. The snp module is a stub/placeholder and should be ignored.

## Architecture decisions

Read `docs/decisions/` for rationale. Key points:

- **"Parse, don't validate"**: domain constraints are encoded in `Annotated` types (`sumstat_types.py`), not imperative validators. Reuse types from `core/sumstat_types.py` before creating new ones.
- **Validation context**: models require `Model.model_validate(data, context={...})` — never direct instantiation. Context carries runtime metadata (e.g. `assembly`, `allow_zero_pvalues`, `primary_effect_size`).
- **Structural vs semantic validation**: Pydantic handles structure. `validate_semantics()` is an abstract hook for domain checks (may intentionally be unimplemented).
- **Private attributes** (`PrivateAttr`) store runtime context (e.g. `_assembly`) to keep the data model clean.
- Concrete models are marked `@final` to prevent deep hierarchies.

## Adding a new data model

1. Create a package under `sumstatlib/src/gwascatalog/sumstatlib/<name>/`
2. Define `Annotated` types in `sumstat_types.py`, reusing `core/sumstat_types.py` types
3. Define enums in `sumstat_enums.py` using `StrEnum`
4. Create the model in `models.py`, inheriting `BaseSumstatModel` and decorated with `@final`
5. Add tests for types (`test_<name>types.py`) and model (`test_<name>model.py`) in `sumstatlib/tests/`
6. Export the model in `sumstatlib/src/gwascatalog/sumstatlib/__init__.py`

## Code conventions

- Every module starts with `from __future__ import annotations`
- Use `typing.Annotated` with `pydantic.Field` for type definitions, not bare types
- Use `match`/`case` for multi-branch validation logic (Python 3.12+)
- Enums inherit from `StrEnum`
- Use `pathlib` (not `os.path`) — enforced by ruff rule `PTH`
- Types used only for annotations go in `TYPE_CHECKING` blocks — enforced by ruff rule `TC`
- Prefer absolute imports; strictly avoid circular imports

## Error handling

- Prefer to raise ValidationErrors in the library
- In the validation application (`sumstatapp`), catch and collect `ValidationError` and display messages in a scrollable panel for user review
- Non-validation exceptions should not be caught, allow them to propagate and crash the app

## Testing patterns

- **Type tests**: use `TypeAdapter` via the helper `run_type_validation_test()` in `sumstatlib/tests/helpers.py`
- **Model tests**: parametrize with `(input_data, context, expected_error)` tuples; call `Model.model_validate(input_data, context=context)`
- Tests assert that `ValidationError` messages contain an expected substring
- Tests live in `sumstatlib/tests/`; run with `uv run pytest` from the workspace root

## Build & run

```shell
uv sync                    # install workspace dependencies
uv run pytest              # run sumstatlib tests
uv run ruff check .        # lint
uv run gwascatalog-submit-sumstat # launch the TUI wizard (sumstatapp entry point)
```

## TUI app structure (sumstatapp)

It's critical to follow the "one thing per page" principle and other GOV.UK design system guidelines to maximise clarity and usability.

- `SumstatWizardApp` defines a linear screen flow in `SCREEN_ORDER`
- Each screen extends `WizardScreen` (reactive `can_proceed` gates the Next button)
- `WizardState` dataclass accumulates user choices across screens
- Navigation: `push_screen` / `pop_screen`; styles in `wizard.tcss`
- Validation is triggered on the final review screen, which calls `model_validate()` on the appropriate Pydantic model based on user input
- Pydantic validation errors are caught and displayed in a scrollable panel for user review

### User persona for sumstatapp

- A senior researcher or clinician who is a specialist in their disease/trait
- They understand the data well, but have limited CLI skills and no time or motivation to learn - they had a bioinformatician do the analysis for them.
- They now want to share the data, but the bioinformatician is unavailable to help make the submission.
- These users may be uncomfortable using a terminal and would prefer a web-based interface.

Consider the user journey and how to make it as smooth as possible for this persona. The app should guide them through the process with clear instructions, helpful error messages, and a simple interface that doesn't require technical expertise.

## When in doubt

- Prefer to modify or reuse existing types rather than create new ones
- Never introduce imperative validators unless explicitly instructed
- Do not refactor directory structure
- Do not introduce APIs deprecated in Pydantic v2
- Avoid loading entire datasets into memory unless explicitly required