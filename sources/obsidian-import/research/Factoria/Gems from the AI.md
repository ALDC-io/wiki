# Gem #1:
# The Wrong Way (Common Mistake)

Many people start like this:

User → Agent → Tools → Chaos

Agents start inventing workflows and tool usage.

You lose control of:

state transitions  
security  
side effects  
retries

This is why your **Agent Operating Model document was so important**.


# Gem #2:

# One More Important Insight

When OpenClaw eventually runs, it will **not build the repo**.

Instead it will:

generate dbt files  
generate docs  
call tools

But the **Factoria repo itself should remain human-controlled**.

You can use OpenClaw to **generate code suggestions**, but the platform architecture should stay deterministic.


# Gem #3:
sqlmodel==0.0.16

`SQLModel` combines:

SQLAlchemy + Pydantic

and is excellent for FastAPI.



# Gem #4:
# Why We Use a Schema Instead of the Model

We separate **API schemas** from **database models**.

### Schema (API input)

TicketCreate

What the user sends.

Example:

{  
  "ticket_kind": "DATA_ENGINEERING",  
  "title": "Create fct_orders",  
  "description": "Build fact table from raw orders"  
}

---

### Model (Database)

Ticket

Contains additional fields:

ticket_id  
state  
created_at  
updated_at

These are **system-generated**, not user input.



# Gem #5:

GET /tickets/{ticket_id}/workflow
# What This Endpoint Does

This is **one of the most important endpoints in Factoria**.

It returns the **entire workflow timeline**:

ticket  
workflow run  
workflow events  
current state

Later it will show things like:

TICKET_INTAKE  
↓  
DESIGN_REVIEW  
↓  
PROFILING  
↓  
BUILD  
↓  
QA  
↓  
READY_FOR_REVIEW  
↓  
PR_CREATION

This becomes the **debug UI for autonomous agents**.

![[Pasted image 20260304220222.png]]


# Gem #6:

This is the **same core pattern used by:**

- Temporal
    
- Airflow
    
- Prefect
    
- GitHub Actions
    
- Kubeflow Pipelines
    

But adapted for **AI agents**.

You are effectively building a **next-generation AI automation runtime**.



2026-03-13

![[Pasted image 20260313082747.png]]