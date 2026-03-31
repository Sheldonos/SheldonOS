---
name: master-orchestrator
description: Autonomously manages complex, multi-stage enterprise projects from start to finish. Use this skill to orchestrate other enterprise skills, manage project state, and execute a project plan with minimal user intervention.
---

# Master Orchestrator

This skill enables Manus to act as an autonomous project manager, orchestrating the full lifecycle of a complex enterprise project. It leverages a suite of specialized enterprise skills to execute the project plan with minimal human oversight.

## Core Principles

- **Autonomy**: The orchestrator is designed to make decisions, manage resources, and drive the project to completion independently.
- **Hierarchy**: It uses a hierarchical model, delegating tasks to specialized sub-agents and skills.
- **Persistence**: All project state is saved to disk, allowing for long-running, asynchronous execution and recovery.
- **Adaptability**: The orchestrator can adjust its plan based on real-time feedback and changing conditions.

## Project Workflow

Follow this workflow to manage a project using the Master Orchestrator skill.

### 1. Project Initialization

At the start of a new project, you must initialize the project environment.

1.  **Get Project Name**: Ask the user for a short, descriptive name for the project (e.g., `project-lemos`).
2.  **Initialize Directory**: Run the `init_project.py` script to create the project directory structure.

    ```bash
    python3 /home/ubuntu/skills/master-orchestrator/scripts/init_project.py <project_name>
    ```

3.  **Load Requirements**: Read the user's project requirements file and save it to the project's root directory.

### 2. Planning and Decomposition

Once the project is initialized, create a detailed execution plan.

1.  **Decompose Project**: Read the project requirements and use the `task_decomposer.py` script to break down the high-level objectives into a series of actionable tasks. This may be an iterative process.

    ```bash
    python3 /home/ubuntu/skills/master-orchestrator/scripts/task_decomposer.py "<A high-level objective from the requirements>"
    ```

2.  **Route Tasks to Skills**: For each task, determine the appropriate category (e.g., `strategic`, `development`) and use the `skill_router.py` script to identify the correct enterprise skill to use. Refer to `/home/ubuntu/skills/master-orchestrator/references/skill-mapping.md` for guidance.

    ```bash
    python3 /home/ubuntu/skills/master-orchestrator/scripts/skill_router.py <task_category>
    ```

3.  **Create Execution Plan**: Create a Markdown file named `execution_plan.md` in the project directory. This file should list all tasks, their assigned skills, dependencies, and estimated completion times.

4.  **Update State**: Use the `state_manager.py` script to record the initial plan in the project's state file.

    ```bash
    python3 /home/ubuntu/skills/master-orchestrator/scripts/state_manager.py <project_name> update 'phases' "$(cat execution_plan.md)"
    ```

### 3. Execution

Execute the plan task by task, updating the state as you go.

1.  **Execute Tasks**: For each task in the `execution_plan.md`, invoke the designated enterprise skill. Pass all necessary context and inputs.
2.  **Update State on Completion**: After each task is completed, update the project state using `state_manager.py` to mark the task as complete and record the path to any deliverables.

    ```bash
    python3 /home/ubuntu/skills/master-orchestrator/scripts/state_manager.py <project_name> update 'completedTasks' '["task_name"]'
    ```

3.  **Log Decisions**: Keep a detailed log of all actions taken and decisions made in a file named `project_log.md`.

### 4. Completion and Delivery

Once all tasks are complete, finalize the project and deliver the results.

1.  **Validate Deliverables**: Review all deliverables to ensure they meet the project requirements.
2.  **Generate Final Report**: Create a `final_report.md` summarizing the project, its outcomes, and key decisions made.
3.  **Package Deliverables**: Create a zip archive of the `deliverables` directory.
4.  **Notify User**: Use the `message` tool to inform the user that the project is complete and provide the final report and the deliverables archive as attachments.

## Bundled Resources

This skill includes the following resources to aid in project orchestration:

### `scripts/`

-   `init_project.py`: Initializes the project directory structure.
-   `state_manager.py`: Reads, writes, and updates the project's JSON state file.
-   `task_decomposer.py`: A placeholder for a more advanced task decomposition logic.
-   `skill_router.py`: Maps task categories to the appropriate enterprise skills.

### `references/`

-   `skill-mapping.md`: A guide for mapping task categories to skills.
-   `execution-patterns.md`: Describes common workflow patterns like sequential and parallel execution.

### `templates/`

-   `project-state.json`: The template for the project's state file.
