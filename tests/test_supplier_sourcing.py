from dataclasses import replace

import pandas as pd
from fastapi.testclient import TestClient

from aromatwin.config import Settings
from aromatwin.main import create_app
from aromatwin.services.supplier_offer_importer import prepare_supplier_offer_frame
from aromatwin.services.supplier_sourcing import (
    build_sourcing_decisions,
    group_supplier_offers,
    public_safe_decision,
)

FORBIDDEN = ("price", "aed", "usd", "supplier_code", "cn_code", "quantity", "stock", "cost", "margin", "commercial")


def _offer(supplier: str = "Private supplier", price: object = 5, code: object = "X"):
    frame = pd.DataFrame({"BRAND": ["Fictional House"], "NAME": ["Night Air"],
        "ORI": ["Fictional House / Night Air"], "CN CODE": [code], "QTY": [1],
        "AED": [price], "USD": [price]})
    return prepare_supplier_offer_frame(frame, supplier, "private.csv", "existing_supplier").rows[0]


def test_groups_catalogue_then_candidate() -> None:
    catalogue = replace(_offer(), linked_catalogue_fragrance_id=3)
    candidate = replace(_offer("Other"), linked_match_candidate_id=7)
    groups = group_supplier_offers([catalogue, candidate])
    assert groups[("catalogue", 3)] == [catalogue]
    assert groups[("candidate", 7)] == [candidate]


def test_internal_ranking_and_audit_flags() -> None:
    preferred = replace(_offer("A", 4), linked_catalogue_fragrance_id=3, confidence_score=0.9)
    lower = replace(_offer("B", 8, None), linked_catalogue_fragrance_id=3,
                    confidence_score=0.8)
    duplicate = replace(preferred, supplier_file_hash="other-hash")
    suspicious = replace(_offer("C", -1), linked_catalogue_fragrance_id=3,
                         confidence_score=0.8)
    decisions = build_sourcing_decisions([preferred, lower, duplicate, suspicious])
    assert min(d.internal_rank for d in decisions) == 1
    assert any("missing_supplier_code" in d.risk_flags for d in decisions)
    assert sum("duplicate_offer" in d.risk_flags for d in decisions) == 2
    assert any("suspicious_price" in d.risk_flags for d in decisions)


def test_public_decision_is_allowlisted_and_does_not_promote() -> None:
    decision = build_sourcing_decisions([replace(_offer(), confidence_score=0.9)])[0]
    public = public_safe_decision(decision)
    assert not any(token in key.casefold() for key in public for token in FORBIDDEN)
    assert decision.catalogue_fragrance_id is None


def test_openapi_marks_sourcing_routes_internal_and_safe() -> None:
    schema = TestClient(create_app(Settings(environment="test"))).get("/openapi.json").json()
    assert "/supplier-sourcing/build" in schema["paths"]
    endpoint = schema["paths"]["/supplier-sourcing/decisions"]["get"]
    assert "internal private supplier sourcing" in endpoint["tags"]
    properties = schema["components"]["schemas"]["SupplierSourcingDecisionRead"]["properties"]
    assert not any(token in key.casefold() for key in properties for token in FORBIDDEN)


def test_public_samples_have_no_commercial_headers() -> None:
    for filename in ("supplier_sourcing_sample.csv", "margin_scenarios_sample.csv"):
        columns = pd.read_csv(f"data/samples/{filename}").columns
        assert not any(token in key.casefold() for key in columns for token in FORBIDDEN)
