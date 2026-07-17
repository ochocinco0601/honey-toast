# Observability Capability Gap — Dependency & Internal Error Alerting

**What this is:** where Splunk Observability Cloud serves as an organization's shared observability platform, it cannot alert on a class of errors that the observability standard treats as required. This names the gap, grounds why it's a required capability rather than a preference, and states the need. It does not prescribe the fix, the cost, or the roadmap — those belong to the platform's owner.

---

## The gap

Splunk Observability Cloud computes its alertable metrics only from inbound work. Errors that occur on **outbound dependency calls (databases, HTTP), message producers (Kafka), and internal operations** are captured in individual traces but are **excluded from the metrics that drive dashboards and alerts**. A service can therefore read green while those paths are actively erroring.

This is documented behavior of the platform's metric model — verified against Splunk's own product documentation (cited below), not a local misconfiguration. Where Splunk is run as a single shared platform, the gap is not one team's — **every team that relies on it inherits it.**

## Why it's a required capability, not a preference

**Errors is a canonical Application-layer signal** — one of the Four Golden Signals (Google SRE) and the "E" in the RED method for request-driven services. Dependency and internal errors are Application-layer errors. A platform that cannot alert on them cannot compute a canonical signal for those paths, leaving a required position in the standard that can't be filled.

For business observability the need is sharper: knowing *which* dependency or transaction failed is how a business-health breach is traced down to its mechanism. Without dependency-level error visibility, that chain can't be walked.

## The standard it fails

The observability standard's computation rule is explicit: status is computed from each layer's own signals, and **"a green that no signal computes is not a green."** A platform that renders green on a path where errors are occurring but no signal counts them produces exactly that — a green nothing computed. It does not meet the bar for those paths.

## Where it lands in real work

A service whose database or producer path is throwing errors reads green on the surface teams use to decide whether to act. The error sits in the trace; nothing on the alerting surface reflects it. This is the computation rule failing in practice — a green the standard says is not a real green — made structural rather than incidental.

## What an observability practice can say — and what it can't

An observability practice's job here is to name the gap against the standard and state the need: **Splunk needs to alert on dependency, producer, and internal errors** to meet the bar it is measured against.

How that is closed — configuration, a different capability, at whatever cost, on whatever timeline — belongs to the platform's owner. This articulation does not prescribe it.

---

## Sources

- **Splunk — Monitoring MetricSets** (the load-bearing claim): Monitoring MetricSets, which power dashboards and alerts, are created only for spans with `span.kind` of `SERVER` or `CONSUMER` — so `CLIENT`, `PRODUCER`, and `INTERNAL` spans are excluded. → https://help.splunk.com/en/splunk-observability-cloud/monitor-application-performance/analyze-services-with-span-tags-and-metricsets/learn-about-monitoring-metricsets
- **Splunk — MetricSets in APM** (overview of the two MetricSet types): https://docs.splunk.com/observability/en/apm/span-tags/metricsets.html
- **Splunk — Index span tags → Troubleshooting MetricSets** (the supported path to add coverage, at a cardinality cost): https://docs.splunk.com/observability/en/apm/span-tags/index-span-tags.html
- **Observability standard** ([IN-23](observability-practice/observability-bok/instruments/in-23-observability-standard.md)): canonical signal sets per layer; the computation rule ("a green that no signal computes is not a green").
