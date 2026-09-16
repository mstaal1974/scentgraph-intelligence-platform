from fastapi import FastAPI
from aromatwin.routers import ROUTERS

app = FastAPI(
    title="AromaTwin Intelligence Platform",
    version="0.4.0",
    description="Supplier-first fragrance intelligence with auditable profile and enrichment review",
)
for router in ROUTERS:
    app.include_router(router)
