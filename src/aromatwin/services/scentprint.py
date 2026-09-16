from aromatwin.models.scent_vector import VECTOR_DIMENSIONS
from aromatwin.schemas.scentprint import ScentprintRequest, ScentprintResponse


def match_scentprint(request: ScentprintRequest) -> ScentprintResponse:
    return ScentprintResponse(
        vector={
            dimension: request.preferences.get(dimension, 0.0) for dimension in VECTOR_DIMENSIONS
        },
        matches=[],
    )
