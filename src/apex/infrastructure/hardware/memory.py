"""
System memory inspection for APEX.

Support Linux memory information and cgroup v1/v2 limits.
"""

from dataclasses import dataclass
from pathlib import Path

_MIB = 1024 * 1024
_PROC_MEMINFO = Path("/proc/meminfo")
_PROC_CGROUP = Path("/proc/self/cgroup")
_CGROUP_ROOT = Path("/sys/fs/cgroup")


@dataclass(frozen=True, slots=True)
class MemoryInfo:
    """Immutable description of system and cgroup memory."""

    total_mib: int
    available_mib: int
    used_mib: int
    cgroup_limit_mib: int | None
    cgroup_used_mib: int | None
    effective_available_mib: int

    @property
    def usage_percent(self) -> float:
        """Returns system RAM usage as a percentage."""
        if self.total_mib == 0:
            return 0

        return self.used_mib / self.total_mib * 100


def _read_system_memory() -> tuple[int, int]:
    """Read total and available Ram from /proc/meminfo."""

    values: dict[str, int] = {}

    with _PROC_MEMINFO.open(encoding="utf-8") as meminfo:
        for line in meminfo:
            key, separator, value = line.partition(":")

            if separator and key in {"MemTotal", "MemAvailable"}:
                values[key] = int(value.strip().split()[0]) // 1024

    if "MemTotal" not in values or "MemAvailable" not in values:
        raise RuntimeError("Could not read system memory from /proc/meminfo")

    total = values["MemTotal"]
    available = min(values["MemAvailable"], total)

    return total, available


def _read_cgroup_memory() -> tuple[int, int] | None:
    """
    Read the current cgroup memory limit and usage.

    Supports cgroup v2 and v1.
    Returns None when no finite memory limit is found.
    """

    try:
        cgroups_entries = _PROC_CGROUP.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None

    for entry in cgroups_entries:
        hierarchy, controllers, relative_path = entry.split(":", 2)
        relative_path = relative_path.lstrip("/")

        # cgroup v2
        if hierarchy == "0" and not controllers:
            directory = _CGROUP_ROOT / relative_path
            limit_file = directory / "memory.max"
            usage_file = directory / "memory.current"

        # cgroup v1
        elif "memory" in controllers.split(","):
            directory = _CGROUP_ROOT / "memory" / relative_path
            limit_file = directory / "memory.limit_in_bytes"
            usage_file = directory / "memory.usage_in_bytes"

        else:
            continue

        try:
            raw_limit = limit_file.read_text(encoding="utf-8").strip()
            raw_usage = usage_file.read_text(encoding="utf-8").strip()

            if raw_limit == "max":
                return None

            limit_bytes = int(raw_limit)
            usage_bytes = int(raw_usage)

            if limit_bytes >= 1 << 60:
                return None

            return limit_bytes // _MIB, usage_bytes // _MIB
        except (OSError, ValueError):
            continue
    return None


def get_memory_info() -> MemoryInfo:
    """
    Collect system Ram and effective memory availability.

    The effective availability respects finite cgroups limits
    when the can be detected
    """

    total, available = _read_system_memory()
    used = total - available

    cgroup_memory = _read_cgroup_memory()

    if cgroup_memory is None:
        cgroup_limit = None
        cgroup_used = None
        effective_available = available
    else:
        cgroup_limit, cgroup_used = cgroup_memory
        cgroup_available = max(0, cgroup_limit - cgroup_used)
        effective_available = min(available, cgroup_available)

    return MemoryInfo(
        total_mib=total,
        available_mib=available,
        used_mib=used,
        cgroup_limit_mib=cgroup_limit,
        cgroup_used_mib=cgroup_used,
        effective_available_mib=effective_available,
    )
