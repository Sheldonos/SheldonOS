---
name: agent-lifecycle-manager
description: Automate the complete lifecycle of sub-agents, including creation, training, deployment, retraining, and decommissioning. Use when managing autonomous agents, building agentic systems, or optimizing agent workforce for day-to-day operations.
---

# Agent Lifecycle Manager

## Overview

This skill automates the entire lifecycle of autonomous sub-agents, from creation to decommissioning. It ensures your agentic workforce remains dynamic, adaptive, and continuously optimized for performance. Effective lifecycle management is critical for maintaining a healthy and efficient agent ecosystem.

## Core Lifecycle Stages

1. **Creation**: Spawn new agents in response to new tasks or changing workloads
2. **Training**: Equip agents with necessary skills, knowledge, and context
3. **Deployment**: Assign trained agents to specific tasks and integrate them into the workforce
4. **Retraining**: Continuously adapt agents to new information and requirements
5. **Decommissioning**: Gracefully remove agents when tasks are complete or they become obsolete

## Workflow: Automated Agent Lifecycle Management

### Step 1: Agent Creation

Automate agent creation using pre-defined templates. Each template specifies the agent's role, capabilities, and resource requirements.

**Triggers for Creation:**
- New projects requiring specialized capabilities
- Increased workload exceeding current agent capacity
- Need for specialized skills not present in current workforce

**Implementation:**
- Create a library of agent templates for common roles (data analyst, content creator, code developer, researcher)
- Use the `map` tool to spawn multiple agents in parallel when needed
- Define clear role specifications including required capabilities and expected outputs

### Step 2: Automated Training and Onboarding

Implement an automated training pipeline for new agents:

**Skill Ingestion:**
- Provide agents with relevant skills from `/home/ubuntu/skills/` directory
- Include skill references in agent prompts to ensure they follow established workflows
- Create custom skills for specialized agent roles using the `skill-creator` skill

**Knowledge Base Access:**
- Provide agents with comprehensive knowledge bases of relevant information
- Use file paths in `map` tool inputs to pass documentation and reference materials
- Structure knowledge as markdown files for easy agent consumption

**Simulated Environments:**
- Test agents in controlled settings before live deployment
- Use sample data and test cases to validate agent performance
- Iterate on agent configuration based on test results

### Step 3: Dynamic Deployment and Task Assignment

Deploy agents dynamically to maximize efficiency:

**Task Assignment:**
- Use the `map` tool for parallel task distribution across multiple agents
- Match agent capabilities to task requirements
- Ensure clear output schemas for consistent agent deliverables

**Integration:**
- Seamlessly integrate new agents into existing workflows
- Provide agents with context about related agents and dependencies
- Monitor initial performance and adjust as needed

### Step 4: Continuous Performance Monitoring and Retraining

Track and improve agent performance continuously:

**Performance Monitoring:**
- Review agent outputs for quality, accuracy, and consistency
- Track completion rates and error patterns
- Identify agents that require retraining or optimization

**Retraining Triggers:**
- Performance falls below acceptable thresholds
- New information or requirements emerge
- User feedback indicates issues with agent outputs

**Feedback Loops:**
- Use agent output as training data for improvement
- Refine prompts and instructions based on observed behavior
- Update skills and knowledge bases to address common issues

### Step 5: Automated Decommissioning

Conserve resources by removing unnecessary agents:

**Triggers for Decommissioning:**
- Task completion with no future need for the agent
- Agent becomes obsolete due to changing requirements
- Chronic underperformance despite retraining efforts

**Resource Management:**
- Agents in `map` tool automatically terminate after task completion
- No manual cleanup required for parallel subtasks
- Focus resources on active, productive agents

## Best Practices

### Resource Management
- Monitor total agent count and computational requirements
- Use parallel processing judiciously to avoid overwhelming the system
- Balance agent specialization with resource efficiency

### Version Control for Agents
- Track changes to agent templates and configurations
- Document successful agent patterns for reuse
- Maintain history of prompt refinements and their impacts

### Security
- Ensure agent creation follows proper authorization
- Validate agent outputs before using in production systems
- Implement safeguards against unauthorized agent modification

### Audit Trails
- Maintain detailed logs of agent lifecycle events
- Document reasons for agent creation and decommissioning
- Track performance metrics for continuous improvement

## Integration with Other Skills

This skill works best when combined with:
- **skill-creator**: Create specialized skills for agent roles
- **Parallel processing (`map` tool)**: Deploy multiple agents simultaneously
- **File management**: Organize agent knowledge bases and outputs

## Example: Creating a Research Agent Fleet

```
1. Creation: Spawn 10 research agents using `map` tool
2. Training: Provide each agent with research methodology skill and domain knowledge
3. Deployment: Assign each agent a specific research topic
4. Monitoring: Review outputs for quality and completeness
5. Retraining: Update prompts for agents that missed key information
6. Decommissioning: Agents automatically terminate after delivering results
```

## Notes

- Agents spawned via `map` tool operate in isolated sandboxes
- Files must be explicitly passed between agents using absolute paths
- Output schemas ensure consistent agent deliverables
- Agent lifecycle is optimized for task-based execution rather than persistent services
