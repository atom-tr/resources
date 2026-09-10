---
trigger: always_on
description: Mandatory requirement to check and prioritize available MCP tools before executing shell commands, CLI tools, or web searches
---

# MCP First Policy

- **Mandatory MCP Priority**: ALWAYS check and prioritize available MCP tools (`kubernetes`, `grafana`, `codegraph`, `cloudflare`, etc.) before running shell commands, CLI tools, or web searches.
- **Strict Prohibition**: Never use manual shell commands or CLI (e.g., `kubectl`, `curl`, raw API requests) when a dedicated MCP tool exists for that task.
- **Codegraph Prerequisites**: For `codegraph`, ensure `nvm use 22` and run `codegraph sync` before querying or using codegraph tools.
- **Auth Failure Protocol (Stop & Ask)**: If an MCP tool fails due to authentication, authorization, or credentials (401, 403, expired token, missing context), DO NOT attempt shell commands or retry alternative CLI commands. The CLI shares the same environment and will also fail, wasting time and tokens. IMMEDIATELY stop and ask the user to verify authentication and check CLI credentials.
- **No Wasteful Retries**: Never retry alternative commands as a workaround for authentication or permission failures.
