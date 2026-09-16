import pytest
from aromatwin.services.similarity import cosine_similarity


def test_cosine_similarity() -> None:
    assert cosine_similarity([1, 2, 3], [1, 2, 3]) == pytest.approx(1)
    assert cosine_similarity([1, 0], [0, 1]) == 0


def test_zero_vector_has_no_similarity() -> None:
    assert cosine_similarity([0, 0], [1, 1]) == 0


def test_vectors_require_same_dimensions() -> None:
    with pytest.raises(ValueError):
        cosine_similarity([1], [1, 2])
