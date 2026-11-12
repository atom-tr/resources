---
trigger: model_decision
description: IaC and DevOps practice standards
---

- Declarative IaC (Terraform, Helm, Kustomize) over imperative.
- Never hardcode secrets; use env vars, Vault, or Sealed Secrets.
- All scripts/configs must be idempotent (safe to re-run).
- Pin versions for tools, images, dependencies; avoid `latest`.
- Structured JSON logging for scripts and services.
