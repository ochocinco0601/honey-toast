# Source Classification for Arc42

How to assess raw source material and map it to arc42 chapters.

## Source Type Taxonomy

| Source Type | Description | Examples |
| :---------- | :---------- | :------- |
| **Product docs** | Business-level descriptions of what a system does | README, product briefs, wiki overviews, pitch decks |
| **Architecture docs** | Structural and design documentation | Existing arc42, C4 diagrams, HLD/LLD docs, Confluence architecture pages |
| **API specifications** | Interface contracts | OpenAPI/Swagger, AsyncAPI, gRPC proto files, WSDL |
| **Code repositories** | Source code and its structure | Service repos, monorepo modules, package layout |
| **ADRs** | Architecture Decision Records | Markdown ADRs, decision logs, RFC documents |
| **Config/IaC** | Deployment and infrastructure definitions | Dockerfile, Kubernetes manifests, Terraform, CI/CD pipelines, env files |
| **Runbooks** | Operational procedures | Incident response docs, escalation guides, on-call handbooks |
| **Monitoring configs** | Existing observability setup | Alert rules, dashboard JSON, SLO definitions, logging configs |
| **Transcripts** | Conversations containing domain knowledge | Call recordings, meeting notes, Slack threads, interview notes |
| **Diagrams** | Visual representations | Architecture diagrams, sequence diagrams, network diagrams, data flow diagrams |
| **Compliance/governance** | Regulatory and organizational mandates | Security policies, compliance checklists, governance frameworks |
| **Incident reports** | Past failure documentation | Post-mortems, RCA documents, incident timelines |

## Source-to-Chapter Mapping Matrix

Which source types typically feed which arc42 chapters. **P** = primary source, **S** = secondary/supporting.

| Source Type | Ch1 Goals | Ch2 Constraints | Ch3 Context | Ch4 Strategy | Ch5 Blocks | Ch6 Runtime | Ch7 Deploy | Ch8 Concepts | Ch9 Decisions | Ch10 Quality | Ch11 Risks | Ch12 Glossary |
| :---------- | :-------: | :--------------: | :---------: | :----------: | :--------: | :---------: | :--------: | :----------: | :-----------: | :----------: | :--------: | :-----------: |
| Product docs | **P** | | S | S | | | | | | S | | **P** |
| Architecture docs | S | S | **P** | **P** | **P** | **P** | S | **P** | S | S | S | S |
| API specs | | | **P** | | S | S | | | | | | S |
| Code repos | | | S | | **P** | S | S | **P** | | | | |
| ADRs | | S | | **P** | | | | S | **P** | S | | |
| Config/IaC | | S | | | S | | **P** | S | | | | |
| Runbooks | | | | | | S | S | | | | **P** | S |
| Monitoring configs | | | | | | | S | S | | **P** | S | |
| Transcripts | **P** | S | S | S | | | | | S | S | S | **P** |
| Diagrams | | | **P** | S | **P** | **P** | **P** | | | | | |
| Compliance/gov | | **P** | | | | | | S | S | S | S | |
| Incident reports | | | | | | S | | | | | **P** | |

## Coverage Assessment

For each source, assess which chapters it can inform:

```
SOURCE COVERAGE MATRIX
┌─────────────────────────────────────────────────────────────────────────┐
│ Source   │ Ch1 │ Ch2 │ Ch3 │ Ch4 │ Ch5 │ Ch6 │ Ch7 │ Ch8 │ ... │ Ch12│
│ S1: ...  │  P  │     │  S  │     │  P  │  S  │     │     │     │     │
│ S2: ...  │     │  P  │     │  S  │     │     │     │     │     │     │
│ S3: ...  │  S  │     │  P  │     │     │  P  │     │     │     │     │
│ Coverage │ 2   │ 1   │ 2   │ 1   │ 1   │ 2   │ 0   │ 0   │     │ 0   │
└─────────────────────────────────────────────────────────────────────────┘
```

After mapping all sources:
- **Rich** (2+ primary sources): produce full chapter content
- **Thin** (1 source or secondary only): produce minimum viable version
- **Gap** (no sources): produce skeleton with gap statements

## Gap Identification

Chapters with zero coverage get explicit gap statements, not fabricated content. A gap statement names:
1. What information is missing
2. What source type would fill it
3. How critical the gap is for downstream consumers

Example:
> **Gap:** No source material for deployment view. To fill this chapter, provide Docker/Kubernetes configs, deployment diagrams, or IaC files.

## The Honest Gap Principle

Three levels of content honesty:
- **Extracted:** directly stated in a source. Cite with `[S1: section/line]`.
- **Inferred:** reasoned from multiple sources. State the reasoning chain and cite the sources that support it.
- **Gap:** no source material exists. Say so explicitly. Never fabricate plausible-sounding content to fill structural slots.

An arc42 document with honest gaps is more valuable than one with plausible hallucinations. Gaps are actionable (the user knows what to provide next). Hallucinations are dangerous (they look like facts).
