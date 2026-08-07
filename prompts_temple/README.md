# Prompt templates

Copy a template into a new conversation and replace every `<...>` placeholder.
The bridge must already have an active local tunnel; each template starts with a
non-mutating `1+1` probe.  If that probe fails, the agent should report the
connection failure and make no design changes.

| Template | Use it for |
| --- | --- |
| `00-bridge-session.md` | A general Virtuoso task |
| `01-execute-skill-read-only.md` | Execute supplied SKILL without modifying a design |
| `02-inspect-virtuoso-state.md` | Inspect the active Virtuoso session |
| `03-edit-schematic-or-layout.md` | Change a specific schematic or layout cellview |
| `04-run-spectre.md` | Run a remote Spectre simulation |
| `05-maestro-ade.md` | Inspect or operate a Maestro/ADE session |

The templates assume this repository is the working directory and use the
project's `AGENTS.md` conventions.
