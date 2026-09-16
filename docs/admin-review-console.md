# Admin review console

## Purpose

The admin review console is a lightweight internal, human-in-the-loop view of the staged
AromaTwin workflow. It aggregates safe metadata without replacing the supplier import,
matching, profile, enrichment, catalogue, vector, recommendation, or Maison API services. It
is not a production authentication system; deployment must put the internal route behind the
operator's access controls.

FastAPI serves the dependency-free interface at `/admin-console/`. Its API lives under
`/admin/`, and the CSV download is available at `/admin/export/review-queue`.

## Stages and queue fields

The fixed stage sequence is `supplier_import`, `match_candidate`, `profile_draft`,
`enrichment_review`, `catalogue_promotion`, `scent_vector`, `recommendation`, and
`maison_api_ready`. Empty foundation stages remain visible in summary responses.

Each item exposes only its console ID, stage, source record ID, public-safe title, status,
confidence and source-confidence scores, licensing-risk flag, restricted-content detection
flag, provenance summary, blocking reason, reviewer, update time, and next action. The console
can filter by stage and highlights confidence, provenance, licensing, and restricted-content
flags.

## Decisions, blockers, and readiness

Reviewers can approve, reject, or request additional sources. Approval delegates to the
existing stage-specific function for profile drafts, enrichment reviews, scent vectors, and
recommendations. Therefore the console cannot override low-confidence, provenance,
licensing, copied-content, or state-transition checks. Unsupported approval and source-request
transitions return a clear `422` response; no record is automatically approved.

Rejection requires a reason. Mutable stage records are rejected through their existing
services; console-only stages retain an in-process audit decision pending a durable admin
store. Requests for more sources are supported for profile drafts and enrichment reviews and
are explicitly labelled as blockers.

The blocked view explains why a record cannot advance. The readiness report separates review-
ready items from blocked items and reports Maison API readiness only when downstream approved,
public-safe evidence exists. It is monitoring metadata, not a publication command.

## Privacy and licensing guardrails

Input rows are converted through a strict output allowlist. Supplier prices, supplier codes,
stock, quantities, CN codes, and commercial terms cannot be represented by the admin schemas
or export. Descriptions, third-party reviews, ratings, images, comments, and UGC are likewise
never passed through. Only an original public-safe title and provenance summary are shown.

High licensing risk, copied restricted content, missing provenance, and low confidence become
explicit blocking reasons. The UI deliberately displays flags rather than underlying source
content. These boundaries preserve the same licensing posture for Maison Obsidian and future
licensed retailer integrations: retailers receive approved catalogue intelligence, while
humans retain accountable control of every promotion decision.

## Local use and export

Run `uvicorn aromatwin.main:app --reload`, then open `http://localhost:8000/admin-console/`.
Generate the tracked safe export with:

```bash
python scripts/export_admin_review_queue.py
```

## Bulk profile link

Bulk-generated drafts and their enrichment tasks are upstream inputs to admin review. Generation never changes approval state or invokes catalogue promotion; reviewers use the existing decision controls after provenance and licensing checks.

## Private pilot orchestration

This module may supply non-mutating readiness evidence to the [private pilot workflow](private-pilot-workflow.md). The pilot layer records only safe statuses, counts, bands, blockers, and human-review actions; it does not bypass this module's existing review gates or expose private source values.

## Persisted review state

Operational review items may be stored by the persistence layer for durable status history. The layer never auto-approves or publishes records, and `/operations` exposes only allow-listed summaries. See [Production persistence and audit trail](production-persistence-audit.md).
