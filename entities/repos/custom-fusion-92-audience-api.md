---
tags: [entity, repo, fusion92, aldc, api, on-prem]
aliases: [DIOS API, DIOS-to-DAX API, custom-fusion-92-audience-api]
sources: [Confluence TECH/1766031362 (DIOS-to-DAX API, Brayden Offboarding), Confluence CF92/1692991495, Confluence CF92/1364688898, repo review 2026-04-20 (README, main.py, file_specification.py, file_handler.py, gunicorn.conf.py, Dockerfile, requirements.txt, client/client.py, generate_sample_file.py)]
created: 2026-04-17
updated: 2026-04-20
---

# custom-fusion-92-audience-api

Custom web API built for [[fusion92]] that formats marketing audience data into per-ad-platform exports. Repo: https://github.com/ALDC-io/custom-fusion-92-audience-api. Production URL: https://audience-fusion92-app.aldc-ca-w1.com/. Runs on-prem as a Docker container behind Nginx and Cloudflare DNS.

## What it does

Fusion92 runs a web app internally called **DIOS**. DIOS posts raw audience data (rows of personal identifiers — email, address, IP, etc) to this API. The API joins two sources of audience data and outputs one or more files per destination platform, each formatted to that platform's requirements.

Each destination platform expects a different layout:

- **Reddit**: separate files for emails, phone numbers, mobile advertising IDs
- **Meta**: one CSV with one row per audience member, all identifying columns inline
- Other platforms: similar per-platform rules

"DAX" is Fusion92's umbrella term for the products ALDC builds for them — hence "DIOS-to-DAX" (DIOS is the input side; DAX is the product family).

## Architecture

### Tech stack

Python 3.11+ · FastAPI + Pydantic · Gunicorn with UvicornWorker · pandas · nextcloud-api-wrapper · python-dotenv.

Source: `requirements.txt`.

### Entry point and process model

FastAPI app object: `main:app`. Gunicorn runs it using `gunicorn.conf.py`:

| Setting | Value | Note |
|---|---|---|
| `workers` | `2 * cpu_count() + 1` | Gunicorn default formula |
| `timeout` | `0` | No worker watchdog (see Tech Debt) |
| `timeout_keep_alive` | `600` | 10-minute keep-alive for DIOS long requests |
| `max_requests` | `200` (jitter `50`) | Worker recycled after 200 requests — prevents memory leak growth |
| `limit_request_fields` | `32768` | Raised from default (large audience payloads) |
| `bind` | `0.0.0.0:80` | |
| `worker_class` | `uvicorn.workers.UvicornWorker` | ASGI-compatible |

Dockerfile (`Dockerfile`): `FROM python:3.11`, installs requirements, EXPOSE 80/443, CMD `["gunicorn", "main:app"]` (picks up `gunicorn.conf.py` automatically by filename convention).

### Key abstractions

- **`FileHandler` ABC** (`file_handler.py:23`) — interface for all file I/O. Two implementations:
  - `NextcloudFileHandler` — WebDAV via `nextcloud-api-wrapper`. All operations wrapped in `_with_retry` (2 retries). Methods: `ensure_folder_exists`, `upload_file_contents`, `list_folders`, `copy_path`, `delete_path`, `move_path`.
  - `LocalFileHandler` — shutil/pathlib for local debugging only. No network I/O.
  - Swap point: `create_file_handler()` at `main.py:49` — hard-coded to return `NextcloudFileHandler()`. Not env-driven (see Tech Debt).

- **`FileSpecification`** (`file_specification.py:20`) — 12-attribute class defining per-platform transform rules (schema mappings, hash fields, output format flags, size/row limits). Instantiated 17 times in `file_specifications` list (Snapchat=3, Reddit=2, all others=1).

- **`Platform` enum** (`file_specification.py:4`) — 14 values: `viant`, `soapbox`, `google_ads`, `google_dv360`, `meta`, `linkedin`, `tiktok`, `the_trade_desk`, `snapchat`, `reddit`, `x`, `pinterest`, `microsoft_ads`, `amazon_dsp`.

- **`in_progress_uploads: set[tuple[str, str]]`** (`main.py:29`) — per-process guard that rejects duplicate uploads for the same `(netsuite_project, audience_name)` pair with 202. Per-process, not cross-worker (see Tech Debt).

### Request auth

Single shared API key: `x-auth-apikey` header validated against `X_AUTH_APIKEY` env var (`main.py:80`). No per-user auth, no rate limiting.

### Transform pipeline

`format_audience_data` (`main.py:157`) runs as a background task after `/audience/upload` returns 202:

1. Create temp staging path (`{path}_tmp_{timestamp}`)
2. For each `FileSpecification` in `file_specifications`:
   - **Min-row guard**: if `audience` count < `min_row_count`, write `{platform}_ERROR.csv` and skip
   - **Single-column branch** (`is_single_column=True`): build audience1 and/or audience2 DataFrames → hash → filter/rename → concat all columns end-to-end into one column
   - **Multi-column branch**: join audience1 + audience2 DataFrames → hash → `combine_columns` → filter/rename → add `extra_fields` → drop blanks and duplicates
   - Split by `max_row_count` if set
   - Write CSV chunks, splitting further by `file_size_limit_bytes` (hard cap 100 MB per `FILE_SIZE_LIMIT_BYTES`) and `file_count_limit`
   - File naming: `{platform}_{N}.csv` or `{platform}_{suffix}_{N}.csv`
3. Atomic move: rename temp → real destination (deletes existing first)
4. Cleanup lambda removes `upload_key` from `in_progress_uploads`

**Hashing**: SHA256 applied to `hash_fields` values via `hashlib.sha256`. Default `hash_fields=["email"]`. Amazon DSP specifies output-column names in `hash_fields` but hashing runs before renaming — fields may not match at hash time (see Tech Debt).

**`audience2` pivot**: long-form `(RECD_LUID, TYPE, VALUE)` input is pivoted on `TYPE`. Only types present in the spec's `audience2_schema.keys()` are retained — filters out `HARDWARE_TV`, `UID2`, `TTD`, `HEM_MD5` etc.

## Data Flow

### Service-level pipeline

```
DIOS (Fusion92-owned, S3 source)
  → HTTP POST JSON → POST /audience/upload
  → BackgroundTask: format_audience_data
  → Nextcloud DAX_RAW_DoNotUse/<netsuite_project>/<audience_name>/<platform>/*.csv  (staging)
  → (user-triggered via flight-check UI) POST /audience/process
  → BackgroundTask: process_audience_data (copy, no re-transform)
  → Nextcloud DAX/<netsuite_project>/<audience_name>/<platform>/*.csv  (production)
  → consumed by flight-check frontend / DAX ad-platform activation
```

### Upload payload structure

```json
{
  "file_meta": {
    "user": "user@example.com",
    "project": "project_name",
    "audience_name": "audience_123",
    "netsuite_project": "PRJ000123",
    "data_origin": "experian"
  },
  "audience": [
    { "recd_luid": "...", "fnam_fnam": "Jane", "snam_snam": "Doe",
      "addr1": "123 Main St", "city_cnab": "Springfield",
      "stat_abbr": "IL", "recd_zipc": "62701",
      "email": "jane@example.com", "phone": "5550000000" }
  ],
  "audience2": [
    { "RECD_LUID": "...", "TYPE": "HEM_SHA256", "VALUE": "abc123..." }
  ]
}
```

- `audience`: PII rows keyed by `recd_luid` (lowercase)
- `audience2`: long-form triplets `(RECD_LUID, TYPE, VALUE)` — `RECD_LUID` uppercase to match DIOS format; this is intentional, not a bug

**Scale**: up to 1M `audience` rows; `audience2` is larger (multiple TYPE rows per LUID); joined in-memory → up to **60 GB RAM** at target scale.

### Nextcloud folder structure

Two folders drive the pipeline. Both live on **Fusion92's own Nextcloud instance** —
`NEXTCLOUD_HOST=nextcloud.fusion92.net`, under the `aldc` account there:

> **Correction 2026-07-26 (this page previously said "the ALDC Nextcloud instance"):** that
> was wrong and it cost a full investigation lane on FU92-420 — `cloud.aldc.io` was searched
> end to end (admin account, Agent account, `Client_Tenants/FUSION_92`) and found nothing,
> correctly, because the folders were never there. Verified from the service's own
> `/home/aldc/dios-api/env` on `aldcsuptdock1c01`. These folders are **client-owned
> infrastructure**, which matters for access requests and for anything touching retention.

**`DAX_RAW_DoNotUse/` (staging)**
```
DAX_RAW_DoNotUse/
  <netsuite_project>/
    <audience_name>/
      amazon_dsp/  google_ads/  google_dv360/  linkedin/
      meta/  microsoft_ads/  pinterest/  reddit/
      snapchat/  soapbox/  the_trade_desk/  tiktok/
      viant/  x/
```

Populated by `/audience/upload` background task. Also read by `/projects/{project_name}/audiences` to populate the DIOS Audience Name dropdown in [[entities/repos/flight-check|flight-check]].

**`DAX/` (production output)**

Same structure. Populated by `/audience/process` (copy-only, no re-transform). The [[entities/repos/flight-check|flight-check]] UI and DAX ad-platform activation consume files from here.

`DAX_RAW_DoNotUse` env var: `NEXTCLOUD_STAGING_PATH`. `DAX` env var: `NEXTCLOUD_PATH`. Both are Nextcloud-relative paths (not full URLs).

*Source: CF92/1692991495*

### Processed-file naming

- Default: `{platform_value}_{N}.csv` (e.g. `meta_0.csv`, `meta_1.csv`)
- With suffix: `{platform_value}_{suffix}_{N}.csv` (e.g. `snapchat_EMAIL_0.csv`, `reddit_MAID_0.csv`)

## API Reference

All endpoints require `x-auth-apikey` header. Value must match `X_AUTH_APIKEY` env var. Credential: `vault/infra-credentials.md` § Fusion92 — DIOS API.

---

### `POST /audience/upload`

Stages audience data. Returns immediately; heavy processing runs as a background task.

**Request**: `AudienceUploadRequest` — `file_meta` + `audience` list + `audience2` list (see payload structure above).

**Responses**:

| Code | Condition | Body |
|---|---|---|
| 202 | Success — background task queued | `{status, url, parameters, headers, resources: {peak_memory_mb, current_memory_mb, duration_seconds}}` |
| 202 | Upload already in progress for same `(netsuite_project, audience_name)` | `"Upload already in progress"` |
| 400 | `audience` list empty | `"'audience' list is empty."` |
| 400 | Pydantic `ValidationError` | Field names that failed validation |
| 500 | Other exception | Error message + request schema hint |

The `resources` block in the 202 response uses `tracemalloc` (started before, stopped after request parsing) — useful for profiling upload overhead separate from background work.

---

### `POST /audience/process`

Copies staged platform files from `DAX_RAW_DoNotUse` into `DAX`. No re-transform.

**Request**: `AudienceProcessRequest` — `file_meta` (netsuite_project + audience_name) + `platforms: list[Platform]`.

**Responses**:

| Code | Condition |
|---|---|
| 202 | Background copy task queued |
| 404 | Staging path for project/audience doesn't exist |
| 400 | `ValidationError` |
| 500 | Other exception |

If a requested platform's folder is missing from staging, the background task logs the error but **returns normally** — the caller receives no error signal (`# FIXME` at `main.py:408`, `main.py:478`).

---

### `GET /projects/{project_name}/audiences`

Lists audiences for a NetSuite project. Synchronous. Used by [[entities/repos/flight-check|flight-check]] to populate the Audience Name dropdown.

**Response** (200): JSON array of audience folder names under `DAX_RAW_DoNotUse/{project_name}/`. Temp folders (`*_tmp_YYYY-MM-DD_...`) are filtered out.

## Platform Specifications

One row per `FileSpecification` entry. 14 Platform enum values → 17 specs (Snapchat=3, Reddit=2).

Field name abbreviations: `fname`=`fnam_fnam`, `lname`=`snam_snam`, `addr`=`addr1`, `city`=`city_cnab`, `state`=`stat_abbr`, `zip`=`recd_zipc`. `HEM`=`HEM_SHA256`, `MAID`=`HARDWARE_ANDROID_AD_ID`.

| Platform | Suffix | Audience1 inputs | Audience2 inputs | Hash fields | 1-col | No-hdr | Min rows | Max rows | File limit | Combined | Extra fields |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Viant | — | email | HEM | email | ✓ | ✓ | — | — | 100 MB (×10 files) | — | — |
| Soapbox | — | addr, addr2, city, state, zip | — | email | ✗ | ✗ | — | — | 100 MB | — | — |
| Google Ads | — | fname, lname, zip, email, phone | HEM | email | ✗ | ✗ | — | — | 100 MB | — | Country=USA |
| Google DV360 | — | fname, lname, zip, email, phone | HEM | email | ✗ | ✗ | — | — | 100 MB | — | Country=USA |
| Meta | — | email, fname, lname, city, state, zip, phone | HEM, MAID | email | ✗ | ✗ | 100 | — | 100 MB | — | country=USA |
| LinkedIn | — | fname, lname, email | MAID, HEM | email | ✗ | ✗ | — | — | **20 MB** | (email, HEM) | country=USA |
| TikTok | — | phone, email | HEM, MAID | email | ✗ | ✗ | — | — | 1 GB | — | — |
| The Trade Desk | — | email | HEM | email | ✓ | ✓ | — | — | 100 MB | — | — |
| Snapchat | EMAIL | email | HEM | email | ✓ | ✓ | — | — | 1 GB | — | — |
| Snapchat | PHONE | phone | — | (email¹) | ✓ | ✓ | — | — | 1 GB | — | — |
| Snapchat | MAID | — | MAID | (email¹) | ✓ | ✓ | — | — | 1 GB | — | — |
| Reddit | EMAIL | email | HEM | email | ✓ | ✗ | — | — | 1 GB | — | — |
| Reddit | MAID | — | MAID | email | ✓ | ✗ | — | — | 1 GB | — | — |
| X | — | email | HEM | email | ✓ | ✓ | — | — | 100 MB | — | — |
| Pinterest | — | email | HEM | email | ✓ | ✓ | — | — | 100 MB | — | — |
| Microsoft Ads | — | email | HEM | email | ✓ | ✗ | — | **4 M** | 100 MB | — | — |
| Amazon DSP | — | fname, lname, addr, city, state, zip, phone, email | HEM | fname, lname, addr, city, state, zip, phone² | ✗ | ✗ | — | **5 M** | 1 GB | (email, HEM) | — |

**Notes:**
1. Snapchat PHONE and MAID specs default `hash_fields=["email"]` but output no email column — hash is effectively a no-op for these specs.
2. Amazon DSP `hash_fields` list uses **output column names** (`first_name`, `last_name`, etc.) but hashing runs before `filter_and_rename_dataframe_columns` — these names don't exist in the DataFrame at hash time. Fields are likely output un-hashed. This is a suspected bug (see Tech Debt).

**Call-outs:**
- LinkedIn `file_size_limit_bytes=20_000_000` — smallest per-file limit, most likely to split large audiences.
- Viant `file_count_limit=10` — hard cap on output file count regardless of size.
- Meta `min_row_count=100` — audiences below 100 rows produce an error file instead of output.
- All file limits are capped at 100 MB by `FILE_SIZE_LIMIT_BYTES` constant even if spec sets higher — exception: TikTok/Snapchat/Reddit/LinkedIn/Amazon DSP set per-spec limits that override the cap (the code uses `min(file_size_limit_bytes, FILE_SIZE_LIMIT_BYTES)` — so 1 GB specs are still capped at 100 MB).

Source: `file_specification.py:124–354`.

## Developer Guide

### Prerequisites

- Python 3.11+
- pip
- Docker (optional — for production-parity testing)
- Nextcloud credentials (`NEXTCLOUD_HOST`, `NEXTCLOUD_USER`, `NEXTCLOUD_PASSWORD`) — or swap to `LocalFileHandler` for local-only testing
- API key (`X_AUTH_APIKEY`) — value in `vault/infra-credentials.md` § Fusion92 — DIOS API

### Setup

```bash
git clone https://github.com/ALDC-io/custom-fusion-92-audience-api
cd custom-fusion-92-audience-api
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

Create `.env` in the project root:

```env
NEXTCLOUD_HOST=cloud.example.com
NEXTCLOUD_PATH=DAX
NEXTCLOUD_STAGING_PATH=DAX_RAW_DO_NOT_USE
NEXTCLOUD_USER=your_user
NEXTCLOUD_PASSWORD=your_password
X_AUTH_APIKEY=your_api_key
```

Values for the ALDC production instance: `vault/infra-credentials.md` § Fusion92 — DIOS API and `vault/infra-credentials.md` § NextCloud.

### Running locally

**Dev server (with Nextcloud):**
```bash
uvicorn main:app --reload
```

**Docker:**
```bash
docker build -t dios-api .
docker run -p 80:80 --env-file .env dios-api
```

### Local-only mode (no Nextcloud)

Edit `main.py:49` — change `return NextcloudFileHandler()` to `return LocalFileHandler()`. Files will be written to local paths derived from `NEXTCLOUD_STAGING_PATH` and `NEXTCLOUD_PATH` env vars. Remember to flip back before committing — this is code-level, not env-controlled.

### Smoke testing

1. Generate a sample payload: `python generate_sample_file.py` (edit `row_count` inside the script to control size). Writes `dios_audience.json`.
2. Edit URL at `client/client.py:8` to point at your local instance (`http://localhost:8000/audience/upload` or the on-prem URL).
3. Run: `python client/client.py` — reads `client/dios_audience.json` and POSTs it.

For large-payload testing (>10k rows), use `client/client.py` — Postman/Bruno time out on large payloads.

### Debugging

- Logs to `uvicorn.error` logger. Background task errors appear after the 202 response.
- `/audience/upload` 202 body includes `tracemalloc` stats (`peak_memory_mb`, `current_memory_mb`, `duration_seconds`) for profiling request parsing overhead.
- `/audience/process` silent failures: check server logs for the error JSON logged by `process_audience_data`.

### Common pitfalls

| Pitfall | Detail |
|---|---|
| Forgot to flip `create_file_handler` back | `main.py:49` always returns NextcloudFileHandler in production. After local testing with LocalFileHandler, revert before pushing. |
| Per-worker `in_progress_uploads` | With multiple Gunicorn workers, the same `(netsuite_project, audience_name)` can be uploaded concurrently from different workers — deduplication is best-effort. |
| Nextcloud 100 MB write cap | `NextcloudFileHandler.write_file` uploads the whole file in one request. `FILE_SIZE_LIMIT_BYTES` (100 MB) handles chunking, but verify actual Nextcloud instance limit. |
| `recd_luid` vs `RECD_LUID` case | `audience` uses lowercase `recd_luid`; `audience2` uses uppercase `RECD_LUID`. Matches DIOS source format — don't "fix" either. |
| `/audience/process` returns 202 even on partial failure | If a platform's staging folder doesn't exist, the background task logs the error and exits silently. No 4xx/5xx is returned. |

## Deployment

### Infrastructure

| Component | Detail |
|---|---|
| Host | Support Docker host (on-prem) |
| Reverse proxy | Nginx — TCP port-forward to container port 80. Request timeout **maxed out** (DIOS requests take 2–5 minutes) |
| DNS | [[Cloudflare]] — maps `audience-fusion92-app.aldc-ca-w1.com` to public IP. **Cloudflare proxying is disabled** for this hostname — Cloudflare's timeout cap would be exceeded by DIOS requests |
| Container port | 80 (Gunicorn bind `0.0.0.0:80`) |
| Production URL | `https://audience-fusion92-app.aldc-ca-w1.com/` |

See [[local-network]] for the Nginx reverse-proxy setup and [[aldc-naming-convention]] for hostname conventions.

### Image build

```bash
docker build -t dios-api .
```

Dockerfile summary: `FROM python:3.11` → install requirements → COPY source → EXPOSE 80/443 → CMD `["gunicorn", "main:app"]`.

### Running on the host

```bash
docker run -d \
  -p 80:80 \
  --env-file /path/to/.env \
  --restart unless-stopped \
  dios-api
```

Env vars must include all 6 values in the `.env` setup table above. Values in `vault/infra-credentials.md` § Fusion92 — DIOS API.

### No CI/CD — partially wrong, corrected 2026-07-26

There is no `.github/` directory in this repo and **no automated tests gate deploys**, but
images are *not* built by hand on the host. The actual deploy script at
`/home/aldc/dios-api/run.sh` on `aldcsuptdock1c01` pulls a **pre-built image from GHCR**:

```bash
sudo docker run --restart unless-stopped -d --name=dios-api-$1 \
  -p 7000:80 --env-file=./env ghcr.io/aldc-io/dios-api:$1
```

So: images are built and published to `ghcr.io/aldc-io/dios-api` and tagged; only the
**deploy step** is manual (`./run.sh <tag>`). Container naming is `dios-api-<tag>`, host port
**7000** — which is the NPM proxy target for `audience-fusion92-app.aldc-ca-w1.com`.

Rollback is therefore `./run.sh <previous-tag>`, not a rebuild from source.

**Logging consequence (matters for any usage-analysis work — see FU92-420):** `run.sh`
passes **no `--log-opt`**, so the container uses the default `json-file` driver with **no
rotation**. The log is unbounded and survives for the container's lifetime, which means
available log history equals *time since the container was last recreated* — it is not
truncated by a retention policy. Recreating the container destroys all of it.

No staging slot.

### Rollback

Rebuild image from the prior commit and restart the container. No blue/green, no slot swap. Rollback is a `git checkout <prev-sha>` + rebuild.

### No staging environment

Single production deployment only. This differs from [[core_api]], [[entities/repos/eclipse|eclipse]], and [[eclipse_exp]], all of which use Azure staging slots. There is no test/QA environment to validate changes before production.

## Why on-prem (not cloud)

The architecture is memory-heavy and non-streaming:

- Each request loads the full audience dataset into memory (no chunking)
- Two datasets are joined in-memory with pandas DataFrames (doubles the footprint)
- At target scale (~1 M audience rows), requests need up to **60 GB RAM**
- Response times of 2–5 minutes exceed most managed cloud services' request-timeout caps

On-prem works because ALDC controls the server, so memory sizing and timeouts can be tuned freely.

## Path to cloud-hosting (open)

Cloud-hosting would require re-architecting to remove the in-memory-join constraint. One possible direction:

1. Move the audience-data join out of pandas and into a database (e.g. [[Snowflake]])
2. Generate the per-platform formatted outputs as tables/views, streamed or chunked out to Nextcloud rather than held in memory
3. Stream or chunk incoming request data into the database instead of loading full payloads

Blocker: this changes DIOS's contract with the API. Fusion92 would need to agree to the interface change.

## DIOS → DAX Integration Specification

*Source: CF92/1364688898 (meeting 2024-09-05)*

Defines the API contract between DIOS (Fusion92's internal audience web app) and the DAX REST API.

### Data Transfer

- **Source:** DIOS audience data from S3 buckets
- **Transport:** JSON POST to DAX REST API endpoint (JSON preferred over CSV — allows metadata)
- **Payload fields:** LUID (DAX ID), first name, last name, city, state, zip, email, project info, audience name
- **Response:** Job ID for async processing; optionally report match rate back to DIOS

### Phase 1 (September 2024)

- Match individual audiences as received (e.g., 10,000 records at a time)
- DAX matches to Viant IDs internally before pushing to Viant DSP
- F92 manually runs campaigns using uploaded audiences in Viant
- Goal: quick delivery (service request due 2024-09-19)

### Phase 2 (Future)

- Monthly full DAX dataset matching (focus on changed records)
- [[Snowflake]] implementation + full infrastructure build-out

### Client Separation

JSON keys or folder structure provide sufficient client separation (e.g., Ford vs. Outcomes). DAX handles internal filtering.

### Key Clarifications

- Viant audience upload is automated by DAX — F92 does not manually place audiences in Viant DSP.
- Full Snowflake architecture is a later phase; Phase 1 prioritizes quick delivery.

*See [[fusion92-data-architecture]] § Snowflake-Centric Architecture Shift for the strategic context behind the Phase 2 direction.*

## Open questions

### Is the `aldc` account the only Nextcloud holder of DAX folders?

*Raised 2026-07-28 during FU92-420. Unverified — parked, not blocking.*

The DIOS service authenticates to `nextcloud.fusion92.net` as `NEXTCLOUD_USER=aldc`, and any
enumeration of audience storage therefore sees only that account's view. **If another account on
that instance holds its own `DAX` / `DAX_RAW_DoNotUse` folders, those audiences are invisible to
us.** This is the one unexamined route to higher usage volume than FU92-420 measured (114
conversions, of which 8 genuine campaign audiences).

Question for Fusion92 when convenient: *does any account other than `aldc` hold DAX audience
folders?* Answering it from our side needs admin visibility on their Nextcloud instance.

Two lesser gaps in the same category: the documented **90-day retention** (per Dave Nugent) is
demonstrably not running — folders from March 2025 survive — but if it ever ran, older audiences
are gone; and audiences **deleted manually** leave no trace.

### Ruled out — do not re-investigate

Volume looking low prompted a reasonable suspicion that a *test* environment had been measured
instead of production. It had not:

- **Single deployment only.** See § *No staging environment* below. One DIOS container, on the
  only publicly-exposed host; none on `wks-agent`, `aldcproddock1c01` or `aldcproddock1c03`;
  the live service config points at the production Nextcloud host and paths.
- **Test project names in production storage are expected, not anomalous.**
  [[entities/repos/flight-check|flight-check]] runs two environments — prod
  `dax.fusion92.eclipse.aldc.io` and QA `dax.fusion92.eclipse.aldc-ca-w1.com` — and both proxy
  DIOS through a single `DIOS_API_URL`. With only one DIOS deployment they necessarily address the
  same instance, so **QA activity writes into production storage.** That is why scratch names
  (`zzz`, `asdf`, `wizard_test_7`) sit alongside real campaign audiences.
- **Low volume matches the documented maturity.** Phase 1 was quick-delivery with Fusion92
  running campaigns manually, and [[fusion92-data-architecture]] records the DIOS→DAX integration
  as *"paused 2–3 weeks (client priorities)"*. A pilot that never scaled.

> **Corollary worth remembering:** folder *existence* in this storage is not evidence of usage —
> both the QA environment and a since-fixed create-on-read defect produced folders. Count
> per-platform output subfolders instead.

---

## Tech Debt / Known Issues

| Issue | Detail |
|---|---|
| **Committed API key** | `client/client.py:16` contains the production `X_AUTH_APIKEY` value committed in plaintext to git history. Key extracted to `vault/infra-credentials.md` § Fusion92 — DIOS API. **Rotate the key** and refactor `client.py` to read from env var. |
| Per-process `in_progress_uploads` | `main.py:29` — per-process set, not shared across Gunicorn workers. Duplicate-upload rejection is best-effort only. |
| `gunicorn timeout=0` | `gunicorn.conf.py:8` — no worker watchdog. A hung worker stays hung indefinitely. Consider a non-zero timeout. |
| `/audience/process` silent failures | `process_audience_data` logs errors but returns normally. Missing platform staging data is silently ignored. `# FIXME` comments at `main.py:408` and `main.py:478`. |
| `create_file_handler()` hard-coded | `main.py:49` always returns `NextcloudFileHandler()`. Should be env-driven (e.g., `USE_LOCAL_HANDLER=true`) to enable local testing without code edits. |
| Amazon DSP hash timing bug | `hash_fields` for Amazon DSP uses output column names (`first_name`, etc.) but hashing runs before `filter_and_rename_dataframe_columns` — column names don't exist at hash time. Fields are likely output un-hashed. |
| No test suite | `client/client.py` is a manual smoke-test script, not an automated test. No pytest, no unit tests, no contract tests against DIOS. |
| No CI/CD | No `.github/` directory. All builds and deploys are manual steps on the host. |
| No `.env.template` | Env var documentation lives in `README.md` only. A committed `.env.template` with placeholder values would reduce onboarding friction. |

## See Also

- [[fusion92]] — client this API serves
- [[entities/repos/flight-check|flight-check (repo)]] — Next.js frontend that calls this API for `/projects/{project_name}/audiences` (audience dropdown) and `/audience/process` (Process Audience button)
- [[dax-media-app]] — the product this API is a backend for. Product-scope context (roles, statuses, Phase 2) lives there.
- [[Cloudflare]] — DNS (with proxying disabled) for the public hostname
- [[Snowflake]] — candidate database for the cloud-redesign (Phase 2)
- [[nextcloud]] — file storage for `DAX_RAW_DoNotUse` and `DAX` folders
- [[flight-check]] — ALDC operational runbook (NOT this repo — different thing with similar name)
- [[fusion92-data-architecture]] — DIOS→DAX→DSP architecture + Snowflake migration strategy
- [[local-network]] — on-prem Nginx reverse proxy + Tailscale that host this service
- [[aldc-naming-convention]] — naming conventions that apply to the service hostname
