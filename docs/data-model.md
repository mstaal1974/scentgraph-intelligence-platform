# Data Model

Brands own canonical fragrances. Notes and accords are governed many-to-many taxonomies. Each fragrance has at most one comparable scent vector. Directional clone relationships distinguish an alternative from its referenced original. Products map retailer-owned sellable records onto canonical fragrance intelligence without contaminating the canonical entity.

Aliases preserve source spellings. `source_provenance` attaches evidence and confidence to entities so sourced facts remain auditable rather than silently merged. Check constraints keep scores and vector dimensions bounded; uniqueness constraints prevent obvious duplicate canonical records.

The schema separates source facts, canonical identities, derived vectors, and commercial products. This protects the proprietary layer—normalisation, taxonomy, confidence decisions, vectors, mappings, and algorithms—while allowing evidence to be re-evaluated.
