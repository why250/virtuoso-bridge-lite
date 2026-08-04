# Edit a schematic or layout

```text
Work in D:\Users\Administrator\Documents\GitHub\virtuoso-bridge-lite and
read AGENTS.md first.

Use the already deployed Virtuoso bridge and first run the non-mutating 1+1
probe.  If it fails, stop without changing any design data.

Target: <library>/<cell>/<schematic or layout view>
Goal: <precise change to make>

Before editing, inspect the target cellview and report its current state,
including any existing objects or connectivity relevant to the goal.  Confirm
that the opened cellview exactly matches the target.  Then use the project's
schematic/layout editing API or SKILL bridge to make the change, save it, and
provide a concise before/after summary.  Do not alter any other cellview.
```
