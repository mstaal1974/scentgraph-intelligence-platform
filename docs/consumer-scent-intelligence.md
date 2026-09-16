# Consumer scent intelligence foundation

This internal AromaTwin layer records scent **preferences**, not identity, demographics, health, psychology, or other sensitive traits. It is a service-layer foundation for future quizzes, recommendations, scent twins, wardrobes, reviewed social proof, and product discovery—not a customer account system, public review community, social network, campaign generator, or MicroPromote integration.

## Scentprint

A Scentprint is a pseudonymous preference profile built from structured quiz answers: liked and disliked scent families, notes and accords; moods, occasions and seasons; intensity, projection and longevity preferences; bounded scent-dimension preferences; product formats; and stated familiarity. Creation never infers gender, age, income, ethnicity, health, personality, or protected traits. Matching compares only supplied structured fields. The weak, moderate, strong and excellent bands are accompanied by concise shared-field reasons; absent evidence produces a weak result rather than an invented note, accord, season, mood, or claim.

## Structured feedback and aggregation

Feedback connects a private Scentprint ID to a fragrance, product, or variant and captures rating bands, stated purchase intent, perceived performance bands, contexts, and explicitly liked/disliked notes. A private free-text field is never returned by the safe projection. An optional public-safe quote remains hidden until human approval; submission never publishes it automatically.

Community scent intelligence groups structured feedback by fragrance/product. Outputs contain counts, bands, common structured contexts, and an original summary. They contain no consumer ID or individual wardrobe/feedback record. Fewer than the configured minimum responses yields `insufficient_data`; sufficient results still require review. This signal supplements and never overwrites approved expert or provenance-backed fragrance data.

## Private scent wardrobe

Wardrobe items represent owns, tried, wants-to-try, not-for-me, gifted, considering-full-size, and reordered states. Gap analysis can suggest a tester, 50 ml upgrade, diffuser, bundle, or avoiding a similar profile. Individual wardrobe details are private-key protected and are not public social activity. Any future public insight must be anonymised and thresholded first.

## Data boundary and downstream value

Private records may contain internal IDs and an individual's private feedback note. Public-safe projections use only pseudonymous aliases or aggregates and exclude contact information, raw notes, individual behaviour, seller-private data, and every supplier-commercial field. Sample data is fictional. Third-party descriptions, reviews, ratings, comments, images, and UGC are not ingested or republished.

These structured signals can later improve recommendation fit, reveal where consumer perception differs from an approved profile without replacing it, highlight catalogue gaps, and inform review-gated product readiness or launch decisions. Public social proof and consumer community features require separate consent, moderation, anti-abuse, and publication design. MicroPromote is also deliberately excluded: marketing activation must remain a later, separately governed layer.

## API and offline workflow

`/consumer-scent` routes are internal and private-key protected. Default Scentprint and feedback responses are allowlisted safe projections. Offline scripts generate fictional samples, aggregate optional private input into `data/private/reports/`, and audit tracked sample files. Private reports must remain ignored and untracked.
