"""Discover supplier files without moving or disclosing their values."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from aromatwin.schemas.private_supplier_pilot import PrivateSupplierIntakeRead

SUPPORTED_SUFFIXES = {".csv", ".xls", ".xlsx"}
PRIVATE_MARKERS = ("price", "cost", "margin", "stock", "quantity", "qty", "supplier_code",
                   "cn_code", "aed", "usd", "commercial", "terms")
FORMAT_REQUIRED = {
    "existing_supplier": {"brand", "name"},
    "fatma": {"brand", "product"},
    "generic_supplier": {"brand", "product_name"},
}


def _inside(path: Path, root: Path) -> bool:
    return path == root or path.is_relative_to(root)


class PrivateSupplierIntakeService:
    def __init__(self, data_root: str | Path = "data") -> None:
        self.data_root = Path(data_root).resolve()
        self.private_root = self.data_root / "private"
        self.import_root = self.private_root / "imports"

    def scan(self, location: str | Path | None = None) -> list[PrivateSupplierIntakeRead]:
        root = Path(location or self.import_root).resolve()
        if root.is_file():
            paths = [root]
        elif root.exists():
            paths = sorted(path for path in root.rglob("*") if path.is_file())
        else:
            paths = []
        return [self.inspect(path) for path in paths]

    def inspect(self, source: str | Path) -> PrivateSupplierIntakeRead:
        path = Path(source).resolve()
        created = datetime.now(UTC)
        digest = hashlib.sha256(str(path).encode()).hexdigest()[:12]
        base = dict(intake_id=f"intake-{digest}", supplier_public_label=self._label(path),
                    private_source_path=str(path), file_type=path.suffix.lower().lstrip(".") or "none",
                    row_count_estimate=0, header_confidence="none", detected_private_fields=[],
                    blocking_issues=[], recommended_next_action="Do not process this file.",
                    created_at=created)
        if not _inside(path, self.private_root) or _inside(path, self.data_root / "samples"):
            return PrivateSupplierIntakeRead(**{**base, "detected_format": "unknown",
                "readiness_status": "blocked_outside_private_path",
                "blocking_issues": ["source_not_under_data_private"]})
        if path.suffix.lower() not in SUPPORTED_SUFFIXES:
            return PrivateSupplierIntakeRead(**{**base, "detected_format": "unknown",
                "readiness_status": "blocked_unsupported_file_type",
                "blocking_issues": ["unsupported_file_type"]})
        try:
            frame = (pd.read_csv(path, nrows=1000) if path.suffix.lower() == ".csv"
                     else pd.read_excel(path, nrows=1000))
        except Exception:  # malformed input becomes a safe blocker, never a value-bearing error
            return PrivateSupplierIntakeRead(**{**base, "detected_format": "unknown",
                "readiness_status": "blocked_missing_required_columns",
                "blocking_issues": ["header_unreadable"]})
        headers = {str(value).strip().lower().replace(" ", "_") for value in frame.columns}
        private = sorted(marker for marker in PRIVATE_MARKERS if any(marker in h for h in headers))
        detected = self._format(headers, path)
        required = FORMAT_REQUIRED.get(detected, set())
        missing = sorted(required - headers)
        status = "ready_for_import"
        issues: list[str] = []
        action = "Proceed to controlled import after operator review."
        if detected == "unknown":
            status, issues, action = ("needs_format_mapping", ["unknown_supplier_format"],
                                      "Create and approve a private format mapping.")
        elif missing:
            status, issues, action = ("blocked_missing_required_columns",
                                      ["missing_required_columns"],
                                      "Correct the private file or approved mapping.")
        return PrivateSupplierIntakeRead(**{**base, "detected_format": detected,
            "row_count_estimate": len(frame),
            "header_confidence": "high" if detected != "unknown" else "low",
            "detected_private_fields": private, "readiness_status": status,
            "blocking_issues": issues, "recommended_next_action": action})

    @staticmethod
    def _format(headers: set[str], path: Path) -> str:
        if "fatma" in path.name.lower() and {"brand", "product"} <= headers:
            return "fatma"
        if {"brand", "name"} <= headers:
            return "existing_supplier"
        if {"brand", "product_name"} <= headers:
            return "generic_supplier"
        return "unknown"

    def _label(self, path: Path) -> str:
        try:
            relative = path.relative_to(self.import_root)
            candidate = relative.parts[1] if relative.parts[0] == "suppliers" and len(relative.parts) > 2 else path.parent.name
        except ValueError:
            candidate = "private-supplier"
        safe = "".join(char.lower() if char.isalnum() else "-" for char in candidate).strip("-")
        return safe or "private-supplier"


def public_intake_summary(item: PrivateSupplierIntakeRead) -> dict[str, object]:
    rows = item.row_count_estimate
    band = "none" if rows == 0 else "small" if rows <= 100 else "medium" if rows <= 1000 else "large"
    return {"intake_id": item.intake_id, "supplier_public_label": item.supplier_public_label,
            "detected_format": item.detected_format, "file_type": item.file_type,
            "row_count_band": band, "header_confidence": item.header_confidence,
            "readiness_status": item.readiness_status, "blocker_count": len(item.blocking_issues),
            "recommended_next_action": item.recommended_next_action}
