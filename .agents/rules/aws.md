---
trigger: always_on
description: AWS development and secret safety rules
---

- Project instructions override these rules.
- Prefer AWS MCP; fall back to CLI if unavailable.
- Load relevant AWS skills first; prefer skill guidance.
- Verify uncertain parameters/limits against docs; state uncertainty.
- Prefer declarative IaC (CDK/CloudFormation) over CLI.
- Follow Well-Architected Framework.
- Use hyphens (`-`), never em dashes (`—`), in resource names.

## Secret Safety
- MUST load `aws-secrets-manager` skill first for any secrets task.
- NEVER call `secretsmanager get-secret-value` or `batch-get-secret-value`, and NEVER call Secrets Manager Agent daemon directly.
- MUST use `{{resolve:secretsmanager:secret-id:SecretString:json-key}}` with `asm-exec` to resolve secrets at runtime without context leakage.
