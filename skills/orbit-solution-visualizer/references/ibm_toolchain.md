# IBM Toolchain Reference

## Tool Roles in the Pipeline

| Tool | Role | Key Output |
|------|------|------------|
| **IBM ELM DOORS Next** | Requirements governance | Baselined BR/SR hierarchy, traceability matrix, domain glossary |
| **IBM DevOps Solution Workbench** | Architecture design | C4 diagrams, domain model JSON, OpenAPI specs, scaffolded code, K8s manifests |
| **IBM Project Bob** | AI-governed code generation | Full service implementations, unit tests, CI/CD config |

---

## DOORS Next — What Goes In / What Comes Out

**Inputs** (human-authored):
- Business objectives (e.g., "Reduce WISMO calls by 40%")
- Stakeholder needs (role + need + rationale)
- Non-functional requirements (latency, security, retention)
- Regulatory constraints

**Operations inside DOORS Next**:
1. **Decompose**: Break Business Requirements (BR) into System Requirements (SR)
2. **Trace**: Link every SR → BR using OSLC links so changes propagate
3. **Baseline**: Take an immutable snapshot before architecture begins

**Outputs** (feed into Solution Workbench):
- Baselined BR/SR catalog (numbered: BR-01, SR-01.1, SR-01.2…)
- Traceability matrix (SR ↔ BR)
- Domain glossary (canonical entity names)
- Governed PDF export

**Naming convention**: `BR-{nn}` for business requirements, `SR-{nn}.{n}` for system requirements.

---

## Solution Workbench — What Goes In / What Comes Out

**Inputs** (from DOORS Next):
- Baselined SR catalog
- Domain glossary
- Jira tickets (synced from DOORS Next)

**Operations inside Solution Workbench**:
1. **C4 Context Diagram**: System + users + external systems (Level 1)
2. **C4 Container Diagram**: All deployable services with tech stack tags (Level 2)
3. **C4 Component Diagram**: Internal components of each service (Level 3)
4. **Domain Model**: JSON aggregate/entity/value-object/enum definitions
5. **OpenAPI Specs**: One YAML per service
6. **Scaffolded Code**: Stubs with `// TODO [BOB]:` markers
7. **K8s Manifests**: Deployment + Service YAML per container
8. **Decision Documents**: Architecture decision records (ADRs) with options, strengths/weaknesses, chosen solution

**Outputs** (feed into Project Bob prompt):
All of the above artifacts, packaged as the "Solution Workbench Output Bundle."

---

## Project Bob — Prompt Structure

Bob operates in 4 modes: **Architect → Plan → Code → Review**

The master prompt must include:
1. **Context block**: Project name, tech stack, architecture summary
2. **Artifacts block**: Paste or reference all Solution Workbench outputs
3. **Task list**: Numbered tasks, one per service/component
4. **Quality gates**: Coverage %, security requirements, logging standards
5. **Governance note**: Reference to DOORS Next baseline ID

---

## Node/Container Color Coding (IBM Solution Designer)

| Node Type | Header Color | Icon |
|-----------|-------------|------|
| Container | Teal `#007d79` | Service-specific |
| Use Case | Purple `#6929c4` | Diamond |
| Risk | Red `#da1e28` | Warning triangle |
| Database | Blue `#0043ce` | Cylinder |
| Message Bus | Orange `#ff832b` | Lightning bolt |

---

## IBM Carbon Design System Tokens (for web app)

```css
--ibm-blue-60: #0f62fe;      /* Primary action / active nav */
--ibm-teal-60: #007d79;      /* Container node headers */
--ibm-gray-100: #161616;     /* Header / status bar background */
--ibm-gray-10: #f4f4f4;      /* Canvas background */
--ibm-white: #ffffff;        /* Sidebar background */
--ibm-purple-60: #6929c4;    /* Use case nodes */
--ibm-red-60: #da1e28;       /* Risk nodes */
--ibm-green-40: #42be65;     /* Connected status indicator */
--ibm-yellow-30: #f1c21b;    /* Warning indicator */
```

Font: `IBM Plex Sans` (body), `IBM Plex Mono` (code, paths, tags)
Google Fonts CDN: `https://fonts.googleapis.com/css2?family=IBM+Plex+Mono&family=IBM+Plex+Sans:wght@300;400;600;700&display=swap`
