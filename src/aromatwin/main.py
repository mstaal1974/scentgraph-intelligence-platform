from fastapi import FastAPI
from aromatwin.routers import ROUTERS

app = FastAPI(
    title="AromaTwin Intelligence Platform",
    version="0.2.0",
    description="Supplier-first, brand-neutral commercial fragrance intelligence API",
)
for router in ROUTERS:
    app.include_router(router)
