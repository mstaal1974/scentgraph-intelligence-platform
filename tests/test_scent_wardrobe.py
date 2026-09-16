import pytest
from pydantic import ValidationError

from aromatwin.schemas.consumer_scent import ScentWardrobeItemCreate
from aromatwin.services.scent_wardrobe import add_item, analyse_gaps

STATUSES = {"owns", "tried", "wants_to_try", "not_for_me", "gifted",
            "considering_full_size", "reordered"}


def test_wardrobe_supports_all_statuses() -> None:
    for status in STATUSES:
        assert add_item(ScentWardrobeItemCreate(scentprint_id="p-1", status=status)).status == status
    with pytest.raises(ValidationError):
        ScentWardrobeItemCreate(scentprint_id="p-1", status="public")


def test_gap_analysis_produces_next_actions() -> None:
    item = add_item(ScentWardrobeItemCreate(
        scentprint_id="p-1", status="tried", usage_contexts=["everyday"],
        reorder_interest="high",
    ))
    result = analyse_gaps([item], ["woody"])
    assert "upgrade to 50ml" in result["next_actions"]
    assert result["missing_usage_contexts"]
