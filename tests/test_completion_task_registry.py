from aromatwin.services.completion_task_registry import (
    REQUIRED_CATEGORIES,
    build_completion_task_registry,
)


def test_registry_contains_every_required_category():
    tasks = build_completion_task_registry()
    assert set(REQUIRED_CATEGORIES) <= {task.category for task in tasks}


def test_external_requirements_are_never_automatically_completed():
    tasks = build_completion_task_registry()
    for task in tasks:
        if (task.requires_private_supplier_files or task.requires_credentials
                or task.requires_human_review or task.requires_external_repository
                or task.requires_deployment_environment):
            assert not task.can_complete_automatically
            assert task.status.startswith("blocked_")
