from collections.abc import Sequence
from dataclasses import dataclass
from sqlalchemy import select
from sqlalchemy.orm import Session
from aromatwin.models.match_candidate import MatchCandidate
from aromatwin.models.provenance import SourceProvenance
from aromatwin.models.supplier_item import SupplierItem
from aromatwin.models.profile_draft import ProfileDraft
from aromatwin.schemas.profile_draft import ProfileDraftCreate, ProfileDraftGenerateRequest


@dataclass(frozen=True)
class GenerationSource:
    supplier: dict[str, object]
    candidate: dict[str, object]
    provenance: list[dict[str, object]]


class ProfileDraftRepository:
    def __init__(self, session: Session):
        self.session = session

    def list(self) -> list[ProfileDraft]:
        return list(self.session.scalars(select(ProfileDraft).order_by(ProfileDraft.id)))

    def get(self, draft_id: int) -> ProfileDraft | None:
        return self.session.get(ProfileDraft, draft_id)

    def generation_sources(self, request: ProfileDraftGenerateRequest) -> list[GenerationSource]:
        statement = select(MatchCandidate, SupplierItem).join(
            SupplierItem, SupplierItem.id == MatchCandidate.supplier_item_id
        )
        if request.supplier_item_ids:
            statement = statement.where(SupplierItem.id.in_(request.supplier_item_ids))
        if request.match_candidate_ids:
            statement = statement.where(MatchCandidate.id.in_(request.match_candidate_ids))
        rows = self.session.execute(statement).all()
        sources = []
        for candidate, supplier in rows:
            provenance = self.session.scalars(
                select(SourceProvenance).where(
                    SourceProvenance.entity_type == "match_candidate",
                    SourceProvenance.entity_id == candidate.id,
                )
            ).all()
            sources.append(
                GenerationSource(
                    supplier={
                        "id": supplier.id,
                        "normalised_brand": supplier.normalised_brand,
                        "normalised_name": supplier.normalised_name,
                        "supplier_brand_raw": supplier.supplier_brand_raw,
                        "supplier_name_raw": supplier.supplier_name_raw,
                    },
                    candidate={
                        "id": candidate.id,
                        "supplier_item_id": candidate.supplier_item_id,
                        "candidate_brand": candidate.candidate_brand,
                        "candidate_fragrance_name": candidate.candidate_fragrance_name,
                        "candidate_source_type": candidate.candidate_source_type,
                        "match_confidence": float(candidate.match_confidence),
                    },
                    provenance=[
                        {
                            "source_name": item.source_name,
                            "source_type": item.source_type,
                            "source_reference": item.source_reference,
                            "source_url": item.source_url,
                            "licence_status": item.licence_status,
                            "commercial_use_allowed": item.commercial_use_allowed,
                            "confidence": float(item.confidence),
                        }
                        for item in provenance
                    ],
                )
            )
        return sources

    def existing_keys(self) -> set[tuple[int, int | None]]:
        rows = self.session.execute(
            select(ProfileDraft.supplier_item_id, ProfileDraft.match_candidate_id).where(
                ProfileDraft.review_status.in_(
                    ("needs_human_review", "requires_more_sources", "approved_for_catalogue")
                )
            )
        ).all()
        return {(row[0], row[1]) for row in rows}

    def add(self, draft: ProfileDraftCreate) -> ProfileDraft:
        payload = draft.model_dump(mode="python")
        payload["review_status"] = draft.review_status.value
        record = ProfileDraft(**payload)
        self.session.add(record)
        self.session.flush()
        return record

    def approval_provenance(self, draft: ProfileDraft) -> Sequence[SourceProvenance]:
        if draft.match_candidate_id is None:
            return []
        return self.session.scalars(
            select(SourceProvenance).where(
                SourceProvenance.entity_type == "match_candidate",
                SourceProvenance.entity_id == draft.match_candidate_id,
            )
        ).all()

    def save(self, draft: ProfileDraft) -> ProfileDraft:
        self.session.add(draft)
        self.session.commit()
        self.session.refresh(draft)
        return draft

    def commit_created(self, drafts: list[ProfileDraft]) -> list[ProfileDraft]:
        self.session.commit()
        for draft in drafts:
            self.session.refresh(draft)
        return drafts
