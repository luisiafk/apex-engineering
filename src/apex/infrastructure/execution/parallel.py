"""
CPU-bound parallel execution engine for APEX.

Uses ProcessPoolExecutor and limits concurrenci according to
available CPU cores adn estimated memory budget per worker.
"""

from collections.abc import Callable, Iterable
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from time import perf_counter
from typing import TypeVar

from apex.infrastructure.hardware.resources import get_resource_info

T = TypeVar("T")
R = TypeVar("R")


@dataclass(frozen=True, slots=True)
class ParallelConfig:
    """Configuration for parallel task execution."""

    max_workers: int | None = None
    memory_per_worker_mib: int = 1024
    reserver_memory_mib: int = 512

    def __post_init__(self) -> None:
        if self.max_workers is not None and self.max_workers < 1:
            raise ValueError("max_workers must be at least 1")

        if self.memory_per_worker_mib < 1:
            raise ValueError("memory_per_worker_mib must be positive")

        if self.reserver_memory_mib < 0:
            raise ValueError("reserve_memory_mib cannot be negative")


@dataclass(frozen=True, slots=True)
class TaskResult[R]:
    """Result of one executed task."""

    task_index: int
    success: bool
    value: R | None
    error: str | None
    duration_seconds: float


def _execute_task[T, R](
    function: Callable[[T], R],
    task_index: int,
    task: T,
) -> TaskResult[R]:
    """Execute one task inside a worker process."""

    start = perf_counter()

    try:
        value = function(task)

        return TaskResult(
            task_index=task_index,
            success=True,
            value=value,
            error=None,
            duration_seconds=perf_counter() - start,
        )

    except Exception as exc:  # noqa: BLE001
        return TaskResult(
            task_index=task_index,
            success=False,
            value=None,
            error=f"{type(exc).__name__}: {exc}",
            duration_seconds=perf_counter() - start,
        )


class ParallelExecutor:
    """Resource-aware executor for independent CPU-bound task."""

    def __init__(self, config: ParallelConfig | None = None) -> None:
        self.config = config or ParallelConfig()

    def get_worker_count(self) -> int:
        """
        Calculate the maximun safe worker count using the
        available CPU cores and effective available RAM.
        """

        resources = get_resource_info()

        cpu_limit = resources.cpu.available_cores

        if resources.memory is None:
            raise RuntimeError("Unable to retrieve memory information.")
        else:
            usable_memory = (
                resources.memory.available_mib - self.config.reserver_memory_mib
            )

        memory_limit = usable_memory // self.config.memory_per_worker_mib

        if cpu_limit < 1:
            raise RuntimeError("No CPU cores are available")

        if memory_limit < 1:
            raise RuntimeError("Insufficient available memory for one worker")

        worker_count = min(cpu_limit, memory_limit)

        if self.config.max_workers is not None:
            worker_count = min(
                worker_count,
                self.config.max_workers,
            )

        return worker_count

    def run(
        self,
        function: Callable[[T], R],
        tasks: Iterable[T],
    ) -> list[TaskResult[R]]:
        """
        Execute independent tasks in parallel.

        The function and its arguments must be serializable
        by Python's multiprocessing mechanism

        Results are returned in the original task order.
        Individual task failure are captured in TaskResults.
        """

        task_list = list(tasks)

        if not task_list:
            return []

        worker_count = self.get_worker_count()
        results: list[TaskResult[R] | None] = [None] * len(task_list)

        with ProcessPoolExecutor(max_workers=worker_count) as executor:
            futures = {
                executor.submit(
                    _execute_task,
                    function,
                    index,
                    task,
                ): index
                for index, task in enumerate(task_list)
            }

            for future in as_completed(futures):
                index = futures[future]

                try:
                    results[index] = future.result()

                except Exception as exc:  # noqa: BLE001
                    results[index] = TaskResult(
                        task_index=index,
                        success=False,
                        value=None,
                        error=f"{type(exc).__name__} : {exc}",
                        duration_seconds=0.0,
                    )

        final_results: list[TaskResult[R]] = []

        for index, result in enumerate(results):
            if result is None:
                raise RuntimeError(f"Task {index} did not produce a result.")
            final_results.append(result)

        return final_results
