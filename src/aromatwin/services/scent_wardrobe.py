"""Private-by-default scent wardrobe operations and gap suggestions."""

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from uuid import uuid4

from aromatwin.schemas.consumer_scent import ScentWardrobeItemCreate, ScentWardrobeItemUpdate


@dataclass
class ScentWardrobeItem:
    wardrobe_item_id: str
    scentprint_id: str
    fragrance_id: str | None
    product_id: str | None
    variant_id: str | None
    status: str
    usage_contexts: list[str]
    favourite_for: list[str]
    purchase_stage: str | None
    last_used_season: str | None
    reorder_interest: str
    next_recommendation_action: str | None
    created_at: datetime
    updated_at: datetime


def add_item(payload: ScentWardrobeItemCreate) -> ScentWardrobeItem:
    now = datetime.now(UTC)
    return ScentWardrobeItem(wardrobe_item_id=str(uuid4()), **payload.model_dump(),
                             created_at=now, updated_at=now)


def update_item(item: ScentWardrobeItem, payload: ScentWardrobeItemUpdate) -> ScentWardrobeItem:
    values = asdict(item)
    values.update(payload.model_dump(exclude_unset=True))
    values["updated_at"] = datetime.now(UTC)
    return ScentWardrobeItem(**values)


def remove_item(items: list[ScentWardrobeItem], wardrobe_item_id: str) -> bool:
    before = len(items)
    items[:] = [item for item in items if item.wardrobe_item_id != wardrobe_item_id]
    return len(items) < before


def analyse_gaps(items: list[ScentWardrobeItem], preferred_families: list[str] | None = None) -> dict[str, object]:
    contexts = {value for item in items for value in item.usage_contexts}
    missing_contexts = sorted({"everyday", "evening", "seasonal"} - contexts)
    actions = ["try tester" if any(item.status == "wants_to_try" for item in items) else "try bundle"]
    if any(item.status == "tried" and item.reorder_interest == "high" for item in items):
        actions.append("upgrade to 50ml")
    if not any("home" in context.casefold() for context in contexts):
        actions.append("add diffuser")
    status_counts = {status: sum(item.status == status for item in items)
                     for status in {item.status for item in items}}
    if status_counts and max(status_counts.values()) > max(2, len(items) // 2):
        actions.append("avoid similar profile")
    return {"missing_usage_contexts": missing_contexts,
            "underrepresented_families": preferred_families or [],
            "overrepresented_statuses": [key for key, value in status_counts.items() if value > 2],
            "next_actions": list(dict.fromkeys(actions))}
