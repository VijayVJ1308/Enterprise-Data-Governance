"""
Phase 21: Enterprise Airflow DAG & Operator Runtime Engine.
Provides standard Airflow DAG context management, task dependency syntax (>>),
Python/Bash/QualityCheck operators, XCom communication, and topological execution.
"""

import time
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Callable, Union

logger = logging.getLogger("AirflowOrchestrator")


class DagRunContext:
    """Carries execution state, timestamps, and XCom messaging between tasks."""

    def __init__(self, run_id: Optional[str] = None):
        self.run_id = run_id or f"manual__{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}"
        self.execution_date = datetime.now(timezone.utc).isoformat()
        self._xcom_store: Dict[str, Dict[str, Any]] = {}  # {task_id: {key: value}}

    def xcom_push(self, task_id: str, key: str, value: Any) -> None:
        self._xcom_store.setdefault(task_id, {})[key] = value

    def xcom_pull(self, task_id: str, key: str = "return_value") -> Any:
        return self._xcom_store.get(task_id, {}).get(key)


class BaseOperator:
    """Base class for all Airflow tasks."""

    def __init__(
        self,
        task_id: str,
        dag: Optional["DAG"] = None,
        retries: int = 0,
        retry_delay_seconds: int = 5,
        **kwargs,
    ):
        self.task_id = task_id
        self.dag = dag
        self.retries = retries
        self.retry_delay_seconds = retry_delay_seconds
        self.upstream_list: List["BaseOperator"] = []
        self.downstream_list: List["BaseOperator"] = []

        # Auto-register with DAG if provided or active in context
        active_dag = dag or DAG.get_current_dag()
        if active_dag:
            self.dag = active_dag
            active_dag.add_task(self)

    def __rshift__(self, other: Union["BaseOperator", List["BaseOperator"]]):
        """Support task1 >> task2 and task1 >> [task2, task3] syntax."""
        targets = other if isinstance(other, list) else [other]
        for t in targets:
            if t not in self.downstream_list:
                self.downstream_list.append(t)
            if self not in t.upstream_list:
                t.upstream_list.append(self)
        return other

    def __lshift__(self, other: Union["BaseOperator", List["BaseOperator"]]):
        """Support task2 << task1 and [task2, task3] << task1 syntax."""
        sources = other if isinstance(other, list) else [other]
        for s in sources:
            s >> self
        return other

    def execute(self, context: DagRunContext) -> Any:
        raise NotImplementedError("Operators must implement execute().")


class PythonOperator(BaseOperator):
    """Executes a Python function with runtime context and parameters."""

    def __init__(
        self,
        task_id: str,
        python_callable: Callable,
        op_kwargs: Optional[Dict[str, Any]] = None,
        dag: Optional["DAG"] = None,
        **kwargs,
    ):
        super().__init__(task_id, dag=dag, **kwargs)
        self.python_callable = python_callable
        self.op_kwargs = op_kwargs or {}

    def execute(self, context: DagRunContext) -> Any:
        call_kwargs = dict(self.op_kwargs)
        call_kwargs["context"] = context
        call_kwargs["ti"] = context  # Airflow task instance alias
        result = self.python_callable(**call_kwargs)
        context.xcom_push(self.task_id, "return_value", result)
        return result


class QualityCheckOperator(BaseOperator):
    """Evaluates an automated data quality gate assertion before allowing downstream tasks."""

    def __init__(
        self,
        task_id: str,
        check_callable: Callable[..., bool],
        min_score: float = 85.0,
        dag: Optional["DAG"] = None,
        **kwargs,
    ):
        super().__init__(task_id, dag=dag, **kwargs)
        self.check_callable = check_callable
        self.min_score = min_score

    def execute(self, context: DagRunContext) -> Any:
        passed = self.check_callable(context=context, min_score=self.min_score)
        if not passed:
            raise ValueError(
                f"QualityCheckOperator '{self.task_id}' failed: Data Quality Gate score below required {self.min_score}% threshold."
            )
        context.xcom_push(self.task_id, "gate_status", "PASSED")
        return {"gate": self.task_id, "status": "PASSED", "min_score": self.min_score}


class DAG:
    """Airflow Directed Acyclic Graph orchestrator."""

    _current_dag: Optional["DAG"] = None

    def __init__(
        self,
        dag_id: str,
        schedule_interval: str = "@daily",
        start_date: Optional[datetime] = None,
        default_args: Optional[Dict[str, Any]] = None,
        description: str = "",
        tags: Optional[List[str]] = None,
        catchup: bool = False,
    ):
        self.dag_id = dag_id
        self.schedule_interval = schedule_interval
        self.start_date = start_date or datetime.now(timezone.utc)
        self.default_args = default_args or {}
        self.description = description
        self.tags = tags or []
        self.catchup = catchup
        self.tasks: Dict[str, BaseOperator] = {}

    def __enter__(self):
        DAG._current_dag = self
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        DAG._current_dag = None

    @classmethod
    def get_current_dag(cls) -> Optional["DAG"]:
        return cls._current_dag

    def add_task(self, task: BaseOperator) -> None:
        self.tasks[task.task_id] = task

    def get_task(self, task_id: str) -> BaseOperator:
        if task_id not in self.tasks:
            raise KeyError(f"Task '{task_id}' not found in DAG '{self.dag_id}'.")
        return self.tasks[task_id]

    def get_topological_sort(self) -> List[BaseOperator]:
        """Compute execution order using topological sorting."""
        in_degree = {task_id: len(task.upstream_list) for task_id, task in self.tasks.items()}
        queue = [task for task_id, task in self.tasks.items() if in_degree[task_id] == 0]
        sorted_tasks = []

        while queue:
            node = queue.pop(0)
            sorted_tasks.append(node)
            for downstream in node.downstream_list:
                in_degree[downstream.task_id] -= 1
                if in_degree[downstream.task_id] == 0:
                    queue.append(downstream)

        if len(sorted_tasks) != len(self.tasks):
            raise ValueError(f"Cycle detected in DAG '{self.dag_id}'. Topo sort failed.")

        return sorted_tasks

    def run(self, context: Optional[DagRunContext] = None) -> Dict[str, Any]:
        """Execute the DAG in topological dependency order."""
        ctx = context or DagRunContext()
        ordered_tasks = self.get_topological_sort()
        task_results: Dict[str, Any] = {}
        start_ts = time.time()

        for task in ordered_tasks:
            t_start = time.time()
            try:
                res = task.execute(ctx)
                task_results[task.task_id] = {
                    "status": "SUCCESS",
                    "result": res,
                    "elapsed_ms": int((time.time() - t_start) * 1000),
                }
            except Exception as e:
                task_results[task.task_id] = {
                    "status": "FAILED",
                    "error": str(e),
                    "elapsed_ms": int((time.time() - t_start) * 1000),
                }
                logger.error(f"Task {task.task_id} failed: {e}", exc_info=True)
                return {
                    "dag_id": self.dag_id,
                    "run_id": ctx.run_id,
                    "status": "FAILED",
                    "failed_task": task.task_id,
                    "tasks": task_results,
                    "total_elapsed_ms": int((time.time() - start_ts) * 1000),
                }

        return {
            "dag_id": self.dag_id,
            "run_id": ctx.run_id,
            "status": "SUCCESS",
            "tasks": task_results,
            "total_elapsed_ms": int((time.time() - start_ts) * 1000),
        }
