# Fragrance Profile Builder

## Supplier-first draft flow

The profile builder consumes sanitised `supplier_items.csv`, `match_candidates.csv`, `review_queue.csv`, and `source_provenance.csv` staging exports. Supplier availability establishes that an item exists; candidate matching provides an identity hypothesis. Neither is an approved fragrance claim.

For queued items, the builder creates deterministic original text using brand and fragrance identifiers only. It does not read or reproduce third-party descriptions, reviews, ratings, images, comments, UGC, supplier prices, supplier codes, or commercial terms. No live web search, scraping, or external AI API is used. Notes, accords, contextual fields, and vectors remain empty unless separately and permissibly established later.

Every generated record has `review_status=needs_human_review`. Reference-only or restricted candidates receive capped confidence and provenance notes requiring independent permitted sources. Generation can never approve a draft.

## Review and licensing guardrails

Approval is a separate human decision. The API reads provenance from the server-side `source_provenance` table; callers cannot self-assert source permissions. At least one stored official or licensed-commercial source must document commercial-use permission, a source reference or URL, and confidence of 0.70 or higher. A named reviewer and rationale are recorded. Reference-only, non-commercial, unknown, or unverified provenance is rejected. Rejection records a reviewer, reason, time, and controlled status.

Reference databases may support discovery and identifier matching only. Their descriptions, editorial material, reviews, images, ratings, comments, and UGC cannot be copied or paraphrased into commercial profiles unless suitable rights are documented.

## Future catalogue promotion

`approved_for_catalogue` means the profile draft passed review; it does not itself create a catalogue fragrance. A later, separately audited promotion workflow will map approved fields into canonical catalogue records while preserving draft and provenance history.

Maison Obsidian will consume only promoted catalogue profiles through the licensed API. It will not receive draft queues, restricted source material, or confidential supplier commercial data.

## Commands

```bash
python scripts/build_profile_drafts.py
uvicorn aromatwin.main:app --reload
```

The CLI writes the review-only public sample output to `data/profile_drafts.csv`. API generation persists drafts through SQLAlchemy, skips an already-active supplier/candidate pair, and never reads confidential supplier pricing into a profile.

## Public draft contract

Profile draft APIs and `data/profile_drafts.csv` expose structured `*_json` attributes, confidence, provenance notes, workflow state, and review timestamps only. They exclude supplier cost, quantity, supplier-code, and commercial-term fields. The `restricted_content_detected` guard must remain false for approval, draft source confidence must be at least 0.70, and the server must find independently permitted provenance; client assertions cannot bypass these checks.

All implementation lives in the existing `src/aromatwin/` package. No parallel application namespace or second API stack is maintained.
