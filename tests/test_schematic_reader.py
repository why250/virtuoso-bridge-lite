from __future__ import annotations

from types import SimpleNamespace

import pytest

from virtuoso_bridge.virtuoso.schematic.reader import _parse_schematic, read_schematic
from virtuoso_bridge.virtuoso.schematic import SchematicOps


def test_read_schematic_raises_on_skill_error() -> None:
    class Client:
        def execute_skill(self, skill: str, timeout: int = 300):
            return SimpleNamespace(output="", errors=["*Error* sprintf: argument #3 should be a number"])

    with pytest.raises(RuntimeError, match="read_schematic SKILL error"):
        read_schematic(Client(), "LIB", "CELL", param_filters=None)


def test_read_schematic_forwards_timeout() -> None:
    class Client:
        timeout: int | None = None

        def execute_skill(self, skill: str, timeout: int = 300):
            self.timeout = timeout
            return SimpleNamespace(output="INSTANCES\nNETS\nPINS\nEND\n", errors=[])

    client = Client()

    read_schematic(client, "LIB", "CELL", param_filters=None, timeout=123)

    assert client.timeout == 123


def test_client_bound_read_delegates_to_unified_reader(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}
    owner = object()

    def fake_read(client: object, lib: str, cell: str, **kwargs: object) -> dict[str, object]:
        captured["client"] = client
        captured["lib"] = lib
        captured["cell"] = cell
        captured["kwargs"] = kwargs
        return {"instances": []}

    monkeypatch.setattr(
        "virtuoso_bridge.virtuoso.schematic.reader.read_schematic",
        fake_read,
    )

    result = SchematicOps(owner).read("LIB", "CELL", include_positions=True, timeout=123)

    assert result == {"instances": []}
    assert captured == {
        "client": owner,
        "lib": "LIB",
        "cell": "CELL",
        "kwargs": {"include_positions": True, "timeout": 123},
    }


def test_read_schematic_raises_on_empty_output() -> None:
    class Client:
        def execute_skill(self, skill: str, timeout: int = 300):
            return SimpleNamespace(output="", errors=[])

    with pytest.raises(RuntimeError, match="returned empty output"):
        read_schematic(Client(), "LIB", "CELL", param_filters=None)


def test_parse_schematic_defaults_non_numeric_widths() -> None:
    raw = """
INSTANCES
INST|I222<1:14>|FIRAS|LB_FCT_cunit
TERM|CINP|<*14>CINP
NETS
NET|FCT_NTUNE_D<2:0>|nil|signal|nil|I222<1:14>.CINP
PINS
PIN|FCT_NTUNE_D<2:0>|inputOutput|nil
END
"""

    data = _parse_schematic(raw, include_positions=False, filter_config=None)

    assert data["instances"][0]["name"] == "I222<1:14>"
    assert data["instances"][0]["terms"] == {"CINP": "<*14>CINP"}
    assert data["nets"]["FCT_NTUNE_D<2:0>"]["numBits"] == 1
    assert data["pins"]["FCT_NTUNE_D<2:0>"]["numBits"] == 1
