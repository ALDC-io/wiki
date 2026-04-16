Build a **Python-first monorepo with an explicit orchestrator, specialist agents, closed feedback loops, typed contracts, and approval gates** so you are optimizing for “systems that build systems,” not one-off prompt-driven coding.

## Why this architecture fits the course

Your course notes emphasize four ideas that should shape the starter repo: **build the agent pipeline instead of hand-building everything**, **split work into specialist agents**, **close loops with self-checking and repair**, and **measure agent performance with explicit KPIs and context/tooling patterns**. That is why the base architecture below is organized around an orchestrator, reusable prompt/templates, deterministic workflow state, strong tests, and human review gates instead of a single general-purpose coding bot.

---

## Recommended default

**Start with a monorepo.**

Why:

- easiest place to share prompts, schemas, agent contracts, eval datasets, and CI
- simplest way to implement “spec → code → test → deploy” closed loops
- best fit for early-stage agentic engineering, where the hard part is workflow quality, not repo boundaries

Use:

- **LangGraph** when you want explicit nodes, transitions, and shared state in a workflow.
- **FastAPI** for the control plane and internal APIs.
- **uv** for dependency/project management, **Ruff** for lint/format, **pytest** for tests, and **mypy** for type checks.
- **GitHub Actions** for CI/CD, **Dependabot** for dependency updates, and **Trivy** for security scans.
- **OpenTelemetry** for traces/logs/metrics, with **Prometheus** for infra metrics/alerts and **MLflow tracing** for agent request traces, latency, token usage, and debugging.

---

## High-level agent pipeline

This mirrors the course’s “AI developer workflow” idea: one agent writes specs, another writes code, another runs tests, and the orchestrator coordinates loops and repair.

---

## Repository layout

agentic-starter/  
├─ .github/  
│  ├─ workflows/  
│  │  ├─ ci.yml  
│  │  ├─ cd-staging.yml  
│  │  ├─ cd-prod.yml  
│  │  ├─ security.yml  
│  │  └─ evals-nightly.yml  
│  └─ dependabot.yml  
├─ .devcontainer/  
│  └─ devcontainer.json  
├─ docs/  
│  ├─ architecture.md  
│  ├─ runbook.md  
│  ├─ security.md  
│  ├─ data-governance.md  
│  ├─ adr/  
│  │  ├─ 0001-use-monorepo.md  
│  │  ├─ 0002-use-langgraph.md  
│  │  └─ 0003-human-review-gates.md  
│  └─ diagrams/  
│     └─ agent-pipeline.mmd  
├─ specs/  
│  ├─ product/  
│  │  └─ example-feature.md  
│  ├─ acceptance/  
│  │  └─ example-feature.acceptance.yaml  
│  └─ contracts/  
│     ├─ code-task.schema.json  
│     ├─ test-task.schema.json  
│     └─ deploy-task.schema.json  
├─ prompts/  
│  ├─ system/  
│  │  ├─ orchestrator.md  
│  │  ├─ spec-agent.md  
│  │  ├─ code-agent.md  
│  │  ├─ test-agent.md  
│  │  ├─ review-agent.md  
│  │  └─ deploy-agent.md  
│  ├─ repair/  
│  │  ├─ failing-tests.md  
│  │  ├─ lint-fixes.md  
│  │  └─ policy-violation.md  
│  └─ rubrics/  
│     ├─ code-quality.md  
│     ├─ test-quality.md  
│     └─ release-readiness.md  
├─ apps/  
│  ├─ control-plane/  
│  │  ├─ app/  
│  │  │  ├─ main.py  
│  │  │  ├─ api/  
│  │  │  ├─ services/  
│  │  │  └─ deps.py  
│  │  └─ Dockerfile  
│  └─ dashboard/  
│     └─ ...  
├─ agents/  
│  ├─ orchestrator/  
│  │  ├─ graph.py  
│  │  ├─ state.py  
│  │  ├─ policies.py  
│  │  └─ checkpoints.py  
│  ├─ spec_agent/  
│  │  └─ agent.py  
│  ├─ code_agent/  
│  │  └─ agent.py  
│  ├─ test_agent/  
│  │  └─ agent.py  
│  ├─ review_agent/  
│  │  └─ agent.py  
│  ├─ deploy_agent/  
│  │  └─ agent.py  
│  └─ monitor_agent/  
│     └─ agent.py  
├─ workflows/  
│  ├─ spec_to_code.yaml  
│  ├─ test_repair_loop.yaml  
│  └─ deploy_release.yaml  
├─ libs/  
│  ├─ agent_sdk/  
│  │  ├─ models.py  
│  │  ├─ tool_registry.py  
│  │  ├─ prompts.py  
│  │  ├─ telemetry.py  
│  │  └─ guardrails.py  
│  ├─ common/  
│  │  ├─ settings.py  
│  │  ├─ logging.py  
│  │  ├─ security.py  
│  │  └─ git_ops.py  
│  └─ evals/  
│     ├─ datasets/  
│     ├─ runners/  
│     ├─ metrics.py  
│     └─ scorecards.py  
├─ tools/  
│  ├─ repo_writer.py  
│  ├─ pr_creator.py  
│  ├─ test_runner.py  
│  ├─ coverage_reporter.py  
│  └─ deploy_cli.py  
├─ infra/  
│  ├─ docker-compose.yml  
│  ├─ k8s/  
│  │  ├─ base/  
│  │  ├─ staging/  
│  │  └─ prod/  
│  ├─ terraform/  
│  └─ otel/  
│     └─ collector-config.yaml  
├─ tests/  
│  ├─ unit/  
│  ├─ integration/  
│  ├─ contract/  
│  ├─ eval/  
│  ├─ fixtures/  
│  └─ golden/  
├─ data/  
│  ├─ eval_sets/  
│  ├─ synthetic/  
│  └─ redacted/  
├─ scripts/  
│  ├─ bootstrap.sh  
│  ├─ local_ci.sh  
│  ├─ seed_eval_data.py  
│  └─ release.sh  
├─ .env.example  
├─ .gitignore  
├─ .python-version  
├─ AGENTS.md  
├─ Makefile  
├─ pyproject.toml  
├─ uv.lock  
├─ README.md  
└─ mkdocs.yml

### What the important files do

**`AGENTS.md`**  
Keep repo-local instructions here: architecture rules, naming conventions, forbidden actions, test commands, branch strategy, and “always do X before Y.” CrewAI’s docs explicitly recommend `AGENTS.md` as a lightweight repo-local source of truth for coding agents.

**`specs/acceptance/*.yaml`**  
Machine-readable acceptance criteria. This becomes the contract between the spec agent, code agent, and test agent.

**`workflows/*.yaml`**  
Workflow definitions: node order, retry policy, escalation thresholds, approval gates, and artifact handoffs.

**`libs/agent_sdk/`**  
The reusable substrate all agents share:

- typed request/response models
- tool wrappers
- prompt loaders
- telemetry decorators
- guardrail checks
- retry policy helpers

**`libs/evals/`**  
Keep evals separate from ordinary tests. Regression in agent behavior is often invisible to unit tests.

---

## Sample starter files

### `AGENTS.md`

# AGENTS.md  
  
## Operating rules  
- Never write to main directly.  
- Always produce a plan artifact before code changes.  
- All code changes must map to an acceptance criterion ID.  
- Run lint, type-check, unit, and contract tests before proposing a PR.  
- If tests fail twice, escalate to human review.  
- Never access production secrets from local development.  
- Never include raw PII in prompts, traces, or eval datasets.  
  
## Repo commands  
- install: uv sync  
- lint: uv run ruff check .  
- format: uv run ruff format .  
- type-check: uv run mypy .  
- test: uv run pytest

### `workflows/spec_to_code.yaml`

name: spec_to_code  
entrypoint: spec_agent  
steps:  
  - id: spec_agent  
    outputs: [technical_spec, acceptance_criteria, risks]  
  - id: orchestrator  
    validates: [technical_spec, acceptance_criteria]  
  - id: code_agent  
    outputs: [code_patch, migration_plan, docs_patch]  
  - id: test_agent  
    outputs: [unit_tests, integration_tests, test_report]  
  - id: review_agent  
    outputs: [review_summary, release_recommendation]  
gates:  
  - after: spec_agent  
    requires: human_approval_if_scope == "high"  
  - after: test_agent  
    requires: coverage_delta >= 0 and critical_failures == 0  
repair_loops:  
  - from: test_agent  
    to: code_agent  
    max_attempts: 2

### `libs/agent_sdk/models.py`

from pydantic import BaseModel  
from typing import Literal  
  
class TaskPriority(BaseModel):  
    level: Literal["low", "medium", "high", "critical"]  
  
class SpecArtifact(BaseModel):  
    title: str  
    summary: str  
    acceptance_criteria: list[str]  
    non_goals: list[str]  
    constraints: list[str]  
  
class CodeArtifact(BaseModel):  
    files_changed: list[str]  
    migration_required: bool  
    rollback_plan: str  
  
class TestArtifact(BaseModel):  
    unit_tests_added: int  
    integration_tests_added: int  
    status: Literal["pass", "fail"]  
    failure_summary: str | None = None

### `pyproject.toml`

[project]  
name = "agentic-starter"  
version = "0.1.0"  
requires-python = ">=3.12"  
  
[tool.ruff]  
line-length = 100  
  
[tool.pytest.ini_options]  
testpaths = ["tests"]  
python_files = ["test_*.py", "*_test.py"]  
  
[tool.mypy]  
python_version = "3.12"  
strict = true

---

## CI/CD pipeline design

GitHub Actions is a good default because it supports build, test, and deployment workflows as YAML-defined jobs and is built for both CI and CD. Dependabot handles version/security update PRs, and Trivy covers repo and artifact scanning.

### PR pipeline (`ci.yml`)

Run on every pull request:

1. checkout
2. `uv sync`
3. `ruff check` and `ruff format --check`
4. `mypy`
5. `pytest tests/unit tests/contract`
6. lightweight eval suite
7. Trivy repo scan
8. upload artifacts: coverage, junit XML, eval scorecard, agent trace sample

### Staging deploy (`cd-staging.yml`)

Run on merge to `main`:

1. build image
2. Trivy image scan
3. deploy to staging
4. run smoke tests
5. run canary eval set
6. require manual approval before prod

### Production deploy (`cd-prod.yml`)

Run only after approval:

1. deploy with version tag
2. post-deploy health checks
3. shadow evals against real traffic
4. auto-rollback if error budget or quality gates fail

### Nightly evaluation (`evals-nightly.yml`)

Run on schedule:

- replay saved traces
- benchmark against curated eval sets
- compare output quality, latency, cost, and failure modes to baseline

---

## Testing strategy

`pytest` is a strong default because it scales from small readable tests to more complex functional testing, and its fixture model is useful for deterministic agent test setups.

Use **five layers**:

1. **Unit tests**  
    Pure functions, tool wrappers, parsers, schema validation, retry policies.
2. **Contract tests**  
    Ensure every agent input/output artifact matches the schema.
3. **Golden tests**  
    Expected output snapshots for prompts, plans, code diffs, and review summaries.
4. **Integration tests**  
    Full workflow execution with stubbed model/tool calls.
5. **Evaluation tests**  
    Quality scoring on representative scenarios:
    - correctness
    - completeness
    - policy compliance
    - hallucination rate
    - repair success rate

### Closed-loop test policy

- code agent writes patch
- test agent generates and runs tests
- if failing, repair prompt is issued with failure trace
- after **2 failed repair attempts**, escalate to a human

That matches the course’s “close the loops” emphasis on self-correcting systems.

---

## Dependency and environment management

I would standardize on **uv** for Python project and dependency management. Astral documents uv as a Python package/project manager and provides project workflows like `uv sync` and `uv run`, which is exactly what you want for reproducible local and CI environments.

### Recommended approach

- commit `pyproject.toml`
- commit `uv.lock`
- use `.python-version`
- keep `.env.example` under version control
- use secrets only via environment injection in CI/runtime
- use per-environment config:
    - local
    - test
    - staging
    - prod

### Environment rules

- **local**: mock tools + sandbox model keys
- **CI**: ephemeral secrets, no prod data
- **staging**: redacted data only
- **prod**: least-privileged service accounts, no interactive shell access for agents

---

## Agent orchestration patterns and templates

LangGraph is especially well-suited for this style because it models workflows as nodes with transitions and shared state. CrewAI is a nice alternative when you want more role-based “crew/flow” ergonomics, and AutoGen’s AgentChat is good for multi-agent conversational patterns.

### Pattern 1: Orchestrator + specialist agents

Best default.

**Roles**

- Orchestrator
- Spec agent
- Code agent
- Test agent
- Review agent
- Deploy agent
- Monitor agent

**Why it works**

- central state
- explicit handoffs
- easier debugging
- easier human review
- safer retries

### Pattern 2: Planner / executor split

Best when tasks are large.

- **Planner agent** creates plan + subtasks
- **Executor agents** perform one bounded subtask each
- **Verifier agent** checks result before merge

### Pattern 3: Critic / repair loop

Best when output quality matters more than speed.

- builder agent creates artifact
- critic agent scores it
- repair agent revises it
- stop when score threshold is met or retry budget is exceeded

### Pattern 4: Human-gated release flow

Best for production changes.

- deploy agent cannot release without a signed approval artifact
- monitor agent can trigger rollback automatically, but cannot push new code unreviewed

---

## Agent templates

### 1) Spec-to-code agent

**Input**

- product spec
- constraints
- coding standards
- acceptance criteria

**Output**

- technical design
- affected files
- implementation plan
- code patch draft

**Prompt skeleton**

You are the Spec-to-Code Agent.  
Translate the provided product specification into:  
1. a technical design  
2. a file-level change plan  
3. implementation notes  
4. explicit assumptions  
5. risks and open questions  
  
Rules:  
- map every change to an acceptance criterion ID  
- do not invent nonexistent modules  
- prefer modifying existing files over creating new ones unless justified  
- return structured JSON matching SpecArtifact

### 2) Test agent

**Input**

- code diff
- acceptance criteria
- risk areas
- coverage baseline

**Output**

- new unit tests
- new integration tests
- risk-based test matrix
- pass/fail report

**Prompt skeleton**

You are the Test Agent.  
Design and run tests for the supplied diff.  
  
Must:  
- validate every acceptance criterion  
- add regression tests for changed behavior  
- call out missing observability or missing rollback coverage  
- return structured JSON matching TestArtifact

### 3) Deployment agent

**Input**

- release notes
- image tag
- migration plan
- rollout strategy

**Output**

- deploy plan
- canary steps
- rollback steps
- post-deploy verification checklist

**Prompt skeleton**

You are the Deployment Agent.  
Prepare a safe release plan.  
  
Must:  
- identify schema/data migration risks  
- require human approval for production  
- define rollback triggers  
- define post-release monitors and thresholds

---

## Detailed example workflow: spec → code → tests → deployment

### 1. Specification intake

Product owner drops `specs/product/feature-x.md`.

### 2. Spec agent normalizes it

Creates:

- technical summary
- non-goals
- constraints
- acceptance criteria YAML
- risk register

### 3. Human review gate #1

A human approves:

- scope
- acceptance criteria
- boundaries
- risky dependencies

### 4. Orchestrator creates execution state

It assembles:

- repo context
- relevant files
- coding standards
- allowed tools
- retry budget
- escalation policy

### 5. Code agent proposes implementation

Outputs:

- patch plan
- touched file list
- migration notes
- draft code

### 6. Static checks run

- Ruff
- mypy
- schema validation
- forbidden-path policy checks

### 7. Test agent generates and executes tests

- unit tests
- integration tests
- contract tests
- smoke tests

### 8. Repair loop

If checks fail:

- orchestrator packages failure traces
- code agent gets a focused repair task
- max 2 repair attempts
- then escalate

### 9. Review agent summarizes

Produces:

- what changed
- risks
- test evidence
- release recommendation
- docs impact

This maps directly to the course’s multi-agent development flow and close-the-loop pattern.

### 10. Human review gate #2

A human reviews:

- code diff
- risky migrations
- prompt-generated code quality
- security implications

### 11. Deploy agent prepares release

Creates:

- staging deployment plan
- canary steps
- rollback plan
- monitor thresholds

### 12. Staging deployment

Smoke tests + canary evals run.

### 13. Human review gate #3

Human approves production.

### 14. Production deployment

Controlled rollout.

### 15. Monitor agent watches signals

- latency
- error rate
- quality score drift
- cost spikes
- rollback trigger status

### 16. Post-release learning loop

Traces and review outcomes are added to eval datasets so the workflow gets better over time.

---

## Security and data governance

### Security controls

- least-privilege credentials for every tool
- tool allowlists per agent
- no direct prod DB write access for coding agents
- sandboxed execution for generated code
- signed commits/releases for deployable artifacts
- Trivy scans on repo + container images
- Dependabot for vulnerable dependency updates and alerts.

### Data governance controls

- classify data into: public / internal / confidential / regulated
- redact PII before prompts, traces, evals
- store prompt inputs and outputs separately from raw business data
- define retention windows for traces and eval artifacts
- maintain dataset provenance for every eval set
- keep “human-approved examples” and “production traces” in separate stores

### Policy rules for agentic projects

- agents may propose; humans approve production-impacting changes
- agents can read docs, schemas, and staging configs
- agents cannot rotate secrets or change IAM policy
- agents cannot self-approve releases
- agents cannot train on raw customer data without explicit governance sign-off

---

## Monitoring and KPIs

OpenTelemetry is a vendor-neutral framework for traces, metrics, and logs, and the Collector gives you a scalable way to receive/process/export telemetry. Prometheus is a common open-source monitoring/alerting backbone. MLflow tracing is useful for agent/LLM traces because it captures inputs, outputs, metadata, latency, and costs for each step.

### Instrumentation stack

- **OpenTelemetry**: request traces, span hierarchy, tool-call metadata
- **Prometheus**: infra/service metrics and alerting
- **MLflow tracing**: agent-level traces and debugging
- optional: framework-native observability if you choose PydanticAI or LangSmith-like tooling; PydanticAI explicitly supports OpenTelemetry-compatible backends.

### KPIs to track

#### Reliability

- workflow success rate
- first-pass success rate
- repair-loop success rate
- rollback rate
- flaky test rate

#### Quality

- acceptance criteria pass rate
- hallucination / invalid-change rate
- review rejection rate
- escaped defect rate
- eval benchmark score

#### Speed

- spec-to-PR time
- PR-to-staging time
- mean repair time
- deploy lead time

#### Cost

- tokens per successful task
- tool calls per successful task
- cost per accepted PR
- cost per deployed feature

#### Human leverage

- human minutes saved per release
- percent of runs requiring escalation
- approval rate after first review
- ratio of autonomous vs assisted completions

---

## Human-in-the-loop review points

You asked for explicit review points; here’s the minimum safe set.

### Gate 1: scope approval

Before code generation:

- acceptance criteria
- risk rating
- architectural fit
- policy constraints

### Gate 2: merge approval

Before merge:

- code diff
- tests
- dependency changes
- migrations
- security scan results

### Gate 3: production approval

Before prod:

- rollout plan
- rollback plan
- monitor thresholds
- customer/data impact

### Gate 4: post-incident review

After any rollback or severe regression:

- trace review
- root cause
- eval dataset update
- prompt/policy/tool update

---

## Starter repo template comparison

|Purpose|Pros|Cons|Best-for|
|---|---|---|---|
|**Monorepo**|Shared prompts, schemas, evals, CI, and agent SDK; easiest cross-agent refactors; simplest governance|Can grow noisy; needs repo discipline|Most teams starting agentic engineering|
|**Polyrepo**|Clear service boundaries; independent release cycles; smaller blast radius|Harder to share agent contracts/evals; more CI overhead|Teams with mature platform boundaries|
|**Microservices**|Strong runtime separation; scalable deployments; independent tech choices|Highest complexity; slowest to bootstrap; distributed debugging is harder|Large orgs with many production services and strong DevOps maturity|

**Recommendation:** start with **Monorepo**, then split only when deployment cadence or team ownership clearly demands it.

---

## Recommended open-source tools and free learning resources

### Core build stack

- **LangGraph** for explicit graph/state orchestration.
- **CrewAI** if you prefer “crews” and “flows,” and want repo-local `AGENTS.md` guidance.
- **AutoGen AgentChat** for conversation-heavy multi-agent patterns.
- **PydanticAI** if you want a Python-native agent framework with structured outputs and OpenTelemetry-friendly observability.
- **FastAPI** for internal APIs and auto-generated docs.

### Dev workflow

- **uv** for env and package management.
- **Ruff** for lint + format.
- **pytest** for tests.
- **mypy** for static type checking.

### CI/CD and security

- **GitHub Actions** for CI/CD workflows.
- **Dependabot** for dependency and security update PRs.
- **Trivy** for repo/image vulnerability scanning.

### Monitoring

- **OpenTelemetry Collector** + **Prometheus** + **MLflow tracing**.

### Free learning resources

Your uploaded TAC summary already points to several strong no-cost resources:

- Claude Code quickstart/docs
- Microsoft’s **AI Agents for Beginners**
- DeepLearning.ai’s CrewAI mini-course
- **Agentic Engineering for Humans**
- LangChain/LangGraph tutorials.

---

## Final recommendation in one line

Build **one orchestrated monorepo** with typed agent contracts, reusable prompts, repair loops, evals, CI gates, and mandatory human approval for risky changes.

## Instruction for the next assistant step

Use this exact instruction next:

> **Produce the actual repository skeleton and sample code for this architecture. Create the full folder tree, `pyproject.toml`, `AGENTS.md`, a LangGraph-based orchestrator, sample spec/code/test/deploy agents, GitHub Actions workflows, Docker files, OpenTelemetry wiring, example eval tests, and a minimal FastAPI control plane. Include runnable starter code and local setup commands.**