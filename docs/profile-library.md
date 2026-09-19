# Fragrance profile library

The repository ships a **first-party profile library**: 48 original profiles across 12 fictional
houses, carrying reviewed taxonomy, derived scent vectors, recommendations, and inspired-by
relationships. It exists so the ingestion → review → promotion → vector → recommendation →
retailer-API path runs end to end on realistic, discriminative data.

Everything in it is original AromaTwin content. No real brand, composition, or marketing copy is
reproduced, and nothing derives from a third-party fragrance database. **Building a library of
real-brand profiles is a separate commercial step that needs a permitted source**; this seed does
not substitute for one, and the note names it uses are generic perfumery ingredients.

## Building it

```bash
python scripts/build_profile_library.py
python scripts/build_scent_vectors.py --approve
python scripts/build_recommendations.py
```

The seed is pushed through the real gates rather than written straight to the catalogue. Each
profile becomes an enrichment review under `data/library/`, and `promote_enrichment_review`
validates provenance, confidence, licensing risk, restricted content, and supplier-private
columns before anything reaches `data/catalogue_fragrances.csv`.

`--approve` records review sign-off on generated vectors. Generation alone leaves a vector at
`needs_human_review`, which the Maison gate excludes by design. The flag is only appropriate for
catalogue content whose source fields are known public-safe, such as this seed; it still runs
`approve_scent_vector`, so the confidence and content gates apply.

`data/enrichment_reviews.csv` is the human review queue for records still awaiting a decision and
is **not** an input to promotion. The library keeps its own inputs under `data/library/` so the
two are never confused.

## Shape

| Artifact | Rows | Notes |
| --- | --- | --- |
| `data/catalogue_fragrances.csv` | 48 | Approved public projection, now carrying taxonomy |
| `data/scent_vectors.csv` | 48 | 23 dimensions, 44 distinct signatures |
| `data/recommendations.csv` | 480 | Derived from catalogue and vectors only |
| `data/clone_relationships.csv` | 40 | Inspired-by pairs within a shared direction |
| `data/profile_drafts.csv` | 3 | Drafts that deliberately do not clear the gates |

Eight coherent scent directions (woody chypre, citrus aromatic, fresh aquatic, aromatic fougere,
white floral, amber floral, amber woody, gourmand) are distributed evenly across the houses. Each
profile carries a signature note and accord so profiles sharing a direction do not collapse to an
identical vector.

The three pending drafts are deliberate. A library where every candidate is promoted is not a
realistic one, and the review console and readiness reporting need real work to show. They stay at
draft stage and never reach the catalogue or the retailer API.

## Catalogue taxonomy

The public catalogue carries `family`, `notes`, `accords`, `mood`, `occasion`, and `season`
alongside identity. These are the structured fields `scent_vector_engine` reads. Before they
existed the catalogue held only a description and a concentration, the engine's keyword lexicon
matched nothing, and every generated vector was zero across all 23 dimensions while still
reporting a non-zero confidence score.

Vector generation weights reviewed taxonomy above prose (`STRUCTURED_WEIGHT` against
`NARRATIVE_WEIGHT`) and matches on stemmed tokens, so "woods" and "woody" unify to "wood".
Matching stays exact after stemming: a shared-prefix rule would let the `season` column collide
with the `sea` marine keyword on every record.

## Known limits

- Lexicon dimensions overlap (`woody`/`green` share *forest* and *grove*, `aquatic`/`marine` share
  *ocean* and *sea*), so correlated dimensions inflate similarity. Calibration is outstanding.
- The library is served from CSV through a module-level singleton, so catalogue changes need a
  process restart and lookups scan linearly. Moving it onto the Postgres schema the Alembic
  revisions already define is the next structural step.
- Profiles are first-party and fictional. They validate the pipeline; they are not a commercial
  catalogue.
