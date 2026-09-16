from aromatwin.schemas.maison_integration import MaisonProductExportRead
from aromatwin.services.maison_export_contracts import contract_fields, export_recommendation


def test_public_contracts_exclude_private_and_commercial_fields():
    fields = {field for values in contract_fields().values() for field in values}
    assert not fields & {"supplier_price", "supplier_code", "consumer_private_notes", "raw_margin"}
    assert {"product_id", "public_description", "variant_sku"} <= set(MaisonProductExportRead.model_fields)


def test_recommendation_drops_unknown_private_input():
    row = dict(recommendation_id="r", source_product_id="a", recommended_product_id="b",
               recommendation_type="similar", match_score_band="medium", reason_summary="summary",
               public_safe_explanation="reviewed", status="draft", consumer_private_notes="drop")
    assert "consumer_private_notes" not in export_recommendation(row).model_dump()
