# Architecture

`virtuoso-bridge` makes an already-running Virtuoso session available to a
local Python program or CLI.  It deliberately separates remote transport from
SKILL execution: SSH reaches the remote machine, while the live Virtuoso
process evaluates the SKILL code.

## Components

| Component | Runs in | Responsibility |
| --- | --- | --- |
| `VirtuosoClient` | Local Python process | Sends a SKILL request to a TCP endpoint and turns the reply into `VirtuosoResult`.  It has no SSH dependency. |
| `SSHClient` / CLI | Local machine | Deploys bridge resources, maintains the SSH port forward, and records its state.  This layer is not used in local mode. |
| Bridge daemon | Remote machine, child of Virtuoso | Listens for one TCP request at a time and translates between JSON/TCP and the Virtuoso IPC pipes. |
| `ramic_bridge.il` | Inside the Virtuoso SKILL runtime | Starts and observes the daemon, evaluates received SKILL, and writes its result back through IPC. |

## Remote request path

```text
Local Python or CLI
    |  JSON: {"skill": "...", "timeout": N}
    v
VirtuosoClient -> 127.0.0.1:<local port>
    |  SSH -L forward (encrypted)
    v
Remote bridge daemon -> stdin/stdout IPC pipes
    v
Virtuoso `RBIpcDataHandler` -> `evalstring(...)`
    |  result or SKILL error markers
    +----------------------------------------> VirtuosoResult on the local client
```

For a simple expression, the daemon writes a wrapper such as
`let(((__vb_r 1+2)) hiFlush() __vb_r)` to its stdout.  Virtuoso receives that
text in the `ipcBeginProcess` data handler, evaluates it in the current
Virtuoso process, and sends the result to the daemon with `ipcWriteProcess`.
Multiline requests are written to a temporary `.il` file and evaluated with
`load()` so comments and multiple forms retain their meaning.

The daemon is a transport adapter, not a Cadence API implementation.  It does
not manipulate cellviews or ADE directly; SKILL always runs in the existing
Virtuoso session and therefore has access to that session's libraries,
windows, edit context, and loaded PDK environment.

## Startup and lifecycle

1. `virtuoso-bridge start` detects a usable remote Python, uploads the Python
   daemon and SKILL files to a per-user, per-client temporary directory, then
   starts an SSH local-port forward.
2. It prints the `load(".../virtuoso_setup.il")` form.  Loading that form in
   the target Virtuoso CIW sets bridge paths and port, loads
   `ramic_bridge.il`, and calls `RBStart()`.
3. `RBStart()` uses the SKILL API `ipcBeginProcess(...)` to launch the Python
   daemon as a child of Virtuoso.  SKILL IPC callbacks receive daemon stdout,
   stderr, and process-exit events.
4. Each request is handled serially.  A timeout watchdog interrupts the
   Virtuoso process if a request fails to return, preventing a stuck call from
   blocking the bridge forever.

The `start` command does not itself control the Virtuoso GUI.  The CIW load is
the bootstrap action that attaches the network bridge to the intended live
session.

## Why SSH alone is insufficient

SSH can run shell commands or start a separate batch Virtuoso process, but it
does not provide a supported command channel into an already-running GUI
Virtuoso session.  A newly launched batch process would not share the active
session's windows, selected objects, ADE state, or in-memory context.  The
daemon plus `ipcBeginProcess` uses Virtuoso's managed child-process pipes to
create that channel while keeping execution inside the existing process.

## Security boundary

Remote deployment and normal client traffic rely on passwordless SSH and its
local port forward.  The daemon protocol itself is intentionally small and
does not add a separate authentication layer; treat its listener as a trusted
endpoint.  In particular, review its bind address and firewall exposure before
using the bridge on a shared or untrusted network.

## Independent Spectre path

Spectre simulation is intentionally separate.  `SpectreSimulator` uses SSH to
run simulation commands and retrieve artifacts; it does not require the
Virtuoso daemon or a loaded SKILL bridge.
