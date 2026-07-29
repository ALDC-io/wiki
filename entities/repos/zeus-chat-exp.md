---
tags: [repo, zeus, zeus-chat, nextjs, typescript, aldc, eclipse, powerbi, navira, multi-tenant, llm, litellm, azure]
aliases: [zeus-chat-exp, Zeus Chat, zeus.analyticlabs.io, northwind-chat]
sources: []
created: 2026-07-29
updated: 2026-07-29
---

# zeus-chat-exp (Zeus Chat)

ALDC's **agentic chat product** — a **Next.js 16 (App Router) / React 19 / TypeScript** multi-tenant LLM chat surface that answers business questions by calling tools against [[zeus-memory]] (memories, entities, KB), the [[Eclipse]] data plane (live Power BI datasets), Google/Microsoft connectors, and web search. Repo: `github.com/ALDC-io/zeus-chat-exp` (private). Local: `C:\Users\PaulRussell\repos\zeus-chat-exp`. Production: **https://zeus.analyticlabs.io**.

The `-exp` suffix is historical ("experiment") — this is a live product serving real client financial data, not a prototype. The Vercel project is still named **`northwind-chat`** (PR previews deploy there); production runs on **Azure Container Apps**.

## Stack

| Layer | Choice |
|---|---|
| Framework | Next.js **16.2.4** (App Router), React **19.2.4**, TypeScript 5 |
| UI | **Mantine v9** (`@mantine/core|hooks|notifications`), Tabler icons, DOMPurify |
| LLM access | **OpenAI SDK** (`openai` v6) pointed at a **LiteLLM proxy**, plus **Anthropic SDK** (`@anthropic-ai/sdk` v0.90) direct for the confabulation judge (Haiku 4.5) |
| State/cache | **Redis** (`ioredis`) — sessions, rate limits, inflight caps |
| Crypto | `libsodium-wrappers-sumo` (token/secret sealing), `src/lib/crypto.ts` |
| Tests | **Vitest** (unit + integration configs), **Playwright** (e2e) |
| Deploy | Docker → **Azure Container Registry `acrzeusmemorydev`** → Azure Container Apps; LiteLLM proxy deployed as a sibling container app |
| CI | `.github/workflows/` — `ci.yml` (tsc / vitest / prod build / LiteLLM smoke), `deploy.yml`, **`claude-review.yml`** (Opus PR review bot) |

## Repo layout

```
src/
├── app/
│   ├── page.tsx              # chat home; quick-action pills (briefing, trend alerts,
│   │                         #   team utilization, METRICS DIGEST) that inject prompts
│   ├── embed/route.ts        # embeddable surface
│   └── api/                  # ~60 route handlers
│       ├── chat/route.ts     # THE core route — orchestrates the whole agent loop
│       ├── auth/ login/ me/  # session auth, SSO, OBO bridge, TOTP, password reset
│       ├── chat-store/       # persisted sessions, folders, sharing, email
│       ├── connectors/       # Google + Microsoft OAuth connect/disconnect/status
│       ├── memories/ memory/ # Zeus Memory CRUD + classify-on-save
│       ├── team/             # roster, presence, shares, activity
│       ├── briefing/ advice/ skills/ learn/ upload/ export/
├── components/
│   ├── zeus-chat.tsx         # ~3k-line main chat client (SSE consumer, viz, badges)
│   └── right-pane, session-sidebar, team-panel, share-*, settings/
├── lib/
│   ├── system-prompt.ts      # buildSystemPrompt() — the single prompt assembler
│   ├── confabulation-judge.ts# post-response Haiku judge (ALDC-626 Q6)
│   ├── tenant-data-config.ts # tenant → DatasetConfig; catalog fetch/cache/validate
│   ├── eclipse-client.ts     # Eclipse dataset metadata + dataset/request queries
│   ├── adapters/powerbi.ts   # NAVIRA_CATALOG, measure/column metadata, COGS_MEASURES
│   ├── viz/                  # chart spec extraction, validation, layouts, palette
│   ├── zeus-client.ts, ccx-client.ts, litellm-client.ts, anthropic-routing.ts
│   ├── auth-session.ts, sessions.ts, oauth-client.ts, rate-limit.ts, redis.ts
│   └── team*.ts, chat-store-mapping.ts, retrieval-learner.ts, insight-classifier.ts
└── tools/
    ├── schemas.ts            # tool definitions grouped into tiers
    └── handlers.ts           # ~2.5k lines — every tool implementation
```

## The agent loop (`src/app/api/chat/route.ts`)

Single POST route, SSE-streamed. Roughly:

1. **Auth + session** → `sess` (tier, tenant context via Zeus `whoami`).
2. **`resolveDataAccess(tenant_id, …)`** — populates the sync cache used later by `getDatasetConfig`.
3. **Context assembly** — core-memory anchors (tenant-scoped since ALDC-626 Vector 3), CCX peek (memories + news, internal-tier only), calendar windows, connected sources, skills, and **`confabulationCorrections`** (recent judge signals re-injected as "you previously fabricated X").
4. **`buildSystemPrompt(sess, hasZeusKey, opts)`** — one big assembled prompt; branches on `hasDataAccess`, `isAdmin`, `hasGoogle`/`hasMicrosoft`, tier.
5. **Multi-round tool loop** — `buildRound0Tools(isInternal)` then subsequent rounds; tool results stream back as SSE frames (`data_result`, sources, memory writes, advice).
6. **Post-response `judgeConfabulation(...)`** — fire-and-forget Haiku 4.5 call comparing the assistant text against the turn's `retrievalTrace`; verdicts persisted via `emitMeasurementEvent` and re-read next turn by `fetchRecentConfabulations`.

### Tool tiers (`src/tools/schemas.ts`)
- **`MEMORY_TOOLS`** — `search_memory`, `scatter_search`, `write_memory`, `entity_profile`, `search_entities`, `search_meeting_clips`, `search_web`, `deep_research`, KB CRUD, `query_data`, …
- **`INTERNAL_ONLY_TOOLS`** (fail-closed, gated on `isInternal`) — `get_trend_alerts`, `get_team_utilization`, **`get_metrics_digest`**
- **`ADMIN_TOOLS`** / **`RBAC_SELF_TOOLS`** — RBAC grants, roles, users
- **`SKILL_TOOLS`**, **`CCX_TOOLS`** (only when `CCX_SERVICE_URL` set)

`isInternal = (sess.tier ?? "internal") === "internal"` — note the **default is internal**.

## Data access — how Zeus Chat reads client analytics

This is the part that matters for [[GEP]]/Navira work.

- **`src/lib/tenant-data-config.ts`** maps tenant → `DatasetConfig { accountId, datasetId, eclipseApiUrl, eclipseAppUrl, dataViewId, label }`.
- There is currently **exactly one** dataset config: **`NAVIRA_DATASET_CONFIG`** — account `da8904db`, dataset `e80ffd34-e77e-4311-9902-5a7e37a41546` (the same Eclipse PBI "Data Model" that [[concept-gep-data]] reads), `label: "Navira"`.
- Access is granted two ways:
  - **`TENANT_TO_DATASET_CONFIG`** — a hardcoded allowlist of 8 tenant UUIDs: Heather Tabor (Navira) plus **7 ALDC staff** (JK, Vlad Ryzhkov, Mike Stuart, Paul Russell, Lori Beck, LingJun Zhou, Tamoor Zahid).
  - **`DATA_ACCESS_ORG_ANCESTORS`** — the Navira org and the ALDC Management Team org; any descendant tenant resolves via `GET /api/v1/org/{id}/tree` on Zeus and is cached in `resolvedAccessCache`.
- **`getDatasetConfig()` is synchronous** (map read); **`resolveDataAccess()` is async** and must run first to populate the cache. `hasDataAccess` in the chat route is just `getDatasetConfig(tenant_id) !== null`.
- **Catalog** — `NAVIRA_CATALOG` (from `adapters/powerbi.ts`) seeds the cache at cold start; `refreshAllCatalogs()` pulls live measure/column metadata from Eclipse, merges descriptions 3 ways (data dictionary > NAVIRA_CATALOG > PBI description), sanitises, and runs **guard-set assertions** (`COGS_MEASURES`, `SALES_GUARD`, `MARKETING_GUARD`) that log `GUARD_SET_VIOLATION` if a known measure disappears. `validatePostRefresh` detects orphaned dictionary keys, probable renames (by measure-expression hash), and changed formulas.

### `query_data` (`src/tools/handlers.ts`)
The measure-query tool. Resolves natural-language measure/dimension names against the catalog, applies periodicity + filters, calls the Eclipse `dataset/request` API, and returns:
- a **text `content`** summary (+ up to 50 rows of JSON) for the model,
- an SSE **`data_result`** frame for the UI (rows, `measures_used`, `dimensions_used`, filters, `eclipseUrl` deep link, `dataset_label`, `null_measures`),
- a **confidence score** computed from resolution quality, periodicity set/omitted, cross-scope, pre-COGS window, and row count → `confidence_pct` plus `confidence_level ∈ VERIFIED | APPROXIMATE | NO_DATA_ACCESS`,
- a **`retrievalTrace`** entry consumed by the confabulation judge.

Concurrency is capped per tenant (`dataQueryInflight`).

> ⚠️ **The confidence badge exists twice.** There is a real UI badge in `zeus-chat.tsx` driven by `data_result.confidence_level`, *and* `system-prompt.ts` separately instructs the model to type `**Confidence: Verified (90%)**` as markdown. An LLM-authored provenance stamp is spoofable by construction — this is the structural root cause behind [[ALDC-739]].

## Anti-confabulation machinery

Zeus Chat has an unusual amount of purpose-built anti-hallucination scaffolding, which is worth knowing before adding more:

1. **Prompt-level rules** in `buildSystemPrompt` — source-attribution rules, confidence-format rules, a `hasDataAccess: false` branch that forbids quoting financial figures, and (from [[ALDC-739]]) a "Data query hard rules — MANDATORY" block.
2. **`confabulation-judge.ts`** — post-hoc Haiku 4.5 judge (from ALDC-626 Q6, replacing a regex detector). Classifies `fabricated_value`, `invented_tool_result`, `source_misattribution`, `unconnected_source`. Documented recall: ~75% fabricated values, ~90% invented tool results. **Fire-and-forget — it never blocks the streamed response.**
3. **Feedback loop** — judge verdicts persist as measurement events; `fetchRecentConfabulations` pulls them next turn into `confabulationCorrections` in the system prompt. This loop is powerful and **bidirectionally dangerous**: false positives teach the model to distrust correct retrievals.
4. **Prompt-injection fencing** — untrusted blocks are explicitly fenced in the judge prompt; `tenant-data-config.ts` sanitises control chars and caps lengths on all catalog strings; there is a dedicated "response rows prompt injection surface" test in `src/lib/__tests__/coverage-gaps.test.ts`.

## Testing

- `npm test` → `vitest run` (~1,280 tests at the time of [[ALDC-739]]).
- `npm run test:e2e` → Playwright: `auth-smoke`, `data-tool-e2e`, `memory-pipeline-e2e`, `obo-auth-e2e`, `sharing-e2e`, `admin-tools-e2e`, `web-search-e2e`, `onboarding-e2e`, `aldc626-context-assembly-e2e`, `session-end-learnings-e2e`.
- `npm run test:integration` → `scripts/run-integration.sh` (LiteLLM proxy up, real provider keys).
- **Repo rule (`CLAUDE.md` → `AGENTS.md`):** before opening a PR you must run `npm test` and fix *production* code, not tests. Changing a test requires calling it out explicitly in the PR description.
- **`claude-review.yml`** auto-runs an Opus review on every PR open/sync, posting inline + summary comments. Expect bot review comments on every PR here; they are advisory, occasionally overstated, and worth verifying before acting.

## Known tickets

- [[ALDC-739]] — P1: Zeus Chat fabricated a full financial digest with a fake "Verified (100%)" badge; plus a real Net Sales period-filter leak and a tenant-attribution gap.
- ALDC-722 — PBI periodicity routing for historical queries + Navira cross-scope detection (PR #165).
- ALDC-705 — `is one of` filter (PR #162).
- ALDC-626 — context assembly / confabulation work (Q6 = the judge; Vector 3 = tenant-scoped core memory).

## Gotchas

- **Vercel preview project is `northwind-chat`** — an old name; don't assume a separate app.
- **`sess.tier ?? "internal"`** defaults users *into* the internal tier — the fail-closed gate is on tool advertisement, not on the tier default.
- **Two caches keyed differently**: `catalogCache`/`resolvedAccessCache` are keyed on **lowercased** tenant id; always lowercase before lookups.
- Caches hang off `globalThis` deliberately — `instrumentation.ts` and route modules are separate module instances under Next.js.
- **`get_metrics_digest` returns ALDC's OWN business actuals** (AR aging, P&L, utilisation, pipeline) — *not* client/Navira data. The home-page "metrics digest" pill sends the literal prompt `"Give me today's metrics digest."`, which is the exact prompt that reproduced [[ALDC-739]].
- The local clone drifts fast (the repo went from PR #24 to PR #167 in a few weeks) — **always `git fetch` before reviewing**.

## See Also

- [[ALDC-739]]
- [[zeus-memory]]
- [[Eclipse]]
- [[GEP]]
- [[concept-gep-data]] — the other app reading the same Eclipse dataset
- [[core_api]]
- [[claude_code_enhanced]]
