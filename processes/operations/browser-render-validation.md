---
tags: [process, operations, testing, playwright, browser, consumer-layer, evidence]
aliases: [browser_ops, CDP harness, Claude in Chrome replacement, render evidence]
sources: [FU92-428 (2026-08-28, measured against prod fusion92.eclipse.aldc.io)]
created: 2026-08-28
updated: 2026-08-28
---

# Browser render validation (the `browser_ops` CDP harness)

How to get **rendered-surface evidence** — the thing the global evidence rules demand for any
dashboard/report/UI change — when Claude in Chrome will not pair.

**Harness:** `aldc-launchpad/browser_ops/` (branch `feature/fu92-428-429-evidence` @ `c8d8e35`).
Playwright attached over CDP to a real Chrome. Built on FU92-428, where a query-layer check would
have given the wrong answer twice.

## Why CDP-attach rather than a fresh browser

Claude in Chrome **will not pair on the `paul.russell@aldc.io` Enterprise account** (confirmed
2026-08-28: extension v1.0.85 installed, Default profile, no blocking policy, re-pair failed).

Eclipse issues an **`httpOnly`, `__Secure-` session cookie scoped to `.eclipse.aldc.io`**
(`flight-check/authOptions.ts:133-146`). Two consequences:

- `httpOnly` means page JavaScript cannot read it, so cookie-scraping approaches were never viable.
- Attaching to a browser **you** are already logged into means the cookie rides along automatically
  and **no password, token or cookie is ever handled by the automation.** That is the point: it is
  both simpler *and* the only version where credentials never change hands.

> The Docker `playwright-mcp` container (`:8931`) is an **isolated headless Chromium with no access
> to your profile**. Fine for unauthenticated work; it cannot reach anything behind a login.

## ⚠ The gotcha that costs an hour

**Since Chrome 136, `--remote-debugging-port` is SILENTLY IGNORED on the Default user-data-dir.**
It is a deliberate anti-cookie-theft control. The flag appears in the process command line, Chrome
starts normally, and **nothing ever listens on the port** — no error, anywhere.

Measured 2026-08-28 on Chrome 151, same binary, back to back:

| Launch | CDP listening? |
|---|---|
| `--remote-debugging-port=9222` on the Default profile | **no** |
| `--remote-debugging-port=9223 --user-data-dir=<other dir>` | **yes** |

⇒ **You must pass `--user-data-dir` pointing somewhere other than the default.** Do not work around
it by copying the Default profile across — that is exactly the theft the control exists to stop.

```powershell
$prof = "$env:LOCALAPPDATA\Google\Chrome\CDP-Automation-Profile"
Start-Process "C:\Program Files\Google\Chrome\Application\chrome.exe" `
  -ArgumentList "--remote-debugging-port=9222","--user-data-dir=$prof",
                "--no-first-run","--no-default-browser-check","<target url>"
```

Runs as a second window alongside normal Chrome, which needs no restart. The profile **persists**,
so the app login is a one-time human action.

## Always calibrate before trusting a result

`preflight.mjs` reports `AUTHENTICATED` / `NOT AUTHENTICATED` by whether the app bounces to `/login`.
**Run it and see it fail once** (before logging in) — a negative control is what makes the later
positive trustworthy. Same principle as any other instrument: *a reading from an instrument you have
not proved can see is not a measurement.*

## ⛔ Evidence files leak client data — grep before committing

Two leaks in this harness's own first run, both caught before staging, both now fixed at source:

1. `record()` stored the first 2,000 bytes of **every** response body — including a successful
   export, i.e. the client's data.
2. `refuseDownloads()` cancelled the download, then logged `download.url()`. **For a `data:` URI the
   URL *is* the entire file** — 44,798 chars of client media-plan data landed in the evidence JSON.
   *A helper written to avoid storing a file stored it anyway, through the one field nobody thinks of
   as content.*

`lib/attach.mjs` now withholds success payloads and `data:`/`blob:` URLs at capture time. Regardless:
**grep any new evidence file for long base64 runs before staging** (`grep -rnoE '[A-Za-z0-9+/]{60,}'`).

The same class of mistake applies to **Cosmos document captures**: a user document carries the
account's `password` hash and `password_reset` token. Strip them, and treat a captured document as a
*rollback reference*, never a restore payload — replaying it also reverts any password changed since.

## Two measurement lessons worth more than the tooling

- **Never measure a consumer-layer limit from outside the consumer's session.** An unauthenticated
  probe put FU92-428's request-size cap at n≈133; inside the real session it is **n=114**, because
  cookies and browser headers eat the budget. The anonymous probe said "the code is fine". It wasn't.
- **Check whether the app is in an iframe before writing a single selector.** Eclipse renders
  Flight Check in an iframe on `dax.<client>.eclipse.aldc.io`; the top document has no table and no
  buttons. Measuring the shell host produced an entirely wrong conclusion that survived several steps.

## See Also

- [[dax-media-app]] — the app this was built against; carries the export ceiling and the `dax.`
  subdomain security finding
- [[fusion92-platform-ids]] — the other FU92 defect validated with this harness
- [[vacuous-verification]] — the sibling failure mode: a green check that checked nothing
