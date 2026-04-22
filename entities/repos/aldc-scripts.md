---
tags: [entity, repo, aldc-scripts, utilities, cost-monitoring, slack, airtable, bash, python, cron]
aliases: [aldc-scripts, ALDC scripts, ALDC utility scripts, aldc/scripts, cost-monitoring scripts]
sources:
  - repos/aldc-scripts/f92_ticket_report.py
  - repos/aldc-scripts/send_slack.sh
  - repos/aldc-scripts/cost-monitoring/DEPLOY_TO_SERVER4.md
  - repos/aldc-scripts/cost-monitoring/azure-costs.sh
  - repos/aldc-scripts/cost-monitoring/corporate-costs-report.sh
  - repos/aldc-scripts/cost-monitoring/github-usage.sh
  - repos/aldc-scripts/cost-monitoring/send-cost-report-slack.sh
  - repos/aldc-scripts/cost-monitoring/install-cron.sh
  - repos/aldc-scripts/cost-monitoring/deploy-azure-automation.sh
  - repos/aldc-scripts/cost-monitoring/azure-runbook.ps1
  - repos/aldc-scripts/cost-monitoring/azure-logic-app.json
  - repos/aldc-scripts/cost-monitoring/reports/cost-report-2026-02-17.md
  - repos/aldc-scripts/cost-monitoring/reports/cost-report-2026-02-18.md
created: 2026-04-20
updated: 2026-04-20
---

# aldc-scripts

A small grab-bag repo (`github.com/ALDC-io/aldc-scripts`, 3 commits total as of 2026-04-20) holding ALDC-internal utility scripts that don't belong to any one product: a Fusion92 ticket-status PDF generator, a generic Slack-webhook wrapper, and the corporate cost-monitoring dashboard (Azure + GitHub + Anthropic). The repo has no CI/CD, no package manifest, no tests, and no `README.md`. The only in-repo documentation is `cost-monitoring/DEPLOY_TO_SERVER4.md`. Everything runs on operator machines or the Server4 VM directly. Git remote: `https://github.com/ALDC-io/aldc-scripts.git`; default branch is **`master`**, not `main` — unusual for ALDC repos.

**Disambiguation:** This is not `claude_code_enhanced/scripts/` (that dir holds CCE install + per-machine setup tooling in a different repo, unrelated). It is not one of the `scripts/` subdirectories inside [[eclipse_exp]], [[core_api]], or the [[clients-repo]] (each product repo has its own). It is not the [[executive-snapshot-email]] cron job (which runs on a different VM — Auriga — posts to a different channel, and has different recipients). It is also not the [[workflows]] repo's `F92_*` Azure Functions apps — naming is coincidental; both use the `F92` prefix because both are Fusion92-related, but they are different codebases on different runtimes.

---

> **Status: likely legacy — verify before relying on.** Drift between scripts in this repo and current wiki content (e.g. the Azure subscription lists in `azure-costs.sh` and `corporate-costs-report.sh` include subscriptions not documented in [[azure-environments]], and vice versa) suggests several scripts may have been superseded without the repo being pruned. Live status of individual scripts is unconfirmed as of 2026-04-20. All 3 commits were authored by Lori Beck (`lori.beck@aldc.io`). **Do NOT assume a script still runs just because it exists in this repo** — check cron schedules on the host, recent invocation logs, or ask the script's last committer before relying on it.
>
> **Additional evidence (2026-04-20, Paul Russell):** the `#the-olds` Slack channel targeted by `send-cost-report-slack.sh` is **not visible to Paul in the ALDC Slack workspace**. This is a strong signal that the weekly cost-report cron is dead, the channel was archived / renamed / made private, or the webhook is pointing at a destination Paul does not have access to. Either way, the `cost-monitoring/` production entry point cannot be assumed to be delivering output. Verify with Lori Beck (the author) and/or check `crontab -l` on Server4 as the `aldc` user before trusting anything in the `cost-monitoring/` directory.

---

## Repo layout

Full tree as of 2026-04-20 (13 source files, 2 committed report artefacts):

```
aldc-scripts/
├── f92_ticket_report.py             # Python 3, 315 lines — Airtable → PDF report (Fusion92 ticket status)
├── send_slack.sh                    # Bash, 35 lines — generic Slack webhook wrapper (jq-escaped JSON POST)
└── cost-monitoring/
    ├── DEPLOY_TO_SERVER4.md         # Runbook (125 lines) — how to deploy cost-monitoring to Server4
    ├── azure-costs.sh               # Bash, 102 lines — Azure cost report across 9 subscriptions (ad-hoc)
    ├── corporate-costs-report.sh    # Bash, 252 lines — unified Azure + GitHub + Anthropic MTD report → .md
    ├── github-usage.sh              # Bash, 145 lines — GitHub org (aldc-io) usage stats → .json
    ├── send-cost-report-slack.sh    # Bash, 93 lines — weekly wrapper: runs corporate-costs + posts Slack summary
    ├── install-cron.sh              # Bash, 20 lines — installs the weekly cron job
    ├── deploy-azure-automation.sh   # Bash, 146 lines — provisions Azure Automation Account + Runbook (prototype)
    ├── azure-runbook.ps1            # PowerShell, 94 lines — Azure Automation alternative (prototype, not in prod)
    ├── azure-logic-app.json         # Azure Logic App workflow definition (prototype, incomplete, not deployable)
    └── reports/
        ├── cost-report-2026-02-17.md  # Artefact — committed example output
        ├── cost-report-2026-02-18.md  # Artefact — committed example output
        └── slack-delivery.log          # Runtime log (committed sample; appended to on each run → git-dirty)
```

Notes:
- Every commit in `master` history is from Lori Beck (`lori.beck@aldc.io`): `180d4c0` (add Slack script), `111a64b` (add Fusion92 report), `1254813` (fix cost-monitoring paths + redact webhook).
- `reports/` contains two committed sample cost reports (Feb 17 + Feb 18, 2026). These are runtime artefacts and should not be committed — no `.gitignore` currently exists. See Tech Debt.
- No `.gitignore`, no `.env.example`, no `README.md`, no `CLAUDE.md`, no `CODEOWNERS`, no `.github/`. Intentional grab-bag shape.

---

## Script catalogue

This is the centrepiece section — the repo has no cross-script architecture, so a per-script inventory replaces the standard Architecture section.

### Table A — Script inventory

| Script | Lang | Purpose | Entry point | Last known frequency | Status | Host | Credentials required | Cross-reference |
|---|---|---|---|---|---|---|---|---|
| `f92_ticket_report.py` | Python 3 | Fetch Fusion92 ticket list from Airtable "Resource Allocation · F92 View [INTERNAL]" and generate a PDF status report with ALDC branding (executive summary + status-bar + sortable table by priority + key highlights). | `python3 f92_ticket_report.py` (writes to `~/../aldc/reports/Fusion92_Ticket_Status_YYYY-MM-DD.pdf`) | Ad-hoc (operator-run) | `unconfirmed` | Operator workstation (Linux with DejaVu fonts at `/usr/share/fonts/truetype/dejavu`) | `AIRTABLE_TOKEN` read from `~/../aldc/.env` (`fetch_tickets()` at `f92_ticket_report.py:46–66`) | [[fusion92]] (client page) |
| `send_slack.sh` | Bash | Generic Slack incoming-webhook wrapper. Uses `jq -Rs '{text: .}'` to safely JSON-encode the message before POSTing. Returns non-zero if Slack response is not `ok`. | `./send_slack.sh <webhook_url> <message>` | Ad-hoc (called by other scripts) | `unconfirmed` | Any machine with `bash`, `jq`, `curl` | Slack webhook URL passed as argument (not stored in repo) | Primary consumer: `send-cost-report-slack.sh` |
| `cost-monitoring/azure-costs.sh` | Bash | Per-subscription Azure cost listing across all 9 ALDC subscriptions for the current month, with per-service breakdown via `jq group_by`. Writes coloured stdout and `/tmp/azure-costs-YYYYMMDD.json`. | `./azure-costs.sh` (diagnostic) | Ad-hoc | `unconfirmed` | Any machine with `az` CLI logged in + `jq` + `bc` | `az login` session with Cost Management Reader on each subscription | [[azure-environments]] (4 of 9 subscription IDs already documented there) |
| `cost-monitoring/corporate-costs-report.sh` | Bash | Unified MTD cost report across Azure + GitHub (aldc-io) + Anthropic. Writes a markdown report to `$REPORT_DIR/cost-report-YYYY-MM-DD.md` (REPORT_DIR hard-coded to `/home/aldc/scripts/cost-monitoring/reports` — Server4-specific path). | `./corporate-costs-report.sh` (invoked by `send-cost-report-slack.sh`) | Weekly via wrapper (if cron active) | `unconfirmed` | Server4 (paths hard-coded) | `az login` + `gh auth` + Cost Management Reader on each subscription | Report is consumed by the Slack wrapper and readable standalone |
| `cost-monitoring/github-usage.sh` | Bash | Standalone GitHub org report for `aldc-io` — members, repos (count/private/storage), Actions billing, Storage billing, 30-day commit activity per member. Writes `/tmp/github-usage-YYYYMMDD.json`. | `./github-usage.sh` (diagnostic) | Ad-hoc | `unconfirmed` | Any machine with `gh` CLI authenticated + `jq` + `bc` | `gh auth login` (owner permissions needed for Actions + Storage billing endpoints; script tolerates 403 gracefully) | Not called by the weekly wrapper — superseded by inline GitHub calls in `corporate-costs-report.sh`. Retain for ad-hoc deep dives. |
| `cost-monitoring/send-cost-report-slack.sh` | Bash | **Production entry point.** Weekly cron target. Runs `corporate-costs-report.sh`, gathers Azure resource counts + GitHub members/repos, builds a Slack-formatted message, and POSTs via `send_slack.sh`. Channel `#the-olds` (recipients: Lori / JK / Mike). Logs to `reports/slack-delivery.log`. | `./send-cost-report-slack.sh` (called by cron: `0 9 * * 1`) | Last known: weekly, Mon 09:00 server-local | `unconfirmed` — cron presence on Server4 not confirmed as of 2026-04-20 | Server4 | `SLACK_WEBHOOK_THE_OLDS` env var (sourced from `/home/lori/.env`), `az login`, `gh auth` | [[executive-snapshot-email]] (sibling weekly-Slack pattern on a different VM — different host, different channel, different recipients) |
| `cost-monitoring/install-cron.sh` | Bash | Idempotently adds the `send-cost-report-slack.sh` entry to the current user's crontab. Schedule: `0 9 * * 1` (Mon 09:00). No-op if entry already exists. | `./install-cron.sh` (Server4 setup step) | One-shot (Server4 setup) | `unconfirmed` | Server4 | Current user's crontab write access | `DEPLOY_TO_SERVER4.md` runbook (in-repo) |
| `cost-monitoring/deploy-azure-automation.sh` | Bash | **Prototype, abandoned.** Provisions Azure Automation Account `aa-aldc-cost-reports` in resource group `rg-aldc-automation`, enables system-managed identity, assigns Cost Management Reader on 5 subscriptions, imports `azure-runbook.ps1`, publishes, schedules Mon 09:00 PST. | `./deploy-azure-automation.sh` | One-shot (setup) | `likely legacy` — no evidence of live Automation Account | Azure-authenticated workstation | `az login` with permissions to create automation accounts + role assignments, `SLACK_WEBHOOK_THE_OLDS` | [[azure-environments]], sibling: `azure-runbook.ps1` |
| `cost-monitoring/azure-runbook.ps1` | PowerShell | **Prototype, abandoned.** Azure Automation runbook that would replace `send-cost-report-slack.sh`. Uses managed identity + `Get-AzConsumptionUsageDetail` + GitHub REST. Reads `SlackWebhook_TheOlds` and `GitHubToken` from Automation Variables. | Invoked by Azure Automation schedule (if deployed) | Weekly (if deployed) | `likely legacy` — not in production | Azure Automation | Automation Variables (not env vars): `SlackWebhook_TheOlds`, `GitHubToken` | Deployed by `deploy-azure-automation.sh`. Not currently in production. |
| `cost-monitoring/azure-logic-app.json` | JSON (ARM) | **Prototype, incomplete, not deployable.** Azure Logic App workflow definition (weekly recurrence Mon 09:00 PST → HTTP GETs to Azure Subscriptions + GitHub members/repos → Compose → Slack POST). References `parameters('github_token')` which is not declared in the `parameters` block — only `slack_webhook_url` is declared. | Import into Azure Logic Apps | (unused) | `likely legacy` | Azure Logic Apps | `slack_webhook_url` (SecureString), undeclared `github_token` | Not deployable as-is. Prototype only. |

### Table B — Output artefacts

| Artefact | Producer | Path | Committed? |
|---|---|---|---|
| `Fusion92_Ticket_Status_YYYY-MM-DD.pdf` | `f92_ticket_report.py` | `~/../aldc/reports/` (operator-local) | No |
| `azure-costs-YYYYMMDD.json` | `azure-costs.sh` | `/tmp/` | No |
| `github-usage-YYYYMMDD.json` | `github-usage.sh` | `/tmp/` | No |
| `cost-report-YYYY-MM-DD.md` | `corporate-costs-report.sh` | `/home/aldc/scripts/cost-monitoring/reports/` (Server4) | 2 historical samples yes (Feb 17 + Feb 18, 2026); ongoing runs gitignored locally on Server4 |
| `slack-delivery.log` | `send-cost-report-slack.sh` | `reports/slack-delivery.log` | Yes (empty-ish sample committed) — appending on each run makes `git status` dirty — see Tech Debt |
| `cron.log` | cron wrapper | `reports/cron.log` | No (log path per `install-cron.sh:6`) |

---

## Data Flow

### Fusion92 ticket report

Single-hop: Airtable → PDF.

- **Source:** Airtable Base `app4jxyVmcfEH1D9k`, Table `tblOl8YykVDXq37an`, View **"F92 View [INTERNAL]"** (hard-coded at `f92_ticket_report.py:18–20`).
- **Auth:** Bearer token (`AIRTABLE_TOKEN`) read from `~/../aldc/.env` — not the repo's `.env`, but the operator's ALDC-wide env file.
- **Transform:** maps Airtable records → priority-sorted dicts (P1/P2/P3/unprioritised). Uses `Status`, `Priority`, `Outcome`, `Success Criteria`, `Remediation Steps`, `Outcome Group`, `Last Modified` fields. Detects paused state by scanning `Remediation Steps` for the `"PAUSED"` substring (`f92_ticket_report.py:78`).
- **Output:** landscape-letter PDF via `fpdf` with embedded DejaVu Unicode font from `/usr/share/fonts/truetype/dejavu`. Logo sourced from `~/../aldc/templates/aldc-logo.png`. PDF saved to `~/../aldc/reports/Fusion92_Ticket_Status_YYYY-MM-DD.pdf`.
- **No network output.** PDF distribution to Fusion92 is manual (email attachment or upload).

### Weekly corporate cost report

Three inputs → markdown report → Slack post to `#the-olds`.

1. **Azure Consumption API** via `az consumption usage list` for 9 subscriptions. Per the Feb 18 report artefact, 3 subscriptions returned full data; 6 returned "no data" (likely insufficient Cost Management Reader scope at time of the report — scope unconfirmed).
2. **GitHub org API** via `gh api /orgs/aldc-io/*` — members list, repo list (with `diskUsage`), Actions billing, Storage billing, 30-day commit search. Owner permissions required for billing endpoints; scripts `|| echo '{}'` on 403 so a non-owner identity runs silently with empty billing data.
3. **Anthropic API** — **not queried.** `corporate-costs-report.sh` always emits a "See Console" stub regardless of actual Anthropic spend. See Tech Debt.

- **Transform:** shell-side `jq`/`bc` summation; markdown report written line-by-line to `reports/cost-report-YYYY-MM-DD.md`.
- **Output:** Slack message to `#the-olds` via `send_slack.sh` → `SLACK_WEBHOOK_THE_OLDS` webhook; log tee'd to `reports/slack-delivery.log`.
- **Azure subscription list** is hard-coded in **three separate places**: `azure-costs.sh:26–36`, `corporate-costs-report.sh:68–78`, `deploy-azure-automation.sh:54–60`. The three lists disagree: `azure-costs.sh` and `corporate-costs-report.sh` list all 9 subscriptions; `deploy-azure-automation.sh` lists only 5 (drops Stage 1, Demo 1, Support 1, zeus_memory_dev). See [[azure-environments]] for the 4 IDs already documented there; 5 additional IDs (Stage 1, Development 2, Demo 1, Support 1, zeus_memory_dev) appear in the cost scripts but are not yet in that page.

### Slack webhook pass-through

`send_slack.sh` is two hops: argv → `jq -Rs '{text: .}'` → temp file → `curl` POST. No state, no logging, no retries. Returns 1 if Slack response is not the literal string `ok`.

### No other data flows

No database writes. No cron-driven Airtable polling. No inbound webhooks. No long-running daemons.

---

## Developer Guide

### Prerequisites (per script)

**`f92_ticket_report.py`**
- Python 3.10+ (`from pathlib import Path`, f-strings; no walrus-operator syntax)
- `fpdf` — the legacy package, **not `fpdf2`**. The `add_font(..., uni=True)` kwarg is the legacy `fpdf` API; `fpdf2` will fail with an unknown-kwarg error. Pin explicitly to `fpdf` (no `2`).
- Linux with DejaVu fonts at `/usr/share/fonts/truetype/dejavu` (`apt install fonts-dejavu-core`). Windows/macOS will fail at font registration unless the operator edits `FONT_DIR`.
- `~/../aldc/.env` must contain `AIRTABLE_TOKEN=...`. `~/../aldc/templates/aldc-logo.png` and `~/../aldc/reports/` must exist.
- **Path trap:** `Path.home().parent` means one directory above the user's home. For `/home/lori`, that's `/home/`, so the expected structure is `/home/aldc/{.env,templates,reports}/` — a Server4-adjacent layout, not a per-user layout. On Windows (`C:\Users\PaulRussell`), `Path.home().parent` resolves to `C:\Users\` — very fragile outside Server4.

**`send_slack.sh`**
- `bash`, `jq`, `curl`. Nothing else.

**`azure-costs.sh`, `corporate-costs-report.sh`, `github-usage.sh`, `send-cost-report-slack.sh`**
- `bash`, `jq`, `bc`, `curl`, `sed` (GNU sed — `sed -i` syntax)
- `az` CLI authenticated (`az login`), identity with Cost Management Reader on each subscription being scanned
- `gh` CLI authenticated (`gh auth login`), org-owner scope on `aldc-io` for full billing visibility (partial data returned without it — no error, just silent empty output)

**`deploy-azure-automation.sh`**
- `az` CLI with permissions to create resource groups, automation accounts, role assignments, runbooks, schedules.

**`azure-runbook.ps1`**
- Runs inside Azure Automation — uses `Get-AutomationVariable`, `Connect-AzAccount -Identity`. Not intended to run locally.

**`azure-logic-app.json`**
- Deploy via `az logic workflow create` or Azure Portal. **Incomplete** — missing `github_token` parameter declaration. Not deployable as-is.

### Clone and run

1. `git clone https://github.com/ALDC-io/aldc-scripts.git && cd aldc-scripts`. Note the default branch is **`master`**, not `main` — differs from all other ALDC repos.
2. `chmod +x cost-monitoring/*.sh send_slack.sh` (files are committed with `0755`, but some systems drop permissions on clone).
3. For the Fusion92 report: `pip install fpdf` (legacy package, not `fpdf2`) + ensure `AIRTABLE_TOKEN` in the operator's `.env`.
4. For cost-monitoring: `az login && gh auth login`; export `SLACK_WEBHOOK_THE_OLDS` (from [[vault]] § Slack webhooks).

### Running each script locally

- `python3 f92_ticket_report.py` — prints progress lines; output PDF path printed at end.
- `./cost-monitoring/azure-costs.sh` — coloured stdout, `/tmp/azure-costs-*.json` dumped.
- `./cost-monitoring/corporate-costs-report.sh` — **will fail outside Server4** unless you manually `mkdir -p /home/aldc/scripts/cost-monitoring/reports` first (`REPORT_DIR` is hard-coded at line 8 and the `mkdir -p` at line 22 will fail if `/home/aldc` doesn't exist without elevated permissions).
- `./cost-monitoring/github-usage.sh` — standalone, safe to run anywhere with `gh` authenticated.
- `./cost-monitoring/send-cost-report-slack.sh` — **sends a real Slack message.** Don't run without the webhook pointing at a test channel.
- `./send_slack.sh <webhook> <message>` — quick webhook test.

### Common pitfalls

1. **`corporate-costs-report.sh` has Server4 paths baked in** — `REPORT_DIR=/home/aldc/scripts/cost-monitoring/reports` (line 8). Running on an operator workstation writes to a path that doesn't exist without manual setup.
2. **`SLACK_SCRIPT` hard-coded to `/home/aldc/scripts/send_slack.sh`** in `send-cost-report-slack.sh:9`. Server4-only. The committed file expects `send_slack.sh` to have been copied to that exact path per `DEPLOY_TO_SERVER4.md:35–39`.
3. **`f92_ticket_report.py` path assumptions** — `Path.home().parent / "aldc"` is a Server4-adjacent layout. On Windows, resolves under `C:\Users\aldc\`; will need manual setup.
4. **`fpdf` vs `fpdf2`** — installing `fpdf2` breaks the script. Pin to `fpdf` (no `2`) explicitly.
5. **Azure subscription list drift** — three scripts keep their own hard-coded list; `deploy-azure-automation.sh` lists only 5 while the others list 9. Update one, forget the others — silent miss.
6. **GitHub billing endpoints require org-owner scope.** Scripts `|| echo '{}'` the failure, so a non-owner `gh` identity runs cleanly but produces empty billing data. Easy to miss.
7. **Anthropic cost is never fetched programmatically** — the report always emits "See Console" regardless of actual spend.
8. **`fpdf` font file requirement** — `/usr/share/fonts/truetype/dejavu/DejaVuSans*.ttf`. On non-Debian hosts: `apt install fonts-dejavu-core`.
9. **`reports/slack-delivery.log` is committed** — running the script appends to it, so `git status` looks dirty after every run.
10. **`master` default branch** — differs from the rest of ALDC repos (`main`). Watch for PR tooling defaults.

---

## Deployment

### Deployment target — Server4 (production CCE host)

The only "deployed" script in this repo is `cost-monitoring/send-cost-report-slack.sh`, scheduled via cron on Server4. Server4 is the ALDC production CCE host; see [[deployment-groups]] for the host inventory and [[claude_code_enhanced]] for the CCE context. The in-repo runbook `cost-monitoring/DEPLOY_TO_SERVER4.md` is the authoritative deployment guide.

No CI/CD — deployment is manual `scp`.

**Live status unconfirmed.** As of 2026-04-20, whether the cron job is actually installed and running on Server4 has not been verified. Check `crontab -l` as the `aldc` user before assuming the weekly report is active.

### Deploy steps (summarised — defer to in-repo runbook for detail)

1. `scp -r cost-monitoring aldc@<server4>:/home/aldc/scripts/`
2. Copy `send_slack.sh` from repo root to `/home/aldc/scripts/send_slack.sh` (path hard-coded in `send-cost-report-slack.sh:9`).
3. `ssh aldc@<server4>` → `chmod +x /home/aldc/scripts/cost-monitoring/*.sh` → `mkdir -p /home/aldc/scripts/cost-monitoring/reports`
4. Verify `az account show` + `gh auth status`. Ensure `SLACK_WEBHOOK_THE_OLDS` is set in `/home/lori/.env` — this path is hard-coded in the script and is sourced despite the script running as the `aldc` user (see Tech Debt item on cross-user env dependency).
5. Run `./install-cron.sh` to install the Mon 09:00 cron job.
6. Manual test: `./send-cost-report-slack.sh` (sends a live Slack message to `#the-olds`).

### Alternative deployment paths (prototype, abandoned)

- **Azure Automation** — `deploy-azure-automation.sh` + `azure-runbook.ps1`. Would provision Automation Account `aa-aldc-cost-reports` in resource group `rg-aldc-automation` with managed identity, Cost Management Reader on 5 subscriptions, and a Mon 09:00 PST schedule. **Not in production.** No evidence of a live Automation Account as of 2026-04-20. Treat as prototype.
- **Azure Logic App** — `azure-logic-app.json`. Even more self-contained. **Incomplete and not deployable** — missing `github_token` parameter declaration. Treat as prototype.

These were started but not finished. The Server4 cron path is the only route that was ever in production (status currently unconfirmed — see above).

### Rollback

No rollback machinery. If a weekly cost report breaks: `crontab -e` to comment out the line, or `scp` an older version of the script tree. Report files accumulate with no retention policy — see Tech Debt.

### No repo-level CI/CD

No `.github/workflows/`. No tests. No linter. No pre-commit hook. Unlike [[eclipse_exp]], [[workflows]], and [[custom-fusion-92-audience-api]] (which all have PR checks per [[ai-pr-workflow]]), this repo has zero automated gates. Any commit to `master` ships. Low-consequence here because outputs are read by humans on one VM, but flag for readers who assume the ALDC-wide CI story applies.

---

## Security & Credentials

### Credential scan — results

**No hardcoded secrets remaining.** Commit `1254813` ("Fix cost-monitoring script paths and redact hardcoded Slack webhook") explicitly removed a hard-coded Slack webhook URL. Post-redaction verified: grep across the repo for `ghp_`, `sk-ant-`, `xoxb-`, `AKIA`, and the Slack `hooks.slack.com/services/T.../B.../[token]` pattern returns no matches.

**One partial Slack webhook URL remains in `DEPLOY_TO_SERVER4.md:85–89`:** `https://hooks.slack.com/services/T01Q410SQ9W/B0A9QGFT1C3/...` — the `...` shows the private suffix was deliberately truncated. The workspace ID (`T01Q410SQ9W`) and channel app ID (`B0A9QGFT1C3`) are visible but are not actionable without the suffix. Low severity; see Tech Debt for recommendation.

**Other identifiers in the repo (not secrets):**
- Slack User IDs in `azure-runbook.ps1:80` — `<@U0A6A9VN96V>` `<@U01NZCSEWQ7>` `<@U081KV3RKT8>` (Lori, JK, Mike). ALDC-internal, not exploitable.
- Azure subscription IDs hard-coded in three scripts. Not secrets; cross-referenced in [[azure-environments]].
- Airtable Base ID `app4jxyVmcfEH1D9k` and Table ID `tblOl8YykVDXq37an` hard-coded at `f92_ticket_report.py:18–19`. Not secrets.

### Runtime credentials required (operator must provide)

| Credential | Description | Storage |
|---|---|---|
| `AIRTABLE_TOKEN` | Personal access token with read scope on the F92 Airtable base | Operator's `~/../aldc/.env` |
| `SLACK_WEBHOOK_THE_OLDS` | Incoming webhook URL for `#the-olds` Slack channel | `/home/lori/.env` on Server4 (see Trust Boundaries note below); referenced via `${SLACK_WEBHOOK_THE_OLDS:-}` — empty-string fallback means an unset value won't error, but the webhook POST will fail silently |
| `az` session | AAD identity with Cost Management Reader on relevant subscriptions | `az login` session |
| `gh` session | GitHub PAT or `gh auth login` session with org-owner scope on `aldc-io` | `gh auth login` session |
| Automation Variables (Azure path only) | `SlackWebhook_TheOlds` + `GitHubToken` as encrypted Automation Variables | Azure Automation (prototype path only) |

Cross-reference [[vault]] / `vault/credentials.md` § Slack webhooks for the full webhook URL. If a vault entry does not yet exist for `AIRTABLE_TOKEN`, file it before running the Fusion92 report script.

### Trust boundaries

- **Server4** holds `SLACK_WEBHOOK_THE_OLDS` in `/home/lori/.env`. Compromise of Server4 = ability to post arbitrary messages to `#the-olds`. Not a data-plane risk.
- **Airtable token** stored in `/home/aldc/.env` (or equivalent on operator workstation). Compromise = read access to the Fusion92 ticket list.
- **No secret ever flows through GitHub Actions** — no CI/CD exists.

---

## Status & future home

### Current status: unconfirmed / likely legacy

The repo was last committed to by Lori Beck (3 commits, all in the `master` branch). No active maintainer has been confirmed. The key unknowns:

- Is the weekly cost-report cron actually running on Server4 right now? (Check `crontab -l` as the `aldc` user.)
- Is `f92_ticket_report.py` still being run for Fusion92 reviews, or has that been superseded?
- Are the Azure subscription lists in these scripts current (9 subscriptions in `corporate-costs-report.sh`) or stale?

Given the drift against [[azure-environments]] and the absence of any recent commit activity, treat this repo as **likely legacy until confirmed otherwise**.

### Future home candidates (if scripts are confirmed active)

- **Cost-monitoring dashboard:**
  - A [[Prefect]] scheduled flow (weekly, parameterised per cloud). [[Prefect]] is already the target for connector migration; adding a cost-reporting flow is straightforward.
  - An [[eclipse_exp]] ops dashboard — the platform already has health/perf infrastructure that could surface cost data.
  - An Azure Automation Account — `deploy-azure-automation.sh` already provides the scaffold; finishing and deploying it would retire Server4 as a cost-monitoring host.
- **Fusion92 ticket report:**
  - Integration into [[custom-fusion-92-audience-api]] (`/tickets/report` endpoint) — low fit because the report is operational, not data-plane.
  - A [[Prefect]] flow that runs weekly and posts the PDF to a Google Drive folder or Slack channel.
  - Remaining ad-hoc in this repo indefinitely is also acceptable — it's low-volume and operator-invoked.
- **`send_slack.sh`:** once everything that calls it moves, retire it. Until then, keep.

No immediate migration commitment. Cross-reference [[ai-delivery-pivot|ALDC AI-Driven Delivery Pivot]] for the broader platform consolidation direction.

---

## Tech Debt & Known Issues

1. **Three Azure subscription lists that have already drifted.** `deploy-azure-automation.sh:54–60` lists 5 IDs; `azure-costs.sh:26–36` and `corporate-costs-report.sh:68–78` list 9. A single sourced list (env file, JSON, or the [[azure-environments]] wiki table) would remove drift risk. **First step: confirm which scripts are still active before investing in consolidation.**
2. **No programmatic Anthropic cost fetch.** `corporate-costs-report.sh` always emits "See Console." Anthropic's Admin API (introduced late 2025) could fill this gap; the script predates it. Retire or fix once active status confirmed.
3. **Server4 paths hard-coded in three scripts** (`corporate-costs-report.sh:8`, `send-cost-report-slack.sh:9`, and the `/home/lori/.env` sourcing path). Running on any non-Server4 host requires edits.
4. **Cross-user env dependency: `send-cost-report-slack.sh` sources `SLACK_WEBHOOK_THE_OLDS` from `/home/lori/.env`** while running as the `aldc` user. Acknowledged in the script's comment at line 10 (`# set in /home/lori/.env as SLACK_WEBHOOK_THE_OLDS`). Brittle — if Lori's home dir is removed or the env file changes structure, the cron job breaks silently (the `:-` fallback returns empty string, not an error).
5. **`azure-logic-app.json` is incomplete.** References undeclared `parameters('github_token')`. Not deployable as-is. Either finish it or delete it.
6. **Two unused alternative deploy paths** (`azure-runbook.ps1` + `deploy-azure-automation.sh` + `azure-logic-app.json`) were started but not completed. Keeping all three alongside the cron path is confusing. Retire or confirm — don't leave prototypes alongside production scripts without clear labelling.
7. **Committed runtime artefacts** — `reports/cost-report-2026-02-17.md`, `reports/cost-report-2026-02-18.md`, `reports/slack-delivery.log`. A `.gitignore` on `reports/*.md` and `reports/*.log` would fix this.
8. **No `.gitignore`, no `README.md`, no `.env.example`, no pre-commit.** Bare-bones repo hygiene.
9. **Partial Slack webhook URL in `DEPLOY_TO_SERVER4.md:85–89`** — workspace + channel app IDs visible. Low severity (suffix was deliberately truncated), but the doc should reference [[vault]] instead of embedding any part of the URL.
10. **`fpdf` (not `fpdf2`) with no version pin.** `pip install fpdf` installs whatever is current; a future release could break `add_font(..., uni=True)`. Pin explicitly.
11. **Fusion92 report path assumptions** are Server4-adjacent (`Path.home().parent / "aldc"`). Windows/macOS-hostile without manual setup.
12. **No CI/CD, no tests** — a broken script ships silently until the next Monday run. Unlike the rest of the ALDC portfolio, this repo has zero automated gates.

---

## See Also

- [[fusion92]] — client page; Airtable view name and priority taxonomy originate here
- [[azure-environments]] — 4 of the 9 subscription IDs are already documented; the cost scripts' hard-coded lists should be reconciled against this page once active scripts are confirmed
- [[executive-snapshot-email]] — sibling weekly-Slack automation running on a different VM (Auriga → `aldctestagnt1c01`); different host, different recipients, different channel — disambiguate explicitly
- [[deployment-groups]] — Server4 context (the production CCE host)
- [[claude_code_enhanced]] — CCE lives on the same Server4 host; the repos coexist but don't share code
- [[Azure]] — tool page; cost scripts use the Consumption API heavily
- [[vault]] — runtime credentials reference (Slack webhook, Airtable token)
- [[ai-pr-workflow]] — the ALDC-wide PR workflow that this repo does NOT enforce
- [[Prefect]] — future-home candidate for the cost-monitoring dashboard
- [[eclipse_exp]] — future-home candidate for ops dashboards and cost-monitoring surfaces
- [[custom-fusion-92-audience-api]] — the other Fusion92-adjacent repo; the `F92` naming here is coincidental (different runtime, different purpose)
- [[workflows]] — Azure Functions backend for DAX Media App; also uses `F92_` prefix (naming collision — different codebase, different runtime)
