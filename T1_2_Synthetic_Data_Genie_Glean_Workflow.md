# Synthetic Data → Databricks Genie → Glean Agents
## T1-2 Experience Agent · Pre-Access POC Workflow

> **Status:** working plan, written without Databricks access.
> **Owner:** Shrey · **Date:** 23 July 2026 · **Trigger:** manager call (Hinglish transcript)

---

# Part 1 — What the manager actually asked for

## 1.1 Decode of the call

| What was said | What it means |
|---|---|
| *"Google कहीं से भी सब कुछ scrape करके data लेकर आता है. Glean is kind of that application."* | Someone was explaining Glean to the room. **Glean = Google for the enterprise** — it indexes across all internal systems and answers questions. This is the mental model the team is working from |
| *"nobody has seen it, right? All of us… ऐसा ना हो कि हम black हो जाएं"* | **Nobody on the team has hands-on Glean experience.** Explicit fear of being blindsided/blocked on the integration. This is the real anxiety driving the whole request |
| *"It's gonna be super speedy project"* | Compressed timeline is acknowledged |
| *"first August मतलब वह तो onboarding वाला… हमने तो accesses next week से मिलना चालू"* | **1 Aug is NOT the project start** — that's onboarding/billing/account linking, handled separately. **Databricks accesses start arriving next week** (w/c ~27 July) |
| *"since I don't have the access for Databricks, अभी मैं बस check कर लेता हूं कि what is the flow और कैसे हम Genie में implement कर सकते हैं data को and उसको कैसे Glean API / Glean agents से connect कर सकते हैं"* | **Shrey's own commitment.** Produce the end-to-end flow on paper while access is pending |
| *"मैं इसका एक पूरा workflow बनाकर रखता हूं कि क्या क्या किया जा सकता है"* | Deliverable = **a complete workflow document**. This file |
| *"Synthetic data बनाया था… POC type… बहुत major नहीं चाहिए मुझे. Hundred, two hundred rows"* | **100–200 rows. Explicitly small.** Do not over-engineer |
| *"हमारे लिए वह quick refresher भी हो जाएगा और हम जब system में घुसेंगे तो speedy काम भी हो जाएगा"* | Two purposes: **(a) team learns the stack now, (b) when real access lands they move fast** because everything is already built and only the source swaps |
| *"जो tables group में share किया है, वही सारे tables हैं?" — "वही सारे tables हैं"* | **Use the tables from the Experience Hub Agentic workbook.** No new list coming |
| *"gold tables के through ही हमें productionize कर पाएं… but हमारे पास सारे gold tables हैं नहीं"* | **Two caveats, stated explicitly.** (1) Production must run on Gold. (2) We don't have all the Gold tables. So: **model the Gold tables preferentially**, fall back to Silver only where no Gold exists |
| *"उसमें silver और gold दोनों का है. तो gold वाले कर लेते हैं… सारे नहीं. हम देख लेते हैं generally"* | Prioritise Gold, don't attempt all of them, keep it general |
| *"most contribution will be a total duplication… वह तो later on challenge. एक बार MVP बना, देखा इन्होंने तो फिर ठीक है"* | Anticipated data problem is **duplication / entity resolution**. Deliberately deferred — build MVP first *(low transcription confidence on this line; worth re-confirming)* |
| *"आप मैं वह evening में connect कर?… तो भी बताना ना क्या progress है"* | **Progress check-in this evening.** Even partial progress counts |

## 1.2 The ask, in one sentence

> Build a tiny synthetic replica of the Gold tables, stand up the whole
> Genie → Glean chain against it, and prove the flow works — so that when
> Databricks access arrives next week the team is swapping a data source,
> not starting an integration.

## 1.3 What "done" looks like for the evening call

1. This workflow document
2. A generated 100–200 row dataset with the real table names *(done — see Part 4)*
3. A clear answer on **how Genie connects to Glean**, with the two viable paths and a recommendation
4. A named list of what is blocked on access vs what isn't

---

# Part 2 — Architecture: where Genie and Glean each sit

## 2.1 The core insight

**Glean and Databricks are good at different halves of the problem. Don't build either half twice.**

| Problem | Best tool | Why |
|---|---|---|
| "What does our research say about T1-2 onboarding friction?" — documents, research, playbooks, Moments that Matter | **Glean** | Document RAG, permission-aware retrieval and citation is Glean's core product. It already indexes SharePoint/Drive/Confluence-type sources |
| "What was WiFi FCR in June vs January by region?" — governed numbers over the lakehouse | **Databricks Genie** | Genie generates SQL against Unity Catalog tables with UC permissions and lineage intact. Glean cannot query the lakehouse |

**So: Glean is the orchestration + UI + document layer. Genie is the structured-data tool the Glean agent calls.**

This directly serves proposal §3.3.5 ("derive answers from the Experience Hub knowledge base") *and* §3.2/§4 (numbers), which are two different retrieval paths — exactly the router argument from the NY Post chatbot.

## 2.2 Target flow

```
   User in Glean
        │  "Why did OnBoarding case volume jump since January?"
        ▼
┌───────────────────────────────────────────────┐
│  GLEAN AGENT  (built in Agent Builder)        │
│  ─ routing instructions decide the path       │
└───────┬───────────────────────────┬───────────┘
        │ documents / research      │ numbers / metrics
        ▼                           ▼
┌────────────────────┐   ┌──────────────────────────────┐
│ Glean native       │   │ CUSTOM ACTION                │
│ search + index     │   │ "Query CX Metrics"           │
│ (Experience Hub    │   │  POST /execute {question}    │
│  docs, research)   │   └──────────────┬───────────────┘
└────────────────────┘                  ▼
                            ┌──────────────────────────┐
                            │ THIN WRAPPER SERVICE     │
                            │ auth · async→sync · shape│
                            └──────────────┬───────────┘
                                           ▼
                            ┌──────────────────────────┐
                            │ DATABRICKS GENIE         │
                            │ /api/2.0/genie/spaces/   │
                            │   {space_id}/…           │
                            │  NL → SQL → rows         │
                            └──────────────┬───────────┘
                                           ▼
                            ┌──────────────────────────┐
                            │ UNITY CATALOG            │
                            │ Gold tables (synthetic   │
                            │ now, real later)         │
                            └──────────────────────────┘
```

## 2.3 What the docs confirm

**Databricks Genie**
- <cite index="4-1">The Genie Conversation APIs let users self-serve data insights in natural language from any surface — Databricks Apps, Slack, Teams, SharePoint, custom-built applications — and let you embed Genie in any AI agent, with or without Agent Framework</cite>. That last clause is the important one for us: **no Databricks Agent Framework required**, which matters because the delivery surface is Glean.
- Entry point is <cite index="4-1">`POST /api/2.0/genie/spaces/{space_id}/start-conversation`</cite>, with follow-up turns via `create_message` on the same conversation. <cite index="6-1">These are stateful conversations supporting follow-up questions</cite>.
- <cite index="5-1">The API is asynchronous because Genie takes time to analyse data and generate SQL — the flow always requires asking the question and then polling</cite>. **This is why a wrapper service is needed**; Glean actions want request/response.
- <cite index="5-1">For third-party tools the recommended auth is OAuth M2M via a service principal; a PAT is fine for quick local testing</cite>.
- Prerequisites: <cite index="8-1">Genie uses data registered to Unity Catalog and requires at least CAN USE permission on a Pro or Serverless SQL warehouse, and Databricks Assistant must be enabled</cite>.
- ⚠️ The docs are blunt about the failure mode: <cite index="9-1">if the agent is incomplete or untested, users might still receive incorrect results even with a correct API integration</cite>. **Genie quality is a curation problem, not an integration problem.** Budget accordingly.
- Naming note: Databricks docs now say **"Genie Agents"** where they used to say "Genie spaces". The endpoint still uses `spaces/{space_id}`. Say "Genie Agent" in front of the client.

**Glean**
- <cite index="12-1">Custom actions are defined in the Glean admin console with a display name, description, unique identifier and type; triggers with example queries so Glean knows when to call the action; an uploaded YAML or JSON API spec with a single endpoint such as `/execute` with request parameters; authentication config; and built-in testing tools</cite>.
- <cite index="12-1">The custom action is then added as a step in Agent Builder, with parameters set as fixed values, user inputs, or AI-predicted values, and can be combined with native actions in the same workflow</cite>.
- <cite index="13-1">Agents can be built no-code in Agent Builder, or via REST APIs; agent execution requires the `agents` and `chat` scopes</cite>.
- <cite index="14-1">Glean also supports bringing custom permission-aware data in alongside its out-of-the-box connectors, and creating actions using MCP and the OpenAPI spec</cite>.

**The MCP shortcut:** Glean supports MCP, and Databricks ships a managed MCP server that exposes Genie. <cite index="5-1">The Databricks Managed MCP Server is suited to third-party tools that are AI agent frameworks</cite>. If GM's Glean tenant permits registering an external MCP server and the network path exists, this replaces the wrapper service entirely. **Check this first — it could remove a whole component.**

## 2.4 Two integration paths — recommendation

| | **Path A — Custom Action + wrapper** | **Path B — MCP** |
|---|---|---|
| Components | Glean action → your service → Genie API | Glean → Databricks managed MCP → Genie |
| Code | ~150 lines + hosting | Near zero |
| Control over auth/identity | Full | Limited to what the connector exposes |
| Response shaping | Full | Limited |
| Depends on | Nothing exotic | GM Glean tenant allowing external MCP; network path to workspace |
| Risk | Higher effort, lower unknowns | Lower effort, higher unknowns |

**Recommendation: pursue B as a spike, build A as the plan.** Path A is the one you can commit to a date on. Spend one hour checking whether B is available before writing the wrapper — if it is, you've saved a week.

---

# Part 3 — Phased workflow

## Phase 0 — Unblocked today (no access needed)

| # | Task | Output |
|---|------|--------|
| 0.1 | Decode transcript, confirm scope | Part 1 of this doc |
| 0.2 | Design the synthetic schema from the workbook categories | `generate_synthetic_data.py` |
| 0.3 | Generate 100–200 row dataset | `./synthetic/*.csv` + `create_tables.sql` |
| 0.4 | Write the Genie instruction pack + example SQL | Part 5 |
| 0.5 | Write the question bank for evaluation | Part 7 |
| 0.6 | Draft the OpenAPI spec for the Glean custom action | Part 6.2 |
| 0.7 | Ask the access + architecture questions | Part 8 |

## Phase 1 — Land the data (day 1 of access)

| # | Task | Note |
|---|------|------|
| 1.1 | `DESCRIBE TABLE` every real table in the workbook | **Highest-value first action.** 15 minutes of work that corrects every schema guess |
| 1.2 | Update the `TABLES` registry + column names in the generator | Single file to edit by design |
| 1.3 | Create a dev catalog e.g. `t1_2_dev` with `raw`/`gold_cx` schemas | Never write synthetic data into a prod catalog |
| 1.4 | Load the CSVs as Delta tables | `create_tables.sql` is pre-generated |
| 1.5 | Confirm SQL warehouse (Pro or Serverless) + Databricks Assistant enabled | Genie prerequisite |

## Phase 2 — Genie Agent (space) — days 1–3

| # | Task |
|---|------|
| 2.1 | Create the Genie Agent, add the 8–12 tables |
| 2.2 | Write table + column comments in UC (Genie reads these) |
| 2.3 | Write **General Instructions** (Part 5.1) |
| 2.4 | Add **certified example SQL** for the 8 canonical questions (Part 5.2) |
| 2.5 | Add join hints and metric definitions |
| 2.6 | Run the question bank, log accuracy, iterate instructions |
| 2.7 | Note the `space_id` from the URL |

## Phase 3 — API access to Genie — day 3

| # | Task |
|---|------|
| 3.1 | Create a service principal, grant it: CAN RUN on the Genie Agent, CAN USE on the SQL warehouse, SELECT on the tables |
| 3.2 | Configure OAuth M2M |
| 3.3 | Test `start-conversation` end-to-end from a notebook/curl |
| 3.4 | Measure latency (this drives whether Glean gets a sync or async pattern) |

## Phase 4 — Wrapper service — days 4–6

| # | Task |
|---|------|
| 4.1 | FastAPI service, single `POST /execute` endpoint |
| 4.2 | Async→sync: start conversation, poll to completion, timeout guard |
| 4.3 | Return `{answer_text, sql, row_count, rows[], genie_link}` |
| 4.4 | Guardrails: row cap, query timeout, allow-list of tables, reject PII columns |
| 4.5 | Log every question + generated SQL (this becomes the eval set and the audit trail) |
| 4.6 | Deploy — Databricks Apps is the path of least resistance; it's already inside the workspace network and auth boundary |

## Phase 5 — Glean side — days 6–9

| # | Task |
|---|------|
| 5.1 | **Spike Path B first:** can this Glean tenant register an external MCP server? |
| 5.2 | Register the custom action in the Glean admin console: name, description, unique ID, type |
| 5.3 | Define **triggers + example queries** so Glean knows when to fire it |
| 5.4 | Upload the OpenAPI spec |
| 5.5 | Configure auth from Glean → wrapper |
| 5.6 | Test in the console's built-in action tester |
| 5.7 | Build the agent in Agent Builder; add the action as a step |
| 5.8 | Write routing instructions: documents → native search, numbers → the action |
| 5.9 | Push Experience Hub docs into the Glean index (or confirm they're already indexed) |

## Phase 6 — Evaluate & demo — days 9–10

| # | Task |
|---|------|
| 6.1 | Run the full question bank through Glean end-to-end |
| 6.2 | Score: did it route correctly? was the SQL right? was the number right? |
| 6.3 | Build the §3.3.2 pre/post demo (Part 7.3) |
| 6.4 | Record a 5-minute walkthrough |

---

# Part 4 — The synthetic dataset

## 4.1 Design rules

1. **Schema-faithful, volume-tiny.** Real `catalog.schema.table` names. When access lands you change the source, not the pipeline.
2. **Referentially consistent.** `vin` and `individual_id` join across every table. Genie's value *is* joins — disconnected random tables prove nothing.
3. **Distributions match the June 2026 deck.** Case mix, FCR ~77%, CSAT ~82%, bimodal NPS, and the Hardware Replacement ramp. So a stakeholder can sanity-check a Genie answer against a number they already believe.
4. **Zero real PII.** Fully fabricated → demoable with no Glenda approval, no Acxiom licence question (R-03), no re-identification risk (R-04).
5. **One config block.** Column names are provisional guesses; `TABLES` + the builder functions are the only things to correct after `DESCRIBE TABLE`.

## 4.2 What was generated

**Gold — the productionisation target**

| Table | Rows | Grain |
|---|---|---|
| `aftersales_prod.gold_enterprise_experience_engine_e3_gmna.e3_vin_detail` | 180 | one row per VIN |
| `aftersales_prod.gold_enterprise_experience_engine_e3_gmna.e3_indiv_detail` | 150 | one row per individual |
| `marketing_prod.gold_customer_feature_store_gmna.vehicle_attributes` | 180 | one row per VIN |
| `sales_prod.gold_vehicle_ownership_gmna.vehicle_ownership` | 180 | one row per ownership record |

**Silver — included only where no Gold exists** *(the agent is useless without verbatims)*

| Table | Rows |
|---|---|
| `…silver_enterprise_experience_engine_e3_gmna.survey_hub_inmoment_us_vw` | 195 |
| `…silver_enterprise_experience_engine_e3_gmna.survey_hub_inmoment_global_vw` | 60 |
| `customer_prod.silver_individual_gmna.acxiom_survived_individual_demographic` | 150 |
| `customer_prod.silver_individual_gmna.consolidated_customer` | 150 |

**Proposed gap tables — no source identified anywhere in the workbook**

| Table | Rows | Why it exists |
|---|---|---|
| `t1_2_dev.gold_cx.get_help_case` | 990 | **Every §4 primary metric lives here** and nothing in the workbook supplies it. Six months × 3 case types needs volume to show a trend |
| `t1_2_dev.gold_cx.content_engagement` | 300 | Metric 8 (Content Engagement) |
| `t1_2_dev.gold_cx.training_participation` | 75 | Metric 9 (Training Participation) |
| `t1_2_dev.gold_cx.action_log` | 11 | **The intervention register.** Seeded with the real Key Actions from the deck |

> `action_log` is the highest-leverage table here. The deck's "Key Actions" column is a list of interventions with dates — Telus order fixed 6/10, AT&T improvement complete, Google Assistant resolved June. Turning it into a joinable dimension is what makes §3.3.2 pre/post measurement computable at all. Nobody has asked for this table; propose it.

## 4.3 Verified properties

```
Hardware Replacement ramp   Jan 5 → Jun 30 cases   (mirrors 2,413 → 11,998)
June case mix               OnBoarding .44 / WiFi .41 / Infotainment .16
FCR                         ~0.72 baseline, lifts as interventions land
Join integrity              survey → vin      ✓
                            ownership → individual ✓
```

## 4.4 Honest caveats to state out loud

- **Column names are guesses.** Categories came from the workbook; the actual column names did not. Everything is structured so this costs 15 minutes to fix, but say so rather than let anyone assume otherwise.
- **`e3_vin_detail` vs `vehicle_attributes` overlap** on segment/body style/category. The workbook maps those categories to both. Real schemas will settle it.
- **The four gap tables are proposals, not discoveries.** They are shaped to make the metrics computable. Getting them corrected — or getting told where the real data is — is a *good* outcome of showing this.
- **`_global_vw` vs `_us_vw` relationship is unknown** (R-06). Generated as disjoint; if global actually contains US, every union in the Genie space is double-counting.

---

# Part 5 — Genie Agent configuration

> This is where the project succeeds or fails. The API integration is a day's work. Genie accuracy is weeks of curation. The Databricks docs say it plainly: <cite index="9-1">an incomplete or untested agent returns incorrect results even with a correct API integration</cite>.

## 5.1 General Instructions (draft — paste into the Genie Agent)

```
You answer questions about T1-2 truck customer experience for General Motors.

SCOPE
- T1-2 = full-size and mid-size pickup programs (Chevrolet Silverado/Colorado,
  GMC Sierra/Canyon). Always filter to t1_2_program_flag = 'Y' unless the user
  explicitly asks about other vehicles.
- Data covers January 2026 to June 2026. If asked about periods outside this,
  say so rather than returning an empty result.

METRIC DEFINITIONS (use these exactly; never invent a variant)
- Case Volume            = COUNT(case_id)
- Closed within 24 hours = AVG(CASE WHEN closed_within_24h='Y' THEN 1 ELSE 0 END)
- First Contact Resolution (FCR)
                         = AVG(CASE WHEN first_contact_resolution='Y' THEN 1 ELSE 0 END)
- Average Days to Close  = AVG(days_to_close)
- CSAT                   = AVG(csat_score) on a 1-5 scale; report as % of 5
- NPS                    = (%Promoters - %Detractors) * 100, where
                           Promoter = nps_score >= 9, Passive = 7-8, Detractor <= 6
- Top Drivers/Pain Points= COUNT(case_id) grouped by call_driver, descending

JOIN RULES
- get_help_case  → e3_vin_detail                on vin
- get_help_case  → consolidated_customer        on individual_id
- survey_hub_*   → e3_vin_detail                on vin
- vehicle_ownership → e3_vin_detail             on vin
- Never join survey_hub_inmoment_us_vw to survey_hub_inmoment_global_vw
  without an explicit instruction; the overlap between them is unconfirmed.

REPORTING RULES
- Default time grain is month. Default comparison is vs January 2026.
- Always state the row count and the date range covered.
- Percentages to one decimal. Counts with thousands separators.
- If a question needs a column that does not exist, say which column is missing.
  Do not substitute a similar one.
- Never return individual-level rows containing zip_code, gender_code, or
  num_children. Aggregate to region or above.
```

## 5.2 Certified example SQL to attach

Attach one worked query per canonical question. This is the single highest-return activity in the whole build.

1. Case volume by case type by month
2. FCR by case type, June vs January
3. Top 3 call drivers per case type for a given month
4. NPS by region, promoters/passives/detractors breakdown
5. Detractor verbatims for a given call driver
6. **Pre/post an intervention** — join `action_log` to `get_help_case` on `case_type`, split on `action_date`, compare FCR and volume either side
7. Content engagement → subsequent NPS (the §3.3.3 combination question)
8. Cases per 1,000 vehicles in operation by brand/model

## 5.3 UC comments

Genie reads table and column comments. Before curating instructions, run `COMMENT ON` for every table and every non-obvious column. Cheap, and it lifts accuracy noticeably.

---

# Part 6 — Glean integration detail

## 6.1 Wrapper service contract

```
POST /execute
Request : { "question": "string", "space_id": "optional override" }
Response: {
  "answer_text" : "OnBoarding case volume rose 34% from January to June...",
  "sql"         : "SELECT ...",
  "row_count"   : 6,
  "rows"        : [ {...}, ... ],      # capped
  "genie_link"  : "https://<workspace>/genie/rooms/<space_id>/...",
  "as_of"       : "2026-06-30"
}
```

Non-negotiables inside the wrapper:
- **Row cap** (e.g. 100) — Glean agents choke on large payloads
- **Timeout guard** — Genie is async; fail cleanly at ~45s rather than hanging the agent
- **Table allow-list** — reject any generated SQL touching tables outside the Genie space
- **PII column deny-list** — belt and braces on top of UC masks
- **Log every question + generated SQL** — this becomes both the eval set and the audit trail

## 6.2 Glean custom action definition

Per Glean's spec, you'll need:

| Field | Value |
|---|---|
| Display name | `Query T1-2 CX Metrics` |
| Description | "Answers quantitative questions about T1-2 customer experience: case volume, FCR, CSAT, NPS, call drivers, and pre/post intervention measurement. Use for any question involving a number, trend, count, or comparison over time." |
| Unique identifier | `t1_2_cx_metrics` |
| Type | **Retrieval** (it returns information; it doesn't mutate anything) |
| Triggers / example queries | "What was WiFi FCR in June?" · "How many OnBoarding cases last month?" · "Top call drivers for Infotainment" · "Did the Telus fix improve anything?" · "NPS by region" |
| API spec | OpenAPI YAML, single `/execute` endpoint, one required string param `question` |
| Authentication | Service token / OAuth per GM standard |

Then in Agent Builder: add the action as a step, set `question` as an **AI-predicted** parameter (the agent rewrites the user's phrasing into a clean analytical question).

## 6.3 Agent routing instructions

```
You are the T1-2 Experience Agent.

Start by asking the user for Brand, Vehicle and Trim if not already given.   [§3.1]

ROUTING
- Numbers, counts, trends, comparisons, metrics, "how many", "what was",
  "did X improve"  → call the Query T1-2 CX Metrics action.
- Research, findings, playbooks, "what do we know about", "why do customers",
  Moments that Matter, journey definitions → use Glean search over the
  Experience Hub knowledge base.
- Mixed questions → do both, lead with the number, support it with the research.

ALWAYS
- Cite the source: Genie link for numbers, document link for research.
- State the date range and row count behind any number.
- If the action fails or returns nothing, say so plainly. Never estimate a
  number yourself.
```

That last line matters. The failure mode that will kill trust fastest is the agent confabulating a case volume when the tool call fails.

## 6.4 Identity — the decision that needs making early

If the wrapper calls Genie with a **single service principal**, every Glean user sees identical data. That defeats Unity Catalog row filters and undoes the entire PII story (R-04).

| Option | Verdict |
|---|---|
| Single service principal, unrestricted tables | ❌ Unacceptable — bypasses UC |
| **Single service principal, Genie space restricted to non-PII aggregate Gold tables** | ✅ **Recommended for MVP.** Safe because there's nothing sensitive to leak |
| On-behalf-of token exchange (Glean user → Databricks identity) | ⏳ Correct long-term; needs SSO work, not a 6-week item |
| Pass user email, filter in the wrapper | ⚠️ Enforcement in application code, not the platform. Auditors dislike it |

**Take the middle row for MVP and write down that you did, plus why.** This is a decision the Databricks Architect should ratify — flag it rather than absorb it.

---

# Part 7 — Evaluation

## 7.1 Question bank

Build ~30 questions across four buckets, with a known-correct answer computed directly in SQL:

| Bucket | Example | Tests |
|---|---|---|
| Simple aggregate | "How many WiFi cases in June?" | Basic NL→SQL |
| Filtered + grouped | "FCR by region for OnBoarding in Q2" | Joins + filters |
| Comparative | "How did Infotainment volume change since January?" | Time comparison |
| Causal / pre-post | "Did the Telus fix improve WiFi resolution?" | §3.3.2, `action_log` join |
| Routing | "What does our research say about onboarding friction?" | Should go to Glean, **not** Genie |

## 7.2 Scoring

For every question record: **routed correctly?** · **SQL correct?** · **number correct?** · **latency**. Three separate failure modes with three different fixes — routing failures are agent instructions, SQL failures are Genie instructions, number failures are data.

## 7.3 The demo to build

**"Did the Telus order fix on 10 June actually work?"**

The agent should: recognise it as a pre/post question → call the action → Genie joins `action_log` to `get_help_case` → splits WiFi cases on 10 June → compares volume and FCR either side → returns a narrated answer with the SQL and a caveat that this is a before/after comparison, not a controlled causal estimate.

That single question demonstrates §3.1, §3.3.2, §3.3.4 and §3.3.5 at once, and it uses an intervention the stakeholders already recognise from their own deck.

> **Caveat to state in the demo:** a raw before/after comparison is not causal evidence. Seasonality, concurrent interventions and volume shifts all confound it. Proper §3.3.2 work needs difference-in-differences or a matched control group. Saying this early sets the right expectation for the efficacy models in §3.3.3 and keeps the team out of the trap of over-claiming from a bar chart.

---

# Part 8 — Questions to raise

## 8.1 On the evening call

1. **Path A or Path B?** Can GM's Glean tenant register an external MCP server, or do we build the custom action + wrapper? One hour of checking saves a week.
2. **Who owns the Glean side?** Custom actions are defined in the Glean **admin console** — that needs an admin. Does the team have one, or is it GM-side?
3. **Which Genie space, whose workspace?** Genie needs a Pro or Serverless SQL warehouse and Databricks Assistant enabled.
4. **Can we get a dev catalog** (`t1_2_dev`) for synthetic data? Never load fabricated rows into a prod catalog.
5. **`DESCRIBE TABLE` on day one** — can someone with access run it this week and send the output? It unblocks the schema correction before Shrey's own access lands.

## 8.2 Worth naming as findings

- **The §4 metrics have no source table.** Every primary metric — case volume, FCR, CSAT, days to close, call drivers — needs a Get Help / case-management source that isn't in the workbook. This is arguably a bigger blocker than the Gold layer.
- **`action_log` doesn't exist and needs to.** Without an intervention register, §3.3.2 is not computable at all.
- **Nobody has Glean experience** — the manager said so. Budget for that explicitly rather than discovering it in week three. The Path B spike is the cheapest way to reduce that unknown fast.

---

# Appendix — Files

| File | Purpose |
|---|---|
| `generate_synthetic_data.py` | The generator. Edit `TABLES` + column names after `DESCRIBE TABLE` |
| `synthetic/*.csv` | 12 tables, ~2,400 rows total |
| `synthetic/create_tables.sql` | Delta DDL with the real FQNs |
| `synthetic/manifest.json` | Row counts, columns, and a `schema_confirmed` flag per table |

Regenerate at any size:
```bash
python generate_synthetic_data.py --out ./synthetic --individuals 150
python generate_synthetic_data.py --out ./synthetic --individuals 500 --format parquet
```
