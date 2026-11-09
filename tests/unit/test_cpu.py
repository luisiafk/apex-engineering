from apex.infrastructure.hardware.cpu import get_cpu_info


def test_cpu_info_return_valid_data():
    info = get_cpu_info()

    assert info.architecture
    assert info.logical_cores >= 1
    assert info.available_cores >= 1


def test_avialable_cores_do_not_exceed_logical_cores():
    info = get_cpu_info()

    assert info.available_cores <= info.logical_cores
