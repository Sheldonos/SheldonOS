"""
SheldonOS — Deer-Flow Planner Agent v3.0
Replaces the two hardcoded static workflow templates (build_saas_workflow and
build_prediction_market_workflow) with an LLM-driven dynamic DAG generator.

Given any Opportunity, the PlannerAgent:
  1. Evaluates complexity via the Right-Sizing Protocol (ruflo/right_sizer.py)
  2. Calls an LLM to generate a JSON task plan tailored to that opportunity
  3. Constructs a Workflow DAG from the plan and returns it ready for execution

This means SheldonOS can handle any opportunity category — bug bounties,
DeFi arbitrage, content creation, API wrappers — without a human ever writing
a new workflow template.

Reference: Blueprint §3.2 — Level 2, Dynamic Workflow Planning (Deer-Flow v3.0)
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger("sheldon.workforce.planner")

# ─── Agent Roster (used to constrain the planner's output) ───────────────────
# This list is kept in sync with AGENTS.md. The planner must only reference
# agents that exist in the roster.
_DEFAULT_AGENT_ROSTER = [
    # Alpha — Prediction Markets & Quant
    "alpha_data_scientist",
    "alpha_simulation_architect",
    "alpha_quant_analyst",
    "alpha_execution_trader",
    "alpha_market_monitor",
    # Beta — Micro-SaaS Development
    "beta_product_manager",
    "beta_lead_engineer",
    "beta_frontend_wizard",
    "beta_qa_tester",
    "beta_growth_marketer",
    # Gamma — Bug Bounty & Security
    "gamma_lead_pentester",
    "gamma_exploit_developer",
    "gamma_report_writer",
    # Delta — Research & IP
    "delta_research_analyst",
    "delta_ip_strategist",
    "delta_content_publisher",
    # Epsilon — Opportunity Sensing
    "epsilon_scout",
    "epsilon_signal_analyst",
]


class PlannerAgent:
    """
    Dynamically generates a Workflow DAG for any Opportunity using an LLM.

    Usage:
        planner = PlannerAgent()
        workflow = await planner.plan(opportunity, orchestrator)
        await orchestrator.execute(workflow)
    """

    PLANNER_SYSTEM_PROMPT = """
You are the SheldonOS Workflow Planner. Your job is to decompose an opportunity
into a precise, efficient multi-step workflow that the SheldonOS agent workforce
can execute autonomously.

Given an opportunity description and category, output a JSON object with a
single key "tasks" containing an array of task objects. Each task must have:

  - name        : human-readable task name (string)
  - agent_id    : the agent from the roster best suited for this task (string)
  - action      : the specific action verb for the agent (string, snake_case)
  - parameters  : a dict of inputs for the agent (object, may be empty)
  - dependencies: list of task *names* this task depends on (array of strings,
                  empty list for tasks with no prerequisites)

Rules:
  - Only use agents from the provided roster. Do not invent new agents.
  - Maximize parallelism: tasks with no dependency on each other should have
    empty dependency lists so they can run concurrently.
  - Minimize unnecessary tasks: include only what is strictly needed.
  - The final task must always be an output/delivery task (e.g., deploy,
    submit_report, publish, execute_trade).
  - For bug bounty opportunities, always include a scope validation task first.
  - For prediction market opportunities, always include a simulation task.
  - For SaaS opportunities, always include a market validation task first.

Available agents: {agent_roster}
"""

    def __init__(self) -> None:
        from core.llm.llm_provider import get_llm_provider, LLMConfig, LLMMessage
        self.llm = get_llm_provider()
        self.LLMConfig = LLMConfig
        self.LLMMessage = LLMMessage
        self._agent_roster: List[str] = _DEFAULT_AGENT_ROSTER

    async def plan(self, opportunity: Any, orchestrator: Any) -> Any:
        """
        Generate a dynamic Workflow DAG for the given opportunity.

        Args:
            opportunity: An Opportunity dataclass instance from sheldon_orchestrator.py
            orchestrator: A WorkflowOrchestrator instance used to build the Workflow

        Returns:
            A Workflow instance ready for execution via orchestrator.execute()
        """
        from core.workforce.deer_flow.workflow_orchestrator import Workflow

        logger.info(
            f"[Planner] Planning workflow for: {opportunity.title[:60]} "
            f"(category={opportunity.category})"
        )

        # ── Step 1: Right-size the workflow ──────────────────────────────────
        sizing = await self._right_size(opportunity)
        logger.info(
            f"[Planner] Complexity={sizing.get('complexity_score', '?')}/10 | "
            f"team_size={sizing.get('recommended_team_size', '?')} | "
            f"parallel_tasks={len(sizing.get('parallelizable_subtasks', []))}"
        )

        # ── Step 2: Generate the task plan via LLM ───────────────────────────
        task_plan = await self._generate_plan(opportunity, sizing)

        # ── Step 3: Build the Workflow DAG ───────────────────────────────────
        workflow = self._build_workflow_from_plan(task_plan, opportunity, orchestrator)

        logger.info(
            f"[Planner] Generated workflow '{workflow.name}' with "
            f"{len(workflow.tasks)} tasks"
        )
        return workflow

    async def _right_size(self, opportunity: Any) -> Dict[str, Any]:
        """
        Delegate to the Right-Sizer for complexity evaluation.
        Falls back to a sensible default if the right-sizer is unavailable.
        """
        try:
            from core.workforce.ruflo.right_sizer import RightSizer
            sizer = RightSizer()
            return await sizer.evaluate(opportunity)
        except Exception as e:
            logger.warning(f"[Planner] Right-sizer unavailable, using defaults: {e}")
            return {
                "complexity_score": 5,
                "recommended_team_size": 3,
                "parallelizable_subtasks": [],
                "sequential_subtasks": [],
                "estimated_token_budget": 50000,
            }

    async def _generate_plan(
        self, opportunity: Any, sizing: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Call the LLM to generate a JSON task plan for the opportunity.
        Returns a list of task dicts on success, or a safe fallback plan on error.
        """
        roster_str = "\n".join(f"  - {a}" for a in self._agent_roster)
        system_prompt = self.PLANNER_SYSTEM_PROMPT.format(agent_roster=roster_str)

        user_message = (
            f"Opportunity Title: {opportunity.title}\n"
            f"Category: {opportunity.category}\n"
            f"Description: {opportunity.description[:800]}\n"
            f"Estimated Revenue: ${getattr(opportunity, 'estimated_revenue_usd', 0):.0f}\n"
            f"Complexity Score: {sizing.get('complexity_score', 5)}/10\n"
            f"Recommended Team Size: {sizing.get('recommended_team_size', 3)}\n\n"
            f"Generate the optimal workflow task plan for this opportunity."
        )

        model = os.getenv("DEFAULT_AGENT_MODEL", "claude-3-5-sonnet-20241022")

        try:
            response = await self.llm.complete(
                messages=[self.LLMMessage(role="user", content=user_message)],
                config=self.LLMConfig(
                    model=model,
                    max_tokens=2048,
                    system_prompt=system_prompt,
                ),
            )

            # Parse JSON from response
            content = response.content.strip()
            # Strip markdown code fences if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()

            plan_data = json.loads(content)
            tasks = plan_data.get("tasks", [])

            if not tasks:
                logger.warning("[Planner] LLM returned empty task list — using fallback")
                return self._fallback_plan(opportunity)

            logger.info(f"[Planner] LLM generated {len(tasks)}-task plan")
            return tasks

        except json.JSONDecodeError as e:
            logger.error(f"[Planner] JSON parse error in LLM plan: {e}")
            return self._fallback_plan(opportunity)
        except Exception as e:
            logger.error(f"[Planner] Plan generation failed: {e}")
            return self._fallback_plan(opportunity)

    def _build_workflow_from_plan(
        self,
        task_plan: List[Dict[str, Any]],
        opportunity: Any,
        orchestrator: Any,
    ) -> Any:
        """
        Convert a list of task dicts into a Workflow DAG.
        Resolves dependency names to task_ids for correct DAG wiring.
        """
        workflow = orchestrator.create_workflow(
            name=f"[v3.0] {opportunity.category.upper()}: {opportunity.title[:50]}",
            company_id=self._infer_company(opportunity.category),
            goal=opportunity.description[:200],
        )

        # First pass: create all tasks and build name→task_id map
        name_to_id: Dict[str, str] = {}
        task_objects = []
        for task_def in task_plan:
            task = orchestrator.add_task(
                workflow=workflow,
                name=task_def.get("name", "Unnamed Task"),
                agent_id=task_def.get("agent_id", "epsilon_scout"),
                action=task_def.get("action", "execute"),
                parameters={
                    **task_def.get("parameters", {}),
                    "_opportunity_id": getattr(opportunity, "opportunity_id", ""),
                    "_opportunity_title": opportunity.title,
                },
                dependencies=[],  # Wire dependencies in second pass
            )
            name_to_id[task_def.get("name", "")] = task.task_id
            task_objects.append((task, task_def.get("dependencies", [])))

        # Second pass: resolve dependency names to task_ids
        for task, dep_names in task_objects:
            resolved_deps = []
            for dep_name in dep_names:
                dep_id = name_to_id.get(dep_name)
                if dep_id:
                    resolved_deps.append(dep_id)
                else:
                    logger.warning(
                        f"[Planner] Dependency '{dep_name}' not found for task "
                        f"'{task.name}' — skipping"
                    )
            task.dependencies = resolved_deps

        return workflow

    def _fallback_plan(self, opportunity: Any) -> List[Dict[str, Any]]:
        """
        Minimal safe fallback plan used when LLM plan generation fails.
        Routes to the most appropriate agent based on opportunity category.
        """
        category_to_agent = {
            "prediction_market": ("alpha_quant_analyst", "analyze_and_trade"),
            "bug_bounty": ("gamma_lead_pentester", "assess_and_report"),
            "saas": ("beta_product_manager", "validate_and_plan"),
            "research": ("delta_research_analyst", "research_and_publish"),
            "arbitrage": ("alpha_execution_trader", "evaluate_and_execute"),
        }
        agent_id, action = category_to_agent.get(
            opportunity.category, ("epsilon_scout", "investigate")
        )
        return [
            {
                "name": f"Execute {opportunity.category} opportunity",
                "agent_id": agent_id,
                "action": action,
                "parameters": {"opportunity": opportunity.description[:300]},
                "dependencies": [],
            }
        ]

    @staticmethod
    def _infer_company(category: str) -> str:
        """Map opportunity category to the responsible SheldonOS company."""
        return {
            "prediction_market": "alpha",
            "arbitrage": "alpha",
            "saas": "beta",
            "bug_bounty": "gamma",
            "research": "delta",
        }.get(category, "beta")
