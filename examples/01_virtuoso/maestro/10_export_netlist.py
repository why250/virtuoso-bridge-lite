#!/usr/bin/env python3
"""Export a Maestro test/corner netlist without running a simulation.

Usage::

    python 10_export_netlist.py <LIB> <CELL>
    python 10_export_netlist.py <LIB> <CELL> --test TRAN --corner tt

The default local destination is
``output/<LIB>/<CELL>/netlist/<test>__<corner>/``. Existing destinations are
protected unless ``--overwrite`` is supplied.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from virtuoso_bridge import VirtuosoClient


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("lib", help="Library containing the Maestro view")
    parser.add_argument("cell", help="Cell containing the Maestro view")
    parser.add_argument("--test", help="Configured test (required if multiple exist)")
    parser.add_argument("--corner", default="Nominal", help="Configured corner")
    parser.add_argument("--output-root", default="output", help="Local artifact root")
    parser.add_argument("--overwrite", action="store_true", help="Replace an existing export")
    args = parser.parse_args()

    result = VirtuosoClient.from_env().maestro.export_netlist(
        args.lib,
        args.cell,
        test=args.test,
        corner=args.corner,
        output_root=Path(args.output_root),
        overwrite=args.overwrite,
    )
    print(f"Test/corner: {result.test}/{result.corner}")
    print(f"Spectre input: {result.input_scs}")
    print(f"Circuit netlist: {result.netlist}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
