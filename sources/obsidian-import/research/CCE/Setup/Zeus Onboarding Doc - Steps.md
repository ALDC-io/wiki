Onboarding doc is updated with Paul's info. Here's what he needs:  
  
**His Zeus API Key:** `<REDACTED — Zeus Memory API key; see vault/infra-credentials.md § Zeus Memory / CCE — Learnings API (zeus.aldc.io)>`  
**Tenant ID:** `c1234567-0000-0000-000a-000000000001`  
  
**Quick Setup (5 min):**  
1. Create `~/.env` — pull from Dashlane (`CCE Team Env` note) or manually add:  
  

   ZEUS_API_URL=[https://zeus.aldc.io](https://zeus.aldc.io)
   ZEUS_ALDC_API_KEY=<REDACTED — Zeus Memory API key; see vault/infra-credentials.md § Zeus Memory / CCE — Learnings API (zeus.aldc.io)>
   

2. Install auto-updater:  
  

   mkdir -p ~/.claude/hooks
   gh api repos/ALDC-io/zeus-memory/contents/scripts/cce-hooks-updater.py --jq .content | base64 -d > ~/.claude/hooks/cce-hooks-updater.py
   chmod +x ~/.claude/hooks/cce-hooks-updater.py
   

3. Copy the settings.json from the onboarding doc  
4. Run: `source ~/.env && python3 ~/.claude/hooks/cce-hooks-updater.py`  
5. Start Claude Code — should see `[CCE] Online: paul ...`  
Full doc: `/home/aldc/.claude/TEAM_ONBOARDING.md`