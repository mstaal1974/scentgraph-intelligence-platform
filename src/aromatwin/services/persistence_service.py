"""Progressive integration boundary for persisting workflow summaries."""

from typing import Any

from sqlalchemy.orm import Session

from aromatwin.persistence.audit_log import AuditLog
from aromatwin.persistence.repositories import (
    ArtifactRepository,
    AuditEventRepository,
    ConsumerScentprintRepository,
    LaunchCandidateRepository,
    ProfileDraftRepository,
    ProvenanceRepository,
    ReviewItemRepository,
    RunRepository,
    SellerDemandRepository,
    StageRepository,
)


def _only(summary: dict[str, Any], fields: set[str]) -> dict[str, Any]:
    return {key: value for key, value in summary.items() if key in fields}


class PersistenceService:
    """Accept allow-listed summaries; never mutate the originating workflow payload."""

    def __init__(self, session: Session):
        self.session = session

    def persist_pilot_run_summary(self, summary: dict[str, Any]):
        fields = {
            "run_id",
            "run_mode",
            "workflow_type",
            "status",
            "started_at",
            "completed_at",
            "readiness_status",
            "private_output_root",
            "public_summary_path",
        }
        item = RunRepository(self.session).upsert(**_only(summary, fields))
        self.record_audit_event(
            event_type="workflow_run_created",
            actor_type="system",
            linked_entity_type="run",
            linked_entity_id=item.run_id,
            event_summary="Workflow run summary persisted.",
        )
        return item

    def persist_run_stage_result(self, summary: dict[str, Any]):
        fields = {
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
        }
        return StageRepository(self.session).append(**_only(summary, fields))

    def persist_profile_draft_summary(self, summary: dict[str, Any]):
        fields = {
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
        }
        return ProfileDraftRepository(self.session).upsert(**_only(summary, fields))

    def persist_review_item_summary(self, summary: dict[str, Any]):
        fields = {
            "review_item_id",
            "linked_entity_type",
            "linked_entity_id",
            "review_type",
            "review_status",
            "priority_band",
            "assigned_role",
            "decision",
            "decision_reason",
        }
        return ReviewItemRepository(self.session).upsert(**_only(summary, fields))

    def persist_launch_candidate_summary(self, summary: dict[str, Any]):
        fields = {
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
        }
        return LaunchCandidateRepository(self.session).upsert(**_only(summary, fields))

    def persist_seller_demand_summary(self, summary: dict[str, Any]):
        fields = {
            "demand_brief_id",
            "seller_public_label",
            "seller_segment",
            "demand_theme",
            "product_formats_json",
            "private_data_redacted",
            "review_status",
        }
        return SellerDemandRepository(self.session).upsert(**_only(summary, fields))

    def persist_consumer_scentprint_summary(self, summary: dict[str, Any]):
        fields = {
            "scentprint_id",
            "consumer_public_alias",
            "preference_summary_json",
            "privacy_status",
            "private_data_redacted",
            "review_status",
        }
        return ConsumerScentprintRepository(self.session).upsert(**_only(summary, fields))

    def persist_provenance_summary(self, summary: dict[str, Any]):
        fields = {
            "provenance_id",
            "linked_entity_type",
            "linked_entity_id",
            "source_type",
            "source_confidence_band",
            "permitted_use_status",
            "provenance_summary",
            "review_status",
        }
        return ProvenanceRepository(self.session).upsert(**_only(summary, fields))

    def persist_public_safe_artifact(self, summary: dict[str, Any]):
        fields = {
            "run_id",
            "artifact_type",
            "artifact_label",
            "storage_location",
            "storage_visibility",
            "content_hash",
            "public_safe",
        }
        safe = _only(summary, fields)
        if not safe.get("public_safe") or safe.get("storage_visibility") != "public":
            raise ValueError("Only explicitly public-safe artifacts may use this helper")
        return ArtifactRepository(self.session).create(**safe)

    def record_audit_event(self, **event: Any):
        return AuditLog(AuditEventRepository(self.session)).record(**event)
