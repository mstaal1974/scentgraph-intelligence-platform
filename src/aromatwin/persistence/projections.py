"""Allow-list projections used by every operational API and export."""

from typing import Any


def _project(value: Any, fields: tuple[str, ...]) -> dict[str, Any]:
    return {field: getattr(value, field) for field in fields}


def run_public_summary(value: Any) -> dict[str, Any]:
    return _project(
        value,
        (
            "run_id",
            "run_mode",
            "workflow_type",
            "status",
            "started_at",
            "completed_at",
            "readiness_status",
            "created_at",
            "updated_at",
        ),
    )


def stage_public_summary(value: Any) -> dict[str, Any]:
    return _project(
        value,
        (
            "run_id",
            "stage_name",
            "stage_status",
            "accepted_count",
            "skipped_count",
            "blocked_count",
            "warning_count",
            "blocker_summary",
            "started_at",
            "completed_at",
        ),
    )


def artifact_public_summary(value: Any) -> dict[str, Any]:
    result = _project(
        value,
        (
            "run_id",
            "artifact_type",
            "artifact_label",
            "storage_visibility",
            "content_hash",
            "public_safe",
            "created_at",
        ),
    )
    if value.public_safe and value.storage_visibility == "public":
        result["storage_location"] = value.storage_location
    return result


def profile_draft_public_summary(value: Any) -> dict[str, Any]:
    return _project(
        value,
        (
            "profile_draft_id",
            "run_id",
            "canonical_brand",
            "canonical_fragrance_name",
            "profile_status",
            "source_confidence_band",
            "missing_fields_json",
            "enrichment_needed",
            "review_status",
            "provenance_summary",
            "created_at",
            "updated_at",
        ),
    )


def review_item_public_summary(value: Any) -> dict[str, Any]:
    return _project(
        value,
        (
            "review_item_id",
            "linked_entity_type",
            "linked_entity_id",
            "review_type",
            "review_status",
            "priority_band",
            "assigned_role",
            "decision",
            "decision_reason",
            "created_at",
            "updated_at",
        ),
    )


def launch_candidate_public_summary(value: Any) -> dict[str, Any]:
    return _project(
        value,
        (
            "launch_candidate_id",
            "fragrance_id",
            "product_id",
            "canonical_brand",
            "canonical_fragrance_name",
            "launch_priority_band",
            "launch_status",
            "margin_suitability_band",
            "supplier_availability_band",
            "seller_demand_band",
            "consumer_interest_band",
            "blocking_issues_json",
            "recommended_next_action",
            "review_status",
            "created_at",
            "updated_at",
        ),
    )


def seller_demand_public_summary(value: Any) -> dict[str, Any]:
    return _project(
        value,
        (
            "demand_brief_id",
            "seller_public_label",
            "seller_segment",
            "demand_theme",
            "product_formats_json",
            "private_data_redacted",
            "review_status",
            "created_at",
            "updated_at",
        ),
    )


def consumer_scentprint_public_summary(value: Any) -> dict[str, Any]:
    return _project(
        value,
        (
            "scentprint_id",
            "consumer_public_alias",
            "preference_summary_json",
            "privacy_status",
            "private_data_redacted",
            "review_status",
            "created_at",
            "updated_at",
        ),
    )


def provenance_public_summary(value: Any) -> dict[str, Any]:
    return _project(
        value,
        (
            "provenance_id",
            "linked_entity_type",
            "linked_entity_id",
            "source_type",
            "source_confidence_band",
            "permitted_use_status",
            "provenance_summary",
            "review_status",
            "created_at",
        ),
    )


def audit_event_public_summary(value: Any) -> dict[str, Any]:
    return _project(
        value,
        (
            "audit_event_id",
            "event_type",
            "actor_type",
            "linked_entity_type",
            "linked_entity_id",
            "event_summary",
            "risk_level",
            "privacy_boundary",
            "created_at",
        ),
    )
