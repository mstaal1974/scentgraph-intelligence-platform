import pandas as pd
from aromatwin.services.matching import candidate_from_reference, candidate_from_supplier
from aromatwin.services.supplier_importer import prepare_supplier_frame


def test_candidate_match_creation_from_original_hint() -> None:
    frame = pd.DataFrame(
        [
            {
                "BRAND": "Oil House",
                "NAME": "No. 1 TOP",
                "ORI": "Original Brand / Original Scent",
                "CN CODE": "1",
                "QTY": 1,
                "AED": 10,
                "USD": 3,
            }
        ]
    )
    row = prepare_supplier_frame(frame, "Supplier", "list.csv").rows[0]
    candidate = candidate_from_supplier(row, 42)
    assert candidate.candidate_brand == "Original Brand"
    assert candidate.candidate_fragrance_name == "Original Scent"
    assert candidate.review_status == "match_candidate"


def test_reference_candidate_is_explicitly_reference_only() -> None:
    candidate = candidate_from_reference(
        supplier_item_id=42,
        candidate_brand="Brand",
        candidate_name="Scent",
        source_reference="row-1",
    )
    assert candidate.candidate_source_type == "reference_only"
