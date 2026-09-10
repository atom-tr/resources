---
trigger: glob
globs:
  - "**/*.sh"
  - "**/*.bash"
  - "**/*.zsh"
  - "**/*.py"
description: Code style standards for Bash and Python scripts, comments, and error handling
---

# Code Style

## Comments
- Always write code comments in English

## Bash
- Prefer single-line commands where readable; use scripts only when logic requires it

## Python
- Follow PEP 8; prefer stdlib over third-party libs unless a library is the standard tool

## Error Handling
- Always handle errors explicitly — no silent failures
