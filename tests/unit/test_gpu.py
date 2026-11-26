from types import SimpleNamespace

from apex.infrastructure.hardware import gpu


def test_get_gpu_info_detects_single_gpu(monkeypatch):
    monkeypatch.setattr(gpu.shutil, "which", lambda _: "/usr/bin/nvidia-smi")

    def mock_run(command, **kwargs):
        if "--query-gpu=name,driver_version,memory.total,memory.used" in command:
            return SimpleNamespace(
                stdout="NVIDIA GeForce GTX 1650, 550.163.01, 4096, 1024\n"
            )

        return SimpleNamespace(stdout="CUDA Version: 12.4")

    monkeypatch.setattr(gpu.subprocess, "run", mock_run)

    result = gpu.get_gpu_info()

    assert result is not None
    assert result.name == "NVIDIA GeForce GTX 1650"
    assert result.driver_version == "550.163.01"
    assert result.memory_total_mib == 4096
    assert result.memory_used_mib == 1024
    assert result.memory_free_mib == 3072
    assert result.cuda_version_supported == "12.4"


def test_get_gpu_info_detects_first_gpu_when_multiple_exist(monkeypatch):
    monkeypatch.setattr(gpu.shutil, "which", lambda _: "/usr/bin/nvidia-smi")

    def mock_run(command, **kwargs):
        if "--query-gpu=name,driver_version,memory.total,memory.used" in command:
            return SimpleNamespace(
                stdout=(
                    "NVIDIA GeForce GTX 1650, 550.163.01, 4096, 1024\n"
                    "NVIDIA GeForce RTX 3080, 550.163.01, 10240, 2048\n"
                )
            )

        return SimpleNamespace(stdout="CUDA Version: 12.4")

    monkeypatch.setattr(gpu.subprocess, "run", mock_run)

    result = gpu.get_gpu_info()

    assert result is not None
    assert result.name == "NVIDIA GeForce GTX 1650"
    assert result.memory_total_mib == 4096
    assert result.memory_used_mib == 1024


def test_get_gpu_info_returns_none_when_nvidia_smi_is_missing(monkeypatch):
    monkeypatch.setattr(gpu.shutil, "which", lambda _: None)

    result = gpu.get_gpu_info()

    assert result is None


def test_get_gpu_info_returns_none_when_nvidia_smi_fails(monkeypatch):
    monkeypatch.setattr(gpu.shutil, "which", lambda _: "/usr/bin/nvidia-smi")

    def mock_run(command, **kwargs):
        raise gpu.subprocess.CalledProcessError(1, command)

    monkeypatch.setattr(gpu.subprocess, "run", mock_run)

    result = gpu.get_gpu_info()
    assert result is None
