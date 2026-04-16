### 1. `projects/` directory map

| Bucket                   | Contents                                                                                                                             | Notes                                                                                                              | Recommendation                                                                                                                             |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------ |
| **Active workspaces**    | `2026-03-11-ecommerce-commission-engine/PROJECT_PLAN.md`, `2026-03-12-jira-live-pipeline/{PROJECT_PLAN,PROGRESS,UNMAPPED_FIELDS}.md` | Live project plans plus journaling; only two folders are marked “ACTIVE.”                                          | Move these into per-user workspaces (e.g., `~/.cce/projects/<id>`) before shipping releases, and treat Git history here as reference only. |
| **Historical/Completed** | `projects/completed/` holds ~17 dated folders (Dec 2025 – Mar 2026) plus `test_template_system`.                                     | Valuable knowledge base, but it bloats the runtime repo and forces everyone to pull someone else’s client history. | Export to a “CCE Operations Archive” repo or Confluence/Notion; leave behind read-only snapshots or compressed archives.                   |
| **Templates & Ops docs** | `CLAUDE_CODE_PROJECT_TEMPLATE.md`, `client_work_pipeline.md`, `WORK_DIVISION_STRATEGY.md`, `ZEUS_*` specs, etc.                      | Mixed with live notes; no clear separation between canonical templates vs. ad-hoc notes.                           | Promote templates into a dedicated `docs/templates/` (versioned with releases). Push ops memos into a knowledge base or Zeus memory.       |
| **Backups**              | `backups/affine_backup_20251223.sql`                                                                                                 | Full SQL dump committed to source; risky.                                                                          | Remove from git, store in secure object storage, reference via signed URL.                                                                 |

**Conclusion:** treat `projects/` as user data, not product code. Extract it before packaging, then add CLI commands (`cce projects pull/push`) that sync to Zeus/S3.

---

### 2. `.claude/skills/` snapshot

- **Scope**: 45 top-level categories (~190 skill files) plus `.archived/` and governance docs (`SKILLS_INDEX.md`, `skills_index.json`, `SKILL_TEMPLATE.md`, `EXTERNAL_SKILLS.md`).
- **Patterns noticed**:
    - Categories mix runtime-critical skills (`cce/*`, `zeus-memory/*`, `system/*`) with customer-specific playbooks (`affine/`, `analytics-labs/`, `profitability/`).
    - No semantic versioning or manifest enforcement—skills are markdown files with freeform headers; nothing ensures they’re consistent or tested before being committed.
    - `.archived/` exists but the launcher still ships it, so old guidance remains accessible to every user.
    - Some skills reference code paths directly (e.g., `.claude/skills/zeus-memory/zeus-memory-knowledge-synchronizer.md` cites `tools/context7_handler.py`), meaning stale skills could point to code that’s been removed.

**Suggested actions**:

1. Split skill bundles:
    - **Core** (ships with installer): `system`, `zeus-memory`, `cce`, `security`, `testing`, `workflow`, `hooks`.
    - **Optional packs**: customer-specific categories distributed via ZIPs or `cce skills add`.
2. Introduce a manifest schema (e.g., `skills/index.yaml`) with `name`, `version`, `category`, `checksum`, `min_cce_version`.
3. Enforce intent: `cce` should only sync new skills into `~/.cce/skills`; the repo holds signed releases, not the writable source of truth.
4. Archive/retire categories like `affine/`, `analytics-labs/` into a separate “customer runbook” repo so non-relevant users don’t see them.

---

### 3. `tools/` breakdown

|Tier|Files|Purpose|Notes|
|---|---|---|---|
|**Critical path**|`cce_cli.py`, `template_engine.py`, `git_integration.py`, `zeus_integration.py`, `skill_discovery.py`, `skill_generator.py`, `workflow_executor.py`, `parallel_executor.py`, `multi_agent_orchestrator.py`, `model_router.py`|Power core CLI workflows, skill indexing, orchestration, and Zeus integration.|These should be packaged, linted, and unit-tested; they define the “product.”|
|**Setup / Ops**|`cce_setup.sh`, `install-cce-hook.sh`, `setup_zeus_mcp.py`, `cce_startup_sync.py`, `daily_health_check.sh`, `setup_monitoring.sh`, `proxmox/*`|Environment bootstrap and ops automation.|Some scripts reference hardcoded paths (`/home/aldc/...`). Need to parameterize before releasing to non-ALDC machines.|
|**Analytics / QA**|`comprehensive_qa_suite.py`, `simplified_qa_runner.py`, `performance_optimizer.py`, `context_estimator.py`, `decision_logger.py`, `backfill_decisions.py`, `skill_semantic_search.py`|QA + analytics helpers.|Many aren’t referenced by the launcher today; decide whether to fold them into optional plugins or drop.|
|**Integrations / Experimental**|`context7_handler.py`, `cache_manager.py`, `context_compactor.py`, `recovery_manager.py`, `production_builder.py`, `workflow_executor.py` (Upstash), `tools/presentations/*`, etc.|Advanced capabilities for hallucination reduction, distributed cache, packaging.|Need dependency audit: e.g., `context7_handler.py` pulls Context7 docs, but only `multi_agent_orchestrator.py` imports it. Determine if we actually ship Context7 or keep it behind a feature flag.|

**Quick wins**:

- Add a manifest (e.g., `tools/manifest.yaml`) capturing dependency + maturity for each script.
- Introduce automated smoke tests for the CLI-critical modules; right now `tests/` only covers `context7_handler`.
- Move rarely used scripts (presentations, research prototypes) into `_archive/` so non-tech users aren’t tempted to run them.

---

### 4. Next steps proposed

1. **Decide what belongs in the “core installer”** – likely `cce` + core tools + core skills, nothing else.
2. **Define data sync boundaries** – plan how `projects/` and skill customizations will live in user space (Zeus storage or `~/.cce/`) so people stop committing them to `main`.
3. **Tag optional packs** – for example, “customer artifacts” vs. “platform engineering.” That way we can hand non-technical folks only what they need.
4. Once we agree on which buckets move where, I can draft the manifest files + migration scripts and prep the Claude prompt/docs you mentioned.

Let me know if you want any of these buckets prioritized (e.g., extracting completed projects first, or classifying skills into core vs. optional).