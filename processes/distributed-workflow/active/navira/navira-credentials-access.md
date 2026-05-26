---
tags: [workflow, navira, credentials, auth, questionnaire]
aliases: [Navira Credentials, Navira Auth Questionnaire]
sources: [eclipse_exp/frontend/public/navira/navira-auth-questionnaire.html]
created: 2026-04-27
updated: 2026-05-25
audited: 2026-04-28
---

# Navira — Access & Credentials Tracker

Cross-cutting prerequisite for all phases. Tracks API credential status across all 12+ platforms in the Navira integration.

**Source:** Interactive questionnaire at `eclipse_exp/frontend/public/navira/navira-auth-questionnaire.html` (46 questions, auto-saves to browser localStorage, has JSON export + clipboard copy). Prepared April 9, 2026.

## Client Communications Log

Credential-related communications from Navira. Newest first.

| Date | From | To | Subject | Key Details |
|---|---|---|---|---|
| 2026-05-25 | Paul Russell (paul.russell@aldc.io) | — (system) | Windsor auto-link-generation deployed | Windsor API integrated into `func-aldc-cred`. `GET /api/windsor/check-status` and `POST /api/windsor/generate-link` endpoints live. Client credential dashboard now generates fresh Windsor OAuth links at click time — eliminates expired-link problem. Google Ads + Meta/Facebook supported. `WINDSOR_API_KEY` set on Function App. |
| 2026-05-08 | Paul Russell (paul.russell@aldc.io) | Lori Beck (lori.beck@aldc.io) | GP-221 UK PPC OAuth complete | UK token exchange completed. Profile ID **1236242149887729** (GBP, Europe/London). 12 EU profiles returned (UK, DE, FR, IT, ES, NL, SE, PL, IE, BE, AE, SA). No further Navira action needed. ALDC to update pipeline config + validate data flow. |
| 2026-05-07 | Justin Shuster (jshuster@navira.io) | Paul Russell (paul.russell@aldc.io) | UK credentials call scheduling | Live call scheduled **Fri 2026-05-08, 12:30–1:30 PM EST** (9:30–10:30 AM PST) with Justin + third party to complete UK Amazon Ads OAuth code exchange in real time. Codes expire in ~5 min — live call ensures immediate exchange. |
| 2026-04-30 | Paul Russell (paul.russell@aldc.io) | Lori Beck (via Jira GP-238, GP-239) | Windsor auth links for Google Ads + Facebook Ads | Decision: use Windsor.ai (ALDC existing Plus account, $0 incremental cost). Auth links generated for Navira to click: Google Ads (`google_ads`) + Facebook Ads (`facebook`). Posted to GP-238 and GP-239. Pending Navira authorization. |
| 2026-04-15 | Justin Shuster (jshuster@navira.io) | Lori Beck (lori.beck@aldc.io), CC: Heather Tabor (htabor@navira.io) | Google Ads - Requesting Access to our account | Navira MCC ID: **`728-582-8945`**. Step-by-step linking instructions: Google Ads Manager → Accounts → Link Existing Account → enter `728-582-8945` → Send Request → Justin approves. Grants access to main account + all linked children accounts. **Status: Superseded by Windsor approach (2026-04-30) — MCC linking no longer needed.** |

## Authentication Summary

| Platform | Auth Method | Required IDs | Status | Phase |
|---|---|---|---|---|
| **Google Ads** | Windsor.ai OAuth | MCC Account ID(s) — Amazon vs D2C split TBD | **Auto-generated links** (2026-05-25). Windsor API integration deployed to `func-aldc-cred` — links generated at click time via portal, never expire before use. Previous static links expired before Justin's ads person could click. Pending Navira authorization. ALDC field verification needed post-auth. | 1A |
| **Amazon Advertising API** | LWA OAuth | US/UK/CA profile IDs | **All 3 marketplaces active.** UK complete (2026-05-08) — Profile ID 1236242149887729, GBP, 12 EU profiles. US active (708K rows). CA confirmed active (68K rows, 2026-05-08). | 1A |
| **Meta (Facebook) Ads** | Windsor.ai OAuth | Business Manager ID, Ad Account ID(s) | **Auto-generated links** (2026-05-25). Windsor API integration deployed — links generated at click time. Pending Navira authorization. ALDC field verification needed post-auth. | 1A |
| **TikTok for Business** | OAuth 2.0 | Business Center ID | Net New — no ALDC connector or credentials exist | 1B |
| **Email Marketing Platform** | API Key or OAuth | Platform TBD (Klaviyo/Mailchimp/HubSpot?) | TBD — platform not yet identified | 1B |
| **Target+** | API or SFTP | Seller account | TBD — platform not yet confirmed | 1B |
| **Amazon SP-API (Agency)** | LWA OAuth per customer | App registration + per-customer OAuth grants | Partial — ALDC has SP-API connector + Navira's own credentials; agency multi-tenant needs app registration | 1C |
| **Sellercloud** | API Key/Token | Confirm inventory endpoint coverage | Have — REST + SQL connections active for GEP account `da8904db`; confirm inventory endpoints | 2 |
| **Navira Purchasing System** | TBD | System type unknown | TBD — system type unknown | 2 |
| **SmartScout** | API Key or Export | Subscription tier determines API access | TBD | 3 |
| **Email/Calendar (M365 or Google)** | OAuth (Graph or Gmail) | Tenant/workspace ID | TBD — ALDC has Azure AD infra for Graph API | 4 |
| **Document Storage** | OAuth (SharePoint/OneDrive/GDrive) | Site/drive IDs | TBD | 4 |

## Client Access Request — What to Ask Navira

Organized by action required. Goal: ask Navira only for what we genuinely need, give clear direction, and don't ask questions for access we already have.

### Already Have — No Client Action Needed

These platforms have active, production credentials. Navira does **not** need to provide anything.

| Platform | What ALDC Has | Phase |
|---|---|---|
| **Amazon Ads (US)** | Production connector + active LWA refresh token (account `da8904db`). Centralized ALDC OAuth app. Long-lived token, no expiry. | 1A |
| **Amazon SP-API (Navira's own account)** | Production connector + active LWA credentials (partner `A3VJEVLAWT2I1E`). 19-marketplace support. In active production use. | 1C |
| **Sellercloud (Sales)** | REST API (team `globalecomp`, user `support@aldc.io`) + Direct SQL (VPN-gated) + CSV supplement. All active for GEP account `da8904db`. | 2 |

### Ask Navira — Specific Items Required

Items grouped by phase priority. Each item has a clear ask and context for why we need it.

#### Phase 1A — Marketing Ad Platforms

**Google Ads** — Navira has already provided MCC ID (`728-582-8945`) and linking instructions (Justin Shuster, 2026-04-15). ALDC MCC linking + developer token application in progress.
1. ~~MCC Account ID~~ — **Already provided:** `728-582-8945` (Justin Shuster → Lori Beck, 2026-04-15)
2. Are Amazon-focused and D2C campaigns in the same MCC or separate accounts?
3. List all Google Ads account IDs under the MCC to include
4. ~~MCC admin for OAuth access~~ — **Already have contact:** Justin Shuster (jshuster@navira.io)

**Meta (Facebook) Ads** — ALDC has Facebook App (`812919267215628`) + production connector ready. Need Navira's Business Manager details.
1. Business Manager ID
2. All ad account IDs to include (format: `act_xxxxxxxxx`)
3. Is there an existing system user with a long-lived token? (Preferred over personal tokens for automated access — doesn't expire like personal tokens)
4. Name/email of the Business Manager admin who can create a system user and grant ALDC's app ad account access

**Amazon Ads (UK/CA extension)** — All three marketplaces confirmed active (2026-05-08). US (708K rows) + CA (68K rows) in production. UK OAuth completed 2026-05-08.
1. ~~Does Navira run PPC campaigns in UK and/or CA?~~ **RESOLVED 2026-05-08:** Yes — all three (US, UK, CA) confirmed active.
2. ~~Are UK/CA under the same Amazon Advertising account as US, or separate accounts?~~ Same account — UK profile returned from same LWA token on 2026-05-08 call.
3. ~~Profile IDs for UK/CA (or confirm ALDC can retrieve them via API — our connector auto-enumerates)~~ **RESOLVED:** UK Profile ID 1236242149887729. CA already in production.

#### Phase 1B — Social & Emerging

**TikTok for Business** — ALDC has no existing TikTok infrastructure. Net-new build.
1. Is Navira active on TikTok Shop (selling products directly)?
2. What does "Creator Connections" refer to? (TikTok Creator Marketplace, a separate influencer platform, or internal tracking?)
3. Business Center ID
4. Name/email of the TikTok Business Center admin who can authorize API access

**Email Marketing** — Blocked until platform identified. ALDC has no connector for any email marketing platform.
1. Which platform does Navira use? (Klaviyo, Mailchimp, HubSpot, Constant Contact, ActiveCampaign, other?)
2. What metrics matter? (sends, opens, clicks, revenue attributed?)
3. Does email revenue tie back to Shopify/Amazon orders?
4. Name/email of the platform admin who can generate API credentials

**Target+** — Blocked until confirmed. ALDC has no Target+ infrastructure.
1. Is Navira an active Target+ marketplace seller?
2. How is data currently accessed? (Partner Portal download, Target+ API, SFTP/EDI, third-party tool?)
3. What data is needed? (Sales/orders, advertising/promotion, inventory, settlements?)

#### Phase 1C — Agency Customers

**Amazon SP-API (Agency model)** — See caveat below. Multi-tenant access for agency customers requires either upgrading the existing SP-API app or registering a new public app (Amazon approval, 2–4 weeks).
1. How many agency customer accounts at launch? At 12 months?
2. Which SP-API data scopes are needed? (Orders, Reports, FBA Inventory, Finances/settlements, Product Listings)
3. Will agency customers OAuth into a Navira-registered app, or provide their own tokens?

> **Caveat — SP-API App Registration:** The existing SP-API app (partner `A3VJEVLAWT2I1E`) is registered as a **private/self-authorized app** — it can only access Navira's own Seller Central data. To access agency customers' data, the app must support **OAuth authorization from third-party sellers**, which means either:
>
> - **Option A:** Convert the existing private app to a **public app** (if Amazon allows this upgrade path), or
> - **Option B:** Register a **new public app** from scratch
>
> Both options require Amazon approval (2–4 week review). **ALDC needs to investigate which option is viable before asking Navira to act.** See "ALDC to Investigate First" section below.

#### Phase 2 — Inventory

**Sellercloud (Inventory extension)** — Existing sales credentials are active. Need to confirm inventory endpoint access.
1. How many warehouse locations does Navira have in Sellercloud?

**Navira Purchasing System** — System type unknown. Need basic identification before ALDC can design the integration.
1. What type of system? (ERP module, standalone software, custom-built, spreadsheet/manual?)
2. Does it have an API? If yes, what type? (REST, SOAP, GraphQL, database access, file export only?)
3. Name/email of the system owner or IT contact

#### Phase 3 — Competitor

**SmartScout** — ALDC has no SmartScout infrastructure.
1. What subscription tier is Navira on? (Essentials, Business, Enterprise)
2. Does the plan include API access, or export-only?
3. If API: is there an existing API key?
4. If export-only: what format and frequency?
5. Are other competitive intelligence tools in use? (Jungle Scout, Helium 10, Keepa, etc.)

#### Phase 4 — Unstructured Data

**Email & Productivity Platform** — ALDC has Azure AD infrastructure reusable for M365 Graph API.
1. What suite does Navira use? (Microsoft 365, Google Workspace, hybrid?)
2. Where are documents stored? (SharePoint, OneDrive, Google Drive, local server, Dropbox?)
3. How are meetings conducted — are transcripts available? (Teams, Zoom, Google Meet, manual notes?)
4. If M365: Azure AD Tenant ID + global admin contact
5. If Google Workspace: domain + super admin contact
6. Any legal/HR/compliance restrictions on indexing employee email or documents?

### ALDC to Investigate First — Don't Ask the Client Yet

Items ALDC must resolve internally before involving Navira. Prevents asking unnecessary or premature questions.

| # | Item | Investigation | Outcome Determines |
|---|---|---|---|
| I-1 | ~~**SP-API private → public app upgrade**~~ | **RESOLVED 2026-05-08:** Amazon does not support converting private → public. New public app registration required via Solution Provider Portal (SPP) at developer.amazonservices.com/solution-provider-portal. Identity verification ~20 min, approval ~1–2 weeks. SPP replaced Seller Central for developer management as of Aug 31, 2025. ALDC to register now — no Navira action needed until OAuth consent flow ready. | N/A — new app registration is the path; ~1–2 week approval (not 2–4 weeks) |
| I-2 | **Sellercloud inventory endpoint permissions** | Test existing REST API credentials (`support@aldc.io` on team `globalecomp`) against inventory endpoints (Summary, Warehouse, FBA). Check rate limits. | Whether to ask Navira for a permissions upgrade or separate API user (Phase 2) |
| I-3 | **Sellercloud VPN dependency for Prefect** | Evaluate whether ACI work pools can be configured with VPN connectivity to `10.13.0.113`, or whether REST-only path is sufficient for inventory. | Whether VPN access is a blocker or can be sidestepped |
| I-4 | ~~**Amazon Ads UK/CA profile auto-discovery**~~ | **RESOLVED 2026-05-08:** UK profile exchanged on live call — Profile ID 1236242149887729 (GBP, Europe/London). CA confirmed active in production (68K rows). All 3 marketplaces confirmed. | N/A — all marketplaces resolved |
| I-5 | ~~**Google Ads — full setup required**~~ | **RESOLVED 2026-04-30:** Using Windsor.ai instead of direct API. No Manager Account, developer token, or OAuth app needed. Windsor auth link sent to Navira via GP-238. Fallback to direct API only if Windsor field verification fails. | N/A — Windsor eliminates the 1–2 week developer token lead time |
| I-6 | ~~**Facebook App token status**~~ | **RESOLVED 2026-04-30:** Using Windsor.ai instead of direct API. No ALDC Facebook App or token provisioning needed. Windsor auth link sent to Navira via GP-239. Eliminates 60-day token refresh burden. Fallback to direct API only if Windsor field verification fails. | N/A — Windsor handles token lifecycle |

### Pre-Filled Questionnaire

A JSON file with all known ALDC-side answers is available for import into the interactive questionnaire:

**File:** `vault/navira-questionnaire-prefill.json`

**Usage:**
1. Open `eclipse_exp/frontend/public/navira/navira-auth-questionnaire.html` in a browser
2. Click the **Import** button in the save bar
3. Select the JSON file — page reloads with pre-filled fields
4. All `[NAVIRA TO PROVIDE]` markers indicate where client input is still needed

## Credential Audit Results (2026-04-27)

Audit of 4 sources: (A) GEP Eclipse connection configs (`clients/GEP/eclipse/connections/`), (B) Connector repo implementations (`connector/connector/connectors/`), (C) Prefect account registry (`connector/connector/account_registry.py`), (D) Wiki connector specs + vault (`entities/tools/connectors/`, `vault/infra-credentials.md`).

### Summary Table

| Platform | ALDC Has | Reusable for Navira? | Navira Must Provide | ALDC Action Required |
|---|---|---|---|---|
| **Google Ads** | **Windsor.ai** (ALDC Plus account, $0 incremental). Auth link sent 2026-04-30 (GP-238). Fusion92 Google Ads (23 accounts) already proven through Windsor. | Yes — via Windsor OAuth link | ~~MCC Account ID~~ **already provided** (`728-582-8945`, 2026-04-15); clarify Amazon vs D2C split; **click Windsor auth link** | Field verification post-auth (campaign.id, all_conversions, conversion_action_name, currency_code); configure Snowflake destination task |
| **Amazon Ads API** | Production connector `amazon_ads.py` (857 lines, SP/SB/SD/STV/DSP); GEP connection `amazon_ads.json` with active refresh token (account `da8904db`); centralized ALDC OAuth app (Client ID `amzn1...3d878`) | Yes — **already in production for Navira US**; same OAuth app works for multi-profile | UK/CA profile IDs (if separate profiles exist); confirm multi-region advertising setup | Migrate connector to Prefect; extend to UK/CA profiles (multi-profile already supported); create Prefect block from existing connection |
| **Meta (Facebook) Ads** | **Windsor.ai** (ALDC Plus account, $0 incremental). Auth link sent 2026-04-30 (GP-239). Fusion92 Meta Ads already proven through Windsor (`ad_insights_windsor.json`). Direct API connector `facebook_business.py` (553 lines) exists as fallback but has no token refresh logic and is generating failure alerts in observability-dev. | Yes — via Windsor OAuth link | **Click Windsor auth link**; BM ID + ad account IDs still useful for ALDC records | Field verification post-auth (campaign/ad set/ad breakdowns, spend, conversions, ROAS, custom events); configure Snowflake destination task |
| **TikTok for Business** | Nothing — no connector, no connection configs, no wiki spec for any client | No — net-new build required | Business Center ID; TikTok Shops API status; clarify "Creator Connections" (TikTok feature or separate platform?); OAuth consent | Register ALDC TikTok for Business developer app; build connector from scratch; implement OAuth flow |
| **Email Marketing** | Nothing — no Klaviyo/Mailchimp/HubSpot connectors | No — blocked until platform identified | Which platform (Klaviyo, Mailchimp, HubSpot, etc.); API key or admin OAuth access; what metrics matter | Build connector once platform identified |
| **Target+** | Nothing | No — blocked until confirmed | Confirm Target+ marketplace seller status; API vs manual feed availability; account credentials | Evaluate API/SFTP access; build connector or file ingestion |
| **Amazon SP-API (Agency)** | Production connector `amazon_sellercentral.py` (1258 lines, orders/reports/inventory/fulfillment); GEP connection `amazon_seller_central.json` with active LWA credentials (partner `A3VJEVLAWT2I1E`); multi-marketplace support built in (19 marketplaces) | Yes for Navira's own account (**already live**); agency multi-tenant requires public app status — **investigate first** (I-1): upgrade existing app or register new one? | Per-customer OAuth grants; number of agency customers at launch | **First:** resolve I-1 (private→public app path). Then: migrate connector to Prefect; implement multi-tenant credential management in Prefect blocks |
| **Sellercloud** | GEP connections active: REST (`globalecomp` team, user `support@aldc.io`), SQL (direct to `10.13.0.113` via VPN, user `GEP_Chris.Verde`), CSV supplement on Nextcloud; no standalone connector class in `connector/connectors/` (likely uses SQL/REST base connectors) | Yes — **these ARE Navira's credentials** (GEP = Navira) | Confirm inventory endpoint coverage (Summary, Warehouse, FBA?); rate limits for inventory vs sales; whether separate API user needed | Migrate to Prefect (Phase 0 priority — first migration candidate); verify inventory endpoints work with existing REST/SQL credentials; VPN dependency must be handled in ACI work pool networking |
| **Navira Purchasing** | Nothing — system type unknown | N/A | System type (ERP, custom app, spreadsheet?); API availability; access credentials | Evaluate once system identified |
| **SmartScout** | Nothing | N/A | Subscription tier (API vs export-only); API key if available; export format/frequency | Evaluate once tier confirmed |
| **Email/Calendar** | ALDC Azure AD infrastructure (tenant `e2bae64b...`); App Registration experience; Microsoft Graph API pattern | Partial — Azure AD infra reusable for M365 Graph API; different approach for Google Workspace | Tenant/workspace ID; OAuth consent; admin access for Graph API permissions | Create App Registration for Navira (or reuse ALDC multi-tenant); implement Graph/Gmail connector |
| **Document Storage** | Nextcloud infrastructure (cloud.aldc.io); Azure blob storage pipeline | No — Navira likely uses SharePoint/OneDrive/GDrive, not Nextcloud | Which platform (SharePoint, OneDrive, GDrive); site/drive IDs; OAuth consent | Build SharePoint/OneDrive connector (Graph API) or GDrive connector |

### Per-Platform Detail Notes

#### Google Ads — MCC provided, ALDC must build from scratch

> **Correction (2026-04-28):** The developer token in `vault/infra-credentials.md` (`oMW0AfGN4JsIX7cJxLzX_A`) is **unverified and likely not usable for Navira**. It was extracted from Confluence sample code (TECH/1145143297) during a batch wiki ingest. Fusion92's Google Ads integration used **Windsor.ai** as an aggregation layer (`windsorai_v1` connector), not the Google Ads API directly. No Google Ads connection JSON exists for GEP/Navira, and no `google_ads.py` connector exists in the connector repo. ALDC has the documented *setup pattern* ([[google-ads]]) but does not have working Google Ads API credentials for any client.

**Navira MCC already provided:** Justin Shuster (jshuster@navira.io) emailed Lori Beck on 2026-04-15 with MCC linking instructions and Navira's main account ID: **`728-582-8945`**. He described the Manager Account → "Link Existing Account" flow and noted that linking would grant access to the main account plus all linked children accounts.

**Critical path (ALDC-side, no further client action needed for linking):**

**Step 0 — Create ALDC Google Ads Manager Account** (ALDC does not currently have one)
1. Go to `ads.google.com/home/tools/manager-accounts/`
2. Sign in with Paul's personal Gmail (interim — ALDC has no company Google account; `support@aldc.io` M365 password not currently available)
3. Click **Create a manager account**
4. Account name: "Analytic Labs"
5. Purpose: select **Manage other people's accounts**
6. Set country, timezone, currency
7. Note the new Manager Account ID (format: `xxx-xxx-xxxx`) — save to Dashlane

> **Pending transfer:** Manager Account is temporarily under Paul's personal Gmail. Once `support@aldc.io` M365 access is restored: create a Google account for that email → add as Admin on the Manager Account → promote to Owner → remove personal Gmail. Transfer is instant, no approval needed.

**Step 1 — Link Navira's MCC** (from Justin Shuster's email, 2026-04-15)
1. From the new ALDC Manager Account at `ads.google.com`, click **Accounts** in the left sidebar
2. Click the blue **+** button → select **Link existing account**
3. Enter Navira's account number: **`728-582-8945`**
4. Click **Send request**
5. Justin Shuster (jshuster@navira.io) approves on Navira's side
6. Once approved, ALDC has access to Navira's main account and all linked children accounts

**Step 2 — Apply for Developer Token**
1. In the ALDC Manager Account: **Tools & Settings** → **API Center**
2. Apply for a developer token — select **Basic Access**
3. Requires a brief description of intended API use (automated ad performance reporting for client analytics)
4. Google reviews — allow ~1–2 weeks for Basic Access approval
5. The token is issued at the Manager Account level and works for any MCC linked to it

**Step 3 — Create OAuth App (Google Cloud Console)**
1. Go to `console.cloud.google.com` → create a new project (e.g. "ALDC Google Ads")
2. Search "Google Ads API" → **Enable**
3. **APIs & Services** → **OAuth consent screen** → select **External** → configure app name + support email
4. **APIs & Services** → **Credentials** → **Create Credentials** → **OAuth Client ID** → type: **Desktop Application**
5. Set `http://127.0.0.1` as Authorized JavaScript Origins
6. Save — note the **Client ID** and **Client Secret**

**Step 4 — Generate OAuth Refresh Token**
1. Go to `developers.google.com/oauthplayground`
2. Click the gear icon → check **Use your own OAuth credentials**
3. Enter the Client ID and Client Secret from Step 3
4. In the left panel, find **Google Ads API v17** → select `https://www.googleapis.com/auth/adwords`
5. Click **Authorize APIs** → sign in with the ALDC account that owns the Manager Account → grant access
6. Click **Exchange authorization code for tokens**
7. Copy the **Refresh Token** — this is the long-lived credential for API access

**Step 5 — Build Prefect Connector**
- Build `google_ads.py` from scratch (no existing connector in `connector/connectors/`)
- The GAQL query pattern in [[navira-data-dictionary-phase1a]] (cost_micros, conversions as DOUBLE, campaign.id as primary key) informs the implementation
- Store credentials in Prefect SecretStr blocks

**Remaining question for Navira:** Are Amazon-focused and D2C campaigns in the same MCC or separate accounts? This determines whether one or two connections are needed.

#### Amazon Ads — Already in production, extend to UK/CA

The `amazon_ads.py` connector (857 lines) is production-grade with full support for SP, SB, SD, Sponsored Television, and DSP. It uses a centralized ALDC OAuth app (Client ID hardcoded at `amazon_ads.py:337`). The GEP Eclipse connection `amazon_ads.json` has an active LWA refresh token for Navira's account (`da8904db`).

The connector already handles multi-profile enumeration (line 405–423), so UK/CA support is mostly a matter of confirming that Navira has advertising profiles in those regions. The connector retrieves all profiles for the authorized account and filters by account type.

**Token status:** LWA refresh tokens for Amazon Ads are long-lived (no expiry) — the existing GEP token should still be valid.

#### Meta / Facebook Ads — ALDC app exists, Navira-specific tokens needed

The `facebook_business.py` connector (530+ lines) handles Campaign and AdSet levels with insights. It uses the `facebook_business` Python SDK. ALDC maintains a Facebook App (`812919267215628`); the app_secret is stored in existing connection configs.

The ALDC support@aldc.io account has a Facebook developer profile and a sandbox access token recorded in `vault/infra-credentials.md`.

**60-day token expiry:** Long-lived Facebook access tokens expire ~60 days. See [[connector-token-refresh]] for the refresh runbook. The Prefect implementation must include automated token refresh logic. Navira will need its own long-lived access token generated after providing Business Manager ID and ad account access.

#### Amazon SP-API — Production for Navira, agency model needs investigation

`amazon_sellercentral.py` (1258 lines) is ALDC's most comprehensive connector — supports orders, reports (21+ report types), inventory, fulfillment (inbound/outbound), seller participation, and catalog classification. Multi-marketplace support covers 19 regions. The GEP connection (`amazon_seller_central.json`) has active LWA credentials (partner ID `A3VJEVLAWT2I1E`, client_identifier `amzn1.application-oa2-client.4bd6969a...`).

> **Caveat — Private vs Public App (Investigation I-1):**
> The existing app is registered as a **private/self-authorized app** — it can only access Navira's own Seller Central data. For the agency model (Phase 1C), where Navira needs to pull data from *agency customers'* Seller Central accounts, the app must support **OAuth authorization from third-party sellers**. This requires **public app** status.
>
> Amazon SP-API distinguishes:
> - **Private app** — self-authorized, accesses only the owning seller's data. No Amazon approval needed beyond initial registration.
> - **Public app** — authorized by other sellers via OAuth. Requires Amazon review (2–4 weeks) and may need to be listed in the Amazon Marketplace Appstore.
>
> **Open question:** Can the existing private app be **upgraded** to public, or must a new app be registered? ALDC must check Amazon's SP-API documentation before asking Navira to take any action. This is tracked as investigation I-1 in the "ALDC to Investigate First" table above.

Per-customer OAuth grants then authorize the (public) app for each agency customer's data.

#### Sellercloud — Fully credentialed, VPN dependency is the risk

Three active connections exist for GEP/Navira account `da8904db`:
- **REST API** (`sellercloud_rest.json`): team `globalecomp`, authenticated as `support@aldc.io`
- **Direct SQL** (`sellercloud_sql.json`): server `10.13.0.113`, user `GEP_Chris.Verde` — requires VPN agent `gep-sellercloudvpn`
- **CSV supplement** (`sellercloud_channel_map_csv.json`): Nextcloud path

The VPN dependency for SQL access is a significant concern for Prefect migration — ACI workers would need VPN connectivity. The REST API path is preferred for Prefect.

**Note:** No standalone `sellercloud.py` connector exists in `connector/connectors/`. The legacy Sellercloud integration likely uses the generic SQL connector for the SQL path and REST base connector for the API path. Phase 0 must create a typed Sellercloud Prefect connector.

#### Prefect Block Infrastructure (Source C)

`account_registry.py` currently only registers `ALDC_QA` (line 58). Adding Navira requires either:
- Manual code change to add `NAVIRA_PROD` (current pattern)
- Phase 0 Gap G3 — auto-discover accounts by scanning `connector/accounts/*/account.py`

Snowflake credential blocks are auto-created with `PLACEHOLDER` passwords (line 38) — actual passwords must be manually set in Prefect UI after deployment.

### Credentials to Extract to Vault

The following credentials are in plaintext in the `clients/GEP/eclipse/connections/` JSON files (committed to the `clients` git repo). Per wiki rule #2, credential values should be referenced by vault placeholder, not stored inline. These should be verified as gitignored — if not, they need extraction:

- `amazon_ads.json` → LWA refresh token
- `amazon_seller_central.json` → LWA refresh token, client_identifier, client_secret
- `sellercloud_rest.json` → username + password for support@aldc.io on Sellercloud
- `sellercloud_sql.json` → SQL server username + password

> **Note:** Eclipse connection JSONs are the configuration mechanism — Eclipse reads these at runtime. They cannot be replaced with vault references without changing the Eclipse runtime. The concern is whether the `clients` repo is public or has appropriate access controls. Prefect migration resolves this — Prefect Blocks use `SecretStr` fields encrypted at rest.

### Token Expiry Status

| Platform | Token Type | Expiry Model | Current Status |
|---|---|---|---|
| Amazon Ads (GEP/Navira) | LWA refresh token | Long-lived (no expiry) | Likely valid — verify with test API call |
| Amazon SP-API (GEP/Navira) | LWA refresh token | Long-lived (no expiry) | Likely valid — in active production use |
| Sellercloud REST (GEP/Navira) | Username/password | No expiry (password-based) | Active — in production use |
| Meta/Facebook (Navira) | Long-lived access token | ~60-day expiry | Not yet provisioned — Navira must provide BM ID + ad accounts first |
| Google Ads (Navira) | OAuth refresh token | Long-lived (no expiry once generated) | Not yet provisioned — MCC provided (`728-582-8945`); ALDC must link, apply for dev token, create OAuth app, then generate refresh token |

## Credential Provisioning Workflow

1. **Identify** — determine platform, auth method, and required IDs from table above
2. **Request** — send the relevant questionnaire section to Navira contact
3. **Provision** — create OAuth apps, generate tokens, record in secrets management (CC3)
4. **Test** — verify API access with a minimal query before building the connector
5. **Store** — credentials go to the centralized secrets manager per CC3 decision

## See Also

- [[navira/README|Navira Roadmap]] — master workflow hub
- [[navira-access-briefing]] — client meeting briefing: access requirements by phase, corrections from EI lead's list
- [[credential-validation-toolkit]] — API credential tester CLI (validates creds, resolves investigations I-1 through I-6)
- [[phase-1a-marketing-ad-platforms]] — first phase requiring credentials
- [[connector-development-standards]] — ALDC connector pattern (includes auth patterns)
- [[google-ads]], [[facebook-ads]], [[amazon-ads]], [[bing-ads]] — existing ALDC connector specs
- [[connector-token-refresh]] — operational token refresh runbook (Bing 90-day, Facebook 60-day)
