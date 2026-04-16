JJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJ





















































































































3G
T'
# Decision #1:
The small improvement is: **make ticket creation “workflow-run aware” from day 1** by adding:

1. a **stable `trace_id`** for the run (used to correlate events/jobs/sessions)
    
2. an **explicit `attempt` number** (retries become run #2, #3…)
    
3. a **single helper** that appends workflow events consistently (so later agents/jobs can use it)
    

This sets you up for clean retries + OpenClaw orchestration without refactors.

### Why this is the “small improvement” that matters

When you later add OpenClaw, you’ll need to correlate:

- agent sessions
    
- runner jobs
    
- workflow events
    

All under one run.

`trace_id` makes that **easy**, and `attempt` makes retries **clean**.

Also, the `append_workflow_event()` helper is the foundation for:

- state transitions
    
- gate approvals
    
- runner job submissions
    
- artifact registration
    
- agent session start/stop
    

Everything becomes an event stream.


# Decision #2:

Create GET /workflows/{workflow_run_id}

# Why This Endpoint Matters

This endpoint is the **core workflow inspection endpoint**.

Later it will expose:

workflow state  
events  
runner jobs  
agent sessions  
artifacts

Which becomes the **Factoria execution timeline**.


# Decision #3:

# The Improvement: State Handler Pattern

Instead of:

if current_state == "TICKET_INTAKE":  
if current_state == "DESIGN_REVIEW":  
if current_state == "PROFILING":

We use a **state → function mapping**.

Benefits:

- cleaner code
    
- easy to add states
    
- agents plug in naturally
    
- OpenClaw integration becomes trivial


# Decision #4:

# Your Architecture Now Looks Like This

API  
 │  
 ▼  
Tickets Endpoint  
 │  
 ▼  
WorkflowRun  
 │  
 ▼  
Orchestrator  
 │  
 ▼  
State Handler  
 │  
 ▼  
Agent  
 │  
 ▼  
Runner Job  
 │  
 ▼  
Artifacts

That is exactly how **autonomous systems should be structured**.


# Decision # 5:

Excellent — **Option A is the correct architecture** for Factoria.  
It keeps the system **secure, modular, and production-ready**.

You will now have a **3-service architecture**:

Factoria API  
      │  
      ▼  
OpenClaw Gateway  
      │  
      ▼  
Agent Runtime

Later we will add the **Runner service**, making the full system:

           +------------------+  
           |   Factoria API   |  
           | (workflow brain) |  
           +---------+--------+  
                     │  
                     ▼  
           +------------------+  
           |  OpenClaw Gateway|  
           |  (agent runtime) |  
           +---------+--------+  
                     │  
                     ▼  
           +------------------+  
           |   Runner Service |  
           |  (dbt / SQL / GH)|  
           +------------------+

This separation is **critical for security** because agents cannot directly execute infrastructure operations.


## Decision #6:

### Runner Execution Service

A new container:

runner/

Responsible for executing:

dbt compile  
dbt build  
snowflake SQL  
git commit  
gh create pr

Agents will **never run shell directly**.


# Decision #6:

# 4️⃣ When To Create The Workspace

Create it **when a workflow_run is created**, not when agents start.

Example location:

api/app/routes/tickets.py

(or wherever you create `WorkflowRun`).

Example:

from app.services.workspace_manager import WorkspaceManager  
  
workspace = WorkspaceManager().create_run_workspace(  
    tenant_id=workflow_run.tenant_id,  
    ticket_id=workflow_run.ticket_id,  
    workflow_run_id=workflow_run.workflow_run_id  
)  
  
workflow_run.workspace_root = str(workspace)  
  
session.add(workflow_run)  
session.commit()

---

# 5️⃣ Why This Matters

This prevents a **huge class of future bugs**.

Without per-run workspace isolation you get:

compile logs overwritten  
QA logs overwritten  
agent artifacts mixed  
retry runs corrupting each other

With this design every run has its own environment.


# Decision  #7 : State Management is crucial for agent workflows

# Why This Matters

Autonomous workflows **must follow this pattern**:

enter state  
↓  
agent executes  
↓  
agent produces artifacts  
↓  
workflow advances

If you reverse it, agents run for the **wrong state**, which is what happened.


# Decision #8: Handling state mapping - separation

|Map|Purpose|Used By|
|---|---|---|
|`STATE_AGENT_MAP`|which **agent runs**|AgentRunner|
|`STATE_ARTIFACT_MAP`|what **artifact file is produced**|Artifact writing|

![[Pasted image 20260306155632.png]]



# Decision 9:  Move to event driven architecture 

# What We Are Changing

Right now your workflow does this:

POST /tickets  
   ↓  
orchestrator.advance()  
   ↓  
run agent  
   ↓  
transition state  
   ↓  
run next agent

That means **agents and transitions are tied together**.

This becomes a problem when agents take minutes or hours.

---

# New Architecture

We change it to:

POST /tickets  
   ↓  
state entered  
   ↓  
AgentRunner starts agent  
   ↓  
agent completes  
   ↓  
agent_complete event logged  
   ↓  
orchestrator.advance()

This is **event-driven orchestration**.

![[Pasted image 20260306161415.png]]


# Decision #10: - Workflow Engine Comparison

![[Pasted image 20260306163818.png]]

