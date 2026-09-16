# Private supplier import workflow

Multi-supplier commercial lists use the dedicated offer importer described in
[Multi-supplier offer import](multi-supplier-offer-import.md). Inputs, staging, and detailed reports
must remain under `data/private/`. Import creates offer records only; matching links those offers to
existing candidates or approved catalogue records and cannot promote catalogue content.

Use `scripts/import_supplier_offers.py` for either supported layout and
`scripts/audit_supplier_offers.py` before committing. Console output and public-safe summaries
contain counts and warnings, never private commercial values.
