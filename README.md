# AromaTwin Intelligence Platform

AromaTwin is a standalone, API-first commercial fragrance-intelligence platform for clone, inspired-by, and private-label retailers. Supplier catalogues are the authoritative source of commercial availability. Third-party fragrance databases are reference-only matching aids unless documented commercial permission says otherwise.

Maison Obsidian is the first intended customer, not a code, catalogue, or branding dependency. Every retailer integrates through the same versioned API boundary.

## Quick start

```bash
cp .env.example .env
docker compose up -d postgres
python -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'
pytest
uvicorn aromatwin.main:app --reload
```

OpenAPI documentation is served at `http://localhost:8000/docs`.

Run the private profile draft review console from the repository root:

```bash
streamlit run apps/private_profile_review_console.py
```

The console reads private profile runs and records internal review decisions under
`data/private/` only. It does not publish catalogue content or initiate downstream actions.

See [Development and testing](docs/development-and-testing.md) for the cloud, local, and CI test
workflow.

## Fragrance profile library

The repository ships a first-party library of 48 original profiles across 12 fictional houses,
with reviewed taxonomy, scent vectors, recommendations, and inspired-by relationships, so the
whole pipeline runs end to end on realistic data:

```bash
python scripts/build_profile_library.py
python scripts/build_scent_vectors.py --approve
python scripts/build_recommendations.py
```

Everything in it is original AromaTwin content about fictional houses. A library of real-brand
profiles is a separate commercial step requiring a permitted source. See
[Fragrance profile library](docs/profile-library.md).

## Generating scent profiles

Supplier drafts can be enriched into full scent profiles with a model-backed provider:

```bash
export OPENAI_API_KEY=... ANTHROPIC_API_KEY=...
python scripts/enrich_private_profile_batch.py --run-id <run> --provider chain
```

`--provider` accepts `offline`, `openai`, `anthropic`, or `chain`; `chain` runs OpenAI first and
falls back to Claude before the offline provider, so one vendor rate-limiting does not drop a
batch to keyword inference.

Only an allow-listed identity payload leaves the application, and model output is never trusted:
it is validated against controlled vocabularies, stripped of private and restricted fields, marked
per field as supplier evidence or model inference, and always returned needing human review. See
[Model-backed scent profile generation](docs/ai-profile-generation.md), which also sets out the
provenance risk this approach carries.

## Authentication

Authentication fails closed. `/maison`, `/products`, and `/scentprint-quiz` require
`X-API-Key`; the operator surfaces require `X-Private-API-Key` or `X-Admin-API-Key`; only
`/health`, `/deployment/health`, and the OpenAPI documents are anonymous. A non-local
`AROMATWIN_ENVIRONMENT` refuses to start while any key is unset. For local development without
keys, set `AROMATWIN_ALLOW_INSECURE_LOCAL_AUTH=true` explicitly. See
[Security and deployment](docs/security-and-deployment.md).

## Foundation scope

This repository establishes the supplier ingestion, candidate matching, independent enrichment, provenance, licensing guardrails, review workflow, catalogue, and proprietary intelligence boundaries. It intentionally excludes frontend, ecommerce, authentication, billing, full restricted-dataset imports, direct Maison Obsidian integration, and production deployment.
