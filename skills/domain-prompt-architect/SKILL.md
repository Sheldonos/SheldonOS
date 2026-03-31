---
name: specialized-prompt-writer
description: A framework for writing highly structured, specialized AI prompts for any domain (e.g., writing, coding, analysis, strategy) based on the Amir Mushich methodology. Use when a user asks to generate professional, multi-phased prompts for complex tasks outside of image/video generation.
---

# Specialized Prompt Writer

This skill provides a framework for writing professional, highly structured AI prompts. It adapts the renowned Amir Mushich creative direction methodology into a universal, domain-agnostic framework capable of producing exceptional results across any field—from strategic analysis and technical coding to creative writing and system architecture.

## Core Philosophy

This approach to AI generation is built on the following principles:
1. **Director Mindset**: Treat AI as an expert you DIRECT, not a search engine you query.
2. **Core Identity First**: Always ground the prompt in the fundamental DNA, purpose, or identity of the subject, brand, or project.
3. **Specificity Wins**: Vague prompts yield vague results; precise, structured direction yields professional output.
4. **AI Autonomy with Guardrails**: Use "Act as [role]" and specific constraints to empower the AI to make intelligent decisions within defined parameters.
5. **Positive Framing**: Describe exactly what you WANT, rather than what you don't want.

## The "Smart Prompt" Framework

These "smart prompts" are highly structured and typically follow this anatomy:

### 1. Variable Declaration
Declare variables at the top for easy swapping (e.g., `[COMPANY NAME] = Acme Corp`, `[TARGET AUDIENCE] = Enterprise CIOs`, `[TECH STACK] = Python/React`).

### 2. Role Assignment
Always assign a specific, high-level professional role to the AI (e.g., `Act as a Visionary Enterprise Architect and Master Strategist.`).

### 3. Goal Statement
Provide one clear sentence stating the ultimate output goal (e.g., `Goal: Generate a comprehensive, multi-phased digital transformation roadmap for [COMPANY NAME].`).

### 4. Phase-Based Instructions
Break the prompt down into distinct, logical phases. For example:
- **PHASE 1: SEMANTIC INTELLIGENCE (AUTONOMOUS)** - Context analysis, identity extraction, data synthesis.
- **PHASE 2: STRUCTURAL LOGIC** - Framework, architecture, narrative arc, or grid layout.
- **PHASE 3: CORE EXECUTION** - The main content generation, coding, or stylistic application.
- **PHASE 4: REFINEMENT & NUANCE** - Tone, edge cases, texture, or advanced details.
- **PHASE 5: OUTPUT SPECIFICATIONS** - Format, length, technical constraints, or render settings.

### 5. Output Specs Block
Always end with strict technical or formatting specifications (e.g., `Output as a valid JSON object`, `Use Markdown with strict H2/H3 hierarchy`, `Generate Mermaid.js diagrams`).

## Key Techniques to Apply

When writing prompts using this skill, ensure you incorporate these techniques:

- **AI Autonomy Blocks**: Give the AI freedom to make expert decisions within defined parameters (e.g., "Analyze the core market dynamics... autonomously determine the top 3 unexploited niches...").
- **Adaptive Analysis**: Instruct the AI to analyze the input context and adapt the output accordingly.
- **Sensory & Precise Language**: Use highly specific, professional terminology relevant to the domain.
- **Named Frameworks/Styles**: Use specific references (e.g., "McKinsey MECE framework", "Clean Architecture principles", "Hero's Journey").

## Workflow

1. **Understand the Request**: Identify the domain, subject, and desired output format (e.g., business strategy, code architecture, creative writing).
2. **Select a Template**: Choose the most appropriate template from the `references/templates.md` file.
3. **Customize the Prompt**: Fill in the variables and adapt the role, phases, and output specs to fit the specific request.
4. **Deliver the Prompt**: Present the finalized prompt to the user, ready to be copied and pasted into their AI tool of choice.
5. **Add Value**: Include a "Tips for Maximum Value" section and semantic search hashtags as specified in the knowledge base.

## Bundled Resources

- **`references/templates.md`**: Contains a collection of generalized signature prompt templates for various use cases (Strategic Analysis, Technical Architecture, Creative Narrative, etc.). Read this file to select the appropriate template for the user's request.
