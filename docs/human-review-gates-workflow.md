# Human review gates workflow

The review workflow turns generated intelligence into **human-reviewed, action-ready internal
work**. It does not add intelligence, a storefront, campaign generation, or a public marketplace.

## Gates and queues

Fourteen formal gate types cover supplier offers, matching, profile drafts, enrichment,
provenance, catalogue approval, product readiness, sourcing, margin bands, seller-demand matches,
aggregate consumer signals, launch candidates, pilot blockers, and public exports. Every gate
requires evidence, names an owner role, permits an explicit decision, and requires an audit trail.
There is no auto-approval path.

The queue builder accepts allow-listed workflow summaries from profile, enrichment, provenance,
sourcing, seller-demand, aggregate consumer-signal, launch, pilot, persistence, and operational
audit sources. It emits identifiers, bands, statuses, role labels, and constructed public-safe
summaries. It never copies arbitrary source prose into queue output.

## Decisions are not publication

A decision records a reviewer role/pseudonymous alias, internal reason, safe evidence summary,
next internal status, and audit requirement. Approval means only approval for the named next
internal stage. It does **not** publish, promote a catalogue record, create a product or SKU,
initiate a launch, or generate a campaign. Repeated identical decisions receive the same stable
identifier to support idempotent handling.

When persistence is supplied, the decision service calls its audit boundary. The in-memory API is
an operational adapter, not production persistence; production callers should persist the queue
summary and decision audit event in one transaction.

## Operational connections

Pilot blockers and launch candidates enter dedicated review gates. Their approval unlocks planning,
not execution. Persistence records can be projected into the same queue without changing existing
workflow services. A future admin UI may consume these private endpoints, but no UI is part of this
layer.

## Privacy boundary

Default API responses are public-safe projections even though routes require the private API key.
They expose IDs, bands, statuses, aggregate counts, safe summaries, and roles only. Private decision
reasons remain in private operational storage.

Never commit real supplier files, seller briefs, consumer records, private notes, individual
feedback, contact details, supplier identifiers, customs identifiers, inventory, quantities,
prices, costs, margin values, or commercial conditions. Never copy third-party descriptions,
reviews, ratings, images, comments, or user-generated content.

## Private supplier pilot execution pack

The focused execution layer is documented in [Private supplier pilot execution](private-supplier-pilot-execution.md). It adds path-safe intake, explicit preflight plans, private run boundaries, aggregate acceptance evidence, privacy auditing, and mandatory human review without changing the underlying intelligence workflow or permitting publication.
