from apex.infrastructure.hardware import memory


def test_read_cgroup_memory_v2(monkeypatch, tmp_path):
    cgroup_dir = tmp_path / "test"
    cgroup_dir.mkdir()

    (cgroup_dir / "memory.max").write_text(str(2 * 1024**3))
    (cgroup_dir / "memory.current").write_text(str(512 * 1024**2))

    proc_cgroup = tmp_path / "proc" / "self" / "cgroup"
    proc_cgroup.parent.mkdir(parents=True)
    proc_cgroup.write_text("0::/test\n")

    monkeypatch.setattr(memory, "_PROC_CGROUP", proc_cgroup)
    monkeypatch.setattr(memory, "_CGROUP_ROOT", tmp_path)

    result = memory._read_cgroup_memory()
    assert result == (2048, 512)


def test_read_cgroup_memory_v2_unlimited(monkeypatch, tmp_path):
    cgroup_dir = tmp_path / "test"
    cgroup_dir.mkdir()

    (cgroup_dir / "memory.max").write_text("max")
    (cgroup_dir / "memory.current").write_text(str(512 * 1024**2))

    proc_cgroup = tmp_path / "proc" / "self" / "cgroup"
    proc_cgroup.parent.mkdir(parents=True)
    proc_cgroup.write_text("0::/test\n")

    monkeypatch.setattr(memory, "_PROC_CGROUP", proc_cgroup)
    monkeypatch.setattr(memory, "_CGROUP_ROOT", tmp_path)

    result = memory._read_cgroup_memory()
    assert result is None


def test_get_memory_info_respects_cgroup_limit(monkeypatch):
    monkeypatch.setattr(
        memory,
        "_read_system_memory",
        lambda: (8192, 4096),
    )
    monkeypatch.setattr(
        memory,
        "_read_cgroup_memory",
        lambda: (2048, 1536),
    )

    result = memory.get_memory_info()

    assert result.total_mib == 8192
    assert result.available_mib == 4096
    assert result.used_mib == 4096
    assert result.cgroup_limit_mib == 2048
    assert result.cgroup_used_mib == 1536
    assert result.effective_available_mib == 512


def test_get_memory_info_never_returns_negative_effective_memory(
    monkeypatch,
):
    monkeypatch.setattr(
        memory,
        "_read_system_memory",
        lambda: (8192, 4096),
    )
    monkeypatch.setattr(
        memory,
        "_read_cgroup_memory",
        lambda: (2048, 2300),
    )

    result = memory.get_memory_info()

    assert result.effective_available_mib == 0


def test_read_cgroup_memory_v1(monkeypatch, tmp_path):
    cgroup_dir = tmp_path / "memory" / "test"
    cgroup_dir.mkdir(parents=True)

    (cgroup_dir / "memory.limit_in_bytes").write_text(str(1024 * 1024**2))
    (cgroup_dir / "memory.usage_in_bytes").write_text(str(256 * 1024**2))

    proc_cgroup = tmp_path / "proc" / "self" / "cgroup"
    proc_cgroup.parent.mkdir(parents=True)
    proc_cgroup.write_text("5:memory:/test\n")

    monkeypatch.setattr(memory, "_PROC_CGROUP", proc_cgroup)
    monkeypatch.setattr(memory, "_CGROUP_ROOT", tmp_path)

    result = memory._read_cgroup_memory()

    assert result == (1024, 256)


def test_read_cgroup_memory_v1_unlimited(monkeypatch, tmp_path):
    cgroup_dir = tmp_path / "memory" / "test"
    cgroup_dir.mkdir(parents=True)

    (cgroup_dir / "memory.limit_in_bytes").write_text(str(1 << 60))
    (cgroup_dir / "memory.usage_in_bytes").write_text(str(256 * 1024**2))

    proc_cgroup = tmp_path / "proc" / "self" / "cgroup"
    proc_cgroup.parent.mkdir(parents=True)
    proc_cgroup.write_text("5:memory:/test\n")

    monkeypatch.setattr(memory, "_PROC_CGROUP", proc_cgroup)
    monkeypatch.setattr(memory, "_CGROUP_ROOT", tmp_path)

    result = memory._read_cgroup_memory()

    assert result is None


def test_read_cgroup_memory_ignores_malformed_entries(
    monkeypatch,
    tmp_path,
):
    proc_cgroup = tmp_path / "proc" / "self" / "cgroup"
    proc_cgroup.parent.mkdir(parents=True)
    proc_cgroup.write_text("malformed-entry\n")

    monkeypatch.setattr(memory, "_PROC_CGROUP", proc_cgroup)
    monkeypatch.setattr(memory, "_CGROUP_ROOT", tmp_path)

    result = memory._read_cgroup_memory()

    assert result is None
