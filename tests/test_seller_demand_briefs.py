import pytest
from pydantic import ValidationError

from aromatwin.schemas.seller_demand import SellerDemandBriefCreate
from aromatwin.services.seller_demand_briefs import create_brief, public_safe_brief


def payload() -> dict[str, object]:
    return {"seller_name": "Private retailer", "seller_segment": "niche",
            "target_customer": "adult discovery", "desired_moods": ["calm"],
            "product_formats": ["30ml bottle"], "private_seller_notes": "confidential launch"}


def test_creation_validates_format_and_defaults_to_review() -> None:
    brief = create_brief(SellerDemandBriefCreate(**payload()))
    assert brief.review_status == "needs_human_review"
    with pytest.raises(ValidationError):
        SellerDemandBriefCreate(**{**payload(), "product_formats": ["unsupported"]})


def test_public_brief_excludes_identity_and_private_notes() -> None:
    public = public_safe_brief(create_brief(SellerDemandBriefCreate(**payload())))
    assert "private_seller_notes" not in public
    assert "seller_name" not in public
    assert public["inspired_by_targets"] == []
