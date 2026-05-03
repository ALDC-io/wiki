---
tags: [concept, pattern, snowflake, provisioning, infrastructure, automation]
aliases: [Snowflake provisioning, idempotent Snowflake setup]
sources: [tickets/gep/GP-248.md, prefect-connectors/scripts/provision_gep_prefect.py]
created: 2026-05-02
updated: 2026-05-02
---

# Snowflake Environment Provisioning Pattern

A reusable pattern for scripting idempotent Snowflake environment setup — databases, schemas, roles, users, and grants — via Python. Extracted from [[GP-248]] (Prefect GEP environment isolation).

## The Pattern

```python
# Core ingredients of a good provisioning script
import argparse, getpass, secrets, string, snowflake.connector

# 1. Configurable role (default SYSADMIN; use ACCOUNTADMIN when needed)
parser.add_argument("--role", default="SYSADMIN")

# 2. Configurable target (nonprod / prod / all) — run one half at a time
parser.add_argument("--target", choices=["nonprod", "prod", "all"])

# 3. --dry-run flag — prints SQL without executing
parser.add_argument("--dry-run", action="store_true")

# 4. Password via getpass — never hardcoded; prompts interactively
password = getpass.getpass(f"Password for {user}: ")

# 5. Idempotent SQL — IF NOT EXISTS everywhere
"CREATE DATABASE IF NOT EXISTS {db} CLONE {source}"
"CREATE ROLE IF NOT EXISTS {role}"
"CREATE USER IF NOT EXISTS {user} ..."

# 6. Graceful error handling — "already exists" is OK
except snowflake.connector.errors.ProgrammingError as e:
    if "already exists" in str(e).lower():
        print(f"  --  {label} (already exists)")
    else:
        raise

# 7. Password generation — 24 chars, upper+lower+digit+special
def generate_password(length=24):
    alphabet = string.ascii_letters + string.digits + "!@#$%^*"
    ...
```

Reference implementation: `prefect-connectors/scripts/provision_gep_prefect.py`

---

## Snowflake Role Hierarchy (Canada accounts)

| Role | Can do | Cannot do |
|---|---|---|
| SYSADMIN | CREATE DATABASE, CREATE SCHEMA, CREATE WAREHOUSE | CREATE ROLE, CREATE USER |
| USERADMIN | CREATE ROLE, CREATE USER | CREATE DATABASE |
| SECURITYADMIN | CREATE ROLE, CREATE USER, GRANT | CREATE DATABASE |
| ACCOUNTADMIN | Everything | — |

**Key gotcha:** SYSADMIN and USERADMIN/SECURITYADMIN are siblings under ACCOUNTADMIN — they do NOT inherit each other. A script that creates databases AND roles/users needs ACCOUNTADMIN, or must switch roles mid-execution (not supported in a single connection). Practical solution: add a `--role` flag and document which role is needed for which operations.

**Prod wj66376 specifics (2026-05-02):**
- `paulrussell` → SYSADMIN only
- `PROD_DG1_CORE_ADMIN` → ACCOUNTADMIN ✅ (use for CREATE ROLE/USER on prod)

**Non-prod og35375 specifics:**
- `paulrussell` → SYSADMIN (sufficient for most setup)
- `TEST_DG1_CORE_ADMIN` → USAGE role only (not useful for provisioning)

---

## Standard Grant Set for a Service Account Database

```sql
GRANT USAGE ON DATABASE {db} TO ROLE {role};
GRANT CREATE SCHEMA ON DATABASE {db} TO ROLE {role};
GRANT ALL PRIVILEGES ON ALL SCHEMAS IN DATABASE {db} TO ROLE {role};
GRANT ALL PRIVILEGES ON FUTURE SCHEMAS IN DATABASE {db} TO ROLE {role};
GRANT ALL PRIVILEGES ON ALL TABLES IN DATABASE {db} TO ROLE {role};
GRANT ALL PRIVILEGES ON FUTURE TABLES IN DATABASE {db} TO ROLE {role};
GRANT ALL PRIVILEGES ON ALL VIEWS IN DATABASE {db} TO ROLE {role};
GRANT ALL PRIVILEGES ON FUTURE VIEWS IN DATABASE {db} TO ROLE {role};
GRANT ALL PRIVILEGES ON ALL STAGES IN DATABASE {db} TO ROLE {role};
GRANT ALL PRIVILEGES ON FUTURE STAGES IN DATABASE {db} TO ROLE {role};
GRANT ALL PRIVILEGES ON ALL FILE FORMATS IN DATABASE {db} TO ROLE {role};
GRANT ALL PRIVILEGES ON FUTURE FILE FORMATS IN DATABASE {db} TO ROLE {role};
```

Stages and file formats are required for Prefect connectors (COPY INTO pipeline).

---

## Running in Git Bash

Always use forward-slash paths — backslash paths silently fail:

```bash
# CORRECT
cd /c/Users/PaulRussell/repos/prefect-connectors
python scripts/provision_gep_prefect.py --target nonprod

# WRONG — silent "no such file" error
cd C:\Users\PaulRussell\repos\prefect-connectors
```

Scripts using `getpass` require an interactive terminal. Use the `!` prefix in Claude Code to run in Paul's terminal session where password entry works.

---

## Utility Scripts

All in `prefect-connectors/scripts/`:

| Script | Purpose |
|---|---|
| `provision_gep_prefect.py` | Main GP-248 provisioning (databases + service accounts) |
| `check_grants.py` | Inspect all grants for a Snowflake user |
| `reset_passwords.py` | Reset service account passwords and print new values |
| `create_pbi_workspaces.ps1` | Create PBI workspaces via PowerShell module |

---

## See Also

- [[GP-248]] — where this pattern was established
- [[sandbox-feature-delivery]] — per-feature schema isolation pattern
- [[Prefect]] — GEP Prefect databases and service account table
- `vault/infra-credentials.md` § Prefect Service Accounts — passwords for GEP accounts
