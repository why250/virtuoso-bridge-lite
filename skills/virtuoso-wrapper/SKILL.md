---
name: virtuoso-wrapper
description: Promote verified Cadence Virtuoso SKILL operations or repeatable SKILL workflows into named, reusable Python APIs in src/virtuoso_bridge. Use when adding, extending, or refactoring a schematic, layout, Maestro, or general Virtuoso Python wrapper; do not use for one-off SKILL execution.
---

# Virtuoso Wrapper

Turn an already-validated native SKILL operation into a small, testable Python
API. Python builds, batches, and transports SKILL; the active Virtuoso CIW
still evaluates the native SKILL and remains authoritative for design changes.

## Entry gate

1. State the user-visible operation, its inputs, result, and whether it reads
   or changes a design.
2. Search the matching existing module, examples, and `skills/virtuoso`
   references before designing an API. Extend an existing wrapper when its
   abstraction fits.
3. Obtain evidence for every native SKILL call from Cadence documentation, a
   working project example, or a live Virtuoso session. Do not infer function
   names, argument order, object slots, or PDK behavior from Python code.
4. Record operation-specific prerequisites: Virtuoso version, cellview/edit
   context, GUI requirement, PDK dependency, and any save/check requirement.

For a builder-style schematic example, read
[references/schematic-instance-wrapper.md](references/schematic-instance-wrapper.md).
For bridge architecture and design rationale, read
[`../../docs/python-wrapper-design.md`](../../docs/python-wrapper-design.md).

## Choose the narrowest layer

| Need | Implementation home |
| --- | --- |
| Deterministic SKILL text from Python values | Domain `ops.py` builder returning `str` |
| Open, batch, check, and save related edits | Domain editor or operations facade |
| Structured design/result inspection | Existing or new reader API |
| One-off or not-yet-promoted operation | `VirtuosoClient.execute_skill()` after validation |

Keep a builder transport-independent: it returns SKILL and does not call the
client. Keep connection, batching, timeout, and result handling in the
existing client/editor layer. Do not introduce a second transport path.

## Implement the wrapper

1. Add the smallest semantic Python API that captures the validated operation;
   do not expose incidental temporary SKILL variables as public parameters.
2. Use shared helpers from `virtuoso.ops` for SKILL quoting, points, view types,
   and cellview lifecycle. Escape every caller-provided SKILL string.
3. Follow the neighboring module's public-export pattern and preserve
   compatibility with its existing APIs.
4. For edit workflows, batch related operations through the domain editor so
   validation and persistence occur in the established order. Do not silently
   save, delete, or open GUI windows from a builder.
5. Make failure behavior explicit. Preserve SKILL-side errors through the
   existing result/error mechanism; add Python validation only where it gives a
   clearer, deterministic error before sending SKILL.

## Complete the wrapper contract

Every promoted wrapper requires all of the following:

1. A focused Python unit test that checks generated SKILL, escaping, defaults,
   and important invalid-input behavior without requiring a Virtuoso daemon.
2. A live Virtuoso validation when the operation changes a cellview, depends on
   DFII objects, GUI state, or a PDK. If unavailable, document why and provide
   the exact manual verification procedure.
3. A runnable example in the matching `examples/01_virtuoso/<domain>/` folder
   showing the intended public API and prerequisites.
4. An update to the matching Python/API reference that maps the wrapper to the
   native SKILL it emits, including relevant limitations and prerequisites.

Run the focused tests and then the project test suite. Do not claim that a
string-level unit test proves a PDK- or GUI-dependent Virtuoso operation.

## Handoff checklist

Report the native SKILL evidence, Python API signature, emitted-SKILL test,
live-validation result or limitation, example path, and documentation update.
