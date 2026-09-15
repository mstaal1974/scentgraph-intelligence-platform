# Maison Obsidian Integration

Maison Obsidian is ScentGraph's first implementation and an API customer; it does not own or embed the platform internally. ScentGraph remains independently deployable, brand-neutral, and suitable for other retailers.

Maison Obsidian will map its product SKUs to ScentGraph fragrance IDs and call the same documented endpoints used by any licensee. Its website or commerce services may request fragrance details, similar scents, clone matches, recommendations, and Scentprint matches. Retail prices, stock, checkout, merchandising, and customer presentation stay in Maison Obsidian systems.

A future integration will use scoped credentials, tenant configuration, quotas, metering, contract-version headers, and caching rules. No Maison Obsidian catalogue assumptions or branding belong in core taxonomy, import, ranking, or persistence code. This foundation defines the boundary only and performs no live integration.
