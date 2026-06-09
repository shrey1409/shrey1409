# NYPost Conversational AI Chatbot — Master Specification
**Version:** 1.0  
**Author:** Shrey  
**Status:** Active Development  
**Last Updated:** June 2026  
**Classification:** Internal — Confidential

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Business Context](#2-business-context)
3. [Finalized Architecture](#3-finalized-architecture)
4. [LangGraph Node Specifications](#4-langgraph-node-specifications)
5. [Technology Stack](#5-technology-stack)
6. [Knowledge Layer Design](#6-knowledge-layer-design)
7. [Data Strategy](#7-data-strategy)
8. [RBAC & Guardrails Design](#8-rbac--guardrails-design)
9. [Hallucination Prevention Strategy](#9-hallucination-prevention-strategy)
10. [Feature Specifications](#10-feature-specifications)
11. [LangGraph State Schema](#11-langgraph-state-schema)
12. [Prompt Engineering Specifications](#12-prompt-engineering-specifications)
13. [Error Handling & Edge Cases](#13-error-handling--edge-cases)
14. [Environment & Infrastructure](#14-environment--infrastructure)
15. [Development Phases](#15-development-phases)
16. [Open Questions & Blockers](#16-open-questions--blockers)
17. [Decisions Log](#17-decisions-log)

---

## 1. Project Overview

### 1.1 What We Are Building

A **Slack-integrated conversational AI chatbot** that sits on top of NYPost's internal business dashboards and data mart. Users from three teams — Executives, Commerce, and Marketing — can ask natural language questions directly in Slack and receive data-driven, SQL-backed answers in real time.

The system is **not a general-purpose chatbot**. It is a structured, persona-aware, access-controlled analytics assistant. Every response is grounded in actual database results — no hallucinated numbers, no fabricated insights.

### 1.2 Problem Being Solved

NYPost executives and business teams currently need to:
- Navigate multiple dashboards manually
- Wait for ad-hoc analytics team to run queries
- Interpret raw data without business context

This system replaces that workflow with a single Slack interface where any authorized user can ask complex analytical questions and receive summarized, accurate, business-contextualized answers instantly.

### 1.3 Scope of Version 1 (Demo Build)

- Slack as the sole UI
- Three user personas: Executive, Commerce, Marketing
- 2–3 tables per persona (schema-injection approach, not RAG)
- Synthetic data only (compliance requirement — no real client data in sandbox)
- LangGraph orchestration with Claude Sonnet 4.6 as the reasoning model
- Human-in-the-Loop (HIL) for unanswerable queries
- PostgreSQL as the database (sandbox environment)

### 1.4 Scope Explicitly OUT for V1

- RAG / vector database (future enhancement when tables scale to ~100)
- Automated Briefings / Cronjobs (needs cloud environment, cannot demo)
- Data Export Engine (low priority, Phase 2)
- Real client data (blocked by compliance)
- Multi-turn conversational memory (future)

---

## 2. Business Context

### 2.1 User Types and Their Needs

| User Type | Primary Questions | Data Domain |
|-----------|------------------|-------------|
| **Executive** | KPI summaries, churn trends, revenue, MAU/DAU | feature_store, executive_kpi_summary, GA4 aggregates |
| **Commerce** | Affiliate performance, subscription conversions, product revenue | braintree_subscriptions, commerce_metrics |
| **Marketing** | Persona targeting, newsletter performance, campaign ROI | persona_assignments, sailthru_metrics, audience_segments |

### 2.2 Data Sources in Scope

The NYPost data ecosystem spans 8 source systems:
- **GA4** — Web behavior events (confirmed in scope for Executive Dashboard)
- **Braintree** — Payment and subscription transactions
- **Sailthru** — Email/newsletter engagement
- **Pushly** — Push notification performance
- **OpenWeb** — Comment and community engagement
- **Trackonomics** — Affiliate/commerce tracking
- **TransUnion** — Demographic enrichment (PII-sensitive)
- **Zephr** — Identity, entitlements, subscription management

**Gold Layer / Mart:** A pre-aggregated `feature_store` table with one row per registered user, containing 64 pre-computed ML features and persona labels. This is the primary table the chatbot queries.

### 2.3 The 9 Audience Personas (Domain Knowledge)

These are the ML-clustered audience segments the system must understand and reference correctly:

1. **Loyalist** — High-frequency, long-tenure, deep engagement. Core subscription base.
2. **Commerce Reader** — High purchase intent, affiliate-driven behavior.
3. **Casual Visitor** — Irregular visits, low depth, traffic-driven.
4. **Sports Fanatic** — Sports content-dominant, high session frequency during events.
5. **Breaking News Seeker** — High recency, low depth, alert-driven.
6. **Crossword Addict** — Feature-specific engagement, high retention.
7. **Page Six Devotee** — Celebrity/entertainment vertical dominant.
8. **Low Engager** — High bounce, low retention, re-engagement target.
9. **Anonymous Converter** — Converted without prior tracked engagement.

### 2.4 Key Business KPIs the System Must Know

| KPI | Definition | Primary Table |
|-----|-----------|---------------|
| **MAU** | Unique registered users with ≥1 session in calendar month | ga4_events |
| **Churn Rate** | Active subscribers 90 days ago with no login in last 30 days | zephr_users + braintree_subscriptions |
| **Bounce Rate** | Sessions with single page view < 10 seconds / total sessions | ga4_events |
| **Subscription Score** | Float 0–1, propensity to subscribe | feature_store |
| **Churn Score** | Float 0–1, propensity to cancel | feature_store |
| **Commerce Score** | Float 0–1, propensity to purchase | feature_store |
| **Avg Session Duration** | Pre-aggregated seconds per user | feature_store |

---

## 3. Finalized Architecture

### 3.1 The Complete Pipeline

```
[Slack UI]
    ↓
[Slack API]  ← receives POST webhook on every message
    ↓
[Guardrails / RBAC Layer]  ← pure logic, no LLM, validates user access
    ↓
[Agent (Reasoning)]  ← Claude Sonnet 4.6, understands query intent
    ↓
[Persona Decision: Executive / Commerce / Marketing]  ← conditional routing
    ↓
(Injects Specific Table Schema Prompt)  ← knowledge layer, no vector DB for V1
    ↓
[Execute SQL in Database]  ← SQLAlchemy → PostgreSQL sandbox
    ↓
[Human-in-the-Loop Validation]  ← LangGraph interrupt if result is empty/suspect
    ↓
[Agent Summarizes Result / Formats]  ← cheap model (Haiku), plain English output
    ↓
(If presentation requested) → [Export Engine]  ← optional branch, low priority
    ↓
[Slack UI] ← [Slack API]  ← response returned to user's channel
```

### 3.2 Two-Model Architecture

| Role | Model | Why |
|------|-------|-----|
| **Reasoning Agent** | Claude Sonnet 4.6 | Needs nuance, business context understanding, SQL generation quality |
| **Summarizer Agent** | Claude Haiku 4.5 | Pure formatting task — ~20x cheaper, no reasoning needed |

### 3.3 Orchestration Framework

**LangGraph** (confirmed decision).

Reasons LangGraph was chosen over LangChain:
- The persona routing decision is a **conditional edge** — native to LangGraph's graph model
- **HIL (Human-in-the-Loop)** maps directly to LangGraph's interrupt/checkpoint mechanism
- Guardrail placement (pre vs post query) is trivially repositionable — just move a node
- Full pipeline state is inspectable at every step for debugging
- Supports cycles (retry bad SQL) natively
- LangChain is linear chains; this architecture is a stateful branching graph

---

## 4. LangGraph Node Specifications

### Node 1: `slack_ingestion`

**Type:** Entry point  
**LLM:** None  
**Purpose:** Receive and parse the incoming Slack message

**Input (from Slack webhook POST):**
```json
{
  "user_id": "U0123ABC",
  "username": "shrey.dev",
  "channel_id": "C0456DEF",
  "channel_name": "analytics-bot",
  "text": "Show me top 5 personas by session duration this week",
  "timestamp": "1717891234.000100"
}
```

**Output to state:**
```python
state["slack_user_id"] = "U0123ABC"
state["slack_username"] = "shrey.dev"
state["slack_channel"] = "C0456DEF"
state["raw_query"] = "Show me top 5 personas by session duration this week"
state["timestamp"] = "1717891234.000100"
```

**Notes:**
- Must handle Slack retry events (Slack resends if no 200 response within 3 seconds)
- Must filter out bot messages to prevent infinite loops
- Must handle slash commands vs regular messages separately if needed

---

### Node 2: `rbac_check`

**Type:** Logic gate  
**LLM:** None  
**Purpose:** Validate user identity, determine data access permissions, flag PII restrictions

**Input:** `state["slack_user_id"]`

**Process:**
1. Look up user in the access control table using `slack_user_id`
2. Return their allowed roles, allowed tables, and blocked PII columns
3. If user not found → reject with "unauthorized" message back to Slack

**Output to state:**
```python
state["user_name"] = "Shrey"
state["user_roles"] = ["executive", "commerce"]      # can have multiple
state["allowed_tables"] = [
    "feature_store",
    "executive_kpi_summary",
    "braintree_subscriptions",
    "commerce_metrics"
]
state["blocked_columns"] = ["last_name", "email", "address_zip", "hashed_email"]
state["is_authorized"] = True
```

**Access Control Table Schema (to be built):**
```sql
CREATE TABLE user_access_control (
    slack_user_id   VARCHAR(20) PRIMARY KEY,
    user_name       VARCHAR(100),
    roles           TEXT[],           -- array: ['executive', 'commerce']
    allowed_tables  TEXT[],           -- array of table names
    blocked_columns TEXT[],           -- PII columns to never surface
    created_at      TIMESTAMP DEFAULT NOW()
);
```

**Critical Design Decision:**
RBAC answers **"what can this user see"** — it does NOT determine what persona context the query belongs to. That is the Reasoning Agent's job. These are two different questions.

**Edge cases:**
- Multi-role users (e.g., executive + commerce access) → pass all allowed tables to reasoning agent
- User with no matching record → return 401, log attempt
- Empty allowed_tables list → return "You don't have access to any data sources yet"

---

### Node 3: `reasoning_agent`

**Type:** LLM call  
**LLM:** Claude Sonnet 4.6  
**Purpose:** Understand the query intent, determine persona context, identify needed tables, output confidence score

**Input:**
- `state["raw_query"]`
- `state["allowed_tables"]` (from RBAC — constraints the agent must respect)
- `state["user_roles"]`
- Table descriptions (loaded from knowledge layer config file)

**Prompt Template:**
```
You are a data routing agent for NYPost's internal analytics system.
Your job is to analyze a user's query and determine which business 
persona context it belongs to and which tables are needed to answer it.

USER QUERY: {raw_query}

USER'S ALLOWED TABLES: {allowed_tables}

TABLE DESCRIPTIONS:
{table_descriptions}

PERSONA DEFINITIONS:
- executive: High-level KPI summaries, revenue trends, MAU/DAU, 
  churn overview, audience health metrics
- commerce: Subscription conversions, affiliate performance, 
  payment data, product-level revenue
- marketing: Persona targeting, newsletter performance, 
  audience segmentation, campaign ROI

RULES:
1. Only route to personas whose tables the user has access to
2. If the query spans multiple personas, choose the primary one
3. If confidence < 0.75, set needs_clarification = true
4. Never include blocked columns in your table selection

Respond ONLY in this exact JSON format:
{
  "persona": "executive|commerce|marketing",
  "confidence": 0.0-1.0,
  "tables_needed": ["table1", "table2"],
  "reasoning": "one sentence explanation",
  "needs_clarification": true|false,
  "clarification_question": "question to ask user if unclear, else null"
}
```

**Output to state:**
```python
state["routed_persona"] = "executive"
state["routing_confidence"] = 0.91
state["tables_needed"] = ["feature_store"]
state["routing_reasoning"] = "Query asks for persona-level session metrics"
state["needs_clarification"] = False
state["clarification_question"] = None
```

**Cost note:** This is the most expensive call in the pipeline. Optimize the prompt to be as concise as possible while maintaining accuracy.

---

### Node 4: `persona_router`

**Type:** Conditional edge (LangGraph router function)  
**LLM:** None  
**Purpose:** Branch the graph to the correct schema injection path

**Logic:**
```python
def persona_router(state: PipelineState) -> str:
    if state["needs_clarification"]:
        return "ask_clarification"        # → back to Slack, await reply
    
    if state["routing_confidence"] < 0.75:
        return "ask_clarification"
    
    persona = state["routed_persona"]
    routing_map = {
        "executive":  "schema_injector_executive",
        "commerce":   "schema_injector_commerce",
        "marketing":  "schema_injector_marketing"
    }
    return routing_map.get(persona, "ask_clarification")
```

**Edges defined:**
- `ask_clarification` → formats clarification message → `slack_responder`
- `schema_injector_executive` → Node 5 (executive schemas)
- `schema_injector_commerce` → Node 5 (commerce schemas)
- `schema_injector_marketing` → Node 5 (marketing schemas)

---

### Node 5: `schema_injector`

**Type:** Prompt builder  
**LLM:** None  
**Purpose:** Load the relevant table schemas and business rules into a structured prompt for SQL generation

**Input:**
- `state["routed_persona"]`
- `state["tables_needed"]`
- `state["raw_query"]`
- `state["blocked_columns"]`
- Knowledge layer config files (YAML/JSON, loaded at startup)

**What it builds — the enriched prompt:**
```
You are a SQL generation agent for NYPost's PostgreSQL analytics database.

USER QUESTION: {raw_query}

DATABASE SCHEMAS:
{injected_table_schemas}     ← only tables_needed, not all tables

BUSINESS RULES:
{persona_specific_rules}     ← e.g., "always filter is_new_user = FALSE"

COLUMN RESTRICTIONS:
Never include these columns in SELECT or WHERE: {blocked_columns}

EXAMPLE QUERIES:
{few_shot_examples}          ← 2-3 question→SQL pairs for this persona

Generate ONLY a valid PostgreSQL SELECT query. No explanation. No markdown.
```

**Output to state:**
```python
state["enriched_prompt"] = "..."   # full prompt ready for SQL generator
state["injected_schemas"] = {...}  # for HIL cross-checking
```

**Schema injection format (per table):**
```
TABLE: feature_store
Purpose: Gold layer. One row per registered user. Pre-computed ML features.
Grain: One row per user_id. No duplicates.
Columns:
  - user_id (UUID, PK): universal identifier
  - persona_label (VARCHAR): one of [Loyalist, Commerce Reader, 
    Casual Visitor, Sports Fanatic, Breaking News Seeker, 
    Crossword Addict, Page Six Devotee, Low Engager, Anonymous Converter]
  - avg_session_duration (FLOAT): seconds, already aggregated
  - churn_score (FLOAT 0-1): propensity to cancel
  - subscription_score (FLOAT 0-1): propensity to subscribe
  - commerce_score (FLOAT 0-1): propensity to purchase
  - account_age_days (INTEGER): days since registration
  - is_new_user (BOOLEAN): TRUE if account_age_days < 30
  - bounce_rate (FLOAT): ratio of bounce sessions
  - visits_per_week (FLOAT): average weekly visit frequency
ALWAYS APPLY: WHERE is_new_user = FALSE
NEVER USE: last_name, email, address_zip, hashed_email
```

---

### Node 6: `sql_generator`

**Type:** LLM call  
**LLM:** Claude Sonnet 4.6  
**Purpose:** Generate syntactically valid, logically correct PostgreSQL query

**Input:** `state["enriched_prompt"]`

**Output to state:**
```python
state["generated_sql"] = """
    SELECT persona_label, 
           ROUND(AVG(avg_session_duration)::numeric, 1) as avg_duration_seconds,
           ROUND(AVG(avg_session_duration)/60.0, 2) as avg_duration_minutes
    FROM feature_store
    WHERE is_new_user = FALSE
    GROUP BY persona_label
    ORDER BY avg_duration_seconds DESC
    LIMIT 5;
"""
```

**Pre-execution validation (before passing to executor):**
```python
FORBIDDEN_KEYWORDS = ["DROP", "DELETE", "INSERT", "UPDATE", 
                       "TRUNCATE", "ALTER", "CREATE", "GRANT", "REVOKE"]

def validate_sql(sql: str, allowed_tables: list, blocked_columns: list) -> dict:
    sql_upper = sql.upper()
    
    # Check for dangerous operations
    for keyword in FORBIDDEN_KEYWORDS:
        if keyword in sql_upper:
            return {"valid": False, "reason": f"Forbidden keyword: {keyword}"}
    
    # Check only allowed tables are referenced
    # Check no blocked columns appear in SELECT
    
    return {"valid": True, "reason": None}
```

---

### Node 7: `sql_executor`

**Type:** Database call  
**LLM:** None  
**Purpose:** Execute validated SQL against PostgreSQL, return structured result

**Input:** `state["generated_sql"]`

**Execution wrapper:**
```python
async def execute_sql(sql: str, timeout_seconds: int = 30):
    async with engine.connect() as conn:
        try:
            result = await asyncio.wait_for(
                conn.execute(text(sql)),
                timeout=timeout_seconds
            )
            rows = result.fetchall()
            columns = result.keys()
            return {
                "success": True,
                "rows": [dict(zip(columns, row)) for row in rows],
                "row_count": len(rows),
                "columns": list(columns)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "rows": [],
                "row_count": 0
            }
```

**Output to state:**
```python
state["sql_result"] = {
    "success": True,
    "rows": [
        {"persona_label": "Loyalist", "avg_duration_seconds": 487.3, "avg_duration_minutes": 8.12},
        {"persona_label": "Crossword Addict", "avg_duration_seconds": 412.1, ...},
        ...
    ],
    "row_count": 5,
    "columns": ["persona_label", "avg_duration_seconds", "avg_duration_minutes"]
}
state["sql_error"] = None
```

---

### Node 8: `hil_validator`

**Type:** Logic gate + LangGraph interrupt  
**LLM:** None  
**Purpose:** Validate the SQL result before summarization. Interrupt pipeline and escalate to human if result is suspect.

**Triggers for HIL escalation:**
```python
def should_escalate_to_hil(state: PipelineState) -> bool:
    result = state["sql_result"]
    
    # Trigger 1: SQL execution failed
    if not result["success"]:
        return True
    
    # Trigger 2: Empty result set
    if result["row_count"] == 0:
        return True
    
    # Trigger 3: Suspiciously large values (data quality check)
    for row in result["rows"]:
        if row.get("avg_session_duration", 0) > 86400:   # > 24 hours
            return True
        if row.get("churn_score", 0) > 1.0:              # score out of range
            return True
    
    # Trigger 4: Low routing confidence (double-check)
    if state["routing_confidence"] < 0.80:
        return True
    
    return False
```

**When HIL triggers:**
1. LangGraph hits an **interrupt checkpoint** — pipeline state is saved
2. System sends notification to human reviewer (email or Slack DM)
3. Message includes: original query + generated SQL + error/suspicion reason
4. Human reviews and either:
   - **Approves:** pipeline resumes from saved state → goes to summarizer
   - **Rejects/corrects:** human provides corrected SQL or flags as unanswerable
   - **Marks unanswerable:** system sends "I couldn't find data to answer this" to user

**Output to state:**
```python
state["hil_triggered"] = True | False
state["hil_reason"] = "Empty result set for query: ..."
state["hil_resolved"] = False   # updated when human acts
```

---

### Node 9: `summarizer`

**Type:** LLM call  
**LLM:** Claude Haiku 4.5 (cheaper model — pure formatting, no reasoning needed)  
**Purpose:** Convert raw SQL result into clear, business-appropriate English response

**Input:**
- `state["raw_query"]`
- `state["sql_result"]`
- `state["routed_persona"]`

**Prompt Template:**
```
You are a data analyst assistant for NYPost's {persona} team.
Convert the SQL result below into a clear, concise business insight.

ORIGINAL QUESTION: {raw_query}

SQL RESULT:
{formatted_result_table}

FORMATTING RULES:
- For executive: maximum 4 sentences, high-level, dollar/percentage framing
- For commerce: include specific numbers, product/conversion focus
- For marketing: persona-centric language, actionability focus
- Convert seconds to minutes/hours where relevant
- Never mention SQL, tables, or technical details
- If data covers current incomplete period, add: "(Note: current period data may be incomplete)"
- End with one actionable insight where appropriate

Respond in plain text only. No markdown. No bullet points unless listing items.
```

**Output to state:**
```python
state["final_response"] = """
Top 5 personas by average session duration this week:
1. Loyalist — 8.1 minutes
2. Crossword Addict — 6.9 minutes  
3. Sports Fanatic — 6.6 minutes
4. Breaking News Seeker — 3.4 minutes
5. Commerce Reader — 3.1 minutes

Loyalists and Crossword Addicts are spending significantly more time 
per session than other segments. Consider prioritizing these groups 
for subscription upsell campaigns.
"""
```

---

### Node 10: `export_engine`

**Type:** Conditional branch  
**LLM:** None (for V1)  
**Priority:** Low — not required for demo  
**Purpose:** Convert formatted response into a downloadable file if requested

**Trigger detection:**
```python
EXPORT_KEYWORDS = ["export", "report", "download", "send me", "presentation", "csv", "file"]

def export_requested(raw_query: str) -> bool:
    return any(kw in raw_query.lower() for kw in EXPORT_KEYWORDS)
```

**V1 Scope:** Simple CSV export of the raw SQL result. PDF/presentation in later phases.

---

### Node 11: `slack_responder`

**Type:** API call  
**LLM:** None  
**Purpose:** Send the final response back to the user's Slack channel

**What it sends:**
```
[Final formatted response text]

━━━━━━━━━━━━━━━━━━━━━━
📊 Data source: feature_store  |  Queried: 2026-06-08 14:32 UTC
✅ Helpful?   ❌ Wrong context — reroute
```

**Feedback button handling:**
- ✅ → log as successful interaction, no action
- ❌ → prompt user: "Which context did you mean — Executive, Commerce, or Marketing?" → re-run pipeline with override

---

## 5. Technology Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Orchestration** | LangGraph | Latest | Graph-based agent pipeline |
| **LLM Framework** | LangChain | Latest | LLM abstraction layer |
| **Reasoning LLM** | Claude Sonnet 4.6 | `claude-sonnet-4-6` | Query understanding + SQL generation |
| **Summary LLM** | Claude Haiku 4.5 | `claude-haiku-4-5-20251001` | Response formatting |
| **Language** | Python | 3.11 | Primary implementation language |
| **Database** | PostgreSQL | 15 | Sandbox data store |
| **ORM** | SQLAlchemy | 2.x | Safe SQL execution layer |
| **API Server** | FastAPI | Latest | Receives Slack webhooks |
| **Slack** | Slack Bolt SDK | Latest | Slack API integration |
| **Environment** | VS Code + Sandbox | — | Development environment |
| **Dependency Mgmt** | pip / venv | — | Package management |

**Future additions (not V1):**
- pgvector — PostgreSQL extension for vector embeddings (when RAG is needed)
- MLflow — experiment tracking
- Redis — caching layer for repeated queries

---

## 6. Knowledge Layer Design

### 6.1 V1 Approach: Schema-in-Prompt (Confirmed)

For the demo build, the knowledge layer is implemented as **direct prompt injection** — not RAG. The team confirmed this decision due to timeline constraints and the small number of tables (2–3 per persona).

**How it works:**
- Table descriptions, column definitions, and business rules are stored in YAML/JSON config files
- At runtime, the `schema_injector` node loads the relevant config for the detected persona
- This content is injected directly into the SQL generation prompt

**File structure:**
```
knowledge_layer/
├── tables/
│   ├── feature_store.yaml
│   ├── executive_kpi_summary.yaml
│   ├── braintree_subscriptions.yaml
│   ├── commerce_metrics.yaml
│   ├── ga4_events_aggregated.yaml
│   └── persona_assignments.yaml
├── kpi_definitions/
│   ├── churn_rate.yaml
│   ├── mau.yaml
│   ├── bounce_rate.yaml
│   └── subscription_conversion.yaml
├── persona_profiles/
│   ├── loyalist.yaml
│   ├── commerce_reader.yaml
│   └── [all 9 personas].yaml
├── business_rules/
│   ├── global_rules.yaml        ← apply to all queries
│   ├── executive_rules.yaml
│   ├── commerce_rules.yaml
│   └── marketing_rules.yaml
└── few_shot_examples/
    ├── executive_examples.yaml
    ├── commerce_examples.yaml
    └── marketing_examples.yaml
```

### 6.2 Table Description Format (YAML)

```yaml
# knowledge_layer/tables/feature_store.yaml
table_name: feature_store
description: >
  Gold layer pre-aggregated table. One row per registered NYPost user.
  Contains 64 pre-computed ML features used for audience segmentation.
  The primary table for all persona-level analytics queries.
grain: one row per user_id, no duplicates
row_estimate: 66_000_000
always_apply_filter: "WHERE is_new_user = FALSE AND account_age_days >= 30"
join_key: user_id

columns:
  - name: user_id
    type: UUID
    role: primary_key
    description: Universal user identifier, issued by Zephr at registration

  - name: persona_label
    type: VARCHAR
    role: ml_feature
    description: Assigned cluster name from ML pipeline
    valid_values:
      - Loyalist
      - Commerce Reader
      - Casual Visitor
      - Sports Fanatic
      - Breaking News Seeker
      - Crossword Addict
      - Page Six Devotee
      - Low Engager
      - Anonymous Converter

  - name: avg_session_duration
    type: FLOAT
    role: ml_feature
    description: Average session duration in seconds, pre-aggregated
    note: Already averaged — do not re-aggregate with AVG() without GROUP BY persona

  - name: churn_score
    type: FLOAT
    range: 0.0-1.0
    description: Propensity to cancel subscription. >0.7 = high risk.

  - name: subscription_score
    type: FLOAT
    range: 0.0-1.0
    description: Propensity to subscribe. Use for upsell targeting.

  - name: commerce_score
    type: FLOAT
    range: 0.0-1.0
    description: Propensity to make a purchase. Use for commerce targeting.

  - name: bounce_rate
    type: FLOAT
    description: Ratio of bounce sessions. >0.70 = Low Engager signal.

  - name: account_age_days
    type: INTEGER
    description: Days since user registration. >365 = Loyalist signal.

  - name: is_new_user
    type: BOOLEAN
    description: TRUE if account_age_days < 30. ALWAYS filter these out.

pii_columns:
  - last_name
  - email
  - address_zip
  - hashed_email
```

### 6.3 KPI Definition Format (YAML)

```yaml
# knowledge_layer/kpi_definitions/churn_rate.yaml
kpi_name: Churn Rate
business_definition: >
  Percentage of users who had an active subscription 90 days ago
  but have not logged in within the last 30 days.
owner: Executive + Marketing
primary_tables:
  - zephr_users
  - braintree_subscriptions
formula: COUNT(churned_users) / COUNT(active_90d_ago_users)
sql_template: |
  SELECT 
    ROUND(
      COUNT(*) FILTER (
        WHERE last_login < NOW() - INTERVAL '30 days'
        AND subscription_entitlements != 'none'
      )::numeric / 
      NULLIF(COUNT(*) FILTER (
        WHERE created_at < NOW() - INTERVAL '90 days'
        AND subscription_entitlements != 'none'
      ), 0) * 100, 2
    ) as churn_rate_pct
  FROM zephr_users
  WHERE is_new_user = FALSE
threshold:
  concerning: "> 5% monthly"
  target: "< 3% monthly"
time_window_default: last 30 days
important_nuances:
  - Current month data is incomplete — always caveat responses
  - New users (< 30 days) excluded from all churn calculations
  - Cross-validate subscription status with braintree_subscriptions
```

### 6.4 Future RAG Enhancement (Phase 2+)

When the table count grows to ~100, the schema-injection approach becomes too large for a single prompt. At that point:

1. Each table/KPI description document gets converted to a vector embedding using an embedding model
2. Embeddings stored in `pgvector` (PostgreSQL extension)
3. On each query, semantic search finds the top-5 most relevant documents
4. Only those 5 documents get injected into the prompt

This is a drop-in enhancement — the `schema_injector` node is the only component that changes.

---

## 7. Data Strategy

### 7.1 Synthetic Data (Mandatory for V1)

**Hard compliance rule:** No real client data can be loaded into the sandbox environment. This is a cybersecurity/compliance requirement, not a preference.

**Approach:**
1. Get table schema + column descriptions from the two source teams (Dashboard team + Ad-hoc Analytics team)
2. Get a 20–30 record sample to understand data distributions and realistic value ranges
3. Generate synthetic data that mirrors real distributions without containing any real user data
4. Load synthetic data into PostgreSQL sandbox

**Synthetic data generation requirements per table:**
- Match column data types exactly
- Match realistic value ranges (e.g., session_duration 30–600 seconds, not 0–999999)
- Maintain referential integrity (user_ids consistent across tables)
- Realistic persona distribution (roughly matching known NYPost proportions)
- Include edge cases (NULL values, boundary values) for testing

### 7.2 Data Flow Into Sandbox

```
Source Teams deliver:
  - Table schemas (DDL)
  - Column descriptions
  - 20-30 sample records (anonymized if possible)
        ↓
Shrey/Savitha generate synthetic dataset
        ↓
Manual transfer to sandbox via collaborator folder
        ↓
Load into PostgreSQL sandbox
        ↓
Pipeline connects and queries
```

### 7.3 Tables Confirmed In Scope (V1)

**PENDING** — awaiting delivery from:
- Dashboard Team: their most important tables + column descriptions
- Ad-hoc Analytics Team: their most important tables + column descriptions

**Confirmed data source:** GA4 — Executive Dashboard is entirely GA4-based (confirmed by Subhatosh).

---

## 8. RBAC & Guardrails Design

### 8.1 Role-Based Access Control

**Decision: RBAC runs BEFORE the reasoning agent (pre-query).**

Rationale: If a user doesn't have access to a table, the agent should never generate SQL against it. Blocking at the start is cheaper, safer, and prevents the model from even reasoning about forbidden data.

**Role → Table Mapping (to be finalized with actual table names):**

| Role | Accessible Tables | PII Restricted |
|------|------------------|----------------|
| **executive** | feature_store, executive_kpi_summary, ga4_aggregated | last_name, email, address_zip |
| **commerce** | braintree_subscriptions, commerce_metrics, feature_store | email, last_name, hashed_email |
| **marketing** | persona_assignments, audience_segments, feature_store | all PII columns |
| **admin** | all tables | none |

**Multi-role users:** A user with `["executive", "commerce"]` roles receives the union of both allowed_tables lists. The reasoning agent then determines which persona context the specific query belongs to.

### 8.2 PII Guardrails

Two enforcement points:
1. **Pre-query:** `blocked_columns` list is passed to `schema_injector` — these column names are explicitly excluded from the schema prompt so the LLM never learns to reference them
2. **Post-execution (safety net):** Before passing result to summarizer, strip any rows/columns matching blocked_columns list

**PII columns that must NEVER appear in responses:**
- `last_name`
- `email`
- `address_zip`
- `hashed_email`
- `first_name` (in most contexts)
- Any column from TransUnion enrichment table

### 8.3 Query Safety Guards

The `sql_executor` node enforces:
```python
FORBIDDEN_SQL_KEYWORDS = [
    "DROP", "DELETE", "INSERT", "UPDATE",
    "TRUNCATE", "ALTER", "CREATE", "GRANT",
    "REVOKE", "EXEC", "EXECUTE", "CALL"
]
MAX_RESULT_ROWS = 1000          # prevent data dumps
QUERY_TIMEOUT_SECONDS = 30      # prevent runaway queries
```

---

## 9. Hallucination Prevention Strategy

Hallucination in this system means: the LLM's response contains numbers, facts, or claims not present in the actual SQL result.

### 9.1 Four-Layer Defense

**Layer 1 — Grounding (structural prevention):**
Every numerical claim in the response must come from the SQL result. The summarizer prompt explicitly states: "Only include figures that appear in the SQL result provided."

**Layer 2 — Confidence gating (routing prevention):**
If routing confidence < 0.75, don't proceed — ask for clarification. Wrong persona context = wrong SQL = wrong data = hallucinated answer.

**Layer 3 — HIL validation (mid-pipeline catch):**
Empty results, SQL errors, or out-of-range values trigger human review before any response is generated.

**Layer 4 — User feedback loop (post-delivery catch):**
Every response includes ✅/❌ feedback buttons. ❌ triggers logging + re-route option. Misroutes are logged as few-shot training signals for future prompt improvement.

### 9.2 Source Attribution

Every response includes:
```
📊 Data source: {tables_queried}  |  Queried: {timestamp}
```

This makes errors auditable and builds user trust.

---

## 10. Feature Specifications

### 10.1 Feature Priority Matrix

| Feature | Priority | V1 Demo | Notes |
|---------|----------|---------|-------|
| Slack Integration | **Critical** | ✅ Yes | Already done |
| RBAC / Guardrails | **Critical** | ✅ Yes | Pre-query enforcement |
| Persona Routing | **Critical** | ✅ Yes | LangGraph conditional edge |
| Schema Injection | **Critical** | ✅ Yes | Awaiting table descriptions |
| Text-to-SQL | **Critical** | ✅ Yes | Core capability |
| HIL Integration | **High** | ✅ Yes | LangGraph interrupt |
| Summarization | **High** | ✅ Yes | Haiku model |
| Feedback Buttons | **Medium** | ✅ Yes | ✅/❌ in Slack |
| Automated Briefings | Low | ❌ No | Needs cloud + can't demo |
| Data Export | Low | ❌ No | Phase 2 |
| RAG / Vector DB | Future | ❌ No | When ~100 tables |

### 10.2 Human-in-the-Loop (HIL) Specification

**Trigger conditions:** Empty result, SQL error, suspicious values, low routing confidence

**Notification format:**
```
🚨 HIL Required — Query Could Not Be Auto-Resolved

Original query: "Show me churn rate for Loyalists"
Asked by: @shrey.dev in #analytics-bot
Time: 2026-06-08 14:32 UTC

Generated SQL:
[SQL here]

Reason flagged: Empty result set (0 rows returned)

Actions:
[✅ Approve & Send Response]  [✏️ Edit SQL & Retry]  [❌ Mark Unanswerable]
```

**When marked unanswerable:**
```
Bot response to user:
"I wasn't able to find data to answer your question about churn rate 
for Loyalists. This has been flagged for the analytics team to 
investigate. You'll receive a follow-up response shortly."
```

---

## 11. LangGraph State Schema

Complete TypedDict definition for the shared pipeline state:

```python
from typing import TypedDict, Optional

class PipelineState(TypedDict):
    # ── Slack Input ──────────────────────────────────────
    slack_user_id:          str
    slack_username:         str
    slack_channel:          str
    raw_query:              str
    message_timestamp:      str

    # ── RBAC Output ──────────────────────────────────────
    user_name:              str
    user_roles:             list[str]
    allowed_tables:         list[str]
    blocked_columns:        list[str]
    is_authorized:          bool

    # ── Reasoning Agent Output ───────────────────────────
    routed_persona:         str           # "executive" | "commerce" | "marketing"
    routing_confidence:     float
    tables_needed:          list[str]
    routing_reasoning:      str
    needs_clarification:    bool
    clarification_question: Optional[str]

    # ── Schema Injection Output ──────────────────────────
    enriched_prompt:        str
    injected_schemas:       dict

    # ── SQL Generation Output ────────────────────────────
    generated_sql:          str
    sql_validation:         dict          # {"valid": bool, "reason": str}

    # ── SQL Execution Output ─────────────────────────────
    sql_result:             dict          # {"success", "rows", "row_count", "columns"}
    sql_error:              Optional[str]

    # ── HIL Output ───────────────────────────────────────
    hil_triggered:          bool
    hil_reason:             Optional[str]
    hil_resolved:           bool
    hil_action:             Optional[str] # "approved" | "edited" | "unanswerable"

    # ── Summarizer Output ────────────────────────────────
    final_response:         str
    export_requested:       bool

    # ── Control ──────────────────────────────────────────
    error_message:          Optional[str]
    pipeline_stage:         str           # current node name, for debugging
```

---

## 12. Prompt Engineering Specifications

### 12.1 Reasoning Agent Prompt Design Principles

- **Be explicit about JSON output format** — include exact schema with types
- **Include routing constraints** — LLM must only choose from allowed_tables
- **Set confidence threshold** — tell the model what < 0.75 means
- **Keep it focused** — routing is a classification task, not a reasoning essay

### 12.2 SQL Generator Prompt Design Principles

- **Schema first, question last** — LLM performs better when context precedes instruction
- **Include 2-3 few-shot examples** — dramatically improves SQL correctness on domain-specific patterns
- **Explicit business rules** — "always filter is_new_user = FALSE" must be stated, not implied
- **Forbidden columns listed explicitly** — never rely on the model to infer PII restrictions
- **Output constraint** — "Generate ONLY a valid PostgreSQL SELECT query. No explanation. No markdown."

### 12.3 Summarizer Prompt Design Principles

- **Persona-aware tone** — executive = brief/KPI-focused, marketing = persona/action-focused
- **Source constraint** — only reference numbers that appear in the SQL result
- **Unit conversion** — always convert seconds to minutes/hours for readability
- **Incompleteness caveat** — flag if querying current incomplete period
- **One actionable insight** — every response ends with what the team should *do* with this data

---

## 13. Error Handling & Edge Cases

### 13.1 Error Scenarios and Responses

| Scenario | Detection Point | System Action | User Message |
|----------|----------------|---------------|-------------|
| Unauthorized user | `rbac_check` | Log + reject | "You don't have access to the analytics system yet." |
| Ambiguous query | `reasoning_agent` (confidence < 0.75) | Ask clarification | "Did you mean [X] or [Y]?" |
| SQL syntax error | `sql_executor` | HIL trigger | "Flagged for review — team will follow up" |
| Empty result | `sql_executor` | HIL trigger | "No data found — flagged for review" |
| Out-of-range values | `hil_validator` | HIL trigger | "Result flagged — human reviewing" |
| LLM API timeout | Any LLM node | Retry x2, then fail | "System temporarily unavailable — try again in a moment" |
| Wrong persona (user feedback) | `slack_responder` (❌) | Re-route | "Which context did you mean — Executive, Commerce, or Marketing?" |

### 13.2 The Correction Loop (Misrouting)

If a user clicks ❌ Wrong context:
1. Bot asks: "Which context did you mean?"
2. User replies: "Marketing"
3. System re-runs from `schema_injector` with `routed_persona = "marketing"` override
4. Misroute logged: `{query, wrong_persona, correct_persona}` → future few-shot training signal

---

## 14. Environment & Infrastructure

### 14.1 Development Environment

- **Platform:** Sandbox (VS Code)
- **Database:** PostgreSQL (sandbox instance)
- **Data:** Synthetic only — compliance requirement
- **Claude Access:** Via Anthropic API key configured in VS Code settings

### 14.2 Project Directory Structure

```
nypost-chatbot/
├── main.py                    # FastAPI app + Slack webhook receiver
├── graph.py                   # LangGraph graph definition
├── nodes/
│   ├── slack_ingestion.py
│   ├── rbac_check.py
│   ├── reasoning_agent.py
│   ├── persona_router.py
│   ├── schema_injector.py
│   ├── sql_generator.py
│   ├── sql_executor.py
│   ├── hil_validator.py
│   ├── summarizer.py
│   ├── export_engine.py
│   └── slack_responder.py
├── knowledge_layer/
│   ├── tables/                # YAML table descriptions
│   ├── kpi_definitions/       # YAML KPI definitions
│   ├── persona_profiles/      # YAML persona profiles
│   ├── business_rules/        # YAML business rules
│   └── few_shot_examples/     # YAML question→SQL examples
├── state.py                   # PipelineState TypedDict
├── database/
│   ├── connection.py          # SQLAlchemy engine setup
│   ├── schema.sql             # Table DDL for sandbox
│   └── synthetic_data/        # Synthetic data load scripts
├── config/
│   ├── rbac_config.yaml       # User → role → table mappings
│   └── settings.py            # API keys, DB URL, thresholds
├── tests/
│   ├── test_nodes.py
│   └── test_pipeline.py
└── requirements.txt
```

### 14.3 Environment Variables Required

```bash
ANTHROPIC_API_KEY=          # Claude API key
SLACK_BOT_TOKEN=            # Slack bot OAuth token
SLACK_SIGNING_SECRET=       # Slack webhook verification
DATABASE_URL=               # PostgreSQL connection string
ROUTING_CONFIDENCE_THRESHOLD=0.75
SQL_EXECUTION_TIMEOUT=30
HIL_NOTIFICATION_EMAIL=     # Where to send HIL alerts
```

---

## 15. Development Phases

### Phase 1: Foundation (Week 1)
- [ ] Set up project structure and environment
- [ ] Configure Slack webhook receiver (FastAPI)
- [ ] Build `rbac_check` node with dummy access control table
- [ ] Define `PipelineState` TypedDict
- [ ] Build LangGraph skeleton (all nodes stubbed, graph wired)
- [ ] Set up PostgreSQL connection with synthetic data
- **Blocker:** Need table schemas from Dashboard team + Ad-hoc Analytics team

### Phase 2: Core Pipeline (Week 1–2)
- [ ] Build `reasoning_agent` node with routing prompt
- [ ] Build `persona_router` conditional edges
- [ ] Build `schema_injector` with YAML knowledge layer
- [ ] Build `sql_generator` with validation
- [ ] Build `sql_executor` with safety guards
- [ ] End-to-end test: Slack message → SQL result

### Phase 3: Safety & Quality (Week 2)
- [ ] Build `hil_validator` with LangGraph interrupt
- [ ] Build `summarizer` node (Haiku)
- [ ] Add feedback buttons to `slack_responder`
- [ ] Implement correction/re-route loop
- [ ] Add source attribution to all responses

### Phase 4: Demo Preparation
- [ ] Load synthetic data for all confirmed tables
- [ ] Build 5–10 demo queries per persona
- [ ] Test all error scenarios
- [ ] Performance testing (response time target: < 10 seconds)
- [ ] Demo script preparation

---

## 16. Open Questions & Blockers

### Critical Blockers (Nothing moves without these)

| Blocker | Owner | Status |
|---------|-------|--------|
| Table schemas from Dashboard Team | Dashboard Team | **PENDING** |
| Table schemas from Ad-hoc Analytics Team | Ad-hoc Analytics Team | **PENDING** |
| RBAC source — do we have a user→role→tables mapping? | Subhatosh | **PENDING** |
| Confirm LLM provider: Anthropic or OpenAI? | Subhatosh | Leaning Claude (shown in diagram) |
| Mechanism to move schema/descriptions into sandbox | Savitha/Shrey | Collaborator folder tentatively |

### Design Questions Still Open

| Question | Options | Recommendation |
|----------|---------|----------------|
| Persona routing: based on user role OR query content? | Role-only vs content-based | Content-based (reasoning agent) — handles multi-role users |
| HIL notification channel | Email vs Slack DM | Slack DM to reviewer (faster) |
| Feedback button persistence | Ephemeral vs permanent | Ephemeral (disappears after 1 use) |
| Re-route on ❌: auto re-run or ask user first? | Auto vs ask | Ask — avoids wrong second attempt |

---

## 17. Decisions Log

| Date | Decision | Rationale | Decided By |
|------|----------|-----------|-----------|
| June 2026 | LangGraph over LangChain | Stateful branching graph, native HIL support, conditional edges | Team |
| June 2026 | RBAC pre-query (not post) | Cheaper, safer, prevents model reasoning about forbidden data | Team |
| June 2026 | Schema-injection over RAG for V1 | Timeline, only 2-3 tables initially | Subhatosh |
| June 2026 | Claude Sonnet 4.6 for reasoning | Quality of SQL generation and intent understanding | Subhatosh (diagram) |
| June 2026 | Cheaper model for summarization | Formatting only — no reasoning needed, cost saving | Architecture decision |
| June 2026 | Synthetic data only | Compliance — real client data cannot enter sandbox | Compliance/Subhatosh |
| June 2026 | Slack as sole UI | Integration already done, primary team tool | Subhatosh |
| June 2026 | Reasoning agent IS required | Multi-role users need content-based routing, not just identity-based | Shrey (validated) |

---

*This document is the single source of truth for the NYPost Conversational AI Chatbot project. Update it after every architectural decision or team call. Share with Claude Code in terminal for implementation guidance.*
