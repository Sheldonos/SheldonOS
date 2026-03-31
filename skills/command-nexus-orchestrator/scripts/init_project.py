#/usr/bin/env python3
import os
import json
import sys

def init_project(project_name):
    """Initializes the project directory structure."""
    project_path = os.path.join('/home/ubuntu', project_name)
    os.makedirs(project_path, exist_ok=True)

    # Create subdirectories
    os.makedirs(os.path.join(project_path, 'deliverables'), exist_ok=True)
    os.makedirs(os.path.join(project_path, 'logs'), exist_ok=True)
    os.makedirs(os.path.join(project_path, 'state'), exist_ok=True)

    # Create initial state file
    state_file = os.path.join(project_path, 'state', 'project_state.json')
    if not os.path.exists(state_file):
        with open(state_file, 'w') as f:
            json.dump({'project_name': project_name, 'status': 'initialized', 'phases': {}}, f, indent=4)

    print(f"Project '{project_name}' initialized at {project_path}")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python init_project.py <project_name>")
        sys.exit(1)
    project_name = sys.argv[1]
    init_project(project_name)
