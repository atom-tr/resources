---
trigger: model_decision
description: Infrastructure as Code (IaC), secrets management, idempotency, versioning, and structured logging guidelines
---

# Infrastructure & DevOps Practices

## IaC
- Prefer declarative over imperative approaches (Terraform, Helm, Kustomize)

## Secrets
- Never hardcode secrets; use environment variables, Vault, or Sealed Secrets

## Idempotency
- All scripts and configurations must be safe to re-run

## Versioning
- Always pin versions for tools, images, and dependencies — avoid `latest`

## Logging
- Use structured logging (JSON preferred) for scripts and services
