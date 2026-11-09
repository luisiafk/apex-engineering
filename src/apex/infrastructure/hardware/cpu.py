"""
CPU hardware inspection for APEX

Provides information about the host processor and
the CPU cores avialable to the current process.
"""

import os
import platform
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CPUInfo:
    """Immutable description of the avialable CPU resources."""

    architecture: str
    processor: str
    logical_cores: int
    available_cores: int


def _get_processor_name() -> str:
    """Retrieve the processor model name on linux."""

    processor = platform.processor()

    if processor:
        return processor

    try:
        with open("proc/cpuinfo", encoding="utf-8") as cpu_file:
            for line in cpu_file:
                if line.lower().startswith(("model name", "hardware")):
                    return line.split(":", 1)[1].strip()
    except OSError:
        pass

    return platform.machine()


def get_cpu_info() -> CPUInfo:
    """ "
    Detect CPU characteristics.

    Returns:
        CPUInfo: Information about the processor and
        the logcal cores avialables for APEX.
    """

    logical_cores = os.cpu_count() or 1

    try:
        available_cores = len(os.sched_getaffinity(0))
    except (AttributeError, OSError):
        available_cores = logical_cores

    available_cores = max(1, min(available_cores, logical_cores))

    return CPUInfo(
        architecture=platform.machine(),
        processor=_get_processor_name(),
        logical_cores=logical_cores,
        available_cores=available_cores,
    )
