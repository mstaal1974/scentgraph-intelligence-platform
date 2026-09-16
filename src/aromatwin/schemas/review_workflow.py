"""Typed contracts for the internal human-review workflow."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

Decision = Literal["approve", "reject", "request_enrichment", "request_supplier_review",
                   "request_provenance_review", "request_product_setup",
                   "request_compliance_review", "hold", "mark_duplicate",
                   "mark_out_of_scope", "escalate"]


class ReviewGatePublicSummary(BaseModel):
    gate_id: str
    gate_type: str
    linked_entity_type: str
    linked_entity_id: str
    reviewer_role: str
    public_safe_summary: str


class ReviewGateRead(ReviewGatePublicSummary):
    required_evidence: list[str]
    allowed_decisions: list[Decision]
    blocking_conditions: list[str]
    next_allowed_statuses: list[str]
    audit_required: bool


class ReviewQueueItemPublicSummary(BaseModel):
    review_item_id: str
    gate_type: str
    linked_entity_type: str
    linked_entity_id: str
    title: str
    priority_band: Literal["low", "normal", "high", "urgent"]
    confidence_band: str
    risk_band: Literal["low", "moderate", "high", "blocked"]
    review_status: str
    assigned_role: str
    recommended_next_action: str
    public_safe_summary: str
    created_at: datetime
    updated_at: datetime


class ReviewQueueItemRead(ReviewQueueItemPublicSummary):
    gate_id: str
    required_evidence: list[str]
    blocking_conditions: list[str]
    recommended_decision: Decision


class ReviewDecisionCreate(BaseModel):
    review_item_id: str
    decision: Decision
    reviewer_role: str
    reviewer_alias: str | None = None
    decision_reason: str | None = None
    evidence_summary: str = "Evidence reviewed."


class ReviewDecisionPublicSummary(BaseModel):
    decision_id: str
    review_item_id: str
    gate_id: str
    decision: Decision
    reviewer_role: str
    reviewer_alias: str
    evidence_summary: str
    next_status: str
    next_action: str
    creates_audit_event: bool
    created_at: datetime


class ReviewDecisionRead(ReviewDecisionPublicSummary):
    decision_reason: str | None = Field(default=None, description="Internal/private; never public.")


class ReviewReadinessReport(BaseModel):
    queue_id: str
    total_items: int
    queued_count: int
    in_review_count: int
    approved_count: int
    rejected_count: int
    enrichment_requested_count: int
    supplier_review_requested_count: int
    provenance_review_requested_count: int
    product_setup_requested_count: int
    compliance_review_requested_count: int
    held_count: int
    escalated_count: int
    blocked_count: int
    high_priority_count: int
    urgent_count: int
    top_bottlenecks: list[str]
    owner_role_summary: dict[str, int]
    next_actions: list[str]
    readiness_status: str


class ReviewWorkflowAuditReport(BaseModel):
    passed: bool
    reviewed_item_count: int
    decision_count: int
    audit_required_count: int
    violations: list[str]

