# Astro blog output & cover image (only read this file when needed)

Read this file only when the user explicitly asks for "markdown", "blog post", "Astro", a
downloadable file, or a cover image for the digest. For normal conversational digest requests,
ignore this file entirely and use the default report format in SKILL.md.

## Astro blog mode

Create an actual `.md` file (write to the outputs directory and present it) with this EXACT
structure. Output ONLY the file — no explanation before/after it in chat:

```
---
title: "DevOps News - Last <window>"
description: "High-signal DevOps updates, security alerts, and changelogs"
pubDate: "<ISO_DATE>"
author: "atomtr"
tags: ["devops", "kubernetes", "aws", "cicd", "security"]
---

## 🔥 Key Highlights
- ...

---

## 🚀 New Tools / Tech
### [Tool Name]
- What it is:
- Why it matters:
- Source:

---

## ⚙️ Important Updates
### [Tool / Version]
- Key changes:
- Impact:
- Source:

---

## 🔐 Security Alerts
### [CVE-ID]
- Severity:
- Affected systems:
- Impact:
- Mitigation:
- Source:

---

## 📰 Notable News
### [Headline]
- Summary:
- Why it matters:
- Source:

---

## 📄 Changelog Highlights
### [Project Name]
- Key changes:
- Breaking changes:
- Source:

---

## 🧠 Notes
- Short insight or trend observation (optional)
```

If there's nothing high-impact in the window, still generate the file and state plainly:
"No significant high-impact DevOps updates in the last `<window>`."

Language: if the conversation is in Vietnamese, write the digest content in Vietnamese but keep
tool names, CVE IDs, version numbers, and technical terms in English.

## Cover image (only if user asks for one)

Style prompt to use with an image generation tool:

"A minimalist monochrome blog cover for a DevOps article, styled like a clean dashboard UI, black
and white color palette, bold geometric sans-serif font, thick outlined containers, flat design,
no shadows or gradients, structured grid layout, subtle icons, modern brutalist interface style,
high contrast, simple and professional, large title text area, tech-focused aesthetic."
