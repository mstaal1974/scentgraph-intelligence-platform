# Staging smoke test and operator handoff

This pack performs read-only, post-deployment checks against an AromaTwin staging API. It verifies public health, deployment health and readiness, optional OpenAPI availability, private-route authentication, internal workflow health, response privacy, and a non-wildcard staging CORS policy. Reports retain status metadata only: response bodies and credentials are never included.

It **does not deploy**, provision, migrate, upload supplier files, approve records, publish products, create campaigns, connect Maison Obsidian, or call production intentionally. A human remains responsible for selecting and verifying the staging host.

## Run after a human staging deployment

Configure values in the shell or hosting secret store, never in a command, file, screenshot, issue, or CI log:

```bash
export AROMATWIN_STAGING_BASE_URL='<staging URL from the operator>'
export AROMATWIN_STAGING_PRIVATE_API_KEY='<value from the staging secret store>'
python scripts/smoke_test_staging_api.py --include-openapi
```

The private key has no command-line option: environment injection avoids shell history and process-list disclosure. The service uses it only to build request headers; it never stores or prints it. `--skip-private-checks` supports a limited public-only run, and `--timeout` controls each request timeout. Use `--output data/private/reports/staging-smoke.json` only when sanitized check detail is needed. Output outside that private directory is rejected.

## Interpret results

`staging_smoke_passed` is eligible for manual handoff. `staging_smoke_passed_with_warnings` requires review of skipped or warning checks. Blocking statuses distinguish unreachable staging, authentication failure, privacy risk, readiness failure, and an unknown failure. Resolve every blocker and rerun; never waive a privacy blocker.

The unauthenticated private check passes only for an HTTP 401 or 403. With the environment key configured, the same private health route must return 200. Deployment readiness, platform completion, private-pilot, review-workflow, and operations checks expose status only and do not inspect private records.

## Manual handoff and pilot readiness

Run `python scripts/check_staging_operator_handoff.py`. With no input it marks every step `manual_required`, deliberately separating absence of human evidence from `complete`. An operator may provide a JSON mapping using `--checklist`; accepted statuses are `complete`, `ready`, `missing`, `blocked`, and `manual_required`.

Before a private supplier pilot, a human must confirm the host and URL, secret-store key, database, migration decision, private storage, CORS allowlist, deployment-readiness run, smoke run, private upload location, human-review process, and rollback process. Supplier input is uploaded to private runtime storage only after these confirmations.

## Public export and CI example

Export an allowlisted summary with:

```bash
python scripts/export_staging_smoke_report.py \
  data/private/reports/staging-smoke.json data/samples/staging-smoke-public.json
```

The exporter accepts input only below `data/private/reports/` and emits IDs, masked URL, statuses, counts, blockers, warnings, and the next action. Review even an allowlisted export before sharing it.

`.github/workflows/staging-smoke-template.yml` is intentionally disabled with a false job condition. After human review, configure both named GitHub Secrets and remove that condition. Do not replace secret references with literal values.

Never commit credentials, connection strings, private paths, supplier files or commercial terms, seller briefs, consumer data, response bodies, or staging evidence containing those values. Run `python scripts/audit_staging_smoke_privacy.py` before handoff.

## Maison integration readiness boundary

The Maison readiness pack consumes only approved, public-safe summaries through allow-listed contracts.
It does not change existing generation, pilot, review, persistence, or staging workflows and never
performs an external sync. See [Maison integration readiness](maison-integration-readiness.md).
