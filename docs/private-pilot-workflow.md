# Private pilot workflow

## Purpose and boundaries

The private pilot workflow is an evidence-only orchestration layer over the existing supplier,
profile, catalogue, recommendation, seller-demand, consumer-signal, and launch-readiness modules.
It produces a conservative run manifest, blockers, and readiness report. It does **not** approve or
publish records, promote catalogue entries, create products, scrape the web, copy third-party
content, or generate campaigns. MicroPromote remains deliberately out of scope until a later,
separately reviewed integration.

All operational source material belongs under `data/private/`. A private run writes only to
`data/private/runs/{run_id}/`; this ignored directory must never be committed. Fictional,
aggregate demo artifacts may be written under `data/samples/`. Never commit source supplier
files, commercial values, seller briefs or private notes, individual consumer records or notes,
or copied descriptions, reviews, ratings, comments, imagery, or other user-generated content.

## Running it

```bash
python scripts/run_private_pilot_workflow.py --dry-run --input data/private/imports/input.csv
python scripts/run_private_pilot_workflow.py --run-id pilot-001 --input data/private/imports/input.csv
python scripts/run_private_pilot_workflow.py --demo-sample
python scripts/run_private_pilot_workflow.py --dry-run --stages supplier_import,profile_coverage
python scripts/export_pilot_readiness_report.py pilot-001
python scripts/audit_pilot_workflow_privacy.py
```

A dry run is memory-only. A private run records `manifest.json`, `readiness.json`, and
`result.json` in its private run directory. Demo mode uses fictional evidence and writes only a
public-safe CSV beneath `data/samples/`. Input paths outside `data/private/` are rejected.

## Stages and dependencies

Stages run in this order for a full workflow: supplier import; offer matching; sourcing;
commercial-scenario band assessment; bulk profile generation; coverage; enrichment queue;
catalogue readiness; scent-vector readiness; recommendation readiness; product catalogue
readiness; seller-demand matching; consumer-signal readiness; launch intelligence; launch-gap
analysis; and the final readiness report. Each full-run stage depends on approved evidence from
its predecessor. Selected stages can be evaluated independently when private input evidence is
provided. Missing evidence causes a skip and a blocker—not an inferred value or a mutation.

Blockers contain a type, severity, accountable role, safe explanation, and recommended fix.
Readiness is conservative: privacy failures block the run; failed/critical evidence is low
confidence; core skipped stages mean missing inputs; other gaps lead to enrichment, supplier
review, or product-setup statuses. Completing launch intelligence can make a run eligible for a
**small private pilot**, but never authorises public launch. Explicit human admin-review gates
remain mandatory.

## Connections

Admin review consumes the safe blockers and evidence statuses and remains the only approval
boundary. Launch intelligence supplies aggregate readiness bands and gap evidence; the pilot
workflow does not change its candidates. API endpoints live below the configured internal prefix
and require the private API key outside local development. Their default projections contain
counts, statuses, remediation summaries, and bands only.

## Optional durable persistence

Completed private manifests can be migrated through the summary-only persistence boundary documented in [Production persistence and audit trail](production-persistence-audit.md). This is opt-in and does not replace or mutate run files.
