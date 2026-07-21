# IN-14 — Documentation Factory

**Type:** Production

**State:** Seeded

**Lifecycle position:** Cross-cutting (produces stakeholder documentation at any lifecycle stage)

---

## Purpose

The Documentation Factory turns business observability data into stakeholder-facing documents. A factory here is a generation procedure — implementable as deterministic tooling or an AI-executed method. Teams that author stakeholder documentation manually produce inconsistent artifacts — a service summary written in January, a portfolio report written in June, and a compliance report written in October each reflect different snapshots, different authors' emphasis, and different data freshness. The factory pattern inverts this: a single query against current data produces every document the stakeholder set needs, at the altitude they need it.

## Inputs

- Service profiles — identity, stakeholders, impact categories, ownership
- Signal definitions — what's measured, at what thresholds, across which layers
- Operational state — dashboard coverage, playbook coverage, alert coverage
- Document templates by audience — executive summary, team onboarding brief, compliance report, adoption update
- Altitude-filtering rules — same underlying data, different summarization depth per audience

## Outputs

- Executive summaries — portfolio view, one-line-per-service with health-definition coverage and impact categories (definition state from the system of record — live health display belongs to the monitoring platforms the definitions feed)
- Team onboarding briefs — service-specific, showing what the team needs to know and do
- Compliance reports — observability coverage against regulatory / permit-to-operate checklists
- Adoption updates — progress against targets, friction patterns, stuck services
- Portfolio maturity views — aggregate progression across the service inventory

## Generation Approach

1. Query current data — service profiles, signals, operational state
2. Apply the template for the target audience
3. Filter by altitude — an executive summary strips technical detail; a team onboarding brief includes it
4. Inject stakeholder-appropriate language — impact categories become executive-readable phrases, technical signal names become plain-language descriptions
5. Emit the document in the target format (markdown, slide, PDF, Confluence page)
6. Validate — every document reflects current data on generation; no stale snapshots

## Design Principles

- **Currency over craftsmanship.** A hand-crafted document is stale the moment it ships. A generated document reflects current state on every read.
- **Altitude-appropriate, not altitude-watered-down.** An executive summary isn't a technical document with the technical parts removed. It's a different document composed from the same data, led by what the executive needs to decide.
- **Single source, many views.** A change to a service profile propagates to every document that draws from it — executive summary, onboarding brief, compliance report update together.
- **Documents link back to their data.** Every generated document carries a reference to the source data and generation timestamp, so consumers can verify currency and trace claims.

## KA Cross-References

| KA | Relationship |
|----|-------------|
| [KA10 — Stakeholder Engagement](../ka10-stakeholder-engagement.md) | This instrument produces communication artifacts for [KA10.2](../ka10-stakeholder-engagement.md#cross-altitude-communication) (Cross-Altitude Communication) |
| [KA08 — Data Governance](../ka08-data-governance.md) | Document currency depends on the system-of-record data quality this KA governs |

## Related Instruments

- [IN-04 Service Profile Template](in-04-service-profile-template.md) — primary data source
- [IN-20 Portfolio Maturity View](in-20-portfolio-maturity-view.md) — a specific type of generated document
- [IN-21 Terrain Presentation](in-21-terrain-presentation.md) — a specific type of generated stakeholder communication
