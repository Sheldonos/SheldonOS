#!/usr/bin/env python3
"""
generate_architecture_data.py
Generates the architecture data JSON for the IBM Solution Designer web app
from a structured use case description.

Usage:
    python generate_architecture_data.py --company "Tractor Supply" \
        --use-case "Unified Carrier Tracking Hub" \
        --services "Tracking Dashboard,API Gateway,Carrier Integration Service,Tracking Service,Event Bus (Kafka),Config DB (PostgreSQL),Tracking DB (MongoDB),Notification Service" \
        --external "FedEx API,UPS Portal,Roadie API,LTL Carriers,Order Management System,Customer Notification Channels" \
        --output architecture_data.json
"""

import argparse
import json
import sys

# Canvas layout constants
CANVAS_WIDTH = 1400
CANVAS_HEIGHT = 900

def build_architecture(company: str, use_case: str, services: list[str], externals: list[str]) -> dict:
    """Build the full architecture data structure for the web app."""

    # Auto-assign positions in a hub-and-spoke layout
    # Center: core processing services
    # Left: use cases / actors
    # Right: downstream services
    # Bottom: data stores
    # Top: external systems

    nodes = []
    edges = []

    # Use case nodes (left side)
    use_cases = [
        {"label": "Real-Time Tracking", "desc": f"As a customer, I want to track my shipment in real time."},
        {"label": "Exception Management", "desc": f"As a logistics manager, I need to see all delayed shipments across all carriers in one place."},
    ]
    for i, uc in enumerate(use_cases):
        nodes.append({
            "id": f"uc-{i}",
            "type": "usecase",
            "label": uc["label"],
            "description": uc["desc"],
            "tech": [],
            "x": 60,
            "y": 140 + i * 200,
            "width": 220,
            "height": 120
        })

    # Risk node
    nodes.append({
        "id": "risk-0",
        "type": "risk",
        "label": "Carrier API Rate Limits",
        "description": "Polling-based carriers may throttle requests at peak season. Requires exponential backoff.",
        "tech": ["Functional Risk"],
        "x": 60,
        "y": 560,
        "width": 220,
        "height": 110
    })

    # Determine tech stacks by service name heuristics
    def infer_tech(name: str) -> list[str]:
        n = name.lower()
        if "dashboard" in n or "frontend" in n or "ui" in n: return ["React", "TypeScript", "Vite"]
        if "gateway" in n: return ["Node.js", "k8s"]
        if "integration" in n or "carrier" in n: return ["Node.js", "k8s"]
        if "kafka" in n or "event" in n or "bus" in n: return ["Kafka", "k8s"]
        if "postgres" in n or "sql" in n or "config" in n: return ["PostgreSQL", "k8s"]
        if "mongo" in n or "nosql" in n: return ["MongoDB", "k8s"]
        if "notification" in n: return ["Node.js", "k8s"]
        if "tracking service" in n: return ["Java", "k8s"]
        return ["Node.js", "k8s"]

    def infer_icon(name: str) -> str:
        n = name.lower()
        if "dashboard" in n or "ui" in n: return "monitor"
        if "gateway" in n: return "gateway"
        if "kafka" in n or "event" in n: return "lightning"
        if "postgres" in n or "sql" in n: return "database"
        if "mongo" in n: return "database"
        if "notification" in n: return "notification"
        return "service"

    # Layout: arrange services in a grid on the right/center
    service_positions = [
        (700, 80),   # top center
        (700, 260),  # center
        (480, 420),  # center-left
        (700, 420),  # center
        (920, 420),  # center-right
        (480, 620),  # bottom-left
        (700, 620),  # bottom-center
        (920, 620),  # bottom-right
    ]

    for i, svc in enumerate(services):
        x, y = service_positions[i] if i < len(service_positions) else (600 + (i % 3) * 220, 200 + (i // 3) * 200)
        nodes.append({
            "id": f"svc-{i}",
            "type": "container",
            "label": svc,
            "description": f"Handles {svc.lower()} responsibilities for the {use_case}.",
            "tech": infer_tech(svc),
            "icon": infer_icon(svc),
            "x": x,
            "y": y,
            "width": 200,
            "height": 120
        })

    # External system nodes (far right)
    for i, ext in enumerate(externals):
        nodes.append({
            "id": f"ext-{i}",
            "type": "external",
            "label": ext,
            "description": f"External system: {ext}",
            "tech": ["External"],
            "x": 1160,
            "y": 60 + i * 130,
            "width": 180,
            "height": 90
        })

    # Auto-generate edges: use cases → first service, services → each other in sequence
    if len(services) >= 2:
        edges.append({"from": "uc-0", "to": "svc-0", "label": "use", "style": "dashed"})
        edges.append({"from": "uc-1", "to": "svc-1", "label": "use", "style": "dashed"})
        # Core flow edges
        edges.append({"from": "svc-0", "to": "svc-1", "label": "REST/HTTPS", "style": "solid"})
        if len(services) >= 3:
            edges.append({"from": "svc-1", "to": "svc-2", "label": "route", "style": "solid"})
        if len(services) >= 4:
            edges.append({"from": "svc-1", "to": "svc-3", "label": "route", "style": "solid"})
        if len(services) >= 5:
            edges.append({"from": "svc-2", "to": "svc-4", "label": "publish events", "style": "solid"})
            edges.append({"from": "svc-3", "to": "svc-4", "label": "consume events", "style": "solid"})
        if len(services) >= 6:
            edges.append({"from": "svc-2", "to": "svc-5", "label": "stores config", "style": "solid"})
        if len(services) >= 7:
            edges.append({"from": "svc-3", "to": "svc-6", "label": "persists events", "style": "solid"})
        if len(services) >= 8:
            edges.append({"from": "svc-4", "to": "svc-7", "label": "triggers", "style": "solid"})

    # External edges
    for i in range(min(len(externals), 4)):
        edges.append({"from": "svc-2", "to": f"ext-{i}", "label": "webhook / poll", "style": "dashed"})

    return {
        "project": {
            "name": use_case,
            "company": company,
            "branch": f"{company.lower().replace(' ', '-')}-v1",
            "acronym": "".join(w[0].upper() for w in use_case.split()[:3])
        },
        "nodes": nodes,
        "edges": edges
    }


def main():
    parser = argparse.ArgumentParser(description="Generate IBM Solution Designer architecture data")
    parser.add_argument("--company", required=True, help="Company name")
    parser.add_argument("--use-case", required=True, help="Use case name")
    parser.add_argument("--services", required=True, help="Comma-separated list of service/container names")
    parser.add_argument("--external", required=True, help="Comma-separated list of external systems")
    parser.add_argument("--output", default="architecture_data.json", help="Output JSON file path")
    args = parser.parse_args()

    services = [s.strip() for s in args.services.split(",")]
    externals = [e.strip() for e in args.external.split(",")]

    data = build_architecture(args.company, args.use_case, services, externals)

    with open(args.output, "w") as f:
        json.dump(data, f, indent=2)

    print(f"✅ Architecture data written to {args.output}")
    print(f"   {len(data['nodes'])} nodes, {len(data['edges'])} edges")
    print(f"   Project: {data['project']['name']} ({data['project']['acronym']})")


if __name__ == "__main__":
    main()
