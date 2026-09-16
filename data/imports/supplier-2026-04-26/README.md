# AromaTwin supplier import package — 26.04.2026

Generated from `PERFUME OIL PRICE LIST  26.04.2026 (1).xlsx` sheet `Table 1`.

This package is supplier-first. It is intended for staging/import into AromaTwin or Maison Obsidian tooling, not direct catalogue publication.

## Key outputs

- `supplier_items.csv` — cleaned supplier availability rows with provenance, raw fields, normalised matching fields, prices, flags, and review status.
- `match_candidates.csv` — initial match candidates generated from supplier rows only.
- `brands.csv` — unique normalised brand candidates and row counts.
- `review_queue.csv` — medium/high priority rows needing human review before catalogue approval.
- `duplicates.csv` — duplicate exact rows and duplicate supplier-code flags.
- `source_provenance.csv` — source records and commercial/IP guardrails.

## Important guardrail

All rows start as `needs_verification`. Do not use the rows as approved product/catalogue copy until independent verification, enrichment, and review are completed.

Import batch: `supplier_20260426`
Converted at UTC: `2026-09-15T23:52:40+00:00`
