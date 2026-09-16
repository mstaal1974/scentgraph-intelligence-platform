# Consumer Scentprint quiz contract

## Purpose and boundary

This pack defines a versioned contract for a future customer-facing preference quiz. It supplies
fixed questions, allowlisted answers, deterministic scoring rules, presentation-ready result
shapes, and fictional examples. It is stateless: it creates no account, persists no response, and
calls no external service. A Scentprint is preference guidance, not a diagnosis, personal identity
inference, or promise of attraction, confidence, status, wellbeing, or product performance.

The quiz deliberately avoids identity, contact, health, biometric, and sensitive demographic
questions. Open-ended input is disabled, reducing the chance that a participant submits private
information or third-party content. A caller supplies only a generated public alias and selected
option IDs. Consent for any future persistence, analytics, or account linking is outside this pack
and must be designed and reviewed before those capabilities exist.

## Contract

Version `1.0.0` covers scent family, intensity, fresh/warm balance, sweetness, woody/resinous,
floral, citrus/fresh, gourmand, occasion, season, mood, projection, longevity, discovery style,
and avoid-note-family sections. Every question provides its ID, section, wording, answer type,
options, scoring dimensions, required flag, safe-use hint, and privacy note.

The scorer returns weights for scent, note, accord, mood, occasion, and season preferences; bands
for intensity, sweetness, freshness, warmth, projection, longevity, and discovery preference; and
an allowlisted avoid-note-family summary. It also returns completion counts, a confidence band,
contract version, generated quiz ID, public alias, privacy status, and timestamp. Raw prose is
neither accepted nor retained.

The result payload summarizes dominant families, accords, moods, occasions, and seasons. Product
matches contain a public product ID/title/format, score band, shared preference categories, and a
scent-preference-only explanation. Production matching may use only human-approved, public-safe
catalogue projections. With no such records, only the explicit demo endpoint returns the clearly
fictional `Fictional Horizon` sample; it does not represent a real product.

## Integration

Consumer scent intelligence may later consume the vector as one structured input, without copying
private feedback into public output. Maison integration can consume the public result schema after
an explicit mapping and human review. A future Maison frontend can fetch `GET
/scentprint-quiz/contract`, render only its declared options, submit choices to `POST
/scentprint-quiz/score`, and use the returned bands and summaries. Frontend implementation belongs
in the Maison repository and is intentionally absent here.

Real deployment still requires approved product metadata, a reviewed consent/retention design,
staging validation, accessibility and content review, and an approved integration mapping. Never
commit customer records, credentials, private supplier files, seller briefs, commercial terms,
private notes, or unreviewed third-party text or media. Commercial and private fields must never
enter these public schemas, samples, exports, or explanations.

## Local operations

Build fictional CSV examples with `PYTHONPATH=src python scripts/build_scentprint_quiz_samples.py`.
Validate the contract with `PYTHONPATH=src python scripts/check_scentprint_quiz_contracts.py` and
audit artifacts with `PYTHONPATH=src python scripts/audit_scentprint_quiz_privacy.py`. JSON/CSV
exports are generated locally by `PYTHONPATH=src python scripts/export_scentprint_quiz_contracts.py`.

## Commercial entitlement boundary

The anonymous quiz contract may be represented as a public-safe API entitlement. That entitlement does not grant access to consumer-private intelligence, raw individual feedback, or internal records; those workflows remain private and manually controlled.
