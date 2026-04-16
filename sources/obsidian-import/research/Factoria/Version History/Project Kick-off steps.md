
A good pattern is to treat your docs as:

- **Blueprint** = vision + requirements + “why”
    
- **Handbook** = implementation contract + “how” (runner split, compose, phases, tool chain)
    

## How to use the docs in OpenClaw without it going off the rails

### 1) Create a “Project Constitution” message (pinned / always included)

Paste a short, distilled set of non-negotiables so every agent run stays aligned:

- Service names + ports (`web` 3000, `api` 8000 dev, `gateway` 18789, `runner` 9000 internal)
    
- **Runner-only execution** (no shell in agents or api)
    
- Tool chain path: agent → gateway → api tool → runner job
    
- Secrets live only in runner (+ api→runner token)
    
- Workspace volume read/write rules (runner rw, api ro)
    

This should be 20–40 lines, not the entire docs.

### 2) Feed the full docs as attachments/context, but prompt with small excerpts

Give the full docs once so OpenClaw can cite them, then when you ask for work, include:

- the _exact phase_ you’re building
    
- the _specific section_ of the handbook it must follow
    
- the _deliverable_ (files to create/modify)
    

That prevents it from “re-inventing” architecture.

### 3) Orchestrate a multi-agent team by phases (matches your roadmap)

Don’t ask for “build the whole product”. Ask for **Phase 1**, then Phase 2, etc.

Example Phase 1 agent lineup:

- **Architect**: verifies repo structure + compose + boundaries
    
- **Runner Engineer**: implements runner API + job framework + logs/artifacts
    
- **API Engineer**: builds tool proxy endpoints + job tracking schema
    
- **Security Reviewer**: checks secrets + container hardening + auth token flow
    

### 4) Make code generation safe and reviewable

Require that every agent:

- outputs a **file tree plan**
    
- then outputs **patch-style diffs** (or explicit file contents)
    
- includes a **local test command** for each deliverable (`docker compose up`, `curl runner`, etc.)
    

### 5) Keep a single “source of truth” for decisions

As you make choices (e.g., “Runner auth: Bearer token”, “dbt profiles via Docker secret”), add them to a short `DECISIONS.md`. Agents can read that and stop re-arguing.

## The one big caution

If you rely on prompting alone, agents may propose patterns that violate your boundary (like mounting Docker socket or running dbt inside `api`). Your docs already forbid that — so in your OpenClaw “constitution,” explicitly say:

- “Any suggestion to mount `/var/run/docker.sock` is rejected.”
    
- “Runner API must be allowlisted; no ‘run arbitrary shell’ job.”
    

## Practical next step

Start with **Phase 1** and ask OpenClaw for:

1. repo scaffold (`/web /api /gateway /runner /infra`)
    
2. docker-compose that boots all four containers
    
3. runner “hello world job” + `/run`, `/jobs/{id}`, `/logs`
    
4. api can submit a runner job and display status
    

Once that works, everything else builds cleanly.