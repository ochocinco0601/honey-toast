# About This BOK

**Current working version.** Opinionated starting point for organizing observability as a professional domain. Not canonical. Not finished. (Structure and vocabulary: [How the BOK is Organized](how-the-bok-is-organized.md) · start point: [the hub](README.md).)

## Why it exists

Observability work sprawls — monitoring, incident response, SLOs, platform tooling, adoption, governance. No single framework covers it. This BOK adopts structure from established prior art and applies it to the domain.

## What's opinionated

- **The lifecycle spine.** Core Practice runs *Define → Implement → Enforce → Observe → Respond.* Business context scopes everything downstream.
- **Three categories.** Core Practice (the lifecycle), Enabling Practice (cross-cutting infrastructure), Management Practice (organizational). Adapted from ITIL's practice-category idea; the semantics are this BOK's own.
- **Practice Instruments as peers.** Templates, assessments, factories, protocols get their own catalog — they draw from multiple KAs. Following BABOK Techniques Chapter.
- **Perspectives as a third peer.** Platform-type and context-type variation (cloud-native, mainframe, hybrid, SaaS, agentic) is a lens that bends KA and Instrument application, not a set of KAs. Following BABOK Perspectives Chapter.
- **Content states visible.** Every topic tagged Current / Seeded / Missing. Honest about what's filled in.

## Prior art

| Dimension | Adopted from |
|---|---|
| Three-peer structure | BABOK v3 (KA + Technique + Perspective composition) |
| Lifecycle spine | ITIL service-lifecycle thinking (v3) + SRE operational loop, adapted to a 5-stage observability sequence |
| Three-category KA split | Adapted from ITIL's practice-category idea; the Core/Enabling/Management semantics are this BOK's own |
| KA → Topic structure | SWEBOK, PMBOK, DMBOK |
| 7-section page pattern | Inspired by ITIL practice-guide structure; the seven sections are this BOK's own |
| Every-page-is-page-one | Mark Baker (XML Press, 2013) |
| Structured writing | Robert Horn, Information Mapping (IEEE 1993) |
| Documentation type discipline | Daniele Procida, Diataxis |
| Practice Instruments catalog | BABOK Techniques Chapter |
| Perspectives catalog | BABOK Perspectives Chapter |
| Content state audit | Halvorson, *Content Strategy for the Web* |
| Audience-altitude framing (the same content pitched per organizational level) | This BOK's own framing, drawing on Hoshin Kanri's nested planning levels |
| Four-Layer Model (Business Health / Business Impact / Application / System) | ArchiMate structural layers (Business / Application / Technology) plus a Business Impact layer added on top; per-layer signal dimensions from Google SRE / Wilkie (Golden Signals / RED), Brendan Gregg (USE), APQC Process Performance |
| Observability domain content | Google SRE, Charity Majors / Ben Sigelman, OpenTelemetry |

## Who it's for

- **Practitioners** locating concepts and finding tools
- **Program / strategy** deciding where to invest

Leaders typically read one-pagers produced *from* the BOK, not the BOK itself. The markdown + YAML structure is also machine-readable — AI assistants can ground questions against the BOK programmatically, a secondary benefit of the form.

## What's next

Iteration. The BOK improves when real work produces contributions that land in KA pages (Current) or queue for validation (Seeded). Structural revisions happen when accumulated contributions don't fit the taxonomy — that's a signal, not a failure.
