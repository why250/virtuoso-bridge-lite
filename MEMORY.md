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

### 2026-08-04 Keep Virtuoso Bridge `.cdsinit` load paths on one line

- **Symptom:** Virtuoso reports `*Error* load: can't access file` for the
  bridge setup file even though the file exists.
- **Root cause:** The `load("...")` string was split across two lines.  SKILL
  treats the embedded newline and indentation as path whitespace, producing a
  different, nonexistent filename.
- **Fix:** Keep the bridge entry as one quoted line, for example
  `load("/home/<user>/.virtuoso-bridge/.../virtuoso_setup.il")`.  Verify the
  exact stored line remotely after editing; terminal display wrapping is not
  itself a problem.
