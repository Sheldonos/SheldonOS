---
name: ibm-solution-accelerator
description: A complete workflow for discovering a company use case, generating IBM DevOps Solution Workbench architecture artifacts (C4 diagrams, domain models, OpenAPI specs, scaffolded code), and producing a master IBM Project Bob prompt. Use when a user asks to develop an application or use case using IBM DevOps Solution Workbench and IBM Project Bob.
---

# IBM Solution Accelerator

This skill provides a complete, end-to-end workflow for designing and architecting enterprise applications using the IBM toolchain (DOORS Next, Solution Workbench, and Project Bob). It takes a high-level business problem and generates a comprehensive, production-ready architecture package and AI prompt.

## Core Workflow

When a user requests to build an application using IBM Solution Workbench and Project Bob, follow these steps sequentially:

### Step 1: Research and Discovery
1. Identify the target company and the specific use case.
2. Use the `search` tool to research the company's business model, current challenges, and technical landscape.
3. Define the core business problem that the application will solve.

### Step 2: Architecture Design (Solution Workbench Simulation)
Act as the IBM DevOps Solution Workbench to generate the following architectural artifacts:
1. **C4 Diagrams:** Write Mermaid code for a System Context Diagram (Level 1) and a Container Diagram (Level 2). Render these to PNG using the `sheldon-render-diagram` utility.
2. **Domain Model:** Design a comprehensive JSON domain model including Aggregates, Entities, Value Objects, and Enums.
3. **OpenAPI Specifications:** Write complete OpenAPI 3.0 YAML specifications for the core microservices.
4. **Scaffolded Code:** Write realistic boilerplate code (e.g., Node.js/Express or Java/Spring Boot) with `TODO [BOB]` markers where business logic should be implemented.
5. **Deployment Manifests:** Write a Kubernetes/OpenShift deployment YAML for the services.

### Step 3: Master Prompt Generation (Project Bob)
Create a comprehensive, copy-paste-ready prompt for IBM Project Bob. This prompt must:
1. Provide the project context.
2. Instruct Bob to read the generated artifacts (domain model, OpenAPI specs, scaffolded code).
3. Break down the implementation into specific, numbered tasks.
4. Include strict security and code quality requirements.

### Step 4: Document Compilation
1. Read the template at `/home/ubuntu/skills/ibm-solution-accelerator/templates/solution_document_template.md`.
2. Compile all generated artifacts and the master prompt into a single, professional Markdown document based on the template.
3. Convert the Markdown document to a PDF using the `sheldon-md-to-pdf` utility.
4. Deliver the final PDF and Markdown files to the user.

## References

For detailed information on the IBM tools simulated in this workflow, read:
- `/home/ubuntu/skills/ibm-solution-accelerator/references/ibm_toolchain_overview.md`

## Output Quality Standards

- **Professionalism:** The final document must be highly professional, suitable for presentation to enterprise architects and C-level executives.
- **Technical Accuracy:** OpenAPI specs must be valid YAML. Domain models must follow DDD principles. Scaffolded code must be syntactically correct for the chosen language.
- **Completeness:** Do not use placeholders like "insert code here" in the final output. Generate the full, realistic content for all artifacts.
