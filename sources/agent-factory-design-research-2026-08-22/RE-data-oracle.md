# R-E — The oracle for data-engineering work, and a corpus that can detect a blind spot

**Researcher note on evidence access, first, because it bounds everything below.**
MEASURED — this session's egress proxy allows `github.com`, `raw.githubusercontent.com` and
`pypi.org`, and **refused every other host I tried**: `docs.getdbt.com`, `docs.datafold.com`,
`docs.reccehq.com`, `learn.microsoft.com`, `arxiv.org`, `dl.acm.org`, `www.vldb.org`,
`www.cs.hku.hk`, `en.wikipedia.org`, `huggingface.co`, `openreview.net`,
`www.semanticscholar.org`, `endjin.com`, `scispace.com` (each returned
`EGRESS_BLOCKED … blocked by the network egress proxy`). Per `/root/.ccr/README.md` §"403 / 407
from the proxy" these are organization policy denials and must be reported, not routed around.

Consequence for tiering: where a doc lives in a git repo I read the primary file and marked it
`DOCUMENTED`. Where the primary doc is on a blocked host, I have only the search index's extract,
and I marked it `REPORTED` even when the source is a vendor reference page that would otherwise
qualify as `DOCUMENTED`. Every such case is labelled "primary unreachable". **Roughly a third of
the vendor claims below are one tier weaker than they should be purely because of the proxy.**

---

## 1. Verdict

There is no single oracle for this work, and the search for one is the error. What exists is a
**ladder of five oracle classes** — structural, internal-consistency, independent-instrument,
**relational/metamorphic**, and **render** — and A1–A12 today occupy only the first three, with
the third (A10) unimplemented and, in the calibration corpus, circular. Every one of the twelve
assertions is a **single-run, single-observation** claim, which means all twelve can be satisfied
simultaneously by a pipeline that is consistently wrong; the estate's own history (a repoint that
passed DAX parity while every visual showed "Error loading data") is exactly that shape. The two
missing rungs are cheap and available: **metamorphic relations** give independence without a
second source-of-truth client (re-run with a different request shape and assert a relation between
the two landings — no ground truth required), and a **mechanically checkable render oracle for
Power BI does exist** — render the report through the embedded JS client in a headless browser
and assert on `visualRendered` events and the absence of known error strings; John Kerski's
`pbi-dataops-visual-error-testing` does precisely this against ten enumerated error messages, and
it needs a service principal and at least PPU capacity. On tooling: **Recce, SQLMesh `table_diff`
and Lakebridge `reconcile` are real substitutes for parts of A8/A10; Great Expectations, Soda,
Elementary and Monte Carlo are not** — they are distributional monitors that answer "does this
look like yesterday", which cannot see a first-ever migration and cannot see request-vs-result at
all. On contracts: **ODCS is worth adopting as the serialisation of the blueprint, and worth
rejecting as the definition of the GreenContract** — ODCS has no vocabulary for provenance
tiering (MEASURED/DERIVED/ASSUMED), for UNMEASURABLE, or for "which tenants were *requested*",
and those three are the whole point of this repo's design. On corpus: the adequacy criterion is
not case count, it is **negative-control kill rate per assertion, stratified by mechanism**, and
the strongest external evidence for that is EvalPlus — adding 80× more test inputs to a *fixed*
set of problems dropped top models' pass@k by 19.3–28.9%, i.e. the corpus was mis-ranking with
the same number of cases.

---

## 2. What the evidence says

### 2.0 The load-bearing finding: the corpus's "independent" instruments are not independent

`MEASURED` — read from `/home/user/agent-factory/evals/corpus/windsorai-2026-08-20.json` and
`factory/calibration.py:40-47`.

Three of the assertions the contract leans on hardest are, in the *positive* calibration case,
**restatements of the landing rather than observations of anything else**:

| Assertion | Its "independent" input | What the corpus actually supplies |
|---|---|---|
| A9 completeness | `p.config(ctx)["accounts"]` = what was *requested* | `world.config.accounts = ["1234567890","9876543210"]` — identical to the set of `account_id` values present in `world.landed.rows` |
| A10 source agreement | `p.source(ctx)["per_key_counts"]` | `{"1234567890": 18, "9876543210": 2}` — sums to 20, exactly the landed row count, and per-key exactly the landed per-key count |
| A12 tenancy scope | `target.allowed_tenants` | `calibration_target()` does `replace(load_target(BLUEPRINT), allowed_tenants=list(_doc()["tenants"]))`, and `_doc()["tenants"]` is the same two ids that appear in `landed.rows` |

The repo is honest about *why* (`calibration.py:41-46`: "so the world and the target cannot drift
apart"), and the blueprint states the principle correctly ("Reading it out of landed rows would
make completeness unfalsifiable"). But the consequence stands: **the positive case proves only
that the assertions do not cry wolf against a self-consistent world.** The mutation cases
(`tests/test_connector_contract.py:154`, `:182`, `:196`) prove each can fail. Neither proves the
assertion has an instrument that could disagree with the landing on a live run — and
`Probes.source()` raises `Unmeasurable` (`factory/connector_contract.py:74`), so **on the first
live run A10 will report UNMEASURABLE, not PASS**. A10 is the contract's only claimed independent
oracle and it is currently a stub.

This is the same class of hole the calibration already caught once (the empty `required_keys`
guard). It is now one level up: not "the check silently did not run" but "the check ran against
its own reflection".

### 2.1 The state of the art in data-change verification

I assessed each against three questions: **what class of wrongness does it catch**, **what does it
structurally miss**, **what would it cost to wire into A1–A12**.

#### Datafold data-diff (value-level diffing)

- `DOCUMENTED` — algorithm, from the repo's own technical doc: it "splits the table into smaller
  segments, then checksums each segment in both databases", achieving "performance within an order
  of magnitude of `count(*)` when there are few/no changes"; on checksum mismatch it recursively
  subdivides until below `--bisection-threshold`, at which point "it will pull down every row in
  the segment and compare them in memory in data-diff". Requires `--key-column` (typically the PK)
  and recommends `--update-column` plus "indexes on the columns you are comparing. Preferably a
  compound index."
  <https://github.com/datafold/data-diff/blob/master/docs/technical-explanation.md>
- `DOCUMENTED` — **the open-source project is dead**: "As of May 17, 2024, Datafold is no longer
  actively supporting or developing open source data-diff." Last release 0.11.2, Python 3.8–3.11.
  <https://pypi.org/project/data-diff/>
- `REPORTED` (primary `docs.datafold.com` unreachable) — Datafold Cloud integrates with dbt Cloud
  CI, posts value-level diff results as a PR comment, and adds column-level lineage for downstream
  impact.
- **Catches:** value-level drift between two materialisations of the same logical table, cheaply,
  at scale. This is a genuine A8/A10-class instrument.
- **Structurally misses:** it compares *two things you already have*. It cannot tell you a row is
  missing from **both** sides, which is precisely the partial-extraction shape. It needs a stable
  primary key — and this estate's own evidence file records that the declared PK
  `(account_id, campaign_id, date)` cannot be right for the measured 20 rows.
- **Cost to wire in:** the OSS tool is unmaintained and Python-3.11-capped; the maintained path is
  a paid cloud product with dbt Cloud coupling this estate does not have (Eclipse → Snowflake →
  Power BI, no dbt). **Verdict: the *algorithm* is worth stealing (checksum-bisect over a key
  range), the *product* is not adoptable here.**

#### Recce (dbt PR review with data checks)

- `DOCUMENTED` — from the repo README: offers "Profile, Value, Top-K, and Histogram Diffs", query
  diff ("write and compare any two queries side by side"), and column-level lineage/impact; and
  critically, "For full diffing capabilities like data comparisons and impact checks, you'll need
  to **prepare two environments to compare against**." Requires Python 3.10–3.12 and a dbt project.
  <https://github.com/DataRecce/recce>
- **Catches:** before/after distribution shifts on a change — the "did this change only what it
  should?" question R8 §0.3 names.
- **Structurally misses:** it is a **human review aid** producing a checklist, not a machine
  verdict; and it is dbt-shaped end to end.
- **Cost:** requires dbt. Not adoptable. **Decoration for this estate**, but the *checklist-travels-
  with-the-PR* idea maps directly onto attaching a `ContractResult` JSON to the PR.

#### SQLMesh

- `DOCUMENTED` — breaking/non-breaking classification: "adding or modifying a model's `WHERE`
  clause is a breaking change because downstream models contain rows that would now be filtered
  out"; contrasted with "an addition of a new column, an action which doesn't affect downstream
  models". Downstream categorisation is inferred: "the categorization of indirectly modified
  downstream models is inferred based on the types of changes to the directly modified models."
  <https://github.com/TobikoData/sqlmesh/blob/main/docs/concepts/plans.md>
- `DOCUMENTED` — `table_diff` does a schema diff ("fields have been added, removed, or changed data
  types") plus a row diff via "an `OUTER JOIN` of the two tables then, for each column with the
  same name and data type, comparing data values"; output includes FULL MATCH / COMMON / SOURCE
  ONLY / TARGET ONLY counts and per-column `pct_match`. **Requirement:** "all models being compared
  must have their `grain` defined that is unique and not null, as this is used to perform the join
  between the tables." Cross-database diffing "requires Tobiko Cloud's specialized cross-database
  feature".
  <https://github.com/TobikoData/sqlmesh/blob/main/docs/guides/tablediff.md>
- `REPORTED` (readthedocs unreachable) — SQLMesh unit tests are declarative YAML with fixed inputs
  and expected outputs, testable at CTE level.
- **Catches:** the strongest *classification* story of anything surveyed — it will tell you a change
  is breaking before you run it, and `table_diff`'s `pct_match` per column is the single most
  directly reusable output shape for an A8/A10 report.
- **Structurally misses:** everything upstream of the warehouse. SQLMesh's world starts at SQL; the
  connector's request-to-API-to-landing path is invisible to it. And `grain` unique-and-not-null is
  the same PK dependency, with the same unresolved question here.
- **Cost:** adopting SQLMesh wholesale is a transformation-framework migration. **But `table_diff`'s
  output contract (schema diff + 4-way row-count split + per-column pct_match) is a ~1-day
  reimplementation in Snowflake SQL and should be A8's report format.**

#### dbt tests / unit tests / contracts + model versions

- `DOCUMENTED` — unit tests: "Unit tests allow you to validate your SQL modeling logic on a small
  set of static inputs *before* you materialize your full model in production." Explicitly
  dev/CI-only: "dbt Labs strongly recommends only running unit tests in development or CI
  environments. Since the inputs of the unit tests are static, there's no need to use additional
  compute cycles running them in production." Stated limitation: they cannot validate whether dbt
  correctly merged/inserted incremental records.
  <https://github.com/dbt-labs/docs.getdbt.com/blob/current/website/docs/docs/build/unit-tests.md>
- `REPORTED` (primary `docs.getdbt.com` unreachable) — model contracts: `contract.enforced: true`
  requires every column's `name` and `data_type`; partial contracts are not allowed. Constraints
  work only on `table` and `incremental` materialisations, never on `ephemeral` or `view`. And the
  sharp bit: `not_null` and `check` constraints "are enforced only after a model is built…dbt
  considers these constraints definable but **not enforced**, which means they're not part of the
  model contract."
- **Catches:** shape. A renamed or retyped column, a dropped column, an added column.
- **Structurally misses:** meaning. A contract that says `spend NUMBER(38,2)` is satisfied by a
  column of zeros, by a column in the wrong currency, and by a table missing an entire account.
- **Cost:** N/A (no dbt). **The transferable idea is `model versions` + deprecation dates** — a
  consumer-facing versioning discipline that this estate's Power BI layer has no analogue of.

#### Great Expectations / Soda / Elementary / Monte Carlo

- `REPORTED` (primary unreachable) — GE: `expect_table_row_count_to_be_between` /
  `_to_equal` are Batch Expectations; cross-table row-count comparison requires **Evaluation
  Parameters**, i.e. a second validation run whose result is fed in. `row_condition` restricts an
  Expectation to a subset.
- `REPORTED` (primary unreachable) — SodaCL has `row_count`, `freshness`, `schema`, `reference`
  (values in column A must exist in column B of another table) and **`reconciliation` checks — but
  "this feature is not supported in Soda Core OSS"**, i.e. source↔target reconciliation is the paid
  tier. <https://docs.soda.io/soda-documentation/soda-v3/sodacl-reference/recon>
- `REPORTED` (primary reachable only via search) — Elementary: `volume_anomalies`,
  `freshness_anomalies`, column-distribution and schema-change tests, running as native dbt tests;
  volume anomalies "split the data into time buckets and calculate the number of rows per bucket
  for a `training_period`, then compare the number of rows per bucket within the detection period."
  <https://github.com/elementary-data/elementary>
- `REPORTED` — Monte Carlo: ML-driven anomaly detection; practitioner and competitor writeups
  consistently report tuning burden and false positives ("noisy assets still need tuning to reduce
  false positives"). I could not find a vendor-primary statement of what it structurally cannot
  detect; **could not verify.**
- `REPORTED` — AWS Deequ ("unit tests for data" on Spark; `VerificationSuite` + `Check` constraints,
  a metrics repository, and anomaly detection over metric history), from Schelter et al.,
  *Automating Large-Scale Data Quality Verification*, PVLDB 11(12):1781–1794, 2018. Primary PDF
  (`vldb.org`) unreachable. <https://github.com/awslabs/deequ>
- **What all four catch:** drift relative to the recent past.
- **What all four structurally miss, and this is the decisive point:** every one of them needs a
  **history** to be anomalous *against*. `windsorai` landed its **first row ever on 2026-08-20**
  after ten attempts and zero completions (`blueprints/windsorai_gep.yaml`). A volume-anomaly
  monitor with a `training_period` has nothing to train on. A migration's first correct run is
  exactly the case where distributional monitoring has zero power. They also cannot express
  request-vs-result: none of them has a place to put "these six accounts were asked for".
- **Verdict: decoration for the migration gate; potentially useful as a *post*-certification
  standing monitor**, which is a different job and should not be conflated with the GreenContract.

#### Databricks Lakebridge `reconcile` — the closest existing thing to A10

- `DOCUMENTED` — four report types: **schema** (column names and types, "verify DDL migration is
  correct", no join columns needed), **row** (hash comparison, "a quick row-level check when there
  is no primary key"), **data** ("row and column values via join columns" with per-column mismatch
  detail), and **all**. Plus a separate `aggregates-reconcile` for counts/sums/averages. Sources
  supported include Oracle, Snowflake, SQL Server, Redshift, Teradata, BigQuery.
  <https://github.com/databrickslabs/lakebridge> (`docs/lakebridge/docs/reconcile/`)
- **Why it matters here:** the **row** report type is the answer to "we do not trust the declared
  primary key". Hash-per-row + set comparison gives a completeness verdict with no PK at all. That
  removes the single largest blocker on the windsorai blueprint (open question #1 in
  `docs/evidence/phase-a-windsorai.md`).
- `REPORTED` (primary `docs.snowflake.com` unreachable) — the Snowflake-native version of the same
  move is `HASH_AGG`, which "returns a 64-bit signed hash value over the set of input columns" and
  is order-insensitive across rows, **with the documented caveat** that "It is possible, though very
  unlikely, that two different input tables will produce the same result for HASH_AGG. If you need
  to make sure that two tables or query results that produce the same HASH_AGG result really
  contain the same data, you must still compare the data for equality (for example, by using the
  MINUS operator)." <https://docs.snowflake.com/en/sql-reference/functions/hash_agg>

#### Summary table — replace, steal, or ignore

| Tool | Replaces an assertion? | Verdict |
|---|---|---|
| Lakebridge `reconcile` (row/data/aggregate) | **A8, and A10's mechanism** | **Steal the design.** Row-hash removes the PK dependency. |
| Snowflake `HASH_AGG` + `MINUS` | **A8 fidelity check** | **Adopt directly.** Two SQL statements. Collision caveat is documented and cheap to close. |
| SQLMesh `table_diff` output shape | A8/A10 *reporting* | **Steal the format** (4-way split + per-column pct_match). |
| data-diff bisect-checksum algorithm | A10 at scale | Steal the algorithm; the tool is dead. |
| dbt contracts / model versions | A9's shape half only | Concept worth copying for the PBI consumer boundary. |
| dbt unit tests / SQLMesh unit tests | A5 (already covered) | Marginal. |
| Recce | nothing (human aid) | Decoration here. |
| Great Expectations / Soda OSS | A9's null/positivity clauses only | **Not worth the dependency** — A9 already does this in 8 lines. |
| Elementary / Monte Carlo | nothing at migration time | **Decoration for the gate**, monitor afterwards. |
| Soda `reconciliation` checks | A10 | Paid tier only. |

---

### 2.2 The downstream render oracle

**The direct answer: yes, a mechanically checkable "the visual actually rendered" test exists for
Power BI, it is open source, and its cost is a service principal plus at least Premium-Per-User
capacity plus a headless browser per report page.**

#### The layers, in ascending order of what they actually prove

**Layer 0 — static analysis of the report layout.** PBI Inspector applies JSON rules to the report
layout / PBIR files.
`DOCUMENTED` — its base ruleset covers "visual count and object density per page", custom visual
usage, chart configuration, accessibility, and page naming; it emits JSON/HTML/PNG/console output
and "ADO outputs Azure DevOps compatible task commands for use in a deployment pipeline"; PNG
output "draws report pages wireframes clearly showing any failing visuals". **Crucially it does
not check that a visual's fields exist in the semantic model** — that is out of scope for the tool.
<https://github.com/NatVanG/PBI-Inspector> (successor: <https://github.com/NatVanG/fab-inspector>)
Catches: convention violations. Misses: everything about data.

**Layer 1 — the model's metadata is reachable.** XMLA endpoint.
`DOCUMENTED` — "Power BI Premium datasets…open-platform connectivity from Microsoft and third-party
client applications and tools" over "the XML for Analysis (XMLA) protocol". Read-only: "Data
visualization applications and tools can query dataset model data, metadata, events, and schema."
Clients listed include SSMS, SSDT, SQL Server Profiler, PowerShell cmdlets, Tabular Editor, DAX
Studio, ALM Toolkit, Excel, Report Builder. Documented limitations include: OLS rules "are
currently not supported", and datasets with push-data via REST API are unsupported.
<https://github.com/MicrosoftDocs/powerbi-docs/blob/live/powerbi-docs/admin/service-premium-connect-tools.md>

**Layer 2 — the model answers a DAX query.** Two routes.
- `REPORTED` (primary `learn.microsoft.com` unreachable) — `Invoke-ASCmd` (SqlServer PowerShell
  module) "enables database administrators to execute an XMLA script, TMSL script, Data Analysis
  Expressions (DAX) query, Multidimensional Expressions (MDX) query, or Data Mining Extensions
  (DMX) statement against an instance of Analysis Services". Module v21+ on PS 5.1, v22+ on PS 7.x.
- `REPORTED` (primary unreachable) — the Power BI REST `Execute Queries` API: DAX only ("MDX, INFO
  functions and DMV queries are not supported" on the older endpoint); a query requesting more than
  one table or more than the allowed row count returns limited data plus an error; **Pro and PPU are
  limited to 40 query requests per minute per user**; service principals unsupported for datasets
  with RLS or SSO.
- `DOCUMENTED` — the practitioner pattern on top of this is Kerski's **DAX Query View Testing
  Pattern**: every test is a DAX query returning a fixed 4-column table — `TestName` (string),
  `ExpectedValue`, `ActualValue`, `Passed` (boolean) — held in a DAX query view tab named
  `[name].[environment].test(s)` with environment ∈ {DEV, TEST, PROD, ALL}, covering calculations,
  content (row counts, blanks) and schema (via INFO functions). Run in CI by `Invoke-DQVTesting`
  after a `git diff` identifies changed semantic models; "any failed test will fail the pipeline".
  <https://github.com/kerski/fabric-dataops-patterns/blob/main/DAX%20Query%20View%20Testing%20Pattern/dax-query-view-testing-pattern.md>

**This layer is exactly the estate's "query-layer check is not a render check" rule.** The docs give
the mechanism for why it can pass while visuals fail: `DOCUMENTED` —
> "Data refresh in the Power BI service will fail when the source column or table is renamed or
> removed." … "It fails because the Power BI service doesn't also include a schema refresh." …
> "A renamed or removed column or table at the data source will be removed with a schema refresh,
> and it can break visuals and DAX expressions."
> — <https://github.com/MicrosoftDocs/powerbi-docs/blob/main/powerbi-docs/connect-data/refresh-data.md>

A measure that still resolves will answer a DAX query. A *visual* binds to a specific
column/hierarchy in the report layout; when that binding is dangling the visual renders
"We are not able to identify the following fields" while the measure query still returns a number.
That is the mechanism behind "DAX parity passed while every visual showed Error loading data".

**Layer 3 — the visual actually rendered. This is the real oracle, and it exists.**

`DOCUMENTED` — the embedded client exposes the primitives:
- `report.ts` `allowedEvents` includes `"visualRendered"` and `"renderingStarted"`.
  <https://github.com/microsoft/PowerBI-JavaScript/blob/master/src/report.ts>
- `ISettings` in powerbi-models includes `visualRenderedEvents?: boolean` (opt-in for per-visual
  render events) and — **note this one** — `hideErrors?: boolean`, which would suppress the error
  surface a text-matching oracle depends on. There is a typed `IError { message; detailedMessage?;
  errorCode?; level?; technicalDetails? }`.
  <https://github.com/microsoft/powerbi-models/blob/master/src/models.ts>

`DOCUMENTED` — the assembled tool: **`kerski/pbi-dataops-visual-error-testing`**, "Templates for
testing Power BI reports for broken visuals using Azure DevOps, PowerShell, and Microsoft
Playwright". Its process is: (1) authenticate a service principal, (2) "Generate an embed token for
the report page to be tested", (3) "Verify that the rendered report does not contain broken
visuals". Detection is **string matching against ten enumerated error messages**:
1. "Power BI encountered an unexpected error while loading the model."
2. "Couldn't retrieve the data model."
3. "You don't have permission to view this tile or open the workbook."
4. "Power BI visuals have been disabled by your administrator."
5. "Data shapes must contain at least one group or calculation that outputs data."
6. "Can't display the data because Power BI can't determine the relationship between two or more fields."
7. "The groups in the primary axis and the secondary axis overlap."
8. "This visual has exceeded the available resources."
9. "We are not able to identify the following fields."
10. "Couldn't retrieve the data for this visual."

Prerequisites: service principal with `Report.Read.All` and `Dataset.Read.All`; "Ensure your Power
BI workspace is within at least a Premium Per User Capacity." Stated limitation: "Testing reports
that use composite models does not work due to a limitation with Microsoft's PowerBI-JavaScript
library." <https://github.com/kerski/pbi-dataops-visual-error-testing>

**Critique, which matters given this repo's own rule.** That oracle is an *absence-of-error* check,
and `connector_contract.py`'s opening docstring says "Every assertion states a positive fact that
must be observed. None is satisfied by the absence of an error." A ten-string blocklist fails that
rule three ways: a new Power BI error string is invisible to it, `hideErrors: true` silences it,
and a visual that renders *a wrong number* passes it. **The fix is available from the same
primitives:** set `visualRenderedEvents: true`, count `visualRendered` events, and assert
`count == N` where N is the number of visuals declared on that page in the report layout JSON
(which PBI Inspector already parses). That is a positive fact. Combine: `visualRendered` count
equals declared visual count **AND** no `error` event **AND** no blocklisted string. Then keep the
DAX-layer value assertions from Layer 2 for the numbers themselves.

**Layer 4 — server-side render.** `exportToFile`.
`DOCUMENTED` — "The `exportToFile` API enables exporting a Power BI report by using a REST call" to
PDF/PPTX/PNG; asynchronous with polling; result URL "is available for 24 hours". Constraints:
"The report you're exporting must reside in a workspace backed by a Premium, Embedded, or Fabric
capacity", **"not supported for Premium Per User (PPU)"**; "The number of exports (single visuals
or report pages) that can be included in a single exported report is **50**"; "Exported reports
can't exceed a file size of **250 MB**"; R, Python, PowerApps, Visio, ArcGIS and paginated visuals
"aren't supported"; and to avoid a premature capture, "use the 'Rendering' events API" and only
begin the export when rendering is finished.
<https://github.com/MicrosoftDocs/powerbi-docs/blob/main/powerbi-docs/developer/embedded/export-to.md>
**Could not verify** whether a visual that fails to render causes the export *job* to fail, or
whether the error text is simply baked into the returned image. Until that is settled,
`exportToFile` is a **golden-image diffing** oracle (compare PNG to a baseline), not a pass/fail
one — and pixel diffing is notoriously flaky. Layer 3 is the better buy.

#### The general problem, for comparison

- `REPORTED` (Google Cloud docs unreachable) — **Looker Content Validator**: "searches your LookML
  for the model, Explore, and field names that are referenced in your Looker content (Looks and
  dashboards)" and "will show an error for any references your content makes to an unknown LookML
  object". It is explicitly distinguished from the LookML Validator. **This is reference validation,
  not render validation** — it is the direct analogue of the missing Power BI check, and Power BI
  has no first-party equivalent. There is also a first-party CI Content Validator.
  <https://docs.cloud.google.com/looker/docs/content-validation>,
  <https://docs.cloud.google.com/looker/docs/ci-content-validator>
- `REPORTED` — **Spectacles** goes one step further than reference validation: "The SQL validator
  runs queries in your data warehouse to verify the `sql` field in each dimension is valid. To
  avoid consuming resources, queries use `LIMIT 0` and `WHERE 1=2`." Four validators (SQL, Assert,
  Content, LookML) run on PRs. <https://docs.spectacles.dev/cli/reference/sql-validator/>,
  <https://github.com/spectacles-ci/spectacles>. Note `LIMIT 0 / WHERE 1=2` proves *compilability*,
  not *correctness* — the same trap, one layer down.
- `REPORTED` (docs.getdbt.com unreachable) — **dbt exposures** declare downstream consumers with
  `depends_on: [ref(...)]` and enable `dbt build --select +exposure:name`. But "exposures are
  metadata objects, you cannot run or build them" — selecting an exposure builds its *upstream*
  models. **An exposure is a dependency declaration, not a test.** It gives you blast-radius
  selection, which is genuinely useful; it gives you zero verification of the consumer.
- **Tableau:** could not verify any equivalent render oracle. The Metadata API gives lineage;
  I found no documented "this viz rendered" assertion.

**Net: nobody has solved this in general. Power BI is, unusually, the platform where the strongest
mechanical render oracle is actually available, because the embedded JS client exposes per-visual
render events.** That is a fortunate accident for this estate.

---

### 2.3 Data contracts as a design primitive

#### Open Data Contract Standard (ODCS, Bitol / Linux Foundation AI & Data)

`DOCUMENTED` — the full example's top-level keys are:
`apiVersion, kind, id, version, status, name/description, domain, dataProduct, tenant,
authoritativeDefinitions, servers, schema, price, team, roles, slaProperties, support, tags,
customProperties, contractCreatedTs`.
Quality rules appear at both table and column level with fields `metric`, `mustBe` /
`mustBeGreaterThan`, `type` (including `library` for built-in rules), `description`, `dimension`,
`method`, `severity`, `businessImpact`, `schedule`, `scheduler`, `customProperties`. SLA properties
in the example include `latency`, `generalAvailability`, `endOfSupport`, `endOfLife`, `retention`,
`frequency`, `timeOfAvailability`. A JSON Schema ships in the repo
(`schema/odcs-json-schema-v3.1.0.json`), and files are conventionally `*.odcs.yaml`.
<https://github.com/bitol-io/open-data-contract-standard>

#### Data Contract CLI

`DOCUMENTED` — `datacontract test` "connects to a data source and runs schema and quality tests to
verify that the actual data complies with the contract"; supports 18+ sources including Snowflake,
BigQuery, Databricks, Postgres, Kafka, S3, DuckDB, Trino; commands `test`, `lint`, `import`,
`export`, `dbt sync/test`; checks include field presence, type, nullness, uniqueness, row counts and
freshness; there is a GitHub Action wrapper. MIT, Python.
<https://github.com/datacontract/datacontract-cli>, <https://github.com/datacontract/datacontract-action>

#### Schema registry compatibility modes (the strongest prior art on *evolution*)

`REPORTED` (docs.confluent.io unreachable) — BACKWARD (default), BACKWARD_TRANSITIVE, FORWARD,
FORWARD_TRANSITIVE, FULL, FULL_TRANSITIVE, NONE. BACKWARD allows deleting fields and adding fields
with defaults; FORWARD allows adding fields and removing optional ones; transitive variants check
against **all** prior versions rather than only the latest.
<https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html>

#### Is "contract" the right abstraction for a GreenContract? — a split verdict

**What ODCS would gain you, concretely:**
1. A published JSON Schema, so `factory/targets.py`'s "unknown keys raise" becomes a schema
   validation rather than bespoke code.
2. `servers`, `team`, `roles`, `support`, `slaProperties` — sections the blueprint will eventually
   need and would otherwise invent badly.
3. `severity` and `businessImpact` per quality rule — the vocabulary for "which assertions block
   promotion" that A1–A12 currently lacks (everything is `required: true`).
4. Tool interop for free: `datacontract test` can execute an ODCS contract against Snowflake today.
5. A version/status lifecycle (`version`, `status`, `endOfSupport`, `endOfLife`) — this is exactly
   the discipline the Power BI consumer boundary has none of.

**What ODCS structurally cannot express, and these are the three things the repo exists for:**
1. **Provenance tiering.** The windsorai blueprint labels every field MEASURED / DERIVED / ASSUMED /
   INCOMPLETE, in comments, because there is nowhere else to put it. ODCS has `customProperties` and
   `authoritativeDefinitions`, so it *can* be bolted on — but a tier that lives in
   `customProperties` is not validated, and an ASSUMED field that reads as a value is precisely how
   the empty-`required_keys` hole happened.
2. **UNMEASURABLE.** ODCS quality rules are pass/fail with `severity`. There is no vocabulary for
   "the instrument could not run", and `datacontract test` reporting a check as failed-or-passed
   would re-collapse the four verdicts that `factory/contract.py` exists to keep apart. This is the
   same defect as `verify-qa-success` reporting UNMEASURED as `failed` — the one that parked a
   ticket in QA for eleven weeks.
3. **Request-vs-result.** ODCS describes *the dataset*. There is no slot for "these six
   `account_id` values were requested from the vendor", because a data contract's subject is the
   artifact, not the act that produced it. A9 and A12 are assertions about a **request**, and that
   is a genuinely different object.

**Recommendation (`BET`):** adopt ODCS as the **serialisation format of `ConnectorTarget`'s
descriptive half** — schema, quality library rules, SLA, team, versions — and keep a small
ALDC-native section (as `customProperties` with its own JSON Schema, or as a sibling file) for
`requested_scope`, `provenance_tier` and `unmeasurable_policy`. Gained: a validated schema, a
lifecycle, and one-command execution of the boring checks. Lost: nothing, provided the
GreenContract remains the authoritative verdict-holder and `datacontract test` is treated as *one
probe among several*, never as the contract. **Do not let an ODCS PASS enter the system as a
`Verdict.PASS`** — it must arrive as an observation into a probe, exactly like every other fact.

---

### 2.4 Completeness and tenancy — canonical names and negative controls

#### Completeness in ingestion: the canonical vocabulary

The literature name is older than data engineering. It is **batch control totals** from EDP/IT
audit, and the modern data-warehouse packaging is **Audit–Balance–Control (ABC)**.

| Technique | Canonical name | Evidence |
|---|---|---|
| Count of records in a batch, compared source vs target | **record count / item count** (a *control total*) | `REPORTED` — "Control totals can be based on document counts, record counts, quantity totals, dollar totals, or hash totals." IT-audit application controls. <https://www.infosecinstitute.com/resources/management-compliance-auditing/it-auditing-and-controls-a-look-at-application-controls/> |
| Sum of a meaningful measure (spend) source vs target | **control total** / financial total | same |
| Sum of a meaningless key (account ids) purely to detect substitution | **hash total** — "A hash total has no intrinsic meaning" | same |
| Per-step log of rows read/inserted/updated/rejected, plus source–target difference explanation, plus remediation | **Audit, Balance and Control (ABC)** — Audit = the log; Balance = "the ability to explain the difference between source(s) and target(s) in each step"; Control = remediation | `REPORTED` — <https://www.xtivia.com/blog/etl-audit-balance-control-recommendations/> |
| Incremental-load boundary marker | **watermark / high-water mark** | `DOCUMENTED` — "A watermark is a column that has the last updated time stamp or an incrementing key." "The delta loading solution loads the changed data between an old watermark and a new watermark." Four ADF approaches: watermark, change tracking, LastModifiedDate, time-partitioned folder/file name. <https://github.com/MicrosoftDocs/azure-docs/blob/main/articles/data-factory/tutorial-incremental-copy-overview.md> |
| Declaring the expected input set up front and failing if any member is absent | **manifest with mandatory entries** | `DOCUMENTED` — "You can use a manifest to make sure that the COPY command loads all of the required files, and only the required files, for a data load." "The optional `mandatory` flag specifies whether COPY should return an error if the file is not found. The default of `mandatory` is `false`." <https://github.com/awsdocs/amazon-redshift-developer-guide/blob/master/doc_source/loading-data-files-using-manifest.md> |
| Post-load verification query against the load log | **load verification** (`STL_LOAD_COMMITS`), run in the same transaction as the COPY | `REPORTED` — same AWS guide, "Verifying that the data loaded correctly" |
| Row-level fingerprint comparison with no PK | **row-hash reconciliation** | `DOCUMENTED` — Lakebridge `row` report: "generating a hash for each row in the source and target tables and then comparing them" |
| Whole-relation fingerprint | **checksum / aggregate hash** | `REPORTED` — Snowflake `HASH_AGG`, with the documented collision caveat requiring `MINUS` to confirm |
| Metric-level source↔target comparison (counts, sums, averages) | **aggregate reconciliation** | `DOCUMENTED` — Lakebridge `aggregates-reconcile` |

**Note the pattern.** `mandatory: true` in a Redshift manifest is *the same idea* as
`required_keys` in `ConnectorTarget` — and Redshift's default is `false`, which is *the same bug*
the calibration matrix found. The default of a completeness guard is "off", everywhere, and that
is the failure mode.

#### Pagination completeness — the honest answer

`REPORTED`, and weak. There is **no canonical name and no established technique** for proving a
paginated pull was exhaustive. What practitioner sources converge on: validate that page sizes
match the request, that records are non-overlapping and unique across pages, that every page
returned a 2xx, and that the terminal condition (`next_cursor == null`) was actually reached rather
than the loop exiting on an error or a max-pages guard. The structural problem is documented:
"The total number of records in the set is not provided when using cursor pagination, though
certain resources may provide a different endpoint to retrieve this value." So an API-side count
endpoint is the only *proof*; where it does not exist, cursor pagination admits **no completeness
proof at all**, only heuristics. <https://developer.zendesk.com/documentation/api-basics/pagination/paginating-through-lists-using-cursor-pagination/>

**This is a finding for the spec, not a gap in my search:** for a cursor-paginated vendor with no
count endpoint, a completeness assertion must return **UNMEASURABLE**, not PASS. The metamorphic
relations in §2.6 (MR1 partition-union, MR2 date-additivity) are the only available substitute,
because they detect truncation *without* needing a total.

#### Request-vs-result verification

**Canonical name: could not verify.** I found no established term. The nearest established
concepts, each of which captures part of it:
- **Manifest-based load verification** (Redshift, above) — the *closest* structural match: the set
  of things to load is declared out-of-band, and absence is an error.
- **Reference check** (SodaCL: "validate that the values in a column in a table are present in a
  column in a different table") and dbt's `relationships` / `accepted_values` tests — the same
  shape when the "different table" is a control table of requested scope.
- **Balance**, in the ABC sense: "the ability to explain the difference between source(s) and
  target(s)".

The repo has independently arrived at the right design and should name it. I would call it a
**declared-scope assertion**: the scope is an input to the run, recorded before the run, and the
landing is checked against it. The blueprint's comment already states the principle better than
any source I found: *"this list is the requested scope, not the observed landing. Reading it out of
landed rows would make completeness unfalsifiable."*

#### The negative controls that prove each check can fail

These are the mutations that must exist. `tests/test_connector_contract.py` has the first four;
the rest are missing.

| Check | Negative control | Present today? |
|---|---|---|
| A9 completeness | drop one requested account from the landing | ✅ `test_a9_catches_a_partial_extraction_a6_cannot_see` |
| A9 completeness | **empty the requested-scope source entirely** → must be UNMEASURABLE, not PASS | ✅ structurally (raises `Unmeasurable`), but no test asserts the *verdict* is UNMEASURABLE rather than PASS for that path — **add it** |
| A9 completeness | requested scope declares A,B,C; live config observes A,B → **the two disagree** → must be UNMEASURABLE | ❌ missing. This is the tenancy-staleness case the blueprint warns about |
| A9 completeness | all accounts present, one account's rows truncated to page 1 (right keys, wrong counts) | ❌ missing — **A9 cannot catch this by construction**; only A10 or MR1 can |
| A10 source agreement | per-key count off by one on one key | ✅ `test_a10_catches_loaded_consistently_wrong` |
| A10 source agreement | **source probe returns the landing's own counts** (self-reference) → should be detectable | ❌ missing, and this is the live corpus's current state (§2.0) |
| A12 tenancy | a foreign tenant's row present | ✅ `test_a12_catches_another_clients_rows` |
| A12 tenancy | `allowed_tenants` derived from the landing → must not be accepted as a declared scope | ❌ missing — and `calibration_target()` does exactly this |
| A12 tenancy | filter removed; unfiltered pull returns 45 accounts of which 6 are ours → the assertion must fail | ❌ missing (this is MR8) |
| A8 fidelity | emitted 20, landed 19 | ✅ |
| A8 fidelity | emitted 20, landed 20, but **10 of them duplicated and 10 dropped** | ❌ missing — count parity is not content parity; needs row-hash |

---

### 2.5 Corpus construction that can detect a blind spot

Prior work (`docs/research/answers/R1-answer-eval-harness.md`) already settled: 29 cases for a
10%-prevalence blind spot (rule of three, 95%), a **regression corpus** of every semantically
distinct historical failure (explicitly *not* frequency-weighted, because "your observed
distribution is endogenous to a badly broken system"), plus a **challenge corpus** stratified by
mechanism, plus `positive_real_001`. I am not re-litigating that. What the external methodology
literature adds is four things R1 did not cover.

#### (a) Case count is the wrong adequacy criterion — EvalPlus is the proof

`REPORTED` (primary unreachable) — EvalPlus extended HumanEval's **test inputs** by **80×** using
LLM-based and mutation-based input generation, holding the number of *problems* fixed. Result:
top-performing models' pass@k dropped by **19.3–28.9%**, and the authors state that "test
insufficiency can lead to **mis-ranking**".
<https://github.com/evalplus/evalplus>

**Transferable, and this is the single most important item in §5:** the analogue of "80× more test
inputs per problem" for this repo is **more mutations per assertion**, not more corpus cases. The
repo currently has ~1–3 mutations per assertion (`test_every_assertion_has_been_proved_able_to_fail`
enforces ≥1). R1 already noted that "one hand-written mutant per assertion is not an adequacy
criterion". EvalPlus quantifies the cost of stopping there. And the economics are favourable: the
repo's own evidence records replayed scoring at **under a second**, so mutation breadth is nearly
free while live infrastructure is not.

#### (b) SWE-bench Verified — the transferable thing is the *exclusion rule*, not the size

`REPORTED` (openai.com and huggingface.co unreachable) — **93 experienced Python developers**
annotated **1,699** random samples from the SWE-bench test set. Each criterion carried a severity
label in [0,1,2,3]; 0–1 minor, 2–3 severe. Filtering removed any sample where the problem statement
or the FAIL_TO_PASS tests scored ≥2 on the ensemble label, "which is equivalent to filtering out
samples where **any single annotator of three** has flagged an issue with the sample". They
deliberately over-sampled the 1–4h and >4h difficulty bands, then randomly sampled the remainder to
reach **500**.
<https://www.swebench.com/verified.html>, <https://openai.com/index/introducing-swe-bench-verified/>

**Transferable:** (i) each corpus case needs an **independent second reader** who states the
expected verdict *before* seeing the harness's output; (ii) **disagreement is grounds for exclusion,
not debate** — a case three readers cannot agree on is an ambiguous case and will produce a
meaningless score; (iii) deliberately over-sample the hard strata rather than sampling
proportionally. For a 2-person consultancy, "three annotators" is unaffordable; the affordable
version is **one human + a second LLM reader with the blueprint but not the corpus**, and any
disagreement escalates to the human or the case is dropped.

#### (c) τ-bench pass^k — report reliability, not average success

`REPORTED` (arxiv unreachable) — τ-bench introduced **pass^k**: the probability that **all k**
i.i.d. trials on the same task succeed. Measured result: "for the best-performing gpt-4o function
calling agent which has a > 60% average task success, **pass^8 drops to < 25%**."
<https://arxiv.org/abs/2406.12045>, <https://sierra.ai/blog/tau-bench-shaping-development-evaluation-agents>

**Transferable, directly:** this estate's headline metric is "recorded orchestrator runs that
finished with no human: 3 of 14" — a pass@1-shaped number. A certification gate that fires once per
change and passes is a pass^1 measurement. **The corpus should be run k times and the verdict
reported as pass^k**, because a connector migration that is right 60% of the time is not a
migration you can leave unattended, and pass^1 makes it look like one.

#### (d) MLE-bench — the corpus needs its own A11

`REPORTED` (arxiv/openreview unreachable) — MLE-bench curates **75** Kaggle competitions, each with
a complexity rating (low: <2h for an experienced human; medium: 2–10h; high: >10h), local grading
code, and a human leaderboard for comparison. It defends the corpus with two mechanisms: **rule-
breaking detection** (GPT-4o analysing agent logs for violations) and **plagiarism detection**
(the Dolos tool, comparing agent code against top Kaggle notebooks). Best setup (o1-preview + AIDE)
reached at least bronze on **16.9%** of competitions.
<https://arxiv.org/abs/2410.07095>, <https://openai.com/index/mle-bench/>

**Transferable:** the corpus needs anti-gaming instrumentation of its own — the exact analogue of
A11 (`tests_modified`, `gates_bypassed`) but applied at the *corpus* level rather than the run
level. R1 already flagged the critical version of this ("the evaluator and its supposedly pinned
corpus remain inside the agent's write boundary"); `docs/evidence/phase-a-windsorai.md` lists it as
Not Done. MLE-bench is the external precedent that this is standard practice in serious benchmark
construction, not paranoia. Also transferable: the **complexity rating as an explicit stratum**.

#### (e) Mutation testing as adequacy criterion — the settled position

`REPORTED` — mutation score = proportion of seeded artificial faults killed by the suite; it is the
standard adequacy metric and correlates with real-fault detection, but R1 already established the
limit (Papadakis et al.: correlation weak after controlling for suite size). Nothing I found
changes that. **Use mutation kill-rate as a *floor* per assertion, never as a score to maximise.**

#### (f) Property-based testing and stratified sampling

`REPORTED` — pandera generates Hypothesis strategies from a schema ("Pandera models export a
`strategy` method that returns a hypothesis strategy for generating data from the schema"), usable
with `@hypothesis.given` in pytest. <https://pandera.readthedocs.io/en/stable/data_synthesis_strategies.html>
**Transferable but limited**: it generates data *conforming to a declared schema*, which is the
wrong direction — the interesting faults are non-conforming. Its real use here is generating the
**negative** corpus: mutate the schema, generate against the mutant, assert the contract fails.

`REPORTED` — I found **no** data-pipeline-specific fault-injection literature of usable quality.
The chaos-engineering corpus is about infrastructure faults (network partitions, node kills, "state
corruption testing includes cache eviction, data inconsistency, and stale reads"), not about
seeding *semantically wrong rows*. **Could not verify** that anyone has published a fault taxonomy
for data-content faults. The repo's mutation registry is, as far as I can tell, ahead of the
published state of the art on this specific point.

#### (g) Concrete corpus recommendation

Stratify by **mechanism × observability**, and size each stratum, not the whole:

| Stratum | Why it is its own stratum | Min cases |
|---|---|---|
| SILENT-EMPTY (COMPLETED, zero rows) | already shipped twice | 3 |
| PARTIAL (COMPLETED, some keys absent) | the hole calibration found | 4 (one key / all-but-one / page-1-truncation / duplicate-masking-absence) |
| STALE (rows from a prior session) | A7's whole reason | 2 |
| CONSISTENTLY-WRONG (right counts, wrong values) | A9 cannot see it | 3 |
| TENANCY (foreign rows, and unfiltered-key) | ⭐ the named gap | 3 |
| SCOPE-UNKNOWABLE (requested set unavailable/disagreeing) | must yield UNMEASURABLE | 3 |
| INSTRUMENT-DOWN (each probe individually unavailable) | 9 probes × refuse | 9 |
| PREFLIGHT (image/digest/commit/deployment drift) | A3/A4 | 4 |
| POLICY (secret leak, out-of-scope write, test-tree edit, gate bypass) | A11 | 4 |
| RENDER (semantic model refreshes, visual does not) | ⭐ the second named gap | 3 |
| POSITIVE-REAL | must remain real | 1 |

That is **39 cases across 11 strata**, of which ~29 are already achievable by mutation of the
existing world at sub-second cost. **The 29 figure from R1 is per-stratum for a 10%-prevalence
blind spot *within that stratum*, not a total** — the correct reading is that no single stratum
here is yet powered to detect a 10% blind spot, and the honest statement of corpus power is
per-stratum, not global. Do not report a single "corpus size" number.

---

### 2.6 Metamorphic testing — the highest-value transferable idea

#### The literature

`REPORTED` (primary sources on blocked hosts) —
- Metamorphic testing was proposed by **Chen et al., 1998**, "to use metamorphic relations to check
  test results and to generate test cases". A **metamorphic relation (MR)** is "a relation on
  inputs and outputs of multiple test cases" — "axioms about the software under test presented in a
  special form as axioms that contain multiple test cases".
- The core motivation is *the oracle problem*: "even if we do not know the correct output of a
  single input, we might still know the relations between the outputs of multiple inputs."
- Terminology: initial inputs are **source test cases**; MRs transform them into **follow-up test
  cases**.
- The standard survey is Chen, Kuo, Liu, Poon, Towey, Tse & Zhou, *Metamorphic Testing: A Review of
  Challenges and Opportunities*, **ACM Computing Surveys 51(1), 2018**, DOI 10.1145/3143561.
  (Preprint: `cs.hku.hk/data/techreps/document/TR-2017-04.pdf` — unreachable from this session.)
- MR categories (Kanewala & Bieman): (1) **permutative** — change element order; (2) **additive /
  multiplicative / invertive** — change element values; (3) **inclusive / exclusive /
  compositional** — add or remove elements.
- Applied to data specifically: **Auer & Felderer, "Addressing Data Quality Problems with
  Metamorphic Data Relations", 4th Int'l Workshop on Metamorphic Testing (MET '19)**, DOI
  10.1109/MET.2019.00019 — applies MT to data quality with "exemplary application on a big data
  application"; the key observation is that in big-data testing, MRs "may also cover properties of
  the **data itself**", not only of the program.

**Why this is the right fit here, stated plainly:** every one of A1–A12 needs *something outside the
run* to compare against — a source of truth (A10), a declared scope (A9, A12), a pinned digest (A3).
Where that external thing does not exist or cannot be obtained, the assertion is UNMEASURABLE, and
today several are. **Metamorphic relations need nothing external.** They manufacture the second
observation by re-running with a transformed request. For a vendor API with no count endpoint, no
sandbox and no second client, MRs are the *only* available independent instrument.

#### Ten metamorphic relations for a connector migration into Snowflake

Notation: `pull(S, W)` = the landing produced by a run requesting scope `S` over window `W`,
restricted to rows stamped with that run's session id. `Σ_m` = sum of additive metric `m`.

| # | Category | Relation | Detects | Negative control (must break it) |
|---|---|---|---|---|
| **MR1** | inclusive / decompositional | `pull({A,B,C}, W)` ≡ `pull({A},W) ∪ pull({B},W) ∪ pull({C},W)`, compared as a multiset on (key, date, metrics) | **Truncation and tenancy leakage at once.** Per-account pulls cannot share a paging cursor, so a whole-scope pull that silently stops after page N will be a strict subset. This is the check A9 structurally cannot make. | Drop the last page from the whole-scope pull; the union must exceed it |
| **MR2** | additive | `Σ_m pull(S, [d1,d2])` = `Σ_m pull(S,[d1,dm])` + `Σ_m pull(S,[dm+1,d2])`, per key | Off-by-one window boundaries, timezone-shifted date filters, double counting on the seam | Shift the split point by one day in one half only |
| **MR3** | inclusive / monotone | For `W ⊆ W'` and non-negative additive `m`: `Σ_m pull(S,W) ≤ Σ_m pull(S,W')`, **and** the (key,date) set of `W` is a subset of that of `W'` | A filter applied *after* aggregation; a window parameter being ignored | Make the wider pull apply a `LIMIT`; monotonicity breaks |
| **MR4** | identity under repetition | Re-running the identical request under a **new session id** yields a row multiset identical on (PK, metrics) | Vendor-side sampling, non-determinism, non-idempotent MERGE. This is the metamorphic form of A8 and it is what makes "landed == emitted" mean something | Introduce an `ORDER BY … LIMIT` without a tiebreaker; runs diverge |
| **MR5** | permutative | Reordering the requested account list, or the requested field list, does not change the landed content | Cursor state carried across accounts; request-order-dependent server behaviour | Have the connector reuse one cursor object across accounts |
| **MR6** | compositional | `rollup(pull(S,W) at campaign grain) ≡ pull(S,W) at account grain`, for additive metrics only | Hidden filters at one grain; dedup at the wrong level. **And it must *fail* for ratio metrics** — discovering which metrics break it is how you learn which are non-additive | Apply a `WHERE status='ENABLED'` at one grain only |
| **MR7** | exclusive / null | A request scoped to an account with no data must land **exactly zero** rows *and* report COMPLETED *and* A7 must classify it as legitimate-empty (`expect_rows: false`), distinguishably from SILENT-EMPTY | Proves the pipeline can tell "nothing to fetch" from "fetch failed" — the shape this estate shipped twice | Make the connector swallow a 500 and return empty; the two cases must not be indistinguishable |
| **MR8** | ⭐ inclusive / tenancy | In a **T2 ephemeral clone schema only**: `pull(∅_filter, W) ⊃ pull(S, W)`, and `pull(∅_filter,W) \ pull(S,W)` consists **entirely** of tenants ∉ `allowed_tenants` | **The only relation that proves the tenancy filter is doing work** rather than the vendor happening to return only our accounts. Directly addresses the "45 Google accounts, 6 are Navira's" fact in the blueprint | Remove the filter from the scoped pull; it stops being a strict subset. Also: if the unfiltered pull returns exactly `|S|` accounts, the *vendor key* is not what the blueprint claims and the whole A12 premise is wrong |
| **MR9** | multiplicative | Where the connector exposes a unit/currency option, `Σ_m pull(S,W,unit=micros)` = `10^6 × Σ_m pull(S,W,unit=units)` exactly | **Unit drift** — the "spend is 1,000,000× too big" bug that passes every null, positivity and type check and is only caught when a human reads a dashboard | Change the scale factor in the connector; the ratio stops being exact |
| **MR10** | exclusive / projection | Requesting a **subset** of fields returns the same (PK) set and the same values for those fields as the full request projected down | Field-list-dependent server-side filtering; a join that changes cardinality when a dimension is dropped — a classic silent row-multiplier | Add a dimension whose presence fans out rows; PK sets diverge |

Plus one to hold in reserve:

**MR11 (temporal stability / restatement bound)** — re-pulling a window that closed ≥ N days ago
must be identical, or differ within a *declared* restatement tolerance. Detects vendors silently
restating history. It cannot be run at migration time (needs elapsed time), so it belongs to the
standing monitor, not the gate — and this is the one place Elementary's `volume_anomalies` earns
its keep.

**Cost.** MR1 for 6 accounts is 7 runs; MR2 is 3; MR4 is 2; MR5 is 2; MR8 is 2. A full MR suite is
~15–20 connector runs against one date. If a canary run is cheap in absolute terms (one date, one
connector), this is affordable *once per connector migration* and clearly not affordable per commit.
**Recommendation: MR1, MR4, MR7 and MR8 in the promotion gate; MR2, MR3, MR5, MR6, MR9, MR10 in a
one-off certification suite run once per connector and re-run when the connector changes.**

---

## 3. What this changes in the spec

Concrete, against files in `/home/user/agent-factory`.

**A. `factory/connector_contract.py` — the assertion set is under-specified in two places and
circular in one.**
1. **A10 is a stub with a self-referential fixture.** `Probes.source()` refuses; the corpus's
   `world.source.per_key_counts` is arithmetically derived from `world.landed.rows`. Either build a
   real second instrument (an independent API client counting rows vendor-side) or **rename A10 to
   what it is** and add A10′ as the metamorphic relation MR1 — which needs no second instrument.
   Leaving A10 named "independent second instrument" while it is a mirror is the exact failure mode
   the repo was built to prevent.
2. **A8 checks count parity, not content parity.** `len(stamped) != emitted` passes a world where 10
   rows were dropped and 10 duplicated. Add a row-hash: Snowflake `HASH_AGG` over the stamped rows
   compared with a hash the connector emits, with the documented collision caveat closed by `MINUS`
   on mismatch. Lakebridge's `row` report type is the design to copy.
3. **A9 cannot detect per-key truncation.** All requested keys present, one key's rows truncated to
   the first page, and A9 says "N rows satisfy every declared invariant." This is the same *class*
   as the hole already found, one level finer. MR1 is the fix; a page-count or vendor-side count
   assertion is the alternative.
4. **A12 needs a positive proof, not just a filter check.** Add **A13-tenancy-filter-effective**
   (MR8): in a T2 clone, an unfiltered pull must be a strict superset whose difference is entirely
   out-of-scope tenants. Without it, A12 passes trivially whenever the vendor key happens to be
   correctly scoped, and the blueprint's own staleness warning ("A PASS on A12 means 'the landing
   matched what we declared', not 'what we declared is still correct'") stays unaddressed.
5. **Add A14-consumer-renders.** The contract stops at the landing table. The estate's stated rule
   is that a query-layer check is not a render check, and the contract currently has neither. See C.

**B. `blueprints/windsorai_gep.yaml` and `factory/targets.py` — adopt ODCS for the descriptive half.**
Serialise schema, quality library rules, SLA and versions as ODCS v3.1.0 (validated against
`schema/odcs-json-schema-v3.1.0.json`), and keep an ALDC section for the three things ODCS cannot
express: `requested_scope`, `provenance_tier` (MEASURED/DERIVED/ASSUMED — today these live in YAML
*comments*, which is why an ASSUMED field can silently read as a value), and `unmeasurable_policy`.
Wire `datacontract test` in as **one probe**, never as a verdict.

**C. `docs/specs/architecture-v0.md` — the PROVE plane needs a render tier, and it changes the
isolation ladder.**
The ladder (T0 worktree / T1 read-only warehouse / T2 ephemeral clone) has no rung for the consumer
layer. A render check needs: a service principal with `Report.Read.All` + `Dataset.Read.All`, an
embed token, a Premium-Per-User-or-better workspace, and a headless browser. That is a **T3**: it
touches a *published* artifact in a shared tenant, cannot be cloned, and cannot be rolled back.
Specify it explicitly rather than letting a T1 agent acquire report credentials by accident.
Implementation: `kerski/pbi-dataops-visual-error-testing` as the starting point, **plus** the
positive-fact upgrade — `visualRenderedEvents: true`, assert `visualRendered` count equals the
declared visual count from the report layout JSON, assert `hideErrors` is false, assert no `error`
event, and only *then* apply the ten-string blocklist as a secondary net.
Also note for §7 of that doc: **MR8 requires T2 by construction** — an unfiltered pull that returns
another client's rows must land somewhere disposable. That is an argument *for* the ephemeral clone
tier that the strawman does not currently make, and it is a stronger one than parallelism.

**D. `evals/corpus/` — three changes.**
1. Break the `config.accounts` ≡ `landed.account_id` identity in the positive fixture. Add a case
   where the requested scope is a strict superset of what landed (must FAIL) and one where the
   requested scope is unavailable (must be UNMEASURABLE, and a test must assert *that verdict*).
2. Stop deriving `tenants` from the landing in `factory/calibration.py:47`. The calibration target
   should carry a *declared* tenant list that differs from the landed set in at least one case.
3. Restructure to the 11 strata in §2.5(g). Report power **per stratum**; never publish a single
   corpus-size number.

**E. `factory/evals.py` / `factory/certify.py` — report pass^k, not pass@1.**
τ-bench's measured collapse (>60% pass@1 → <25% pass^8) is the reason. A certification that fires
once is a pass^1 measurement and it will overstate readiness for unattended running, which is the
whole point of the factory.

**F. `evals/MANIFEST.sha256` — MLE-bench is the external precedent for corpus-level anti-gaming.**
R1 called the corpus's location inside the agent write boundary Critical; the phase-A evidence
lists it as Not Done. MLE-bench ships log-based rule-breaking detection *and* plagiarism detection
as standard benchmark hygiene. This is not over-engineering.

---

## 4. What I could not settle

1. **Whether `exportToFile` fails on a broken visual.** The docs say unsupported *visual types*
   cause problems and that you should wait for the Rendering event, but nowhere state whether a
   data-bound visual that errors makes the export job fail or simply bakes the error text into the
   PNG. **Settled by:** one experiment — publish a report with a deliberately dangling field
   binding, call `exportToFile`, inspect the job status and the PNG. ~1 hour on a Premium/Fabric
   capacity.
2. **The canonical name for request-vs-result verification.** I found no established term across
   IT-audit, data-engineering or testing literature. Nearest are manifest-mandatory (Redshift),
   reference checks (SodaCL), and "Balance" (ABC). **Settled by:** a literature search I could not
   perform, because ACM DL, IEEE Xplore, arXiv and Semantic Scholar are all egress-blocked.
3. **Monte Carlo's structural limits from a primary source.** Everything I found was competitor
   marketing or practitioner anecdote. **Could not verify.**
4. **Whether a cursor-paginated vendor pull admits any completeness proof at all** absent a count
   endpoint. My reading is no — and therefore that the honest verdict is UNMEASURABLE — but I found
   no authoritative statement of that, only practitioner checklists. **Settled by:** reading the
   Windsor.ai API reference for a count/total endpoint. That is a 10-minute check the operator can
   do and I could not.
5. **Any data-content fault taxonomy.** The chaos-engineering literature covers infrastructure
   faults; I found nothing that enumerates *semantic* data faults for injection. If none exists,
   the repo's mutation registry is novel and should be written up rather than assumed derivative.
6. **The real `windsorai` grain.** Not a research question, but it gates MR1, MR4, MR6 and A8's
   row-hash: 20 rows across 18 campaigns on one date is inconsistent with the declared PK. One
   `SELECT account_id, COUNT(DISTINCT campaign_id), COUNT(*) FROM …` settles it.
7. **A third of the vendor claims above are one evidence tier weaker than they should be** purely
   because `docs.getdbt.com`, `learn.microsoft.com`, `docs.datafold.com`, `docs.reccehq.com`,
   `docs.soda.io`, `docs.snowflake.com`, `docs.confluent.io`, `arxiv.org`, `dl.acm.org` and
   `vldb.org` are blocked by this session's egress policy. **Settled by:** re-running the specific
   fetches listed in §2 from a session whose policy permits vendor documentation hosts. The GitHub-
   hosted subset (Microsoft docs repos, dbt docs repo, SQLMesh, ODCS, Lakebridge, PowerBI-JavaScript,
   powerbi-models, Kerski, PBI Inspector, data-diff, Recce, datacontract-cli, Redshift dev guide,
   azure-docs) is fully verified and needs no re-check.

---

## 5. Sources

**Read directly (primary, `DOCUMENTED`):**
- https://github.com/datafold/data-diff/blob/master/docs/technical-explanation.md
- https://pypi.org/project/data-diff/
- https://github.com/DataRecce/recce
- https://github.com/TobikoData/sqlmesh/blob/main/docs/concepts/plans.md
- https://github.com/TobikoData/sqlmesh/blob/main/docs/guides/tablediff.md
- https://github.com/dbt-labs/docs.getdbt.com/blob/current/website/docs/docs/build/unit-tests.md
- https://github.com/databrickslabs/lakebridge (docs/lakebridge/docs/reconcile/)
- https://github.com/bitol-io/open-data-contract-standard (docs/examples/all/full-example.odcs.yaml; schema/odcs-json-schema-v3.1.0.json)
- https://github.com/datacontract/datacontract-cli
- https://github.com/datacontract/datacontract-action
- https://github.com/MicrosoftDocs/powerbi-docs/blob/live/powerbi-docs/admin/service-premium-connect-tools.md
- https://github.com/MicrosoftDocs/powerbi-docs/blob/live/powerbi-docs/admin/troubleshoot-xmla-endpoint.md
- https://github.com/MicrosoftDocs/powerbi-docs/blob/main/powerbi-docs/connect-data/refresh-data.md
- https://github.com/MicrosoftDocs/powerbi-docs/blob/main/powerbi-docs/developer/embedded/export-to.md
- https://github.com/microsoft/PowerBI-JavaScript/blob/master/src/report.ts
- https://github.com/microsoft/powerbi-models/blob/master/src/models.ts
- https://github.com/kerski/pbi-dataops-visual-error-testing
- https://github.com/kerski/fabric-dataops-patterns/blob/main/DAX%20Query%20View%20Testing%20Pattern/dax-query-view-testing-pattern.md
- https://github.com/NatVanG/PBI-Inspector
- https://github.com/NatVanG/fab-inspector
- https://github.com/awsdocs/amazon-redshift-developer-guide/blob/master/doc_source/loading-data-files-using-manifest.md
- https://github.com/MicrosoftDocs/azure-docs/blob/main/articles/data-factory/tutorial-incremental-copy-overview.md
- https://github.com/awslabs/deequ
- https://github.com/elementary-data/elementary
- https://github.com/spectacles-ci/spectacles

**Reachable only via search index (`REPORTED`, primary blocked by egress policy):**
- https://docs.getdbt.com/docs/mesh/govern/model-contracts
- https://docs.getdbt.com/docs/build/exposures
- https://docs.datafold.com/integrations/orchestrators/dbt-cloud
- https://docs.reccehq.com/
- https://docs.soda.io/soda-documentation/soda-v3/sodacl-reference/recon
- https://docs.soda.io/sodacl-reference/metrics-and-checks
- https://docs.greatexpectations.io/docs/cloud/expectations/expectations_overview/
- https://greatexpectations.io/expectations/expect_table_row_count_to_equal/
- https://docs.snowflake.com/en/sql-reference/functions/hash_agg
- https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html
- https://learn.microsoft.com/en-us/rest/api/power-bi/datasets/execute-queries
- https://learn.microsoft.com/en-us/rest/api/power-bi/datasets/execute-dax-queries
- https://learn.microsoft.com/en-us/powershell/module/sqlserver/invoke-ascmd
- https://docs.cloud.google.com/looker/docs/content-validation
- https://docs.cloud.google.com/looker/docs/ci-content-validator
- https://docs.spectacles.dev/cli/reference/sql-validator/
- https://docs.tabulareditor.com/common/using-bpa.html
- https://raw.githubusercontent.com/microsoft/Analysis-Services/master/BestPracticeRules/BPARules.json (referenced by Tabular Editor CLI `-A` flag)
- https://www.swebench.com/verified.html · https://openai.com/index/introducing-swe-bench-verified/
- https://github.com/evalplus/evalplus
- https://arxiv.org/abs/2406.12045 (τ-bench) · https://sierra.ai/blog/tau-bench-shaping-development-evaluation-agents
- https://arxiv.org/abs/2410.07095 (MLE-bench) · https://openai.com/index/mle-bench/
- https://dl.acm.org/doi/10.1145/3143561 (Chen et al., *Metamorphic Testing: A Review of Challenges and Opportunities*, ACM CSUR 51(1), 2018)
- https://dl.acm.org/doi/10.1109/MET.2019.00019 (Auer & Felderer, *Addressing Data Quality Problems with Metamorphic Data Relations*, MET '19)
- https://www.cs.colostate.edu/~bieman/Pubs/KanewalaBiemanISSRE2013preprint.pdf (MR categories)
- https://www.vldb.org/pvldb/vol11/p1781-schelter.pdf (Deequ, PVLDB 11(12):1781–1794)
- https://pandera.readthedocs.io/en/stable/data_synthesis_strategies.html
- https://www.xtivia.com/blog/etl-audit-balance-control-recommendations/ (ABC)
- https://www.infosecinstitute.com/resources/management-compliance-auditing/it-auditing-and-controls-a-look-at-application-controls/ (batch control totals, hash totals)
- https://developer.zendesk.com/documentation/api-basics/pagination/paginating-through-lists-using-cursor-pagination/

**Repo files cited (`MEASURED`):**
`/home/user/agent-factory/factory/connector_contract.py`,
`factory/contract.py`, `factory/calibration.py`,
`blueprints/windsorai_gep.yaml`,
`evals/corpus/windsorai-2026-08-20.json`,
`tests/test_connector_contract.py`,
`docs/evidence/phase-a-windsorai.md`,
`docs/research/answers/R1-answer-eval-harness.md`,
`docs/research/R8-data-engineering-agent-factory.md`.
