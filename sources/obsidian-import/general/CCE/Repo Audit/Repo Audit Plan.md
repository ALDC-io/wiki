### 1. What CCE currently is

- **Purpose** – an “AI-first development shell” that wraps Claude Code with automation: auto-update, Zeus Memory sync, 190+ prompt “skills,” project scaffolding, and CLI helpers (see `README.md`).
- **Execution flow** – users run the `cce` Bash launcher (`cce/`), which:
    1. Forces the repo back to `origin/main` (via `git checkout -- . && git clean -fd && git reset --hard origin/main`).
    2. Runs skill discovery + Zeus MCP scripts (`hooks/`).
    3. Starts automation features (workflow executor, context compactor, recovery mgr, etc., under `tools/`).
- **Content mix** – one repo holds the runtime launcher, 190+ skills (`.claude/skills`), per-project notes (`projects/`), docs, hooks, and CLI utilities.

---

### 2. Key design issues blocking safe use by non-technical users

1. **Single mutable repo for everything**
    - Core code, skills, personal project artifacts, and docs all share `main`. Non-technical users are editing the same tree the launcher later force-resets (see comments in `cce`), guaranteeing conflicts/data loss.
2. **Auto-hard-reset conflicts with “edit in place” workflow**
    - Startup literally wipes local changes (`git clean -fd`). The only way users preserve edits is by pushing straight to `main`, so they step on each other by design.
3. **Lack of packaging or releases**
    - Distribution is “clone main and hope,” despite being meant for non-devs. No tagged releases, installers, or even a `requirements.txt`; everything is ad‑hoc Bash + Python.
4. **Stateful data lives inside the repo**
    - Project trackers, skill experiments, and environment instructions sit under version control. They should live in `~/.cce/` or an external store, not in the repo that self-resets.
5. **Opaque governance / branching**
    - No branch protection, no PR flow, no CHANGELOG. Management can’t tell what changed; users can’t reason about which version they’re on.
6. **Risky scripts with root-like behavior**
    - Hook scripts attempt cross-repo syncs (e.g., auto-touching `~/repos/zeus-memory`) and call remote services without opt-in. Non-technical users have no visibility into what runs on their machines.
7. **Testing & documentation gaps**
    - Almost no automated tests (`tests/` is empty). Docs focus on marketing copy rather than install/run/dependency troubleshooting (aside from `docs/ENVIRONMENT_BEST_PRACTICES.md`).

---

### 3. Refactor / stabilization plan

| Phase                         | Goal                                     | Actions                                                                                                                                                                                                                                                                                                              |
| ----------------------------- | ---------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **0. Discovery (now)**        | Understand real use cases & expectations | Inventory actual users, machines, and “must-keep” artifacts in `projects/` and `.claude/skills`. Interview management/non-technical folks about what CCE must do vs. nice-to-have.                                                                                                                                   |
| **1. Separate concerns**      | Split immutable code from mutable data   | 1) Extract launcher + tools into `cce-core`. 2) Move skills library into `cce-skills` (versioned bundles). 3) Move org/project docs to a “CCE Projects” knowledge repo or Notion.                                                                                                                                    |
| **2. Package & release**      | Give non-devs a stable install path      | - Package `cce-core` as a pip package or self-contained tarball with checksums. <br>- Provide an installer that writes to `/opt/cce` (read-only) and creates `~/.cce/` for user data. <br>- Publish signed releases (GitHub tags) so users never touch Git manually.                                                 |
| **3. User-safe workflows**    | Prevent people from stomping each other  | - Inside `cce`, clone per-user worktrees (e.g., `~/cce_workspaces/<user>`). <br>- Default git remote to a protected central repo; force CLI to create feature branches and open PRs (auto-merge back once reviewed). <br>- Provide a `cce sync` command that snapshots skills/projects to Zeus or S3 instead of Git. |
| **4. Governance & telemetry** | Make it observable and accountable       | - Add version banners + `cce version`. <br>- Build a CHANGELOG + release notes pipeline. <br>- Instrument CLI to log which features are used; feed into Zeus memory + management dashboard.                                                                                                                          |
| **5. Productization**         | Align with management expectations       | - Define “CCE personas” (non-technical PM, ops analyst, etc.), map required flows, and trim features they don’t need. <br>**- Possibly split the current repo into multiple cooperating services (launcher, automation workers, skill registry).**                                                                   |

---

### 4. Specific fixes for the current repo (short term)

1. **Freeze main** – create `release/*` tags for the current state so we have a rollback target.
2. **Branch enforcement** – add `.git/hooks/pre-push` to block pushes to `main` unless CI ran; guide users to `cce publish` (which can open PRs automatically).
3. **Data relocation** – script to move `projects/*` and `.claude/skills/*` into `~/.cce/` plus a backup to Zeus.
4. **Installer rewrite** – new `install.sh` should fetch versioned artifacts (not the mutable repo) and never call `git clean`.
5. **Documentation refresh** – produce:
    - `docs/PRODUCT_OVERVIEW.md` (plain-language “what problem CCE solves”).
    - `docs/USER_OPERATIONS.md` (step-by-step for non-devs).
    - `docs/BRANCHING_MODEL.md` for managers.

---

### 5. Plan to engage non-technical users & management

1. **Purpose clarification doc** – summarize (in plain English) what CCE currently automates versus what users expect; include questions for leadership (e.g., “Should CCE own credential distribution?”).
2. **Survey/interview script** – gather from each user: tasks they run, pain points, desired outputs, tolerance for CLI vs. GUI.
3. **Solution options** – prepare decision matrix: (a) continue single repo but enforce release pipeline, (b) split into core + data repos, (c) rebuild as managed service (hosted Zeus integration + thin client). Include cost, effort, and risk for each.
4. **Change management** – propose a staged rollout: pilot new workflow with two users, document results, then onboard the rest.

---

### 6. Next steps / assignments

- **Deep dive** – I’ll map the contents of `projects/`, `.claude/skills/`, and `tools/` to see which pieces are critical vs. cruft. Expect a follow-up inventory doc.
- **Prompt & docs prep** – once the architecture picture is clearer, we can draft:
    - A concise “CCE mission + problems” prompt for Claude, so it understands the repo before touching anything.
    - Supporting `.md` files (e.g., `docs/AUDIT_SUMMARY.md`, `docs/REFactor_PLAN.md`) for future investigations.