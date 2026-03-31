---
name: b2b-personalized-outreach
description: Researches B2B leads and crafts two hyper-personalized outreach messages for each, transitioning from a human connection to a commercial conversation. Use when asked to perform personalized outreach, connect with leads, or generate sales messages.
---

# B2B Personalized Outreach

This skill provides a framework for conducting deep, personalized research on a list of B2B leads and generating a two-part outreach sequence for each lead.

## Workflow

The process is designed to be executed in a single, parallel step using the `map` tool.

### 1. Prepare Inputs

- **Leads**: A list of individuals to research, formatted as `"[Full Name], [Title] at [Company]"`.
- **Product Portfolio**: The list of products or services the seller offers. This should be embedded directly into the prompt template.

### 2. Execute Parallel Research and Message Generation

Use the `map` tool to spawn a parallel research task for each lead. This is the core of the skill.

- **`name`**: `b2b_personalized_outreach`
- **`title`**: "Research leads and generate personalized outreach messages"
- **`prompt_template`**: The full prompt template is located in `references/prompt_template.md`. Read this file and use its content for the `prompt_template` argument.
- **`inputs`**: The list of leads prepared in the previous step.
- **`output_schema`**: Use the schema defined below.

#### Output Schema

```python
[
    MapOutputSchema(
        name="lead_name",
        type="string",
        title="Lead Name",
        description="Full name of the lead",
        format="Plain text, e.g. 'John Smith'",
    ),
    MapOutputSchema(
        name="title_and_company",
        type="string",
        title="Title and Company",
        description="Current role and employer",
        format="Plain text, e.g. 'Senior Engineer at Acme Corp'",
    ),
    MapOutputSchema(
        name="key_findings",
        type="string",
        title="Key Research Findings",
        description="3-5 specific, concrete facts found about this person from public sources, including sources used",
        format="Plain text, each fact on a new line starting with a dash",
    ),
    MapOutputSchema(
        name="relevant_products",
        type="string",
        title="Relevant IBM Products",
        description="IBM products from the portfolio most relevant to this lead",
        format="Comma-separated list",
    ),
    MapOutputSchema(
        name="message_1",
        type="string",
        title="Message 1 - Human Connection",
        description="First outreach message: warm, specific, no product mention, under 100 words",
        format="Plain text, ready to send",
    ),
    MapOutputSchema(
        name="message_2",
        type="string",
        title="Message 2 - Commercial Transition",
        description="Second message: natural transition to commercial conversation, references specific challenge and IBM product, under 120 words",
        format="Plain text, ready to send",
    ),
]
```

### 3. Compile and Deliver Results

Once the `map` operation is complete, the results will be available in a CSV and JSON file. 

1.  Read the results from the generated file.
2.  Format the output into a clear, readable Markdown document.
3.  Organize the document by lead, presenting the two messages for each person.
4.  Optionally, create a summary table of key findings for quick reference.
5.  Deliver the final Markdown document and the raw CSV/JSON files to the user.
