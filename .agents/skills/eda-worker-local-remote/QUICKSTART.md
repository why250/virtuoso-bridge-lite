# EDA-worker Local↔Remote — Quickstart

Transport layer for Cursor ↔ eda-worker: MCP shell + `ops.upload` / `ops.download`. Agent entry: [SKILL.md](SKILL.md).

## Prerequisites

1. eda-worker entry in `%USERPROFILE%\.cursor\mcp.json` with `url`, `X-EDA-Token`, and `X-EDA-Tools`.
2. `python -m ops.upload --help` works on PATH (ops discovers workers from mcp.json).
3. Cursor has the matching MCP server loaded (e.g. `eda-worker-linux--sz16` → `user-eda-worker-linux--sz16`).

### mcp.json shape (placeholders only)

```json
{
  "mcpServers": {
    "eda-worker-linux--sz16": {
      "url": "http://<worker-host>:8092/mcp",
      "headers": {
        "X-EDA-Token": "<your-token>",
        "X-EDA-Tools": "ads,ansys,matlab,virtuoso"
      }
    }
  }
}
```

Do not commit real tokens.

## Manual CLI

### Upload

```powershell
python -m ops.upload C:\path\to\local\file.sh /home/eda_grp/weihaoyu/skills/file.sh
# Multiple workers:
python -m ops.upload --host <worker-host> .\local.txt /home/eda_grp/weihaoyu/tmp/local.txt
```

### Download

```powershell
python -m ops.download /home/eda_grp/weihaoyu/tmp/local.txt .\local.txt
python -m ops.download --host <worker-host> /home/eda_grp/weihaoyu/tmp/local.txt
```

### Remote shell (via MCP, not SSH)

Use the loaded eda-worker server and the domain EDA prefix, e.g. `ads__system`.

MCP shells are non-interactive and do **not** auto-run `~/.bashrc`. Always prefix with `source ~/.bashrc` (eda-worker `shell_guard` **blocks** `bash -lc`):

```text
action=shell
command=source "$HOME/.bashrc" >/dev/null 2>&1 || true; hostname; pwd; command -v python3; echo ok
```

Long jobs: raise timeout or run in background and poll; confirm remote logs before treating a timeout as failure. Domain product env (e.g. ADS install discovery) may still live in domain scripts if not already in `~/.bashrc`.

**Two-phase poll (agents):** after `cmd &`, poll every **10s for the first 60s**, then every **30s** until done or domain timeout. Check the exit/status file every poll; stop immediately when complete. Do not start with a 30–90s blind sleep.

### Mirror a remote folder

1. List files (`file_list` or `find <remoteDir> -maxdepth 1 -type f`).
2. Create the local directory.
3. Download each file (≤50MB each). Prefer the call operator (`&`) so `-Files` arrays stay intact:

```powershell
& .cursor/skills/eda-worker-local-remote/scripts/mirror_download.ps1 `
  -RemoteDir "/home/eda_grp/weihaoyu/example/BJT_IV_Gm_PowerCalcs/output/runs/20260715_024311/01_sim" `
  -LocalDir ".\example\BJT_IV_Gm_PowerCalcs\output\runs\20260715_024311\01_sim" `
  -Files @("hpeesofsim_stdout.log", "BJT_IV_Gm_PowerCalcs.ds", "netlist.log")
```

Do **not** nest `powershell -File … -Files @("a","b")` — `-File` only binds the first array element (remaining names become unbound positionals). The helper collects leftovers as a fallback, but `&` is correct.

Or loop manually:

```powershell
python -m ops.download "$remoteDir/$name" (Join-Path $localDir $name)
```

## Expected behavior

| Step | Success signal |
|------|----------------|
| health / capabilities | `STATUS=OK` (or equivalent) |
| shell smoke | `EXIT_CODE=0`, stdout shows hostname / `ok`; `python3` resolved if set in `~/.bashrc` |
| upload | remote path exists (`file_list` or `ls`) |
| download | local file non-empty |
| mirror | all listed files present under `-LocalDir` |

## Troubleshooting

| Symptom | Check |
|---------|--------|
| AmbiguousWorker | More than one eda-worker in mcp.json → `ops.upload --host <ip>` |
| Auth / 401 | Token in mcp.json `X-EDA-Token`; reload Cursor MCP |
| File >50MB | Split, compress, or use another transfer path |
| shell_guard block | Avoid `bash -lc` (blocked); use `source ~/.bashrc; …`. Other bans → rephrase or run via a script file |
| Shell MCP timeout (incl. long ADS export/sim) | Background job + two-phase poll (10s for 60s, then 30s); check remote artifacts before assuming failure |
| `PositionalParameterNotFound` / only first file mirrored | Nested `powershell -File` + `-Files @(...)` — use `& .\mirror_download.ps1 …` instead |
| `command not found` / wrong PATH | Prefix with `source "$HOME/.bashrc" >/dev/null 2>&1 || true;`; confirm vars in worker profile |
| Empty local download | Absolute remote path; confirm with `file_list`; file ≤50MB |
| Wrong worker | Match `--host` to mcp.json `url` host; prefer `eda-worker-linux--*` |

## Related

- Domain example (ADS): [../ads-netlist-simulation-eda-worker/SKILL.md](../ads-netlist-simulation-eda-worker/SKILL.md)
- Self-hosted shell MCP (different stack): repo `notes/self-hosted-remote-shell-mcp.md`
