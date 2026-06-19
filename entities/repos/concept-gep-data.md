---
tags: [repo, gep, navira, dashboard, sku-profitability, nextjs, vercel, eclipse-api]
aliases: [concept-gep-data, eclipse-dashboard, SKU Profitability concept app]
sources: []
created: 2026-06-18
updated: 2026-06-18
---

# concept-gep-data (repo)

ALDC-built **Next.js 15 / React 19** dashboard app — an exploratory ("concept") richer SKU Profitability + AI-chat experience for [[GEP]]/Navira. Repo: `github.com/ALDC-io/concept-gep-data` (project name `eclipse-dashboard`). Local: `C:\Users\PaulRussell\repos\concept-gep-data`.

## ⚠️ Two surfaces are both called "SKU Profitability" — do not conflate

| | Live client surface | This repo |
|---|---|---|
| App | `navira-demo.analyticlabs.io` (Eclipse sidebar iframe `/application/navira-demo`) | `concept-gep-data.vercel.app` |
| Owner | **Datavize** (Marshall Johnston / Steven Deutekom) — source NOT in any ALDC repo | **ALDC** (this repo) |
| Auth | Eclipse RBAC | Supabase |
| Status | what GEP/Navira use **today** | concept / not in front of clients |

**Both point at the SAME live GEP data** (Eclipse account `da8904db`, PBI dataset `e80ffd34` = "Data Model"). So merging changes here does **NOT** change what the client sees in their Datavize sidebar. Likely intended as a future ALDC replacement for the Datavize app. This corrects the [[GP-256]]/[[GP-259]] notes that imply the only SKU Profitability frontend is the inaccessible Datavize one.

## Architecture

- **Data:** no DB client. React → `src/hooks/useMetrics.ts` → `src/lib/api-client.ts` → `/api/eclipse/request` → `src/lib/eclipse-api.ts` → `POST https://api.aldc.io/v1/dataset/request` → PBI "Data Model". Measures are hardcoded strings in `METRIC_CONFIGS` (`eclipse-api.ts`).
- **Comparisons:** previous-period + YoY computed client-side as **date-shifted parallel queries** off `'Date'[Date]` (`getPreviousPeriodDateRange`/`getYearOverYearDateRange` in `utils.ts`). The model's `Date` table exposes `Week Name`/`Month Name` etc., so a daily/weekly/monthly grain toggle is **frontend-only** (no model change) — see [[GP-263]].
- **Columns are hardcoded** in JSX (`GrossSalesDetailView.tsx`, `MetricCard.tsx`) — every new column/badge is a manual edit.

## Build / test / deploy

- `npm run dev | build | lint`. **No mock mode** — cards need live `NEXT_PUBLIC_ECLIPSE_BEARER_TOKEN` + `NEXT_PUBLIC_ECLIPSE_ACCOUNT_ID`; without them the dashboard renders a skeleton then an API error.
- Test harness added 2026-06-18 (GP-266): **vitest** + `@testing-library/react` (`npm test` → `vitest run`).
- **Deploy: Vercel.** `main` → production (`concept-gep-data.vercel.app`); branch push → **preview deploy = staging** (needs Preview-scope env vars to render real data). Rollback = Vercel **Instant Rollback** to a prior immutable deployment, or `git revert`. No in-repo CI/CD, Docker, or Azure config.
- Also has Supabase auth, LangChain/Claude chat, and Zeus Memory MCP integration.

## Related
- [[GP-266]] — inline LY/YoY badge (PR #43) · [[GP-263]] — grain toggle · [[GP-258]] — forecast
- [[GEP]] · [[Eclipse]] · [[power-bi]] · [[DV-444]] (the live navira-demo rename)
