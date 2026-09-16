from aromatwin.routers import (
    admin_review,
    brands,
    catalogue,
    clone_matches,
    enrichment_reviews,
    fragrances,
    health,
    maison,
    match_candidates,
    notes,
    private_supplier_workflow,
    profile_drafts,
    recommendations,
    scent_vectors,
    scentprint,
    search,
)

# Compatibility alias retained for imports written before the route was explicitly private.
supplier_items = private_supplier_workflow

ROUTERS = (
    health.router,
    admin_review.router,
    maison.router,
    supplier_items.router,
    match_candidates.router,
    enrichment_reviews.router,
    catalogue.router,
    brands.router,
    fragrances.router,
    notes.router,
    profile_drafts.router,
    search.router,
    recommendations.router,
    scent_vectors.router,
    scentprint.router,
    clone_matches.router,
)
