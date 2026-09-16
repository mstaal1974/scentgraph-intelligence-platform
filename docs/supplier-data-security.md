# Supplier Data Security

## Repository audit

The original tracked `data/imports/supplier-2026-04-26/` directory was reviewed and contained documentation only—no raw supplier CSV or spreadsheet was committed. It now contains fictional, sanitised staging exports required by profile-builder tests; automated auditing rejects commercial columns there. The repository did contain `data/supplier_import_template.csv` with fictional values in supplier-sensitive fields (`CN CODE`, `QTY`, `AED`, and `USD`). Although those values were examples rather than a real supplier disclosure, the file created an unsafe public-sample pattern and has been removed.

Its replacement, `data/samples/supplier_identity_sample.csv`, contains fictional identity hints only. Automated tests and `scripts/audit_supplier_data.py` reject pricing, quantity, SKU, cost, and supplier-code columns in public supplier samples.

## Private boundary

Raw files and generated artifacts belong under `data/private/` or another access-controlled location configured with `AROMATWIN_PRIVATE_IMPORT_ROOT`. Both `data/private/` and top-level `private/` are ignored by Git. Operators should verify ignores, restrict filesystem permissions, avoid copying raw rows into tickets or logs, and never force-add private data.

A repository ignore rule reduces accidental commits; it is not encryption or access control. Production operations should use encrypted storage, least-privilege access, secret-managed mount locations, retention limits, and auditable deletion procedures.
