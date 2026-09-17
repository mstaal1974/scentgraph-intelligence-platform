# Private supplier pilot execution pack

> Prerequisite: a human must complete the [staging smoke test and operator handoff](staging-smoke-test-operator-handoff.md) before placing supplier files in private runtime storage or starting this workflow.

This pack is an operational safety layer over the existing import, matching, sourcing,
profile, enrichment, launch-intelligence, persistence, audit, and review services. It does
not add intelligence, publish records, approve records, create SKUs, or create campaigns.

## Private inputs and intake

Real supplier price files must never be stored under `data/samples/`. Place real files
only in `data/private/imports/suppliers/{supplier_label}/` at runtime, and keep the entire
`data/private/` tree gitignored. Never commit a real supplier file: it can contain
confidential commercial data. Public samples must be fictional and value-free. CSV,
XLSX, and XLS are supported as private runtime inputs; PDFs are not. Recognised layouts are
`existing_supplier`, `fatma`, and `generic_supplier`; an unknown layout requires an
operator-approved mapping.

Create the local private directory and place the workbook there manually. Never copy a
tracked public sample into private runtime storage:

```text
mkdir -p data/private/imports/suppliers/fatma
# place the real workbook manually here:
data/private/imports/suppliers/fatma/<supplier-file>.xlsx
```

If a supplier file is accidentally committed under `data/samples/`, remove it from the
repository before continuing.

Run `python scripts/prepare_private_supplier_inputs.py`. The scanner validates the path,
extension, readable headers, likely format, and required structural columns. It records
field *names* that appear private, never their values. The detailed manifest remains in
`data/private/reports/`. Blocked files are not imported.

## Preflight and modes

An execution plan fixes the stage order, input selection, expected output boundary,
privacy audits, persistence choice, and mandatory review gates before work begins.

* `python scripts/run_private_supplier_pilot.py --dry-run` evaluates preflight and writes
  no operational output.
* `python scripts/run_private_supplier_pilot.py --private-run` writes only beneath
  `data/private/runs/{run_id}/`.
* `python scripts/run_private_supplier_pilot.py --review-only-run` prepares review work
  from existing evidence and excludes import and matching reruns.

Use `--run-id`, `--supplier-label`, and comma-separated `--stages` to constrain a run.
Persistence is opt-in and must retain the existing audit trail. Recovery is deliberately
simple: retain audit evidence, correct the private input or mapping, remove only the
failed private run directory when policy permits, and rerun with a new reviewed plan.

## Review, acceptance, and next steps

Supplier match, provenance, launch-readiness, and final internal review gates remain
mandatory. An acceptance report contains aggregate counts and statuses, not supplier
values or private seller/consumer records. A blocker means an operator must correct or
review the cited class of problem. Acceptance permits only the named **internal** next
step—review, profile enrichment, supplier review, or launch planning—and never recommends
public launch.

After the first run, reconcile its audit record, resolve blockers, complete assigned human
reviews, repeat the privacy audit, and approve a separate internal next-stage decision.
Export a safe report with
`python scripts/export_private_pilot_acceptance_report.py RUN_ID` and audit samples with
`python scripts/audit_private_pilot_inputs.py`.

## Final completion gate

Run `python scripts/complete_platform_readiness.py` before intake. Repository completion is not pilot completion: real inputs must remain under `data/private/`, credentials must be injected at runtime, and every human review gate remains mandatory. See [final platform completion](final-platform-completion.md).

## Hosted staging prerequisite

For a hosted pilot, first satisfy `docs/staging-deployment-readiness.md`. Upload approved private inputs directly to the protected runtime mount after deployment—never commit them—and retain all existing review gates.

## Maison integration readiness boundary

The Maison readiness pack consumes only approved, public-safe summaries through allow-listed contracts.
It does not change existing generation, pilot, review, persistence, or staging workflows and never
performs an external sync. See [Maison integration readiness](maison-integration-readiness.md).

## Private profile production handoff

After intake and candidate matching, use the [private fragrance profile production pack](private-fragrance-profile-production.md). The production preflight must be ready, and operational drafts stay under the run's private `profiles/` directory. This handoff never approves or publishes a profile.

## Profile pipeline rehearsal

The fictional, sample-safe rehearsal pack validates integration without real inputs or external side effects. It never approves drafts, creates products, publishes records, or exports to Maison. See [Profile pipeline rehearsal](profile-pipeline-rehearsal.md).
