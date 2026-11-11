"""
Centralized hardware resources inspection for APEX.
"""

from dataclasses import dataclass

from .cpu import CPUInfo, get_cpu_info
from .gpu import GPUInfo, get_gpu_info
from .memory import MemoryInfo, get_memory_info


@dataclass(frozen=True, slots=True)
class ResourceInfo:
    """Unified description of the host hardware."""

    cpu: CPUInfo
    gpu: GPUInfo | None
    memory: MemoryInfo | None

    @property
    def gpu_available(self) -> bool:
        return self.gpu is not None

    @property
    def logical_cores(self) -> int:
        return self.cpu.logical_cores

    @property
    def available_cores(self) -> int:
        return self.cpu.available_cores

    @property
    def available_memory_mib(self) -> int:
        if self.memory is None:
            return 0
        else:
            return self.memory.effective_available_mib


def get_resource_info() -> ResourceInfo:
    """
    Collect hardware information from the host.
    Returns:
        ResourceInfo: Unified CPU and GPU information.
    """

    return ResourceInfo(
        cpu=get_cpu_info(),
        gpu=get_gpu_info(),
        memory=get_memory_info(),
    )
