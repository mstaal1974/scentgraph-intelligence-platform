# Private supplier import workflow

Multi-supplier commercial lists use the dedicated offer importer described in
[Multi-supplier offer import](multi-supplier-offer-import.md). Inputs, staging, and detailed reports
must remain under `data/private/`. Import creates offer records only; matching links those offers to
existing candidates or approved catalogue records and cannot promote catalogue content.

Use `scripts/import_supplier_offers.py` for either supported layout and
`scripts/audit_supplier_offers.py` before committing. Console output and public-safe summaries
contain counts and warnings, never private commercial values.

## Sourcing and margin reports

Private staged offers can be consumed by `scripts/build_supplier_sourcing_report.py`; its full output is restricted to `data/private/reports/`. Margin assumptions and outputs use the same private boundary. See [Supplier sourcing and margin intelligence](supplier-sourcing-margin-intelligence.md).
