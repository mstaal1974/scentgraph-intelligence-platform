import pytest
from scentgraph.services.similarity import cosine_similarity


def test_cosine_similarity_identical_vectors() -> None:
    assert cosine_similarity([1, 2, 3], [1, 2, 3]) == pytest.approx(1)


def test_cosine_similarity_orthogonal_vectors() -> None:
    assert cosine_similarity([1, 0], [0, 1]) == 0


def test_cosine_similarity_zero_vector() -> None:
    assert cosine_similarity([0, 0], [1, 1]) == 0


def test_cosine_similarity_requires_matching_dimensions() -> None:
    with pytest.raises(ValueError):
        cosine_similarity([1], [1, 2])
