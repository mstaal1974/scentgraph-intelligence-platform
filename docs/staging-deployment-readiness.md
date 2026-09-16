# Staging deployment readiness

> After a human deploys an approved staging build, follow the [staging smoke test and operator handoff](staging-smoke-test-operator-handoff.md). The smoke pack verifies the live deployment but does not deploy or change readiness decisions.

## Scope

This pack validates configuration, repository artifacts, migration syntax, runtime health, storage boundaries, and public-file privacy before a human deploys AromaTwin. It **does not deploy**, provision infrastructure, execute migrations, accept real data, publish products, or bypass review gates.

## Configuration outside Git

Configure these values in the hosting provider, never in a committed file:

- `AROMATWIN_ENV=staging` and unique `AROMATWIN_PRIVATE_API_KEY` (required).
- `DATABASE_URL` from a staging-only managed PostgreSQL service when persistence is enabled.
- `PRIVATE_STORAGE_ROOT` beneath an access-controlled persistent mount such as `/var/lib/aromatwin/private`.
- `CORS_ALLOWED_ORIGINS` containing explicit HTTPS staging origins, never `*`.
- `AROMATWIN_API_KEY` if the public API requires a key; `LOG_LEVEL`; and the `ENABLE_*` feature flags shown in `deployment/staging.env.example`.
- `PUBLIC_SAMPLE_ROOT` may point to the committed fictional samples only.

The checks disclose presence/status and masked path basenames only. They never print credentials or credential-bearing connection strings. Never commit filled environment files, real credentials, private supplier inputs, seller briefs, consumer records, or any commercial fields.

## Storage and database expectations

Use separate staging credentials with least privilege. Backups, retention, TLS, network policy, and credential rotation are operator responsibilities. The private mount must not overlap public samples or static web roots. Upload private supplier files directly to the protected runtime mount only after deployment; never upload them through GitHub.

Review migrations without applying them:

```bash
PYTHONPATH=src python scripts/check_migration_readiness.py
```

This parses migration modules and identifies PostgreSQL-specific markers. SQLite remains a local-check convenience and is not treated as staging parity. A human must review and apply migrations using the normal controlled release process.

## Templates

- Render: copy `render.yaml.example`, create the managed service/database, secret values, disk, and explicit origin in the dashboard.
- Railway: use `railway.json.example`; configure variables, managed database, and persistent volume in the project.
- Fly.io: copy `fly.toml.example`, replace the app/region placeholders, create a volume, and use `fly secrets` outside this repository.
- Docker Compose: copy `docker-compose.staging.example.yml` and create an untracked `staging.env`; supply an external staging database and protect the host/volume.

The examples are starting points, not production infrastructure definitions.

## Operator checks

```bash
PYTHONPATH=src python scripts/check_environment_readiness.py
PYTHONPATH=src python scripts/check_deployment_readiness.py
PYTHONPATH=src python scripts/check_deployment_readiness.py --write-report
python scripts/audit_deployment_privacy.py
```

The optional report is written under ignored private report storage and contains only statuses, counts, masked values, and actions. A non-zero status means an operator must resolve blockers. The public `GET /deployment/health` is minimal; environment, readiness, active checking, and audit endpoints require private API authentication outside local mode.

## Moving to a real staging deployment

1. Merge this readiness-only change after review.
2. Configure staging secrets, database, explicit CORS, and private persistent storage outside Git.
3. Run all checks and review their evidence; resolve every blocker.
4. Have an operator deploy the API and apply reviewed migrations.
5. Verify `/deployment/health`, then authenticate and verify the private readiness endpoints.
6. Upload approved private inputs directly to protected storage, run the private pilot, and complete human review.
7. Plan Maison integration separately and later; this pack does not alter that repository or integrate it.
