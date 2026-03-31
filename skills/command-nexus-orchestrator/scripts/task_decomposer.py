#!/usr/bin/env python3
import json
import sys

def decompose_task(task_description):
    """Decomposes a high-level task into smaller sub-tasks."""
    # In a real implementation, this would involve more sophisticated logic,
    # potentially calling an LLM or using a rule-based system to break down
    # the task. For this example, we'll use a simple placeholder.
    sub_tasks = [
        f"Sub-task 1 for: {task_description}",
        f"Sub-task 2 for: {task_description}",
        f"Sub-task 3 for: {task_description}",
    ]
    return sub_tasks

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python task_decomposer.py <task_description>")
        sys.exit(1)

    task_description = sys.argv[1]
    sub_tasks = decompose_task(task_description)
    print(json.dumps(sub_tasks, indent=4))
