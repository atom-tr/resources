---
trigger: always_on
description: Environment awareness rule - personal development device, not a server
---

# Environment Awareness

- **Personal Device, Not Server**: The host system is a local personal device (workstation/laptop), NOT a target server, staging, or production infrastructure.
- **Prohibited System Probing**: Do NOT run commands to inspect host processes (`ps`, `top`, `kill`), open ports / listening sockets (`netstat`, `ss`, `lsof`), or operating system logs (`journalctl`, `dmesg`, `/var/log/*`). It is completely irrelevant and wastes time and tokens.
- **Workspace Focus**: Limit all operations to the workspace files, code, and official MCP tools.
