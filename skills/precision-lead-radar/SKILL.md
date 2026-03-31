---
name: b2b-lead-intelligence-generator
description: Generate comprehensive B2B lead databases with deep intelligence including decision maker contacts, pain points, solution matching, ROI projections, and revenue potential. Use when prospecting for B2B sales, building lead lists, conducting market research, creating sales intelligence databases, preparing for outreach campaigns, or when a user requests lead generation with detailed business intelligence.
---

# B2B Lead Intelligence Generator Skill v2.0

This skill generates comprehensive B2B lead databases with deep intelligence, including decision maker contacts, pain points, matched AI solutions, ROI projections, and full deliverable packages. It is a production-ready system reverse-engineered from a successful 1,000-lead generation project.

---

## When to Use This Skill

Use this skill when a user asks for:
- B2B lead lists or prospecting databases
- Market research with detailed company intelligence
- Sales intelligence with pain points and solution mapping
- A list of businesses to sell a product or service to

**Trigger phrases:** "find me leads", "build a prospect list", "generate a list of businesses", "who can I sell this to in [market]?"

---

## Inputs Required

Before starting, gather the following from the user:

1.  **Target Market:** The geographic area (e.g., "Atlanta, GA", "Austin, TX").
2.  **Lead Count:** The total number of qualified leads to generate (e.g., 100, 500, 1,000).
3.  **Solution Stack:** The specific products or services to be sold (e.g., "GoHighLevel, OpenAI, Lovabl", "Cybersecurity services").
4.  **Ideal Client Profile (ICP):** (Optional) Any specific industries or business sizes to focus on or exclude (e.g., "only law firms and healthcare", "exclude restaurants").

---

## The 5-Phase Workflow

### Phase 1: Market Research & Strategy

**Goal:** Define the target business categories and geographic sub-zones for lead collection.

1.  **Analyze Market:** Use web search to identify the top 15-25 business categories in the target market. Focus on local service businesses (e.g., law firms, healthcare, home services, real estate).
2.  **Define Geographic Zones:** If the market is large, break it down into 5-10 geographic sub-zones (e.g., "Buckhead", "Midtown", "Perimeter", "Suburbs").
3.  **Create Collection Plan:** Create a plan to collect the target number of leads, distributed across the defined categories and zones. Aim for batches of 50-100 leads at a time for parallel processing.

### Phase 2: Parallel Lead Collection

**Goal:** Collect the raw business data (name, address, phone, website) for the target number of leads.

1.  **Use the `map` tool** for each business category and geographic zone defined in Phase 1.
2.  **Prompt Template for `map`:**
    ```
    Find 50 [industry] businesses in [geographic zone], [city]. For each business, provide the following information:
    - Business Name
    - Full Address
    - Phone Number
    - Website URL
    ```
3.  **Output Schema for `map`:**
    - `business_name`: string
    - `address`: string
    - `phone`: string
    - `website`: string
4.  **Execute in Batches:** Run one `map` operation for each batch of 50-100 leads. Save the output of each batch to a separate CSV file (e.g., `batch_1_law_firms.csv`, `batch_2_healthcare.csv`).

### Phase 3: Intelligence Enrichment

**Goal:** Enrich the raw data with deep intelligence for every lead.

1.  **Use the `map` tool** again, this time using the output from Phase 2 as the input.
2.  **Prompt Template for `map`:**
    ```
    For the business "{{business_name}}" with website "{{website}}", conduct deep research and provide the following intelligence. The target solution stack is [Solution Stack].

    - Decision Maker: [Name and Title]
    - Email: [Email Address]
    - LinkedIn: [LinkedIn Profile URL]
    - Category: [Specific Industry]
    - Size: [Employee Count/Revenue Estimate]
    - Description: [1-2 sentence summary of the business]
    - Pain Points: [List 3-5 specific, quantifiable pain points relevant to the solution stack]
    - AI Solutions: [Map specific tools from the solution stack to each pain point]
    - Use Cases & ROI: [Provide a concrete use case and ROI calculation for each solution]
    - Cost of Doing Nothing: [Calculate the monthly cost of not solving the pain points]
    - Revenue Potential: [Estimate the potential deal size, from $1,200 to $50,000]
    ```
3.  **Output Schema for `map`:** Match the fields in the prompt template.
4.  **Execute in Batches:** Run this enrichment process for each batch CSV from Phase 2. Save the enriched output to new CSV files (e.g., `enriched_batch_1.csv`).

### Phase 4: Database Consolidation & Analysis

**Goal:** Merge all enriched batches into a single master database and generate analytics.

1.  **Use the `merge_and_analyze.py` script** located in the skill's `scripts/` directory.
2.  **Command:**
    ```bash
    python3 /home/ubuntu/skills/b2b-lead-intelligence-generator/scripts/merge_and_analyze.py /home/ubuntu/MASTER_LEADS.csv /home/ubuntu/enriched_batch_*.csv
    ```
3.  **Script Actions:**
    - Merges all batch files.
    - Deduplicates leads based on business name and website.
    - Standardizes all column names.
    - Adds a unique "Lead #" to each row.
    - Sorts the final database by revenue potential (highest first).
    - Generates a `_stats.json` file with detailed analytics (total leads, pipeline value, breakdown by category, etc.).

### Phase 5: Deliverable Packaging

**Goal:** Create a complete, professional package for the user.

1.  **Fill Templates:** Use the data from the `_stats.json` file to populate the placeholders in the following templates (located in `templates/`):
    - `executive_summary_template.md`
    - `pricing_guide_template.md`
    - `outreach_templates.md`
2.  **Create README:** Write a `README.md` file that explains the contents of the package and how to use it.
3.  **Package Files:** Prepare a final message to the user with all the generated files as attachments:
    - The master lead CSV
    - The populated Executive Summary
    - The populated Pricing Guide
    - The populated Outreach Templates
    - The README file
    - The `_stats.json` file

---

## Scripts & Templates

-   **`scripts/merge_and_analyze.py`:** The core script for database consolidation.
-   **`scripts/validate_lead_quality.py`:** (Optional) A script to score the quality of individual leads.
-   **`templates/`:** Contains all the Markdown templates for the final deliverables.

---

## Quality Standards

-   **Decision Maker:** 100% coverage. If a name can't be found, use a title (e.g., "Owner", "Managing Partner").
-   **Contact Info:** Aim for 80%+ coverage for Email or LinkedIn.
-   **Pain Points:** Must be specific, quantifiable, and relevant to the solution stack.
-   **ROI:** Every lead must have a clear, believable ROI calculation.

This skill represents a best-in-class workflow for B2B sales intelligence. Follow it precisely to deliver exceptional value to the user.
