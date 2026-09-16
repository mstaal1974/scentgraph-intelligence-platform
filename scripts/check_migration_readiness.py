#!/usr/bin/env python3
"""Statically inspect migrations without connecting to or changing a database."""

import ast
import json
from pathlib import Path


def inspect_migrations(root: Path = Path("database/migrations/versions")) -> dict[str, object]:
    files = sorted(root.glob("*.py"))
    errors: list[str] = []
    postgres_only: list[str] = []
    for path in files:
        source = path.read_text(encoding="utf-8")
        try:
            compile(source, str(path), "exec", ast.PyCF_ONLY_AST)
        except SyntaxError as exc:
            errors.append(f"{path.name}: line {exc.lineno}")
        if any(marker in source.lower() for marker in ("postgresql", "jsonb", "uuid_generate")):
            postgres_only.append(path.name)
    return {
        "status": "ready" if files and not errors else "blocked",
        "migration_file_count": len(files), "import_syntax_errors": errors,
        "postgres_only_migrations": postgres_only,
        "sqlite_caveat": "SQLite is for local checks only; hosted staging is expected to use PostgreSQL.",
        "destructive_actions_run": False,
    }


def main() -> int:
    report = inspect_migrations()
    print(json.dumps(report, indent=2))
    return int(report["status"] != "ready")


if __name__ == "__main__":
    raise SystemExit(main())
