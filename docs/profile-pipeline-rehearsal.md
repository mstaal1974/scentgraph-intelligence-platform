# Profile pipeline rehearsal

This pack exercises the existing supplier intake, matching, batch planning, draft generation, enrichment, provenance, review, Maison-readiness, and completion boundaries using **fictional, sample-safe identifiers**. It makes no network request and cannot approve or publish a profile, create a product, export to Maison, or deploy infrastructure.

Real supplier files are never required or committed. This prevents confidential commercial values and private seller or consumer material from entering source control. Draft approval remains a human decision because the rehearsal provides integration evidence, not factual fragrance evidence.

## Modes and commands

- `python scripts/run_profile_pipeline_rehearsal.py --mode dry_rehearsal` runs in memory and writes nothing.
- `python scripts/run_profile_pipeline_rehearsal.py --mode sample_private_rehearsal --max-candidates 1 --write-private` may write identifier-only detail beneath `data/private/reports/rehearsals/`.
- `--mode trace_only` builds the trace without simulating draft counts.

The trace follows one fictional candidate through every required stage. References are opaque identifiers; summaries state only the check outcome. The gap report separates code gaps (`operator_action_required=false`) from real-world tasks (`true`). Small deterministic wiring gaps may be fixed in code, while staging setup, authorized runtime input placement, factual review, approval, and any later handoff require an operator.

Run `python scripts/audit_profile_pipeline_rehearsal_privacy.py` before sharing samples. After a pass, configure staging, smoke-test it, place authorized inputs in private runtime storage, run intake and matching, produce private drafts, complete enrichment and provenance review, obtain catalogue review approval, and only then generate a reviewed Maison bundle.
