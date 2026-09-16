# Sanitised supplier staging exports — 2026-04-26

This tracked directory contains fictional, sanitised staging fixtures for profile-builder development: `supplier_items.csv`, `match_candidates.csv`, `review_queue.csv`, and `source_provenance.csv`. They contain no supplier costs, quantities, confidential supplier codes, commercial terms, third-party descriptions, reviews, images, ratings, comments, or UGC.

Do **not** add raw supplier files here. Confidential inputs belong under the gitignored `data/private/imports/supplier-2026-04-26/`; generated private staging and validation reports belong under `data/private/staging/`.

All tracked rows remain staging hypotheses. `supplier_items.csv` uses `supplier_imported`; generated `profile_drafts.csv` uses `needs_human_review`. Neither is an approved catalogue record.
