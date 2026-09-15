INSERT INTO brands (id, name, slug, country, website, verified) VALUES
 (1, 'Tom Ford', 'tom-ford', 'United States', 'https://www.tomford.com/', false),
 (2, 'Maison Francis Kurkdjian', 'maison-francis-kurkdjian', 'France', 'https://www.franciskurkdjian.com/', false)
ON CONFLICT DO NOTHING;
INSERT INTO fragrances (id, brand_id, name, slug, concentration, family, verified, source_confidence) VALUES
 (1, 1, 'Lost Cherry', 'lost-cherry', 'eau de parfum', 'amber floral', false, 0.500),
 (2, 2, 'Baccarat Rouge 540', 'baccarat-rouge-540', 'eau de parfum', 'amber floral', false, 0.500)
ON CONFLICT DO NOTHING;
INSERT INTO notes (id, name, slug, note_type) VALUES (1, 'Bergamot', 'bergamot', 'top'), (2, 'Amber', 'amber', 'base') ON CONFLICT DO NOTHING;
INSERT INTO accords (id, name, slug) VALUES (1, 'Woody', 'woody') ON CONFLICT DO NOTHING;
SELECT setval(pg_get_serial_sequence('brands','id'), (SELECT max(id) FROM brands));
SELECT setval(pg_get_serial_sequence('fragrances','id'), (SELECT max(id) FROM fragrances));
