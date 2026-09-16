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

## Foundation scope

This repository establishes the supplier ingestion, candidate matching, independent enrichment, provenance, licensing guardrails, review workflow, catalogue, and proprietary intelligence boundaries. It intentionally excludes frontend, ecommerce, authentication, billing, full restricted-dataset imports, direct Maison Obsidian integration, and production deployment.
