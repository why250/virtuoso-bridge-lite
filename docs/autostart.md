# Bridge Autostart and Persistent CIW Loading

This guide keeps the remote bridge resources across server reboots, starts the
local SSH tunnel after Windows sign-in, and loads the bridge automatically when
Virtuoso starts.

## 1. Use a persistent remote deployment directory

The default remote scratch root is `/tmp`, which can be cleared on a reboot or
by a cleanup policy.  Set these values in the local project `.env` instead:

```dotenv
VB_REMOTE_SCRATCH_ROOT=/home/<remote-user>/.virtuoso-bridge
VB_CLIENT_ID=<stable-local-client-id>
```

`VB_CLIENT_ID` must remain stable for a given local Windows account.  It makes
the generated CIW setup path stable and prevents two local clients sharing an
EDA account from overwriting one another.

Run `virtuoso-bridge start` once after changing the configuration.  It deploys
the resources to this path:

```text
<scratch-root>/virtuoso_bridge_<remote-user>/<client-id>/virtuoso_bridge/virtuoso_setup.il
```

For example, with `remote-user=userone` and `client-id=Administrator`, the
load form is:

```lisp
load("/home/userone/.virtuoso-bridge/virtuoso_bridge_userone/Administrator/virtuoso_bridge/virtuoso_setup.il")
```

## 2. Load the bridge whenever Virtuoso starts

Append the generated `load(...)` form to the remote user's `~/.cdsinit`.
Do this only after the first `virtuoso-bridge start` has deployed the persistent
file.  The `.cdsinit` entry is evaluated inside each new Virtuoso process; it
loads `ramic_bridge.il` and starts the daemon as that Virtuoso process's child.

To avoid duplicate lines, run the following on the remote host, substituting
the generated load path:

```bash
grep -Fqx 'load("<persistent-setup-path>")' ~/.cdsinit 2>/dev/null || \
  printf '\nload("<persistent-setup-path>")\n' >> ~/.cdsinit
```

## 3. Start the tunnel when Windows signs in

The repository includes `scripts/start-bridge-at-logon.ps1`.  It waits 30
seconds for networking and the SSH agent, then runs `virtuoso-bridge start`.
On failure it retries five times at 15-second intervals.  Its log is written
to:

```text
%LOCALAPPDATA%\virtuoso-bridge\autostart.log
```

Install the current-user Startup entry from PowerShell in the repository root:

```powershell
.\scripts\install-bridge-autostart.ps1
```

The installer creates a shortcut in the Windows Startup folder.  It runs after
the user signs in, not at pre-login machine boot.  This is intentional: the
SSH key or SSH agent normally belongs to the interactive user session.

Remove the entry with:

```powershell
.\scripts\install-bridge-autostart.ps1 -Uninstall
```

## 4. Verify the complete path

After signing in, confirm the local tunnel and remote daemon are available:

```powershell
.\.venv\Scripts\python.exe -c "from virtuoso_bridge import VirtuosoClient; r=VirtuosoClient.from_env().execute_skill('1+1'); print(r.status, r.output, r.errors)"
```

Expected output contains `ExecutionStatus.SUCCESS` and `2`.

If it fails, inspect the autostart log first.  If the log reports SSH
authentication failure, make sure `ssh -o BatchMode=yes <host> "echo ok"`
works from an interactive PowerShell session.  If the tunnel works but the
daemon does not respond, start Virtuoso or check that the persistent `load(...)`
entry is present in `~/.cdsinit`.
