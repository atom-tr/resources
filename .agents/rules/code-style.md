---
trigger: glob
globs: "**/*.sh, **/*.bash, **/*.zsh, **/*.py, **/*.md"
description: Code style and comment standards
---

- Comments in English only.
- Bash: prefer readable 1-liners; scripts only when logic requires.
- Python: PEP 8; prefer stdlib over third-party unless standard.
- Handle errors explicitly; no silent failures.
