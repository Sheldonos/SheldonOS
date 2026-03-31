---
name: ibm-solution-architect-web
description: End-to-end workflow for discovering a company use case, generating IBM DevOps Solution Workbench architecture artifacts (C4 diagrams, domain models, OpenAPI specs, scaffolded code), producing a master IBM Project Bob prompt, and deploying a live interactive IBM Solution Designer web app replica that visualizes the full architecture. Use when a user asks to build an IBM Solution Designer output, map architecture for a company use case using IBM tools, or generate a Solution Workbench + Project Bob package with a live web visualization.
---

# IBM Solution Architect Web

This skill produces two deliverables from a company name and use case:
1. **The IBM Toolchain Package** — DOORS Next requirements, Solution Workbench artifacts (C4 diagrams, OpenAPI specs, domain model, ADRs, scaffolded code), and a master Project Bob prompt.
2. **The Live Web App** — An interactive IBM Solution Designer replica deployed as a website, showing the full architecture with clickable nodes, drill-down diagrams, API explorer, decision documents, and domain method views.

Read `references/ibm_toolchain.md` for IBM tool details and Carbon Design System tokens.
Read `references/webapp_architecture.md` for the exact component structure, data models, and layout rules for the web app.

---

## Workflow

### Phase 1 — Discover the Use Case

Research the company and use case:
- Company business model, industry, and scale
- The specific problem the use case solves
- Key users/actors (e.g., logistics managers, customers, developers)
- External systems that must integrate (APIs, portals, legacy systems)
- Non-functional requirements (latency, security, compliance)

Identify and name:
- **8–12 containers** (deployable services): always include a frontend dashboard, API gateway, 1–2 core processing services, an event bus (Kafka), at least one database, and a notification service
- **2–3 use case nodes** (user stories in "As a [role], I want to..." format)
- **1–2 risk nodes** (functional risks specific to the domain)
- **4–6 external systems** (third-party APIs, legacy platforms)

---

### Phase 2 — Generate DOORS Next Requirements

Produce a baselined requirements catalog:

**Business Requirements (BR)** — 5–8 items, format:
```
BR-01: [Action verb] [measurable outcome]
       Rationale: [why this matters to the business]
       Source: [stakeholder role]
```

**System Requirements (SR)** — 2–3 per BR, format:
```
SR-01.1: The system SHALL [specific technical behavior]
         Traces to: BR-01
         Priority: Must Have | Should Have | Nice to Have
```

Include a **traceability matrix** table: SR rows × BR columns, mark with ✓.

Include a **domain glossary**: canonical entity names that will become the domain model (e.g., `Shipment`, `TrackingEvent`, `Carrier`).

---

### Phase 3 — Generate Solution Workbench Artifacts

Produce all artifacts in a single document. Read `references/ibm_toolchain.md` for the exact output format of each artifact.

**Artifacts to produce:**

| # | Artifact | Format |
|---|----------|--------|
| 1 | C4 Context Diagram | Mermaid `graph LR`, render to PNG with `sheldon-render-diagram` |
| 2 | C4 Container Diagram | Mermaid `graph TB`, render to PNG |
| 3 | C4 Component Diagram | Mermaid `graph TB` for the most complex service |
| 4 | Domain Model | JSON with aggregates, entities, value objects, enums, domain events |
| 5 | OpenAPI Spec (Service 1) | Full YAML, OpenAPI 3.0 |
| 6 | OpenAPI Spec (Service 2) | Full YAML, OpenAPI 3.0 |
| 7 | Scaffolded Code (Service 1) | Node.js/Express stub with `// TODO [BOB]:` markers |
| 8 | Scaffolded Code (Service 2) | Java/Spring Boot stub with `// TODO [BOB]:` markers |
| 9 | K8s Manifest | Deployment + Service YAML for core service |
| 10 | Decision Document (ADR) | Title, Context, Options (strengths/weaknesses), Decision, Implementation Hints |

Run `scripts/generate_architecture_data.py` to produce the JSON data file for the web app:
```bash
python3 skills/ibm-solution-architect-web/scripts/generate_architecture_data.py \
  --company "[Company]" \
  --use-case "[Use Case]" \
  --services "[comma-separated container names]" \
  --external "[comma-separated external systems]" \
  --output architecture_data.json
```

---

### Phase 4 — Write the Master Project Bob Prompt

Structure the prompt in exactly this format:

```
## IBM Project Bob — Master Prompt
### Project: [Use Case Name] — [Company]

**Context**
[2–3 sentences: what the system does, who uses it, tech stack summary]

**Architecture Summary**
[Paste or summarize the C4 Container diagram]

**Artifacts Provided**
- Domain Model JSON (attached)
- OpenAPI Spec: [Service 1] (attached)
- OpenAPI Spec: [Service 2] (attached)
- Scaffolded code stubs (attached)
- K8s manifests (attached)
- DOORS Next Baseline ID: [BL-001]

**Tasks**

Task 1: [Service Name] — [Component Name]
File: [path/to/file.js]
Implement: [specific function/class]
Requirements: [SR-nn.n, SR-nn.n]
Acceptance: [measurable criteria]

[Repeat for each task — typically 6–8 tasks]

**Quality Gates**
- Unit test coverage: ≥ 80%
- No hardcoded secrets — use IBM Secrets Manager
- All endpoints must validate input with schema
- Structured JSON logging on all services
- HMAC-SHA256 signature verification on all webhook endpoints

**Governance**
This implementation must remain traceable to DOORS Next Baseline BL-001.
Do not alter business logic without a corresponding requirement change.
```

---

### Phase 5 — Build and Deploy the Web App

Initialize the web project:
```
webdev_init_project → project name: "[company-slug]-solution-designer"
```

After init, write the brainstorm file (`ideas.md`) then immediately commit to the IBM Carbon Design System aesthetic:
- Dark header (`#161616`), white sidebar, light gray canvas (`#f4f4f4`)
- Teal node headers (`#007d79`), IBM Blue active states (`#0f62fe`)
- IBM Plex Sans + IBM Plex Mono fonts (add via Google Fonts CDN in `index.html`)

**Component build order** (build each file completely before moving to the next):

1. `client/src/index.css` — Carbon Design System CSS variables
2. `client/index.html` — Add IBM Plex Sans + Mono Google Fonts link
3. `client/src/components/ContainerDiagram.tsx` — SVG canvas, node cards, bezier edges, minimap, right detail panel with tabs
4. `client/src/components/ComponentDiagram.tsx` — Level 3 drill-down view
5. `client/src/components/ServiceOverview.tsx` — Service list + sequence diagrams + metadata sidebar
6. `client/src/components/DecisionView.tsx` — ADR document viewer
7. `client/src/components/DomainView.tsx` — Domain method sequence diagrams
8. `client/src/components/ApiView.tsx` — OpenAPI endpoint explorer
9. `client/src/pages/Home.tsx` — Shell using template at `templates/AppShell.tsx.template`; inject `architecture_data.json` as the `ARCHITECTURE_DATA` constant

Populate each component with the **actual use case data** from Phases 1–4. Do not use placeholder lorem ipsum content.

Read `references/webapp_architecture.md` for exact node data models, edge rendering, panel structure, and CSS rules before writing any component.

After all components are built, restart the dev server and save a checkpoint.

---

### Phase 6 — Deliver

Deliver four attachments:
1. **Solution Workbench Output PDF** — all Phase 3 artifacts compiled with `sheldon-md-to-pdf`
2. **Project Bob Master Prompt** — the Phase 4 document as Markdown
3. **DOORS Next Requirements Catalog** — the Phase 2 document as Markdown
4. **Live Web App** — `sheldon-webdev://[checkpoint-id]`

---

## Key Rules

- All node labels, descriptions, tech stacks, and edge labels must reflect the **actual use case** — never use generic placeholders.
- The web app must show at minimum: Container Diagram, Component Diagram (drill-down), and Decisions view.
- Every container node must have a right-panel detail view with at least one linked Decision (ADR).
- The status bar must always show "Connected" (green dot) — this signals the app is live.
- Do not use rounded corners (`border-radius > 2px`) on any panel, card, or button — IBM Carbon uses sharp edges.
- Do not use box shadows on node cards — use `border: 1px solid #c6c6c6` only.
