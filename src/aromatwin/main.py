import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from aromatwin.config import Settings, get_settings
from aromatwin.middleware import SecurityAndLoggingMiddleware
from aromatwin.routers import ROUTERS, admin_review, maison, supplier_items
from aromatwin.security import validate_cors_origins

ADMIN_STATIC = Path(__file__).resolve().parents[2] / "static" / "admin"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
    application = FastAPI(
        title="AromaTwin Intelligence Platform",
        version="0.2.0",
        description="Supplier-first, brand-neutral commercial fragrance intelligence API",
    )
    application.state.settings = settings
    # Dependency overrides make explicitly supplied settings deterministic in tests and app factories.
    application.dependency_overrides[get_settings] = lambda: settings

    for router in ROUTERS:
        if router is admin_review.router:
            if settings.enable_admin_console:
                application.include_router(router, prefix=settings.internal_api_prefix)
        elif router is supplier_items.router:
            if settings.enable_private_supplier_endpoints:
                application.include_router(router, prefix=settings.internal_api_prefix)
        elif router is maison.router:
            application.include_router(router, prefix=settings.public_api_prefix)
        else:
            application.include_router(router)

    application.add_middleware(SecurityAndLoggingMiddleware)
    origins = validate_cors_origins(settings)
    if origins:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials="*" not in origins,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["Accept", "Content-Type", "X-API-Key", "X-Admin-API-Key",
                           "X-Private-API-Key", "X-Request-ID"],
        )
    if settings.enable_admin_console and ADMIN_STATIC.is_dir():
        application.mount(
            f"{settings.internal_api_prefix}/admin-console",
            StaticFiles(directory=ADMIN_STATIC, html=True),
            name="admin-console",
        )
    return application


app = create_app()
