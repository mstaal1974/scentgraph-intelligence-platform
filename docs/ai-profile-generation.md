# Model-backed scent profile generation

`OpenAIEnrichmentProvider` generates scent profiles — family, accords, note pyramid, mood,
occasion, season, and performance bands — from supplier identity records. It is the
model-backed half of the enrichment boundary; `OfflineHeuristicEnrichmentProvider` remains the
default and asserts no notes at all.

## Running it

```bash
export OPENAI_API_KEY=...
python scripts/enrich_private_profile_batch.py --run-id <run> --provider openai --max-profiles 25
```

`openai` is a core dependency, so no extra install step is needed. `AROMATWIN_AI_PROVIDER`
selects the default provider and `AROMATWIN_AI_ALLOW_FALLBACK` controls whether an API failure
degrades to the offline provider or raises.

Input is `data/private/runs/<run>/profiles/drafts.json`; output is `enriched_profiles.json`
beside it. The script refuses to write outside `data/private/`, and the run reports how many
model-asserted fields are waiting on review.

Review the output in the console, which shows each field against its basis:

```bash
streamlit run apps/private_profile_review_console.py
```

## What the model is and is not trusted with

The model proposes; it never decides. Two layers do the work.

**Before the request**, `sanitise_ai_identity` builds the payload from an explicit allow-list
(`IDENTITY_FIELDS` plus `SAFE_METADATA_FIELDS`). It is an allow-list rather than a deny-list, so a
new column from a supplier import cannot accidentally become part of an AI request. The request
asks for a strict JSON schema, and any API failure — rate limit, auth, connection — degrades to
the offline provider rather than crashing the batch.

**After the response**, `validate_enrichment_payload` runs. The schema guarantees the shape of the
answer; it does not guarantee a value is a real season, a sane list length, or original prose, and
it carries no notion of which fields rest on evidence. So the payload is still validated:

- drops unknown keys and any private or restricted key (prices, supplier codes, stock, ratings,
  reviews, images, URLs), at any depth;
- enforces controlled vocabularies for seasons, occasions, and the strength, longevity,
  projection, and confidence bands. **An out-of-vocabulary answer is discarded, not coerced to
  something plausible**, so it surfaces as a gap for review rather than silent bad data;
- bounds every list to 6 items and every term to 40 characters, strips markup, and deduplicates;
- rejects a description containing retail or marketing markers (`shop now`, `out of 5 stars`,
  `all rights reserved`, ™, ©) as probable copied copy;
- forces `review_status` to `needs_human_review` and `enrichment_status` to
  `enriched_pending_review`. There is no code path that returns an approved record.

An unparseable response does not lose the record: it degrades to the deterministic offline
provider, marked low confidence with a note saying the model response could not be parsed.

## Provenance is per field

`field_provenance` marks each populated field as `supplier_evidence` or `model_inference`.
Supplier-stated values always win — the model cannot overwrite a note pyramid the supplier
record asserts — and only inferred fields land in `fields_requiring_human_review`.

This exists because of the risk the design carries. **A model asked for the note pyramid of a
real fragrance returns either recalled third-party database content or a plausible invention.**
Neither is verified fact, and both are exposure under a retailer contract that presents this as
provenance-backed intelligence. Per-field marking is the mitigation: a reviewer approves
specific claims rather than a blob, and the console warns how many unverified proposals a
profile carries before the approval button.

The residual risk is real and is not solved by code: at volume, approvals can become rubber
stamps. Things that would reduce it further, in rough order of value:

1. A licensed fragrance data source, so pyramids rest on evidence rather than inference. This is
   the only change that removes the risk rather than managing it.
2. Sampling audits — re-check a random slice of approved profiles against an independent source
   and track the error rate over time.
3. Publishing confidence to retailers, so a low-confidence profile is visibly a proposal.
4. Reviewer throughput limits, so a single session cannot approve more than a human can actually
   assess.

## Cost and determinism

Generation is one request per profile at `temperature=0.2` with `response_format=json_object`.
It is not deterministic; re-running produces different proposals. The catalogue promotion path
downstream is deterministic, so variation is confined to the draft stage where review happens.
