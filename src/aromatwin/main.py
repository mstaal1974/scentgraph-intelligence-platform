from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from aromatwin.routers import ROUTERS

app = FastAPI(
    title="AromaTwin Intelligence Platform",
    version="0.2.0",
    description="Supplier-first, brand-neutral commercial fragrance intelligence API",
)
for router in ROUTERS:
    app.include_router(router)

ADMIN_STATIC = Path(__file__).resolve().parents[2] / "static" / "admin"
if ADMIN_STATIC.is_dir():
    app.mount("/admin-console", StaticFiles(directory=ADMIN_STATIC, html=True), name="admin-console")
