---
trigger: glob
globs: "**/Chart.yaml, **/values*.yaml, **/templates/**, **/charts/**"
description: Helm chart conventions and upgrade safety
---

- Do NOT delete default values or comments in `values.yaml`; preserve for upgrade diffs.
- Follow official Helm naming conventions.
- Edit `values.yaml` directly; download upstream defaults only for local diff — NEVER push them to git.
