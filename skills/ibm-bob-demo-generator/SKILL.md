---
name: ibm-bob-demo-generator
description: A framework for generating "WOW-First" 5-minute leave-behind demo videos using IBM Project Bob. It pulls validated small-to-mid-sized app ideas from Reddit, builds a working PostgreSQL-backed prototype, and structures a demo script that starts with the final working app and works backwards to the prompt. Use when a user asks to create a client engagement demo, a leave-behind video, or a quick IBM Bob showcase for a prospect or customer.
---

# IBM Bob "WOW-First" Demo Generator

## Purpose

This skill is an **Operational Design Engine (ODE)** for IBM sellers, technical sellers, and client engineering teams. It produces a complete, repeatable, 5-minute leave-behind demo video package — from idea sourcing to working code to a polished demo script — using IBM Project Bob as the hero.

The output is designed to be recorded and left with a client after a discovery call or proof-of-concept engagement. It answers the question every client has but rarely asks aloud: *"Can IBM Bob actually build something real, for a problem I recognize, in a time frame I can believe?"*

The answer is yes. This skill proves it.

---

## Core Philosophy: The "WOW-First" Principle

Most developer demos are structured chronologically: blank screen → prompt → wait → result. This is the wrong order for a sales or engagement context. By the time the result appears, the audience has mentally checked out.

**The WOW-First Principle inverts the sequence:**

| Step | What Happens | Why It Works |
|------|-------------|--------------|
| 1. **Start with the WOW** | Show the fully working, polished application immediately | Captures attention before the audience can disengage |
| 2. **Demonstrate the value** | Walk through the app solving the exact pain point | Creates emotional connection to the problem being solved |
| 3. **Reveal the origin** | Transition to IBM Project Bob and show the prompt | Delivers the "how did you build this so fast?" moment |
| 4. **Prove the enterprise foundation** | Show the generated PostgreSQL schema and backend code | Converts skeptics by proving it is production-grade, not a toy |
| 5. **Issue the challenge** | Ask the client to imagine Bob solving their problem | Ends with forward momentum, not a product pitch |

This structure borrows from the best practices of magic and storytelling: show the impossible result first, then explain how it was done. The explanation becomes a source of wonder rather than a source of impatience.

---

## Workflow

When a user requests a demo or leave-behind video, execute the following phases in order. Read the archetype library at `references/app_archetypes.md` before selecting an idea.

---

### Phase 1 — Idea Sourcing (The Reddit Signal Method)

Do not invent generic demo apps. Source ideas from real, validated complaints on Reddit. The goal is to find a problem that a client's CTO, VP of Engineering, or line-of-business owner will immediately recognize and feel.

**Target subreddits for signal mining:**
- `r/AppIdeas` — direct requests for apps that don't exist
- `r/Entrepreneur` — small business workflow pain points
- `r/smallbusiness` — operational frustrations from real operators
- `r/SideProject` — validated ideas that indie developers are already building
- `r/SomebodyMakeThis` — unmet needs stated plainly

**Scoring criteria for idea selection:**

| Criterion | What to Look For | Weight |
|-----------|-----------------|--------|
| **Specificity** | The problem is concrete, not vague ("I need a way to track which tenant submitted which maintenance request" vs. "I need a better CRM") | High |
| **Audience size** | The target user is a recognizable, sizeable group (tradespeople, small landlords, pet owners, HR coordinators) | High |
| **Database fit** | The problem requires storing relational data (users, records, history, relationships) — this is where PostgreSQL shines | High |
| **Demo-ability** | The core value can be shown in under 90 seconds of screen time | Medium |
| **Existing gap** | Current solutions are either too expensive, too complex, or built for a different audience | Medium |

**The Winning Pattern:** The best demo ideas follow this formula: *"A [specific role] needs to [specific action] but every existing tool was built for [a different, larger audience]. So they're doing it with [a painful workaround like spreadsheets, text messages, or prayer]."*

---

### Phase 2 — The IBM Project Bob Master Prompt

Once the idea is selected, craft the Master Prompt for IBM Project Bob. This is the single most important artifact in the demo — it is the "magic spell" that the audience will see on screen.

**The Master Prompt must:**
1. Open with the problem context in plain language (1-2 sentences).
2. Name the target user explicitly.
3. Specify the full tech stack: React or Next.js frontend, Node.js/Express backend, PostgreSQL database.
4. Define the core database entities and their relationships.
5. Describe the primary UI screens and the most important user action.
6. Include at least one enterprise-grade requirement (authentication, audit logging, role-based access, or data validation).

**Master Prompt Template:**

```
Build a [App Name] for [Target User].

Problem: [1-2 sentence description of the pain point, sourced from Reddit].

Tech Stack:
- Frontend: React with Tailwind CSS
- Backend: Node.js with Express
- Database: PostgreSQL

Database Schema:
- [Entity 1]: [fields and relationships]
- [Entity 2]: [fields and relationships]
- [Entity 3]: [fields and relationships]

Core Features:
1. [Primary feature — the WOW]
2. [Secondary feature — supporting the WOW]
3. [Enterprise feature — authentication, logging, or validation]

UI Requirements:
- Clean, minimal dashboard as the home screen
- [Specific UI requirement for the primary feature]
- Mobile-responsive layout

The application must be production-ready with input validation, error handling, and structured JSON logging on all API endpoints.
```

---

### Phase 3 — Application Artifact Generation

After crafting the Master Prompt, generate the core application artifacts that IBM Project Bob would produce. These are used in the demo's "Enterprise Proof" segment.

**Required artifacts:**

| Artifact | File | Purpose in Demo |
|----------|------|----------------|
| PostgreSQL Schema | `schema.sql` | Shows relational data design — proves this is enterprise-grade |
| Backend API | `server.js` | Shows clean, structured code with proper routes and DB queries |
| Frontend Component | `App.jsx` | Shows the UI that the client saw in the WOW segment |
| `.bob` instructions | `AGENTS.md` | Shows the Bob-specific configuration that guided the build |

When generating the PostgreSQL schema, follow these rules:
- Use `SERIAL PRIMARY KEY` for all ID columns.
- Include `created_at TIMESTAMP DEFAULT NOW()` on all tables.
- Define foreign key constraints explicitly.
- Add at least one index on a frequently queried column.
- Include a `status` column (as an ENUM or VARCHAR with a CHECK constraint) on any entity that has a lifecycle.

---

### Phase 4 — Demo Script & Storyboard

Create the 5-minute demo script using the WOW-First structure. Read the template at `templates/demo_ode_template.md` and populate it with the specific app content.

**Timing discipline is critical.** The demo must fit in exactly 5 minutes. A leave-behind video that runs 7 minutes loses 40% of its audience before the call to action.

| Segment | Time | Content |
|---------|------|---------|
| **The Hook** | 0:00 – 0:30 | State the Reddit-sourced problem. Quote a real post if possible. |
| **The WOW** | 0:30 – 2:00 | Live demo of the working app. Show the primary feature solving the problem. |
| **The Reveal** | 2:00 – 3:30 | Open IBM Project Bob. Show the Master Prompt. Scroll through it slowly. |
| **The Enterprise Proof** | 3:30 – 4:30 | Show `schema.sql` in the IDE. Show one API route. Mention PostgreSQL by name. |
| **The Call to Action** | 4:30 – 5:00 | Ask the client a forward-looking question. End on a challenge, not a pitch. |

**The Call to Action must be a question, not a statement.** For example: *"If Bob can build a validated app for a plumber's scheduling problem in minutes, what would you ask it to build for your team?"* This is far more powerful than "Contact your IBM representative to learn more."

---

### Phase 5 — Document Compilation & Delivery

Compile all artifacts into a single Markdown document using the template at `templates/demo_ode_template.md`. The document serves as both the leave-behind reference and the internal playbook for the demo recording session.

**Final deliverables:**
1. **The ODE Document** (`[app-name]-demo-ode.md`) — The complete package: concept, prompt, code, and script.
2. **The Master Prompt** (standalone, copy-paste ready) — For the presenter to use live in the recording.
3. **The Schema File** (`schema.sql`) — For the Enterprise Proof segment.
4. **The Recording Checklist** (`recording_checklist.md`) — Step-by-step instructions for recording the leave-behind video.

---

## The App Archetype Library

The following archetypes are pre-validated patterns sourced from Reddit signal mining. Each represents a real, recurring complaint from a specific audience. Read `references/app_archetypes.md` for the full library.

| Archetype | Target User | Core Pain | PostgreSQL Complexity | Demo Impact |
|-----------|------------|-----------|----------------------|-------------|
| **Micro-Landlord Portal** | Landlords with 1-5 units | Maintenance requests managed via text messages | Tenants, properties, tickets, status history | High — every client has managed a property or knows someone who has |
| **Tradesperson Scheduler** | Plumbers, electricians, HVAC techs | Scheduling tools built for office workers, not field workers | Jobs, service areas, time blocks, customer bookings | High — immediately relatable, obvious gap in the market |
| **SaaS Price Sentinel** | Startup operators, SMB finance teams | Silent price increases on subscription tools | Subscriptions, price history, alert rules, notifications | High — every company has this problem right now |
| **Meeting Action Extractor** | Team leads, project managers | Transcription tools produce walls of text, not action items | Meetings, participants, action items, owners, due dates | Medium — well-known problem, but several competitors exist |
| **Pet Medication Tracker** | Pet owners with animals on multiple medications | Human health apps don't adapt to veterinary use cases | Pets, medications, dosage schedules, administration logs | Medium — niche but deeply emotional |
| **Field Inspection Logger** | Construction site supervisors, safety officers | Paper forms and photo dumps with no structured data | Sites, inspections, findings, photos, remediation status | Very High — enterprise clients immediately see the B2B application |
| **Small Clinic Waitlist** | Independent medical or dental practices | No affordable waitlist and appointment management tool | Patients, appointments, waitlist queue, provider schedules | High — every client has experienced a bad waiting room |
| **Contractor Invoice Tracker** | Freelancers and independent contractors | Invoices tracked in spreadsheets, late payments missed | Clients, projects, invoices, line items, payment status | High — universally relatable, immediate emotional resonance |

---

## References

Read the following files for supporting detail before executing this skill:

- `references/app_archetypes.md` — Full archetype library with Reddit source threads, Master Prompts, and schema starters.
- `references/wow_first_theory.md` — The psychological and sales theory behind the WOW-First approach.
- `templates/demo_ode_template.md` — The ODE document template to populate for each demo.
- `templates/recording_checklist.md` — Step-by-step checklist for recording the leave-behind video.

---

## Quality Standards

- **The app must be real.** Do not generate a mockup or a wireframe. The demo shows a working application with real data in a real PostgreSQL database. If it cannot be built, choose a different archetype.
- **The prompt must be honest.** The Master Prompt shown in the demo must be the actual prompt used to generate the application. Do not simplify it for the camera.
- **The problem must be sourced.** Every demo must cite a real Reddit thread or community complaint. This is the credibility anchor that separates this demo from a generic product pitch.
- **The timing must be respected.** Five minutes is a constraint, not a suggestion. A leave-behind video that respects the viewer's time is more likely to be shared internally by the client.
- **IBM Bob is the hero.** The presenter is a guide. The client is the protagonist. IBM Project Bob is the tool that makes the impossible possible. Every sentence in the script should reinforce this hierarchy.
