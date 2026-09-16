---
name: daily-report-formatter
description: Use this skill whenever the user pastes or dictates rough daily-report content (yesterday's work, today's plan, blockers, help needed) for a DevOps/engineering standup — often mixed Vietnamese/English, with ticket IDs like INFRA-2472 and tool names — and wants it turned into short, correct, plain-text English ready to paste into Slack. Trigger even on vague asks like "sửa giúp", "dịch sang tiếng Anh", "format lại", or just a messy pasted block, not only explicit "daily report" / "báo cáo hằng ngày" / "standup update" phrasing. Output must have zero Markdown syntax (no #, **, backticks), with each distinct task/topic in the paste separated by a "---" line.
---

# Daily Report Formatter

Turns rough, informal daily-report content (yesterday's work / today's plan /
blockers / help needed) into short, correct, plain-text English, safe to paste
into a Slack workflow that renders Markdown headers/bold incorrectly.

## Input

The user pastes only the **body content for one section** — not the section
header. The four section headers (✅ Hôm qua làm gì? / 📝 Hôm nay sẽ làm gì? /
🚫 Có đang gặp issue/blocker nào không? / 🙋 Có cần ai hỗ trợ không?) are added
automatically by the Slack app template — never generate or repeat them.

The content may contain several distinct, unrelated tasks/topics in one paste
(e.g. one ticket, then an unrelated investigation, then another item). It's
often mixed Vietnamese/English — the user drops into Vietnamese specifically
when they don't know the English word/phrase.

## Output rules

1. **Always output English**, regardless of input language. Translate any
   Vietnamese sentences/phrases to natural, correct English — don't leave
   Vietnamese in the output. Keep ticket IDs, tool/product names, hostnames,
   file paths, and commands exactly as-is (e.g. `Terraform`, `EC2`, `GitLab
   CI`, `Nginx`, `Playwright`, `INFRA-2472`, `proxy-qat.merito.dom`).
2. **Keep it short.** Tighten wording, drop filler, one clear sentence per
   point instead of a long one. Don't pad or over-explain.
3. **No Markdown syntax**: no `#`/`##`/`###`, no `**bold**`/`__underline__`,
   no backtick code spans. Plain text only.
4. **Bullets**: plain `- ` for sub-points, only when a task has 2+ points. If a
   task has only **one** point, merge it onto the same line as the task name
   (`Task name: the point.`) — no bullet, no second line.
5. **Split distinct tasks/topics with a line containing exactly `---`.** Each
   unrelated task/ticket/topic in the paste gets its own block, separated by
   `---` on its own line. Don't put `---` between bullets of the *same* task.
6. **Never add the section headers/emoji** — output starts directly with the
   first task's content.
7. **Grammar & phrasing pass**: fix grammar, tense, and awkward technical
   phrasing without changing meaning or dropping details. Don't invent facts,
   ticket numbers, or details not in the input.
8. **Separate code block per day.** If the input covers more than one day
   (Yesterday / Today), output each day as its own fenced code block, with a
   plain label line above it (`Yesterday:` / `Today:`) — so each block can be
   copied independently into the matching Slack field. If the input covers
   only one day, output a single code block, no label needed.

## Worked example

Given (mixed VN/EN, no header, two unrelated tasks in one paste):

```
INFRA-2472: migrate proxy qat
- fork nginx-forward-qat, merge sau khi confirm ok
laystar888.com
- tiếp tục theo dõi traffic pattern...vv
```

Produce:

```
INFRA-2472: Fork nginx-forward-qat; merge once confirmed working.
---
laystar888.com: Continue monitoring traffic patterns.
```

Notice: no header added, all English, `---` splits the two tasks, each task
has only one point so it's merged onto one line (no bullet), no
`#`/`**`/backticks.

If input mixes both days, e.g.:

```
hôm qua: INFRA-2472 fork nginx-forward-qat, merge sau khi confirm ok
hôm nay: laystar888.com tiếp tục theo dõi traffic pattern
```

Produce two separate blocks:

Yesterday:
```
INFRA-2472: Fork nginx-forward-qat; merge once confirmed working.
```

Today:
```
laystar888.com: Continue monitoring traffic patterns.
```

## Process

1. Split the pasted input into distinct tasks/topics (by blank lines, existing
   `---`, or an obvious topic change).
2. For each task: translate to English if needed, fix grammar, shorten,
   strip Markdown symbols, keep technical terms/IDs verbatim.
3. Join the tasks back together with a `---` line between each (not within).
4. Final scan for leftover `#`, `**`, `_`, or backticks — remove any found.
5. Output the plain-text block(s), ready to paste — no header. Use a
   separate fenced code block per day if the input covers more than one day.