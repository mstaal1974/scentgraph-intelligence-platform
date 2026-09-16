from dataclasses import dataclass
from enum import StrEnum


class PermittedUse(StrEnum):
    official_source = "official_source"
    supplier_source = "supplier_source"
    reference_only = "reference_only"
    restricted_non_commercial = "restricted_non_commercial"
    licensed_commercial = "licensed_commercial"
    unknown = "unknown"


@dataclass(frozen=True)
class SourcePolicy:
    source_name: str
    source_type: str
    permitted_use: PermittedUse
    commercial_use_allowed: bool = False
    can_copy_text: bool = False
    can_copy_images: bool = False
    can_use_for_matching: bool = False

    def __post_init__(self) -> None:
        if not self.commercial_use_allowed and (self.can_copy_text or self.can_copy_images):
            raise ValueError("Non-commercial sources cannot permit text or image copying")


def restricted_reference_policy(source_name: str) -> SourcePolicy:
    return SourcePolicy(
        source_name=source_name,
        source_type="dataset",
        permitted_use=PermittedUse.restricted_non_commercial,
        can_use_for_matching=True,
    )


def validate_matching_use(policy: SourcePolicy) -> None:
    if not policy.can_use_for_matching:
        raise ValueError(f"Source '{policy.source_name}' cannot be used for matching")


def validate_commercial_promotion(policy: SourcePolicy) -> None:
    if (
        policy.permitted_use
        in {
            PermittedUse.reference_only,
            PermittedUse.restricted_non_commercial,
            PermittedUse.unknown,
        }
        or not policy.commercial_use_allowed
    ):
        raise ValueError(
            "Restricted or reference-only sources cannot be promoted to the commercial catalogue"
        )
