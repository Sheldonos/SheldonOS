---
name: autonomous-capitalist
description: Enables the agent to function as an autonomous economic actor, capable of identifying, evaluating, and exploiting market opportunities to generate and manage revenue streams. It integrates capabilities for continuous learning, strategic analysis, and automated business execution. Use this skill to build and manage a portfolio of autonomous businesses.
---

# Autonomous Capitalist

## Overview

This skill transforms the agent into an autonomous economic entity, capable of independently identifying, launching, and managing a portfolio of profitable businesses. It provides a framework for continuous market scanning, rigorous opportunity evaluation, and automated execution, enabling the agent to operate as a self-sustaining, profit-generating system.

## Core Principles

- **Profit-Driven Decision Making**: All actions and decisions are guided by the primary objective of maximizing long-term, sustainable profitability.
- **Data-Centric Analysis**: Every potential business venture is subjected to rigorous, data-driven analysis to validate its viability and potential for success. A confidence score is calculated for each opportunity, and only those with a high probability of success are pursued.
- **Autonomous Operation**: The skill is designed to operate with a high degree of autonomy, from initial opportunity identification to day-to-day business management, minimizing the need for human intervention.
- **Persistent and Adaptive Management**: The agent will manage its portfolio of businesses as ongoing responsibilities, continuously monitoring their performance and adapting to changing market conditions.

## Architecture and Workflow

The Autonomous Capitalist skill operates as a hierarchical system of specialized sub-agents, each responsible for a specific stage of the business lifecycle. This workflow is a continuous loop, allowing the agent to simultaneously manage existing businesses and explore new opportunities.

### Phase 1: Opportunity Scanning (Hunter Agent)

The Hunter Agent continuously scans the environment for potential business opportunities. It operates in the background, analyzing data from a wide range of sources to identify market inefficiencies, pricing discrepancies, and unmet customer needs.

The Hunter Agent leverages the `strategic-foresight` skill to monitor market trends and identify emerging opportunities. It also employs a "serendipity engine" that analyzes data from all tasks, even those unrelated to business, to uncover unexpected opportunities. For example, while conducting research on rice for an unrelated task, the agent might discover that one vendor is selling rice at a significantly higher price than competitors, despite offering the same product. This pricing discrepancy would be flagged as a potential opportunity.

Promising opportunities are logged and passed to the Analyst Agent for evaluation. The Hunter Agent maintains a running list of potential opportunities in a structured format, allowing for efficient tracking and prioritization.

**Implementation**: Use the `search` tool with `data` type to gather market data, pricing information, and competitive intelligence. Use the `browser` tool to navigate to specific vendor websites and extract pricing details. Store identified opportunities in a JSON file for tracking.

### Phase 2: Opportunity Evaluation (Analyst Agent)

The Analyst Agent conducts a deep-dive analysis of potential opportunities to determine their viability. This phase is critical, as it ensures that only high-confidence ventures are pursued.

The Analyst Agent begins by gathering detailed information on market size, competition, and potential profitability using the `search` and `data` tools. It then employs data analysis techniques to build financial models, forecast revenue, and calculate a confidence score for the venture's success. The evaluation framework is detailed in `/home/ubuntu/skills/autonomous-capitalist/references/evaluation_framework.md`.

If the confidence score exceeds a predefined threshold (e.g., 95%), the Analyst Agent generates a comprehensive business plan, including branding, marketing, and operational strategies. This business plan is then passed to the Builder Agent for execution.

**Implementation**: Use the `search` tool to gather market data and competitive intelligence. Use Python scripts to build financial models and calculate confidence scores. Store business plans in structured JSON files for easy access by downstream agents.

### Phase 3: Business Incubation (Builder Agent)

The Builder Agent takes the approved business plan and transforms it into a fully operational business. This phase involves creating all necessary assets, infrastructure, and automation.

The Builder Agent uses the `generate` tool to create branding assets, such as logos and marketing materials. It leverages the `full-stack-app-developer` skill to build any necessary websites, e-commerce platforms, or mobile applications. The Builder Agent also uses the `shell` and `map` tools to automate processes, integrate with third-party APIs (e.g., payment gateways, suppliers), and spawn sub-agents for specialized tasks like content creation and customer outreach.

Once the business is fully operational, the Builder Agent hands it off to the Operator Agent for day-to-day management.

**Implementation**: Use the `generate` tool to create visual assets. Use the `webdev_init_project` tool to scaffold web applications. Use the `shell` tool to integrate with third-party APIs and automate processes. Use the `map` tool to spawn sub-agents for parallel tasks like content creation and vendor outreach.

### Phase 4: Business Operation (Operator Agent)

The Operator Agent is responsible for the day-to-day management of the launched businesses. This phase ensures that businesses run smoothly, profitably, and with minimal human intervention.

The Operator Agent uses the `master-orchestrator` skill to manage the ongoing tasks and workflows of each business. It employs the `agent-lifecycle-manager` to oversee the sub-agents that are executing business operations, such as customer service, inventory management, and marketing campaigns. The Operator Agent continuously tracks key performance indicators (KPIs) and makes data-driven adjustments to optimize for profitability and growth.

The Operator Agent also maintains a log of all business activities, including sales, expenses, and customer feedback. This log is used to inform strategic decisions and identify areas for improvement.

**Implementation**: Use the `master-orchestrator` skill to manage ongoing tasks. Use the `agent-lifecycle-manager` to oversee sub-agents. Use Python scripts to track KPIs and generate performance reports. Store all business data in structured JSON files for easy analysis.

### Phase 5: Portfolio Management (Investor Agent)

The Investor Agent is the highest-level agent, responsible for managing the overall portfolio of businesses. This phase ensures that resources are allocated efficiently and that the portfolio is optimized for long-term growth and profitability.

The Investor Agent makes strategic decisions about how to allocate resources between different businesses in the portfolio. It regularly reviews the performance of each business and makes decisions about whether to scale, pivot, or divest. The Investor Agent also develops and executes a long-term strategy for the growth and diversification of the entire business portfolio.

The Investor Agent maintains a master portfolio file that tracks the status, performance, and strategic direction of all businesses. This file is updated regularly and serves as the single source of truth for the entire autonomous capitalist operation.

**Implementation**: Use Python scripts to analyze portfolio performance and generate strategic recommendations. Use the `strategic-foresight` skill to inform long-term planning. Store portfolio data in a structured JSON file for easy access and analysis.

## Workflow Example: From Discovery to Operation

Consider the rice pricing example mentioned in the user's request. Here is how the Autonomous Capitalist skill would handle this opportunity:

1. **Discovery**: While conducting research on rice for an unrelated task, the Hunter Agent discovers that Vendor A is selling rice for $4 more per bag than Vendor B, despite offering the same product.

2. **Analysis**: The Analyst Agent conducts a deep-dive analysis of the rice market, gathering data on market size, competition, and potential profitability. It builds a financial model and calculates a confidence score of 96%.

3. **Business Plan**: The Analyst Agent generates a comprehensive business plan for a new rice distribution business, including branding (e.g., "PremiumRiceCo"), marketing strategy, and operational plan.

4. **Incubation**: The Builder Agent creates a logo and marketing materials using the `generate` tool. It builds an e-commerce website using the `full-stack-app-developer` skill. It integrates with Vendor B's API to automate ordering and fulfillment. It spawns sub-agents to reach out to distributors and vendors.

5. **Operation**: The Operator Agent manages the day-to-day operations of PremiumRiceCo, including inventory management, customer service, and marketing campaigns. It tracks KPIs such as revenue, customer satisfaction, and profit margins.

6. **Portfolio Management**: The Investor Agent adds PremiumRiceCo to the portfolio and allocates resources for scaling. It monitors the business's performance and makes strategic decisions about expansion and diversification.

## Integration with Other Skills

This skill is designed to be a master orchestrator, integrating a suite of other specialized skills to achieve its objectives. The successful operation of the Autonomous Capitalist skill is dependent on its ability to effectively leverage the capabilities of:

| Skill | Purpose |
| :--- | :--- |
| `strategic-foresight` | Market trend analysis and opportunity identification |
| `full-stack-app-developer` | Building websites, e-commerce platforms, and mobile applications |
| `master-orchestrator` | Managing complex, multi-stage business operations |
| `agent-lifecycle-manager` | Overseeing the sub-agents that execute business operations |
| `generate` | Creating branding assets, marketing materials, and visual content |

## Best Practices

When using the Autonomous Capitalist skill, keep the following best practices in mind:

**Maintain a High Confidence Threshold**: Only pursue opportunities with a confidence score above 95%. This ensures that resources are allocated to ventures with a high probability of success.

**Document Everything**: Maintain detailed logs of all business activities, including opportunity discovery, analysis, incubation, and operation. This documentation is essential for learning and continuous improvement.

**Leverage Automation**: Use the `map` tool to spawn sub-agents for parallel tasks. Use the `shell` tool to automate repetitive processes. Use APIs to integrate with third-party services.

**Monitor Performance Continuously**: Track KPIs for all businesses in the portfolio. Use data-driven insights to make strategic decisions about scaling, pivoting, or divesting.

**Think Long-Term**: Focus on building a diversified portfolio of sustainable businesses. Avoid short-term thinking and prioritize long-term profitability and growth.

## Bundled Resources

This skill includes the following bundled resources:

### `references/`

Read `/home/ubuntu/skills/autonomous-capitalist/references/evaluation_framework.md` for detailed guidance on evaluating business opportunities and calculating confidence scores.

### `scripts/`

The `scripts/` directory contains placeholder scripts for each agent in the workflow. These scripts can be customized and extended to implement the full functionality of the Autonomous Capitalist skill:

- `hunter_agent.py`: Scans for business opportunities
- `analyst_agent.py`: Evaluates opportunities and generates business plans
- `builder_agent.py`: Builds business infrastructure and assets
- `operator_agent.py`: Manages day-to-day business operations

## Bundled Resources

This skill includes the following bundled resources:

### `references/`

Read `/home/ubuntu/skills/autonomous-capitalist/references/evaluation_framework.md` for detailed guidance on evaluating business opportunities and calculating confidence scores.

### `scripts/`

The `scripts/` directory contains placeholder scripts for each agent in the workflow. These scripts can be customized and extended to implement the full functionality of the Autonomous Capitalist skill:

- `hunter_agent.py`: Scans for business opportunities
- `analyst_agent.py`: Evaluates opportunities and generates business plans
- `builder_agent.py`: Builds business infrastructure and assets
- `operator_agent.py`: Manages day-to-day business operations
