from aromatwin.schemas.platform_completion import PlatformCompletionRequest
from aromatwin.services.platform_completion import PlatformCompletionService


def test_safe_checks_complete_without_private_data():
    result, _ = PlatformCompletionService().run()
    assert result.completed_count > 0
    assert result.final_platform_status == "repository_complete_ready_for_private_data"
    assert result.private_pilot_readiness_status == "ready_after_private_supplier_files_added"


def test_demo_does_not_require_real_supplier_files():
    result, _ = PlatformCompletionService().run(PlatformCompletionRequest(demo_mode=True))
    assert result.failed_count == 0
    assert any(blocker.blocker_type == "private_data" for blocker in result.blockers)
