from collections.abc import Iterable


def missing_headers(actual: Iterable[str], required: Iterable[str]) -> set[str]:
    return set(required) - set(actual)
