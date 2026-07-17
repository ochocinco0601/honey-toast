# Perspective — Cloud-Native

**State:** Seeded

The context where the observability industry's center of gravity sits. Container platforms (Kubernetes, ECS, Cloud Run), service meshes (Istio, Linkerd), managed cloud services (AWS, GCP, Azure native monitoring), and OpenTelemetry-native instrumentation.

## What distinguishes this perspective

- **Instrumentation is widely automated.** OTel SDKs, auto-instrumentation agents, service mesh telemetry emission — signals appear without explicit developer effort for most framework code.
- **Cardinality is high by default.** Every pod, every request, every trace gets a unique identifier. Investigative observability ([KA04.6](../ka04-monitoring-visualization.md#exploratory-analysis-hypothesis-driven-investigation)) is the native operating mode.
- **Ephemerality is the rule.** Hosts come and go. Signal identity must be carried by semantic conventions ([KA02.5](../ka02-signal-design.md#semantic-conventions)), not host identity.
- **Service topology is visible.** Meshes and container platforms publish their dependency graphs; topology visualization ([KA04.4](../ka04-monitoring-visualization.md#topology-dependency-visualization)) is an emitted capability.

## KA Variations under this perspective

| KA | Variation |
|----|-----------|
| [KA02 Signal Design](../ka02-signal-design.md) | OpenTelemetry semantic conventions are the practitioner standard. Auto-instrumentation for common frameworks. Distributed tracing assumed, not exceptional. |
| [KA04 Monitoring & Visualization](../ka04-monitoring-visualization.md) | Service mesh dashboards, trace visualization, continuous steady-state monitoring. Batch-window patterns rare. |
| [KA05 Incident Response](../ka05-incident-response.md) | Pod restart, canary rollback, traffic shift, chaos engineering as steady-state discipline. |
| [KA06 Platform & Tooling](../ka06-platform-tooling.md) | CNCF ecosystem stack — Prometheus, Grafana, Tempo, Loki, Jaeger. Managed equivalents (CloudWatch, Google Cloud Monitoring, Azure Monitor). |
| [KA07 Integration & Architecture](../ka07-integration-architecture.md) | Kubernetes-native integration patterns, operators, GitOps for observability config. |

## Known gaps in this perspective

- Cost management for high-cardinality cloud telemetry — referenced in [KA06.6](../ka06-platform-tooling.md#observability-economics-cost-optimization), not yet operationalized for this perspective.
- Cross-cloud correlation when the same logical service spans multiple providers.

## Why this perspective matters

Most published observability guidance assumes this context. Naming it as a perspective keeps its assumptions visible instead of silently universalized — what auto-instrumentation, high cardinality, and ephemerality make easy here does not transfer to the other platform contexts.

## External references

- OpenTelemetry project (CNCF)
- Charity Majors (Honeycomb) on high-cardinality observability
- Ben Sigelman (LightStep/ServiceNow) on distributed tracing
