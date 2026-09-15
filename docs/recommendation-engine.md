# Recommendation Engine

The service boundary accepts a strategy and optional context. Supported strategy vocabulary is `similarity`, `season`, `occasion`, `mood`, and `clone_alternative`; `layering` is reserved for future implementation.

Similarity uses scent-vector cosine similarity. Contextual strategies will combine vector fit with curated season, occasion, and mood signals. Clone alternatives use directional, evidence-backed mappings. Future ranking must expose reason codes, confidence, filters, and deterministic model versions so partners can explain and reproduce outcomes.
