# Memory

### 2026-08-01 SSH agent isolation in automated sessions

- **Symptom:** An automated agent can receive `Permission denied (publickey,...)`
  when it runs `virtuoso-bridge start` or direct SSH, while the same command
  succeeds from the user's interactive PowerShell.
- **Root cause:** The automated command process does not inherit the user's
  SSH-agent session or permission to read private keys outside the workspace.
  This is an execution-environment security boundary, not a bridge or remote
  Virtuoso failure.
- **Fix:** Run `virtuoso-bridge start` from the interactive user session, or
  use the per-user Windows Startup entry.  Once that process has established
  the local SSH tunnel, automated clients can use the existing
  `127.0.0.1:<VB_LOCAL_PORT>` TCP endpoint and execute SKILL normally.
