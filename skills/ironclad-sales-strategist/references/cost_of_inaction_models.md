# Cost of Doing Nothing (CoDN) Financial Models

This document provides simple, defensible financial models to quantify the cost of a customer not acting on a key business challenge. The goal is to anchor the conversation in financial reality and create a clear justification for investment.

## Model 1: Excess Legacy Maintenance Costs

**When to Use:** When a customer has significant legacy systems (e.g., Mainframe, old ERPs) consuming a large portion of their IT budget.

**Formula:**

`CoDN = (Total Annual IT Budget * % Spent on Maintenance) - (Total Annual IT Budget * Target % Spent on Maintenance)`

**Example:**

*   Total Annual IT Budget: $500M
*   Current % Spent on Maintenance: 65%
*   Target % Spent on Maintenance (with our solution): 35%
*   **CoDN** = ($500M * 0.65) - ($500M * 0.35) = $325M - $175M = **$150M per year**

## Model 2: Cost of Downtime

**When to Use:** For challenges related to system reliability, cybersecurity, or supply chain disruptions that could halt revenue-generating operations.

**Formula:**

`CoDN = (Annual Revenue / Operating Hours per Year) * Hours of Downtime per Incident * Number of Incidents per Year`

**Example:**

*   Annual Revenue: $32B
*   Operating Hours per Year: 8,760
*   Estimated Hours of Downtime per Incident: 24
*   Estimated Number of Incidents per Year: 2
*   **CoDN** = ($32B / 8760) * 24 * 2 = $3.65M/hour * 48 hours = **$175M per year**

## Model 3: Developer Productivity Loss

**When to Use:** When challenges relate to slow development cycles, manual processes, or lack of modern tools for a large development organization.

**Formula:**

`CoDN = (Number of Developers * Average Fully-Loaded Developer Salary) * Productivity Loss %`

**Example:**

*   Number of Developers: 3,700
*   Average Fully-Loaded Developer Salary: $150,000
*   Estimated Productivity Loss % due to legacy tools: 20%
*   **CoDN** = (3700 * $150,000) * 0.20 = $555M * 0.20 = **$111M per year**

## Model 4: Regulatory Compliance Risk

**When to Use:** When a challenge relates to non-compliance with a major regulation that has defined financial penalties.

**Formula:**

`CoDN = (Global Annual Revenue * Max Penalty %) * Probability of Fine %`

**Example:**

*   Global Annual Revenue: $32B
*   Max Penalty % (e.g., EU AI Act): 6%
*   Estimated Probability of being found non-compliant and fined: 10%
*   **CoDN** = ($32B * 0.06) * 0.10 = $1.92B * 0.10 = **$192M per year**
