---
tags: [workflow, navira, credentials, briefing, meeting-prep]
aliases: [Navira Access Briefing, Marketing Dashboard Access]
sources: [navira-credentials-access]
created: 2026-04-28
updated: 2026-04-28
---

# Navira — API Access Briefing

**Purpose:** Combined access requirements for the Navira integration, organized by roadmap phase. Merges the EI lead's marketing dashboard access review with ALDC engineering's full credential audit.

**Use:** Reference for client meetings. Clearly separates what ALDC already has, what Navira must provide, and what ALDC must resolve internally.

> **Key principle:** Do not ask Navira for credentials or access that ALDC already has. Several platforms have active production integrations. Asking for these undermines credibility and wastes meeting time.

---

## Phase 1A — Marketing Ad Platforms (Priority 1)

### Google Ads

**ALDC status:** No working Google Ads API integration exists for any client. ALDC is setting up from scratch.

| Item | Status | Action |
|---|---|---|
| Navira MCC Account ID | **Already provided** — `728-582-8945` | Justin Shuster emailed Lori Beck on 2026-04-15 with linking instructions. **Do not re-ask.** |
| MCC admin contact | **Already have** | Justin Shuster (jshuster@navira.io) |
| ALDC Manager Account | **In progress** — Paul Russell creating | ALDC internal — no client action |
| Developer token | **In progress** — Paul applying after MCC link | ALDC internal — ~1–2 week Google approval. No client action |
| OAuth app + refresh token | Not yet started | ALDC internal — no client action |

**Ask Navira:**
1. Are Amazon-focused and D2C campaigns in the same MCC account, or managed separately?
2. List of all Google Ads account IDs under the MCC that should be included in reporting

> **Correction from EI lead's list:** The EI lead listed "MCC ID, developer token, OAuth client credentials" as needed from Navira. The MCC ID was already provided April 15. The developer token and OAuth credentials are ALDC-side setup — Navira does not create or provide these.

---

### Amazon Advertising API (PPC)

**ALDC status:** Production integration **already live** for Navira US. Active LWA refresh token, centralized ALDC OAuth app, 857-line connector supporting SP/SB/SD/STV/DSP campaigns.

| Item                   | Status                                | Action                                  |
| ---------------------- | ------------------------------------- | --------------------------------------- |
| US PPC access          | **Have** — in active production       | Do not ask for any US credentials       |
| LWA client credentials | **Have** — centralized ALDC OAuth app | Do not ask — we already have these      |
| UK/CA access           | **Unknown** — investigating           | ALDC testing auto-discovery first (I-4) |

**Ask Navira:**
1. Does Navira run PPC campaigns in UK and/or CA marketplaces?
2. If yes — are UK/CA under the same Amazon Advertising account as US, or separate accounts?

> **Correction from EI lead's list:** The EI lead listed "API profile IDs (US/UK/CA), LWA client credentials" as needed. We already have US access in production and LWA credentials. Asking for these signals we don't understand our own infrastructure. Only UK/CA confirmation is needed, and even that may be auto-discoverable via API.

---

### Meta (Facebook) Ads

**ALDC status:** Production connector exists (530+ lines). ALDC Facebook App (`812919267215628`) with app_secret is active. Navira-specific tokens not yet provisioned.

| Item | Status | Action |
|---|---|---|
| ALDC Facebook App | **Have** — App ID `812919267215628` | No client action — Navira grants our existing app access |
| Production connector | **Have** — `facebook_business.py` | No client action |
| Navira Business Manager ID | **Need from Navira** | |
| Ad account IDs | **Need from Navira** | |
| System user token or OAuth | **Need from Navira** | |

**Ask Navira:**
1. Business Manager ID
2. All ad account IDs to include (format: `act_xxxxxxxxx`)
3. Is there an existing system user with a long-lived token? (Preferred for production — doesn't expire like personal tokens)
4. Name/email of the Business Manager admin who can create a system user and grant ALDC's app access

> **Note:** This aligns with the EI lead's list. The framing matters — Navira grants access to ALDC's existing app, they don't need to create an app or provide app credentials.

---

## Phase 1B — Marketing Social & Emerging (Priority 1)

### TikTok for Business

**ALDC status:** No TikTok connector, credentials, or infrastructure exists for any client. Net-new build.

**Ask Navira:**
1. Is Navira active on TikTok Shop (selling products directly)?
2. What does "Creator Connections" refer to? (TikTok Creator Marketplace / separate influencer platform / internal tracking?)
3. TikTok Business Center ID
4. Name/email of the Business Center admin who can authorize API access

> **Aligns with EI lead's list.** She had "Business Center ID, app credentials" — add the Creator Connections clarification and TikTok Shops API question to avoid wasted effort.

---

### Email Marketing Platform

> **Missing from EI lead's list.** This feeds Dashboard D7 (Email & Owned Channels) — a marketing dashboard. Should be included in a "Marketing Dashboard Update" meeting.

**ALDC status:** No email marketing connector exists for any client. Blocked until platform identified.

**Ask Navira:**
1. Which email marketing platform does Navira use? (Klaviyo, Mailchimp, HubSpot, Constant Contact, ActiveCampaign, other?)
2. What metrics matter? (sends, opens, clicks, revenue attributed?)
3. Does email revenue attribution tie back to Shopify/Amazon orders?
4. Name/email of the platform admin who can generate API credentials

---

### Target+

> **Missing from EI lead's list.** Feeds Dashboard D8 (Marketplace Expansion). Lower priority but worth a quick identification question if time allows.

**ALDC status:** No Target+ infrastructure. Blocked until seller status confirmed.

**Ask Navira:**
1. Is Navira an active Target+ marketplace seller?
2. If yes — how is data currently accessed? (Partner Portal, API, SFTP/EDI, third-party tool?)

---

## Phase 1C — Sales: Agency Customers (Priority 1)

### Amazon SP-API (Agency Multi-Tenant)

**ALDC status:** Production SP-API integration **already live** for Navira's own Seller Central account (1,258-line connector, 19 marketplaces). Agency multi-tenant model requires additional investigation by ALDC before asking Navira to act.

| Item | Status | Action |
|---|---|---|
| Navira's own SP-API access | **Have** — active production (partner `A3VJEVLAWT2I1E`) | Do not ask for any credentials for Navira's own account |
| LWA app credentials | **Have** | Do not ask — we already have these |
| Agency (multi-tenant) access | **ALDC investigating** | ALDC must determine if existing private app can be upgraded to public, or if a new app registration is needed (I-1) |

**Ask Navira:**
1. How many agency customer accounts need to be connected at launch? At 12 months?
2. Will agency customers OAuth into a Navira-registered app, or provide their own tokens?

**Do NOT ask yet:**
- SP-API app registration details — ALDC must resolve the private→public upgrade path first (investigation I-1). Premature asks here will confuse the client about what's needed.

> **Correction from EI lead's list:** She listed "SP-API developer registration, LWA app credentials" as needed. We already have LWA credentials and an active SP-API app for Navira's own account. The agency model is a specific extension that requires ALDC-side investigation before involving the client.

---

## Phase 2 — Inventory (Priority 2)

### Sellercloud (Inventory Extension)

**ALDC status:** Three active connections for Navira's Sellercloud account (`da8904db`). Sales integration is in production. Inventory endpoint permissions are being tested by ALDC (investigation I-2).

**Ask Navira (low priority — only if time):**
1. How many warehouse locations does Navira have in Sellercloud?

**Do NOT ask yet:**
- API credentials or permissions — ALDC is testing existing credentials against inventory endpoints first. If permissions are insufficient, we'll follow up with a specific ask.

---

### Navira Purchasing System

**ALDC status:** System type completely unknown. Need basic identification.

**Ask Navira (if time allows):**
1. What purchasing/procurement system does Navira use? (ERP module, standalone software, custom app, spreadsheet?)
2. Does it have an API?
3. Name/email of the system owner

---

## Phase 3 — Competitor Intelligence (Priority 3)

### SmartScout

**ALDC status:** No SmartScout infrastructure.

**Ask Navira (only if time — lower priority):**
1. What SmartScout subscription tier? (Essentials, Business, Enterprise)
2. Does the plan include API access, or export-only?

---

## Phase 4 — Unstructured Data (Priority 4)

### Email, Documents & Meeting Notes

**ALDC status:** Azure AD infrastructure reusable for M365 Graph API. No connector built yet.

**Ask Navira (only if time — lowest priority):**
1. What productivity suite does Navira use? (Microsoft 365, Google Workspace, hybrid?)
2. Where are documents stored? (SharePoint, OneDrive, Google Drive?)

---

## Summary: What NOT to Ask Navira

These items are resolved or ALDC-internal. Asking for them wastes meeting time or undermines credibility.

| Do Not Ask For | Reason |
|---|---|
| Google Ads MCC Account ID | Already provided (`728-582-8945`) by Justin Shuster on 2026-04-15 |
| Google Ads developer token | ALDC applies for this via our own Manager Account — Navira doesn't create it |
| Google Ads OAuth client credentials | ALDC creates these in Google Cloud Console — Navira doesn't provide them |
| Amazon Advertising API LWA credentials | Already in production for Navira US |
| Amazon Advertising API US profile IDs | Already in production |
| Amazon SP-API LWA app credentials | Already in production for Navira's own account |
| SP-API developer registration (agency) | ALDC must investigate upgrade path first (I-1) — premature to ask |
| Sellercloud API credentials | Already have active REST + SQL + CSV connections |
| Any "app credentials" for Meta | ALDC has the Facebook App — Navira grants access, not credentials |

## Summary: Priority Ask List

If the meeting is time-limited, these are the highest-value questions in priority order:

1. **Meta/Facebook:** Business Manager ID + ad account IDs + system user token + BM admin contact
2. **Amazon Ads UK/CA:** Do you run PPC in UK and/or CA?
3. **Google Ads:** Are Amazon and D2C campaigns in the same MCC or separate?
4. **TikTok:** Active on TikTok Shop? What is "Creator Connections"? Business Center ID?
5. **Email Marketing:** Which platform? (Klaviyo, Mailchimp, HubSpot?)
6. **SP-API Agency:** How many agency customers at launch?

## See Also

- [[navira-credentials-access]] — full credential audit with investigation items and detailed per-platform notes
- [[navira/README|Navira Roadmap]] — phase definitions and priority order
- [[navira-dashboard-recommendations]] — which dashboards each platform feeds
