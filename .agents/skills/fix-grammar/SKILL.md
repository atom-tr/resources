---
name: fix-grammar
description: Fix grammar and spelling of English text using a local model. Use when the user asks to correct grammar or polish English text.
---
Pass the text via stdin using a quoted heredoc, never as a command argument:

fixg <<'EOF'
<text>
EOF

Return the output as-is. If it exits non-zero, report the error. Do not fix the text yourself.