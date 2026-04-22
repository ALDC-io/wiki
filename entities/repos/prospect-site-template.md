---
tags: [entity, repo, prospect-site-template, nextjs, marketing, template, ai-generated]
aliases: [prospect-site-template, AnalyticLabs prospect microsites, Cultivate template, analyticlabs.io microsites]
sources:
  - repos/prospect-site-template/README.md
  - repos/prospect-site-template/CLAUDE.md
  - repos/prospect-site-template/CONTRIBUTING.md
  - repos/prospect-site-template/package.json
  - repos/prospect-site-template/next.config.ts
  - repos/prospect-site-template/tsconfig.json
  - repos/prospect-site-template/tailwind.config.ts
  - repos/prospect-site-template/vitest.config.ts
  - repos/prospect-site-template/eslint.config.mjs
  - repos/prospect-site-template/create-site.sh
  - repos/prospect-site-template/.env.example
  - repos/prospect-site-template/site.config.example.ts
  - repos/prospect-site-template/src/lib/types.ts
  - repos/prospect-site-template/src/lib/config.ts
  - repos/prospect-site-template/src/app/layout.tsx
  - repos/prospect-site-template/src/app/page.tsx
  - repos/prospect-site-template/src/app/error.tsx
  - repos/prospect-site-template/src/app/globals.css
  - repos/prospect-site-template/src/app/api/chat/route.ts
  - repos/prospect-site-template/src/app/calculator/page.tsx
  - repos/prospect-site-template/src/app/chat/page.tsx
  - repos/prospect-site-template/src/app/why-aldc/page.tsx
  - repos/prospect-site-template/src/components/nav.tsx
  - repos/prospect-site-template/src/components/hero-section.tsx
  - repos/prospect-site-template/src/components/ecosystem-diagram.tsx
  - repos/prospect-site-template/src/components/decision-tree.tsx
  - repos/prospect-site-template/src/components/zeus-chat.tsx
  - repos/prospect-site-template/src/components/dashboard/dashboard-page.tsx
  - repos/prospect-site-template/src/components/dashboard/sidebar.tsx
  - repos/prospect-site-template/src/components/dashboard/kpi-card.tsx
  - repos/prospect-site-template/src/components/pitch/pitch-page.tsx
  - repos/prospect-site-template/src/__tests__/setup.ts
  - repos/prospect-site-template/src/__tests__/live-config.test.ts
  - repos/prospect-site-template/src/__tests__/site-variants.test.ts
  - repos/prospect-site-template/src/__tests__/claude-md-claims.test.ts
  - repos/prospect-site-template/src/__tests__/fixtures/configs.ts
  - repos/prospect-site-template/src/__tests__/fixtures/dashboard-configs.ts
  - repos/prospect-site-template/.github/workflows/ci.yml
  - repos/prospect-site-template/docs/source-analysis.md
created: 2026-04-20
updated: 2026-04-20
---

# prospect-site-template (repo)

**Disambiguation — three other Next.js repos share the ALDC portfolio:** this repo is not [[entities/repos/eclipse|eclipse (repo)]] (the legacy Pages Router portal), not [[eclipse_exp]] (the FastAPI + Next.js 15 platform), and not [[entities/repos/flight-check|flight-check (repo)]] (the DAX Media App frontend). It is also not [[zeus-memory]] — Zeus is an optional integration here, not the product. This repo is the **prospect-site factory**: a single, shared Next.js 15 codebase whose entire content is configuration-driven, producing many independent marketing microsites at `<subdomain>.analyticlabs.io`.

**Future home:** [[eclipse_exp]] is absorbing prospect-site generation as part of the broader ALDC platform consolidation (alongside the legacy [[entities/repos/eclipse|eclipse]] UI, the [[connector]] runtime, and parts of [[core_api]]). The forward-looking webhook in eclipse_exp (`POST /api/v1/onboarding/webhooks/prospect-created` → `build.prospect.aldc.io`) is the planned integration path that will let provisioning a new prospect happen as a single eclipse_exp onboarding action. Until that cutover, **this repo is the canonical way to create prospect sites** and is actively maintained.

The repo holds a single Next.js 15 application whose entire content — theme, copy, sections, calculator tree, chat system prompt — is driven by one gitignored `site.config.ts` file. [[claude_code_enhanced|Claude Code]] generates that config from a natural-language prompt; the resulting folder is copied out and deployed as its own site. The design is deliberate: one immutable codebase, one config file per site, zero CMS, zero database. Config changes are validated at compile time by the TypeScript compiler and at test time by 624 Vitest tests (622 passing, 2 skipped as of 2026-04-20).

Three templates are available, selected by the `template` field in the config:
- **`landing`** — dark theme, 8 scrolling sections, animated hero, ecosystem SVG, decision-tree calculator, optional Zeus Chat. Used by 11 of the 15 known sites (the "Cultivate family" plus `producer`).
- **`dashboard`** — light theme, sidebar, KPI tiles, Zeus Chat FAB. Used by 2 sites: Ghost Pine and AgriStack.
- **`pitch`** — dark, compounding-bars hero, lead capture form, AI comparison table. Used by 1 site: WhyALDC.

The repo is the template/factory. Each of the 15 known deployed sites at `*.analyticlabs.io` is an independent copy of this folder with its own `site.config.ts` and its own Vercel deployment.

---

## Architecture

### Repository layout

```
prospect-site-template/
├── README.md                        # User-facing intro: quick start, templates, routes, CI
├── CLAUDE.md                        # AI-agent instructions (what Claude does when asked to "make a site")
├── CONTRIBUTING.md                  # Commit-time checks (lint, prettier, typecheck, tests)
├── package.json                     # Next 15.3, React 19.1, Tailwind 3, posthog-js, vitest
├── next.config.ts                   # Minimal: just reactStrictMode: true
├── tsconfig.json                    # Strict; @/* → ./src/*
├── tailwind.config.ts               # IMPORTS site.config at build time — accent/glow are per-site
├── postcss.config.mjs               # tailwind + autoprefixer
├── vitest.config.ts                 # jsdom, @vitejs/plugin-react, @/* alias
├── eslint.config.mjs                # next/core-web-vitals + next/typescript (flat config)
├── .prettierrc                      # 2-space, double-quote, trailing commas es5, printWidth 100
├── .editorconfig                    # utf-8 LF 2-space, insert_final_newline
├── .env.example                     # PostHog key + Anthropic key + Zeus (5 vars)
├── .gitignore                       # includes site.config.ts — gitignored on purpose
├── create-site.sh                   # Bash pipeline: copy template → apply config → install → test → build
├── site.config.example.ts           # Committed example (Cultivate food waste landing site)
├── .github/workflows/ci.yml         # Lint + prettier + typecheck + vitest + next build
├── docs/
│   ├── source-analysis.md           # 1000+-line reverse-engineering of 15 deployed sites
│   └── screenshots/                 # landing-hero.png, calculator.png
├── public/assets/
│   ├── aldc_logo.svg
│   └── favicon.svg
└── src/
    ├── lib/
    │   ├── types.ts                 # THE schema. All config types. Source of truth for generation.
    │   └── config.ts                # getConfig() re-export of ../../site.config
    ├── app/
    │   ├── layout.tsx               # Root layout; PostHog snippet; theme-light class for dashboard
    │   ├── page.tsx                 # Template switch: landing|dashboard|pitch
    │   ├── globals.css              # Dark default + .theme-light override
    │   ├── error.tsx                # Global error boundary ("Check your site.config.ts")
    │   ├── calculator/page.tsx      # /calculator (decision tree)
    │   ├── chat/page.tsx            # /chat (Zeus Chat page)
    │   ├── why-aldc/page.tsx        # /why-aldc (stub "Coming soon")
    │   └── api/chat/route.ts        # POST /api/chat — SSE proxy to Anthropic + optional Zeus log
    ├── components/
    │   ├── nav.tsx                  # Fixed top nav with scrollspy (IntersectionObserver)
    │   ├── footer.tsx
    │   ├── sweep-divider.tsx        # 3s gradient sweep separator
    │   ├── hero-section.tsx         # Landing hero: animated words, stat cards, CTA buttons
    │   ├── problem-section.tsx      # Landing section 1
    │   ├── ecosystem-diagram.tsx    # Landing section 2 — interactive SVG graph
    │   ├── stakeholder-grid.tsx     # Landing section 3
    │   ├── platform-timeline.tsx    # Landing section 4 — exactly 4 phases
    │   ├── global-comparison.tsx    # Landing section 5
    │   ├── alignment-section.tsx    # Landing section 6
    │   ├── funding-strategy.tsx     # Landing section 7
    │   ├── join-cta.tsx             # Landing section 8
    │   ├── decision-tree.tsx        # Calculator engine (tiered outcomes, principles sidebar)
    │   ├── zeus-chat.tsx            # Chat UI — inline MD + SVG streaming renderer
    │   ├── dashboard/
    │   │   ├── dashboard-page.tsx   # Top-level dashboard layout
    │   │   ├── sidebar.tsx          # Dashboard sidebar nav
    │   │   └── kpi-card.tsx         # KPI tile (value, change, trend)
    │   └── pitch/
    │       └── pitch-page.tsx       # Pitch template page
    └── __tests__/                   # 11 test files, Vitest + @testing-library/react
        ├── setup.ts                 # Polyfills scrollIntoView + IntersectionObserver in jsdom
        ├── live-config.test.ts      # Validates the actual site.config.ts being built
        ├── config-validation.test.ts
        ├── config-negative.test.ts
        ├── site-variants.test.ts    # 15 site fixtures — 11 cultivate + 2 dashboard + 1 pitch + 1 producer
        ├── dashboard-variants.test.ts
        ├── component-render.test.tsx
        ├── decision-tree.test.ts    # No cycles, all outcomes reachable, tier integrity
        ├── sections.test.ts
        ├── theme.test.ts
        ├── theme-css.test.ts
        ├── claude-md-claims.test.ts # Asserts every CLAUDE.md rule is enforced by the fixture set
        └── fixtures/
            ├── configs.ts           # 883 lines: themes, heroes, siteMetadata, calculators, allSiteNames
            └── dashboard-configs.ts # ghostpineDashboard, agristackDashboard, whyaldcPitch
```

### Tech stack

| Layer | Choice | Notes |
|---|---|---|
| Framework | Next.js 15.3 (App Router, Turbopack dev) | `package.json:15`; `npm run dev` uses `next dev --turbopack` |
| React | 19.1.0 | `package.json:17-18` |
| Language | TypeScript 5.8 (strict) | `tsconfig.json:7`; no `as any` linting rule; `@/*` alias |
| Styling | Tailwind CSS 3.4.17 + `globals.css` custom properties | `.theme-light` class swaps dashboard to light theme |
| Analytics | PostHog (inline browser snippet) | `layout.tsx:35-46`; gated on `NEXT_PUBLIC_POSTHOG_KEY`; host `https://us.i.posthog.com` |
| AI chat | Anthropic Messages API (SSE stream proxied) | `src/app/api/chat/route.ts`; server-side `ANTHROPIC_API_KEY`; default model `claude-sonnet-4-6` |
| AI memory | Zeus Memory (optional) | POST `${ZEUS_API_URL}/api/memory` after each chat; failures non-fatal. See [[zeus-memory]]. |
| Testing | Vitest 3.2 + @testing-library/react 16 + jsdom 27 | `setup.ts` polyfills `scrollIntoView` and `IntersectionObserver` |
| Lint / format | ESLint 9 (flat config) + Prettier 3 | `eslint.config.mjs`; `.prettierrc` |
| CI | GitHub Actions — `.github/workflows/ci.yml` | Node 22; lint + prettier + tsc + vitest + build on every PR to `main` |
| Deploy target | Vercel (extant sites) | Confirmed via `dpl_*` deployment IDs in `docs/source-analysis.md:342-348`. Repo itself is framework-portable. |

### The three-template selection model

This is the single most important architectural fact in the codebase.

`src/lib/types.ts:268` defines `template: "landing" | "dashboard" | "pitch"` as a literal union on the top-level `SiteConfig`. `src/app/page.tsx:70-86` switches on that field and returns one of three component trees:

- **`landing`** → `<Nav />` + `<HeroSection />` + mapped sections array + `<Footer />`. Dark theme always.
- **`dashboard`** → `<Sidebar />` + KPI grid + active section panel + optional Zeus FAB. Light theme only.
- **`pitch`** → `<Nav />` + `<PitchPage />` + `<Footer />`. Dark theme always.

`src/app/layout.tsx:32` applies `className="theme-light"` to the body iff `config.template === "dashboard"`. All other templates inherit the dark default from `globals.css:10-24`. The light-vs-dark switch is a CSS class toggle, not a theme system.

Every component reads `getConfig()` at module load time — a sync import of `../../site.config`. At build time the single config file determines the entire site. There is no runtime config fetch.

Each template requires different config fields (see `CLAUDE.md:57-73` and `src/lib/types.ts:270-299`):

| Template | Required | Optional |
|---|---|---|
| `landing` | `hero`, `sections[]`, `ecosystemDiagram` | `calculator`, `chat` |
| `dashboard` | `dashboard.sidebarLinks`, `dashboard.kpis`, `dashboard.sections` | `chat`, `dashboard.logoPath` |
| `pitch` | `pitch.compoundingBars` (3), `pitch.aiComparison`, `pitch.leadForm`, `pitch.valueProps` (3) | `chat` |

### Config as single source of truth — Tailwind reads site.config at build time

`tailwind.config.ts:2-4` imports `./site.config` and pulls `accentColor` and `glowColor` into the Tailwind theme. This means **the build graph includes `site.config.ts`** — if the config is missing or malformed, the Tailwind build fails before Next.js even compiles.

Consequence: `site.config.ts` must exist before `next build`. The `postinstall` script in `package.json:11` (`test -f site.config.ts || cp site.config.example.ts site.config.ts`) guarantees this on fresh clones.

`globals.css:10-24` declares `--color-background` / `--color-foreground` custom properties for Tailwind's `bg-background`, `text-foreground`, `border-foreground/10` utilities. Accent and glow resolve at build time through the Tailwind config; background/foreground toggle via the `.theme-light` CSS class at runtime.

### Routes

| Route | File | Template behaviour | Notes |
|---|---|---|---|
| `/` | `app/page.tsx` | landing → full 8-section scroller; dashboard → sidebar + KPI grid; pitch → compounding bars + lead form | Template switch on `config.template` |
| `/calculator` | `app/calculator/page.tsx` | Renders `<DecisionTree/>` if `config.calculator` is set, else "No calculator configured" | Landing-typical; also works under dashboard chrome |
| `/chat` | `app/chat/page.tsx` | Renders `<ZeusChat/>` if `config.chat` is set | Nav or Sidebar chrome depending on template |
| `/why-aldc` | `app/why-aldc/page.tsx` | Always renders "Coming soon" stub | Historical placeholder; see Tech Debt |
| `/api/chat` | `app/api/chat/route.ts` | POST — SSE stream proxy to Anthropic; optional Zeus log | Server route only |

### Key abstractions

**`SiteConfig`** (`src/lib/types.ts:267-299`) — the contract. 35+ fields with full TypeScript interfaces. Top-level: `template`, `subdomain`, `siteName`, `siteLabel`, `theme` (ThemeConfig), SEO fields, `nav`, `hero`, `sections[]`, `ecosystemDiagram`, optional `calculator`, `chat`, `dashboard`, `pitch`. Sub-types: `ThemeConfig`, `NavLink`, `NavBadge`, `HeroConfig`, 8 section-type interfaces in a discriminated union (`ProblemSection | VisionSection | StakeholderSection | PlatformSection | GlobalSection | AlignmentSection | FundingSection | JoinSection`), `EcosystemNode` + `EcosystemEdge`, `DecisionNode` + `Outcome` + `Principle` + `CalculatorConfig`, `ChatPrompt` + `ChatConfig`, `KpiCard` + `DashboardSection` + `DashboardConfig`, `PitchConfig`.

**`getConfig()`** (`src/lib/config.ts`) — trivial re-export of `../../site.config`. Every component imports this module. Server and client components share it because `site.config.ts` has no runtime side-effects.

**Decision tree engine** (`src/components/decision-tree.tsx`) — binary (yes/no) DAG. Node IDs beginning `"outcome-"` are terminals; `"start"` is the root. Each outcome has `tier: 1-6`, `color`, `icon`, `valueRecovery` percent, `costImpact`, action list, and a `principle` reference. Validation tests in `decision-tree.test.ts` assert no cycles and all outcomes reachable.

**`ZeusChat`** (`src/components/zeus-chat.tsx`) — client component. Streams SSE from `/api/chat`, renders inline markdown (tables, code, headings, lists, links) and inline `<svg>` blocks with streaming-safe placeholders (lines 16-138). Surfaces `config.chat.suggestedPrompts` on first load; sessions get a `crypto.randomUUID()` for Zeus correlation.

**`Nav`** (`src/components/nav.tsx`) — fixed top nav with a purple gradient stripe (`linear-gradient(135deg, #5D32BB, #615FF3)` — not theme-driven; see Tech Debt). Scrollspy via `IntersectionObserver` (lines 17-27) highlights the anchor for the currently-visible section. Anchor links rewrite to `/#anchor` form on non-home routes.

**`Sidebar`** (`src/components/dashboard/sidebar.tsx`) — dashboard-only. Splits `dashboard.sidebarLinks` into anchor links (sets `activeSection` index) vs route links (normal `<a>` nav). The anchor index maps 1:1 to `dashboard.sections[index]` in `DashboardPage`.

### Design decisions worth calling out

- **Config-driven single build, not a CMS.** All content lives in TypeScript. No database, no headless CMS, no MDX. Trade-off: Claude-generated content is validated by the TypeScript compiler plus 624 Vitest tests; cost is every copy change requires a rebuild.
- **`site.config.ts` is gitignored on purpose** (`.gitignore:3`). The template stays clean; per-site content never contaminates the template repo. The `postinstall` hook copies the example so `npm run dev` works on first clone.
- **Three templates coexist in one codebase by deliberate design.** Each deployed site uses exactly one. Adding a fourth template = one case in `page.tsx` + one top-level component + a new optional config field.
- **AI comparison colours are fixed real-world brand colours** — `CLAUDE.md:158`: Gemini `#4285F4`, ChatGPT `#10a37f`, Copilot `#7B61FF`, Claude `#d97706`. Enforced by assertions in `claude-md-claims.test.ts:61`.
- **Hero format is enforced by tests** — `claude-md-claims.test.ts:5-29` asserts (a) every landing hero `title` ends with ` —` (em-dash space), (b) every `animatedWords` entry ends with `.`, (c) if exactly 2 CTA buttons then first is `solid`, second is `outline`.
- **Hard-coded ecosystem-node colours** — `ecosystem-diagram.tsx:10-16` defines 5 colours by side-kind: hub=accent, source=`#3b82f6`, destination=`#ec4899`, circular=`#f59e0b`, policy=`#8b5cf6`. Only hub uses the config accent; the other four are not theme-driven.

---

## Data Flow

### Build-time — config drives the whole site

Developer (or Claude) writes `site.config.ts` → `npm run build` runs → Tailwind reads `accentColor`/`glowColor` from the config (`tailwind.config.ts:2-4`) → Next.js compiles every component with the config's data baked in at module load (`getConfig()` → sync import of `../../site.config`). Output: `.next/` (static + SSR assets).

There is no runtime fetch for content. No CMS. The config becomes HTML/CSS/JS at build time and is frozen.

### Runtime — three flows

1. **Page renders.** Static pages + React Server Components for `/`, `/calculator`, `/chat`, `/why-aldc`. No data fetching beyond the baked-in config. PostHog snippet fires client-side if `NEXT_PUBLIC_POSTHOG_KEY` is present (`layout.tsx:35-46`).

2. **Chat request.** Browser → `POST /api/chat` with `{message, history, sessionId}` → `app/api/chat/route.ts`:
   - In-memory rate limit: 20 req / min / IP (`route.ts:6-55`).
   - Body validation (`validateBody` — `route.ts:59-80`): rejects `message > 2000 chars`, `history > 20 entries`, bad roles.
   - Returns 404 if `config.chat.systemPrompt` not set; 500 if `ANTHROPIC_API_KEY` missing.
   - POSTs `https://api.anthropic.com/v1/messages` with `stream: true`. Streams back as SSE; each Anthropic `content_block_delta` is re-wrapped into `{type: "token", text}` frames (`route.ts:157-172`).
   - After stream closes: fire-and-forget POST to Zeus Memory at `${ZEUS_API_URL}/api/memory` with `X-API-Key: ${ZEUS_API_KEY}`, body `{content: "User: <Q>\n\nAssistant: <A>", source: "<subdomain>_chat", metadata: {subdomain, session_id, timestamp}}` (`route.ts:9-40`). Non-fatal. Disabled if either var missing. See [[zeus-memory]].

3. **Analytics.** PostHog client-side only. No server-side events. All 15 known sites share the same `NEXT_PUBLIC_POSTHOG_KEY` (public by design — see Integrations).

### Lead capture form (pitch template) — no submit handler

`src/components/pitch/pitch-page.tsx:63` has `<form onSubmit={(e) => e.preventDefault()}>`. The form is visual only; collected state is kept in component state and never POSTed. The CTA in the same component falls through to `mailto:${config.contactEmail}` (line 177). This is a known-pending integration — see Tech Debt.

### Side channels

None. No NextAuth, no cookies set by the app, no Vercel cron jobs, no scheduled tasks. Content-only app plus one streaming server route.

### Cross-reference

Unlike [[entities/repos/flight-check|flight-check (repo)]] (4 backend proxies), [[entities/repos/eclipse|eclipse (repo)]], or [[eclipse_exp]], this repo has no backend integrations beyond Anthropic (required for chat) and Zeus (optional logging).

---

## Developer Guide

### Prerequisites

- Node 22 (CI pins to Node 22 in `.github/workflows/ci.yml:19`; Node 20 likely works; Node 18 will not match CI).
- npm (package-lock.json committed; `npm ci` is the CI install command).
- [[claude_code_enhanced|Claude Code CLI]] — optional; only needed for the AI-assisted generation path.
- Anthropic API key — optional; only needed for `/api/chat` to work locally.
- Zeus Memory API key — optional; only if chat logging should land in Zeus. See [[zeus-memory]].

### First-run setup (from clean clone)

1. `git clone <repo>` and `cd prospect-site-template`. Per `README.md:13`, you must be in this directory for Claude-driven generation to work.
2. `npm install` — triggers the `postinstall` script (`package.json:11`), which copies `site.config.example.ts` to `site.config.ts` if the latter does not exist. This completes the build graph (Tailwind imports the config at build time).
3. `cp .env.example .env.local` and edit:
   - `NEXT_PUBLIC_POSTHOG_KEY` — already set to the ALDC-wide key. Per `CLAUDE.md:37`, do NOT change this.
   - `NEXT_PUBLIC_POSTHOG_HOST` — default `https://us.i.posthog.com`.
   - `ANTHROPIC_API_KEY` — replace the `sk-ant-xxx` placeholder with a real key. Without this, `/api/chat` returns 500.
   - `CHAT_MODEL` — defaults to `claude-sonnet-4-6`. Override only if intentionally switching models.
   - `ZEUS_API_URL` / `ZEUS_API_KEY` — optional. Without them, chat works but nothing is logged to Zeus.
4. `npm run dev` — Turbopack dev server at `http://localhost:3000`.

### Generating a new site via Claude

1. Open Claude Code in the repo directory.
2. Tell Claude: "Make me a site about X" (or "build me a dashboard for Y", or "make an enterprise pitch page for Z").
3. Claude reads `CLAUDE.md`, picks a template (`CLAUDE.md:55-73`), reads `src/lib/types.ts` and `site.config.example.ts`, web-searches any statistics per the fact-checking requirement (`CLAUDE.md:42-51`), writes `site.config.ts`, runs `npx vitest run`, runs `npm run build`, and tells you to `npm run dev`.
4. To keep the generated site: `cp -r . /path/to/new-site && cd /path/to/new-site && git init && git add -A && git commit -m "Initial site"`. Then deploy from the copy (`README.md:55-68`, `CLAUDE.md:17-29`). The template folder stays clean.
5. Alternative: `./create-site.sh <subdomain> ./path/to/config.ts` — same pipeline but scripted. Copies source files to `./sites/<subdomain>/`, installs, tests, builds, prints deploy hints. **Note:** the script writes inside the template folder and those output directories are not gitignored — see Tech Debt.

### Scripts

| Command | What it does |
|---|---|
| `npm run dev` | `next dev --turbopack` on :3000 |
| `npm run build` | `next build` (production output in `.next/`) |
| `npm start` | `next start` against the production build |
| `npm run lint` | `next lint` (ESLint flat config) |
| `npm run typecheck` | `tsc --noEmit` |
| `npm run test` | `vitest run` |
| `postinstall` | Copies `site.config.example.ts` → `site.config.ts` iff absent |

### Testing

Runner: Vitest 3.2. Environment: jsdom, with `scrollIntoView` + `IntersectionObserver` polyfilled in `setup.ts`. Globals (`describe`/`it`/`test`/`expect`) available without import (`vitest.config.ts:12`).

**Actual test count (confirmed 2026-04-20 by running `npx vitest run`):** 624 total — 622 passed, 2 skipped across 11 test files. README line 83 says "624 tests" (correct for total count); CONTRIBUTING line 22 says "394 tests" (wrong — stale, see Tech Debt).

| File | Tests | Purpose |
|---|---|---|
| `config-validation.test.ts` | 193 | Exhaustive valid-config permutations |
| `theme-css.test.ts` | 120 | CSS custom property generation per theme |
| `claude-md-claims.test.ts` | 56 | Asserts CLAUDE.md rules are enforced in fixtures |
| `decision-tree.test.ts` | 40 | No cycles, all outcomes reachable, tier 1-6 legality |
| `live-config.test.ts` | 40 (2 skipped) | Validates the actual built `site.config.ts` |
| `theme.test.ts` | 44 | Theme field validation |
| `site-variants.test.ts` | 67 | 15 site fixtures stay consistent |
| `config-negative.test.ts` | 16 | Invalid configs are rejected |
| `sections.test.ts` | 15 | Section-type field validation |
| `dashboard-variants.test.ts` | 15 | Dashboard fixture correctness |
| `component-render.test.tsx` | 18 | React component smoke renders |

Key test files to understand the design:

- `live-config.test.ts` — validates whatever is currently in `site.config.ts` (theme hex validity, required fields, hero format, template-specific fields). This is what makes the test suite double as a runtime schema check.
- `site-variants.test.ts` — validates that the 15 site fixtures stay consistent: 11 cultivate family, 2 dashboard, 1 pitch, calculator-enabled sites = 11, chat sites = 4 (whyaldc + foodmesh + cpma + ghostpine), no-PostHog sites = [sources] only, `epr` contact-email exception (`john@analyticlabs.io`).
- `claude-md-claims.test.ts` — asserts CLAUDE.md rules: hero title ends with ` —`, animated words end with `.`, first CTA button is `solid` and second is `outline`, pitch has 3 compounding bars labelled Day 1 / Day 90 / Year 1, AI comparison contains Gemini at `#4285F4`.

### Local debug / common pitfalls

- **Tailwind build failure** — if `site.config.ts` is missing or malformed, `tailwind.config.ts:2-4` fails to import it and the whole build dies before Next.js compiles. Fix: verify `site.config.ts` exists (rerun `npm install` to trigger `postinstall`) and TypeScript-compiles cleanly.
- **`/api/chat` 500 without `ANTHROPIC_API_KEY`** — `route.ts:109-111`. Easy to miss if you skipped the `.env.local` copy.
- **`/api/chat` 404 without `config.chat`** — `route.ts:102-104`. The chat route is gated on the site config, not the server env. A landing-only config that doesn't set `chat` returns a 404.
- **Rate limiter is in-memory** — `route.ts:6-8` uses a module-scoped `Map`. In serverless / multi-instance deploys (Vercel's default), each instance has its own counter. Effective limit is higher than the nominal 20/min. Not a security issue; just worth knowing.
- **PostHog key is committed** (in `.env.example`, `CLAUDE.md:37`). Deliberate. The same key is used by all 15 sites; it is a `NEXT_PUBLIC_*` identifier, visible in any browser's network tab. Not a secret.
- **Two test-count claims disagree** — README "624 tests" (correct) vs CONTRIBUTING "394 tests" (stale). See Tech Debt.
- **`create-site.sh` writes `sites/<subdomain>/` in-place** — not gitignored; leaves untracked output if run inside the template folder.
- **`/why-aldc` is a stub** — `src/app/why-aldc/page.tsx` renders "Coming soon". Do not mistake it for a live route.
- **Pitch `<form>` has `onSubmit={(e) => e.preventDefault()}`** — no lead capture backend. CTA falls through to `mailto:`.
- **React 19 + Next 15 is recent** — all five CI checks (lint, prettier, tsc, vitest, build) must pass. Run `npx prettier --write .` before pushing if you hit a format failure.

---

## Deployment

### What "deploys" here

The template repo itself never runs in production. What deploys is a **copy of the template folder with a filled-in `site.config.ts`** — one copy per prospect subdomain. The 15 existing sites at `*.analyticlabs.io` are on Vercel (confirmed by `dpl_*` deployment hashes in RSC chunk URLs — `docs/source-analysis.md:342-348`). README lists Netlify, Cloudflare Pages, Docker, any Node host as options for new sites; no host is prescribed by the template.

There is no `vercel.json` in the repo. Vercel auto-detects Next.js.

### Per-site deployment flow

1. Generate the site (Claude-driven or hand-written `site.config.ts`).
2. `cp -r . /path/to/<subdomain>-site` to make a standalone copy — or run `./create-site.sh <subdomain> [config-path]` which copies `src/`, `public/`, `package.json`, `tsconfig.json`, `next.config.ts`, `tailwind.config.ts`, `postcss.config.mjs`, `vitest.config.ts`, the `.env.example` (as `.env.local`), and the config into `./sites/<subdomain>/`.
3. `git init && git add -A && git commit -m "Initial site"` in the copy.
4. Push to a new GitHub repo.
5. Connect to Vercel (or host of choice); set env vars (`ANTHROPIC_API_KEY`, `ZEUS_API_URL`, `ZEUS_API_KEY`, `CHAT_MODEL`, PostHog pair).
6. DNS CNAME `<subdomain>.analyticlabs.io` → the Vercel deployment.

### Template-repo CI/CD

`.github/workflows/ci.yml` (42 lines) runs on every PR to `main` and every push to `main`. Single job `validate` on `ubuntu-latest`, Node 22.

Steps: `actions/checkout@v4` → `actions/setup-node@v4` (npm cache) → `npm ci` → `npx eslint . --max-warnings 0` → `npx prettier --check .` → `npx tsc --noEmit` → `npx vitest run` → `npx next build` → verify `.next/standalone` or `.next/server` exists.

Workflow name: **"CI — Protect Template Integrity"**. No deploy step. The template repo is not deployed. Each generated site has its own external CI/CD chain.

### Secrets

- `NEXT_PUBLIC_POSTHOG_KEY` — committed in `.env.example`. Public by design (a `NEXT_PUBLIC_*` var; same key used across all 15 sites; visible in any browser network tab). Document in prose; do not extract to vault.
- `ANTHROPIC_API_KEY`, `ZEUS_API_KEY` — `.env.example` has `sk-ant-xxx` / `zm_xxx` placeholders. Not committed in real form. Real values live in the deployment-host secret store, not in any site repo.

### Rollback

Per-site: use the deploying host's rollback (Vercel previous deployment, GitHub revert, etc.). Nothing in the template repo orchestrates this. For the template repo itself: revert the offending PR via GitHub. Running sites are unaffected — they are independently deployed copies.

### Cross-reference

Unlike [[entities/repos/flight-check|flight-check (repo)]], [[entities/repos/eclipse|eclipse (repo)]], and [[eclipse_exp]] — which deploy to Azure Container Apps via GitHub Actions + slot swap — the generated sites deploy to Vercel. Different infrastructure. The [[aldc-naming-convention]] for Azure resources does not apply here.

---

## The 15 Known Sites

### Site catalogue

Data sourced from `src/__tests__/fixtures/configs.ts:5-110` and `:850-881`, cross-referenced against `docs/source-analysis.md`.

| Subdomain | Template | Accent | tokenNamespace | Calculator | Chat | Notes |
|---|---|---|---|---|---|---|
| cultivate | landing | `#10b981` green | cultivate | ✅ | — | Flagship — "From Field to Fork" |
| strategy | landing | `#4f46e5` indigo | cultivate | ✅ | — | — |
| packaging | landing | `#0d9488` teal | cultivate | ✅ Compliance Tool | — | — |
| distribution | landing | `#d97706` amber | cultivate | ✅ Loss Estimator | — | — |
| stewardship | landing | `#059669` green | cultivate | ✅ EPR Calculator | — | — |
| economics | landing | `#2563eb` blue | cultivate | ✅ ROI Calculator | — | — |
| epr | landing | `#e11d48` rose | cultivate | ✅ Assessment | — | Red accent under `cultivate` namespace — legacy quirk per `source-analysis.md:352` |
| eccc | landing | — | cultivate | ✅ Assessment | — | — |
| foodmesh | landing | — | cultivate | ✅ | ✅ | Only landing site with BOTH calculator AND chat |
| cpma | landing | — | cpma | ✅ Navigator | ✅ | — |
| sources | landing | — | sources | ✅ Assessment | — | Only site without PostHog (`configs.ts:848`) |
| producer | landing | — | producer | — | — | No calculator; outside both family lists — see Tech Debt |
| whyaldc | pitch | aldc | aldc | — | ✅ | Lead capture + AI comparison |
| ghostpine | dashboard | `#f59e0b` amber | ghostpine | — | ✅ | Live data + Windy.com iframe (one-off features) |
| agristack | dashboard | `#22c55e` green | agristack | — | — | Light sections below dark hero — third distinct design |

### Template-to-site mapping summary

- **11 landing** (10 cultivate family + `producer`) / **1 pitch** (whyaldc) / **2 dashboard** (ghostpine, agristack).
- Sites with calculator (11): cultivate, strategy, packaging, distribution, stewardship, economics, epr, eccc, foodmesh, cpma, sources.
- Sites with chat (4): whyaldc, foodmesh, cpma, ghostpine.
- Sites without PostHog (1): sources only.
- `epr` uses `john@analyticlabs.io` as contactEmail; all others use `contact@analyticlabs.io`.

### This table is fixture-derived, not runtime-observed

The data lives in `src/__tests__/fixtures/configs.ts` because these are test assertions — the fixtures encode what the template must be able to produce. Whether each subdomain has an active Vercel deployment at any given time is not guaranteed by this repo. `docs/source-analysis.md` documented 15 live sites as of its last scrape. Treat the table as "template capability", not "current production state".

---

## Config Reference

A reader who needs to generate a `site.config.ts` should open `src/lib/types.ts` (the full TypeScript schema) and `site.config.example.ts` (a complete working example for a Cultivate landing site). This section summarises the key fields.

### Top-level fields

| Field | Required | Notes |
|---|---|---|
| `template` | Always | `"landing"` \| `"dashboard"` \| `"pitch"` |
| `subdomain` | Always | e.g. `"cultivate"` |
| `siteName`, `siteLabel` | Always | Display name + short label |
| `theme.accentColor` | Always | CSS hex; drives Tailwind build |
| `theme.glowColor` | Always | CSS hex; accent glow effect |
| `theme.accentRgba` | Always | `rgba(...)` form for CSS transparency |
| `theme.sweepName` | Always | Human name for the sweep animation |
| `theme.tokenNamespace` | Always | Legacy CSS class root (e.g. `"cultivate"`) |
| `title`, `metaDescription`, `ogDescription`, `ogSiteName` | Always | SEO |
| `contactEmail`, `footerTagline`, `footerEntity` | Always | Footer + mailto CTA |
| `nav.links[]` | Always | Array of `{label, href}` |
| `nav.badges[]` | Optional | Prominent nav badges |
| `hero` | Landing only | `HeroConfig`: animated title, words, stat cards, CTAs |
| `sections[]` | Landing only | Array of typed `SectionConfig` objects |
| `ecosystemDiagram` | Landing only | Nodes + edges for SVG diagram |
| `calculator` | Optional | `CalculatorConfig`: decision tree with outcomes + principles |
| `chat` | Optional | `ChatConfig`: system prompt + suggested prompts + model |
| `dashboard` | Dashboard only | `DashboardConfig`: sidebar links, KPIs, sections, optional logoPath |
| `pitch` | Pitch only | `PitchConfig`: compounding bars, AI comparison, lead form, value props |

### Landing section types

Eight discriminated-union types keyed by `type` field:

- **`problem`** — title + 3 narrative paragraphs + optional `accentPhrase` + optional `closingLine` + 3-4 timeline cards.
- **`vision`** — title + subtitle; renders the `ecosystemDiagram`.
- **`stakeholders`** — 6-7 cards; last one is `fullWidth: true` per `CLAUDE.md:115`.
- **`platform`** — exactly 4 phases; required colours `#10b981` `#3b82f6` `#f59e0b` `#8b5cf6` (`CLAUDE.md:116`).
- **`global`** — 4 country cards with `flagColors` (`CLAUDE.md:117`).
- **`alignment`** — 3 pillars.
- **`funding`** — 2 grant categories + summary + tags.
- **`join`** — CTA title + description.

### Ecosystem diagram coordinate conventions (`CLAUDE.md:131-138`)

Hub `x:50 y:50`; sources `x:15 y:20/35/50/65/80`; destinations `x:85 y:25/50/75`; circular `x:35/65 y:90`; policy `x:50 y:8`. Edge colour conventions: `#10b981` (flow), `#ec4899` (distribution), `#f59e0b` (feedback), `#8b5cf6` (policy).

### Calculator tree rules (`CLAUDE.md:140-144`)

- Root ID = `"start"`; outcome node IDs prefixed `"outcome-"`.
- 5-10 question nodes, 5-8 outcome nodes; tiers 1 (best) to 6 (worst); 4 principles.
- No cycles; all outcomes reachable from `"start"`. Validated by `decision-tree.test.ts`.

### Pitch AI comparison required values (`CLAUDE.md:157-158`)

Must include real AI tools with exact brand colours: Gemini `#4285F4`, ChatGPT `#10a37f`, Copilot `#7B61FF`, Claude `#d97706`. These are assertions in `claude-md-claims.test.ts:61` — changing them breaks tests.

### Fact-checking requirement (`CLAUDE.md:42-51`)

Every stat, dollar figure, regulatory date, and organisation name must be web-verified before generating. Unverified values get a `// UNVERIFIED — check before publishing` comment. This is a generation-time discipline, not a runtime check.

---

## Integrations

Three external systems, all touched only by `src/app/api/chat/route.ts` (server-side) or `src/app/layout.tsx` (client-side):

**Anthropic Messages API** — `POST https://api.anthropic.com/v1/messages`, SSE streamed. Headers: `anthropic-version: 2023-06-01`, `x-api-key: ${ANTHROPIC_API_KEY}`. Model from `CHAT_MODEL` env or default `claude-sonnet-4-6`. No SDK — raw `fetch`. Used by `/api/chat` route only.

**Zeus Memory** — optional fire-and-forget `POST ${ZEUS_API_URL}/api/memory` with `X-API-Key: ${ZEUS_API_KEY}` after each completed chat conversation. Body includes the full user/assistant exchange, a content summary, source identifier, and session metadata. Silent on error. Disabled if either env var is absent. Cross-link: [[zeus-memory]].

**PostHog** — inline browser-side snippet injected from `layout.tsx:35-46`, gated on `NEXT_PUBLIC_POSTHOG_KEY`. Client-only (no server-side events). One project key shared across all 15 known sites; the key is committed in `.env.example` by design — it is a public `NEXT_PUBLIC_*` identifier visible in any browser network tab.

---

## Known Issues / Tech Debt

- **Test count discrepancy in docs** — README.md line 83 says "624 tests" (confirmed correct: 622 passed + 2 skipped = 624 total as of 2026-04-20). CONTRIBUTING.md line 22 says "394 tests" (stale, wrong). Update CONTRIBUTING to match the confirmed count.

- **Pitch template lead capture has no backend** — `pitch-page.tsx:63` has `onSubmit={e => e.preventDefault()}`. Form is visual only. No lead data reaches any CRM or queue. CTA falls through to `mailto:`. This will be resolved when prospect-site generation moves into [[eclipse_exp]], which has a full onboarding flow. Until then, document this to anyone deploying a pitch site.

- **In-memory rate limiter** — `api/chat/route.ts:6-8` uses a module-scoped `Map`. In serverless / multi-instance deploys (Vercel's default), each instance has its own counter. Effective rate cap is higher than the nominal 20 req/min per IP. Not a security failing, but deployers should be aware.

- **`create-site.sh` writes `sites/<subdomain>/` in-place** — not gitignored. Running the script inside the template folder leaves untracked output directories. Either add `sites/` to `.gitignore` or document that the script should be run from outside the repo.

- **`/why-aldc` is a stub** — `app/why-aldc/page.tsx` renders "Coming soon". Exists in nav by convention only; legacy sites had a real page here. Either implement or remove.

- **No Vercel config** — no `vercel.json`. Each generated copy relies on Vercel auto-detection. Fine for Next.js, but worth noting so a deployer doesn't search for a config that isn't there.

- **Hard-coded ecosystem-node colours** — `ecosystem-diagram.tsx:10-16`. The 5 side-kind colours (source/destination/circular/policy) are baked into the component; only hub uses the config accent. Changing them requires a component edit, not a config change.

- **Hard-coded nav gradient bar** — `nav.tsx:32` uses `linear-gradient(135deg, #5D32BB, #615FF3)`. Not theme-driven; every site gets the same purple ALDC brand gradient regardless of accent colour.

- **No `.nvmrc` or `engines` field** — CI uses Node 22 explicitly; local dev could drift. Add a `.nvmrc` for consistency.

- **`producer` site fixture is outside both family lists** — `configs.ts:864-865` defines `cultivateFamilySites` (11 sites, not including `producer`) and `dashboardFamilySites` (2 sites). `producer` appears in `themes`, `tokenNamespaces`, and `allSiteNames` but has no dedicated test block in `site-variants.test.ts`. It is unclear whether this is in-flight new work, a decommissioned site, or an oversight. Flagged for human attention.

- **This repo will be absorbed by `eclipse_exp`** — the modernisation is happening in a different repo. Until the eclipse_exp onboarding flow is wired and the `build.prospect.aldc.io` webhook is live, this repo remains the canonical way to create prospect sites. Track progress in [[eclipse_exp]].

---

## See Also

- [[zeus-memory]] — optional destination of chat conversation logs (`/api/chat` → `/api/memory`). Cross-repo runtime dependency.
- [[eclipse_exp]] — next-gen ALDC platform absorbing prospect-site generation. The `POST /api/v1/onboarding/webhooks/prospect-created` webhook targeting `build.prospect.aldc.io` is the planned integration path that will replace this repo's manual clone-and-deploy workflow. See [[eclipse_exp]] for the onboarding flow and KPI templates.
- [[entities/repos/eclipse|eclipse (repo)]] — legacy Next.js 14 Pages Router portal UI. Different product, different repo, different generation of the ALDC stack. Disambiguation only.
- [[entities/repos/flight-check|flight-check (repo)]] — third Next.js repo in the portfolio; fans out to 4 backends (core_api, DAX API, DIOS, NetSuite). Disambiguation only.
- [[claude_code_enhanced]] — CCE is the tool that drives the Claude-prompt generation flow described in Developer Guide. Claude reads `CLAUDE.md` in this repo as its instruction set when generating `site.config.ts`.
- [[ai-development-project-standard]] — ALDC's tracking standard for AI-developed projects. This repo's generation model (>50% AI-authored configs) aligns with that standard.
- [[cce]] — project-level cousin of [[claude_code_enhanced]]; CCE is the runtime, cce is the project/product page.
- [[phaselab]] — another AI-prototyped ALDC product; shares the "config-as-truth" sensibility where brief → spec → variant generation.
- [[connector]] — also being migrated into [[eclipse_exp]] as part of the same strangler-fig consolidation that will absorb this repo.
