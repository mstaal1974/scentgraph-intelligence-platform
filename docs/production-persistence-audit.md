# Production persistence and audit trail

## Purpose

This layer provides durable operational state before private pilots run at scale. It persists run and stage status, safe artifact metadata, profile-draft summaries, review state, launch-candidate bands, redacted seller-demand and consumer-scentprint summaries, provenance, and append-only audit events. Existing CSV workflows remain supported and can adopt this boundary progressively.

## Privacy boundary

The data model deliberately does **not** contain raw supplier commercial values or identifiers, seller-private notes, consumer contact details/private notes, or raw individual feedback. It does not store copied third-party descriptions, reviews, ratings, images, comments, or user-generated content. Public projections are allow-listed and expose only identifiers, counts, bands, statuses, redaction flags, and safe summaries. Private filesystem locations exist only on the internal run/artifact records and are omitted from run projections; artifact locations appear only when both visibility and safety are explicitly public.

Audit summaries pass through a sensitive-topic guard. Records never auto-approve, publish, create products, promote catalogue entries, or generate campaigns. Provenance records retain source type, confidence band, permitted-use status, and a safe summary so reviewers can enforce usage boundaries.

## Database setup and migrations

For local development, the persistence boundary falls back to `data/private/aromatwin-persistence.db` when the normal default points at unavailable Postgres. Tests should explicitly use `sqlite:///:memory:` or a temporary SQLite path. Production accepts the existing `AROMATWIN_DATABASE_URL` Postgres SQLAlchemy URL. Credentials must remain in environment configuration and connection URLs are never printed.

Run `python scripts/init_persistence.py` to create missing tables without dropping data. Alembic users can run `alembic upgrade head`; revision `0004_production_persistence_audit` creates only the ten operational tables and its downgrade removes only those tables.

## Pilot migration and audit export

A private run stays under `data/private/runs/{run_id}/`. Run:

```bash
python scripts/migrate_private_run_to_persistence.py RUN_ID
python scripts/export_operational_audit.py data/private/exports/operational-audit.csv
python scripts/audit_persistence_privacy.py
```

Migration reads manifest/readiness summaries through explicit allow lists, stores the private root internally, creates stage state, and records an audit event. Export emits only run IDs, statuses, blocker counts, risk levels, and safe event summaries. Never commit private run directories, database files, private exports, source files, seller briefs, or consumer records.

## API and review operations

Authenticated `/operations` routes provide health, run/stage/artifact summaries, review items, launch candidates, provenance, audit events, and audit reports. They are internal workflow endpoints even though their responses are public-safe. Review decisions remain human-controlled. Public-safe persistence does not replace the private pilot manifest or source workflow output and does not mutate either.

## Human review workflow

Human review gates now provide private, audit-oriented queues and explicit decisions. Approval is
only permission for a next internal stage; it never publishes records, creates catalogue products
or SKUs, starts launch execution, or generates campaigns. Default API projections contain only
safe identifiers, bands, statuses, role labels, summaries, and aggregate readiness counts. See
[Human review gates workflow](human-review-gates-workflow.md).

## Private supplier pilot execution pack

The focused execution layer is documented in [Private supplier pilot execution](private-supplier-pilot-execution.md). It adds path-safe intake, explicit preflight plans, private run boundaries, aggregate acceptance evidence, privacy auditing, and mandatory human review without changing the underlying intelligence workflow or permitting publication.
