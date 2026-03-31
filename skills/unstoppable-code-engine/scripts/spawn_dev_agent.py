#!/usr/bin/env python3
"""
Spawn Development Sub-Agent Script

This script helps create well-structured prompts for spawning specialized
development sub-agents using the `map` tool. It generates prompts that
include clear objectives, success criteria, and integration requirements.

Usage:
    python3 spawn_dev_agent.py <agent_type> <project_context>

Agent Types:
    - frontend: Frontend developer (React, UI/UX, client-side logic)
    - backend: Backend developer (API, business logic, database)
    - database: Database engineer (schema, migrations, queries)
    - testing: Test engineer (test suites, validation, QA)
    - devops: DevOps engineer (deployment, CI/CD, infrastructure)
    - fullstack: Full-stack developer (end-to-end feature implementation)

Example:
    python3 spawn_dev_agent.py frontend "Build a task management dashboard"
"""

import sys
import json

AGENT_TEMPLATES = {
    "frontend": {
        "title": "Frontend Developer",
        "description": "Specializes in user interface, user experience, and client-side logic",
        "responsibilities": [
            "Implement responsive UI components",
            "Handle client-side state management",
            "Integrate with backend APIs",
            "Ensure cross-browser compatibility",
            "Implement loading states and error handling"
        ],
        "tech_stack": ["React", "TypeScript", "TailwindCSS", "Vite"],
        "deliverables": [
            "Working UI components",
            "API integration code",
            "Responsive design implementation",
            "Client-side validation"
        ]
    },
    "backend": {
        "title": "Backend Developer",
        "description": "Specializes in server-side logic, APIs, and business logic",
        "responsibilities": [
            "Design and implement REST/GraphQL APIs",
            "Implement business logic and validation",
            "Handle authentication and authorization",
            "Integrate with databases and external services",
            "Implement error handling and logging"
        ],
        "tech_stack": ["Node.js", "Express", "TypeScript", "JWT"],
        "deliverables": [
            "API endpoints with documentation",
            "Business logic implementation",
            "Authentication middleware",
            "Database integration code"
        ]
    },
    "database": {
        "title": "Database Engineer",
        "description": "Specializes in database design, optimization, and data management",
        "responsibilities": [
            "Design database schema",
            "Write migration scripts",
            "Optimize queries for performance",
            "Implement data validation constraints",
            "Create seed data for testing"
        ],
        "tech_stack": ["PostgreSQL", "MySQL", "Drizzle ORM", "SQL"],
        "deliverables": [
            "Database schema design",
            "Migration scripts",
            "Optimized queries",
            "Seed data scripts"
        ]
    },
    "testing": {
        "title": "Test Engineer",
        "description": "Specializes in testing, quality assurance, and validation",
        "responsibilities": [
            "Write unit tests for core functionality",
            "Create integration tests",
            "Implement end-to-end test scenarios",
            "Validate edge cases and error handling",
            "Set up test automation"
        ],
        "tech_stack": ["Jest", "Pytest", "Cypress", "Testing Library"],
        "deliverables": [
            "Comprehensive test suite",
            "Test coverage report",
            "Integration test scenarios",
            "Test automation scripts"
        ]
    },
    "devops": {
        "title": "DevOps Engineer",
        "description": "Specializes in deployment, infrastructure, and CI/CD",
        "responsibilities": [
            "Set up deployment pipeline",
            "Configure production environment",
            "Implement monitoring and logging",
            "Set up CI/CD automation",
            "Ensure security and scalability"
        ],
        "tech_stack": ["Docker", "GitHub Actions", "Nginx", "Cloud platforms"],
        "deliverables": [
            "Deployment scripts",
            "CI/CD configuration",
            "Infrastructure as code",
            "Monitoring setup"
        ]
    },
    "fullstack": {
        "title": "Full-Stack Developer",
        "description": "Specializes in end-to-end feature implementation",
        "responsibilities": [
            "Implement complete features from UI to database",
            "Ensure frontend and backend integration",
            "Handle data flow and state management",
            "Implement comprehensive error handling",
            "Create end-to-end tests"
        ],
        "tech_stack": ["React", "Node.js", "TypeScript", "Database"],
        "deliverables": [
            "Complete working feature",
            "Frontend and backend code",
            "Database integration",
            "End-to-end tests"
        ]
    }
}

def generate_agent_prompt(agent_type: str, project_context: str) -> str:
    """Generate a structured prompt for spawning a development sub-agent."""
    
    if agent_type not in AGENT_TEMPLATES:
        raise ValueError(f"Unknown agent type: {agent_type}. Valid types: {', '.join(AGENT_TEMPLATES.keys())}")
    
    template = AGENT_TEMPLATES[agent_type]
    
    prompt = f"""You are a specialized {template['title']} working on the following project:

{project_context}

## Your Role
{template['description']}

## Your Responsibilities
{chr(10).join(f"- {resp}" for resp in template['responsibilities'])}

## Recommended Tech Stack
{', '.join(template['tech_stack'])}

## Expected Deliverables
{chr(10).join(f"- {deliv}" for deliv in template['deliverables'])}

## Success Criteria
Your work is complete when:
1. All deliverables are implemented and working
2. Code is clean, well-documented, and follows best practices
3. All functionality has been tested
4. Integration points are clearly defined and documented
5. You can demonstrate the working implementation

## Integration Requirements
Ensure your work integrates seamlessly with other components:
- Define clear interfaces (APIs, function signatures, data formats)
- Document all integration points
- Provide examples of how to use your components
- Handle errors gracefully at integration boundaries

## Quality Standards
- Write production-ready code
- Include error handling and validation
- Add comments for non-obvious logic
- Follow consistent code style
- Test all major code paths

Begin implementation now. Focus on delivering a complete, working solution.
"""
    
    return prompt

def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    
    agent_type = sys.argv[1].lower()
    project_context = sys.argv[2]
    
    try:
        prompt = generate_agent_prompt(agent_type, project_context)
        print(prompt)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
