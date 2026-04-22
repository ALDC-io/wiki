---
tags: [process, operations, client-management, invoicing, billing]
aliases: [Client Invoicing, Invoicing Process]
sources: [Confluence CLIEN/1730281475]
created: 2026-04-18
updated: 2026-04-18
---

# Client Invoicing Process

Three invoicing models are in use at ALDC. Contact the internal accounting team at `accounting@aldc.io` (cc `esha@jamescameroninc.com`) to request invoice issuance for all types.

## 1. Project-Based Invoicing

Gate payments tied to project phases (Gate 1 / 2 / 3 as defined in the Project Approach).

1. Use project forms found in Figma (Project Forms → project scope tab) or Excel forms provided by John/Sales.
2. Deliver signed forms to customer and John via Docusign.
3. Save pre/post-sign copies to `Nextcloud\Sales\Customers\Projects\<client>\<project>\`.
4. Email accounting to request invoice issuance. Invoice includes a payment link (credit card) or payment instructions.
5. Confirm payment before advancing to the next gate.

## 2. Quarterly Payment Plans (GEP model)

1. During quarterly planning, confirm which new work is included with the client.
2. Verify with the Product Manager that team schedule is available.
3. Reference files: `Nextcloud\Sales\Customers\Global eComm Partners\Quarterly Payments`.
4. Account for: discontinued maintenance, new integrations/maintenance, data license adjustments (# of users → Service Item update).
5. Use Eclipse invoice feature to build the line-item breakdown — ensure Actual Start Dates on Service Items fall within the invoice period.
6. Email accounting with agreed amount. Invoice amount must match the compiled quarterly Excel file.
7. Confirm payment before commencing new work for the quarter.

> **Note:** The Eclipse invoice hasn't been shared directly with the customer since 2025, but it's a good reference to attach internally.

## 3. Monthly Invoicing

1. Use Eclipse invoice feature to verify amounts. Ensure SI Actual Start Dates are accurate for the billing period.
2. Email accounting to request invoice issuance.
3. If invoice is unpaid after 30 days — follow the overdue payment process (TBD as of 2025-12).

## Invoice Storage

All invoices stored at `Nextcloud\ALDC Management\Invoices`.

## Accounting Contacts

- **Internal accounting team:** `accounting@aldc.io`
- **CC:** `esha@jamescameroninc.com`

## See Also

- [[client-deactivation]] — includes Service Item Stop Date step on deactivation
- [[eclipse]] — invoice feature used for line-item breakdowns
- [[nextcloud]] — Nextcloud file paths for sales docs and invoices
- [[GEP]] — primary client on quarterly payment plan
