---
name: devops-news-digest
description: >
  Generate a high-signal DevOps news digest summarizing new tools, critical version updates
  (GitLab, Jenkins, ArgoCD, Kubernetes, AWS, Grafana, Terraform, Docker, Prometheus),
  CVEs/security alerts for CI/CD and cloud-native infra, and notable ecosystem news for a given
  time window (default last 24h). Use this skill whenever the user asks for a "DevOps news
  digest", "DevOps update", "what happened in DevOps", "security alerts for CI/CD/Kubernetes",
  or invokes it explicitly (e.g. "/devops-news", "run my devops digest"). Also trigger if the
  user asks to turn this recurring research task into a scheduled or repeatable report. Default
  output is a conversational Markdown report; a strict Astro-compatible frontmatter blog file and
  a cover-image style prompt are available in references/astro-output.md, loaded only when the
  user asks for "markdown"/"blog post"/"Astro" or a cover image.
---

# DevOps News Digest

Produces a high-signal, engineer-facing summary of DevOps-relevant developments for a given time window (default: last 24h, but honor any window the user specifies, e.g. "last week").

## Workflow

1. **Determine the window.** Default to last 24h unless the user specifies otherwise (last week, last month, etc.). State the window used at the top of the output.
2. **Research using web_search / web_fetch.** Cover these categories, scaling search calls to the window size (more searches for "last week" than "last 24h"):
   - New tools/platforms/frameworks in DevOps, platform engineering, AI+infra automation
   - Version/release updates for: GitLab, Jenkins, ArgoCD, Kubernetes, AWS, Grafana (esp. self-hosted), Terraform, Docker, Prometheus
   - GitHub trending repos (DevOps-related) and high-engagement Hacker News/Reddit threads
   - CVEs / actively exploited vulnerabilities in CI/CD, Kubernetes/containers, cloud infra, GitLab/Jenkins — prioritize NVD, GitHub Security Advisories, vendor security bulletins
   - Partnerships, acquisitions, ecosystem shifts affecting DevOps workflows
   - Official changelogs — extract only key/breaking changes, never copy full changelog text
3. **Filter aggressively.** Skip anything low-impact, marketing fluff, or repetitive. Only include items with real engineering signal. If a category has nothing notable in the window, say so explicitly (don't pad).
4. **Always cite sources** per citation rules — prefer official sources (vendor blog, GitHub releases, changelog, NVD) over aggregators.

## Output modes

**Default (conversational report) — use this unless the trigger below matches.** Deliver the structured Markdown report inline in chat (not as a file), with concise bullet points — no long paragraphs:

```
## 🔥 DevOps News – Last <window>

### 1. Key Highlights (TL;DR)
- ...

### 2. 🚀 New Tools / Tech
- [Tool name]
  - What it is:
  - Why it matters:

### 3. ⚙️ Important Updates
- [Tool name / version]
  - Key changes:
  - Impact:

### 4. 🔐 Security Alerts
- [CVE-ID]
  - Severity:
  - Affected systems:
  - Impact:
  - Fix / mitigation:

### 5. 📰 Notable News
- [Headline]
  - Summary:
  - Why it matters:

### 6. 📄 Changelog Highlights
- [Project name]
  - Key changes:
  - Breaking changes (if any):
```

If there's nothing high-impact in the window, still produce the report and state plainly: "No significant high-impact DevOps updates in the last <window>."

**Astro blog / cover image mode — only load when triggered.** If the user explicitly asks for "markdown", "blog post", "Astro", a downloadable file, or a cover image, read `references/astro-output.md` for the exact frontmatter template and cover-image style prompt before producing output. Don't read that file for a normal conversational digest request — it's not needed and just adds noise.

## Rules (both modes)

- No fluff, no generic explanations — technical, actionable language only.
- Prioritize official sources: vendor blogs, GitHub releases/changelogs, NVD/security advisories.
- Always include links/sources.
- Skip low-impact or repetitive items entirely rather than including them with a caveat.
- For CVEs: always include CVE ID, severity (CVSS if available), affected systems/versions, impact, and concrete mitigation steps — not just "update to latest version" if a specific patched version is known.

## Language

If the user's stated preference or the conversation is in Vietnamese, write the digest content in Vietnamese but keep all tool names, CVE IDs, version numbers, and technical terms in English (do not translate them). This applies to both output modes.
