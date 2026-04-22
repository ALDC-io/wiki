---
tags: [concept, architecture, fusion92, snowflake, data-warehouse, dios]
aliases: [Fusion92 Data Architecture, F92 Architecture]
sources: [CF92/1367212038, CF92/1367703569, CF92/1382088715]
created: 2026-04-18
updated: 2026-04-18
---

# Fusion92 Data Architecture

Data architecture decisions and implementation guidance for [[fusion92]]'s [[Snowflake]] environment and the broader data ecosystem (DIOS → DAX → DSP audience pipeline).

## Snowflake Setup — Implementation Checklist

*Source: CF92/1367212038*

### Phase 1: Environment Planning

- [ ] Determine cloud provider (Azure recommended for SSO/AD integration)
- [ ] Select edition (Standard Edition recommended for initial deployment, ~$2/credit)
- [ ] Define organization name and secure custom URL (e.g. `fusion92.snowflakecomputing.com`)
- [ ] Establish billing model (credit card initially; no prepayment required)

### Phase 2: Future State Design

Define architectural decisions informed by organizational needs:

- **Use Cases** — Document short-term and long-term analytical + transactional workloads
- **Account Structure** — Single vs. multi-account (separate accounts for logically distinct workloads: Experian data, Consumer View, PHI if needed)
- **Access Control** — Design role hierarchy; privileges granted to roles, not users
- **Data Models & Scripting** — Define data organization, transformation patterns
- **Integrations** — Document client connections and data pipelines
- **Warehouse Configuration** — Size, count, assignment to workloads
- **Cost Planning** — Monthly budget + monitoring limits

### Phase 3: Implementation

- [ ] Design role and grant structure (roles built from PUBLIC base)
- [ ] Create accounts (initial: Consumer View, Experience, Experian data accounts)
- [ ] Establish roles and users (including service accounts)
- [ ] Create warehouses, databases, and high-level securables
- [ ] Implement data integrations (cloud storage, APIs, Eclipse connectors)
- [ ] Configure monitoring and cost controls

### Phase 4: Testing & Operationalization

- [ ] Validate query performance and warehouse sizing
- [ ] Test access control and role assignments
- [ ] Implement cost monitoring and budget controls
- [ ] Establish baseline operational procedures

---

## Snowflake Architecture Decisions — September 2024

*Source: CF92/1367703569 (meeting 2024-09-06, ~44 min, attendees: ALDC + Fusion92)*

### Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Cloud Provider | **Azure** | SSO + Azure AD integration |
| Edition | **Standard** (~$2/credit) | Sufficient for initial setup; upgradeable per account |
| Billing | Credit card (no prepayment) | — |
| URL | `fusion92.snowflakecomputing.com` | Secure early |
| Access model | Role-based (roles → users; no direct user privileges) | — |

### Account Structure

Organization > Accounts > Databases. Initial accounts:
- Consumer View account
- Experience account
- Experian data account
- (Potential PHI account — defer until use case confirmed)

### Actions Assigned (2024-09-06)

| Action | Owner |
|--------|-------|
| Create Snowflake org + initial accounts | Ryan |
| Add Sean + Ryan as ORGADMIN | Ryan |
| Identify specific use cases | Ryan (coordinate with team) |
| Review initial setup, provide feedback | Sean |
| Schedule follow-up for detailed design | Both |

---

## DIOS → DAX → DSP Audience Integration

*Source: CF92/1382088715 (Confluence page is image-heavy; text notes extracted below)*

### Temporary State Flow

Manual upload activation via Viant Cleanroom:

`DIOS → Manual Upload → [[nextcloud]] → Viant Cleanroom → DAX Activation → DSP`

**Key constraints:**
- Manual upload to Viant Cleanroom does NOT require DAX IDs (confirmed capability)
- Nextcloud retention period: **90 days** (per Dave Nugent)
- File limits: **300,000 records max / 20 MB per file**
- File organization: folder by date/time of audience receipt

### Future State Flow

Streamlined automated integration (architecture diagram exists in Confluence CF92/1382088715 — image not retrievable via MCP).

**Design considerations:**
- Duplicate handling: system must handle second/third uploads of same audience OR DIOS must prevent duplicate audiences
- Data quality: explicit idempotency or duplicate detection required

### Cross-reference

The [[custom-fusion-92-audience-api|DIOS-to-DAX API]] page documents the Nextcloud folder structure (`DAX_RAW_DoNotUse` / `DAX`) and the "Process Audience" copy workflow. This page covers the upstream data flow into Nextcloud and the downstream Viant Cleanroom activation.

---

## Data Categorization Framework

*Source: CF92/1263501314 (meeting 2024-04-26)*

Dimensional model underpinning Fusion92 dashboard queries and audience segmentation.

**Client-level dimensions:** Business unit, Product/segment, Campaign

**Cross-cutting dimensions:** Channel, Platform, Objective, Location

**Data source:** All dimensions derived from the `ad_group_name` field.

**Core metrics:** Spend, Impressions, Clicks, Conversions, Videos

Framework supports filtering and segmentation across multiple ad platform data sources.

---

## Snowflake-Centric Architecture Shift

*Source: CF92/1365016577 (meeting 2024-09-03, strategic mandate from Dave)*

**Strategic mandate:** Move all Fusion92 data systems into a Fusion92-owned Snowflake instance to simplify architecture and improve cross-team collaboration.

### Architectural Drivers

1. **Simplification** — Reduce fragility of mixed AWS/Azure architecture
2. **Collaboration** — Easier cross-team participation in analytics
3. **Lower overhead** — vs. traditional database administration
4. **Scalability** — Separate analyst/data scientist accounts within the org

### Status (September 2024)

| Item | Status |
|------|--------|
| Experian identity graph → S3 pipeline | Complete |
| Python/EC2 JSON → relational schema | Complete |
| API matching function | Pseudo-code stage |
| DIOS→DAX integration | Paused 2–3 weeks (client priorities) |
| Fusion92 Snowflake account setup | Planned |
| Eclipse re-pointed to Snowflake | Planned |
| Experian data migration (historical) | Planned |

### Standardization Goals

- Consistent data pipeline approach across clients (reduce duplication)
- Standard Snowflake views as reporting interfaces (enforces consistency, manages team turnover)
- ML model framework for consistency across engineers

### Data Migration Notes

- **Experian data:** Fragment tables/aggregations planned for commonly queried subsets (performance optimization post-migration)
- **Dials data:** Optimal Snowflake ingestion method TBD
- **Storage shift:** S3 → Azure storage container for pipeline functions

### Access Control (to develop)

- Snowflake access control framework
- Object creation standards (tables, views, stored procedures)
- Reporting interface standards

## See Also

- [[fusion92]] — client overview, Eclipse connections, Snowflake warehouse views
- [[Snowflake]] — platform reference (account hierarchy, warehouse model, cost)
- [[custom-fusion-92-audience-api]] — DIOS-to-DAX API details (Nextcloud folder structure, REST API spec)
- [[nextcloud]] — staging file storage (90-day retention for DIOS audiences)
- [[adm]] — ADM sub-client (separate GCP/BigQuery stack, not Snowflake)
