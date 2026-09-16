from aromatwin.config import Settings
from aromatwin.main import create_app


def test_openapi_exposes_all_scentprint_quiz_endpoints():
    paths = create_app(Settings()).openapi()["paths"]
    expected = {"/scentprint-quiz/health", "/scentprint-quiz/contract",
                "/scentprint-quiz/questions", "/scentprint-quiz/score",
                "/scentprint-quiz/results/demo", "/scentprint-quiz/audit"}
    assert expected <= set(paths)
    score_schema = paths["/scentprint-quiz/score"]["post"]
    assert "requestBody" in score_schema
