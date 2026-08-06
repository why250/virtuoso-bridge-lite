---
name: ic-transfer
description: Transfer local files and directories to or from IC_Server_Local using the personal IC Transfer HTTP service. Use whenever a request names IC_Server_Local, asks to upload/download/sync files with it, or moves local Python/source files, simulation artifacts, logs, or result directories to that host. Do not use for other SSH hosts.
---

# IC Transfer

Use `ic-transfer`, not direct SCP/SFTP or `ops.upload/download`, for routine local↔`IC_Server_Local` file transfer. The service reads its URL and token from the local user config; never request, print, inspect, commit, or log the token.

## Workflow

1. Confirm the service is reachable before a transfer:

   ```powershell
   & D:\Users\Documents\GitHub\ic-transfer\.venv\Scripts\ic-transfer.exe health
   ```

   If the CLI is on `PATH`, `ic-transfer health` is equivalent. Do not attempt an authenticated transfer if health fails; report the service failure.

2. Upload a regular file with a server-relative POSIX destination:

   ```powershell
   & D:\Users\Documents\GitHub\ic-transfer\.venv\Scripts\ic-transfer.exe upload `
     .\local\script.py 'project/script.py'
   ```

3. Upload a directory with the same command. The client ZIPs it locally and the server safely extracts it:

   ```powershell
   & D:\Users\Documents\GitHub\ic-transfer\.venv\Scripts\ic-transfer.exe upload `
     .\results 'results/run-01'
   ```

4. Download using a server-relative path and an explicit local file path:

   ```powershell
   & D:\Users\Documents\GitHub\ic-transfer\.venv\Scripts\ic-transfer.exe download `
     'results/run-01/output.txt' .\output.txt
   ```

5. Compare the SHA-256 values printed by upload and download when verifying a round trip. Existing destinations require an explicit `--overwrite`.

## Guardrails

- Use `/` in every remote path. Reject absolute paths, `..`, and Windows backslashes.
- Keep shell commands on separate PowerShell lines; a trailing `&` backgrounds a job.
- Do not use direct `scp`, `sftp`, `rsync`, `ops.upload/download`, base64, or manual HTTP requests for this host's routine file transfer.
- Do not reveal `IC_TRANSFER_TOKEN`, read `~/.ic-transfer/.env`, or place secrets in repository `.env` files. Run `ic-transfer config set` only when a user needs to configure their own client.
- The service does not list or delete remote files. Do not invent those operations.

## Service unavailable

If `health` fails, do not silently change protocol. Report the failure. When the user explicitly authorizes a fallback for a necessary source deployment, use the `git-archive-scp-transfer` workflow: committed Git archive only, local and remote SHA-256 verification, and a new explicit staging directory.
