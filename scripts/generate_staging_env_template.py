#!/usr/bin/env python3
"""Regenerate the placeholder-only staging environment example."""

from pathlib import Path

TEMPLATE = """# Placeholder-only staging configuration. Replace values in the host, never here.
AROMATWIN_ENV=staging
# Generate unique values in the hosting provider secret store.
AROMATWIN_API_KEY=<set-in-host-secret-store>
AROMATWIN_PRIVATE_API_KEY=<set-in-host-secret-store>
# Inject the managed connection string through the host secret store.
DATABASE_URL=<set-in-host-secret-store>
# Mount this directory as private, persistent runtime storage.
PRIVATE_STORAGE_ROOT=/var/lib/aromatwin/private
PUBLIC_SAMPLE_ROOT=data/samples
CORS_ALLOWED_ORIGINS=https://staging.example.invalid
LOG_LEVEL=INFO
ENABLE_PUBLIC_API=true
ENABLE_PRIVATE_WORKFLOWS=true
ENABLE_PERSISTENCE=true
ENABLE_REVIEW_WORKFLOW=true
ENABLE_PRIVATE_PILOT=false
ENABLE_PLATFORM_COMPLETION=true
"""


def main() -> int:
    target = Path("deployment/staging.env.example")
    target.parent.mkdir(exist_ok=True)
    target.write_text(TEMPLATE, encoding="utf-8")
    print(f"Generated {target} with placeholders only.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
