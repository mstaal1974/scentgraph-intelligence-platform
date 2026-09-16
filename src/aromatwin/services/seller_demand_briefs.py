"""In-memory domain service for private seller demand briefs."""

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from uuid import uuid4

from aromatwin.schemas.seller_demand import SellerDemandBriefCreate, SellerDemandBriefUpdate


@dataclass
class SellerDemandBrief:
    demand_brief_id: str
    seller_name: str
    seller_segment: str
    target_customer: str
    desired_fragrance_families: list[str]
    desired_notes: list[str]
    desired_accords: list[str]
    desired_moods: list[str]
    desired_occasions: list[str]
    desired_seasons: list[str]
    desired_intensity: str | None
    desired_projection: str | None
    desired_longevity: str | None
    inspired_by_targets: list[str]
    product_formats: list[str]
    target_public_price_band: str | None
    target_margin_band: str
    launch_quantity_band: str | None
    market_positioning: str | None
    urgency: str | None
    exclusions: list[str]
    private_seller_notes: str | None
    review_status: str
    created_at: datetime
    updated_at: datetime


def create_brief(payload: SellerDemandBriefCreate) -> SellerDemandBrief:
    now = datetime.now(UTC)
    return SellerDemandBrief(demand_brief_id=str(uuid4()), **payload.model_dump(),
                             review_status="needs_human_review", created_at=now, updated_at=now)


def update_brief(brief: SellerDemandBrief, payload: SellerDemandBriefUpdate) -> SellerDemandBrief:
    values = asdict(brief)
    values.update(payload.model_dump(exclude_unset=True))
    values["updated_at"] = datetime.now(UTC)
    return SellerDemandBrief(**values)


def public_safe_brief(brief: SellerDemandBrief) -> dict[str, object]:
    """An explicit allowlist deliberately excludes seller identity and private notes."""
    result = asdict(brief)
    result.pop("seller_name")
    result.pop("private_seller_notes")
    return result
