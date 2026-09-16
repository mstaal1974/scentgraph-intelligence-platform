from aromatwin.routers import (
    brands,
    clone_matches,
    enrichment_reviews,
    fragrances,
    health,
    match_candidates,
    notes,
    recommendations,
    scentprint,
    search,
    supplier_items,
)

ROUTERS = (
    health.router,
    supplier_items.router,
    match_candidates.router,
    enrichment_reviews.router,
    brands.router,
    fragrances.router,
    notes.router,
    search.router,
    recommendations.router,
    scentprint.router,
    clone_matches.router,
)
