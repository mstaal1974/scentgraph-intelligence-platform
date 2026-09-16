CREATE OR REPLACE VIEW supplier_review_queue AS
SELECT si.id,si.supplier_name,si.supplier_brand_raw,si.supplier_name_raw,si.normalised_brand,si.normalised_name,si.variant_marker,si.status,count(mc.id) AS candidate_count
FROM supplier_items si LEFT JOIN match_candidates mc ON mc.supplier_item_id=si.id
GROUP BY si.id;

CREATE OR REPLACE VIEW approved_catalogue AS
SELECT f.id,f.name,f.slug,f.concentration,f.family,b.name AS brand_name,f.source_confidence
FROM fragrances f JOIN brands b ON b.id=f.brand_id
WHERE f.review_status='approved_for_catalogue' AND b.review_status='approved_for_catalogue';

CREATE OR REPLACE VIEW licensing_risk_queue AS
SELECT mc.id AS match_candidate_id,mc.supplier_item_id,rs.source_name,rs.permitted_use,rs.commercial_use_allowed,mc.review_status
FROM match_candidates mc JOIN reference_sources rs ON rs.id=mc.reference_source_id
WHERE rs.commercial_use_allowed=false AND mc.review_status NOT LIKE 'rejected_%';
