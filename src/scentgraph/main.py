from fastapi import FastAPI
from pydantic import BaseModel
from scentgraph.routers import (
    brands,
    clone_matches,
    fragrances,
    notes,
    recommendations,
    scentprint,
    search,
)


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


app = FastAPI(
    title="ScentGraph Intelligence Platform",
    version="0.1.0",
    description="Brand-neutral fragrance intelligence API",
)
for router in (
    brands.router,
    fragrances.router,
    notes.router,
    search.router,
    recommendations.router,
    scentprint.router,
    clone_matches.router,
):
    app.include_router(router)


@app.get("/health", response_model=HealthResponse, tags=["operations"])
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="scentgraph", version=app.version)
