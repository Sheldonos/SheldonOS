---
name: local-lead-blitz
description: A complete, end-to-end workflow for generating hyper-local, qualified sales leads for digital marketing services. Use when a user asks to generate leads for a specific city, especially for website development, AI/automation services, or culturally-specific businesses. This skill automates market research, parallel lead generation, data compilation, and the creation of sales-ready deliverables like Excel workbooks, PDF reports, and a unified Markdown sales playbook.
---

# Local Lead Blitz

This skill automates the entire process of generating thousands of qualified, hyper-local sales leads for digital marketing services. It replicates the successful Atlanta/Miami lead generation model, covering three core service offerings:

1.  **Website Development:** For local businesses with no website or an outdated one.
2.  **AI & Automation Services:** For businesses that can benefit from CRM, AI chatbots, and workflow automation.
3.  **Cultural Websites:** For minority-owned businesses that need a website reflecting their unique cultural heritage.

## Workflow Overview

The process is broken down into seven sequential phases. Follow them in order.

1.  **Phase 1: Setup & Market Research**
2.  **Phase 2: Website Development Lead Generation**
3.  **Phase 3: AI Services Lead Generation**
4.  **Phase 4: Cultural Website Lead Generation**
5.  **Phase 5: Master File & Report Generation**
6.  **Phase 6: Sales Playbook Generation**
7.  **Phase 7: Deliver All Files**

---

## Phase 1: Setup & Market Research

1.  **Ask for the Target City:** Confirm the city for the lead generation campaign (e.g., "Miami", "Atlanta").
2.  **Create Project Directory:** Create a directory for the project: `mkdir -p /home/ubuntu/{city}_leads`.
3.  **Conduct Market Research:** Use the `search` tool to understand the target city's business landscape. Identify key industries, dominant cultural communities, and major commercial neighborhoods. This research will inform the lead generation queries.

---

## Phase 2: Website Development Lead Generation

1.  **Generate Leads in Parallel:** Use the `map` tool to generate 500-1000 website development leads. Use the prompt template found in `/home/ubuntu/skills/local-lead-blitz/references/website_leads_prompt.md`. The `inputs` should be a list of business categories relevant to the target city (e.g., "Auto Repair in Miami", "Restaurants in Coral Gables").
2.  **Compile Master CSV:** Run the `compile_website_leads.py` script to process the parallel results into a master CSV file. The script will be in the `scripts` directory.

    ```bash
    python3.11 /home/ubuntu/skills/local-lead-blitz/scripts/compile_website_leads.py
    ```

---

## Phase 3: AI Services Lead Generation

1.  **Generate Leads in Parallel:** Use the `map` tool to generate ~1000 AI services leads. Use the prompt template found in `/home/ubuntu/skills/local-lead-blitz/references/ai_leads_prompt.md`. The `inputs` should be a list of industry verticals relevant to the target city (e.g., "Law Firms in Miami", "Healthcare Clinics in Miami").
2.  **Compile Master CSV:** Run the `compile_ai_leads.py` script.

    ```bash
    python3.11 /home/ubuntu/skills/local-lead-blitz/scripts/compile_ai_leads.py
    ```
3.  **Handle Supplemental Leads (If Necessary):** If the initial batch has parsing issues or low yield, run a supplemental batch and merge the results using the `merge_ai_leads.py` script.

---

## Phase 4: Cultural Website Lead Generation

1.  **Generate Leads in Parallel:** Use the `map` tool to generate ~500 cultural website leads. Use the prompt template found in `/home/ubuntu/skills/local-lead-blitz/references/cultural_leads_prompt.md`. The `inputs` should be a list of culturally-specific business categories and neighborhoods (e.g., "Cuban restaurants in Little Havana", "Haitian art galleries in Little Haiti").
2.  **Compile Master CSV:** Run the `compile_cultural_leads.py` script.

    ```bash
    python3.11 /home/ubuntu/skills/local-lead-blitz/scripts/compile_cultural_leads.py
    ```

---

## Phase 5: Master File & Report Generation

1.  **Install Dependencies:** Ensure `openpyxl` and `pandas` are installed: `sudo pip3 install openpyxl pandas`.
2.  **Create Excel Workbooks:** Run the three workbook creation scripts to generate the master Excel files with dashboards and guides.

    ```bash
    python3.11 /home/ubuntu/skills/local-lead-blitz/scripts/create_website_leads_workbook.py
    python3.11 /home/ubuntu/skills/local-lead-blitz/scripts/create_ai_leads_workbook.py
    python3.11 /home/ubuntu/skills/local-lead-blitz/scripts/create_cultural_leads_workbook.py
    ```
3.  **Create PDF Reports:** For each of the three lead types, write a summary report in Markdown and convert it to PDF using `manus-md-to-pdf`.
4.  **Create ZIP Packages:** Create a ZIP archive for each lead package, containing the CSV, Excel workbook, and PDF report.

---

## Phase 6: Sales Playbook Generation

1.  **Split Leads into Batches:** Run the `split_for_batches.py` script to prepare the compiled CSVs for parallel processing.

    ```bash
    python3.11 /home/ubuntu/skills/local-lead-blitz/scripts/split_for_batches.py
    ```
2.  **Generate Playbook Entries:** Use the `map` tool to convert all lead batches into the formatted Markdown sales playbook. Use the prompt template from `/home/ubuntu/skills/local-lead-blitz/references/playbook_prompt.md`.
3.  **Compile Final Playbook:** Run the `compile_playbook.py` script to assemble the final, unified Markdown file.

    ```bash
    python3.11 /home/ubuntu/skills/local-lead-blitz/scripts/compile_playbook.py
    ```

---

## Phase 7: Deliver All Files

Use the `message` tool to deliver all final ZIP packages and the unified sales playbook Markdown file to the user.
