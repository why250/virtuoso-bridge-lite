# Python Wrapper Design

## Purpose

`virtuoso-bridge` does not replace Cadence SKILL.  Virtuoso still evaluates
native SKILL in the active CIW session.  The Python package under
`src/virtuoso_bridge` provides a higher-level, local interface for selected,
validated Virtuoso workflows.

The purpose of a wrapper is to turn a proven SKILL operation into a named,
reusable Python function.  It gives users and automated clients a stable API
instead of requiring each caller to reconstruct the same raw SKILL text.

```text
Python API call
    -> Python builder / wrapper
    -> native SKILL string or operation batch
    -> VirtuosoClient transport
    -> active Virtuoso CIW evaluates the SKILL
```

For example, a schematic helper can build SKILL using `dbCreateInst` or
`schCreateWire`; it does not emulate a schematic database in Python.  Python
organizes and validates the request, while the running Virtuoso session
performs the actual design operation with its loaded PDK, libraries, and GUI
context.

## Why wrappers exist

Wrappers make common operations safer and easier to reuse:

- **Validated construction.** A builder centralizes the known-good SKILL form,
  argument order, quoting, coordinate formatting, and required setup.
- **Semantic API.** A call such as `add_wire_between_instance_terms(...)`
  expresses intent without requiring callers to manually locate terminal
  coordinates or reconstruct the SKILL implementation.
- **Workflow safeguards.** A context manager can collect related operations,
  then run `schCheck` and `dbSave` at the correct point.
- **Less repeated raw SKILL.** LLMs and users can call documented Python APIs
  for supported operations rather than independently composing unfamiliar
  SKILL snippets on every task.
- **Testable behavior.** The Python-level API, generated SKILL, and an
  end-to-end Virtuoso result can each be covered by examples and tests.

## Scope and boundaries

`VirtuosoClient.execute_skill(...)` remains the raw escape hatch: it sends a
SKILL string to the existing session.  It is appropriate for a small
read-only expression or a Cadence feature that has no wrapper yet.

Raw SKILL is not an invitation to guess function names, signatures, or PDK
behavior.  For a design operation, prefer an existing wrapper.  If none
exists, first validate the native SKILL through Cadence documentation, a
working project example, or the active Virtuoso session.  Only then should it
be sent directly or promoted into a wrapper.

The wrappers are intentionally not a complete Cadence API.  They cover the
workflows that this project has verified and maintains.  Cadence-specific,
version-dependent, or PDK-specific operations may still require native SKILL
and additional validation.

## Extension path

A new native SKILL capability should become a reusable wrapper only after its
operation and constraints are understood.  The normal extension path is:

1. Validate the native SKILL command or complete workflow against the target
   Virtuoso version and relevant PDK/design context.
2. Add a focused builder or wrapper in the matching package area, such as
   `virtuoso/schematic`, `virtuoso/layout`, or `virtuoso/maestro`.
3. Put transport-independent SKILL string construction in a builder where
   practical; keep transport and result handling in the client/editor layer.
4. Add an example that shows the intended API and any prerequisite context.
5. Add tests for generated SKILL and, when a live Virtuoso test is available,
   for the resulting operation.
6. Document the Python API, the native SKILL operations it emits, limitations,
   and any relevant PDK or GUI constraints.

After this process, clients call the Python API rather than repeatedly writing
the underlying SKILL.  The raw SKILL remains visible and auditable in the
implementation, while the wrapper supplies a stable interface for routine
use.

## Current schematic pattern

The schematic package illustrates the separation:

- `virtuoso/schematic/ops.py` builds native SKILL strings.
- `virtuoso/schematic/editor.py` batches operations and runs the schematic
  check/save sequence on successful context-manager exit.
- `VirtuosoClient` sends the resulting request to the active Virtuoso session.

This division keeps the Python API convenient without obscuring that Cadence
SKILL, evaluated by Virtuoso, is the authority for design changes.
