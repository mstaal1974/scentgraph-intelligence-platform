# Architecture

AromaTwin uses four deliberately separated layers:

1. **Supplier availability:** immutable raw supplier rows and import batches establish what can be purchased.
2. **Candidate matching:** reversible, non-published hypotheses link supplier rows to possible commercial fragrances.
3. **Independent enrichment:** original descriptions and verified facts pass a human review workflow.
4. **Proprietary intelligence:** vectors, clone assessments, recommendation signals, Scentprints, and retailer product mappings.

FastAPI exposes typed OpenAPI contracts; services enforce workflow rules; SQLAlchemy models isolate persistence; PostgreSQL stores operational state. Pandas supports CSV/XLSX staging. No source may bypass candidate and review boundaries. No retailer has direct table access.

Authentication, metering, frontend, commerce, production deployment, and live retailer integration are intentionally deferred.
