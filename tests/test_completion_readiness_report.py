from aromatwin.services.platform_completion import PlatformCompletionService


def test_report_separates_safe_and_blocked_work():
    _, report = PlatformCompletionService().run()
    assert report.safe_to_run_now
    assert report.requires_private_supplier_files
    assert report.requires_api_keys_or_secrets
    assert report.requires_human_review
    assert report.requires_deployment
    assert report.requires_external_website_repository_work
    assert "data privacy controls" in report.sections
