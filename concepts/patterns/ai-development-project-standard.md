---
tags: [concept, pattern, ai, standard, policy, tracking, metrics]
aliases: [AI Development Project Standard, AI project tracking standard]
sources: [Confluence TECH/1612218379 (AI Development Project Standard), established 2025-05-28]
created: 2026-04-17
updated: 2026-04-17
---

# AI Development Project Standard

ALDC's documentation + tracking standard for projects developed primarily by AI assistants. Established 2025-05-28 by the Technology Team. First implementation: ALDC Slack Monitoring System. Applies to any project where **>50%** of development is done by AI, any standalone tool/system created by AI, and major features built through AI assistance.

## Mandatory project header

Every AI-developed project page in Confluence must include this block near the top:

```markdown
## AI Development Metrics
| Metric | Value |
|--------|-------|
| **Tokens Used** | ~X.XM tokens |
| **Development Time** | X hours |
| **Estimated Cost** | $XX.XX USD |
| **AI Model** | Claude Opus 4 |
| **Last Updated** | Month DD, YYYY |
```

### Metric definitions

- **Tokens Used** — approximate total tokens for the development conversation(s)
- **Development Time** — actual time spent in AI development sessions
- **Estimated Cost** — based on current token pricing (Claude Opus 4: $15/M input, $75/M output — verify current rates at write time)
- **AI Model** — specific model used
- **Last Updated** — date of last significant update

## What to track

### Development metrics
- Token usage (input / output broken out)
- Time spent in development
- Number of iterations / revisions

### Business metrics
- Expected time savings
- Cost reduction
- Revenue impact
- ROI calculations

### Technical metrics
- Lines of code generated
- Test coverage
- Performance benchmarks

## ROI template

```
Development Cost:     $[AI development cost]
Weekly Time Savings:  [hours] @ $[rate]/hour = $[weekly savings]
Monthly ROI:          $[weekly savings × 4]
Payback Period:       [cost / daily savings] days
```

## Aggregate tracking (Confluence-side)

The standard also requires these rollups on Confluence pages in the CORP space:

- **Innovation page** — "AI Development Metrics (Aggregate)": total time, total cost, active project count, estimated monthly value
- **In Progress page** — "AI Development Projects Summary" table: project name, status, AI time, AI cost, estimated value
- **Action Items page** — track AI development tasks in the Technology section with clear AI indicators

## Tagging

All AI-developed projects should include:

- 🤖 emoji in status fields
- "AI Development" label
- Clear AI indication in project title or description

## Review schedule

Quarterly review. Updated based on actual project outcomes, AI pricing changes, new tracking requirements, team feedback.

## See Also

- Example implementation referenced in source: Slack Monitor Project (CORP space)
- [[cce]] / [[factoria]] / [[opentribe]] — AI-adjacent internal projects that would fall under this standard
