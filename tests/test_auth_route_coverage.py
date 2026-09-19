"""Every route is credential-gated unless it is explicitly listed as anonymous.

This is the regression guard for the fail-closed boundary: adding a router without an
authentication dependency fails here rather than silently exposing a surface.
"""

from fastapi import FastAPI
from fastapi.routing import APIRoute

from aromatwin.config import Settings
from aromatwin.main import create_app
from aromatwin.security import (
    require_admin_api_key,
    require_private_api_key,
    require_public_api_key,
)

AUTH_DEPENDENCIES = frozenset(
    {require_admin_api_key, require_private_api_key, require_public_api_key}
)

# Liveness probes carry no catalogue, supplier, or workflow content and must stay reachable
# for load balancers and container orchestration. /deployment/health returns only the version
# string; the detailed /deployment/readiness and /deployment/environment reports are gated.
ANONYMOUS_PATHS = frozenset(
    {
        "/health",
        "/deployment/health",
        "/openapi.json",
        "/docs",
        "/redoc",
        "/docs/oauth2-redirect",
    }
)


def deployed_app() -> FastAPI:
    return create_app(
        Settings(
            environment="production",
            allow_insecure_local_auth=False,
            api_key="public-secret",
            admin_api_key="admin-secret",
            private_api_key="private-secret",
            allowed_origins=("https://store.example",),
        )
    )


def authenticated_routes(app: FastAPI) -> tuple[list[APIRoute], list[APIRoute]]:
    guarded, open_routes = [], []
    for route in app.routes:
        if not isinstance(route, APIRoute) or route.path in ANONYMOUS_PATHS:
            continue
        calls = {dependency.call for dependency in route.dependant.dependencies}
        (guarded if calls & AUTH_DEPENDENCIES else open_routes).append(route)
    return guarded, open_routes


def test_no_route_is_anonymously_reachable() -> None:
    _, open_routes = authenticated_routes(deployed_app())
    assert not open_routes, sorted(
        f"{sorted(route.methods - {'HEAD', 'OPTIONS'})} {route.path}" for route in open_routes
    )


def test_every_mutating_route_is_credential_gated() -> None:
    guarded, open_routes = authenticated_routes(deployed_app())
    mutating = {"POST", "PUT", "PATCH", "DELETE"}
    assert not [route for route in open_routes if route.methods & mutating]
    assert [route for route in guarded if route.methods & mutating], "expected mutating routes"


def test_the_guard_covers_a_meaningful_number_of_routes() -> None:
    """A misconfigured app factory returning few routes must not vacuously pass the guard."""
    guarded, _ = authenticated_routes(deployed_app())
    assert len(guarded) > 150
