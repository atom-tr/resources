---
trigger: always_on
description: Personal workstation boundaries
---

- Host is a local workstation, NOT a server.
- Do NOT inspect host processes (`ps`, `top`, `kill`), ports (`netstat`, `ss`, `lsof`), or logs (`journalctl`, `dmesg`, `/var/log/*`).
- Restrict operations to workspace files, code, and MCP tools.
- NEVER read or inspect `.env*` files.
