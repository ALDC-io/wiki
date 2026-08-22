# R-B — Enforcing an agent's capability tier when the agent needs real credentials

**2026-08-22.** Answers §7.4 of `docs/specs/architecture-v0.md` and the load-bearing claim in §4
that "the dangerous verb is contained by construction, not by prompt."

## Evidence tier convention used here

`MEASURED` I ran it · `DOCUMENTED` I read the primary doc text · `DOCUMENTED*` vendor doc text
quoted through a search index, **page itself unreachable from this sandbox** · `REPORTED` paper or
credible practitioner writeup · `REASONED` argument from constraints · `BET` judgement call.

> **Note on `DOCUMENTED*`.** This session runs behind a domain-allowlisting egress proxy that
> blocked `docs.snowflake.com`, `docs.snowflake.cn`, `docs.docker.com`, `learn.microsoft.com`,
> `developer.hashicorp.com`, `docs.aws.amazon.com`, `www.anthropic.com`, `goteleport.com`,
> `openfga.dev`, `e2b.dev`, `modal.com`, `daytona.io`, `cedarpolicy.com`, `kyverno.io`,
> `gvisor.dev` and `andrewlock.net`, while allowing `github.com`, `raw.githubusercontent.com` and
> `code.claude.com`. `MEASURED` — see §2.2 below, this is itself a finding. Everything I could
> reach directly is `DOCUMENTED`; the rest is honestly downgraded.

---

## 1. Verdict

**The generic sandbox literature is answering the wrong question and the strawman half-inherits its
mistake.** For a data agent the containment axis that matters is not the kernel, it is the
credential: a perfect Firecracker microVM holding the operator's Snowflake password has a blast
radius of the whole warehouse. The single highest-value change is not T1's container — it is that
**the agent stops holding any credential at all**, and a broker outside the sandbox holds it and
injects it on egress. That pattern is not speculative: it ships today in two independent products
(Claude Code `sandbox.credentials` masking + proxy injection; Docker Sandboxes proxy credential
injection), and Claude Code on the web uses it for GitHub tokens. Second: **containers are not
required on Windows.** `@anthropic-ai/sandbox-runtime` has a native-Windows alpha that fences
egress at the kernel with a Windows Filtering Platform filter keyed on a dedicated account SID — no
WSL2, no container, and the workload cannot bypass it by unsetting `HTTPS_PROXY`. That collapses
§7.4 and unblocks §8 item 4 without the container bet. Third: **§4's "enforced by the DECIDE plane"
is the wrong verb.** A control plane that *checks* a tier is admission control; only a launcher
that *constructs* the sandbox and the credential from the tier makes a T1 agent structurally unable
to reach a T2 verb. Fourth, on the 0-of-22 refusals: the estate already owns the right sentence
(`tests/test_evaluator_isolation.py`: *"a boundary nobody has watched reject something is a
diagram, not a control"*) and Anthropic's own devcontainer already ships the copyable mechanism — a
boot-time two-sided assertion that fails the container if a blocked host is reachable. Finally, the
Snowflake side has a hard, documented floor: **a role-restricted PAT's minimum lifetime is one day,
not one run**; sub-hour Snowflake credentials require key-pair JWT (60 min cap), Snowflake OAuth
(600 s), or Vault-style per-lease users.

---

## 2. What the evidence says

### 2.1 Container sandboxing that is actually a control (§7.4)

#### 2.1.1 The reframe that matters most

R3 already stated it and it should be promoted to the front of §4: *"compute isolation and
credential blast radius are different problems. A Firecracker VM can perfectly isolate the host and
still allow the code inside it to delete every Azure resource that its credential legitimately
authorises."* (`docs/research/answers/R3-answer-control-plane.md:662`) `REPORTED`

Everything below is defence in depth around that. For ALDC's actual threat model — an agent with
shell and repo write, not a malicious administrator (the model `tests/test_evaluator_isolation.py`
already names) — kernel escape is not the top risk. `REASONED`

#### 2.1.2 The Docker/Podman flags, and what each actually stops

| Flag | What it actually stops | What it does not |
|---|---|---|
| `--security-opt=no-new-privileges` | Sets `PR_SET_NO_NEW_PRIVS`; setuid/setgid binaries in the image cannot elevate — `sudo` returns EPERM even with the setuid bit | Anything the process is already authorised to do |
| `--read-only` rootfs | Writing a payload/webshell to the image filesystem | Writes to mounted volumes and `tmpfs`; nothing about network |
| userns-remap / rootless | Container UID 0 maps to a high unprivileged host UID, so host root-owned files are inaccessible | Kernel exploits reachable from an unprivileged UID |
| seccomp (Docker default) | ~44 syscalls including `kexec_load` | The ~300 syscalls it allows |
| AppArmor (`docker-default`) | Coarse path/capability confinement | Same |

`REPORTED` — OWASP Docker Security Cheat Sheet and corroborating practitioner writeups; I could not
reach `docs.docker.com` for the primary reference text.

The honest summary: **these are hardening inside one shared kernel, not a boundary.** They raise
the cost of an escape; they do nothing about a credential the container legitimately holds. That is
why they are the wrong first move here. `REASONED`

#### 2.1.3 gVisor and Firecracker

- **gVisor** interposes a user-space kernel (the Sentry) on application syscalls. Its own
  performance document presents start-up time **as a graph, with no number in the text**, and adds
  the caveat: *"most of the time overhead above is associated Docker itself. This is evident with
  the empty `runc` benchmark."* `DOCUMENTED`
  (`raw.githubusercontent.com/google/gvisor/master/g3doc/architecture_guide/performance.md`)
  **Could not verify** a gVisor start-up figure from a primary source. R3's "millisecond-scale"
  came from vendor marketing.
- **Firecracker** README, verbatim: *"The overall security of Firecracker microVMs, including the
  ability to meet the criteria for safe multi-tenant computing, depends on a well configured Linux
  host operating system."* `DOCUMENTED`
  (`raw.githubusercontent.com/firecracker-microvm/firecracker/main/README.md`) — i.e. the microVM
  boundary is conditional on host configuration you must get right, which is the platform work R3
  already said not to take on for four engineers.
- **`MEASURED`: I could not benchmark either.** There is no Docker daemon in this session
  (`dial unix /var/run/docker.sock: no such file or directory`).

#### 2.1.4 Windows — what is real and what is folklore

This is the part of §7.4 that was guessed and can now be settled.

**Real, and it kills the WSL2 assumption:**

> *"The sandbox is built into Claude Code and runs on macOS, Linux, and WSL2. **Native Windows is
> not supported.** On Windows, run Claude Code inside a WSL2 distribution."* `DOCUMENTED`
> — https://code.claude.com/docs/en/sandboxing

> *"WSL1 is not supported because bubblewrap requires kernel features only available in WSL2."*
> `DOCUMENTED` — same page, "OS-level enforcement".

So the MEASURED "sandboxing: **none** — agents run as the user with the user's credentials" is not
an oversight; on native Windows there is currently no OS-enforced Bash sandbox to turn on.

**Real, and it is the finding that changes the plan:** `@anthropic-ai/sandbox-runtime` (`srt`) has
a **native Windows alpha that needs neither WSL2 nor a container**:

> *"The sandboxed process runs under a dedicated `srt-sandbox` local user account, isolated from
> the calling user by native Windows security primitives — a Windows Filtering Platform (WFP)
> egress fence keyed on the sandbox account's SID, and per-session explicit ACEs that grant or deny
> that SID access to configured filesystem paths."* `DOCUMENTED`
> — https://github.com/anthropic-experimental/sandbox-runtime (README, "Windows (alpha)")

> *"a PERMIT for loopback destinations inside the configured proxy port range (default
> `60080–60089`), and a BLOCK for any connect whose token carries the `srt-sandbox` SID. The
> sandboxed process reaches the internet only via the JS HTTP/SOCKS5 proxies listening in that
> range; **a process that strips its proxy environment and connects directly is blocked at the
> kernel.**"* `DOCUMENTED`

> *"Running under a distinct user SID structurally closes the surrogate-spawn class of escape (Task
> Scheduler, `PROC_THREAD_ATTRIBUTE_PARENT_PROCESS` onto a broker-owned process, BITS,
> out-of-process COM with `RunAs="Interactive User"`): any process the child manages to spawn
> out-of-band still carries the `srt-sandbox` SID."* `DOCUMENTED`

Documented Windows caveats, all of which are operational rather than fatal: it is **alpha**;
`windows-install` is a one-time elevated step; TLS termination requires the MITM CA in the *sandbox
user's* `CurrentUser\Root` store (schannel ignores env vars); CRL/OCSP revocation checks go out via
WinHTTP under the caller's token and are blocked by the fence, so schannel tools fail with
`CRYPT_E_REVOCATION_OFFLINE` (`0x80092013`) unless revocation is disabled per tool
(`curl --ssl-no-revoke`, `git -c http.schannelCheckRevoke=false`); and *"`proxyAuthToken` is
visible in the runner's command line."* `DOCUMENTED`

**Windows containers vs WSL2 — the folklore:**
- Windows containers have two isolation modes: process isolation shares the host kernel; Hyper-V
  isolation runs each container in a lightweight VM with its own kernel, *"providing hardware
  isolation and a security boundary around the containers."* `DOCUMENTED*`
  (learn.microsoft.com `windowscontainers/manage-containers/hyperv-container`, blocked here.)
  **Only Hyper-V isolation is a security boundary.** But Windows containers run *Windows*
  workloads; ALDC's stack is Python/dbt/Linux tooling, so they are the wrong tool regardless.
  `REASONED`
- Docker Desktop on Windows with the WSL2 backend runs containers inside a Docker-managed WSL2 VM
  — "double-isolated" from the Windows host. Practitioner consensus is *"WSL 2 offers better
  performance and resource utilization, but provides reduced security isolation"* than the Hyper-V
  backend. `REPORTED`
- Trend Micro published *"Cracking the Isolation: Novel Docker Desktop VM Escape Techniques Under
  WSL2"*. **Could not verify** the technique detail, CVEs or fix status — the page is blocked from
  this sandbox. Treat "WSL2 is a VM so it's a hard boundary" as **unverified folklore** until
  someone reads that paper.

**Start-up cost: still unmeasured, and it should stay unmeasured for now.** For a run whose budget
is `wall_clock: 45m`, the difference between a 150 ms microVM and a 2 s container is 0.07% of the
run. R3 reached the same conclusion. Choose on identity and egress, not cold start. `REASONED`

---

### 2.2 Egress allowlisting — which mechanisms the workload can bypass

Four mechanisms, ranked by whether the thing being confined can defeat the confinement.

| Mechanism | Enforcement point | Bypassable by the workload? |
|---|---|---|
| Proxy env vars only (`HTTPS_PROXY` in the container) | none — convention | **Yes, trivially.** `unset HTTPS_PROXY` |
| DNS-based (Cilium FQDN, dnsmasq allowlist) | DNS response interception → IP program | **Yes** — connect to a literal IP, or use DoH, unless default egress is already deny |
| iptables/nftables **in the container's own netns** | container kernel netns | **Only if it gets `NET_ADMIN`** — and Anthropic's own reference devcontainer grants exactly that |
| Kernel fence in a namespace/principal the workload is not | host netns, or a WFP filter keyed on a different SID, or netns removed entirely | **No** |

Evidence for row 3: Anthropic's published devcontainer runs with
`"runArgs": ["--cap-add=NET_ADMIN", "--cap-add=NET_RAW"]` and `postStartCommand:
sudo /usr/local/bin/init-firewall.sh`, with sudo narrowly scoped
(`node ALL=(root) NOPASSWD: /usr/local/bin/init-firewall.sh`). `DOCUMENTED`
(`raw.githubusercontent.com/anthropics/claude-code/main/.devcontainer/`). The narrow sudoers is
good design; the capability is still in the container, and the script's first act is
`iptables -F`, so an interrupted re-run leaves egress wide open between the flush and
`iptables -P OUTPUT DROP`. `REASONED`

Evidence for row 4, three shipping implementations:
- **Linux (srt):** *"The network namespace of the sandboxed process is removed entirely, so all
  network traffic must go through the proxies running on the host (listening on Unix sockets that
  are bind-mounted into the sandbox)."* `DOCUMENTED`
- **Windows (srt):** the WFP `ALE_AUTH_CONNECT` filter set, machine-wide, keyed on the
  `srt-sandbox` SID, installed by a one-time elevated step. The sandbox account cannot alter it.
  `DOCUMENTED`
- **macOS (srt):** the Seatbelt profile allows only the localhost proxy ports. `DOCUMENTED`

#### The residual that no allowlist fixes

Anthropic's own security limitations, verbatim, and this is the most important sentence in this
whole report:

> *"Because the proxy makes its allow decision from the client-supplied hostname without inspecting
> TLS, code running inside the sandbox can potentially use **domain fronting** or similar
> techniques to reach hosts outside the allowlist."*
> and
> *"Allowing broad domains such as `github.com` can create paths for data exfiltration."*
> `DOCUMENTED` — https://code.claude.com/docs/en/sandboxing (Security limitations)

The `srt` README says the same: *"in some cases it may be possible to bypass the network filtering
through domain fronting"* and *"allowing `github.com` lets a process push to any repository."*
`DOCUMENTED`

**Therefore: an egress allowlist is a control against accident and misconfiguration, and a speed
bump against a determined exfiltrator. It is not a confidentiality boundary.** §4's T1 row should
say that, because a tier that over-claims is worse than one that under-claims. `REASONED`

Even with `network.tlsTerminate`, the docs are explicit that it *"does not add content filtering."*
`DOCUMENTED`

#### What the agent-sandbox products actually do

| Product | Isolation | Egress | Credential handling | Source quality |
|---|---|---|---|---|
| **Claude Code Bash sandbox** | Seatbelt / bubblewrap; Bash subprocesses only | Host proxy, deny-by-default domains; `strictAllowlist`, `allowManagedDomainsOnly` | `credentials.files`/`envVars` with `deny` or `mask`; masked value substituted by the proxy on `injectHosts` | `DOCUMENTED` |
| **`@anthropic-ai/sandbox-runtime`** | Whole process incl. MCP servers and hooks; adds native Windows | Same + WFP kernel fence on Windows; netns removal on Linux | Same masking model | `DOCUMENTED` |
| **Claude Code on the web** | Anthropic-managed VM | Network proxy with a default allowlist | *"a separate proxy holds your GitHub token outside the sandbox while issuing scoped credentials for repository access inside it"* | `DOCUMENTED` |
| **OpenAI Codex CLI** | Seatbelt (macOS), Landlock + seccomp (Linux); sandboxes its tool calls, **not itself** | Network disabled by default in the shell tool (`CODEX_SANDBOX_NETWORK_DISABLED=1`); re-enabled via `sandbox_workspace_write.network_access` | not documented as brokered | `REPORTED` |
| **Docker Sandboxes** | microVM (Docker Desktop 4.60+), own Docker daemon | Host-side proxy, `--policy allow|deny` with `--allow-host`/`--block-host`; MITM CA terminates TLS by default | Proxy injects stored credentials so *"the agent inside the sandbox never sees the raw key, only a placeholder"* | `REPORTED` (docs.docker.com blocked) |
| **E2B** | Firecracker microVM per sandbox | not verified | not verified | `REPORTED` |
| **Modal Sandboxes** | gVisor | not verified | not verified | `REPORTED` |
| **Daytona** | Docker by default, stronger options configurable | not verified | not verified | `REPORTED` |
| **Northflank** | BYOC, container + microVM options | configurable egress | not verified | `REPORTED` |
| **microsandbox** | embeddable self-hosted runtime | per-sandbox iptables allowlist | not verified | `REPORTED` |
| **Devin** | cloud "Devbox" container/VM; `--sandbox` flag for the CLI | *"100% of network requests and command executions are restricted unless configured by specific domain and directory scopes"* | Devin Secrets as a delivery mechanism from an upstream vault | **Could not verify** — third-party writeups only, `docs.devin.ai` unreachable |

**The convergence is the finding.** Two vendors I can quote directly (Anthropic, Docker) and one I
cannot (Devin) independently arrived at the same shape: *the credential lives in a host-side proxy
outside the sandbox; the workload sees a sentinel; substitution happens on egress to an explicitly
named host.* That is prior art for §9's "per-secret approval stays human" being implementable
**without the agent ever holding the secret**, which is strictly stronger than approving a
handover. `DOCUMENTED` + `REASONED`

#### MEASURED: the operational tax of an allowlist, from this session

This session runs behind exactly the control §4 proposes for T1. It blocked 16 of the ~24 domains I
needed. Every block was correct policy and wrong for the task. Two consequences worth budgeting for:

1. **The failure mode is a silent research gap, not an error.** I got `EGRESS_BLOCKED` and moved on;
   an agent with a weaker sense of its own uncertainty would have hallucinated the Snowflake syntax.
   A T1 agent needs the *refusal* surfaced into its transcript — which Claude Code does do:
   *"When a command fails after the sandbox denied it access, Claude Code appends the violation
   details to the failed command's output, so Claude sees which file path or network host the
   sandbox blocked."* `DOCUMENTED`
2. **Allowlist churn is continuous.** An allowlist right for connector migration is wrong for the
   next ticket. Budget a standing "add a host" path, or T1 will be turned off within a month.

---

### 2.3 Short-lived, scoped Snowflake credentials

Scored against the three properties the brief asks for, plus two more that matter.

| Mechanism | (a) not the operator | (b) exactly one role | (c) expires | Mintable per run | Revocable |
|---|---|---|---|---|---|
| **Key-pair (JWT)** | yes — separate `TYPE=SERVICE` user | no, unless paired with role restriction elsewhere | **JWT capped at 60 min**; the *private key* is long-lived | only if a broker holds the key | rotate/remove the public key |
| **PAT** | yes | **yes** — `ROLE_RESTRICTION` | **minimum 1 day** | no (day granularity) | `ALTER USER … REMOVE PAT` — but **not from a session authenticated by that same PAT** |
| **Snowflake OAuth** | yes | via scopes | **600 s, non-configurable**, when `OAUTH_ISSUE_REFRESH_TOKENS = FALSE` | yes | revoke the integration / refresh token |
| **External OAuth (Entra)** | yes | yes, if `EXTERNAL_OAUTH_ANY_ROLE_MODE = DISABLE` (default) | per IdP; Entra access tokens default 60–90 min | yes | via IdP |
| **WIF** | yes | via the bound service user's role | no credential at all | n/a | unbind the workload identity |
| **Vault dynamic secret** | yes — a *new Snowflake user per lease* | yes | **default TTL 1 h, max 24 h** | **yes** | `DROP USER` in `revocation_statements` |

Detail and sources:

- **PAT.** Syntax: `ALTER USER … ADD PROGRAMMATIC ACCESS TOKEN <name> [ROLE_RESTRICTION = '<role>']
  [DAYS_TO_EXPIRY = <int>] [MINS_TO_BYPASS_NETWORK_POLICY_REQUIREMENT = <int>]`. Default expiry 15
  days; `PAT_POLICY` sets `DEFAULT_EXPIRY_IN_DAYS` (1..max) and `MAX_EXPIRY_IN_DAYS` (..365).
  `ROLE_RESTRICTION` does not *grant* the role — the user must already hold it — and once issued
  **the restriction cannot be modified or removed**. `ROLE_RESTRICTION` is required for
  `TYPE=SERVICE` users by default (`REQUIRE_ROLE_RESTRICTION_FOR_SERVICE_USERS`), and service users
  must be subject to a network policy to generate or use a PAT
  (`NETWORK_POLICY_EVALUATION = ENFORCED_REQUIRED`). `DOCUMENTED*`
  (docs.snowflake.com `/user-guide/programmatic-access-tokens`,
  `/sql-reference/sql/alter-user-add-programmatic-access-token`,
  `/sql-reference/sql/create-authentication-policy` — all blocked from this sandbox.)
- **The one genuinely good property of a role-restricted PAT**, and the answer to the secondary-role
  trap below: with a role restriction, *"secondary roles are not used, even if
  `DEFAULT_SECONDARY_ROLES` is set to `('ALL')` for the user."* `DOCUMENTED*`
- **The secondary-roles trap that §4 currently walks into.** Snowflake behaviour bundle **2024_08
  (BCR-1692)** changed `DEFAULT_SECONDARY_ROLES` to default to `ALL`. With `USE SECONDARY ROLES
  ALL`, *"the command doesn't validate role grants up front. Instead, the active secondary roles are
  determined dynamically when each SQL statement executes."* `DOCUMENTED*` So **"T1 = read-only
  warehouse role" is false by default** if the agent's user has been granted anything else: the
  effective privilege is the union. Two fixes, and you should do both — set
  `DEFAULT_SECONDARY_ROLES = ()` on the agent user, *and* use a role-restricted PAT.
- **Key-pair.** Snowflake enforces a maximum JWT lifetime of 60 minutes. `RSA_PUBLIC_KEY` and
  `RSA_PUBLIC_KEY_2` give two slots for zero-downtime rotation. `DOCUMENTED*` The 60-minute cap is
  on the *token*, not the key — so key-pair only gives per-run expiry if a broker holds the private
  key and hands out JWTs.
- **WIF** supports AWS IAM roles, Microsoft Entra ID, Google Cloud service accounts, and OIDC
  providers including Kubernetes and GitHub Actions. `DOCUMENTED*` **The constraint nobody states:
  WIF binds to a workload's *platform* identity. A process on a bare Windows laptop has none.** WIF
  is a reason to move the T1/T2 runner onto Azure Container Apps Jobs (which R3 already recommends,
  with one user-assigned managed identity per tenant) — it is not adoptable on the laptop.
- **Password deprecation.** Snowflake is retiring single-factor password sign-in; service users must
  move to key-pair, OAuth, PAT or WIF. **The milestone dates are contested across the sources I
  could reach** — one says all single-factor password sign-ins blocked by November 2025, another
  places "Milestone 3" in August–October 2026. **Could not verify.** Read
  `docs.snowflake.com/en/user-guide/security-mfa-rollout` directly; if a deadline is live right now
  this is a schedule input, not a nice-to-have.

#### The gap §5's budget field cannot close

`budget: {warehouse_credits: 2}` is currently unenforceable, and the defaults are hostile:

- `STATEMENT_TIMEOUT_IN_SECONDS` defaults to **172800 (48 hours)**. `DOCUMENTED*`
- A resource monitor's SUSPEND action *"waits for currently executing queries to finish"*, and *"a
  query might start before the threshold is reached and complete after the SUSPEND action is
  triggered. This can result in credit overshoot beyond the defined threshold."* `DOCUMENTED*`

So a read-only role bounds *damage* but not *spend*. A tier that claims a credit budget must also
set a per-tier `STATEMENT_TIMEOUT_IN_SECONDS`, a dedicated small warehouse with
`AUTO_SUSPEND` low, and a resource monitor — and must record that the monitor overshoots.
`REASONED`

#### The vault/secret side

- **Vault dynamic secrets, Snowflake database secrets engine:** generates credentials per request,
  default TTL **1 hour**, max **24 hours**, with `revocation_statements="DROP USER IF EXISTS
  {{name}};"`. This is the only mechanism in the table that gives a genuinely per-run Snowflake
  identity created and destroyed by something other than the agent. `DOCUMENTED*`
  (developer.hashicorp.com `/vault/docs/secrets/databases/snowflake` — blocked here.)
- **Licensing/cost reality:** Vault moved to BUSL 1.1 in August 2023; MPL patches stopped after
  31 Dec 2023. **OpenBao** is the MPL 2.0 community fork, now under the Linux Foundation. Vault
  Community is free to license and not free to operate. HCP Vault Dedicated is quoted at ~$0.03/h
  for dev and $1.58–$9.41/h for production plus a per-client monthly charge. `REPORTED`
  (third-party pricing pages only; hashicorp.com blocked — treat the numbers as order-of-magnitude.)
- **Azure side:** Key Vault has no dynamic-secret generation — it stores, it does not mint. Entra
  access tokens default to *"a random value ranging between 60-90 minutes (75 minutes on average)"*,
  and *"Configuring token lifetimes for managed identity service principals isn't supported."*
  `DOCUMENTED` (`raw.githubusercontent.com/MicrosoftDocs/entra-docs/main/docs/identity-platform/configurable-token-lifetimes.md`).
  Configurable access-token lifetime for other principals: min 10 minutes, max 23:59:59.
  `DOCUMENTED`

---

### 2.4 The credential broker pattern — prior art, and what ALDC should actually run

**Named prior art, with what each contributes:**

| System | The contribution | Adoptable by ALDC? |
|---|---|---|
| **AWS STS `AssumeRole` + session policy** | The canonical scoped-down short-lived credential: *"The resulting session's permissions are the intersection of the role's identity-based policy and the session policies."* 900 s min, up to 12 h. `DOCUMENTED*` | Not directly (no AWS), but it is the reference semantics to copy: **intersection, not replacement** |
| **HashiCorp Vault / OpenBao dynamic secrets** | Per-lease identity with automatic revocation on expiry | Possible; heavy for four people |
| **Teleport Machine & Workload Identity** | Short-lived X.509/JWT to workloads, SPIFFE-compatible, with a complete audit log | No — enterprise-shaped |
| **SPIFFE/SPIRE** | Attest the workload against platform facts (node, ServiceAccount, container) and issue a short-lived SVID; default X.509-SVID TTL **1 hour**, proactively renewed at 50% of TTL. `REPORTED` | No — needs a platform to attest against |
| **HashiCorp Boundary** | Session brokering with credential injection so the user never sees the credential | **Could not verify** from primary docs |
| **Claude Code `sandbox.credentials` masking** | *"the sandboxed command sees a per-session sentinel value instead of the real one … When a request leaves the sandbox for one of them, the sandbox proxy replaces the sentinel with the real value. The command and anything it logs never hold the real credential, but its requests still authenticate."* `DOCUMENTED` | **Yes — today, zero build** |
| **Docker Sandboxes proxy injection** | Same shape, at the microVM boundary | Yes, if Windows support checks out |
| **Claude Code on the web** | *"a separate proxy holds your GitHub token outside the sandbox while issuing scoped credentials for repository access inside it"* `DOCUMENTED` | Reference architecture |

**The generalisable name:** this is the **PDP/PEP split** from XACML — the *decision* point is a
separate principal from the *enforcement* point, and the enforcement point sits on the data path.
Combined with **capability tokens** (and macaroons, for tokens that can be attenuated but never
widened), the agent presents a token naming *verbs*, never a credential naming an *identity*. That
is the correct formal reading of §4's "a role with no grant on prod is a control". `REASONED`

**Recommended stack for ALDC, cheapest first:**

1. **The egress proxy holds the secrets and injects them** (Claude Code masking + `injectHosts` +
   `network.tlsTerminate`, or `srt` standalone). Build cost ~0 — it is configuration. This alone
   moves the estate off "the agent runs with the operator's credentials", which is the single
   MEASURED fact §2 of the strawman is built to fix. Note two documented constraints: masking
   *requires* TLS termination at the proxy, and mask entries are honoured only from user, managed
   or `--settings` scope — *"`mask` entries … are all ignored in a repository's
   `.claude/settings.json`"* — which is exactly the right pinning behaviour. `DOCUMENTED`
2. **A local credential broker with its own identity** (~200 lines, one process): holds the
   Snowflake key-pair private key; on request, checks the run's declared tier against a static
   table; mints a 60-minute JWT for the tier's role, or a role-restricted PAT it revokes on run
   exit; appends `granted` and `refused` to an append-only log. The broker, not the agent, is the
   principal that can revoke. `BET` — but see §2.5 on why the refusal log is the point.
3. **Azure managed identity + Snowflake WIF** once the runner moves off the laptop. This is R3's
   recommendation and it stands.
4. **Vault/OpenBao** only when the number of distinct secrets makes hand-rolling worse than
   operating a server.
5. **Teleport / SPIRE** — not for four people on one Windows machine.

Running cost of (1)+(2): zero marginal infrastructure — both run on the same box as the agent. The
real cost is the allowlist churn measured in §2.2.

---

### 2.5 The refusal as evidence — how to make 0-of-22 honest

**The estate already owns the principle.** `tests/test_evaluator_isolation.py`, line 3:

> *"a boundary nobody has watched reject something is a diagram, not a control. So every test here
> makes the evaluator *say no* to a specific attack an agent with shell and repo write could
> actually mount."* `MEASURED` (read from the repo)

So the practice exists at unit-test level and is missing at runtime-gate level. That is the whole
gap.

**Prior art for proving a deny actually denies:**

| Practice | What it gives | Where it comes from |
|---|---|---|
| **Negative controls** | An assay that cannot produce a negative is not measuring | Bench science; R1 already invoked it — *"exactly the kind of evaluator defect negative controls should expose"* |
| **`opa test`** | Rules prefixed `test_`, results PASS/FAIL/ERROR, **plus coverage** — *"If the line refers to the head of a rule, the body of the rule was never true"* — i.e. a machine-checkable "this deny has never fired" detector | `DOCUMENTED*` openpolicyagent.org/docs/policy-testing |
| **OpenFGA assertions** | *"an object that contains a tuple key, and the expectation of whether a call to the Check API of that tuple key will return true or false"* — you store the `false` cases next to the model and run them in CI | `DOCUMENTED*` |
| **AWS IAM policy simulator / `simulate-principal-policy`** | Evaluates a policy without making real requests — cheap, but proves the *policy*, not the *enforcement point* | `DOCUMENTED*` |
| **Kubernetes PSA `audit` / `warn` modes** | Run the policy non-enforcing and count what it *would have* refused. The cheapest honest route to a non-zero refusal count | `DOCUMENTED*` |
| **Google DiRT** | Annual company-wide multi-day disaster drills; *"developed to find vulnerabilities in critical systems and business processes by intentionally causing failures in them"* — Krishnan, CACM 55(11):48–52 (2012) / ACM Queue 10(9):30 | `REPORTED` |
| **Security chaos engineering** | Fault injection aimed at controls; the named control-efficacy metrics are literally *"egress blocks, IAM denies, and segmentation hits"* | `REPORTED` |

**The single most copyable artefact — and it is already in an Anthropic repo.**
`.devcontainer/init-firewall.sh` ends with a two-sided assertion and refuses to finish booting if
either side is wrong:

```bash
if curl --connect-timeout 5 https://example.com >/dev/null 2>&1; then
    echo "ERROR: Firewall verification failed - was able to reach https://example.com"
    exit 1
...
if ! curl --connect-timeout 5 https://api.github.com/zen >/dev/null 2>&1; then
    echo "ERROR: Firewall verification failed - unable to reach https://api.github.com"
    exit 1
```
`DOCUMENTED` — `raw.githubusercontent.com/anthropics/claude-code/main/.devcontainer/init-firewall.sh`

A negative control **and** a positive control, run at every sandbox boot, non-zero exit on failure.
Copy this verbatim, per tier. It produces a refusal event on every single run.

**⚠ The trap in the current gate, and it matters.** `factory/readiness.py :: g_gates_can_refuse`
(line 269) is:

```python
rejected = [e for e in _events(runs)
            if "reject" in str(e.get("event_type", "")).lower()]
...
if rejected:
    return _pass(f"a gate has refused {len(rejected)} times", ev, src)
```

All-time, any event type containing the substring `reject`, **with no distinction between a refusal
that happened because something real was attempted and one the system provoked on purpose.** If you
satisfy this gate with boot-time drill refusals, you have built a gate that certifies itself — the
exact failure mode this whole estate exists to stop (233 diagnoses / 0 fixes; a loop that recorded
its own 1.6% success rate and never adjusted).

**Fix, and it is small:** two counters, not one.
- `refusals_organic` — a gate said no to something the agent actually tried.
- `refusals_drilled` — a deliberate negative control, carrying a `drill_id`.

Require **both** non-zero, and make the gate FAIL when the newest drill is older than the
measurement window rather than only when the count is zero. A stale drill and a never-run drill are
the same evidence. `REASONED`

---

### 2.6 Where the tier is enforced — the pattern has a name, and §4 uses the wrong verb

**Yes, it is a known pattern, with three overlapping names:**

1. **Admission control** — a request carries a declared class; a control-plane component validates
   it before the workload starts and can refuse. The closest exact analogue to T0/T1/T2 is
   **Kubernetes Pod Security Admission**: three named levels (`privileged` / `baseline` /
   `restricted`) declared as a namespace *label* — `pod-security.kubernetes.io/<MODE>: <LEVEL>` —
   enforced by a built-in admission controller, with three modes: `enforce`, `audit`, `warn`.
   `DOCUMENTED*` (kubernetes.io `/docs/concepts/security/pod-security-admission/`.)
   This is *literally* "tier declared in the spec, enforced by the control plane", with a shipping
   implementation and years of operational experience. **Steal the vocabulary and the three modes** —
   `audit` mode in particular is how you get a refusal count without breaking anyone's day.
2. **PDP/PEP** (XACML) — decision point separate from enforcement point.
3. **Capability-based security / capability tokens** — the token names verbs, not an identity.
   Policy-as-code admission (OPA Gatekeeper, Kyverno) is the generic implementation.

**The correction §4 needs.** §4 says the tier is *"declared in the agent spec and enforced by the
DECIDE plane."* A control plane that **checks** a tier is admission control; a launcher that
**constructs** the sandbox, the egress allowlist and the credential *from* the tier is the only
version an agent cannot argue its way past. Anthropic's docs draw exactly this line:

> *"Claude Code evaluates permission decisions before a command runs, based on the command string
> … The operating system enforces the sandbox boundary on the running process, so it holds
> regardless of what the model chose to run and even if an allowed command does more than its name
> suggests."* `DOCUMENTED`

**Rule to write into §4: the tier is an input to construction, never a predicate that is
evaluated.** A T1 agent must have *no code path* to a T2 verb, because the T2 credential was never
minted and the T2 host was never in the allowlist.

**Cheapest honest version for one Windows machine:**

- A launcher that reads `tier:` from the AgentSpec and selects **one of three pre-built, immutable
  profiles**. It never merges a per-run override. The resolved profile's hash goes into the run
  audit; a mismatch between declared tier and resolved profile is a refusal event.
- **T0** — existing worktree + `srt` with `allowedDomains: []` (the srt default is *"all network
  access is denied … An empty allowedDomains list means no network access"* `DOCUMENTED`), no
  Snowflake variables in the environment, `credentials.envVars` `deny` entries for the rest.
- **T1** — `srt` Windows profile; allowlist = `<account>.snowflakecomputing.com`,
  `api.anthropic.com`, `github.com`; the broker mints a 60-minute JWT (or a role-restricted PAT it
  revokes on exit) for a role holding only `SELECT`; `DEFAULT_SECONDARY_ROLES = ()` on the agent
  user; per-tier `STATEMENT_TIMEOUT_IN_SECONDS`.
- **T2** — as T1, plus the clone schema and a role with DDL scoped inside the clone only.
- **Make the policy unwidenable** using the documented pinning: managed settings +
  `allowManagedDomainsOnly` + `strictAllowlist`, and note that *"When managed settings configure
  `sandbox.filesystem` at all, or list any `sandbox.credentials.files` entry with `"mode": "deny"`,
  only managed settings can set the key."* `DOCUMENTED` That is the only Claude-Code-native way to
  stop a repository's own `.claude/settings.json` from relaxing the tier.

**The version that survives moving to cloud:** the same AgentSpec, with the launcher's target
swapped to Azure Container Apps Jobs, one user-assigned managed identity per tier×tenant, Snowflake
WIF instead of PATs, and the "profile" becoming a container image digest. **Nothing in the
AgentSpec changes.** That is the test of whether the tier abstraction is right: *if moving to cloud
requires editing the AgentSpec, the tier was a deployment detail, not a capability.* `BET`

---

## 3. What this changes in the spec

Concrete edits to `/home/user/agent-factory/docs/specs/architecture-v0.md` and the code.

### §4 — the isolation ladder

1. **Add a fourth column: "what the workload cannot do to the control itself."** That column is the
   only thing separating a control from a prompt, and it is what makes T0/T1/T2 arguable.
2. **Re-word the T1 row.** "egress allowlist" currently reads as containment. Replace with:
   *"egress allowlist — contains accident and misconfiguration; does **not** prevent exfiltration
   (hostname-based allow decisions are defeatable by domain fronting, per Anthropic's own security
   limitations)."*
3. **Add to T1/T2: `DEFAULT_SECONDARY_ROLES = ()` on the agent user.** As written, "read-only
   warehouse role" is false by default under Snowflake bundle 2024_08.
4. **Change "enforced by the DECIDE plane"** to *"admitted by the DECIDE plane, **constructed** by
   the launcher. The tier is an input to construction, never a predicate that is evaluated."*
5. **Promote R3's line** (`R3-answer-control-plane.md:662`) into §4 as the opening claim: compute
   isolation and credential blast radius are different problems, and for data work the credential is
   the one that matters.

### §5 — the AgentSpec

6. `tier: T2` alone does not determine a sandbox. Add `egress: [hosts]`, `warehouse_role:`,
   `credential_ttl:`, `statement_timeout_s:`.
7. §5 already says *"every field needs a test asserting it reaches the process."* **The test shape
   is the devcontainer's two-sided curl** — for each declared field, assert both that the allowed
   thing works and the denied thing fails, at sandbox boot, exit non-zero on either.
8. `budget.warehouse_credits: 2` is unenforceable as written. Either drop it or back it with
   `STATEMENT_TIMEOUT_IN_SECONDS` (default is **48 hours**) + a dedicated warehouse + a resource
   monitor, and record in the spec that resource monitors overshoot by design.

### §7 — the "where this is wrong" list

9. **§7 item 4 is settled and should be struck.** T1/T2 do **not** require containers on Windows
   via WSL. `@anthropic-ai/sandbox-runtime`'s native Windows alpha gives a kernel-level egress
   fence (WFP, keyed on a dedicated account SID) and NTFS-ACL filesystem isolation with no container
   and no WSL2. Replace item 4 with the real open question: *"the Windows sandbox runtime is alpha
   and unproven on this machine — one afternoon settles it."* Start-up cost remains unmeasured and
   is probably immaterial at 45-minute run lengths.

### §8 — the sequence

10. **Split item 4.** Currently: "T1 container with an egress allowlist." Split into:
    - **4a — T1 sandbox with an egress allowlist** (`srt` on Windows, no container). Days.
    - **4b — the credential broker: the agent stops holding any credential.** Independent of 4a,
      and it is the change that flips the MEASURED "agents run as the user with the user's
      credentials." Arguably **4b before 4a**, because masking + proxy injection already exists as
      configuration and needs no new isolation technology.
11. **Add a new item between 2 and 3: "the first drill."** Boot-time two-sided assertion per tier.
    Hours. It is what gives the `refuses` gate something real to record, and it must land before the
    tier work so the tier work has a way to be wrong.

### §9 — what this does not change

12. **§9's "per-secret approval stays human" survives and gets stronger.** With masking the human
    approves a *host*, not a secret handover, and the agent never holds the value. Add the
    mechanism, because "approval" without a mechanism is where this estate has been burned before.

### Code

13. **`factory/readiness.py :: g_gates_can_refuse` (line 269)** — split `rejected` into
    `refusals_organic` and `refusals_drilled` (the latter carrying `drill_id`); require both
    non-zero; FAIL when the newest drill is older than the measurement window. As written, drill
    refusals would let the gate certify itself.
14. **New `drills/` directory**, one two-sided assertion script per tier, invoked by the launcher at
    sandbox boot, emitting a `gate_rejected` event with `drill_id` on every run.
15. **`factory/lanes.py:157`** — the `refuses` gate is already in the default gate list. It will
    start passing honestly once 13 and 14 land, and not before.

---

## 4. What I could not settle

| Question | Why | What would settle it |
|---|---|---|
| Container start-up cost on Paul's machine | No Docker daemon in this session; no access to the machine | `Measure-Command { docker run --rm python:3.12-slim python -c "pass" }` × 20, WSL2 backend and Hyper-V backend, on the actual box |
| Current Snowflake password-deprecation milestone dates | `docs.snowflake.com` blocked; two sources disagree (Nov 2025 vs Aug–Oct 2026) | Read `docs.snowflake.com/en/user-guide/security-mfa-rollout` directly. **If a deadline is live now this is a schedule input** |
| Whether any Snowflake path gives a sub-day PAT | Found only `DAYS_TO_EXPIRY` in integer days | Read the PAT reference; failing that, use key-pair JWT (60 min) or Snowflake OAuth (600 s) |
| Whether `srt`'s Windows alpha works on Paul's build | Alpha, one-time elevated install, schannel revocation caveat | `npx @anthropic-ai/sandbox-runtime windows-install` then run the devcontainer-style two-sided assertion. One afternoon |
| Whether Docker Sandboxes runs on Windows, and its start-up cost | `docs.docker.com` and the practitioner writeup both blocked | Read `docs.docker.com/ai/sandboxes/` |
| WSL2 escape specifics (CVEs, fix status) | Trend Micro article blocked | Read it before relying on "WSL2 is a VM so it's a hard boundary" |
| Devin's actual sandbox and secrets mechanism | `docs.devin.ai` unreachable; only third-party writeups | Read `docs.devin.ai/cli/sandbox` |
| Boundary's credential-injection semantics | Primary docs unreachable | Read `developer.hashicorp.com/boundary` |
| Vault/HCP real cost | Third-party pricing pages only | HashiCorp's own pricing page |
| gVisor start-up figure | Its own perf doc gives a graph, not a number | Run `perf.py startup --runtime=runsc` |

One further honest gap: **nothing here measures whether a tiered agent is *productive*.** Every
number in this report is about containment. The strawman's §8 item 1 ("run the loop once, for real")
still has to come first, because a T1 agent that cannot finish a ticket is a control with a 100%
false-positive rate, and that is a different failure than the one this report addresses.

---

## 5. Sources

**Read directly (`DOCUMENTED`):**
- https://code.claude.com/docs/en/sandboxing
- https://code.claude.com/docs/en/sandbox-environments
- https://github.com/anthropic-experimental/sandbox-runtime (README)
- https://raw.githubusercontent.com/anthropics/claude-code/main/.devcontainer/devcontainer.json
- https://raw.githubusercontent.com/anthropics/claude-code/main/.devcontainer/Dockerfile
- https://raw.githubusercontent.com/anthropics/claude-code/main/.devcontainer/init-firewall.sh
- https://raw.githubusercontent.com/firecracker-microvm/firecracker/main/README.md
- https://raw.githubusercontent.com/google/gvisor/master/g3doc/architecture_guide/performance.md
- https://raw.githubusercontent.com/MicrosoftDocs/entra-docs/main/docs/identity-platform/configurable-token-lifetimes.md
- `/home/user/agent-factory/docs/specs/architecture-v0.md`
- `/home/user/agent-factory/docs/research/answers/R3-answer-control-plane.md`
- `/home/user/agent-factory/factory/readiness.py`, `factory/lanes.py`, `tests/test_evaluator_isolation.py`

**Vendor docs reached only through a search index (`DOCUMENTED*`, blocked from this sandbox):**
- https://docs.snowflake.com/en/user-guide/programmatic-access-tokens
- https://docs.snowflake.com/en/sql-reference/sql/alter-user-add-programmatic-access-token
- https://docs.snowflake.com/en/sql-reference/sql/alter-user-remove-programmatic-access-token
- https://docs.snowflake.com/en/sql-reference/sql/create-authentication-policy
- https://docs.snowflake.com/en/user-guide/workload-identity-federation
- https://docs.snowflake.com/en/user-guide/key-pair-auth
- https://docs.snowflake.com/en/user-guide/security-mfa-rollout
- https://docs.snowflake.com/en/sql-reference/sql/use-secondary-roles
- https://community.snowflake.com/s/article/default-secondary-roles-all-overview-and-additional-explanations (BCR-1692)
- https://docs.snowflake.com/en/user-guide/oauth-snowflake-overview
- https://docs.snowflake.com/en/user-guide/resource-monitors
- https://docs.snowflake.com/en/user-guide/cost-controlling-controls
- https://developer.hashicorp.com/vault/docs/secrets/databases/snowflake
- https://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRole.html
- https://www.openpolicyagent.org/docs/policy-testing
- https://www.kubernetes.io/docs/concepts/security/pod-security-admission/
- https://www.kubernetes.io/docs/tasks/configure-pod-container/enforce-standards-namespace-labels/
- https://learn.microsoft.com/en-us/virtualization/windowscontainers/manage-containers/hyperv-container
- https://docs.docker.com/ai/sandboxes/network-policies/
- https://docs.cilium.io/en/stable/security/dns/

**Reported (secondary):**
- https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html
- https://www.trendmicro.com/vinfo/us/security/news/virtualization-and-cloud/cracking-the-isolation-novel-docker-desktop-vm-escape-techniques-under-wsl2 (**unread**)
- https://blog.logrocket.com/comparing-ai-agent-sandbox-platforms-e2b-modal-daytona-and-more/
- https://mintlify.wiki/openai/codex/concepts/sandboxing
- https://agent-safehouse.dev/docs/agent-investigations/codex
- https://www.docker.com/products/docker-sandboxes/
- https://andrewlock.net/running-ai-agents-safely-in-a-microvm-using-docker-sandbox/ (**unread**)
- https://docs.devin.ai/cli/sandbox (**unread**)
- https://queue.acm.org/detail.cfm?id=2371516 — Krishnan, "Weathering the Unexpected", ACM Queue 10(9), CACM 55(11):48–52 (2012)
- https://www.usenix.org/conference/lisa15/conference-program/presentation/krishnan — "10 Years of Crashing Google"
- https://spiffe.io/docs/latest/spire-about/use-cases/
- https://goteleport.com/docs/machine-workload-identity/introduction/
- https://auth0.com/blog/continuous-authorization-testing-fga-github-ci-cd/
- https://infisical.com/blog/hashicorp-vault-pricing
- https://medium.com/snowflake/bundle-change-2024-08-default-secondary-roles-to-all-96135d932051
