---
trigger: always_on
description: MCP-first enforcement
---

- ALWAYS use MCP tools (`kubernetes`, `grafana`, `codegraph`, `cloudflare`) before shell/CLI/web search. Never run manual commands when MCP exists.
- On MCP auth failure (401, 403, expired token): STOP and ask user to verify auth. Do NOT retry via shell/CLI.
