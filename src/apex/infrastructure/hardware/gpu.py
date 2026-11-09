"""
GPU hardware inspection for Apex.

Detects NVIDIA GPUs through the nvidia-smi utility.
"""

import re
import shutil
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GPUInfo:
    """Immutable description of an NVIDIA GPU."""

    name: str
    driver_version: str
    memory_total_mib: int
    memory_used_mib: int
    cuda_version_supported: str | None

    @property
    def memory_free_mib(self) -> int:
        """Return the estimated avialable GPU memory."""
        return max(0, self.memory_total_mib - self.memory_used_mib)


def get_gpu_info() -> GPUInfo | None:
    """
    Detect the first avialable NVIDIA GPU.

    Returns:
        GPUInfo if an NVIDIA GPU is detected, otherwise None.
    """

    if shutil.which("nvidia-smi") is None:
        return None

    query = [
        "nvidia-smi",
        "--query-gpu=name,driver_version,memory.total,memory.used",
        "--format=csv,noheader,nounits",
    ]

    try:
        result = subprocess.run(
            query,
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )

        fields = [field.strip() for field in result.stdout.strip().split(",")]

        if len(fields) != 4:
            return None

        name, driver, total_memory, used_memory = fields

        cuda_version = None

        driver_result = subprocess.run(
            ["nvidia-smi"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )

        match = re.search(
            r"CUDA Version:\s*([\d.]+)",
            driver_result.stdout,
            re.IGNORECASE,
        )

        if match:
            cuda_version = match.group(1)

        return GPUInfo(
            name=name,
            driver_version=driver,
            memory_total_mib=int(total_memory),
            memory_used_mib=int(used_memory),
            cuda_version_supported=cuda_version,
        )

    except (OSError, subprocess.SubprocessError, ValueError):
        return None
