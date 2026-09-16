# Supplier Data Security

## Repository audit

Raw supplier imports and their generated artifacts are prohibited from tracked `data/imports/` and
belong under the ignored `data/private/` boundary. Previously tracked dated import artifacts were
removed rather than relabelled as public samples because they contained supplier-commercial fields.
The repository previously contained `data/supplier_import_template.csv` with fictional values in
supplier-sensitive fields. Although those values were examples rather than a real supplier
disclosure, the file created an unsafe public-sample pattern and has been removed.

Its replacement, `data/samples/supplier_identity_sample.csv`, contains fictional identity hints only. Automated tests and `scripts/audit_supplier_data.py` reject pricing, quantity, SKU, cost, and supplier-code columns in public supplier samples.

## Private boundary

Raw files and generated artifacts belong under `data/private/` or another access-controlled location configured with `AROMATWIN_PRIVATE_IMPORT_ROOT`. Both `data/private/` and top-level `private/` are ignored by Git. Operators should verify ignores, restrict filesystem permissions, avoid copying raw rows into tickets or logs, and never force-add private data.

A repository ignore rule reduces accidental commits; it is not encryption or access control. Production operations should use encrypted storage, least-privilege access, secret-managed mount locations, retention limits, and auditable deletion procedures.
# Supplier offer boundary

Supplier-offer source files and detailed comparison reports are private artifacts under
`data/private/`. Public schemas and samples use an explicit identity/workflow allowlist and omit
commercial fields. The protected `/supplier-offers` API returns the same safe projection by
default; authentication does not make a public response safe to contain commercial data.
