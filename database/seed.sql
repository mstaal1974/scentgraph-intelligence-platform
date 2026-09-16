INSERT INTO review_statuses (code,description,terminal) VALUES
('supplier_imported','Raw supplier row imported',false),('match_candidate','Candidate identity proposed',false),
('needs_verification','Independent verification required',false),('verified_official','Official source checked',false),
('enriched_original','Original enrichment prepared',false),('approved_for_catalogue','Human-approved commercial catalogue record',true),
('rejected_low_confidence','Rejected because evidence was insufficient',true),('rejected_licensing_risk','Rejected because source permissions were unsafe',true)
ON CONFLICT DO NOTHING;
INSERT INTO reference_sources (source_name,source_type,permitted_use,commercial_use_allowed,can_copy_text,can_copy_images,can_use_for_matching,notes) VALUES
('Supplier catalogue','supplier','supplier_source',true,false,false,true,'Primary evidence of commercial availability'),
('Restricted reference dataset','dataset','restricted_non_commercial',false,false,false,true,'Matching and deduplication only')
ON CONFLICT DO NOTHING;
