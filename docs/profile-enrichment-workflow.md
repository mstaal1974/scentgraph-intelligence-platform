# Profile enrichment workflow

> **AI enrichment is draft-only and requires human review before catalogue use.**

## Pipeline overview

A private supplier identity draft is read from
`data/private/runs/{run_id}/profiles/drafts.json`. The enrichment service projects only
review-safe identity fields into a richer draft, classifies broad scent directions, and writes
`enriched_profiles.json` beside the input. The review console merges that projection by
`profile_draft_id`; it never publishes or promotes a record.

The offline provider uses deterministic fragrance-family keywords and a small accord taxonomy.
A name can support a broad classification, but cannot support an exact note pyramid or performance
claim. Unknown values therefore remain empty or `unknown` and are explicitly listed in
`fields_requiring_human_review`.

## Run offline enrichment

From the repository root (with the project environment active):

```bash
python scripts/enrich_private_profile_batch.py \
  --run-id first_private_supplier_profile_run_20260917 \
  --max-profiles 25 \
  --provider offline
```

The run ID is validated, the batch is bounded, and output is constrained to `data/private`.
That directory is ignored by Git and its generated contents must not be committed.

## Optional AI enrichment

`ProfileEnrichmentProvider` is the provider boundary. `OfflineHeuristicEnrichmentProvider` is the
safe default. `OpenAIEnrichmentProvider` is currently a placeholder and is unavailable unless
`OPENAI_API_KEY` is configured; it makes no request and fails clearly rather than silently using a
live service. A future implementation must produce original wording, never reproduce third-party
copy, retain source summaries rather than URLs, and preserve the human-review gate.

## Human review responsibilities

Reviewers must verify family and accord classifications against suitable evidence, establish note
pyramids and performance only from supportable sources, resolve every field named in
`fields_requiring_human_review`, and inspect provenance before approving a draft for a later
catalogue review. Approval in this console is not publication approval.

## Privacy and copyright guardrails

Enriched output contains a strict allowlist and excludes supplier commercial attributes. Never put
supplier files, source URLs, secrets, commercial terms, or generated private outputs in public
artifacts or version control. Store short factual source summaries only. Do not paste manufacturer,
retailer, editorial, or community descriptions; draft prose must be original.

## Streamlit demo mode and private mode

Private mode loads drafts and optional enriched profiles beneath the selected private run and saves
review decisions only beneath `data/private`. If drafts are absent, the console automatically uses
sanitised fictional enriched records. Demo records contain no real supplier or commercial data, and
demo decisions exist only in Streamlit session state and disappear when that session ends.
