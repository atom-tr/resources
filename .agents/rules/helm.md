---
trigger: glob
globs:
  - "**/Chart.yaml"
  - "**/values*.yaml"
  - "**/templates/**"
  - "**/charts/**"
description: Helm chart conventions, values.yaml editing rules, and upgrade safety guidelines
---

# Helm Chart

## values.yaml
- Do NOT delete default values or default comments; keep them for upgrade comparison

## Naming
- Follow official Helm chart naming conventions

## Upgrade Safety
- Edit directly in `values.yaml`; download the upstream default `values.yaml` to local only for diff comparison — do NOT push the default file to git
