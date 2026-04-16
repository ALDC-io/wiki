I’m comparing these as infrastructure choices for PhaseLab, not just “which demo looks coolest.” The key criteria are: isolated previews, parallel fan-out, setup effort, cost/control, and how well each one fits UI prototype generation.

I’ve got a clear recommendation now: **E2B is the best fit for PhaseLab right now**. The interesting twist is that one of your “options,” `disler/agent-sandboxes`, isn’t really a competing sandbox platform — it’s a reference implementation built **on top of E2B**.

Thought for 1m 14s

Yes — after comparing them for **PhaseLab specifically**, I’d choose **E2B**.

## Recommendation

### Pick: **E2B**

Use E2B as the sandbox layer for PhaseLab’s MVP. It is the best fit for:

- spinning up **many parallel UI variants**
- exposing each variant on a **simple preview URL**
- using **custom templates** so every sandbox starts from the same Next.js/Tailwind scaffold
- keeping previews alive long enough for review with **pause/resume / auto-resume**
- later adding snapshot-based fan-out for faster best-of-N runs.

## Why E2B wins for _your_ project

PhaseLab is not just “run code safely.” It needs:

- **front-end preview environments**
- **many isolated variants in parallel**
- **fast startup from a shared base**
- a clean way to hand preview links to a Product Owner

E2B maps directly to that. Every sandbox has a public URL via `sandbox.getHost(port)`, templates can preinstall dependencies and even capture a running process in a snapshot, and E2B supports pause/resume plus auto-resume so a preview can come back without rebuilding from scratch. Those are unusually aligned with UI prototyping.

A particularly strong point for your use case is E2B’s template model: a template can include your base image, env vars, copied files, commands, and a start command that is snapshot-captured, and E2B says loading from that snapshot can be around **~80ms**. That is excellent for “one scaffold, many variants.”

## What about Modal?

Modal is strong, but I would treat it as the **runner-up**, not the first choice.

Modal Sandboxes are clearly capable: they support arbitrary code execution, secure-by-default networking, tunable lifetimes up to 24 hours, snapshots, and public access through tunnels. Modal’s docs also show lots of sandbox-heavy examples, including coding agents, Jupyter, and stateful code interpreters.

But for PhaseLab, Modal is a bit more “general compute platform with sandbox features,” while E2B feels more directly optimized for **agent sandboxes and previewable environments**. The preview flow on Modal is also a little more infrastructural: you expose ports through tunnels, and the tunnel API is documented as experimental at the API-reference level. That is not a dealbreaker, but it is slightly less clean than E2B’s “every sandbox has a public URL” model for your use case.

There’s one place where Modal may become the better choice later: if PhaseLab expands into **heavier infra**, especially GPU-heavy workloads, broader resource tuning, or you want your sandboxing and larger compute platform unified under one system. Modal’s docs emphasize GPUs, volumes, images, and broader infrastructure knobs more than E2B does.

## What about `disler/agent-sandboxes`?

This is **not** really an alternative to E2B or Modal.

The repo README explicitly says it explores **E2B agent sandboxes** with Claude Code, and lists E2B-based fundamentals, CLI, MCP, and workflows. In other words, it is a **reference implementation / learning repo built on E2B**, not a competing sandbox provider. When I checked the GitHub page, it showed 86 stars, 34 forks, and a repo history of 1 commit.

So my recommendation there is:

- **use it for ideas**
- do **not** adopt it as your architecture wholesale

It is helpful for understanding fan-out, CLI wrappers, and MCP patterns, but for PhaseLab MVP it adds more wrapper complexity than you need.

## Final ranking for PhaseLab

### 1. **E2B** — best now

Best fit for:

- multi-variant UI prototyping
- preview links for stakeholders
- fast startup from shared templates
- agent-oriented sandbox ergonomics.

### 2. **Modal** — strong second choice

Best if later you want:

- broader compute platform control
- GPU-heavy or mixed workloads
- one platform for both agent sandboxes and heavier backend jobs.

### 3. **disler/agent-sandboxes** — reference only

Use for:

- learning patterns
- fan-out workflow inspiration
- seeing how E2B can be wrapped with CLI/MCP  
    Not as the primary product dependency.

## The choice I would make

For `phase-lab`, I would build:

- **E2B** for sandbox creation and previews
- a **fixed prototype template** in E2B
- your own lightweight orchestrator in TypeScript
- no MCP layer in v1
- no repo-clone workflow by default

That gives you the shortest path to:

> one brief in → four UI variants out → four live preview links

That is the right MVP.