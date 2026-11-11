import pytest

from apex.infrastructure.execution.workers import (
    WorkerInfo,
    WorkerManager,
    WorkerState,
)


@pytest.fixture
def manager() -> WorkerManager:
    return WorkerManager()


def test_register_worker(manager: WorkerManager) -> None:
    worker = manager.register_worker("worker-1", pid=1234)

    assert isinstance(worker, WorkerInfo)
    assert worker.worker_id == "worker-1"
    assert worker.pid == 1234
    assert worker.state == WorkerState.IDLE
    assert worker.tasks_completed == 0


def test_register_duplicate_worker(manager: WorkerManager) -> None:
    manager.register_worker("worker-1")
    with pytest.raises(ValueError):
        manager.register_worker("worker-1")


def test_register_worker_with_invalid_pid(
    manager: WorkerManager,
) -> None:
    with pytest.raises(ValueError):
        manager.register_worker("worker-1", pid=0)


def test_worker_state_transitions(manager: WorkerManager) -> None:
    manager.register_worker("worker-1")
    worker = manager.mark_busy("worker-1")
    assert worker.state == WorkerState.BUSY

    worker = manager.complete_task("worker-1")
    assert worker.state == WorkerState.IDLE
    assert worker.tasks_completed == 1


def test_worker_can_fail(manager: WorkerManager) -> None:
    manager.register_worker("worker-1")
    worker = manager.mark_failed("worker-1")

    assert worker.state == WorkerState.FAILED


def test_failed_worker_can_stop(manager: WorkerManager) -> None:
    manager.register_worker("worker-1")
    manager.mark_failed("worker-1")
    worker = manager.mark_stopped("worker-1")

    assert worker.state == WorkerState.STOPPED


def test_invalid_transition(manager: WorkerManager) -> None:
    manager.register_worker("worker-1")
    with pytest.raises(RuntimeError):
        manager.complete_task("worker-1")


def test_stopped_worker_cannot_restart(
    manager: WorkerManager,
) -> None:
    manager.register_worker("worker-1")
    manager.mark_stopped("worker-1")
    with pytest.raises(RuntimeError):
        manager.mark_busy("worker-1")


def test_get_available_workers(manager: WorkerManager) -> None:
    manager.register_worker("worker-1")
    manager.register_worker("worker-2")
    manager.mark_busy("worker-2")

    available = manager.get_available_workers()

    assert len(available) == 1
    assert available[0].worker_id == "worker-1"


def test_get_unknown_worker(manager: WorkerManager) -> None:
    with pytest.raises(KeyError):
        manager.get_worker("unknown")


def test_list_workers(manager: WorkerManager) -> None:
    manager.register_worker("worker-1")
    manager.register_worker("worker-2")
    workers = manager.list_workers()
    assert len(workers) == 2
