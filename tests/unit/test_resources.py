from apex.infrastructure.hardware.resources import get_resource_info


def test_resource_info_detects_cpu():
    resources = get_resource_info()

    assert resources.cpu is not None
    assert resources.logical_cores >= 1
    assert resources.available_cores >= 1


def test_resource_info_detects_memory():
    resource = get_resource_info()

    assert resource.memory.total_mib > 0
    assert resource.memory.available_mib >= 0
    assert resource.memory.used_mib >= 0


def test_resource_info_detects_gpu():
    resource = get_resource_info()

    if resource.gpu_available:
        assert resource.gpu is not None
        assert resource.gpu.name
        assert resource.gpu.memory_total_mib > 0
    else:
        assert resource.gpu is None
