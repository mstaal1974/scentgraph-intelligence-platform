BEGIN;

CREATE TABLE review_statuses (
  code TEXT PRIMARY KEY,
  description TEXT NOT NULL,
  terminal BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE reference_sources (
  id BIGSERIAL PRIMARY KEY,
  source_name TEXT NOT NULL UNIQUE,
  source_type TEXT NOT NULL,
  permitted_use TEXT NOT NULL CHECK (permitted_use IN ('official_source','supplier_source','reference_only','restricted_non_commercial','licensed_commercial','unknown')),
  commercial_use_allowed BOOLEAN NOT NULL DEFAULT FALSE,
  can_copy_text BOOLEAN NOT NULL DEFAULT FALSE,
  can_copy_images BOOLEAN NOT NULL DEFAULT FALSE,
  can_use_for_matching BOOLEAN NOT NULL DEFAULT FALSE,
  notes TEXT,
  CHECK (commercial_use_allowed OR (can_copy_text = FALSE AND can_copy_images = FALSE))
);

CREATE TABLE import_batches (
  id UUID PRIMARY KEY,
  supplier_name TEXT NOT NULL,
  source_file TEXT NOT NULL,
  source_sha256 TEXT NOT NULL,
  row_count INTEGER NOT NULL DEFAULT 0 CHECK (row_count >= 0),
  status TEXT NOT NULL REFERENCES review_statuses(code),
  imported_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (supplier_name, source_sha256)
);

CREATE TABLE supplier_items (
  id BIGSERIAL PRIMARY KEY,
  supplier_name TEXT NOT NULL,
  supplier_brand_raw TEXT NOT NULL,
  supplier_name_raw TEXT NOT NULL,
  supplier_ori_raw TEXT,
  supplier_cn_code TEXT,
  quantity NUMERIC(12,3) CHECK (quantity >= 0),
  aed_price NUMERIC(12,2) CHECK (aed_price >= 0),
  usd_price NUMERIC(12,2) CHECK (usd_price >= 0),
  source_file TEXT NOT NULL,
  source_row_number INTEGER NOT NULL CHECK (source_row_number > 0),
  imported_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  import_batch_id UUID NOT NULL REFERENCES import_batches(id) ON DELETE RESTRICT,
  normalised_brand TEXT NOT NULL,
  normalised_name TEXT NOT NULL,
  variant_marker TEXT,
  status TEXT NOT NULL REFERENCES review_statuses(code),
  UNIQUE (import_batch_id, source_row_number)
);

CREATE TABLE match_candidates (
  id BIGSERIAL PRIMARY KEY,
  supplier_item_id BIGINT NOT NULL REFERENCES supplier_items(id) ON DELETE CASCADE,
  candidate_brand TEXT NOT NULL,
  candidate_fragrance_name TEXT NOT NULL,
  candidate_concentration TEXT,
  candidate_source_type TEXT NOT NULL,
  candidate_source_reference TEXT,
  reference_source_id BIGINT REFERENCES reference_sources(id) ON DELETE RESTRICT,
  match_method TEXT NOT NULL,
  match_confidence NUMERIC(4,3) NOT NULL CHECK (match_confidence BETWEEN 0 AND 1),
  match_notes TEXT,
  review_status TEXT NOT NULL REFERENCES review_statuses(code),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  reviewed_at TIMESTAMPTZ,
  UNIQUE (supplier_item_id, candidate_brand, candidate_fragrance_name, candidate_source_type)
);

CREATE TABLE profile_drafts (
  id BIGSERIAL PRIMARY KEY,
  supplier_item_id BIGINT NOT NULL REFERENCES supplier_items(id) ON DELETE RESTRICT,
  match_candidate_id BIGINT REFERENCES match_candidates(id) ON DELETE SET NULL,
  candidate_brand TEXT NOT NULL,
  candidate_fragrance_name TEXT NOT NULL,
  likely_original_brand TEXT,
  likely_original_name TEXT,
  profile_title TEXT NOT NULL,
  description_original TEXT NOT NULL,
  description_generation_method TEXT NOT NULL,
  top_notes_json JSONB NOT NULL DEFAULT '[]',
  heart_notes_json JSONB NOT NULL DEFAULT '[]',
  base_notes_json JSONB NOT NULL DEFAULT '[]',
  accords_json JSONB NOT NULL DEFAULT '[]',
  fragrance_family TEXT,
  gender TEXT,
  season_json JSONB NOT NULL DEFAULT '[]',
  occasion_json JSONB NOT NULL DEFAULT '[]',
  mood_json JSONB NOT NULL DEFAULT '[]',
  scent_vector_json JSONB NOT NULL DEFAULT '{}',
  confidence_score NUMERIC(4,3) NOT NULL CHECK (confidence_score BETWEEN 0 AND 1),
  source_confidence NUMERIC(4,3) NOT NULL CHECK (source_confidence BETWEEN 0 AND 1),
  restricted_content_detected BOOLEAN NOT NULL DEFAULT FALSE,
  provenance_notes TEXT NOT NULL,
  review_status TEXT NOT NULL CHECK (review_status IN ('needs_human_review','approved_for_catalogue','rejected_low_confidence','rejected_licensing_risk','rejected_duplicate','requires_more_sources')),
  reviewer TEXT,
  rejection_reason TEXT,
  approved_at TIMESTAMPTZ,
  rejected_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (review_status <> 'approved_for_catalogue' OR (reviewer IS NOT NULL AND approved_at IS NOT NULL)),
  CHECK (review_status <> 'approved_for_catalogue' OR (restricted_content_detected = FALSE AND source_confidence >= 0.700)),
  CHECK (review_status NOT LIKE 'rejected_%' OR (reviewer IS NOT NULL AND rejected_at IS NOT NULL AND rejection_reason IS NOT NULL))
);
CREATE INDEX profile_drafts_review_queue_idx ON profile_drafts(review_status, created_at);
CREATE UNIQUE INDEX profile_drafts_active_candidate_idx ON profile_drafts(supplier_item_id, match_candidate_id) WHERE review_status IN ('needs_human_review','requires_more_sources','approved_for_catalogue');


CREATE TABLE enrichment_sources (
  id BIGSERIAL PRIMARY KEY, source_name TEXT NOT NULL, source_type TEXT NOT NULL,
  source_url TEXT, source_title TEXT, source_domain TEXT,
  commercial_use_allowed BOOLEAN NOT NULL DEFAULT FALSE,
  can_copy_text BOOLEAN NOT NULL DEFAULT FALSE, can_copy_images BOOLEAN NOT NULL DEFAULT FALSE,
  can_use_for_factual_reference BOOLEAN NOT NULL DEFAULT FALSE, can_use_for_matching BOOLEAN NOT NULL DEFAULT FALSE,
  source_confidence NUMERIC(4,3) NOT NULL DEFAULT 0 CHECK (source_confidence BETWEEN 0 AND 1),
  notes TEXT, created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (commercial_use_allowed OR (can_copy_text = FALSE AND can_copy_images = FALSE))
);

CREATE TABLE enrichment_reviews (
  id BIGSERIAL PRIMARY KEY,
  match_candidate_id BIGINT UNIQUE REFERENCES match_candidates(id) ON DELETE RESTRICT,
  profile_draft_id BIGINT UNIQUE REFERENCES profile_drafts(id) ON DELETE RESTRICT,
  approved_brand TEXT NOT NULL,
  approved_fragrance_name TEXT NOT NULL,
  official_source_url TEXT,
  official_source_checked_at TIMESTAMPTZ,
  source_summary TEXT,
  description_original TEXT,
  note_pyramid_json JSONB NOT NULL DEFAULT '{}',
  description_ai_generated BOOLEAN NOT NULL DEFAULT FALSE,
  description_reviewed BOOLEAN NOT NULL DEFAULT FALSE,
  top_notes JSONB NOT NULL DEFAULT '[]', heart_notes JSONB NOT NULL DEFAULT '[]', base_notes JSONB NOT NULL DEFAULT '[]',
  accords JSONB NOT NULL DEFAULT '[]', fragrance_family TEXT, gender TEXT,
  season JSONB NOT NULL DEFAULT '[]', occasion JSONB NOT NULL DEFAULT '[]', mood JSONB NOT NULL DEFAULT '[]',
  scent_vector_status TEXT,
  scent_vector_json JSONB NOT NULL DEFAULT '{}',
  enrichment_confidence NUMERIC(4,3) NOT NULL DEFAULT 0 CHECK (enrichment_confidence BETWEEN 0 AND 1),
  licensing_risk TEXT NOT NULL DEFAULT 'high' CHECK (licensing_risk IN ('low','medium','high')),
  copied_text_detected BOOLEAN NOT NULL DEFAULT FALSE,
  review_status TEXT NOT NULL REFERENCES review_statuses(code),
  reviewer TEXT,
  review_notes TEXT,
  approved_at TIMESTAMPTZ,
  rejected_at TIMESTAMPTZ,
  source_confidence NUMERIC(4,3) NOT NULL DEFAULT 0 CHECK (source_confidence BETWEEN 0 AND 1),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (profile_draft_id IS NOT NULL OR match_candidate_id IS NOT NULL),
  CHECK (review_status <> 'approved_for_catalogue' OR (description_reviewed AND reviewer IS NOT NULL AND approved_at IS NOT NULL AND enrichment_confidence >= 0.700 AND licensing_risk = 'low' AND copied_text_detected = FALSE))
);


CREATE TABLE profile_source_links (
  id BIGSERIAL PRIMARY KEY, profile_draft_id BIGINT NOT NULL REFERENCES profile_drafts(id) ON DELETE CASCADE,
  enrichment_source_id BIGINT NOT NULL REFERENCES enrichment_sources(id) ON DELETE RESTRICT,
  usage_type TEXT NOT NULL, confidence NUMERIC(4,3) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
  notes TEXT, created_at TIMESTAMPTZ NOT NULL DEFAULT now(), UNIQUE(profile_draft_id,enrichment_source_id,usage_type)
);
CREATE TABLE profile_enrichment_events (
  id BIGSERIAL PRIMARY KEY, profile_draft_id BIGINT NOT NULL REFERENCES profile_drafts(id) ON DELETE CASCADE,
  event_type TEXT NOT NULL, event_summary TEXT NOT NULL, actor TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX enrichment_reviews_status_idx ON enrichment_reviews(review_status,created_at);
CREATE INDEX profile_enrichment_events_profile_idx ON profile_enrichment_events(profile_draft_id,created_at);

CREATE TABLE brands (
  id BIGSERIAL PRIMARY KEY, name TEXT NOT NULL, slug TEXT NOT NULL UNIQUE, country TEXT, website TEXT,
  verified BOOLEAN NOT NULL DEFAULT FALSE, review_status TEXT NOT NULL REFERENCES review_statuses(code),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE fragrances (
  id BIGSERIAL PRIMARY KEY, brand_id BIGINT NOT NULL REFERENCES brands(id) ON DELETE RESTRICT,
  enrichment_review_id BIGINT NOT NULL UNIQUE REFERENCES enrichment_reviews(id) ON DELETE RESTRICT,
  name TEXT NOT NULL, slug TEXT NOT NULL, concentration TEXT, description TEXT, family TEXT, gender TEXT,
  release_year SMALLINT CHECK (release_year BETWEEN 1700 AND 2200), perfumer TEXT,
  verified BOOLEAN NOT NULL DEFAULT FALSE, source_confidence NUMERIC(4,3) NOT NULL DEFAULT 0 CHECK (source_confidence BETWEEN 0 AND 1),
  review_status TEXT NOT NULL REFERENCES review_statuses(code),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (brand_id, slug, concentration),
  CHECK (verified = FALSE OR review_status = 'approved_for_catalogue')
);
CREATE TABLE notes (id BIGSERIAL PRIMARY KEY, name TEXT NOT NULL, slug TEXT NOT NULL UNIQUE, note_type TEXT NOT NULL CHECK (note_type IN ('top','middle','base','general')), description TEXT);
CREATE TABLE fragrance_notes (fragrance_id BIGINT NOT NULL REFERENCES fragrances(id) ON DELETE CASCADE, note_id BIGINT NOT NULL REFERENCES notes(id) ON DELETE RESTRICT, pyramid_level TEXT NOT NULL CHECK (pyramid_level IN ('top','middle','base','general')), display_order INTEGER NOT NULL DEFAULT 0 CHECK (display_order >= 0), strength NUMERIC(4,3) CHECK (strength BETWEEN 0 AND 1), PRIMARY KEY (fragrance_id,note_id,pyramid_level));
CREATE TABLE accords (id BIGSERIAL PRIMARY KEY, name TEXT NOT NULL, slug TEXT NOT NULL UNIQUE, description TEXT);
CREATE TABLE fragrance_accords (fragrance_id BIGINT NOT NULL REFERENCES fragrances(id) ON DELETE CASCADE, accord_id BIGINT NOT NULL REFERENCES accords(id) ON DELETE RESTRICT, weight NUMERIC(4,3) NOT NULL CHECK (weight BETWEEN 0 AND 1), PRIMARY KEY (fragrance_id,accord_id));

CREATE TABLE scent_vectors (
  fragrance_id BIGINT PRIMARY KEY REFERENCES fragrances(id) ON DELETE CASCADE,
  warm NUMERIC(4,3) NOT NULL DEFAULT 0, fresh NUMERIC(4,3) NOT NULL DEFAULT 0, sweet NUMERIC(4,3) NOT NULL DEFAULT 0, dark NUMERIC(4,3) NOT NULL DEFAULT 0,
  woody NUMERIC(4,3) NOT NULL DEFAULT 0, floral NUMERIC(4,3) NOT NULL DEFAULT 0, spicy NUMERIC(4,3) NOT NULL DEFAULT 0, fruit NUMERIC(4,3) NOT NULL DEFAULT 0,
  green NUMERIC(4,3) NOT NULL DEFAULT 0, aquatic NUMERIC(4,3) NOT NULL DEFAULT 0, marine NUMERIC(4,3) NOT NULL DEFAULT 0, leather NUMERIC(4,3) NOT NULL DEFAULT 0,
  powdery NUMERIC(4,3) NOT NULL DEFAULT 0, resinous NUMERIC(4,3) NOT NULL DEFAULT 0, smoky NUMERIC(4,3) NOT NULL DEFAULT 0, gourmand NUMERIC(4,3) NOT NULL DEFAULT 0,
  citrus NUMERIC(4,3) NOT NULL DEFAULT 0, aromatic NUMERIC(4,3) NOT NULL DEFAULT 0, luxury NUMERIC(4,3) NOT NULL DEFAULT 0, projection NUMERIC(4,3) NOT NULL DEFAULT 0, longevity NUMERIC(4,3) NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'estimated',
  CHECK (warm BETWEEN 0 AND 1 AND fresh BETWEEN 0 AND 1 AND sweet BETWEEN 0 AND 1 AND dark BETWEEN 0 AND 1 AND woody BETWEEN 0 AND 1 AND floral BETWEEN 0 AND 1 AND spicy BETWEEN 0 AND 1 AND fruit BETWEEN 0 AND 1 AND green BETWEEN 0 AND 1 AND aquatic BETWEEN 0 AND 1 AND marine BETWEEN 0 AND 1 AND leather BETWEEN 0 AND 1 AND powdery BETWEEN 0 AND 1 AND resinous BETWEEN 0 AND 1 AND smoky BETWEEN 0 AND 1 AND gourmand BETWEEN 0 AND 1 AND citrus BETWEEN 0 AND 1 AND aromatic BETWEEN 0 AND 1 AND luxury BETWEEN 0 AND 1 AND projection BETWEEN 0 AND 1 AND longevity BETWEEN 0 AND 1)
);
CREATE TABLE clone_relationships (
  id BIGSERIAL PRIMARY KEY, supplier_item_id BIGINT REFERENCES supplier_items(id) ON DELETE RESTRICT,
  clone_fragrance_id BIGINT REFERENCES fragrances(id) ON DELETE CASCADE, original_fragrance_id BIGINT NOT NULL REFERENCES fragrances(id) ON DELETE CASCADE,
  product_id BIGINT, relationship_type TEXT NOT NULL, similarity_score NUMERIC(4,3) CHECK (similarity_score BETWEEN 0 AND 1),
  score_status TEXT NOT NULL DEFAULT 'estimated' CHECK (score_status IN ('estimated','reviewed')),
  difference_summary TEXT, performance_notes TEXT, review_status TEXT NOT NULL REFERENCES review_statuses(code),
  CHECK (clone_fragrance_id IS NULL OR clone_fragrance_id <> original_fragrance_id)
);
CREATE TABLE products (id BIGSERIAL PRIMARY KEY, fragrance_id BIGINT REFERENCES fragrances(id) ON DELETE RESTRICT, supplier_item_id BIGINT REFERENCES supplier_items(id) ON DELETE RESTRICT, brand_owner TEXT NOT NULL, product_name TEXT NOT NULL, product_type TEXT, size_ml NUMERIC(8,2) CHECK (size_ml > 0), sku TEXT NOT NULL, price NUMERIC(12,2) CHECK (price >= 0), active BOOLEAN NOT NULL DEFAULT TRUE, UNIQUE (brand_owner,sku));
ALTER TABLE clone_relationships ADD CONSTRAINT clone_product_fk FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL;
CREATE TABLE aliases (id BIGSERIAL PRIMARY KEY, entity_type TEXT NOT NULL, entity_id BIGINT NOT NULL, alias TEXT NOT NULL, source TEXT, UNIQUE(entity_type,entity_id,alias));
CREATE TABLE source_provenance (
  id BIGSERIAL PRIMARY KEY, entity_type TEXT NOT NULL, entity_id BIGINT NOT NULL,
  source_name TEXT NOT NULL, source_type TEXT NOT NULL, source_reference TEXT, source_url TEXT,
  licence_status TEXT NOT NULL, commercial_use_allowed BOOLEAN NOT NULL DEFAULT FALSE,
  confidence NUMERIC(4,3) NOT NULL CHECK (confidence BETWEEN 0 AND 1), notes TEXT, created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX supplier_items_normalised_idx ON supplier_items(normalised_brand,normalised_name);
CREATE INDEX match_candidates_supplier_idx ON match_candidates(supplier_item_id,review_status);
CREATE INDEX provenance_entity_idx ON source_provenance(entity_type,entity_id);
COMMIT;
