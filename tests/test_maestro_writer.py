from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from virtuoso_bridge.virtuoso.maestro import create_netlist_for_corner
from virtuoso_bridge.virtuoso.maestro import export_netlist
from virtuoso_bridge.virtuoso.maestro import MaestroOps


class _RecordingClient:
    def __init__(self) -> None:
        self.expressions: list[str] = []

    def execute_skill(self, expression: str, **_kwargs):
        self.expressions.append(expression)
        return SimpleNamespace(errors=[], output="t")


class _NetlistExportClient:
    def __init__(
        self,
        tests: str = '("tran_test")',
        corners: str = '("Nominal")',
    ) -> None:
        self.tests = tests
        self.corners = corners
        self.expressions: list[str] = []
        self.downloads: list[tuple[str, Path]] = []
        self.commands: list[str] = []

    def execute_skill(self, expression: str, **_kwargs: object) -> SimpleNamespace:
        self.expressions.append(expression)
        if "maeOpenSetup" in expression:
            return SimpleNamespace(errors=[], output='"fnxSession7"')
        if '?typeName "corners"' in expression:
            return SimpleNamespace(errors=[], output=self.corners)
        if "maeGetSetup" in expression:
            return SimpleNamespace(errors=[], output=self.tests)
        return SimpleNamespace(errors=[], output="t")

    def download_file(self, remote_path: str, local_path: Path) -> SimpleNamespace:
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_text(remote_path, encoding="utf-8")
        self.downloads.append((remote_path, local_path))
        return SimpleNamespace(errors=[])

    def run_shell_command(self, command: str) -> SimpleNamespace:
        self.commands.append(command)
        return SimpleNamespace(errors=[])


def test_create_netlist_for_corner_uses_current_session_by_default() -> None:
    client = _RecordingClient()

    result = create_netlist_for_corner(
        client,
        "tran_test",
        "tt",
        "/tmp/tran_tt",
    )

    assert result == "t"
    assert client.expressions == [
        'maeCreateNetlistForCorner("tran_test" "tt" "/tmp/tran_tt")'
    ]


def test_create_netlist_for_corner_passes_explicit_session() -> None:
    client = _RecordingClient()

    create_netlist_for_corner(
        client,
        "tran_test",
        "tt",
        "/tmp/tran_tt",
        session="session3",
    )

    assert client.expressions == [
        'maeCreateNetlistForCorner("tran_test" "tt" "/tmp/tran_tt" '
        '?session "session3")'
    ]


def test_create_netlist_for_corner_session_is_keyword_only() -> None:
    client = _RecordingClient()

    with pytest.raises(TypeError):
        create_netlist_for_corner(
            client,
            "tran_test",
            "tt",
            "/tmp/tran_tt",
            "session3",
        )


def test_maestro_ops_passes_explicit_session_to_corner_netlist_export() -> None:
    client = _RecordingClient()

    MaestroOps(client).create_netlist_for_corner(
        "tran_test",
        "tt",
        "/tmp/tran_tt",
        session="session3",
    )

    assert client.expressions == [
        'maeCreateNetlistForCorner("tran_test" "tt" "/tmp/tran_tt" '
        '?session "session3")'
    ]


def test_export_netlist_selects_single_test_and_downloads_artifacts(tmp_path) -> None:
    client = _NetlistExportClient()

    result = export_netlist(client, "demoLib", "tb_amp", output_root=tmp_path)

    expected_dir = tmp_path / "demoLib" / "tb_amp" / "netlist" / "tran_test__Nominal"
    assert result.test == "tran_test"
    assert result.corner == "Nominal"
    assert result.output_dir == expected_dir
    assert result.input_scs == expected_dir / "input.scs"
    assert result.netlist == expected_dir / "netlist"
    assert [path.name for _, path in client.downloads] == ["input.scs", "netlist"]
    assert any(
        'maeCreateNetlistForCorner("tran_test" "Nominal"' in expr
        for expr in client.expressions
    )
    assert client.commands[0].startswith("rm -rf /tmp/vb_maestro_netlist_")
    assert any("maeCloseSession" in expr for expr in client.expressions)


def test_export_netlist_requires_explicit_test_when_multiple_exist(tmp_path) -> None:
    client = _NetlistExportClient(tests='("ac" "tran")')

    with pytest.raises(ValueError, match="multiple tests"):
        export_netlist(client, "demoLib", "tb_amp", output_root=tmp_path)

    assert not client.downloads
    assert any("maeCloseSession" in expr for expr in client.expressions)


def test_export_netlist_reports_available_corner(tmp_path) -> None:
    client = _NetlistExportClient(corners='("tt" "ff")')

    with pytest.raises(ValueError, match="available: tt, ff"):
        export_netlist(client, "demoLib", "tb_amp", output_root=tmp_path)

    assert not client.downloads
    assert any("maeCloseSession" in expr for expr in client.expressions)


def test_export_netlist_refuses_existing_output_without_overwrite(tmp_path) -> None:
    output_dir = tmp_path / "demoLib" / "tb_amp" / "netlist" / "tran_test__Nominal"
    output_dir.mkdir(parents=True)
    client = _NetlistExportClient()

    with pytest.raises(FileExistsError, match="overwrite=True"):
        export_netlist(client, "demoLib", "tb_amp", output_root=tmp_path)

    assert not client.downloads


def test_export_netlist_overwrite_replaces_expected_files(tmp_path) -> None:
    output_dir = tmp_path / "demoLib" / "tb_amp" / "netlist" / "tran_test__Nominal"
    output_dir.mkdir(parents=True)
    (output_dir / "input.scs").write_text("old", encoding="utf-8")
    (output_dir / "netlist").write_text("old", encoding="utf-8")
    client = _NetlistExportClient()

    result = export_netlist(
        client, "demoLib", "tb_amp", output_root=tmp_path, overwrite=True
    )

    assert result.input_scs.read_text(encoding="utf-8").endswith("input.scs")
    assert result.netlist.read_text(encoding="utf-8").endswith("netlist")


def test_export_netlist_rejects_path_components(tmp_path) -> None:
    client = _NetlistExportClient()

    with pytest.raises(ValueError, match="path component"):
        export_netlist(client, "../demoLib", "tb_amp", output_root=tmp_path)

    assert not client.expressions
