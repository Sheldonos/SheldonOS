# Web App Architecture Reference

This reference describes the exact component structure and data model used to build the IBM Solution Designer replica web app. Use it when implementing the web app phase of the skill.

---

## App Shell Structure

```
Home.tsx (shell)
├── Header (dark, 48px, IBM logo + project name + branch selector + user avatar)
├── Sidebar (white, 160px, icon+label nav items)
├── Main (flex-1, renders active view)
└── StatusBar (dark, 24px, Connected indicator + Problems count + CLI label)
```

**Nav items** (in order, matching IBM Solution Designer):
`Overview → APIs → Domains → Integrations → Diagrams → Model eleme... → Spotlight → Relationships → Decisions → CI/CD`

Active nav: `border-left: 3px solid #0f62fe`, `background: #e8f0fe`, `color: #0f62fe`

---

## Views and Their Components

| Nav Item | Component | Description |
|----------|-----------|-------------|
| Diagrams | `ContainerDiagram.tsx` | SVG canvas with draggable node cards, bezier connectors, minimap, zoom controls, right detail panel |
| Model eleme... | `ComponentDiagram.tsx` | Level 3 drill-down into a single service's internal components |
| Overview | `ServiceOverview.tsx` | Service list on left, sequence diagram + metadata sidebar on right |
| Decisions | `DecisionView.tsx` | Decision list on left, full ADR document on right |
| Domains | `DomainView.tsx` | Method list on left, sequence diagram + description on right |
| APIs | `ApiView.tsx` | API list + endpoint list on left, full endpoint detail on right |

---

## ContainerDiagram — Node Data Model

```typescript
interface NodeData {
  id: string;
  type: "container" | "usecase" | "risk" | "external";
  label: string;
  description: string;
  tech?: string[];        // e.g. ["Node.js", "k8s"]
  x: number;             // canvas position (px)
  y: number;
  width: number;
  height: number;
}

interface EdgeData {
  from: string;          // node id
  to: string;
  label: string;         // relationship description
  style?: "solid" | "dashed";
}
```

**Node card anatomy** (matches IBM Solution Designer exactly):
```
┌─────────────────────────────┐  ← border: 1px solid #c6c6c6
│ CONTAINER          [label]  │  ← teal top border 3px, type badge
│ ● Service Name              │  ← icon + bold name
│ Short description text      │  ← 12px gray
│ [Tech] [Stack]              │  ← tag pills, bg #e0e0e0
└─────────────────────────────┘
  ■ ─────────────────────── ■   ← 4 selection handles when selected
```

---

## Right Detail Panel — Tab Structure

When a node is selected, show a right panel (280px wide):
```
Panel Header: node type badge + node name + close button
Tabs: Details | Usages | Relationships | Loop
```

**Details tab content**:
- General Information table: Type, Name, Stack, Status, Created by, Created on, Tags, Description
- Decisions section: linked ADR cards with Summary, Status badge (Approved/Proposed), "Open in new tab" link

---

## Sequence Diagram Rendering

Render sequence diagrams as pure HTML/CSS tables (no external libraries):

```
Participants: horizontal headers in a row
Messages: arrows rendered as divs with border-bottom + arrow pseudo-element
Return messages: dashed border-bottom
Lifelines: vertical dashed borders between participants
```

Column width: `120px` per participant. Arrow label: `font-size: 11px`, positioned above the arrow line.

---

## Canvas Connectors (SVG)

Use SVG `<path>` elements with cubic bezier curves:
```
d="M {fromX} {fromY} C {fromX+80} {fromY}, {toX-80} {toY}, {toX} {toY}"
stroke="#8d8d8d" stroke-width="1.5" fill="none"
```

For dashed connectors (use case → container): add `stroke-dasharray="5,4"`

Label: `<text>` element at midpoint, `font-size: 11px`, `fill: #525252`

---

## Minimap

Position: `bottom: 16px, left: 16px`, `160×100px`, `z-index: 20`
Render scaled-down versions of all nodes as colored rectangles.
Color by type: container=teal, usecase=purple, risk=red, database=blue.

---

## Key Layout Rules

- Canvas background: `#f4f4f4` (IBM Gray 10)
- Canvas is scrollable/pannable — wrap in `overflow: auto` container
- Node cards use `position: absolute` within a relative canvas div
- Right panel slides in from right — use `position: absolute, right: 0, top: 0, height: 100%`
- All font sizes: header labels 13px, node names 13px bold, descriptions 12px, tech tags 10px
- No rounded corners on panels or cards (IBM Carbon uses 0 or 2px radius only)
- No box shadows on node cards — use border only
