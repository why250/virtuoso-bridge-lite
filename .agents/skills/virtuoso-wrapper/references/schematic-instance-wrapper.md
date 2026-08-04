# Example: Create a schematic instance wrapper

This existing implementation shows the smallest useful promotion path from a
native SKILL operation to a reusable Python API. It is a structural reference;
validate any new operation independently for its Virtuoso version, PDK, and
cellview context.

## Native SKILL operation

Creating an instance needs a master cellview and a target cellview. For the
`analogLib/res/symbol` example, the essential native SKILL shape is:

```skill
let((rbMaster)
  rbMaster = dbOpenCellView("analogLib" "res" "symbol")
  dbCreateInst(cv rbMaster "R0" '(0.000 0.000) "R0"))
```

`cv` is the target schematic cellview. The wrapper must not assume that a
master can be created, that its `symbol` view is present, or that the caller's
PDK provides the same library; those are environment prerequisites.

## Python builder

[`src/virtuoso_bridge/virtuoso/schematic/ops.py`](../../../src/virtuoso_bridge/virtuoso/schematic/ops.py)
implements this as:

```python
schematic_create_inst_by_master_name(
    lib, cell, view, instance_name, x, y, orientation,
    *, cv_expr="cv", view_type=None, mode="r",
) -> str
```

The builder returns SKILL rather than executing it. It:

- maps logical view names to view types when they differ;
- escapes each caller-supplied SKILL string;
- formats coordinates with the shared point helper;
- binds the opened master in a local SKILL variable; and
- emits `dbCreateInst` against an injectable target cellview expression.

This separation lets unit tests inspect generated SKILL without a live daemon
and lets different editors batch the operation appropriately.

## Public use in an edit workflow

The existing RC schematic example uses the builder through the schematic
editor:

```python
from virtuoso_bridge.virtuoso.schematic.ops import (
    schematic_create_inst_by_master_name as inst,
)

with client.schematic.edit(lib, cell) as sch:
    sch.add(inst("analogLib", "res", "symbol", "R0", 0.0, 0.0, "R0"))
    # On successful exit, the editor batches commands, then runs schCheck and dbSave.
```

See
[`examples/01_virtuoso/schematic/01a_create_rc_stepwise.py`](../../../examples/01_virtuoso/schematic/01a_create_rc_stepwise.py)
for the complete runnable flow.

## How to copy the pattern

1. Prove the native SKILL form in the intended Virtuoso environment.
2. Build only the variable portion in the matching domain `ops.py`; reuse the
   shared escaping and formatting helpers.
3. Return the SKILL string and let the existing editor/client decide execution
   and persistence.
4. Add a daemon-free test that asserts the important generated fragments and
   escaped values, then perform the operation-specific live validation.
5. Add a public example and document the native SKILL mapping and prerequisites.

Do not copy the `dbCreateInst` details for a different operation by analogy.
For example, terminal geometry, layout layers, Maestro sessions, and PDK CDF
parameters each require their own verified native SKILL contract.
