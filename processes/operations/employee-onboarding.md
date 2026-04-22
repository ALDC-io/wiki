---
tags: [process, operations, onboarding, accounts, access, hr]
aliases: [Employee Onboarding, New hire checklist, Account setup]
sources: [Confluence TECH/1231945782 (Employee Onboarding)]
created: 2026-04-17
updated: 2026-04-17
---

# Employee Onboarding

Account & software access checklist for a new ALDC hire. Complements the **technical machine setup** at [[environment-setup]] — this page covers accounts and permissions; `environment-setup` covers tooling and local dev environment.

## Phase 1 — core accounts

### Microsoft 365 / Azure
- [ ] Microsoft Office 365 company account access
- [ ] Change password on first sign-in
- [ ] Access invitation for Microsoft [[Azure]]
- [ ] Azure Test subscription permissions for the Microsoft account

### Communications
- [ ] [Slack](https://slack.com/get-started) account setup
- [ ] Access invitation for the ALDC Slack
- [ ] Invite to appropriate channels

### Credentials & time tracking
- [ ] [Dashlane](https://www.dashlane.com/) invite
- [ ] [TSheets](https://tsheets.intuit.com/) (QuickBooks Time) account setup

### VM access
- [ ] VM access through [Parsec](https://parsec.app/)

### GitHub
- [ ] [GitHub](https://github.com/join) account setup
- [ ] **Naming convention**: `aldc-<firstname><lastname>` (e.g. `aldc-mitchellpask`)
- [ ] Enable 2FA
- [ ] Access invitation for the ALDC GitHub org

### Git + repos
- [ ] [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) installation
- [ ] Clone appropriate repos (see [[clients-repo]], [[core_api]], [[connector]])

### Atlassian
- [ ] [Jira and Confluence](https://id.atlassian.com/) account setup
- [ ] Access invitation for the ALDC Atlassian group
- [ ] Add to appropriate Jira groups to view tickets

### Eclipse + Snowflake + Postman
- [ ] [[Eclipse]] Test account + permissions
- [ ] [[Snowflake]] Test account + 2FA
- [ ] [Postman](https://www.postman.com/downloads/) account setup and installation (if required) — see [[Postman]] / [[postman-collections]]

## Phase 2 — expanded access

- [ ] Eclipse Test account (if not already granted)
- [ ] Permissions audit
- [ ] Snowflake **Prod** account + 2FA
- [ ] Azure Test subscription permissions (if not already granted)
- [ ] Nextcloud account creation

## Training walkthroughs

Standard onboarding walkthroughs, typically paired with a mentor:

- Jira walkthrough
- Communication tools (Teams, Slack, meetings, group work)
- Confluence walkthrough
- [[Azure]] [[CosmosDB]] and [[Snowflake]] walkthrough
- Core functionality walkthrough (see [[core_api]])
- Connector functionality walkthrough (see [[connector]])
- Portal walkthrough (Eclipse portal / node web apps)
- Client repo info walkthrough — see [[clients-repo]] and [[client-repo-structure]]

## After access is granted

Once accounts + permissions are in place, hand off to the technical setup at [[environment-setup]] (Git, Python, VS Code, SSMS, SnowSQL, Docker agents, VM access).

## See Also

- [[environment-setup]] — technical machine setup (tooling, Python venv, Docker, VMs)
- [[clients-repo]] — primary repo new hires work in
- [[Eclipse]] / [[Snowflake]] / [[CosmosDB]] / [[Azure]] — the core stack
- [[postman-collections]] — Postman setup for API testing
