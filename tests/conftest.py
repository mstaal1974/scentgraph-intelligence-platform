import os
from collections.abc import Callable, Iterator
from typing import Any

# Authentication fails closed, so the offline suite opts the local environment in before any
# aromatwin import builds Settings. Deployed environments cannot set this: Settings validation
# rejects it outside LOCAL_ENVIRONMENTS.
os.environ.setdefault("AROMATWIN_ALLOW_INSECURE_LOCAL_AUTH", "true")

import pytest  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from aromatwin.main import app as application  # noqa: E402

PRIVATE_SUPPLIER_FIELDS = {
    "aed",
    "aed_price",
    "cn_code",
    "commercial_terms",
    "quantity",
    "stock",
    "supplier_code",
    "supplier_price",
    "usd",
    "usd_price",
}


@pytest.fixture(scope="session")
def app() -> FastAPI:
    """Return the single application instance used by API tests."""
    return application


@pytest.fixture()
def client(app: FastAPI) -> Iterator[TestClient]:
    """Provide a lifecycle-aware client using the supported FastAPI test stack."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def assert_public_safe() -> Callable[[Any], None]:
    """Return an assertion helper that recursively rejects private supplier keys."""

    def assert_safe(value: Any) -> None:
        if isinstance(value, dict):
            keys = {str(key).strip().casefold().replace(" ", "_") for key in value}
            assert keys.isdisjoint(PRIVATE_SUPPLIER_FIELDS)
            for child in value.values():
                assert_safe(child)
        elif isinstance(value, list):
            for child in value:
                assert_safe(child)

    return assert_safe
