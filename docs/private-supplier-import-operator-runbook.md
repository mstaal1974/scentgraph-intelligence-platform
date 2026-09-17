# Private supplier import operator runbook

## Purpose

This runbook is for a human operator running the private supplier import from a local
development checkout or GitHub Codespaces. Use this operator-controlled workflow outside
normal Codex cloud tasks: Codex web tasks cannot reliably receive private runtime files
directly. Nothing here approves or publishes profiles, creates products, deploys
infrastructure, or exports to Maison.

## Safety boundaries

- Never commit a real supplier file, and never stage one with `git add`.
- Never place a real supplier file under `data/samples/` or rename one to look like a
  public sample.
- Place real supplier files only under
  `data/private/imports/suppliers/{supplier_label}/`.
- `data/private/` is gitignored. Private outputs belong only under
  `data/private/runs/` or `data/private/reports/`.
- Check `git status --short` before and after every run. If any supplier file appears as
  tracked or staged, stop immediately; do not run or commit anything.
- Do not copy commercial values into issues, logs, commits, review packets, or chat. This
  includes supplier prices or codes, CN, QTY, AED or USD values, costs, margins, stock,
  quantities, and supplier commercial terms.

## Prerequisites

- Access to a development checkout of this repository.
- Python 3.12 or newer, as specified by `pyproject.toml`.
- Dependencies installed from the project-supported `pyproject.toml` configuration with
  the `dev` extra.
- A private supplier workbook in `.csv`, `.xlsx`, or `.xls` format.
- For Codespaces, a private Codespace with terminal access and enough ephemeral storage.
  The workbook is placed directly into the gitignored runtime directory in that
  Codespace; it does **not** need to be uploaded to GitHub or any tracked folder.

## Set up a current checkout

Start from the latest `main`. For local Linux/macOS or the Codespaces terminal:

```bash
git checkout main
git pull
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev]"
```

For local Windows PowerShell, use the same commands except for activation:

```powershell
git checkout main
git pull
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e ".[dev]"
```

Codespaces already provides the repository checkout. Still update `main`, create and
activate the virtual environment, and install the development dependencies using the
Linux commands above. Do not commit or push the workbook as a way to transfer it.

## Create the private directory and place the file

This example uses the public supplier label `fatma`. On Linux/macOS and Codespaces:

```bash
mkdir -p data/private/imports/suppliers/fatma
```

On Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force data/private/imports/suppliers/fatma
```

Manually copy the workbook into `data/private/imports/suppliers/fatma/`. In Codespaces,
use the file explorer to upload it **directly** to that already-created ignored folder,
not to a GitHub tracked folder. Accepted types are `.csv`, `.xlsx`, and `.xls`. Do not
rename it to a public sample name, move it into `data/samples/`, or run `git add` on it.

Verify the repository boundary:

```bash
git status --short
git check-ignore -v data/private/imports/suppliers/fatma/<supplier-file>
git ls-files --error-unmatch data/private/imports/suppliers/fatma/<supplier-file>
```

The first command must show no supplier file, and `git check-ignore` must identify the
ignore rule. The final command is expected to fail because the file must be untracked.
If it succeeds, stop immediately.

## Pre-run validation

Run the safe repository checks before opening or importing the workbook:

```bash
git status --short
ruff check .
python -m compileall -q src scripts tests
python scripts/validate_data.py data
python scripts/run_all_safe_audits.py
python scripts/audit_private_pilot_inputs.py
python scripts/audit_profile_production_privacy.py
```

The full local or Codespaces environment should install development dependencies before
running pytest. Pytest collection may be blocked when `httpx` is unavailable.

### Optional focused tests

```bash
pytest -q tests/test_private_pilot_privacy.py::test_unsafe_supplier_price_samples_are_absent
pytest -q tests/test_platform_completion.py::test_safe_checks_complete_without_private_data
pytest -q tests/test_platform_completion.py::test_demo_does_not_require_real_supplier_files
```

If pytest collection is blocked only because `httpx` is unavailable, install the dev
dependencies before proceeding. Do not change repository code merely to bypass the
dependency.

## Private supplier import workflow

First scan the private input and inspect the private intake report. Do not continue if
the intake audit or preparation reports a blocker.

```bash
python scripts/prepare_private_supplier_inputs.py
python scripts/audit_private_pilot_inputs.py
python scripts/run_private_supplier_pilot.py --dry-run --supplier-label fatma --run-id first_private_supplier_profile_run_YYYYMMDD
python scripts/run_private_supplier_pilot.py --private-run --supplier-label fatma --run-id first_private_supplier_profile_run_YYYYMMDD
```

`prepare_private_supplier_inputs.py` infers labels from the directory layout and supports
optional `--input` and `--report` paths; its report is constrained to
`data/private/reports/`. The pilot script currently supports both `--supplier-label` and
`--run-id`; choose a non-sensitive label and a unique run ID. It also supports `--stages`
for an intentionally constrained run. Always execute and review the no-write dry run
before the private run.

## Private profile batch workflow

Only after intake and its audits pass, plan and execute a bounded draft batch:

```bash
python scripts/plan_private_profile_batch.py --dry-run --max-profiles 25 --supplier-label fatma --run-id first_private_supplier_profile_run_YYYYMMDD
python scripts/run_private_profile_batch.py --private-batch-run --max-profiles 25 --supplier-label fatma --run-id first_private_supplier_profile_run_YYYYMMDD
python scripts/export_profile_review_packet.py first_private_supplier_profile_run_YYYYMMDD
python scripts/export_profile_production_readiness.py
python scripts/export_private_pilot_acceptance_report.py first_private_supplier_profile_run_YYYYMMDD
python scripts/export_profile_pipeline_gap_report.py --output data/private/reports/profile_pipeline_gap_report.csv
```

The planner and batch runner support `--supplier-label` and `--run-id`. The review packet
and acceptance report require the run ID as a positional argument, not a named flag.
Production readiness uses a private report path by default. The gap reporter defaults to
a public sample path, so this private workflow **must** supply the shown private
`--output`; its optional `--rehearsal-id` defaults internally. These exports are internal
review evidence only: they do not approve or publish a profile or export anything to
Maison.

## Outputs and decision gates

Expected operational output locations are:

```text
data/private/runs/{run_id}/
data/private/runs/{run_id}/profiles/
data/private/reports/
```

All such files must remain ignored and untracked and must not be committed.

- Do not proceed to private profile generation if the intake audit fails.
- Do not proceed to review packets if profile generation reports
  `blocked_privacy_risk` or any other privacy risk.
- Do not approve or publish anything from this workflow.
- Human review is required before any profile can become catalogue-ready.
- Maison export is separate and must not happen during this run.

## Final checks

```bash
python scripts/audit_private_pilot_inputs.py
python scripts/audit_profile_production_privacy.py
python scripts/audit_profile_pipeline_rehearsal_privacy.py
python scripts/run_all_safe_audits.py
git status --short
```

Expected status: no tracked supplier files, no staged private outputs, and—if the
runbook branch is active—only intentional documentation or test changes. Confirm staged
paths separately with `git diff --cached --name-only`. Stop if any private path or
supplier file is listed.

## Troubleshooting

### No private supplier file found

Confirm the workbook extension and exact location beneath
`data/private/imports/suppliers/fatma/`. Do not substitute a file from `data/samples/`.
Run preparation again only after the private file is in place.

### File accidentally placed under `data/samples/`

Stop before running any script. Move the file directly to the private supplier directory,
then use `git status --short` and `git diff --cached --name-only`. If it was staged, unstage
that path with `git restore --staged -- <path>` and verify again. Do not commit it.

### File appears in git status

Stop immediately. Check whether it is staged with `git diff --cached --name-only` and
whether Git tracks it with `git ls-files -- <path>`. Unstage with
`git restore --staged -- <path>` if necessary, move it to the required ignored directory,
and get a repository maintainer's help if it was already committed.

### Pytest is blocked by `httpx`

Activate the virtual environment and run `python -m pip install -e ".[dev]"`, then rerun
pytest. Do not edit tests, application code, or pytest configuration to bypass collection.

### A network proxy blocks pip install

Stop before the import. Use the organization's approved proxy or package mirror and ask
the environment administrator for access. Do not disable TLS verification, download
unverified packages, or proceed with a partial environment.

### Script argument not recognised

Run `python scripts/<script-name>.py --help`, compare it with this runbook, and use only
arguments reported by that checkout. Confirm that `main` is current. Do not guess flags
or modify production code during the operator run.

### An audit reports `blocked_privacy_risk`

Stop at that decision gate. Preserve the private audit evidence, do not create review
packets, and have an authorized human investigate the input or output entirely within
private storage. Never paste sensitive values into an issue or commit.

### Output was created under the wrong path

Stop, do not stage it, and inspect `git status --short` plus
`git check-ignore -v <path>`. Move sensitive output into the appropriate private run or
report directory only if organizational policy permits; otherwise have an authorized
operator securely delete it. Rerun the privacy audits before continuing.

### Safely stop and clean generated private files

Do not run `git clean` over `data/private/`: that could delete the source workbook.
Record the run ID, inspect the exact target with
`find data/private/runs/<run-id> -maxdepth 2 -type f -print`, and remove only that run's
generated directory after authorization. Review report filenames individually before
removing generated reports. Leave `data/private/imports/` untouched, verify the source
workbook still exists, and rerun `git status --short` and the final audits.

## Copy-paste operator checklist

- [ ] Latest `main` pulled
- [ ] Dependencies installed
- [ ] Supplier file placed under `data/private/imports/suppliers/fatma/`
- [ ] Git status checked
- [ ] Audits passed
- [ ] Dry run passed
- [ ] Private run completed
- [ ] Draft profiles generated
- [ ] Review packets exported
- [ ] Final audits passed
- [ ] Git status clean except intended docs/code
- [ ] No private files committed
