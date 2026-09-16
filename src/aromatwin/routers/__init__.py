from aromatwin.routers import (
    brands,
    clone_matches,
    enrichment,
    fragrances,
    health,
    match_candidates,
    notes,
    profile_drafts,
    recommendations,
    scentprint,
    search,
    supplier_items,
)

ROUTERS = (
    health.router,
    supplier_items.router,
    match_candidates.router,
    profile_drafts.router,
    enrichment.router,
    brands.router,
    fragrances.router,
    notes.router,
    search.router,
    recommendations.router,
    scentprint.router,
    clone_matches.router,
)
