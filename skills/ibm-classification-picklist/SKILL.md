---
name: ibm-classification-picklist
description: A skill for navigating and filling out the IBM Patent Classification Picklist (Technology Code and Functional Area fields) in the IBM ThinkIP Invention Disclosure Form. Use when a user asks to file a patent, submit an invention disclosure, fill out the classification picklist, select technology codes, or select functional areas for an IBM patent disclosure.
license: Complete terms in LICENSE.txt
---

# IBM Patent Classification Picklist Navigator

This skill provides a structured workflow for filling out the Classification Picklist in the IBM ThinkIP Invention Disclosure Form when filing patents. It specifically focuses on accurately selecting the **Technology Code** and **Functional Area** fields, which are critical for proper routing and evaluation of the patent application.

## Workflow for Filing Patents

When tasked with filing a patent and filling out the Classification Picklist, follow these steps:

### 1. Analyze the Patent Disclosure

Before selecting codes, analyze the invention disclosure to understand its core technology and the inventors' functional area. This ensures the patent is routed to the correct Invention Development Team (IDT).

*   **Core Technology:** What is the primary technical domain of the patent? (e.g., Quantum Computing, Blockchain, Security, AI, Cloud).
*   **Inventor Location/Function:** Where are the inventors located (US vs. Global) and what is their primary business unit or research area?

### 2. Select the Technology Code

The Technology Code categorizes the patent's technical subject matter. Accurate selection is vital for efficient handling of the Committee Review.

1.  **Identify Keywords:** Extract key technical terms from the patent description.
2.  **Search the Picklist:** Use the "Technology Code" search field in the Classification Picklist dialog. Set the criteria to "Contains" and enter the keywords.
3.  **Review Results:** Examine the resulting classification nodes.
4.  **Select the Best Fit:** Choose the most specific and accurate Technology Code for the patent.

**Common Technology Code Categories for Patents (Examples based on reference images):**

*   **1106 - Quantum:**
    *   `110601` - Quantum Hardware (qubit chips, pkg, interconnects, I/O)
    *   `110602` - Quantum Software: cloud based, hybrid computing
    *   `110603` - Quantum Control Electronics, Cyro-control, Cryogenics & System Infrastructure
    *   `110604` - Quantum Enterprise Workflow & Solutions
    *   `110630` - EDA Tools and Methodology - Quantum
    *   `110640` - Quantum gate and measurement calibrations
    *   `110650` - Quantum algorithms, arch. optimization, circuit compiling, error correction, info theory
    *   `110660` - Algorithms Utilizing Quantum Computers
*   **1204 - Blockchain and Distributed Ledger:**
    *   `120499` - All Blockchain And Distributed Ledger Inventions
*   **9.119 - 908 SECURITY, PRIVACY, CRYPTOGRAPHY, EPAYMENTS**

### 3. Select the Functional Area

The Functional Area categorizes the organizational origin of the patent.

1.  **Determine Geography:** Identify if the submitters are in the US or another geography.
    *   *Note:* Functional areas 1 through 15 are typically for submitters located in the United States.
2.  **Identify Business Unit/Research Area:** Determine the specific division (e.g., Global Markets, Global Services, Research - Almaden, Systems - Cognitive Systems / Power Systems).
3.  **Search the Picklist:** Use the "Functional Area" search field. Set the criteria to "Contains" and enter relevant terms (e.g., "Almaden", "Power Systems").
4.  **Select the Best Fit:** Choose the node that accurately reflects the inventors' organization.

**Common Functional Area Categories for Patents (Examples based on reference images):**

*   **US Submitters:**
    *   `3` - Submitters in US - Global Markets
    *   `4` - Submitters in US - Global Services
    *   `7` - Submitters in US - Research - Almaden
    *   `9` - Submitters in US - Research - Yorktown and US CHQ
    *   `10` - Submitters in US - Systems - Cognitive Systems / Power Systems
    *   `11` - Submitters in US - Systems - Quantum

### 4. Finalize Selection

After selecting the appropriate Technology Code and Functional Area, confirm the selections in the ThinkIP form to proceed with the patent filing process.

## Important Considerations for Patent Filing

*   **Accuracy is Critical:** Selecting an improper tech code may delay processing the patent invention.
*   **ITAR and Export Control:** Be aware of specific Technology Codes that trigger Export Control reviews (e.g., Cryptography, Secure Hardware, Aerospace, specific Quantum codes). If a patent falls under these categories, follow the specific ThinkIP instructions for export-controlled content (e.g., answering "YES" to Export Control questions, providing simplified titles, and not entering detailed descriptions directly into the form).
*   **AskIBM Tech Code Assistant:** If available, recommend using the AskIBM Tech Code Assistant to obtain relevant tech codes for the patent.
