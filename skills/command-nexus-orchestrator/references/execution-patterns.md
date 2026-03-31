# Common Execution Patterns

This document outlines common execution patterns for the master orchestrator.

## Pattern 1: Sequential Execution

**Use Case**: Tasks with direct dependencies.

**Workflow**:
1.  Execute Task A.
2.  Wait for Task A to complete.
3.  Pass the output of Task A as input to Task B.
4.  Execute Task B.

## Pattern 2: Parallel Execution

**Use Case**: Independent tasks that can run concurrently.

**Workflow**:
1.  Identify independent tasks (A, B, C).
2.  Spawn separate agents for each task.
3.  Execute all tasks concurrently.
4.  Aggregate results upon completion.

## Pattern 3: Recursive Decomposition

**Use Case**: Complex tasks that require multiple levels of breakdown.

**Workflow**:
1.  Decompose a high-level task into sub-tasks.
2.  For each sub-task, determine if further decomposition is needed.
3.  If so, recursively apply the decomposition process.
4.  Execute the lowest-level tasks first and bubble up the results.
