#!/usr/bin/env python3
"""
SheldonOS — Agent Export Script
Exports all agent definitions as SOUL.md files for OpenClaw.
Run this after adding new agents to agent_loader.py.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.workforce.agency_agents.agent_loader import AgentLoader


def main():
    print("SheldonOS — Exporting agent SOUL.md files...")
    loader = AgentLoader()

    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                               "core", "control_plane", "openclaw", "souls")

    loader.export_soul_files(output_dir)

    agents = loader.to_dict()
    print(f"\nExported {len(agents)} agents to {output_dir}")
    print("\nAgent Roster:")
    print(f"{'Agent ID':<40} {'Company':<10} {'Model':<35} {'Budget':>12}")
    print("-" * 100)
    for agent in agents:
        print(
            f"{agent['agent_id']:<40} "
            f"{agent['company_id']:<10} "
            f"{agent['model']:<35} "
            f"{agent['token_budget']:>12,}"
        )

    print(f"\nTotal agents: {len(agents)}")
    print(f"SOUL.md files written to: {output_dir}")
    print("\nNext step: Restart the OpenClaw gateway to register new agents.")


if __name__ == "__main__":
    main()
