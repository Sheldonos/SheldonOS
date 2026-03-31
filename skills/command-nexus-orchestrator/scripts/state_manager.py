#!/usr/bin/env python3
import json
import os
import sys

def get_project_path(project_name):
    return os.path.join('/home/ubuntu', project_name)

def get_state_file_path(project_name):
    return os.path.join(get_project_path(project_name), 'state', 'project_state.json')

def read_state(project_name):
    """Reads the current project state."""
    state_file = get_state_file_path(project_name)
    if not os.path.exists(state_file):
        return None
    with open(state_file, 'r') as f:
        return json.load(f)

def write_state(project_name, state):
    """Writes the updated project state."""
    state_file = get_state_file_path(project_name)
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=4)

def update_state(project_name, key, value):
    """Updates a specific key in the project state."""
    state = read_state(project_name)
    if state:
        state[key] = value
        write_state(project_name, state)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python state_manager.py <project_name> <read|write|update> [key] [value_json]")
        sys.exit(1)

    project_name = sys.argv[1]
    action = sys.argv[2]

    if action == 'read':
        state = read_state(project_name)
        if state:
            print(json.dumps(state, indent=4))
    elif action == 'write':
        if len(sys.argv) != 4:
            print("Usage: python state_manager.py <project_name> write <state_json>")
            sys.exit(1)
        new_state = json.loads(sys.argv[3])
        write_state(project_name, new_state)
        print(f"State for project '{project_name}' updated.")
    elif action == 'update':
        if len(sys.argv) != 5:
            print("Usage: python state_manager.py <project_name> update <key> <value_json>")
            sys.exit(1)
        key = sys.argv[3]
        value = json.loads(sys.argv[4])
        update_state(project_name, key, value)
        print(f"State key '{key}' for project '{project_name}' updated.")
    else:
        print(f"Unknown action: {action}")
        sys.exit(1)
