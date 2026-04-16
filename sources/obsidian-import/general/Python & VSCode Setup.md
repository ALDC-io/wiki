
# Engineer Onboarding Guide

This guide walks through the full local setup process for the Connector repositories, including Python environment setup, dependency management, Git hygiene, and Snowflake connectivity. Follow the steps in order for the smoothest experience.

---

# 1. Prerequisites

Ensure the following are installed:

- Git
    
- Python 3.12 (recommended for this repo)
    
- VS Code
    
- VS Code Python extension
    
- Access to Snowflake (non‑prod via SSO)
    

Verify versions:

```bash
git --version
python --version
```

---

# 2. Clone the Repository

```bash
git clone <repo-url>
cd connector
```

Confirm branch:

```bash
git status
```

---

# 3. Create Local Virtual Environment

Create the project venv inside the repo root:

```bash
python -m venv .venv
```

Activate it.

### Git Bash

```bash
source .venv/Scripts/activate
```

### PowerShell

```powershell
.venv\Scripts\Activate.ps1
```

You should see `(.venv)` in your prompt.

---

# 4. Upgrade Core Build Tooling (IMPORTANT)

Before installing requirements:

```bash
python -m pip install --upgrade pip setuptools wheel
```

This prevents many build failures.

---

# 5. Install Dependencies

## ⚠️ Known Issue: pyarrow

The repo currently pins:

```
pyarrow==5.0.0
```

This version **does NOT support Python 3.12** and will fail to build from source.

### Recommended workaround

Use the modified requirements file (without pyarrow):

```bash
pip install -r requirements-no-pyarrow.txt
```

If pyarrow is required later, coordinate with the team to upgrade to a Python‑3.12‑compatible version.

---

# 6. Verify Environment

Quick smoke test:

```bash
python -c "import pandas, numpy; print('env ok')"
```

---

# 7. Git Hygiene (VERY IMPORTANT)

## 7.1 Ensure `.venv` is ignored

Your `.gitignore` should include:

```
.venv/
venv/
__pycache__/
*.pyc
```

✅ This prevents thousands of local files from appearing in source control.

## 7.2 If you previously saw many changes

That happens when the virtual environment is not ignored.

Fix steps (already completed in this setup):

```bash
git add .gitignore
git commit -m "Ignore .venv local virtual environment"
```

Verify clean status:

```bash
git status
```

Expected: only real source changes appear.

---

# 8. Environment Variables

Create a `.env` file in the repo root (already git‑ignored):

```
SNOWFLAKE_ACCOUNT=og35375.canada-central.azure
SNOWFLAKE_USER=PAULRUSSELL
SNOWFLAKE_ROLE=SYSADMIN
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_TOKEN=<if using PAT>
```

Load in Python via:

```python
from dotenv import load_dotenv
load_dotenv()
```

---

# 9. Snowflake Access (Current State)

## ✅ What works

- Web login via SSO
    
- MFA authentication
    
- Account confirmed:
    
    - Account: `OG35375`
        
    - Region: `AZURE_CANADACENTRAL`
        
    - Role: `SYSADMIN`
        
    - Warehouse: `COMPUTE_WH`
        

## ❌ What currently fails

The following methods encountered issues in this environment:

### VS Code Snowflake Extension

Observed errors:

- `Cannot read properties of null (reading 'proofKey')`
    
- `Cannot read properties of null (reading 'ssoUrl')`
    
- Hostname certificate mismatch
    
- No active Snowflake session
    

**Likely cause:** enterprise SSO configuration + extension incompatibility.

---

### Python Connector — External Browser SSO

Error observed:

```
390190 (08001): There was an error related to the SAML Identity Provider account parameter
```

Meaning:

- Snowflake account is SSO‑enabled
    
- Programmatic SSO flow is restricted or misconfigured
    
- Connector cannot complete IdP handshake
    

This is **not a local setup problem**.

---

### Python Connector — Programmatic Access Token (PAT)

Issues observed:

- Invalid OAuth token
    
- Okta tokenUrl NoneType error
    
- Network policy warning
    

Interpretation:

- Token generation works
    
- Account network policy or IdP integration blocks connector usage
    

Requires Snowflake admin confirmation.

---

# 10. Recommended Working Approach (For Now)

Until Snowflake programmatic access is clarified:

## Use SnowSQL for execution (when needed)

SnowSQL supports enterprise SSO more reliably.

Example:

```bash
snowsql -a og35375.canada-central.azure -u PAULRUSSELL --authenticator externalbrowser
```

This should open the browser and complete MFA.

---

# 11. VS Code Setup

## Recommended extensions

- Python
    
- Pylance
    
- Snowflake (optional — may have auth issues)
    

## Interpreter

Select the project interpreter:

```
.venv\Scripts\python.exe
```

---

# 12. Project Sanity Checklist

Before starting real tickets, confirm:

-  Repo clones successfully
    
-  `.venv` activates
    
-  Requirements install (using no‑pyarrow file)
    
-  `.env` loads
    
-  Basic Python imports work
    
-  Git status is clean
    
-  Snowflake web login works
    

---

# 13. Open Issues / Follow‑ups

## 🔴 High Priority

### 1. pyarrow version

- Current pin incompatible with Python 3.12
    
- Team should upgrade to modern version
    

---

### 2. Snowflake programmatic access

Needs clarification from platform team:

- Is externalbrowser allowed for connectors?
    
- Are PATs supported for Python connector?
    
- Is key‑pair auth preferred?
    
- Is OAuth integration required?
    
- What network policy is required?
    

---

### 3. VS Code Snowflake Extension

Currently unreliable due to:

- proofKey null errors
    
- ssoUrl null errors
    
- certificate hostname mismatches
    

Likely causes:

- Enterprise SSO configuration
    
- PrivateLink / network policy
    
- Extension limitations
    

**Recommendation:** do not block development on the extension.

---

# 14. Next Steps for New Engineers

After completing this guide:

1. Pull latest main
    
2. Confirm environment checklist
    
3. Start first ticket
    
4. Coordinate with platform team on Snowflake auth path
    

---

**End of Guide**