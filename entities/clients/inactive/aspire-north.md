---
tags: [entity, client, aspire-north]
aliases: [ASPIRE_NORTH]
sources: [Confluence CLIEN/1047822343, Confluence CAN/1235845127]
created: 2026-04-18
updated: 2026-04-18
---

# ASPIRE_NORTH

Client engagement initiated 2022-12. Minimal documentation — engagement at early/inactive stage.

## Kickoff Notes (2022-12-07)

Attendees: David, Jason, John, Sean, Mitch, Karen.

Technical discovery items discussed:
- Data Sources/Systems assessment (cloud vs. local infrastructure, access approach, current transformation logic)
- Snowflake provisioning — Snowflake contact: Dave; ALDC to receive access for Eclipse integration
- Weekly status meetings established
- Nextcloud federation for file sharing

## Customer Insights Dashboard (REQ-169/CUST-679)

**Status:** In progress (last updated 2024-05-21). **Due:** 2024-04-30.

**RACI:**
- Responsible: Aaron Stryd, Karen Prete, Mitchell Pask
- Accountable: Joe Caslino
- Consulted: Jason Carlson, Sean O'Grady
- Informed: John Moran

**Purpose:** Automate Aspire North's manual customer profiling report workflow. Clients provide a customer file; Aspire enhances it with Experian data, then indexes it against a national consumer file to produce ~40 standardized visualizations for a customer-facing insights deck.

**Key pain points being automated:**
- Manual Excel indexing of customer file vs. national consumer file (Experian, ~900 appendable fields, ~40 standard)
- Manual chart creation in Tableau/Excel and export to PDF/PPTX

**Scope (in):**
- Ingest appended customer file (.CSV) and national consumer file via NextCloud
- Auto-index customer file vs. national consumer file
- 40 visualizations across 4 types; 38 Experian data fields verified
- PNG export: single visualization + full zip deck

**Scope (out):** Automated Experian enhancement, automated report creation.

**Data fields in scope (38 verified):**

| Category | Fields |
|---|---|
| Demographics (11) | Children presence, Dwelling type, Home value, Household income, Homeowner/renter, Length of residence, Age, Education, Ethnic group, Gender, Marital status |
| Personality — Self-Concept (5) | DM Type L, M, P, S, T |
| Mosaic (1) | Mosaic Household |
| Attitudes — Health/Political/Tech (3) | Health & Well Being, Political Persona, Technology Adoption |
| TrueTouch Engagement (7) | Broadcast/Cable TV, Digital Display, Digital Newspaper, Mobile SMS/MMS, Radio, Streaming TV, Traditional Newspaper |
| TrueTouch Buying Behaviours (9) | Brand loyalists, Deal seekers, In-the-moment shoppers, Mainstream adopters, Novelty seekers, Organic/natural, Quality matters, Recreational shoppers, Trendsetters + Savvy researchers |

**Eclipse feature requirements:** File upload UI, auto-indexing pipeline, dashboard with PNG export (single + zip deck).

**Wireframes:** 4 visualization type mockups attached as PDFs in Confluence (blob references — image-only, not retrievable via MCP).

**Source:** Confluence CAN/1235845127

## See Also

- [[client-onboarding-checklist]] — standard onboarding process
