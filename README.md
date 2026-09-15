# ScentGraph Intelligence Platform

ScentGraph is a standalone, API-first fragrance intelligence platform for retailers, brands, and white-label experiences. It turns sourced fragrance facts into governed taxonomies, comparable scent vectors, clone intelligence, recommendations, and customer Scentprints.

Maison Obsidian is the first intended customer, not a code or data dependency. Every consumer integrates through the same versionable API contract.

## Quick start

```bash
cp .env.example .env
docker compose up -d postgres
python -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'
pytest
uvicorn scentgraph.main:app --reload
```

Interactive OpenAPI documentation is available at `http://localhost:8000/docs`.

## Status

This repository contains the foundation only: domain schema, small illustrative datasets, import/validation scaffolding, API contracts, and deterministic service boundaries. Authentication, billing, production deployment, retailer connectors, and UI are intentionally deferred.
