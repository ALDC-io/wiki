---
tags: [entity, person, candidate, interview, hiring, ai-engineer]
aliases: [Erik Johnston]
sources: [resume, interview-analysis-2026-05-08]
created: 2026-05-08
updated: 2026-05-08
---

# Erik Johnston — AI Engineer Candidate

Interview candidate for AI Engineer role at ALDC. Analysed 2026-05-08 against the full wiki (tech stack, repos, projects, team structure). Resume sourced directly from candidate.

**Contact**: johnstonerik17@gmail.com | erik-dev.ca | GitHub: ejohn17
**Location**: Kelowna, British Columbia
**Education**: UBC — B.Sc. Computer Science (2022)

---

## Technical Skills

| Category | Skills |
|---|---|
| Languages | TypeScript, JavaScript |
| Frontend | Next.js, React, Redux, SCSS, CSS3, HTML |
| Backend | Node.js, Express, NoSQL, MySQL |
| Tools | AWS, Google Cloud, Docker, LLMs, DevOps, Git, Agile |

---

## Work Experience

### Xambi Tech (Feb 2025 – Feb 2026) — Software Developer (Remote)
- Built and delivered 20+ websites/software projects using AI-assisted development workflows
- Helped design a standardized AI workflow framework automating project setup and accelerating delivery
- Assisted building **Plutaro**, a vibecoding platform operationalizing rapid AI-driven builds

### Saturn Animation Studios (May 2020 – Aug 2024) — Lead Developer (Kelowna)
- Architected and delivered 3 enterprise SaaS applications (Next.js/React + Node.js/Express), 5000 MAU
- Led a 2-person dev team, managed workflows, collaborated directly with product owner
- Designed CI/CD pipelines and automated testing — 40% deployment efficiency improvement
- Built AI-powered solutions with **Claude 3.5** including automated site inspection reporting (80% efficiency gain)

### UBC (Jan – Apr 2020) — Teaching Assistant
- Instructed 30+ undergrad students in Java OOP, data structures, algorithms

---

## Where His Skills Positively Impact ALDC

### Direct Matches (High Impact)

**1. Next.js / React Frontend — 4 active repos**
- [[eclipse_exp]] frontend (Next.js 15 + Mantine 8 + React Query 5)
- [[prospect-site-template]] (Next.js 15 + Tailwind, 15 deployed microsites)
- [[entities/repos/flight-check|flight-check]] (Next.js 16, DAX Media App)
- [[entities/repos/eclipse|Legacy Eclipse UI]] (Next.js 14, active during strangler-fig migration)

**2. AI-Assisted Development Workflows**
- [[cce]] — 195-skill, 20-hook AI development system
- [[ai-driven-dev-workflow]] — structured methodology (v3.1 tactical agentic framework)
- [[phaselab]] — AI-powered prototype exploration
- [[ai-pr-workflow]] — Semgrep + TruffleHog + Claude Opus review pipeline

**3. Claude / LLM Integration**
- eclipse_exp: AI onboarding chat + tenant-aware AI chat (SSE streaming)
- prospect-site-template: Claude-generated configs + SSE chat proxy
- [[factoria]]: 7 specialist AI agents
- [[zeus-memory]]: LLM-assisted drift detection and doc rewriting

### Good Matches (Medium Impact)

**4. Enterprise SaaS Architecture** — 3 SaaS apps at 5000 MAU maps to eclipse_exp (multi-tenant, RLS, RBAC, 50 connectors) and Zeus Memory

**5. CI/CD & DevOps** — 40% deployment efficiency improvement at Saturn. ALDC needs: GitHub Actions, Docker, Azure Container Apps deployment

**6. NoSQL** — [[CosmosDB]] is critical to Eclipse runtime (connection/template configs)

---

## Complementary Hire Assessment

Paul currently handles all data engineering and AI engineering. The value of this hire is **freeing Paul from frontend/platform work** to focus on data pipelines, Snowflake, Power BI, Prefect, and deep AI agent orchestration.

| Area Erik Covers | Paul Freed Up For |
|---|---|
| eclipse_exp frontend (Next.js 15, Mantine, React Query) | Data pipeline + AI agent work |
| prospect-site-template (15 microsites) | Zeus Memory, Factoria R&D |
| flight-check / DAX Media App frontend | Fusion92 data pipeline maintenance |
| Legacy Eclipse UI (strangler-fig frontend) | Snowflake/PBI delivery for GEP |
| CI/CD pipeline improvements | Architecture + orchestration |
| PhaseLab UI / demo layer | Phase Forge execution layer |
| AI workflow tooling (CCE skills) | Deep agent orchestration (Factoria, OpenClaw) |
| SaaS feature delivery (eclipse_exp) | FastAPI/Python backend + data contracts |

---

## Skill Gaps

| Gap | Severity | Mitigation |
|---|---|---|
| **Python** | Critical (standalone) / Manageable (complementary) | Doesn't need to own it if Paul covers FastAPI/Prefect/connectors. Needs to read it for eclipse_exp backend. |
| **SQL / Data Engineering** | Critical (standalone) / Low (complementary) | No SQL, Snowflake, star schema, ETL/ELT. Needs SQL basics for eclipse_exp data views. |
| **Azure** | Medium | Lists AWS/GCP, not Azure. Transferable but 2–4 week ramp on Container Apps, CosmosDB, slot swaps. |
| **PostgreSQL + RLS** | Medium | MySQL + NoSQL listed. asyncpg, pgvector, RLS patterns would be new. |
| **Power BI** | Low (complementary) | Not mentioned. Paul handles PBI delivery; Erik wouldn't need this. |
| **Snowflake** | Low (complementary) | Core ALDC infrastructure but Paul owns this layer. |
| **Prefect / Orchestration** | Low (complementary) | Not mentioned. Active migration target but Paul owns it. |

---

## Interview Questions

### Scenario-Based (ALDC Use-Cases)

**Q1 — Prospect Site Generation Pipeline**
> "We have a Next.js 15 template that generates marketing microsites from a single TypeScript config file. Claude Code reads a natural-language prompt, generates the config, and the site builds. Currently we have 15 deployed sites on Vercel. A sales rep just closed a new client — a healthcare analytics company. Walk us through how you'd approach generating a new prospect site, what you'd validate before deploying, and how you'd handle a situation where the generated config breaks the Tailwind build because it reads `site.config.ts` at compile time."

**Q2 — Eclipse EXP Frontend Feature**
> "Our next-gen platform bundles a FastAPI backend and a Next.js 15 frontend into a single Docker image via supervisord. The frontend uses Mantine 8 and React Query 5, and sits behind a reverse proxy at `/internal/*`. A client wants a new dashboard view showing connector health status — data comes from `GET /api/v1/connectors/health`. How would you approach building this feature? What complications might arise from the `basePath=/internal` Next.js config?"

**Q3 — AI-Augmented PR Workflow**
> "Every PR triggers four automated checks: Semgrep security scan, TruffleHog secret detection, Claude Opus AI code review, and PyTestArch architecture checks. The bypass list is empty. You've pushed a PR and Claude Opus flagged a concern about removing error handling in a route module. You believe the error handling was redundant. How do you resolve this?"

**Q4 — Multi-Agent AI System Design**
> "We're building Factoria — an autonomous data engineering platform where 7 specialist AI agents turn Jira tickets into dbt model changes delivered as PRs. Agents never execute shell commands directly — only a dedicated Runner container holds credentials. If you were asked to add a 'Documentation Agent' that generates data dictionary pages from dbt model metadata — how would you design its tool allowlist, what artifacts would it produce, and how would it fit into the existing workflow state machine?"

**Q5 — Strangler-Fig Migration**
> "We're migrating from a legacy portal (Next.js 14, CosmosDB, NextAuth) to our next-gen platform (Next.js 15, PostgreSQL with RLS, JWT). We use a strangler-fig pattern with dual-write capability. A tenant reports their data appears in the legacy portal but not the new platform. Walk us through your debugging approach."

**Q6 — AI Workflow Optimization**
> "We've measured ~33% first-attempt success rate for autonomous Claude Code, and 2.74x security vulnerability rate in AI-co-authored code. Our response: plan-before-implement discipline (80% fewer false starts), orchestrator-worker patterns (90% improvement), context isolation per agent phase. Given your experience building AI workflow frameworks at Xambi, what patterns did you discover for improving AI reliability?"

### Experience-Focused

**Q7 — Team Leadership & Scale**
> "At Saturn you led a 2-person dev team delivering 3 SaaS apps to 5000 MAU. ALDC is a similar-sized team but with 12+ repos, two active clients, and several AI R&D projects. How did you prioritize across multiple products? How would you handle context-switching between a production data pipeline bug and an R&D sprint?"

**Q8 — AI Integration Depth**
> "You built an AI-powered inspection reporting system with Claude 3.5 that improved efficiency by 80%. Was it API-based or SDK-based? Did you handle streaming responses? How did you manage prompt engineering, token costs, and error handling? Did you implement any feedback loops?"

**Q9 — CI/CD Pipeline Design**
> "Walk us through the most sophisticated pipeline you've built. How did you handle environment promotion? Automated rollback? Database migrations in your deployment pipeline?"

**Q10 — Plutaro / AI Quality Guardrails**
> "At Xambi you built Plutaro, a vibecoding platform. What was the architecture? How did you handle quality assurance when AI was generating code across 20+ client projects? What guardrails prevented AI-generated security vulnerabilities?"

### Personal Projects & Curiosity

**Q11 — Portfolio & Side Projects**
> "Your resume lists enterprise work but no open-source or side projects. What do you build when no one's paying you? Anything on your GitHub (ejohn17) or erik-dev.ca that demonstrates your approach to AI tooling?"

**Q12 — Multi-Agent / RAG Experimentation**
> "Outside of work, have you experimented with multi-agent systems, RAG pipelines, or LLM tools that persist knowledge across sessions? Our Zeus Memory product does exactly that."

**Q13 — Technical Curiosity**
> "What's the most technically interesting thing you've built or explored recently that isn't on your resume?"

---

## Fit Scoring

### As Complementary Hire (Paul owns data engineering + AI backend)

| Category | Score | Weight | Weighted |
|---|:---:|:---:|:---:|
| Frontend & UI (Next.js/React/TS) | 9/10 | 30% | 2.70 |
| AI/LLM Capability | 6.5/10 | 20% | 1.30 |
| SaaS Feature Delivery | 7.5/10 | 20% | 1.50 |
| DevOps & CI/CD | 7/10 | 15% | 1.05 |
| Backend (Node.js portions) | 6/10 | 10% | 0.60 |
| Cultural / Team Fit | 8/10 | 5% | 0.40 |
| **Overall** | | | **7.55/10** |

### As Standalone AI Engineer (would need to cover full stack)

| Category | Score | Weight | Weighted |
|---|:---:|:---:|:---:|
| Frontend & UI | 9/10 | 20% | 1.80 |
| AI/LLM Capability | 6.5/10 | 25% | 1.63 |
| Backend (Python/FastAPI) | 2/10 | 20% | 0.40 |
| Data Stack (SQL/Snowflake/PBI) | 1/10 | 20% | 0.20 |
| DevOps & Cloud | 5/10 | 15% | 0.75 |
| **Overall** | | | **4.78/10** |

### Priority Interview Questions

1. **Q2** (eclipse_exp frontend) — tests delivery in the actual stack
2. **Q8** (AI integration depth) — separates "used Claude" from "built systems with Claude"
3. **Q10** (Plutaro quality guardrails) — tests AI workflow experience depth
4. **Q3** (AI PR workflow) — tests ability to work within ALDC's strict review pipeline
5. **Q12** (personal AI experimentation) — curiosity signal for an R&D team

---

## See Also

- [[eclipse_exp]] — primary platform where Erik would contribute frontend features
- [[prospect-site-template]] — Next.js 15 prospect site factory (direct skill match)
- [[cce]] — AI development system (workflow match)
- [[ai-pr-workflow]] — PR pipeline Erik would work within
- [[factoria]] — multi-agent system (stretch goal for Erik)
- [[employee-onboarding]] — onboarding checklist if hired
- [[environment-setup]] — technical setup if hired
