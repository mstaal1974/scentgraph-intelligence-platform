# Private fragrance profile production

## Purpose and boundary

This pack turns reviewed private supplier intake and match-candidate summaries into bounded **draft** profile batches. It reuses the existing intake, matching, bulk-generation, enrichment, provenance, review-gate, persistence, audit, and Maison-readiness foundations; it does not replace them. It provides planning, preflight readiness, private execution, public-safe status summaries, enrichment tasks, provenance requirements, and human-review packets.

It does **not** publish, approve a profile, create a product, create a campaign, deploy infrastructure, call an external service, or create a Maison export. No scent characteristic is inferred when evidence is absent: the field stays empty and its status is `needs_enrichment`.

## Private inputs and outputs

Place real supplier files only in untracked runtime storage below `data/private/imports/`. Run the established supplier intake and matching workflows first. Never commit real supplier files, generated operational profiles, seller briefs, consumer records, credentials, or commercial values. Operational output is constrained to `data/private/runs/{run_id}/profiles/`; detailed plans and readiness reports may also use `data/private/reports/`.

The planner selects only public supplier labels and candidate identifiers. It applies the batch maximum, confidence threshold, duplicate policy, intake-ready requirement, and match requirement. Low-confidence or blocked candidates are excluded unless an operator explicitly enables the low-confidence option; every selected record still requires human review.

## Operator workflow

1. Inspect readiness: `python scripts/export_profile_production_readiness.py`.
2. Preview a plan without writing it: `python scripts/plan_private_profile_batch.py --dry-run --max-profiles 25`.
3. Run a no-write production preview: `python scripts/run_private_profile_batch.py --dry-run --max-profiles 25`.
4. After resolving every blocker, run privately: `python scripts/run_private_profile_batch.py --private-batch-run --run-id RUN_ID --max-profiles 25`.
5. Export review guidance privately: `python scripts/export_profile_review_packet.py RUN_ID`.
6. Audit tracked public artifacts: `python scripts/audit_profile_production_privacy.py`.

Private execution writes draft records plus public-safe summaries, enrichment queue entries, provenance requirements, pending review gates, review packets, and audit events. Review packets ask operators to verify identity, evidence, originality, tags, and provenance. They offer decisions but never apply one. Drafts remain `needs_human_review` until the established review workflow records a separate human decision.

After the first batch, operators complete enrichment and provenance review, approve selected profiles only for catalogue review, and only then invoke the existing Maison export workflow manually.

## Privacy rules

Public API responses contain statuses, bands, identifiers, counts, questions, and original safe summaries only. They exclude source paths and all supplier-commercial, seller-private, consumer-private, individual-feedback, and copied third-party material. The fictional CSVs under `data/samples/` are contract examples, never production output.

## Profile pipeline rehearsal

The fictional, sample-safe rehearsal pack validates integration without real inputs or external side effects. It never approves drafts, creates products, publishes records, or exports to Maison. See [Profile pipeline rehearsal](profile-pipeline-rehearsal.md).
