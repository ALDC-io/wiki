---
tags: [process, operations, eclipse, portal, users, auth, test]
aliases: [eclipse-test users, portal user provisioning, eclipse-test.aldc.io login, app_user]
sources: [conversation 2026-07-09 (dev-team eclipse-test user provisioning), aldc-launchpad/scripts/_investigate_portal.py, core_api api/users/lib.pyc]
created: 2026-07-09
updated: 2026-07-09
---

# Eclipse TEST — User Provisioning & the Two Identity Stores

How to create / mirror users for the **`eclipse-test.aldc.io`** portal, and the
non-obvious trap that nearly caused a wrong-store deploy: **two different user
stores exist with near-identical field shapes**. Establish which one the login
surface actually reads *before* touching anything (see [[confirm-consumer-source]]).

## The two stores (do not confuse them)

| | **Eclipse portal** (`eclipse-test.aldc.io`) | **v2 Eclipse SPA** (`eclipse-exp.aldc.io`) |
|---|---|---|
| App | Legacy Next.js/Django portal ([[entities/repos/eclipse\|eclipse repo]]) | Next-gen platform ([[eclipse_exp]]) |
| Backend | [[core_api]] + **PostgreSQL** | [[core_api]] + **CosmosDB** |
| User store | Postgres **`app_user`** table | Cosmos **`user`** container |
| Password hash | stock Django `pbkdf2_sha256$720000` | custom `pbkdf2_sha256$1500` (`api/users/lib.generate_hash_password`) |
| Reachable off-VPN? | **Yes** (Cloudflare, public) | **No** — office-VPN-gated |
| DB | `aldctestpgdbportal1c01` / db `eclipse` (creds → [[credentials#eclipse-portal-postgres-test\|vault]]) | `aldctestcsdb1c01` / db `core` |

Both have `email`, `is_active`, `is_staff`, `is_superuser`, `active_account`,
`is_approver`… — **matching column names, different consumers**. Editing Cosmos
does **not** affect `eclipse-test.aldc.io` logins (proven 2026-07-09: 5 users
provisioned in Cosmos, live login still failed; redone in Postgres `app_user`,
all 5 logged in). The Cosmos `auth_user` container is just OAuth *clients*, not people.

**Discriminating test** (which store does a login read?): the portal login page is a
Django form (`email` + `password` + `csrfmiddlewaretoken`); a real login attempt that
returns `Invalid credentials` while the user *is* correctly set up in a candidate store
means that store is not the one being read. Confirm the target user exists in Postgres
`app_user` (`SELECT … WHERE lower(email)=…`), not just in Cosmos.

## Portal schema (Postgres `eclipse`)

- **`app_user`** — Django user. NOT-NULL: `password, email, first_name, last_name,
  date_joined, is_active, is_staff, is_superuser, is_approver, is_requester,
  department, role, is_beta_tester, is_data_expert, is_allowed_pdf_download`.
  Nullable: `active_account_id, manager_id, last_login`. PK `id` (seq), UNIQUE `email`.
- **`app_account_users`** (`account_id`→`app_account.id`, `user_id`) — account access, UNIQUE(account_id,user_id).
- **`app_user_groups`** (`user_id`, `group_id`→**`app_group.id`**) — report-visibility groups (NOT `auth_group`, which is empty).
- **`app_userextension`** (`authority`, `user_id`) — e.g. `USER_AUTH_REGULAR`.
- **`app_account`** ids: **13**=ALDC Library, **18**=Fusion92, **19**=GEP ([[GEP]]/Navira, `da8904db`), **20**=ALDC Engineering.

## Runbook — mirror a user's access onto new users

1. **Confirm the target store** (above). For `eclipse-test.aldc.io` it is Postgres `app_user`.
2. **Read the template user's full graph** (e.g. Paul = `app_user` id 113): the mirrored
   config columns + `app_account_users` rows + `app_user_groups` rows + `app_userextension.authority`.
3. **Plan-then-apply, in one transaction, with rollback capture** (Paul's evidence gate):
   INSERT `app_user` (hash the shared temp password with Django `pbkdf2_sha256$720000`)
   → INSERT `app_account_users` for each template account → INSERT `app_user_groups` for
   each template group → INSERT `app_userextension`. Save created `id`s; rollback = delete them.
4. **Password**: `pbkdf2_sha256$<720000>$<22-char base62 salt>$<b64(pbkdf2_hmac('sha256',pw,salt,720000))>`.
   Reproduce with `hashlib` (validated == a real login) or Django's `make_password`.
5. **Validate at the consumer** — a real login POST to `https://eclipse-test.aldc.io/login/`
   (GET first for the `csrftoken` cookie + `csrfmiddlewaretoken`; POST with `Referer`).
   Success = **302 → `/` + `sessionid` cookie**. Run a wrong-password control (must stay 200
   "Invalid credentials") to prove the password is actually being checked.
6. **First-login password reset**: portal login page → **"Forgot Password?"** → `/password_reset/`
   (public Django reset form). No enforced first-login reset flag exists — it's by instruction.

> ⚠️ **Security debt:** the portal Postgres admin creds are **hard-coded** in committed repo
> scripts `aldc-launchpad/scripts/_investigate_portal.py` and `_add_portal_report_row.py`.
> Recorded in [[credentials#eclipse-portal-postgres-test\|the vault]]; should move to Key Vault.

## 2026-07-09 — dev-team provisioning (record)

Created 5 users in `app_user` (ids 123–127) mirroring Paul **exactly** incl.
`is_superuser`+`is_staff` (approved) — active_account 19 (GEP), accounts 13/18/19/20,
groups 10/13/15/16/17 (incl. 17=GEP Dev): **vlad.ryzhkov, mike.stuart, lori.beck,
tamoor.zahid, lingjun.zhou** @aldc.io. Shared temp password, all 5 login-verified live
(302 + session), wrong-password control failed as expected. First (mistaken) attempt
provisioned Cosmos `user` — rolled back cleanly once the live login proved the portal
reads Postgres.

## See Also

- [[Eclipse]] · [[eclipse_exp]] · [[entities/repos/eclipse|eclipse (repo)]] · [[core_api]] · [[CosmosDB]]
- [[confirm-consumer-source]] — prove which object a consumer reads before deploying
- [[eclipse-incident-response]] · [[eclipse-2.1-editor-performance]]
- [[credentials#eclipse-portal-postgres-test|Vault: eclipse portal Postgres (test)]]
