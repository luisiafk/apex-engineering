from dataclasses import dataclass, replace
from enum import Enum
from threading import RLock
from typing import ClassVar


class WorkerState(str, Enum):
    IDLE = "idle"
    BUSY = "busy"
    STOPPED = "stopped"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class WorkerInfo:
    worker_id: str
    pid: int | None
    state: WorkerState = WorkerState.IDLE
    tasks_completed: int = 0


class WorkerManager:
    """Thread-safe registry for tracking worker states."""

    _ALLOWED_TRANSITIONS: ClassVar[dict[WorkerState, set[WorkerState]]] = {
        WorkerState.IDLE: {
            WorkerState.BUSY,
            WorkerState.STOPPED,
            WorkerState.FAILED,
        },
        WorkerState.BUSY: {
            WorkerState.IDLE,
            WorkerState.STOPPED,
            WorkerState.FAILED,
        },
        WorkerState.FAILED: {
            WorkerState.STOPPED,
        },
        WorkerState.STOPPED: set(),
    }

    def __init__(self) -> None:
        self._workers: dict[str, WorkerInfo] = {}
        self._lock = RLock()

    def register_worker(
        self,
        worker_id: str,
        pid: int | None = None,
    ) -> WorkerInfo:
        if not worker_id.strip():
            raise ValueError("worker_id cannot be empty.")

        if pid is not None and pid < 1:
            raise ValueError("pid must be a positive integer.")

        with self._lock:
            if worker_id in self._workers:
                raise ValueError(f"Worker '{worker_id}' is already registered.")

            worker = WorkerInfo(
                worker_id=worker_id,
                pid=pid,
            )
            self._workers[worker_id] = worker
            return worker

    def get_worker(self, worker_id: str) -> WorkerInfo:
        with self._lock:
            worker = self._workers.get(worker_id)

            if worker is None:
                raise KeyError(f"Worker '{worker_id}' not found.")

            return worker

    def list_workers(self) -> list[WorkerInfo]:
        with self._lock:
            return list(self._workers.values())

    def get_available_workers(self) -> list[WorkerInfo]:
        with self._lock:
            return [
                worker
                for worker in self._workers.values()
                if worker.state == WorkerState.IDLE
            ]

    def _transition(
        self,
        worker_id: str,
        new_state: WorkerState,
        *,
        increment_completed: bool = False,
    ) -> WorkerInfo:
        with self._lock:
            worker = self._workers.get(worker_id)

            if worker is None:
                raise KeyError(f"Worker '{worker_id}' not found.")

            allowed_states = self._ALLOWED_TRANSITIONS[worker.state]

            if new_state not in allowed_states:
                raise RuntimeError(
                    f"Invalid worker transition: {worker.state.value} -> {new_state.value}."
                )

            updated_worker = replace(
                worker,
                state=new_state,
                tasks_completed=(
                    worker.tasks_completed + 1
                    if increment_completed
                    else worker.tasks_completed
                ),
            )

            self._workers[worker_id] = updated_worker
            return updated_worker

    def mark_busy(self, worker_id: str) -> WorkerInfo:
        return self._transition(worker_id, WorkerState.BUSY)

    def complete_task(self, worker_id: str) -> WorkerInfo:
        return self._transition(worker_id, WorkerState.IDLE, increment_completed=True)

    def mark_failed(self, worker_id: str) -> WorkerInfo:
        return self._transition(worker_id, WorkerState.FAILED)

    def mark_stopped(self, worker_id: str) -> WorkerInfo:
        return self._transition(worker_id, WorkerState.STOPPED)
