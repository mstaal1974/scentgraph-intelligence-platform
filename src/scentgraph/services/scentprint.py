from collections.abc import Iterable
from scentgraph.models.scent_vector import VECTOR_DIMENSIONS
from scentgraph.schemas.scentprint import ScentprintMatch, ScentprintRequest, ScentprintResponse
from scentgraph.services.similarity import cosine_similarity


def build_preference_vector(preferences: dict[str, float]) -> dict[str, float]:
    return {dimension: preferences.get(dimension, 0.0) for dimension in VECTOR_DIMENSIONS}


def match_scentprint(
    request: ScentprintRequest, candidates: Iterable[tuple[int, dict[str, float]]] = ()
) -> ScentprintResponse:
    vector = build_preference_vector(request.preferences)
    values = list(vector.values())
    matches = [
        ScentprintMatch(
            fragrance_id=identifier,
            score=cosine_similarity(values, [candidate.get(d, 0.0) for d in VECTOR_DIMENSIONS]),
        )
        for identifier, candidate in candidates
    ]
    matches.sort(key=lambda match: match.score, reverse=True)
    return ScentprintResponse(vector=vector, matches=matches[: request.limit])
