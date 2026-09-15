CREATE OR REPLACE VIEW fragrance_catalogue AS
SELECT f.id, f.name, f.slug, f.concentration, f.family, f.verified, f.source_confidence,
       b.id AS brand_id, b.name AS brand_name, b.slug AS brand_slug
FROM fragrances f JOIN brands b ON b.id = f.brand_id;

CREATE OR REPLACE VIEW fragrance_provenance_summary AS
SELECT entity_id AS fragrance_id, count(*) AS source_count, max(confidence) AS highest_confidence
FROM source_provenance WHERE entity_type = 'fragrance' GROUP BY entity_id;
