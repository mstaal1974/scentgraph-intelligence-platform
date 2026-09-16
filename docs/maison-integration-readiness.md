# Maison Obsidian integration readiness

## Scope

This pack prepares an **internal handoff contract** through public-safe, allow-listed product,
recommendation, Scentprint-match, and bundle shapes. It assesses evidence, emits local export files,
and describes a proposed transfer in a sync manifest. It does not modify the Maison Obsidian website,
call an external API, publish a product, create a campaign, deploy infrastructure, or connect to a
storefront or advertising/payment platform.

A later workflow will take approved AromaTwin records, validate them against these contracts, produce
a reviewed export bundle, and exercise the contract against a separately deployed staging API. The
Maison website must later be updated in its own repository by its maintainers; this repository neither
contains nor changes that website.

## Contracts

* **Product:** identifiers, display copy, supported variant labels, reviewed fragrance attributes,
  banded performance and public price information, tags, and statuses.
* **Recommendation:** product links, recommendation type, banded score, and original public-safe
  reasons. No individual feedback is carried.
* **Scentprint match:** a non-identifying public alias, banded fit/confidence, and reviewed summary.
* **Bundle:** public title/copy, product and variant identifiers, reviewed context, and statuses.

Fields are enforced by Pydantic schemas and an allow-list exporter. Unknown source fields are dropped.
No unreviewed attributes should be inferred merely to populate a contract.

## Sync manifest and dry runs

The manifest records counts, local filenames and checksums, review/privacy state, blockers, and the next
operator action. Supported modes are `dry_run`, `staging_contract_test`, and
`public_safe_export_only`; none performs a sync. `build_maison_export_bundle.py --dry-run` only prints
its plan. Operational artifacts default to `data/private/reports/maison/`; fictional samples can be
written explicitly under `data/samples/`.

## Privacy and review boundary

Only approved summaries, bands, counts, public aliases, and original public-safe copy may cross the
boundary. Supplier commercial attributes, seller-private material, consumer records, individual
feedback, secrets, credentials, and copied third-party material must never be committed or exported.
Every record still requires the existing provenance and human-review gates. “Approved for Maison” means
internal handoff readiness, not approval for public launch.

## Still required outside this PR

Real supplier input must be placed in ignored private runtime storage. Operators must configure staging
secrets outside Git, deploy the staging API, run smoke tests, complete the private supplier pilot and
human review, generate the export bundle, and review its manifest. The separate Maison repository will
later need an authenticated staging client, mapping and presentation work, failure handling, and its own
review and release process. No live publication is recommended by this pack.
# Future Scentprint quiz integration

The backend now defines a public-safe quiz contract and fictional demo result shape; see
[`scentprint-quiz-contract.md`](scentprint-quiz-contract.md). This is contract readiness only. No
Maison frontend, account linkage, deployment, automatic publication, or campaign behavior is part
of the pack. A later Maison-repository change may render the versioned options after staging,
privacy, content, and human reviews.

## Commercial entitlement boundary

Maison integration remains an internal API group. A commercial plan definition does not activate synchronization: private authentication, operator approval, staging evidence, and the existing Maison readiness gates still apply. Public and white-label summaries contain only reviewed public-safe fields.

## Profile production prerequisite

A private production draft is not Maison-ready. Complete enrichment, provenance review, human profile review, and catalogue review first. Maison bundles remain a separate, explicitly invoked workflow and are never produced by profile-production endpoints or scripts.
