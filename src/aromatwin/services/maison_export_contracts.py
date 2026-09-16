"""Allow-list based Maison exports; unknown/private input keys are never propagated."""

from typing import TypeVar

from pydantic import BaseModel

from aromatwin.schemas.maison_integration import (
    MaisonBundleExportRead,
    MaisonProductExportRead,
    MaisonRecommendationExportRead,
    MaisonScentprintMatchExportRead,
)

T = TypeVar("T", bound=BaseModel)

PRODUCT_EXPORT_FIELDS = tuple(MaisonProductExportRead.model_fields)
RECOMMENDATION_EXPORT_FIELDS = tuple(MaisonRecommendationExportRead.model_fields)
SCENTPRINT_MATCH_EXPORT_FIELDS = tuple(MaisonScentprintMatchExportRead.model_fields)
BUNDLE_EXPORT_FIELDS = tuple(MaisonBundleExportRead.model_fields)


def _export(model: type[T], record: dict[str, object]) -> T:
    """Validate only explicitly allow-listed fields and silently discard private extras."""
    allowed = {key: value for key, value in record.items() if key in model.model_fields}
    return model.model_validate(allowed)


def export_product(record: dict[str, object]) -> MaisonProductExportRead:
    return _export(MaisonProductExportRead, record)


def export_recommendation(record: dict[str, object]) -> MaisonRecommendationExportRead:
    return _export(MaisonRecommendationExportRead, record)


def export_scentprint_match(record: dict[str, object]) -> MaisonScentprintMatchExportRead:
    return _export(MaisonScentprintMatchExportRead, record)


def export_bundle(record: dict[str, object]) -> MaisonBundleExportRead:
    return _export(MaisonBundleExportRead, record)


def contract_fields() -> dict[str, tuple[str, ...]]:
    return {"products": PRODUCT_EXPORT_FIELDS, "recommendations": RECOMMENDATION_EXPORT_FIELDS,
            "scentprint_matches": SCENTPRINT_MATCH_EXPORT_FIELDS, "bundles": BUNDLE_EXPORT_FIELDS}
