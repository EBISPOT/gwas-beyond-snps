import nox

# Use uv for environment creation and package installation
nox.options.default_venv_backend = "uv"
nox.options.sessions = ["lint", "tests"]


@nox.session
def tests(session):
    # Install local workspace packages
    session.install(".")
    session.install("./sumstatlib")

    # manually install pydantic
    session.install("pydantic")

    # Install test tooling
    session.install("pytest", "coverage")

    # Run tests under coverage
    session.run(
        "coverage",
        "run",
        "--source=src,sumstatlib",
        "--omit=*/integration/*",
        "-m",
        "pytest",
        "src",
        "sumstatlib",
        "--ignore-glob=src/**/integration",
        "--ignore-glob=sumstatlib/**/integration",
    )

    # Coverage report (terminal)
    session.run("coverage", "report", "-m", "--fail-under", "90")


@nox.session
def lint(session):
    # Install workspace packages (so type checking resolves imports)
    session.install(".")
    session.install("./sumstatlib")
    # manually install pydantic (this is OK, remember the web app)
    session.install("pydantic")

    # Lint + format + typing tools
    session.install("ruff", "ty")

    # Format check (fails if reformatting needed)
    session.run("ruff", "format", "--check", ".")

    # Lint
    session.run("ruff", "check", ".")

    # Type checking
    session.run("ty", "check", "src", "sumstatlib/src")
