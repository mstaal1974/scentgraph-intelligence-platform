# Commercial packaging and API entitlements

## Scope

This pack defines proposed plan contracts, deterministic API entitlements, sample-context feature access, and repository-evidence readiness reporting. It creates no customer or tenant, issues no credential, performs no outbound call, changes no fragrance intelligence, and provides no frontend. All plans require manual approval.

Billing is intentionally **not connected**. Prices and payment acceptance require separate external commercial, legal, security, and implementation decisions. The catalogue uses a `contract_review_required` band rather than monetary values and is not an offer for sale.

## Proposed plans

The catalogue contains `internal_maison`, `retailer_starter`, `retailer_growth`, `retailer_enterprise`, `supplier_insights`, `marketplace_operator`, `white_label_partner`, `api_partner`, and `sandbox_developer`. These are capability templates, not accounts. White-label readiness means reviewed public-safe exports can be contractually considered; it does not grant branding rights or permit publication. API partner readiness likewise means contract review can begin, not that access is active.

## Entitlements and tenant-safe access

The API matrix evaluates every plan and API group deterministically. Public-safe groups may receive `public` access. Supplier, seller, consumer, review, launch, deployment, Maison, and operator workflows default to `disabled` for customer plans and require a private credential plus human approval when an internal plan permits them. No credential is generated.

Feature checks use fictional context labels only. Data scopes are `public_safe_only`, `tenant_own_data`, `anonymised_aggregate`, `internal_private`, or `disabled`. Cross-context private access is forbidden. White-label exports remain public-safe unless an internal, manually approved workflow explicitly governs them. Usage reporting contains bands and aggregates, not individual activity.

## Data boundaries

Public responses and exports must never contain supplier prices, supplier codes, CN codes, stock, quantities, currencies, costs, margins, commercial terms, seller-private notes, consumer-private records or notes, individual feedback, credentials, contact details, or real account identifiers. Supplier, seller, and consumer workflows stay private. Third-party descriptions, reviews, ratings, comments, images, and user-generated content are outside this pack.

The commercial router is mounted behind the repository's private API-key dependency. Its default list routes deliberately return reduced public-safe schemas. The full internal contracts contain policy metadata only, never business records.

## Readiness and future work

Readiness means repository contracts are ready for manual model review; it never means paid-launch approval. Legal and commercial review are external human gates. Staging configuration and deployment remain manual. A future billing project must separately decide providers, prices, tax, refunds, metering, authorization, credential lifecycle, and compliance; it must not infer payment authority from this pack.

Never commit credentials, database connection strings, real account or consumer data, real supplier files, seller briefs, private operational reports, or commercial source data. Detailed readiness output belongs only under ignored `data/private/reports/`.
