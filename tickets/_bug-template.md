---
tags: [ticket, <CLIENT>, bug]
aliases: [<TICKET-ID>]
sources: []
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
---

# <TICKET-ID> — <Title>

**Type:** Bug | **Status:** Triaged | **Priority:** <priority>

## Problem

<1-3 sentences: what's broken, who's affected, how it manifests.>

- **Reported by:** <name>
- **Environment:** <prod/test/qa>
- **Reproducible:** <always / intermittent / unknown>
- **Blocking:** <what's blocked, or "not blocking">

## Symptoms

<Observable behavior. Error messages, screenshots, logs. Be exact.>

## Initial Analysis

### What we know

<Facts established so far. Rule-outs, confirmed behavior.>

### Likely causes (ranked)

1. **<Most likely>** — <why>
2. **<Next likely>** — <why>
3. **<Fallback>** — <why>

### Key code locations

| What | Where |
|------|-------|
| <component> | `<repo>/<path>` |

## Boot Prompt

````
You are investigating <TICKET-ID> (<short description>).

Boot procedure:
1. Read this ticket: `C:\Users\PaulRussell\repos\wiki\tickets\<client>\<TICKET-ID>.md`
2. Read <relevant wiki pages — architecture, connector spec, deployment guide>
3. Read <relevant source files listed in Key code locations>

Problem: <one-line restatement>

Investigation steps:
1. <First thing to check — the highest-likelihood cause>
2. <Second thing to check>
3. <Reproduce locally or inspect logs>
4. Propose fix with evidence

Scope: diagnose and fix this bug. Do NOT refactor surrounding code.
````

## Investigation Log

<Append findings as you go. Timestamped.>

## Fix

<After diagnosis: what changed, why, and how to verify.>

## See Also

- <Related wiki pages, prior incidents, similar bugs>
