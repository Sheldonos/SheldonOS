"""
SheldonOS — Deer-Flow Workflow Orchestrator
Decomposes complex goals from Paperclip into multi-step Directed Acyclic Graphs (DAGs).
Manages long-horizon task execution across multiple agents and companies.
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger("sheldon.workforce.deer_flow")


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowTask:
    """A single node in a Deer-Flow DAG."""
    task_id: str
    name: str
    agent_id: str
    action: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)  # task_ids that must complete first
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 2


@dataclass
class Workflow:
    """A complete Deer-Flow workflow (DAG of tasks)."""
    workflow_id: str
    name: str
    company_id: str
    goal: str
    tasks: Dict[str, WorkflowTask] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class WorkflowOrchestrator:
    """
    The Deer-Flow Workflow Orchestrator.
    Manages the execution of multi-step workflows across the SheldonOS agent workforce.
    """

    def __init__(self, paperclip_url: str = "http://localhost:3100", openclaw_url: str = "http://localhost:3101"):
        self.paperclip_url = paperclip_url
        self.openclaw_url = openclaw_url
        self.active_workflows: Dict[str, Workflow] = {}
        self._task_handlers: Dict[str, Callable] = {}

    def create_workflow(self, name: str, company_id: str, goal: str) -> Workflow:
        """Create a new empty workflow."""
        workflow = Workflow(
            workflow_id=str(uuid.uuid4()),
            name=name,
            company_id=company_id,
            goal=goal,
        )
        self.active_workflows[workflow.workflow_id] = workflow
        logger.info(f"[{company_id}] Created workflow: {name} ({workflow.workflow_id[:8]})")
        return workflow

    def add_task(self, workflow: Workflow, name: str, agent_id: str, action: str,
                 parameters: Dict = None, dependencies: List[str] = None) -> WorkflowTask:
        """Add a task to a workflow DAG."""
        task = WorkflowTask(
            task_id=str(uuid.uuid4()),
            name=name,
            agent_id=agent_id,
            action=action,
            parameters=parameters or {},
            dependencies=dependencies or [],
        )
        workflow.tasks[task.task_id] = task
        return task

    def _get_ready_tasks(self, workflow: Workflow) -> List[WorkflowTask]:
        """Return tasks whose dependencies are all complete and are still pending."""
        ready = []
        for task in workflow.tasks.values():
            if task.status != TaskStatus.PENDING:
                continue
            deps_complete = all(
                workflow.tasks[dep_id].status == TaskStatus.COMPLETE
                for dep_id in task.dependencies
                if dep_id in workflow.tasks
            )
            if deps_complete:
                ready.append(task)
        return ready

    async def execute_workflow(self, workflow: Workflow) -> Dict[str, Any]:
        """Execute a workflow DAG, respecting dependency order."""
        workflow.status = TaskStatus.RUNNING
        logger.info(f"[{workflow.company_id}] Executing workflow: {workflow.name}")

        max_iterations = len(workflow.tasks) * 3  # Safety limit
        iteration = 0

        while iteration < max_iterations:
            iteration += 1
            ready_tasks = self._get_ready_tasks(workflow)

            if not ready_tasks:
                # Check if all tasks are done
                all_done = all(
                    t.status in (TaskStatus.COMPLETE, TaskStatus.FAILED, TaskStatus.SKIPPED)
                    for t in workflow.tasks.values()
                )
                if all_done:
                    break
                # Check for deadlock
                pending = [t for t in workflow.tasks.values() if t.status == TaskStatus.PENDING]
                if pending:
                    logger.error(f"Workflow deadlock detected in {workflow.workflow_id}")
                    workflow.status = TaskStatus.FAILED
                    return {"status": "deadlock", "workflow_id": workflow.workflow_id}
                break

            # Execute ready tasks (can be parallelized)
            await asyncio.gather(*[self._execute_task(workflow, task) for task in ready_tasks])

        # Determine final status
        failed = [t for t in workflow.tasks.values() if t.status == TaskStatus.FAILED]
        workflow.status = TaskStatus.FAILED if failed else TaskStatus.COMPLETE
        workflow.completed_at = datetime.utcnow().isoformat()

        logger.info(
            f"[{workflow.company_id}] Workflow '{workflow.name}' {workflow.status.value} | "
            f"tasks={len(workflow.tasks)} | failed={len(failed)}"
        )

        return {
            "status": workflow.status.value,
            "workflow_id": workflow.workflow_id,
            "tasks_total": len(workflow.tasks),
            "tasks_complete": sum(1 for t in workflow.tasks.values() if t.status == TaskStatus.COMPLETE),
            "tasks_failed": len(failed),
        }

    async def _execute_task(self, workflow: Workflow, task: WorkflowTask):
        """Execute a single task by dispatching it to the appropriate agent via OpenClaw."""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow().isoformat()
        logger.info(f"[{workflow.company_id}] Running task: {task.name} → agent={task.agent_id}")

        try:
            # Inject results from dependency tasks into parameters
            for dep_id in task.dependencies:
                dep_task = workflow.tasks.get(dep_id)
                if dep_task and dep_task.result:
                    task.parameters[f"dep_{dep_id[:8]}"] = dep_task.result

            # Dispatch to agent via OpenClaw
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.openclaw_url}/api/agent/call",
                    json={
                        "agent_id": task.agent_id,
                        "company_id": workflow.company_id,
                        "action": task.action,
                        "parameters": task.parameters,
                        "timeout_seconds": 300,
                    },
                    timeout=320.0,
                )
                result = resp.json()

            task.result = result
            task.status = TaskStatus.COMPLETE
            task.completed_at = datetime.utcnow().isoformat()

            # Report heartbeat to Paperclip
            await self._report_heartbeat(workflow.company_id, task)

        except Exception as e:
            task.error = str(e)
            task.retry_count += 1
            if task.retry_count <= task.max_retries:
                logger.warning(f"Task '{task.name}' failed (attempt {task.retry_count}/{task.max_retries}): {e}")
                task.status = TaskStatus.PENDING  # Will retry
            else:
                logger.error(f"Task '{task.name}' permanently failed after {task.max_retries} retries: {e}")
                task.status = TaskStatus.FAILED

    async def _report_heartbeat(self, company_id: str, task: WorkflowTask):
        """Report task completion heartbeat to Paperclip."""
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{self.paperclip_url}/api/heartbeat",
                    json={
                        "company_id": company_id,
                        "team_id": "deer_flow",
                        "agent_id": task.agent_id,
                        "task_id": task.task_id,
                        "tokens_used": 0,
                        "status": task.status.value,
                        "result": task.result,
                    },
                    timeout=5.0,
                )
        except Exception as e:
            logger.warning(f"Failed to report heartbeat: {e}")


# ─── Pre-built Workflow Templates ─────────────────────────────────────────────
def build_saas_workflow(orchestrator: WorkflowOrchestrator, opportunity: Dict[str, Any]) -> Workflow:
    """Build a complete Micro-SaaS development workflow from an opportunity."""
    wf = orchestrator.create_workflow(
        name=f"SaaS: {opportunity.get('name', 'Unnamed')}",
        company_id="beta",
        goal=opportunity.get("description", "Build and launch a micro-SaaS product"),
    )

    t1 = orchestrator.add_task(wf, "Market Validation", "beta_product_manager", "validate_market",
                                parameters={"opportunity": opportunity})
    t2 = orchestrator.add_task(wf, "Write PRD", "beta_product_manager", "write_prd",
                                dependencies=[t1.task_id])
    t3 = orchestrator.add_task(wf, "Build Backend", "beta_lead_engineer", "build_backend",
                                dependencies=[t2.task_id])
    t4 = orchestrator.add_task(wf, "Build Frontend", "beta_frontend_wizard", "build_frontend",
                                dependencies=[t2.task_id])
    t5 = orchestrator.add_task(wf, "QA Testing", "beta_qa_tester", "run_tests",
                                dependencies=[t3.task_id, t4.task_id])
    t6 = orchestrator.add_task(wf, "Deploy", "beta_lead_engineer", "deploy_to_production",
                                dependencies=[t5.task_id])
    orchestrator.add_task(wf, "Launch Marketing", "beta_growth_marketer", "launch_campaign",
                           dependencies=[t6.task_id])
    return wf


def build_prediction_market_workflow(orchestrator: WorkflowOrchestrator, market_event: Dict[str, Any]) -> Workflow:
    """Build a prediction market analysis and trading workflow."""
    wf = orchestrator.create_workflow(
        name=f"Prediction: {market_event.get('event', 'Market Event')}",
        company_id="alpha",
        goal="Analyze event, simulate outcomes, and execute profitable prediction market trade",
    )

    t1 = orchestrator.add_task(wf, "Ingest Data", "alpha_data_scientist", "ingest_event_data",
                                parameters={"event": market_event})
    t2 = orchestrator.add_task(wf, "Run Simulation", "alpha_simulation_architect", "run_simulation",
                                dependencies=[t1.task_id])
    t3 = orchestrator.add_task(wf, "Analyze Signal", "alpha_quant_analyst", "evaluate_signal",
                                dependencies=[t2.task_id])
    orchestrator.add_task(wf, "Execute Trade", "alpha_execution_trader", "execute_if_approved",
                           dependencies=[t3.task_id])
    return wf
