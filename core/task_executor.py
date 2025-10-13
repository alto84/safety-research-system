"""Task executor for managing worker agent execution."""
import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

from models.task import Task, TaskStatus, TaskType
from core.llm_integration import ThoughtPipeExecutor, get_reasoning_cache


logger = logging.getLogger(__name__)


class TaskExecutor:
    """
    Manages execution of tasks by worker agents.

    This class handles:
    - Assignment of tasks to appropriate worker agents
    - Execution orchestration
    - Output capture
    - Error handling and timeout management
    """

    def __init__(self, worker_registry: Optional[Dict[str, Any]] = None, enable_intelligent_routing: bool = True):
        """
        Initialize the task executor.

        Args:
            worker_registry: Dictionary mapping TaskType to worker agent instances
            enable_intelligent_routing: If True, use LLM-driven agent selection; if False, use hard-coded routing
        """
        self.worker_registry = worker_registry or {}
        self.active_tasks: Dict[str, Task] = {}
        self.enable_intelligent_routing = enable_intelligent_routing
        self.thought_pipe = ThoughtPipeExecutor() if enable_intelligent_routing else None
        self.reasoning_cache = get_reasoning_cache() if enable_intelligent_routing else None

    def register_worker(self, task_type: TaskType, worker_agent: Any) -> None:
        """
        Register a worker agent for a specific task type.

        Args:
            task_type: Type of task this worker handles
            worker_agent: Worker agent instance
        """
        self.worker_registry[task_type] = worker_agent
        logger.info(f"Registered worker for task type: {task_type.value}")

    def execute_task(self, task: Task, case_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a task using the appropriate worker agent.

        With intelligent routing enabled, this uses LLM reasoning to select the best
        agent(s) based on task and case characteristics, rather than rigid TaskType mapping.

        Args:
            task: Task to execute
            case_context: Optional case context for intelligent routing

        Returns:
            Dictionary containing task output

        Raises:
            ValueError: If no worker registered for task type
            Exception: If task execution fails
        """
        # Determine which agent(s) should handle this task
        if self.enable_intelligent_routing and case_context:
            try:
                agent_to_use = self._intelligent_route_task(task, case_context)
                logger.info(f"Intelligent routing selected agent: {agent_to_use}")
            except Exception as e:
                logger.warning(f"Intelligent routing failed: {e}. Falling back to hard-coded routing.")
                agent_to_use = None
        else:
            agent_to_use = None

        # Fall back to hard-coded routing if intelligent routing disabled or failed
        if agent_to_use is None:
            if task.task_type not in self.worker_registry:
                raise ValueError(f"No worker registered for task type: {task.task_type.value}")
            agent_to_use = self.worker_registry[task.task_type]

        logger.info(f"Executing task {task.task_id} of type {task.task_type.value}")

        # Update task status
        task.update_status(TaskStatus.IN_PROGRESS)
        task.assigned_agent = agent_to_use.__class__.__name__
        self.active_tasks[task.task_id] = task

        try:
            # Execute using selected agent
            worker = agent_to_use

            # Execute the task
            start_time = datetime.utcnow()
            output = worker.execute(task.input_data)
            execution_time = (datetime.utcnow() - start_time).total_seconds()

            # Store output in task
            task.output_data = {
                "result": output,
                "execution_time": execution_time,
                "agent": task.assigned_agent,
            }

            # Update task status
            task.update_status(TaskStatus.COMPLETED)
            logger.info(f"Task {task.task_id} completed successfully in {execution_time:.2f}s")

            return task.output_data

        except Exception as e:
            logger.error(f"Task {task.task_id} failed: {str(e)}")
            task.update_status(TaskStatus.FAILED)
            task.metadata["error"] = str(e)
            raise

        finally:
            # Remove from active tasks
            if task.task_id in self.active_tasks:
                del self.active_tasks[task.task_id]

    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """
        Get the status of a task.

        Args:
            task_id: ID of the task

        Returns:
            Task status or None if task not found
        """
        task = self.active_tasks.get(task_id)
        return task.status if task else None

    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a running task.

        Args:
            task_id: ID of the task to cancel

        Returns:
            True if task was cancelled, False otherwise
        """
        if task_id not in self.active_tasks:
            logger.warning(f"Cannot cancel task {task_id}: not found in active tasks")
            return False

        task = self.active_tasks[task_id]
        task.update_status(TaskStatus.FAILED)
        task.metadata["cancelled"] = True
        del self.active_tasks[task_id]

        logger.info(f"Task {task_id} cancelled")
        return True

    def get_active_task_count(self) -> int:
        """Get the number of currently active tasks."""
        return len(self.active_tasks)

    def _intelligent_route_task(self, task: Task, case_context: Dict[str, Any]) -> Any:
        """
        Use LLM reasoning to determine which agent should handle this task.

        This is a THOUGHT PIPE: Instead of rigid TaskType → Agent mapping,
        Claude analyzes the task and case to select the most appropriate agent.

        Args:
            task: Task to route
            case_context: Case context including question, priority, etc.

        Returns:
            Selected worker agent instance

        Raises:
            ValueError: If selected agent doesn't exist
        """
        # Check cache first
        if self.reasoning_cache:
            cached = self.reasoning_cache.get(
                prompt="intelligent_task_routing",
                context={"task": task.to_dict(), "case": case_context}
            )
            if cached:
                agent_class_name = cached.get("selected_agent_class")
                return self._get_agent_by_class_name(agent_class_name)

        # Build rich context for Claude
        context = self._build_routing_context(task, case_context)

        # Build reasoning prompt
        prompt = self._build_routing_prompt()

        # Execute thought pipe
        try:
            response = self.thought_pipe.execute_thought_pipe(
                prompt=prompt,
                context=context,
                validation_fn=self._validate_routing_response,
                max_retries=1
            )

            # Extract selected agent
            selected_agent_class = response.get("selected_agent_class")
            reasoning = response.get("reasoning", "")

            logger.info(
                f"Intelligent routing selected {selected_agent_class}\n"
                f"Reasoning: {reasoning}"
            )

            # Cache the decision
            if self.reasoning_cache:
                self.reasoning_cache.set(
                    prompt="intelligent_task_routing",
                    context={"task": task.to_dict(), "case": case_context},
                    response=response
                )

            # Get and return agent instance
            return self._get_agent_by_class_name(selected_agent_class)

        except Exception as e:
            logger.error(f"Intelligent routing failed: {e}")
            raise

    def _build_routing_context(self, task: Task, case_context: Dict[str, Any]) -> Dict[str, Any]:
        """Build context for routing decision."""
        # Get available agents with their capabilities
        available_agents = []
        for task_type, agent in self.worker_registry.items():
            agent_info = {
                "agent_class": agent.__class__.__name__,
                "agent_id": agent.agent_id,
                "handles_task_type": task_type.value,
                "version": getattr(agent, "version", "unknown"),
            }

            # Try to get metadata if available
            if hasattr(agent, "get_metadata"):
                try:
                    metadata = agent.get_metadata()
                    agent_info["capabilities"] = metadata
                except:
                    pass

            available_agents.append(agent_info)

        return {
            "task": {
                "task_id": task.task_id,
                "task_type": task.task_type.value,
                "input_query": task.input_data.get("query", ""),
                "input_context": task.input_data.get("context", {}),
                "retry_count": task.retry_count
            },
            "case": {
                "question": case_context.get("question", ""),
                "description": case_context.get("description", ""),
                "priority": case_context.get("priority", "MEDIUM"),
                "context": case_context.get("context", {})
            },
            "available_agents": available_agents,
            "constraints": {
                "must_select_existing_agent": True,
                "single_agent_only": True  # For now, multi-agent composition is future work
            }
        }

    def _build_routing_prompt(self) -> str:
        """Build the reasoning prompt for intelligent routing."""
        return """Analyze this task and determine which agent should handle it.

TASK TYPE: {task[task_type]}
TASK QUERY: {task[input_query]}
CASE QUESTION: {case[question]}
CASE PRIORITY: {case[priority]}

AVAILABLE AGENTS:
{available_agents_json}

YOUR REASONING TASK:
Determine which agent is BEST qualified to handle this specific task based on:

1. **Specialization Match**
   - Does a specialized agent exist for this specific domain? (e.g., ADC_ILD_Researcher for ADC/ILD questions)
   - Would a specialized agent provide more relevant, in-depth analysis than a generic agent?

2. **Task Requirements**
   - What type of analysis does this task require? (literature review / statistical synthesis / mechanistic reasoning)
   - Does the task query suggest specialized knowledge would add value?

3. **Question Relevance**
   - Does the case question indicate a need for domain expertise?
   - Would general literature review suffice, or is specialized reasoning needed?

DECISION CRITERIA:
- **Prefer specialized agents** when the question/task clearly falls within their domain
- **Use generic agents** when the question is broad or doesn't match a specialty
- **Justify your selection** with specific reasoning about why this agent is best fit

CONSTRAINTS:
- You MUST select an agent from the available_agents list (no hallucination)
- You can only select ONE agent (multi-agent composition not yet supported)
- Default to conservative choices if uncertain

Return JSON:
{{
    "selected_agent_class": "AgentClassName",
    "reasoning": "Detailed explanation of why this agent is best fit for this specific task and case",
    "confidence": "High/Moderate/Low - with justification",
    "alternative_considered": "Other agent considered and why not selected",
    "limitations": ["Any limitations of this agent choice for this task"]
}}

IMPORTANT:
- selected_agent_class MUST exactly match an agent_class from available_agents
- Provide specific reasoning tied to the task query and case question
- Do not claim "High" confidence without strong justification per CLAUDE.md
"""

    def _validate_routing_response(self, response: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Validate that routing response selects a valid agent."""
        selected_class = response.get("selected_agent_class")

        if not selected_class:
            logger.error("Routing response missing 'selected_agent_class'")
            return False

        # Validate selected agent exists
        available_classes = [a["agent_class"] for a in context["available_agents"]]
        if selected_class not in available_classes:
            logger.error(
                f"Selected agent '{selected_class}' not in available agents: {available_classes}"
            )
            return False

        # Validate reasoning provided
        reasoning = response.get("reasoning", "")
        if len(reasoning) < 50:
            logger.warning("Routing reasoning is too brief - should explain selection")
            return False

        return True

    def _get_agent_by_class_name(self, class_name: str) -> Any:
        """Get agent instance by class name."""
        for agent in self.worker_registry.values():
            if agent.__class__.__name__ == class_name:
                return agent

        raise ValueError(f"No agent found with class name: {class_name}")
