---
name: eda-worker-local-remote
description: >-
  Local↔eda-worker transport via MCP shell and ops.upload/ops.download, with
  default discovery from %USERPROFILE%\.cursor\mcp.json. Use when uploading or
  downloading files to a remote Linux worker, running remote bash through
  ads__/matlab__/virtuoso__/ansys__system, mirroring a remote directory locally,
  or when a domain skill needs eda-worker / sz16 local-server interaction without
  re-documenting MCP or ops CLI.
---

# EDA-worker Local↔Remote Transport

Generic transport layer for Cursor ↔ eda-worker. Domain skills (ADS netlist, MATLAB, Virtuoso, …) describe **what** to run; this skill describes **how** to shell and transfer files.

## For domain skill authors

| Keep in the domain skill | Link here instead |
|--------------------------|-------------------|
| Remote script paths, product flags, artifact layout | mcp.json resolution |
| Which `__system` prefix (`ads__system`, …) | Full shell / ops recipes + `source ~/.bashrc` wrap |
| Domain timeouts, guardrails, post-process | Directory mirror mechanics |
| Product install discovery (e.g. ADS `ads_env.sh`) unless already in worker bashrc | User PATH / profile init |

**Reuse contract**

1. Before inventing MCP or ops usage, read this file (or [QUICKSTART.md](QUICKSTART.md)).
2. Do not re-document full mcp.json / ops / shell recipes — one pointer + domain paths/commands.
3. You may pin EDA prefix and remote home; this skill resolves the MCP server and tool call pattern.

## Resolve MCP server

Config file: `%USERPROFILE%\.cursor\mcp.json` (example: `C:\Users\sn06071\.cursor\mcp.json`).

1. Prefer a key matching `eda-worker-linux--*` (e.g. `eda-worker-linux--sz16`).
2. Cursor may load it as `user-eda-worker-linux--sz16` — same server; use the loaded name for `CallMcpTool`.
3. Multiple workers → pass `ops.upload --host <ip>` / `ops.download --host <ip>` matching the `url` host in mcp.json.
4. Else use the first `eda-worker*` entry.

Typical entry shape (tokens redacted in docs):

```json
"eda-worker-linux--sz16": {
  "url": "http://<host>:8092/mcp",
  "headers": {
    "X-EDA-Token": "<token>",
    "X-EDA-Tools": "ads,ansys,matlab,virtuoso"
  }
}
```

## Pick `__system` tool

Use the EDA prefix the domain skill or user needs:

| Prefix | When |
|--------|------|
| `ads__system` | ADS workflows (default for ADS domain skills) |
| `matlab__system` | MATLAB |
| `virtuoso__system` | Virtuoso |
| `ansys__system` | ANSYS |

Common actions: `shell`, `file_list`, `health`, `capabilities`, `preflight` (DISPLAY on Linux).

## Remote shell

One-shot non-interactive bash (not SSH). MCP `action=shell` does **not** auto-load `~/.bashrc` the way an interactive terminal does — always prefix so the worker user profile applies (PATH, `python3`, license vars, etc.).

**Default command wrapper** (use this for every shell call):

```text
CallMcpTool → server=<resolved eda-worker> toolName=<eda>__system
  arguments: {
    "action": "shell",
    "command": "source \"$HOME/.bashrc\" >/dev/null 2>&1 || true; <remote command>"
  }
```

Example (`ads__system`):

```text
action=shell
command=source "$HOME/.bashrc" >/dev/null 2>&1 || true; hostname; pwd; command -v python3; echo ok
```

Do **not** use `bash -lc '…'` as the default — eda-worker `shell_guard` blocks it. If you see that block, retry with the `source ~/.bashrc` form above.

- Long jobs: raise timeout, or `cmd &` + poll logs / status files. Do not treat a shell timeout as job failure without checking remote artifacts.
- **Two-phase poll (agents):** after backgrounding a long remote job, do **not** sleep 30–90s blindly:
  1. **First 60s:** poll every **10s** (check exit/status file or log tail each time)
  2. **After 60s:** poll every **30s** until done or the domain script timeout
  Stop as soon as the exit/status file appears (or shows completion).
- `shell_guard` may also block other patterns; rephrase or use domain scripts.
- Prefer absolute paths on the worker.
- User profile init (`~/.bashrc`) belongs here. Product-specific discovery (e.g. ADS `HPEESOF_DIR` / `LD_LIBRARY_PATH` in domain `ads_env.sh`) stays in the domain skill unless that env is already in the worker’s bashrc.

## File transfer

**Only** these CLIs for bulk transfer (≤50MB per file). Never use MCP `file_write` / `file_read` / base64 for routine transfers (inspect-only).

```text
python -m ops.upload <local> <remote>
python -m ops.download <remote> [<local>]
```

- `/home/...` and `/root/...` remotes → worker channel (auto).
- Ambiguous workers → `--host <ip>` from mcp.json `url`.
- `--via-worker` is deprecated; prefer path-based channel selection.

## Mirror a remote directory

ops has no recursive directory download:

1. `file_list` on remote dir, or shell `find <dir> -maxdepth 1 -type f`
2. Create local directory
3. Per file: `python -m ops.download <remote>/<name> <local>/<name>`

Helper: [scripts/mirror_download.ps1](scripts/mirror_download.ps1) (agent still supplies the file name list).

**Call with `&`, not nested `powershell -File`:**

```powershell
& .cursor/skills/eda-worker-local-remote/scripts/mirror_download.ps1 `
  -RemoteDir "/home/.../01_sim" `
  -LocalDir ".\example\...\01_sim" `
  -Files @("hpeesofsim_stdout.log", "cell.ds")
```

`powershell -File … -Files @("a","b")` only binds the first name (PowerShell `-File` quirk). The script collects remaining args as a fallback, but `&` is the preferred call.

When both sides share a project-root convention, keep the **same relative path** under remote home and local `$projectRoot`.

## Smoke checks

1. `<eda>__system` `action=health` (and `capabilities` if useful)
2. Shell with profile: `source "$HOME/.bashrc" >/dev/null 2>&1 || true; hostname; pwd; command -v python3; echo ok`
3. Tiny upload + download round-trip of a small text file

## Out of scope

- ADS / MATLAB / Virtuoso product scripts and semantics
- GUI session tools (`ads__session`, …)
- SSH or self-hosted shell MCP (see repo `notes/self-hosted-remote-shell-mcp.md`)

User-facing CLI and troubleshooting: [QUICKSTART.md](QUICKSTART.md).
