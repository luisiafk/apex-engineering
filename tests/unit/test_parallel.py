from types import SimpleNamespace

import pytest

from apex.infrastructure.execution.parallel import (
    ParallelConfig,
    ParallelExecutor,
)


def square(value: int) -> int:
    return value * value


def failing_task(value: int) -> int:
    if value == 2:
        raise ValueError("Intentional test failure")
    return value


def test_parallel_config_rejects_invalid_workers():
    with pytest.raises(ValueError):
        ParallelConfig(max_workers=0)


def test_parallel_config_rejects_invalid_memory():
    with pytest.raises(ValueError):
        ParallelConfig(memory_per_worker_mib=0)


def test_worker_count_respects_configured_limits(monkeypatch):
    from apex.infrastructure.execution import parallel

    class FakeCPU:
        available_cores = 8

    class FakeResources:
        cpu = SimpleNamespace(available_cores=8)
        memory = SimpleNamespace(available_mib=8192)

    monkeypatch.setattr(
        parallel,
        "get_resource_info",
        lambda: FakeResources(),
    )

    executor = ParallelExecutor(
        ParallelConfig(
            max_workers=3,
            memory_per_worker_mib=1024,
            reserver_memory_mib=512,
        )
    )

    assert executor.get_worker_count() == 3


def test_worker_count_rejects_insufficient_memory(monkeypatch):
    from apex.infrastructure.execution import parallel

    class FakeCPU:
        available_cores = 8

    class FakeResources:
        cpu = SimpleNamespace(available_cores=8)
        memory = SimpleNamespace(available_mib=500)

    monkeypatch.setattr(
        parallel,
        "get_resource_info",
        lambda: FakeResources(),
    )

    executor = ParallelExecutor()

    with pytest.raises(RuntimeError):
        executor.get_worker_count()


def test_parallel_execution_capture_task_erros():
    executor = ParallelExecutor(ParallelConfig(max_workers=2))

    results = executor.run(failing_task, [1, 2, 3])

    assert results[0].success
    assert not results[1].success
    assert "ValueError" in results[1].error
    assert results[2].success


def test_parallel_execution_handles_empty_tasks():
    executor = ParallelExecutor()

    assert executor.run(square, []) == []
