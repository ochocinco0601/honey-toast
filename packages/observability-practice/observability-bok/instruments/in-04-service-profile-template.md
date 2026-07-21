# IN-04 — Service Profile Template

**Type:** Definition

**State:** Current

**Lifecycle position:** Define

---

## Purpose

A Product Owner asks "how do I register a service for observability?" This is the starting point — the service profile is one record that establishes a service's identity, business purpose, criticality, ownership, and organizational placement. It is the root record of the business observability data model: downstream definition instruments (stakeholder expectations, signal definitions) attach to the service registered here.

## The record

One row per service. Thirteen fields:

| Field | Meaning | Required |
|-------|---------|----------|
| `service_id` | Unique identifier (e.g., SVC001) | Yes |
| `serviceName` | Technical name used in systems (e.g., treasury-order-funding-service) | Yes |
| `displayName` | Human-readable name for dashboards | Yes |
| `businessPurpose` | What the service does for the business, in plain language | Yes |
| `tierLevel` | Criticality, from 1 (most critical) to 6 (least critical) | Yes |
| `businessUnit` | Owning business organization | Yes |
| `tags` | Comma-separated categorization labels | No |
| `productOwner` | Email of the responsible Product Owner | Yes |
| `technicalOwner` | Technical owner from the application registry, distinct from the Product Owner | No |
| `org_id` | Organizational placement — key into the org hierarchy | Yes |
| `app_id` | Application identifier from the enterprise configuration management database (CMDB) | Yes |
| `created_by`, `modified_by` | Audit trail | Auto-generated |

Service identity is unique per (`serviceName`, `org_id`, `app_id`) — the same technical name can exist under two organizations without collision.

**Worked example** — a tier-1 home-lending funding service:

| Field | Value |
|-------|-------|
| `service_id` | SVC001 |
| `serviceName` | treasury-order-funding-service |
| `displayName` | Treasury Order Funding Service |
| `businessPurpose` | Execute wire transfers to complete home purchase transactions |
| `tierLevel` | 1 |
| `businessUnit` | Mortgage Lending |
| `productOwner` | sarah.chen@example.com |
| `org_id` | ORG005 |
| `app_id` | APP_0123 |

## Inputs

- Service name, business purpose, and tier (from Product Owner domain knowledge)
- Application identifier (from the enterprise CMDB or application registry)
- Organizational placement (from the org hierarchy)

## Outputs

- One completed service profile record — the root entity of the business observability data model, which downstream definition instruments reference

## KA Cross-References

| KA | Relationship |
|----|-------------|
| [KA01 — Business Context](../ka01-business-context.md) | This instrument captures [KA01.3](../ka01-business-context.md) (Service Definition) and [KA01.5](../ka01-business-context.md#service-profile-construction) (Service Profile Construction) |
| [KA08 — Data Governance](../ka08-data-governance.md) | Service registry feeds [KA08.1](../ka08-data-governance.md#service-catalog-capability-registry) (Service Catalog) |
| [KA07 — Integration & Architecture](../ka07-integration-architecture.md) | CMDB integration provides input data |

## Usage Context

**When to reach for this instrument:**

- A new service needs observability — this is step 1
- A CMDB inventory audit identifies services without observability coverage
- Organizational restructuring requires updating service-to-organization mappings

**Related instruments:**

- [IN-06 Stakeholder Expectation Template](in-06-stakeholder-expectation-template.md) — next step after service registration (who cares about this service?)
- [IN-05 Signal Definition Template](in-05-signal-definition-template.md) — defines the health signals for the registered service
- [IN-01 Service Maturity Model](in-01-service-maturity-model.md) — completing this template moves a service from Identified to beginning Contextualized
- [IN-23 Observability Standard](in-23-observability-standard.md) — the standard a service's observability is placed against; the profile created here is its root record
