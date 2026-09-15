BEGIN;
CREATE TABLE brands (
 id BIGSERIAL PRIMARY KEY, name TEXT NOT NULL, slug TEXT NOT NULL UNIQUE, country TEXT, website TEXT,
 verified BOOLEAN NOT NULL DEFAULT FALSE, created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE fragrances (
 id BIGSERIAL PRIMARY KEY, brand_id BIGINT NOT NULL REFERENCES brands(id) ON DELETE RESTRICT, name TEXT NOT NULL, slug TEXT NOT NULL,
 concentration TEXT, description TEXT, family TEXT, gender TEXT, release_year SMALLINT CHECK (release_year BETWEEN 1700 AND 2200), perfumer TEXT,
 verified BOOLEAN NOT NULL DEFAULT FALSE, source_confidence NUMERIC(4,3) NOT NULL DEFAULT 0 CHECK (source_confidence BETWEEN 0 AND 1),
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now(), UNIQUE (brand_id, slug, concentration)
);
CREATE TABLE notes (id BIGSERIAL PRIMARY KEY, name TEXT NOT NULL, slug TEXT NOT NULL UNIQUE, note_type TEXT NOT NULL CHECK (note_type IN ('top','middle','base','general')), description TEXT);
CREATE TABLE fragrance_notes (
 fragrance_id BIGINT NOT NULL REFERENCES fragrances(id) ON DELETE CASCADE, note_id BIGINT NOT NULL REFERENCES notes(id) ON DELETE RESTRICT,
 pyramid_level TEXT NOT NULL CHECK (pyramid_level IN ('top','middle','base','general')), display_order INTEGER NOT NULL DEFAULT 0 CHECK (display_order >= 0),
 strength NUMERIC(4,3) CHECK (strength BETWEEN 0 AND 1), PRIMARY KEY (fragrance_id, note_id, pyramid_level)
);
CREATE TABLE accords (id BIGSERIAL PRIMARY KEY, name TEXT NOT NULL, slug TEXT NOT NULL UNIQUE, description TEXT);
CREATE TABLE fragrance_accords (
 fragrance_id BIGINT NOT NULL REFERENCES fragrances(id) ON DELETE CASCADE, accord_id BIGINT NOT NULL REFERENCES accords(id) ON DELETE RESTRICT,
 weight NUMERIC(4,3) NOT NULL CHECK (weight BETWEEN 0 AND 1), PRIMARY KEY (fragrance_id, accord_id)
);
CREATE TABLE scent_vectors (
 fragrance_id BIGINT PRIMARY KEY REFERENCES fragrances(id) ON DELETE CASCADE,
 warm NUMERIC(4,3) NOT NULL DEFAULT 0, fresh NUMERIC(4,3) NOT NULL DEFAULT 0, sweet NUMERIC(4,3) NOT NULL DEFAULT 0, dark NUMERIC(4,3) NOT NULL DEFAULT 0,
 woody NUMERIC(4,3) NOT NULL DEFAULT 0, floral NUMERIC(4,3) NOT NULL DEFAULT 0, spicy NUMERIC(4,3) NOT NULL DEFAULT 0, fruit NUMERIC(4,3) NOT NULL DEFAULT 0,
 green NUMERIC(4,3) NOT NULL DEFAULT 0, aquatic NUMERIC(4,3) NOT NULL DEFAULT 0, marine NUMERIC(4,3) NOT NULL DEFAULT 0, leather NUMERIC(4,3) NOT NULL DEFAULT 0,
 powdery NUMERIC(4,3) NOT NULL DEFAULT 0, resinous NUMERIC(4,3) NOT NULL DEFAULT 0, smoky NUMERIC(4,3) NOT NULL DEFAULT 0, gourmand NUMERIC(4,3) NOT NULL DEFAULT 0,
 citrus NUMERIC(4,3) NOT NULL DEFAULT 0, aromatic NUMERIC(4,3) NOT NULL DEFAULT 0, luxury NUMERIC(4,3) NOT NULL DEFAULT 0, projection NUMERIC(4,3) NOT NULL DEFAULT 0,
 longevity NUMERIC(4,3) NOT NULL DEFAULT 0,
 CONSTRAINT scent_vectors_range CHECK (warm BETWEEN 0 AND 1 AND fresh BETWEEN 0 AND 1 AND sweet BETWEEN 0 AND 1 AND dark BETWEEN 0 AND 1 AND woody BETWEEN 0 AND 1 AND floral BETWEEN 0 AND 1 AND spicy BETWEEN 0 AND 1 AND fruit BETWEEN 0 AND 1 AND green BETWEEN 0 AND 1 AND aquatic BETWEEN 0 AND 1 AND marine BETWEEN 0 AND 1 AND leather BETWEEN 0 AND 1 AND powdery BETWEEN 0 AND 1 AND resinous BETWEEN 0 AND 1 AND smoky BETWEEN 0 AND 1 AND gourmand BETWEEN 0 AND 1 AND citrus BETWEEN 0 AND 1 AND aromatic BETWEEN 0 AND 1 AND luxury BETWEEN 0 AND 1 AND projection BETWEEN 0 AND 1 AND longevity BETWEEN 0 AND 1)
);
CREATE TABLE clone_relationships (
 id BIGSERIAL PRIMARY KEY, clone_fragrance_id BIGINT NOT NULL REFERENCES fragrances(id) ON DELETE CASCADE,
 original_fragrance_id BIGINT NOT NULL REFERENCES fragrances(id) ON DELETE CASCADE, relationship_type TEXT NOT NULL,
 similarity_score NUMERIC(4,3) CHECK (similarity_score BETWEEN 0 AND 1), performance_difference NUMERIC(6,3), longevity_difference NUMERIC(6,3),
 projection_difference NUMERIC(6,3), price_difference NUMERIC(12,2), notes TEXT,
 CHECK (clone_fragrance_id <> original_fragrance_id), UNIQUE (clone_fragrance_id, original_fragrance_id, relationship_type)
);
CREATE TABLE products (
 id BIGSERIAL PRIMARY KEY, fragrance_id BIGINT NOT NULL REFERENCES fragrances(id) ON DELETE RESTRICT, brand_owner TEXT NOT NULL,
 product_name TEXT NOT NULL, product_type TEXT, size_ml NUMERIC(8,2) CHECK (size_ml > 0), sku TEXT NOT NULL, price NUMERIC(12,2) CHECK (price >= 0),
 active BOOLEAN NOT NULL DEFAULT TRUE, UNIQUE (brand_owner, sku)
);
CREATE TABLE aliases (
 id BIGSERIAL PRIMARY KEY, entity_type TEXT NOT NULL, entity_id BIGINT NOT NULL, alias TEXT NOT NULL, source TEXT,
 UNIQUE (entity_type, entity_id, alias)
);
CREATE TABLE source_provenance (
 id BIGSERIAL PRIMARY KEY, entity_type TEXT NOT NULL, entity_id BIGINT NOT NULL, source_name TEXT NOT NULL, source_type TEXT NOT NULL,
 source_reference TEXT, confidence NUMERIC(4,3) NOT NULL CHECK (confidence BETWEEN 0 AND 1), notes TEXT, created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX fragrances_brand_id_idx ON fragrances(brand_id);
CREATE INDEX aliases_lookup_idx ON aliases(entity_type, lower(alias));
CREATE INDEX provenance_entity_idx ON source_provenance(entity_type, entity_id);
COMMIT;
