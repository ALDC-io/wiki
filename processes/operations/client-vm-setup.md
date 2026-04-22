---
tags: [process, operations, client-management, vm, parsec]
aliases: [Client VM Setup]
sources: [Confluence CLIEN/1658716161]
created: 2026-04-18
updated: 2026-04-18
---

# Client VM Setup

Setting up a Windows VM for a client to use when they cannot install local tooling (e.g. Mac users without Parallels, or IT restrictions blocking Parallels).

## When to Set Up a Client VM

- Client is a Mac user unable to install Parallels (IT department blocks it)
- Client needs access to Power BI Excel models for testing and has no compatible machine

## Steps

1. Set up VM for the client (Sean O'Grady has infrastructure access details)
2. Client creates a Parsec account and provides credentials to ALDC
3. ALDC uses those credentials to complete VM setup
4. ALDC provides the VM password to the client
5. Client installs the Parsec app (may require their IT department)
6. Client connects to the VM via Parsec, then accesses Eclipse to download a copy of the model
7. Client tests the model within the VM

## Known VM Users (as of 2025-08)

**Fusion92:**
- Juliann Otto
- Ben Lohman
- Ronan Gabriel

## See Also

- [[client-onboarding-checklist]] — broader onboarding process
- [[deployment-groups]] — VM infrastructure details
- [[agent-builds]] — agent VM build procedures
