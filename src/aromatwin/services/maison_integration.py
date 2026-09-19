"""Read-only, allowlisted projection of AromaTwin intelligence for Maison Obsidian."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Iterable, Mapping

from aromatwin.schemas.maison import (
    MaisonCatalogueExportRow,
    MaisonFragranceCard,
    MaisonFragranceDetail,
    MaisonRecommendationCard,
    MaisonScentprintRequest,
    MaisonScentprintResult,
    MaisonScentVectorSummary,
    MaisonSimilarFragranceResult,
)
from aromatwin.services.scent_vector_engine import VECTOR_DIMENSIONS

DATA_DIR = Path(__file__).resolve().parents[3] / "data"
PRIVATE_FIELDS = frozenset(
    {
        "supplier_price",
        "price_aed",
        "aed_price",
        "price_usd",
        "usd_price",
        "supplier_code",
        "stock",
        "quantity",
        "cn_code",
        "commercial_terms",
        "supplier_commercial_terms",
    }
)
RESTRICTED_FIELDS = frozenset(
    {
        "third_party_description",
        "review",
        "reviews",
        "rating",
        "ratings",
        "image",
        "image_url",
        "comment",
        "comments",
        "ugc",
        "user_generated_content",
    }
)
BLOCKED_TYPES = frozenset(
    {"supplier_item", "match_candidate", "profile_draft", "enrichment_review"}
)
SAFE_VECTOR_STATUSES = frozenset({"approved", "public_safe", "review_safe"})
SAFE_RECOMMENDATION_STATUSES = frozenset({"approved", "public_safe"})


def _read(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def _truthy(value: object) -> bool:
    return value is True or str(value).strip().lower() in {"1", "true", "yes", "approved"}


def _tokens(value: object) -> list[str]:
    if isinstance(value, list | tuple | set):
        return [str(item).strip() for item in value if str(item).strip()]
    return [item.strip() for item in str(value or "").replace("|", ",").split(",") if item.strip()]


def _unsafe(row: Mapping[str, object]) -> bool:
    forbidden = PRIVATE_FIELDS | RESTRICTED_FIELDS
    return any(row.get(field) not in (None, "", [], {}, ()) for field in forbidden) or _truthy(
        row.get("copied_restricted_content")
    )


def _approved_catalogue(row: Mapping[str, object]) -> bool:
    if str(row.get("record_type", "catalogue_fragrance")) in BLOCKED_TYPES or _unsafe(row):
        return False
    # Promoted catalogue CSV rows are approved by construction; explicit flags always win.
    status = row.get("review_status") or row.get("approval_status")
    approved = row.get("approved", row.get("public_approved"))
    if approved is not None and str(approved) != "":
        return _truthy(approved)
    return status in (None, "", "approved", "approved_for_catalogue", "public_safe")


class MaisonIntegrationService:
    """Build a safe consumer view without exposing workflow-layer records."""

    def __init__(
        self,
        catalogue: Iterable[Mapping[str, object]] | None = None,
        vectors: Iterable[Mapping[str, object]] | None = None,
        recommendations: Iterable[Mapping[str, object]] | None = None,
        relationships: Iterable[Mapping[str, object]] | None = None,
        *,
        data_dir: Path = DATA_DIR,
    ) -> None:
        self.catalogue = [
            dict(row)
            for row in (
                catalogue if catalogue is not None else _read(data_dir / "catalogue_fragrances.csv")
            )
            if _approved_catalogue(row)
        ]
        ids = {int(row["id"]) for row in self.catalogue}
        self.vectors = {
            int(row["fragrance_id"]): dict(row)
            for row in (vectors if vectors is not None else _read(data_dir / "scent_vectors.csv"))
            if int(row.get("fragrance_id", 0)) in ids
            and str(row.get("review_status")) in SAFE_VECTOR_STATUSES
            and not _unsafe(row)
        }
        self.recommendations = [
            dict(row)
            for row in (
                recommendations
                if recommendations is not None
                else _read(data_dir / "recommendations.csv")
            )
            if int(row.get("source_fragrance_id", 0)) in ids
            and int(row.get("recommended_fragrance_id", 0)) in ids
            and str(row.get("review_status")) in SAFE_RECOMMENDATION_STATUSES
            and not _unsafe(row)
        ]
        self.relationships = [
            dict(row)
            for row in (
                relationships
                if relationships is not None
                else _read(data_dir / "clone_relationships.csv")
            )
            if int(row.get("clone_fragrance_id", 0)) in ids
            and int(row.get("original_fragrance_id", 0)) in ids
            and str(row.get("review_status")) in SAFE_RECOMMENDATION_STATUSES
            and not _unsafe(row)
        ]

    def _row(self, fragrance_id: int) -> dict[str, object] | None:
        return next((row for row in self.catalogue if int(row["id"]) == fragrance_id), None)

    def card(self, row: Mapping[str, object]) -> MaisonFragranceCard:
        return MaisonFragranceCard(
            id=int(row["id"]),
            slug=str(row.get("slug") or ""),
            title=str(row.get("title") or row.get("name") or ""),
            brand=str(row.get("brand") or ""),
            family=str(row.get("family")) if row.get("family") else None,
            accords=_tokens(row.get("accords")),
            mood=_tokens(row.get("mood")),
            occasion=_tokens(row.get("occasion")),
            season=_tokens(row.get("season")),
            confidence_score=float(
                row.get("source_confidence") or row.get("confidence_score") or 0
            ),
            review_status=str(row.get("review_status") or "approved"),
            provenance_status="verified"
            if row.get("provenance_references") or row.get("provenance_summary")
            else "approved",
        )

    def list_fragrances(self) -> list[MaisonFragranceCard]:
        return [self.card(row) for row in sorted(self.catalogue, key=lambda item: int(item["id"]))]

    def detail(self, fragrance_id: int) -> MaisonFragranceDetail | None:
        row = self._row(fragrance_id)
        if row is None:
            return None
        vector = self.vectors.get(fragrance_id)
        summary = None
        if vector:
            summary = MaisonScentVectorSummary(
                dimensions={name: float(vector.get(name) or 0) for name in VECTOR_DIMENSIONS},
                confidence_score=float(vector.get("confidence_score") or 0),
                review_status=str(vector["review_status"]),
            )
        links = sorted(
            {
                int(item["recommended_fragrance_id"])
                for item in self.recommendations
                if int(item["source_fragrance_id"]) == fragrance_id
            }
        )
        return MaisonFragranceDetail(
            **self.card(row).model_dump(),
            concentration=str(row.get("concentration")) if row.get("concentration") else None,
            description=str(row.get("description_original") or row.get("description"))
            if row.get("description_original") or row.get("description")
            else None,
            notes=_tokens(row.get("notes")),
            scent_vector=summary,
            recommendation_links=links,
            inspired_by=self.inspired_by(fragrance_id),
        )

    def by_slug(self, slug: str) -> MaisonFragranceDetail | None:
        row = next((item for item in self.catalogue if item.get("slug") == slug), None)
        return self.detail(int(row["id"])) if row else None

    def _recommendation_card(self, item: Mapping[str, object]) -> MaisonRecommendationCard | None:
        target = self._row(int(item["recommended_fragrance_id"]))
        if target is None:
            return None
        return MaisonRecommendationCard(
            fragrance=self.card(target),
            recommendation_type=str(item.get("recommendation_type") or "similar_fragrance"),
            score=float(item.get("score") or 0),
            confidence_score=float(item.get("confidence_score") or 0),
            reason=str(item.get("reason") or "Public-safe AromaTwin profile match."),
            review_status=str(item.get("review_status")),
        )

    def recommendations_for(self, fragrance_id: int) -> list[MaisonRecommendationCard] | None:
        if self._row(fragrance_id) is None:
            return None
        output = [
            self._recommendation_card(item)
            for item in self.recommendations
            if int(item["source_fragrance_id"]) == fragrance_id
        ]
        return sorted(
            (item for item in output if item), key=lambda item: (-item.score, item.fragrance.id)
        )

    def similar(self, fragrance_id: int) -> list[MaisonSimilarFragranceResult] | None:
        cards = self.recommendations_for(fragrance_id)
        if cards is None:
            return None
        return [
            MaisonSimilarFragranceResult(**item.model_dump(), rank=rank)
            for rank, item in enumerate(cards, 1)
        ]

    def inspired_by(self, fragrance_id: int) -> list[MaisonRecommendationCard]:
        output = []
        for item in self.relationships:
            clone_id, original_id = (
                int(item["clone_fragrance_id"]),
                int(item["original_fragrance_id"]),
            )
            if fragrance_id not in {clone_id, original_id}:
                continue
            target = self._row(original_id if fragrance_id == clone_id else clone_id)
            if target:
                output.append(
                    MaisonRecommendationCard(
                        fragrance=self.card(target),
                        recommendation_type="inspired_by",
                        relationship=str(item.get("relationship_type") or "inspired_by"),
                        score=float(item.get("similarity_score") or 0),
                        confidence_score=float(item.get("similarity_score") or 0),
                        reason=str(
                            item.get("difference_summary") or "Reviewed fragrance relationship."
                        ),
                        review_status=str(item["review_status"]),
                    )
                )
        return sorted(output, key=lambda item: (-item.score, item.fragrance.id))

    def scentprint(self, request: MaisonScentprintRequest) -> list[MaisonScentprintResult]:
        requested = {
            key: float(value)
            for key, value in request.dimensions.items()
            if key in VECTOR_DIMENSIONS
        }
        if not requested or any(value < 0 or value > 1 for value in requested.values()):
            raise ValueError("At least one known scent dimension between 0 and 1 is required")
        # Score across every dimension, treating unrequested ones as zero, rather than
        # cosining the requested subset alone. Comparing only the requested keys normalises
        # magnitude away: a profile with woody 0.1 scored identically to one with woody 1.0,
        # and a profile whose strength lies in dimensions the caller did not ask for was never
        # penalised for it.
        query = [requested.get(name, 0.0) for name in VECTOR_DIMENSIONS]
        norm = math.sqrt(sum(value * value for value in query))
        ranked = []
        for row in self.catalogue:
            vector = self.vectors.get(int(row["id"]))
            if not vector:
                continue
            if any(
                value
                and str(value).lower() not in {token.lower() for token in _tokens(row.get(field))}
                for field, value in (
                    ("family", request.family),
                    ("mood", request.mood),
                    ("occasion", request.occasion),
                    ("season", request.season),
                )
            ):
                continue
            values = [float(vector.get(name) or 0) for name in VECTOR_DIMENSIONS]
            other_norm = math.sqrt(sum(value * value for value in values))
            direction = (
                sum(q * v for q, v in zip(query, values, strict=True)) / (norm * other_norm)
                if other_norm and norm
                else 0.0
            )
            # Cosine is scale-invariant, so direction alone cannot separate a profile that is
            # strongly woody from one that is faintly woody. Coverage is how much of the
            # requested intensity the profile actually delivers, and the two multiply.
            wanted = sum(requested.values())
            covered = sum(
                min(value, float(vector.get(name) or 0)) for name, value in requested.items()
            )
            coverage = covered / wanted if wanted else 0.0
            ranked.append((direction * coverage, row, vector))
        ranked.sort(key=lambda item: (-item[0], int(item[1]["id"])))
        return [
            MaisonScentprintResult(
                rank=rank,
                fragrance=self.card(row),
                score=round(score, 6),
                confidence_score=float(vector.get("confidence_score") or 0),
                review_status=str(vector["review_status"]),
            )
            for rank, (score, row, vector) in enumerate(ranked[: request.limit], 1)
        ]

    def catalogue_export(self) -> list[MaisonCatalogueExportRow]:
        return [
            MaisonCatalogueExportRow(
                **self.detail(card.id).model_dump(
                    exclude={"description", "recommendation_links", "inspired_by"}
                )
            )
            for card in self.list_fragrances()
        ]  # type: ignore[union-attr]

    def recommendation_export(self) -> list[MaisonRecommendationCard]:
        return [
            card
            for source in self.list_fragrances()
            for card in (self.recommendations_for(source.id) or [])
        ]


def json_cell(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))
