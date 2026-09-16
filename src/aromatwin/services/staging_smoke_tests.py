"""Run sanitized, read-only HTTP checks against a human-deployed staging API."""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit, urlunsplit
from urllib.request import Request, urlopen
from uuid import uuid4

from aromatwin.schemas.staging_smoke import (
    StagingSmokeCheckResult,
    StagingSmokePublicSummary,
    StagingSmokeRunRequest,
    StagingSmokeRunResult,
)

SECRET_KEY = re.compile(r"(?i)(api.?key|authorization|password|secret|token|database.?url)")
PRIVATE_KEY = re.compile(
    r"(?i)(supplier.?price|supplier.?cost|supplier.?code|cn.?code|aed.?price|usd.?price|"
    r"margin|stock|quantity|seller.?private|consumer.?private|email|phone|address)"
)
SECRET_VALUE = re.compile(r"(?i)(?:bearer\s+\S+|(?:sk|rk|ghp)_[A-Za-z0-9_-]{12,}|\w+://[^\s:/]+:[^\s@]+@)")


@dataclass(frozen=True)
class SafeHttpResponse:
    status: int
    headers: Mapping[str, str]
    body: bytes


Transport = Callable[[str, str, Mapping[str, str], float], SafeHttpResponse]


def mask_base_url(value: str) -> str:
    """Remove credentials and redact sensitive query values while retaining routing context."""
    parts = urlsplit(value)
    host = parts.hostname or "invalid-host"
    if parts.port:
        host = f"{host}:{parts.port}"
    query = "redacted" if parts.query else ""
    return urlunsplit((parts.scheme, host, parts.path.rstrip("/"), query, ""))


def _default_transport(method: str, url: str, headers: Mapping[str, str], timeout: float) -> SafeHttpResponse:
    request = Request(url, method=method, headers=dict(headers))
    try:
        with urlopen(request, timeout=timeout) as response:  # noqa: S310 - operator-supplied staging URL
            return SafeHttpResponse(response.status, dict(response.headers), response.read(1_000_000))
    except HTTPError as error:
        return SafeHttpResponse(error.code, dict(error.headers), error.read(1_000_000))


def _payload_risks(body: bytes) -> tuple[bool, bool]:
    try:
        payload = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        text = body.decode("utf-8", errors="replace")
        return bool(SECRET_VALUE.search(text)), bool(PRIVATE_KEY.search(text))
    secret = private = False

    def walk(value: object) -> None:
        nonlocal secret, private
        if isinstance(value, dict):
            for key, item in value.items():
                secret |= bool(SECRET_KEY.search(str(key)))
                private |= bool(PRIVATE_KEY.search(str(key)))
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)
        elif isinstance(value, str):
            secret |= bool(SECRET_VALUE.search(value))

    walk(payload)
    return secret, private


def run_staging_smoke_tests(
    request: StagingSmokeRunRequest, *, transport: Transport | None = None
) -> StagingSmokeRunResult:
    """Execute read-only checks and retain only sanitized status metadata."""
    started = datetime.now(UTC)
    send = transport or _default_transport
    base = str(request.base_url).rstrip("/") + "/"
    api_key = request.private_api_key.get_secret_value() if request.private_api_key else None
    results: list[StagingSmokeCheckResult] = []
    responses: list[SafeHttpResponse] = []
    unreachable = False

    def check(name: str, path: str, expected: set[int], *, key: bool = False, method: str = "GET") -> None:
        nonlocal unreachable
        headers = {"Accept": "application/json"}
        if key and api_key:
            headers["X-API-Key"] = api_key
        try:
            response = send(method, urljoin(base, path.lstrip("/")), headers, request.timeout_seconds)
        except (OSError, TimeoutError, URLError):
            unreachable = True
            results.append(StagingSmokeCheckResult(check_name=name, status="failed", summary="Endpoint was unreachable.", blocker_type="unreachable"))
            return
        responses.append(response)
        ok = response.status in expected
        results.append(StagingSmokeCheckResult(
            check_name=name, status="passed" if ok else "failed", http_status=response.status,
            summary="Expected status received." if ok else "Unexpected HTTP status received.",
            blocker_type=None if ok else ("auth_failure" if "private" in name else "readiness_failure"),
        ))

    check("public_health", "/health", {200})
    check("deployment_health", "/deployment/health", {200})
    if request.include_openapi_check:
        check("openapi", "/openapi.json", {200})
    else:
        results.append(StagingSmokeCheckResult(check_name="openapi", status="skipped", summary="Optional check disabled."))
    if request.include_private_checks:
        check("private_endpoint_without_key", "/private-pilot/health", {401, 403})
        if api_key:
            check("private_endpoint_with_key", "/private-pilot/health", {200}, key=True)
            check("platform_completion_readiness", "/platform-completion/readiness", {200}, key=True)
            check("private_pilot_health", "/private-pilot/health", {200}, key=True)
            check("review_workflow_health", "/review-workflow/health", {200}, key=True)
            check("operations_health", "/operations/health", {200}, key=True)
        else:
            for name in ("private_endpoint_with_key", "platform_completion_readiness", "private_pilot_health", "review_workflow_health", "operations_health"):
                results.append(StagingSmokeCheckResult(check_name=name, status="skipped", summary="No private key supplied through the environment."))
    else:
        results.append(StagingSmokeCheckResult(check_name="private_checks", status="skipped", summary="Private checks disabled by operator."))
    check("deployment_readiness", "/deployment/readiness", {200})

    secret_risk = any(_payload_risks(item.body)[0] for item in responses)
    private_risk = any(_payload_risks(item.body)[1] for item in responses)
    results.extend([
        StagingSmokeCheckResult(check_name="runtime_secret_exposure", status="failed" if secret_risk else "passed", summary="Potential secret markers detected." if secret_risk else "No obvious secret markers detected.", blocker_type="privacy_risk" if secret_risk else None),
        StagingSmokeCheckResult(check_name="runtime_private_data_exposure", status="failed" if private_risk else "passed", summary="Potential private-data field markers detected." if private_risk else "No private-data field markers detected.", blocker_type="privacy_risk" if private_risk else None),
        StagingSmokeCheckResult(check_name="response_secret_values", status="failed" if secret_risk else "passed", summary="Potential credential-shaped value detected." if secret_risk else "No credential-shaped values detected.", blocker_type="privacy_risk" if secret_risk else None),
    ])
    if request.include_cors_check:
        try:
            cors = send("OPTIONS", base, {"Origin": "https://untrusted.invalid", "Access-Control-Request-Method": "GET"}, request.timeout_seconds)
            allow_origin = next((v for k, v in cors.headers.items() if k.lower() == "access-control-allow-origin"), "")
            dangerous = allow_origin.strip() == "*" and request.expected_environment == "staging"
            results.append(StagingSmokeCheckResult(check_name="cors_policy", status="failed" if dangerous else "passed", http_status=cors.status, summary="Wildcard CORS detected in staging." if dangerous else "CORS is not dangerously permissive.", blocker_type="privacy_risk" if dangerous else None))
        except (OSError, TimeoutError, URLError):
            results.append(StagingSmokeCheckResult(check_name="cors_policy", status="warning", summary="CORS preflight could not be evaluated."))
    else:
        results.append(StagingSmokeCheckResult(check_name="cors_policy", status="skipped", summary="Optional check disabled."))

    blockers = sorted({item.blocker_type for item in results if item.status == "failed" and item.blocker_type})
    warnings = [item.summary for item in results if item.status == "warning"]
    if secret_risk or private_risk or "privacy_risk" in blockers:
        overall = "blocked_privacy_risk"
    elif unreachable:
        overall = "blocked_unreachable"
    elif "auth_failure" in blockers:
        overall = "blocked_auth_failure"
    elif "readiness_failure" in blockers:
        overall = "blocked_readiness_failure"
    elif any(item.status == "failed" for item in results):
        overall = "blocked_unknown_failure"
    elif warnings or any(item.status == "skipped" for item in results):
        overall = "staging_smoke_passed_with_warnings"
    else:
        overall = "staging_smoke_passed"
    counts = {status: sum(item.status == status for item in results) for status in ("passed", "warning", "failed", "skipped")}
    action = "Proceed to the manual private supplier pilot handoff." if overall == "staging_smoke_passed" else ("Review warnings and complete skipped checks before the pilot." if overall == "staging_smoke_passed_with_warnings" else "Resolve blocking smoke checks and rerun the staging smoke test.")
    return StagingSmokeRunResult(
        smoke_run_id=f"smoke-{uuid4()}", base_url_masked=mask_base_url(base), started_at=started,
        completed_at=datetime.now(UTC), overall_status=overall, passed_count=counts["passed"],
        warning_count=counts["warning"], failed_count=counts["failed"], skipped_count=counts["skipped"],
        check_results=results, blockers=blockers, warnings=warnings, recommended_next_action=action,
    )


def public_summary(result: StagingSmokeRunResult) -> StagingSmokePublicSummary:
    """Project a smoke run into its intentionally narrow public contract."""
    fields = StagingSmokePublicSummary.model_fields
    return StagingSmokePublicSummary(**{name: getattr(result, name) for name in fields})
