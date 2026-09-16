# Final platform completion orchestrator

The completion orchestrator is an internal, authenticated operator handoff layer. It inspects repository evidence, runs deterministic local/demo checks, classifies every remaining task, and emits status/count-only readiness output. It does not add fragrance intelligence, a storefront, campaign generation, or a public marketplace.

## Safe automation

The service can inspect core modules and router registration, parse public samples, plan compilation, verify that privacy audits exist, run an isolated in-memory SQLite smoke check, and validate fictional demo evidence. A task becomes `completed` only after its evidence check passes. Demo mode never needs private input or credentials.

```bash
python scripts/complete_platform_readiness.py
python scripts/run_demo_platform_completion.py
python scripts/run_all_safe_audits.py
python scripts/export_final_readiness_report.py
```

Detailed operational reports may be written only beneath `data/private/reports/` with `--export-private`. The tracked CSV export is deliberately fictional and public-safe.

## Blocker interpretation

- `blocked_private_data_required`: place authorised supplier files in `data/private/imports/` at runtime, run the private-input audit, then execute the documented pilot. Nothing outside `data/private/` is accepted as a real supplier input.
- `blocked_credentials_required`: inject production API keys and secrets through the approved secret manager; never commit them.
- `blocked_human_review_required`: an authorised reviewer must decide profile, legal, compliance, and release gates. Automation does not approve or publish.
- `blocked_deployment_environment_required`: configure the production database, environment variables, runtime target, migrations, monitoring, and rollback before deployment can be called ready.
- `blocked_external_repo_required`: separately authorise work in the Maison Obsidian website repository. This repository does not change that website.

## From repository readiness to a private pilot

1. Place authorised files in private runtime storage under `data/private/imports/`; never commit them.
2. Run the private-input and completion privacy audits.
3. Configure private API credentials and a production database in the deployment secret store.
4. Run a dry run, inspect blockers, and then run the private pilot.
5. Require human review and approval before profile approval, product creation, publication, launch, or external export.

Maison Obsidian integration additionally needs an approved API contract, credentials, staging validation, and separately reviewed website-repository work. MicroPromote remains a future, separately scoped integration and requires an approved data contract and campaign controls. SaaS packaging remains a commercial decision requiring tenancy, billing, support, legal terms, pricing, and compliance review.

Never commit real supplier files or commercial terms, seller briefs or private notes, consumer records or identifiers, credentials, generated private reports, or copied third-party content. The orchestrator never deploys, auto-approves, publishes, creates products, exports to production storefronts, or generates campaigns.
