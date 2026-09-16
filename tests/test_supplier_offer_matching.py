from dataclasses import dataclass

import pandas as pd
from fastapi.testclient import TestClient

from aromatwin.config import Settings
from aromatwin.main import create_app
from aromatwin.services.supplier_offer_importer import prepare_supplier_offer_frame
from aromatwin.services.supplier_offer_matching import compare_supplier_offers, match_supplier_offer


@dataclass
class Identity:
    id: int
    brand: str
    name: str


def offer(reference: str | None):
    return prepare_supplier_offer_frame(pd.DataFrame({"BRAND": ["Fictional House"], "NAME": ["Night Air"],
        "ORI": [reference], "CN CODE": ["private"], "QTY": [1], "AED": [2], "USD": [1]}),
        "Supplier", "offers.csv", "existing_supplier").rows[0]


def test_matching_links_existing_candidate_and_missing_reference_lowers_confidence() -> None:
    candidate = Identity(4, "Fictional House", "Night Air")
    referenced = match_supplier_offer(offer("Fictional House / Night Air"), [candidate], [])
    unreferenced = match_supplier_offer(offer(None), [candidate], [])
    assert referenced.matched_id == 4
    assert referenced.review_status == "matched_to_candidate"
    assert unreferenced.confidence < referenced.confidence
    assert not referenced.created_public_record


def test_comparison_groups_suppliers_without_commercial_values() -> None:
    one = offer(None)
    two = one.__class__(**{**one.__dict__, "supplier_name": "Other supplier"})
    groups = compare_supplier_offers([one, two])
    assert groups == [{"normalised_brand": "Fictional House", "normalised_name": "Night Air",
                       "supplier_count": 2, "offer_count": 2}]
    assert not {"price", "aed", "usd", "code"} & set(groups[0])


def test_openapi_marks_offer_routes_private_and_public_schemas_are_safe() -> None:
    app = create_app(Settings(environment="test"))
    schema = TestClient(app).get("/openapi.json").json()
    paths = schema["paths"]
    assert "/supplier-offers/import" in paths
    assert "internal private supplier offers" in paths["/supplier-offers"]["get"]["tags"]
    properties = schema["components"]["schemas"]["SupplierOfferPublicSummary"]["properties"]
    assert not any(token in key for key in properties for token in ("price", "code", "quantity", "stock", "aed", "usd"))
