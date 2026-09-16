# Licensing Guardrails

> “Restricted or non-commercial fragrance datasets may be used only for discovery, matching, deduplication, and research. They must not be copied into production commercial catalogue records unless a suitable commercial licence or permission is documented.”

Reference sources have explicit capabilities: commercial use, text copying, image copying, and matching. A safe restricted/non-commercial default is `commercial_use_allowed=false`, `can_copy_text=false`, `can_copy_images=false`, and `can_use_for_matching=true`.

Reference-derived identifiers may create candidates only. Promotion requires an independently reviewed enrichment supported by an official, supplier, or licensed-commercial source. The platform rejects direct approval when provenance is reference-only, restricted, unknown, or otherwise disallows commercial use. No automated scraper for restricted sites belongs in AromaTwin.
