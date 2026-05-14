---
tags: [process, interview, hiring, ai-engineer]
aliases: [Erik Interview Guide]
sources: [entities/people/erik-johnston.md]
created: 2026-05-11
updated: 2026-05-11
---

# Erik Johnston — Interview Flow Guide

**Date:** 2026-05-11, 1:30 PM
**Candidate:** Erik Johnston — AI Engineer
**Interviewers:** Mike (may open), Paul

---

## 1. Company Introduction (2 min)

*Skip if Mike covers this at the start.*

- ALDC (Analytic Labs Data Corp) — data engineering and analytics company
- We build Eclipse, a connector platform that pulls data from 50+ sources into Snowflake, delivered through dashboards
- Small, high-leverage team — everyone owns significant surface area
- Heavy AI-native workflow — Claude Code, multi-agent systems, automated PR review pipeline
- Active clients: GEP (e-commerce analytics), Fusion92 (media activation)
- Building next-gen platform (Eclipse EXP): FastAPI + Next.js 15 + PostgreSQL, multi-tenant, AI-native

---

## 2. Your Introduction (2 min)

- Your background, how you got to ALDC
- Your role: Data & Agentic AI Engineer — pipelines, Snowflake, AI agent systems, platform architecture
- What your day looks like: shipping data features end-to-end, building AI tooling (CCE — 195 skills, 20 hooks), R&D on autonomous data engineering (Factoria)
- Why this hire matters: need someone to own frontend/platform delivery so you can focus on data engineering and deep AI work

---

## 3. Erik's Background (5 min)

Let him talk. Listen for:
- How he describes his progression from Saturn (4 years) to Xambi (1 year)
- Whether he frames himself as a builder or a maintainer
- How he talks about leading the 2-person team at Saturn

**Prompt:** "Walk me through your career — what you've built, what you're most proud of, and what brought you to this point."

---

## 4. Deep-Dive: Relevant Experience (10-12 min)

### Saturn Animation Studios — SaaS Applications

Erik built 3 enterprise SaaS apps (Next.js/React + Node.js/Express) at 5000 MAU. This maps directly to Eclipse EXP.

- "Pick the most complex of the three SaaS apps at Saturn. What was the architecture — frontend, backend, database, auth, hosting?"
- "How did you handle multi-tenancy or user isolation? Did each client get their own data, or was it shared?"
- "What was your CI/CD setup? Walk me through a change going from your editor to production."
- "You improved deployment efficiency by 40% — what was broken before, and what did you build to fix it?"

### Saturn — Claude 3.5 Integration (AI-Powered Inspection Reporting)

This is the strongest signal for AI depth. Dig in.

- "The Claude 3.5 inspection reporting system — was that API calls, SDK, or something else?"
- "Did you handle streaming responses? How did you manage prompt engineering iteration?"
- "What happened when Claude gave a bad output? Did you have validation, retry logic, or human-in-the-loop?"
- "How did you handle token costs at scale — any caching, batching, or prompt optimization?"

### Xambi Tech — Plutaro & AI Workflow Framework

He helped build a vibecoding platform and a standardized AI workflow framework. Probe for depth vs. surface.

- "What was the architecture of Plutaro? How did it orchestrate AI code generation across client projects?"
- "You delivered 20+ projects using AI-assisted workflows — what guardrails did you have to prevent AI-generated security issues or broken builds?"
- "What was the standardized AI workflow framework? Was it prompt templates, agent orchestration, code review automation — what specifically?"
- "When AI-generated code was wrong, how did you catch it? What was your quality gate?"

---

## 5. ALDC Tool Stack Alignment (5 min)

Probe familiarity with tools we use daily. Not expecting mastery — looking for transferable knowledge.

| Tool | Question |
|---|---|
| **Docker** | "How have you used Docker? Dev environments only, or production deployment too? Built multi-stage Dockerfiles?" |
| **Azure** | "Your resume lists AWS and GCP. Any Azure experience at all? Container Apps, App Service, Functions?" |
| **NoSQL/CosmosDB** | "You list NoSQL — which databases specifically? How did you model data without a relational schema?" |
| **PostgreSQL** | "Any Postgres experience? We use it with row-level security for multi-tenant isolation." |
| **Git/GitHub** | "What does your branching strategy look like? Have you worked with automated PR review pipelines?" |

---

## 6. LLM & AI Workflow (5-7 min)

This is critical — we're an AI-native team.

- "What LLMs do you use day-to-day? Claude, GPT, Gemini, local models?"
- "Walk me through your typical workflow with AI tooling. When you sit down to build a feature, how does AI fit into your process?"
- "Have you used Claude Code specifically? If so, how — just chat, or do you use it for code generation, debugging, architecture?"
- "Do you use any AI coding tools in your IDE — Copilot, Cursor, Continue, Cline?"
- **"What's your philosophy on AI-generated code? Do you trust it, review it line-by-line, or something in between?"**
- "Have you built any systems that use LLMs as a component — not just for coding help, but embedded in the product?"

---

## 7. Personal Projects & Curiosity (3-5 min)

- "What do you build when nobody's paying you? Anything on your GitHub (ejohn17) or erik-dev.ca?"
- "Have you experimented with multi-agent systems, RAG pipelines, or knowledge management with LLMs?"
- "What's the most technically interesting thing you've explored recently that isn't on your resume?"

---

## 8. Scenario Question (5 min)

Pick ONE based on how the conversation has gone:

**If he's strong on frontend/SaaS:**
> "Our next-gen platform bundles FastAPI + Next.js 15 into a single Docker image. The frontend uses Mantine 8 and React Query 5, behind a reverse proxy at `/internal/*`. A client wants a connector health dashboard — data comes from `GET /api/v1/connectors/health`. How would you approach building this? What complications might arise from the `basePath=/internal` config?"

**If he's strong on AI integration:**
> "We run 4 automated checks on every PR: Semgrep security scan, TruffleHog secret detection, Claude Opus code review, and architecture tests. Claude flags a concern about error handling you removed. You believe it was redundant. How do you handle this?"

**If he's strong on CI/CD:**
> "We deploy via GitHub Actions to Azure staging slots, then manual swap to production. A deploy goes out and a client reports their data shows in the old portal but not the new platform (we're mid-migration using a strangler-fig pattern). Walk me through your debugging approach."

---

## 9. His Questions for Us (3-5 min)

Give him space. His questions tell you a lot about what he cares about.

---

## 10. Close (1-2 min)

- Timeline for next steps
- Thank him for his time

---

## What You're Evaluating

| Signal | Strong | Weak |
|---|---|---|
| **Builder mentality** | Describes architecture decisions, tradeoffs, things he'd do differently | Lists technologies without explaining why or how |
| **AI depth** | Built systems with LLMs as components, understands prompt engineering, cost management, failure modes | "I use ChatGPT/Claude to help me code" and nothing deeper |
| **Quality instincts** | Talks about testing, CI, code review, security unprompted | Ships and hopes for the best |
| **Ownership** | "I built", "I decided", "I debugged" | "We" for everything, can't isolate his contribution |
| **Curiosity** | Side projects, experiments, reads papers/blogs, opinions about tools | Stops learning when the workday ends |
| **Communication** | Clear, structured answers; asks clarifying questions | Rambles, can't summarize, doesn't ask questions |

---

## See Also

- [[erik-johnston]] — full candidate profile, skill gap analysis, fit scoring
- [[employee-onboarding]] — onboarding checklist if hired
- [[environment-setup]] — technical machine setup if hired
