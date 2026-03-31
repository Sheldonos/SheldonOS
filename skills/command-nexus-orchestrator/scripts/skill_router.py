#!/usr/bin/env python3
import json
import sys

SKILL_MAPPING = {
    "strategic": [
        "Psychopolitical Campaign Manager",
        "Strategic Foresight",
        "LemosOS Strategy Playbook",
    ],
    "development": ["Full-Stack App Developer", "Greenlight"],
    "legal": ["Legal System Navigator", "Patent Fortress Strategist"],
    "architecture": ["Agentic Systems Architect", "Enterprise Architect"],
    "management": ["Agent Lifecycle Manager"],
}

def route_task(task_category):
    """Routes a task to the appropriate skill(s)."""
    return SKILL_MAPPING.get(task_category, [])

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python skill_router.py <task_category>")
        sys.exit(1)

    task_category = sys.argv[1]
    skills = route_task(task_category)
    print(json.dumps(skills, indent=4))
