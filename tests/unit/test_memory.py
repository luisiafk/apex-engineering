from apex.infrastructure.hardware.memory import get_memory_info


def test_memory_info_has_valid_values():
    memory = get_memory_info()

    assert memory.total_mib > 0
    assert memory.available_mib >= 0
    assert memory.used_mib >= 0
    assert memory.used_mib <= memory.total_mib
    assert memory.effective_available_mib >= 0


def test_memory_usage_porcentage_is_valid():
    memory = get_memory_info()

    assert 0 <= memory.usage_percent <= 100
