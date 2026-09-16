# Development and testing

## Supported workflow

Development can be completed entirely through a cloud checkout, including from a locked-down
computer with no local Python installation. Create a branch from the latest `main`, make the focused
change in Codex or another cloud environment, run the checks below there, and open a pull request.
GitHub Actions repeats the same checks on every pull request and on pushes to `main`.

CI uses Python 3.12 and installs the editable project with its `dev` extra. That extra deliberately
uses the standard FastAPI/Starlette `TestClient` dependency, `httpx`, and constrains FastAPI and
httpx to their mutually compatible release lines. Do not install `httpx2`: it belongs to a newer,
incompatible Starlette line and is not required by this project. Always install the project extras
rather than relying on packages preinstalled in a Codex image.

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
ruff check .
python -m compileall -q src scripts tests
pytest
```

Codex should run that complete sequence before committing. If dependency imports fail in a reused
environment, create a clean virtual environment and reinstall `.[dev]`; do not patch site-packages,
add non-standard compatibility packages, or skip collection errors.

## Local and focused tests

When Python 3.12 is available locally, create and activate a virtual environment before installing:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
pytest
```

Run a focused file or test while iterating, but finish with full `pytest`:

```bash
pytest tests/test_health.py
pytest tests/test_health.py::test_health_endpoint
pytest
```

Tests are offline and use public-safe repository samples. A future test that genuinely needs an
external service must use the `integration` marker and skip unless its required environment
variables are explicitly configured. Default collection and execution must not require Postgres,
live web access, an AI API, private supplier files, or another repository.

## Data and privacy checks

Run both repository checks after changing public data or data tooling:

```bash
python scripts/validate_data.py data
python scripts/audit_supplier_data.py
```

The validation command checks the expected headers of public repository CSV files. The privacy
audit checks the deliberately minimal public supplier identity sample and tracked paths. Raw supplier
files and private supplier fields—including prices, codes, stock, quantities, classification codes,
and commercial terms—must never be committed. Keep private inputs only in ignored private paths.

If a command cannot run in Codex, record the exact command and error. First reinstall in a clean
environment. Treat only a genuine platform or network restriction as an external limitation; test
failures and dependency-resolution problems belong in repository configuration and should be fixed.
