# Enterprise Agentic Support

A production-style **agentic AI customer support system** built to demonstrate enterprise GenAI architecture patterns including structured LLM outputs, LangGraph orchestration, PostgreSQL-backed tools, deterministic validation, RAG, MCP, human-in-the-loop workflows, evaluations, and observability.

The project is intentionally developed incrementally so each architectural component can be tested and understood independently.

---

## Problem Statement

Build an enterprise agentic AI support system that can understand customer issues, maintain workflow state, retrieve customer and transaction data, reason about the appropriate resolution, retrieve company policies, interact with enterprise systems through tools, and safely execute or escalate actions using deterministic validation and human approval when required.

---

## Current Architecture

The currently implemented workflow is:

```text
                         User Request
                              │
                              ▼
                     Intent Classification
                              │
                              ▼
                        LangGraph State
                              │
                              ▼
                      Customer Lookup
                              │
                              ▼
                         PostgreSQL
                              │
                              ▼
                    Transaction Lookup
                              │
                              ▼
                         PostgreSQL
                              │
                              ▼
                             END
```

Current LangGraph execution:

```text
START
  │
  ▼
classify_intent
  │
  ▼
load_customer
  │
  ▼
load_transactions
  │
  ▼
END
```

---

## Planned Architecture

The final system will evolve toward:

```text
                         Client
                           │
                           ▼
                      FastAPI API
                           │
                           ▼
                Request / Schema Validation
                           │
                           ▼
                  Intent Classification
                           │
                           ▼
                   Conversation State
                           │
                           ▼
                 LangGraph Orchestrator
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
         RAG           Tool Calling      Ask User
          │                │
          ▼                ▼
   Policy Knowledge      MCP Client
       Base                │
                           ▼
                       MCP Server
                ┌──────────┼──────────┐
                ▼          ▼          ▼
               CRM      Billing     Tickets
                │          │          │
                └──────────┼──────────┘
                           ▼
                   Workflow Reasoning
                           │
                           ▼
                  Structured Decision
                           │
                           ▼
                Deterministic Validation
                           │
               ┌───────────┴───────────┐
               ▼                       ▼
           Execute                 Human Review
               │                       │
               └───────────┬───────────┘
                           ▼
                    Response Generation
                           │
                           ▼
                         Client
```

Cross-cutting concerns will include:

```text
Observability
Tracing
Evals
Security
Retries / Timeouts
Cost Monitoring
Latency Monitoring
Audit Logging
```

---

## Technologies

Current stack:

* Python
* FastAPI
* LangGraph
* LangChain OpenAI
* OpenAI
* Pydantic
* SQLAlchemy
* PostgreSQL
* Psycopg
* Docker

Planned additions:

* pgvector
* RAG
* MCP
* Langfuse
* Human-in-the-loop workflows
* Automated evaluation framework

---

## Project Structure

```text
Enterprise-agentic-support/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── repositories.py
│   ├── tools.py
│   ├── schemas.py
│   ├── state.py
│   ├── intent.py
│   └── graph.py
│
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## Database

The project uses PostgreSQL as the main application database.

Current tables:

```text
customers
transactions
```

Example customer data:

```text
C1001
Alice Smith
alice@example.com
active
```

Example transactions:

```text
T1001 | C1001 | $49.99 | subscription | completed
T1002 | C1001 | $49.99 | subscription | completed
```

This allows the application to test scenarios such as duplicate billing.

---

## Intent Classification

The intent classifier uses an LLM with a structured Pydantic output.

Supported intents:

```text
billing_issue
refund_request
technical_issue
account_issue
unknown
```

Example input:

```text
I was charged twice for my subscription
```

Example structured output:

```text
intent='billing_issue' confidence=0.95
```

The classifier does not return arbitrary prose. Its output must conform to the `IntentResult` schema.

Example schema:

```python
class IntentResult(BaseModel):
    intent: Literal[
        "billing_issue",
        "refund_request",
        "technical_issue",
        "account_issue",
        "unknown",
    ]

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )
```

---

## LangGraph State

The workflow maintains shared state as it moves between nodes.

Initial state:

```json
{
  "customer_id": "C1001",
  "message": "I was charged twice for my subscription"
}
```

After intent classification:

```json
{
  "customer_id": "C1001",
  "message": "I was charged twice for my subscription",
  "intent": "billing_issue",
  "intent_confidence": 0.95
}
```

After loading the customer:

```json
{
  "customer_id": "C1001",
  "message": "I was charged twice for my subscription",
  "intent": "billing_issue",
  "intent_confidence": 0.95,
  "customer": {
    "id": "C1001",
    "name": "Alice Smith",
    "email": "alice@example.com",
    "status": "active"
  }
}
```

After loading transactions:

```json
{
  "customer_id": "C1001",
  "message": "I was charged twice for my subscription",
  "intent": "billing_issue",
  "intent_confidence": 0.95,
  "customer": {
    "id": "C1001",
    "name": "Alice Smith",
    "email": "alice@example.com",
    "status": "active"
  },
  "transactions": [
    {
      "id": "T1001",
      "amount": 49.99,
      "type": "subscription",
      "status": "completed"
    },
    {
      "id": "T1002",
      "amount": 49.99,
      "type": "subscription",
      "status": "completed"
    }
  ]
}
```

---

## Sample Execution

Run:

```bash
python - <<'PY'
from app.graph import support_graph

result = support_graph.invoke({
    "customer_id": "C1001",
    "message": "I was charged twice for my subscription",
})

print(result)
PY
```

Sample output:

```python
{
    "customer_id": "C1001",
    "message": "I was charged twice for my subscription",
    "intent": "billing_issue",
    "intent_confidence": 0.95,
    "customer": {
        "id": "C1001",
        "name": "Alice Smith",
        "email": "alice@example.com",
        "status": "active"
    },
    "transactions": [
        {
            "id": "T1001",
            "amount": 49.99,
            "type": "subscription",
            "status": "completed"
        },
        {
            "id": "T1002",
            "amount": 49.99,
            "type": "subscription",
            "status": "completed"
        }
    ]
}
```

---

## Local Setup

Create a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file:

```env
DATABASE_URL=postgresql+psycopg://vrize:vrize_dev_password@127.0.0.1:5433/vrize_agentic_support

OPENAI_API_KEY=your_openai_api_key
```

Do not commit `.env`.

---

## Start PostgreSQL

Start the Docker services:

```bash
docker compose up -d
```

Verify:

```bash
docker compose ps
```

Connect directly to PostgreSQL:

```bash
docker exec -it vrize-postgres psql -U vrize -d vrize_agentic_support
```

View tables:

```sql
\dt
```

Expected tables:

```text
customers
transactions
```

---

## Run FastAPI

Start the API:

```bash
uvicorn app.main:app --reload
```

FastAPI runs at:

```text
http://127.0.0.1:8000
```

Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

Health endpoint:

```text
GET /health
```

Example response:

```json
{
  "status": "ok",
  "database": "configured"
}
```

---

## Current Development Milestones

Completed:

```text
FastAPI setup
        ↓
PostgreSQL Docker environment
        ↓
SQLAlchemy ORM
        ↓
Customer + Transaction models
        ↓
Database repository layer
        ↓
Structured intent classification
        ↓
LangGraph state
        ↓
Customer database lookup
        ↓
Transaction database lookup
```

---

## Next Milestones

### 1. Structured Reasoning

Add a reasoning node that consumes:

```text
intent
customer
transactions
message
```

and returns:

```json
{
  "action": "refund",
  "reason": "Two duplicate completed subscription charges were detected.",
  "requires_approval": false
}
```

### 2. Deterministic Validation

The LLM may propose an action, but business rules will validate whether it is allowed.

Example:

```text
LLM proposes refund
        ↓
Duplicate transaction verified?
        ↓
Refund policy satisfied?
        ↓
Amount exceeds approval threshold?
        ↓
Execute or escalate
```

### 3. RAG

Add internal company policy documents such as:

```text
refund_policy.md
billing_policy.md
security_policy.md
escalation_policy.md
```

Store document embeddings using PostgreSQL + pgvector.

### 4. MCP

Expose enterprise capabilities through MCP servers.

Example:

```text
LangGraph
    ↓
MCP Client
    ↓
MCP Server
├── get_customer
├── get_transactions
├── create_ticket
└── issue_refund
```

### 5. Human-in-the-Loop

Sensitive actions will require manual approval.

Example:

```text
Refund <= $100
→ automatic processing

Refund > $100
→ human approval required
```

### 6. Evals

Measure components independently:

```text
Intent accuracy
Retrieval Recall@K
Tool selection accuracy
Tool argument accuracy
Resolution correctness
Policy compliance
Latency
Cost per request
```

### 7. Observability

Add tracing and monitoring for:

```text
LLM calls
tool calls
retrieval
latency
token usage
cost
errors
workflow transitions
```

---

## Design Principles

This project follows several production AI principles.

### Use deterministic logic when possible

Do not use an LLM for decisions that ordinary application code can reliably perform.

### Use LLMs where ambiguity exists

LLMs are useful for:

```text
intent understanding
reasoning
planning
natural-language generation
```

### Structured outputs over free-form text

Critical system decisions should conform to typed schemas.

### The LLM is not the security boundary

Sensitive actions must be checked by deterministic validation and authorization logic.

### Separate reasoning from execution

The agent may recommend an action, but application code determines whether that action can actually execute.

---

## Target Final Workflow

```text
User
 ↓
FastAPI
 ↓
Intent Classification
 ↓
LangGraph State
 ↓
Customer / Transaction Tools
 ↓
RAG
 ↓
Reasoning
 ↓
Structured Decision
 ↓
Deterministic Validation
 ↓
Human Approval if Required
 ↓
Tool Execution
 ↓
Response
```

The goal is to demonstrate how agentic AI can be integrated into a realistic enterprise software architecture without giving an LLM unrestricted control over business systems.
