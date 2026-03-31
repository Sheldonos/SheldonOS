---
name: enterprise-sales-playbook
description: A strategic framework for executing complex enterprise sales cycles, from initial account intelligence to value proposition design and C-level proposal delivery. Use for developing account penetration strategies, building strategic customer presentations, and managing multi-stakeholder sales campaigns.
---

# Enterprise Sales Playbook

This skill provides a systematic, repeatable playbook for navigating complex, high-value enterprise sales cycles. It integrates deep account intelligence with a value-centric, consultative sales methodology reverse-engineered from proven enterprise technology sales frameworks.

## Core Philosophy

The methodology is built on a single core principle: **map your solution directly to the customer's quantified pain and strategic objectives.** We don't sell products; we sell measurable business outcomes. This playbook operationalizes that philosophy.

## The Five Phases of the Enterprise Sale

The playbook is structured into five distinct phases, moving from broad intelligence gathering to a specific, actionable proposal.

1.  **Phase 1: Account Intelligence & Qualification:** Identify and deeply understand the target account.
2.  **Phase 2: Strategic Opportunity Analysis:** Map the account's challenges and goals to your capabilities.
3.  **Phase 3: Value Proposition & Solution Design:** Craft the specific solution narrative and quantify its business value.
4.  **Phase 4: Engagement & Proposal Development:** Build the C-level presentation and formal proposal.
5.  **Phase 5: Execution Roadmap & Closing:** Define the path from pilot to enterprise-wide adoption.

---

### Phase 1: Account Intelligence & Qualification

**Goal:** Move from a name on a list to a deeply understood potential partner. This phase leverages the `b2b-lead-intelligence-generator` framework to build a foundational understanding of the account.

**Actions:**

1.  **Define Target Profile:** Use `references/ideal_customer_profile.md` to define the target account criteria (industry, size, geography, known challenges).
2.  **Execute Deep-Dive Intelligence Gathering:** Use the `map` tool with the prompt template from `templates/account_intelligence_prompt.md` to gather comprehensive data on the target account. This is an expanded version of the b2b-lead-gen prompt, focused on a single, high-value target.
3.  **Synthesize Account Briefing Document:** Consolidate the gathered intelligence into a structured `account_briefing.md` using the template in `templates/account_briefing_template.md`. This document is the single source of truth for the account.

**Output:** A comprehensive Account Briefing document including key stakeholders, strategic initiatives, reported pain points, current technology stack, and competitive landscape.

---

### Phase 2: Strategic Opportunity Analysis

**Goal:** Identify the single most compelling, urgent, and valuable problem you can solve for the client.

**Actions:**

1.  **Identify Critical Business Challenges:** From the Account Briefing, identify the top 3-5 critical business challenges. These are not technical problems, but business problems (e.g., "29-year-old SAP systems are consuming 70% of IT budget," "Cybersecurity vulnerabilities create risk of $5M+ per incident").
2.  **Map Challenges to Your Solutions:** Create a mapping table that connects each critical challenge to a specific solution or capability you offer. Use the `references/solution_mapping_framework.md` for guidance.
3.  **Quantify the "Cost of Doing Nothing":** For each challenge, build a simple financial model to estimate the annual cost of inaction. Use the formulas and examples in `references/cost_of_inaction_models.md`.
4.  **Define the "Why Now?" Compelling Event:** Identify the trigger that makes this problem urgent *now*. (e.g., "Oracle Java renewal approaching," "New EU AI Act compliance deadline," "Plant consolidation creates a clean-slate opportunity").

**Output:** A prioritized list of strategic opportunities, each with a quantified pain point and a compelling event.

---

### Phase 3: Value Proposition & Solution Design

**Goal:** Design the integrated solution and craft a powerful, quantified value proposition.

**Actions:**

1.  **Select the "Play":** Based on the opportunity analysis, select the appropriate "Play" from the `references/strategic_plays.md`. A play is a pre-defined combination of solutions that addresses a common enterprise challenge (e.g., The Modernization Play, The AI-Powered Development Play).
2.  **Structure the Business Case:** Build the high-level business case using the `templates/business_case_summary_template.md`. This involves defining the investment, the expected value realization (ROI), and the payback period. Model this on the summary slides from the reference decks.
3.  **Develop the Value Realization Story:** Write the narrative that connects the investment to the outcome. Use the "Financial Impact," "Operational Efficiency," and "Strategic Value" buckets seen in the reference decks. Quantify everything.

**Output:** A complete Business Case document outlining the proposed solution, investment, and a multi-year value realization forecast.

---

### Phase 4: Engagement & Proposal Development

**Goal:** Create the C-level ready presentation and formal proposal documents.

**Actions:**

1.  **Generate the Strategic Presentation:** Using the `templates/strategic_presentation_template.md`, build the customer-facing PowerPoint presentation. This template is a synthesis of the most effective slide structures and narrative arcs from the six reference decks.
    *   **Key Principle:** The presentation should tell a story: Our Understanding of Your Challenge -> The Critical Gaps & Risks -> The Integrated Solution -> The Business Value & ROI -> The Path Forward.
2.  **Write the Formal Proposal:** Use the `templates/formal_proposal_template.md` to create the detailed proposal document. This includes the full scope of work, investment details, and terms.
3.  **Prepare the Stakeholder Map & Communication Plan:** Identify all key stakeholders (Economic Buyer, Technical Buyer, User Buyer, Champion) and tailor the messaging for each. Use `references/stakeholder_communication_plan.md`.

**Output:** A complete set of engagement documents: a strategic PowerPoint presentation, a formal proposal, and an internal stakeholder communication plan.

---

### Phase 5: Execution Roadmap & Closing

**Goal:** Define the concrete, phased plan to deliver the promised value and secure the deal.

**Actions:**

1.  **Design the Phased Engagement Roadmap:** Create a multi-phase roadmap, typically starting with a low-risk pilot or proof-of-value. Use the "Pilot to Enterprise Standard in 90 Days" or "Modernization Journey" models from the reference decks. The template is in `templates/engagement_roadmap_template.md`.
2.  **Define Success Metrics & Governance:** For each phase, define the specific, measurable success criteria (KPIs). Also, define the governance structure (e.g., Executive Steering Committee).
3.  **Outline Immediate Next Steps:** Create a clear, time-bound list of actions to move the deal forward (e.g., "Week 1: Executive Alignment Workshop," "Week 2: Commercials & SOW").

**Output:** A detailed Execution Roadmap to be included in the presentation and proposal, outlining the path to value realization.

