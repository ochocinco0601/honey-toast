# Perspective — Mainframe

**State:** Seeded

The context the observability industry's mainstream literature rarely addresses directly. z/OS environments (including multi-system Parallel Sysplex configurations), CICS/IMS transaction monitors, batch-processing workloads, SMF (System Management Facilities) and RMF (Resource Measurement Facility) record feeds, and the specific observability techniques these require.

## What distinguishes this perspective

- **Telemetry is record-based, not stream-based.** SMF records, RMF data, job logs — structured records emitted by the platform itself, captured on time or completion boundaries rather than continuously.
- **Workloads are often batch-oriented.** Observability rhythm follows batch windows. "Successful completion by time X" is a first-class concern; continuous-availability signals are less meaningful than window-completion signals.
- **Transaction monitors provide their own observability.** CICS, IMS, and similar monitors emit counters and exceptions through their own channels, not through OTel-style exporters.
- **Cardinality is bounded differently.** Few hosts, many transactions. The investigative patterns are different — drilling through transaction IDs and job steps, not through pod names and trace IDs.

## KA Variations under this perspective

| KA | Variation |
|----|-----------|
| [KA02 Signal Design](../ka02-signal-design.md) | Signals sourced from SMF/RMF records, transaction-monitor counters, batch-job completion events. Semantic conventions differ from OTel — system-defined field names carry meaning. |
| [KA04 Monitoring & Visualization](../ka04-monitoring-visualization.md) | Dashboard rhythm follows batch windows. Transaction volume / success rate / elapsed time. Queue depth on transaction managers. |
| [KA05 Incident Response](../ka05-incident-response.md) | Checkpoint/restart, batch re-run procedures, transaction queue drain. Recovery through workload rerouting, not pod restart. |
| [KA06 Platform & Tooling](../ka06-platform-tooling.md) | Splunk ITSI, BMC, IBM Z-native observability tools. Feed-based ingestion, not scrape-based. |
| [KA07 Integration & Architecture](../ka07-integration-architecture.md) | Mainframe configuration-management (CMDB) integration, scheduler integration (Control-M, TWS/Autosys bridges), enterprise console federation. |

## Known gaps in this perspective

- Cross-reference between mainframe business-service definitions and cloud business-service definitions during migration periods.
- Emitting correlation-ready records for unified cross-platform correlation — the seam itself is the [Hybrid / Integration perspective](hybrid-integration.md)'s territory; the mainframe-side gap is the record emission.

## External references

- IBM z/OS documentation — SMF (System Management Facilities) and RMF (Resource Measurement Facility) references
- SHARE community — the practitioner body for enterprise mainframe operations
- Vendor mainframe-observability integrations (e.g., Splunk ITSI for z/OS, BMC AMI Ops)

## Why this perspective matters

The mainframe perspective is not legacy context — it is live, regulated, business-critical production for many financial institutions. Observability practice that addresses cloud-native well but treats mainframe as an afterthought produces unusable guidance for the teams running the most critical workloads.
