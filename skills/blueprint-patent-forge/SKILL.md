---
name: ibm-patent-architect
description: A framework for analyzing user ideas, identifying patentable opportunities, and generating finalized, defensible IBM-style patent disclosure documents. Use when a user asks to patent an idea, analyze an idea for patentability, or write an IBM patent disclosure.
---

# IBM Patent Architect

This skill provides a structured methodology for transforming raw ideas into defensible, enterprise-grade IBM patent disclosure documents. It ensures that the resulting patents are novel, logically sound, aligned with industry trajectories, and formatted according to IBM's internal standards.

## Core Philosophy

1. **Pivot from Physics to System Integration:** Do not just patent the underlying science or algorithm (which may be prior art). Patent the novel *integration, control mechanism, and orchestration* of those elements within an enterprise architecture.
2. **Explicit Differentiation:** Clearly define how the proposed system differs from existing solutions (e.g., standard reinforcement learning vs. predictive agentic AI).
3. **Solve the Paradox:** Identify the critical bottleneck or paradox in the current state of the art (e.g., PQC latency vs. quantum coherence) and introduce a specific mechanism to solve it (e.g., Predictive Phase-Space Displacement).
4. **Enterprise Readiness:** Ensure the solution maps to a concrete architecture with clear hardware/software interfaces, APIs, and hybrid cloud integration.

## Workflow

When a user shares an idea and requests a patent, follow these sequential steps:

### Step 1: Idea Analysis & Gap Identification
1. **Analyze the core concept:** Understand the technical domain and the problem being solved.
2. **Conduct Prior Art Research:** Use the `search` tool to find existing patents, papers, and news related to the idea.
3. **Identify Vulnerabilities:** Determine where the idea overlaps with prior art or lacks technical depth.
4. **Formulate the "Secret Sauce":** Develop a novel mechanism or integration strategy that overcomes the identified vulnerabilities and solidifies the patent's defensibility.

### Step 2: Architecture & Claim Strategy
1. **Design the Architecture:** Map the solution into a multi-layered enterprise architecture (e.g., Application Layer, Control Plane, Security Fabric, Physical Layer).
2. **Draft the Claim Strategy:** Focus the primary claims on the novel feedback loop, orchestration, or integration mechanism, explicitly disclaiming the non-novel underlying components.

### Step 3: Document Generation
Generate the final patent disclosure document using the exact IBM format provided in the template below.

## Output Template: IBM Patent Disclosure Format

ALWAYS use this exact template structure for the final output:

```markdown
## [ID]. [Patent Title: Must be descriptive and enterprise-focused]

### STEP 1 - INFORMATION + SECURITY
**1. Is this invention related to ITAR?** [Yes/No]
**2. Does this invention use Technology Code 153020 (Cloud Secure Data Management)?** [Yes/No]
**3. Does this invention use Quantum Technology?** [Yes/No]
**4. Is this invention Export Controlled?** [Yes/No]
**5. Should this invention be kept secret?** [Yes/No]

### STEP 2 - INVENTION DESCRIPTION

**7. Invention Description - Background**
(a) Problem Solved: [Describe the critical bottleneck or paradox in the current state of the art.]
(b) Related Art: [Summarize prior art and explicitly state what it lacks. Include patent search terms.]
(c) Drawbacks: 
1. [Drawback 1]
2. [Drawback 2]
3. [Drawback 3]

**8. Invention Description - Summary**
(a) Main Idea: [Provide a comprehensive overview of the enterprise-grade solution, highlighting the novel integration and control mechanisms.]
(b) Advantages: 
1. [Advantage 1]
2. [Advantage 2]
3. [Advantage 3]
(c) How it solves the problem: [Explain exactly how the novel mechanism overcomes the drawbacks identified in the background.]

**9. Invention Description - Details**
(a) Implementation: [Describe the system architecture in detail, breaking it down into 3-4 primary layers or modules. Explain the data flow and feedback loops between them.]

![Architecture Diagram](architecture.png)

(b) Embodiments:
1. [Enterprise Use Case 1]
2. [Enterprise Use Case 2]
3. [Enterprise Use Case 3]

### STEP 3 – INVENTOR QUESTIONS
**10. Previous Disclosures:** NA
**11. First Submission?** No
**12. In IBM Product?** NA
**13. Disclosed to Non-IBMers?** NA
**14. Customer Activity?** NA
**15. Joint Development?** NA
**16. Government Funded?** No
**17-19. Gov Contract Details:** NA
**20. Acquisition?** NA
**21. Applicable to Standard?** NA
**22. Use by Others:** NA
**23. Discoverability of Use:** High — visible in cloud architecture and API endpoints
**24. Invention Geography:** United States
**25. Functional Area:** Research
**26. Technology Code:** [Relevant Code]
**27. Business Unit:** IBM Research
**28. AI Tools Used?** Yes
**29. AI Tool(s):** Manus AI
**30. Export Control Additional:** [Relevant Category]

### STEP 4 - DOCUMENTS
**Market Analysis & TAM:**
[Provide a detailed Total Addressable Market analysis, including projected growth, revenue potential, and competitive landscape.]

**Detailed Use Cases:**
1. [Detailed Use Case 1 with Expected ROI]
2. [Detailed Use Case 2 with Expected ROI]
3. [Detailed Use Case 3 with Expected ROI]

**Claim Language Draft:**
1. [Primary Independent Claim: Focus on system integration and control mechanism]
2. [Dependent Claim: Specific novel feature]
3. [Dependent Claim: Specific novel feature]
4. [Dependent Claim: Specific novel feature]
5. [Independent Method Claim]
6. [Dependent Method Claim]
7. [Dependent Method Claim]
8. A non-transitory computer-readable medium storing instructions that, when executed by a processor, cause the processor to perform the method of claim 5.

### STEP 5 - RELATED ART
1. [Prior Art Reference 1]
2. [Prior Art Reference 2]

### STEP 6 - INVENTORS
Primary Inventor: IBM Research Team
```

## Additional Requirements
- **Architecture Diagram:** Always generate a Mermaid diagram (`.mmd`) illustrating the system architecture and data flow, render it to a PNG using `manus-render-diagram`, and include it in the final document under the "Implementation" section.
- **Tone:** Professional, academic, and highly technical.
