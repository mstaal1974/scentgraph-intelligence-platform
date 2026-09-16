import json

from pydantic import SecretStr

from aromatwin.schemas.staging_smoke import StagingSmokeRunRequest
from aromatwin.services.staging_smoke_tests import (
    SafeHttpResponse,
    public_summary,
    run_staging_smoke_tests,
)
from scripts.check_staging_operator_handoff import STEPS, build_checklist


def response_transport(method, url, headers, timeout):
    del timeout
    if url.endswith("/private-pilot/health") and "X-API-Key" not in headers:
        return SafeHttpResponse(401, {}, b'{"detail":"Unauthorized"}')
    if method == "OPTIONS":
        return SafeHttpResponse(204, {"Access-Control-Allow-Origin": "https://operator.invalid"}, b"")
    return SafeHttpResponse(200, {}, b'{"status":"ready"}')


def test_smoke_masks_url_and_never_serializes_key():
    key = "unit-test-sensitive-value"
    request = StagingSmokeRunRequest(
        base_url="https://user:pass@staging.invalid/api?token=hidden",
        private_api_key=SecretStr(key),
    )
    result = run_staging_smoke_tests(request, transport=response_transport)
    serialized = result.model_dump_json()
    assert result.base_url_masked == "https://staging.invalid/api?redacted"
    assert key not in serialized
    assert "pass@" not in serialized


def test_unreachable_is_blocked():
    def unreachable(*args):
        raise OSError("unavailable")

    result = run_staging_smoke_tests(
        StagingSmokeRunRequest(base_url="https://staging.invalid"), transport=unreachable
    )
    assert result.overall_status == "blocked_unreachable"


def test_private_denial_and_authenticated_request_pass():
    result = run_staging_smoke_tests(
        StagingSmokeRunRequest(base_url="https://staging.invalid", private_api_key="test-only"),
        transport=response_transport,
    )
    checks = {item.check_name: item.status for item in result.check_results}
    assert checks["private_endpoint_without_key"] == "passed"
    assert checks["private_endpoint_with_key"] == "passed"


def test_public_summary_has_no_checks_or_secret_fields():
    result = run_staging_smoke_tests(
        StagingSmokeRunRequest(base_url="https://staging.invalid", private_api_key="test-only"),
        transport=response_transport,
    )
    payload = json.loads(public_summary(result).model_dump_json())
    assert "check_results" not in payload
    assert "private_api_key" not in payload


def test_handoff_distinguishes_manual_from_complete():
    manual = build_checklist({})
    complete = build_checklist(dict.fromkeys(STEPS, "complete"))
    assert manual.overall_status == "manual_required"
    assert manual.manual_required_count == len(STEPS)
    assert complete.overall_status == "complete"
