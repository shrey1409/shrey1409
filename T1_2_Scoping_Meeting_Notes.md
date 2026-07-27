# T1-2 Experience Agent — Scoping Meeting Notes

> **For:** Claude Code project spec (append to existing spec doc)
> **Source:** pre-project scoping meeting (Hinglish/English transcript, imperfect ASR) + 7 presentation slides
> **Captured:** 2026-07-27
> **Confidence key:** ✅ stated clearly · 🟡 inferred / ASR-ambiguous · ❓ open question
>
> **Terminology fix applied throughout:** the ASR wrote "Genie/GB/GBx/GB rooms/deemed rooms/gene/génie" → all mean **Databricks Genie rooms (spaces)**. It wrote "green/clean/Glenn/giant/DWG-as-front-end" → all mean **Glean** (the agent) or **Glean agents**. "DWG / double white loading / WhiteHat" → **DWG team** (see glossary). "ID / IT / ITTT" → **GM IT**. "folder / cold layer / loan layer / bold" → **gold layer**. "CIBIL / server / silver" → **silver layer**.

---

## 1. TL;DR (read this first)

- **Product:** an **agent** for GM leadership + the **DWG team** to monitor how the **new T1-2 truck launch** is going, by asking natural-language questions instead of reading dashboards.
- **The truck:** T1-2 = a **new truck, 2027 model year, releasing December 2027**. Leadership wants early-warning visibility on customer pain points at launch. ✅
- **The route is now explicit and non-negotiable:**
  `Gold tables → Genie rooms (built/tested in TEST on silver+gold) → promoted to PRODUCTION on GOLD → Glean agent integration → AI governance assessment`. ✅
- **Glean is GM's mandated enterprise front-end.** Not Slack, not Teams, not the Genie UI. Executives may mandate Glean top-down. ✅
- **The two big blockers, named in the meeting:** (1) getting silver→gold promoted to production **with GM IT** (~4 weeks for 3-4 tables historically), (2) the **Glean integration + AI governance assessment** (~2-3 weeks). ✅
- **Data readiness right now: only ~50-60% of the 6 data sources are in gold.** The rest are blocked on **access + masking issues** with the GM data-science/IT team that have been outstanding ~1 month. ✅
- **Genie rooms only answer questions about Databricks tables.** For documents/SharePoint/web, that's a *separate sub-agent* under the Glean agent. ✅
- **Timeline pressure:** MVP wanted around **September** (also heard "August", "late Jan/early Feb", "March" — dates are contradictory in the ASR; treat as ❓ but September is most repeated).
- **Proposed team:** **4-5 members for ~1 month burst**, then **2 people** for enhancements. One person per table. ✅

---

## 2. What the product is (from slides + transcript)

### 2.1 Business context
- GM is launching a **new T1-2 truck** (2027 MY, **Dec 2027** release). ✅
- Leadership wants to **"be on top of things so the release goes smoothly"** — early detection of customer pain points at launch. ✅
- There is an existing team, **DWG**, whose job is exactly this: watch new releases, spot where customers face issues, and track pain points regularly. ✅
- DWG **already has a dashboard** (shown in slides — see §3). The problem: **people doing secondary workflows don't want to open dashboards**; they want to **ask an agent** and get natural-language insights. ✅

### 2.2 What the agent must do (four capability areas — matches the proposal §3.x)
1. **Guided insight configuration** — surface which customers are moving through which **journey stages**, e.g. how many customers fall **back into the onboarding stage**. ✅
2. **Insight → intervention → measurement loop** — derive insights from base data, let the team take **interventions / action items**, then **measure the impact** of those changes (is a key metric going down? is a specific customer-highlighted issue trending?). ✅ (This is the pre/post measurement capability.)
3. **Pre-built prompt / report configurations** — user selects a configured prompt → agent generates a standard report. ✅
4. **Free-form natural-language Q&A** against the data. ✅

### 2.3 The critical architecture facts stated in the meeting

> These are the load-bearing facts. Get them into the spec verbatim.

- **F1 — Genie rooms are data-only.** "If you are using a Genie room, it'll only answer queries related to data — only Databricks/database tables." Documents are out of scope for Genie itself. ✅
- **F2 — Glean is the front-end, and it's mandated.** The team explicitly does NOT want the front-end to be Slack, Teams, or the Genie UI. "Glean has to do that." GM is standardising on Glean; executives may push it top-down. ✅
- **F3 — Multi-source answering happens via sub-agents under Glean.** One Glean agent can route to: a sub-agent that hits **Genie rooms** (data questions), another that hits **SharePoint** (proprietary docs), another that hits the **web** (generic questions). A single agent, multiple question types. ✅ *(For THIS project scope: "internally on data only. There's no SharePoint" — confirm, see ❓Q7.)*
- **F4 — Genie production requires gold.** You can build/test a Genie room in a **test environment using silver tables**, but **Glean integration requires the Genie room to be in PRODUCTION**, and production Genie must run on **gold tables**. ✅
- **F5 — Promotion path.** Gold tables → create Genie room → engineer/train it → promote to production (**GM IT involved here**) → then Glean integration → then **AI governance assessment** (GM IT-supported; guardrails for AI usage of Genie rooms + external-agent integration). ✅
- **F6 — Why Glean specifically (the real reason):** access-tiered users. Not everyone is comfortable reading raw data outputs; Glean gives an **authenticated, permission-aware UI** where any user can run a query, pull a report, or ask NL questions at their access level. ✅

---

## 3. The DWG dashboard slides (the data the agent sits on top of)

The presented deck is a **DWG launch-monitoring report**. This is the analogue the agent must reproduce conversationally. Contents observed across the 7 slides:

### 3.1 Title / framing slide
- "T1-2 Launch" monitoring theme; DWG-style pain-point tracking for a new vehicle release.

### 3.2 Get Help — Top 3 Case Types (the KPI dashboard) 🟡 high-value
Same structure as the proposal's §4.1. Three case-type columns, **June 2026 performance with 6-month trend (Jan→Jun 2026)**:

| Metric | WiFi | OnBoarding | Infotainment |
|---|---|---|---|
| Case Volume | 23,043 ▲ | 31,123 ▲ | 12,757 ▼ |
| % Closed in 24 hrs | 95.4% ▲ | 94.8% ▲ | 92.9% ▲ |
| First Contact Resolution | 77.6% ▼ | 77.6% ▲ | 77.0% ▲ |
| CSAT | 82.6% ▲ | N/A | 81.9% ▲ |
| Expert Support Avg Days to Close | 0.66 ▼ | 1.26 ▼ | 1.7 ▼ |
| Open Defects / Features | In Progress | 8 open | In Progress |

**Top 3 call drivers (June 2026):**
- **WiFi:** No/Slow Internet (9,372), Hotspot: SSID & Password (1,224), Hotspot: Data Not Shared/Disabled (950)
- **OnBoarding:** Hardware Replacement (11,998, **+397% vs Jan** — 2,413→11,998), Enroll Vehicle (3,218), BBWC (1,134)
- **Infotainment:** App Not Working (3,426), On Screen Messages (1,293), DIC – Driver Information Center (674)

> These three case types — **WiFi, OnBoarding, Infotainment** — plus SIM/case-holding/network issues mentioned verbally, are the pain-point taxonomy the agent must answer on. The transcript's "Internet, hotspot, password… onboarding issues… infotainment/network… case holding… SIM set" all map to this dashboard.

### 3.3 Journey-stage / other slides
- One slide shows **customer journey stages** with movement between them (the "customers falling back into onboarding" capability lives here). 🟡
- Other slides reiterate scope/capabilities and the pre/post measurement idea. 🟡

> ⚠️ Photo legibility on the non-KPI slides is medium. Numbers in §3.2 are high-confidence; journey-stage specifics are 🟡. **Re-shoot or get the .pptx** to confirm the journey-stage diagram.

---

## 4. THE WORKFLOW (this is what to encode in the spec)

```
STEP 0  Data sources (6 total)
        └─ Team consumes 4-5 SILVER sources, builds OWN gold-standard tables.
           ~50-60% currently in gold. Rest blocked on access + masking.

STEP 1  GOLD LAYER READY
        └─ All tables the agent needs must be in the gold layer.
           Gold is the source of truth ("source gold") — other GM projects use it,
           so it cannot be modified. Team FETCHES gold + JOINS into its own tables.
           If a table is already in gold → IT has already vetted it → big win,
           the integration script is pre-vetted.

STEP 2  GENIE ROOM(S) — build & train  (TEST env, can use silver)
        ├─ 2a. Create Genie room, reference ALL required tables in ONE room
        │      (fewer rooms is better; combination questions span tables).
        │      Also DEFINE THE DATA MODEL: how tables interact/join.
        ├─ 2b. Metadata creation: column definitions, what each column means,
        │      when to use which column (this is the core "training" effort).
        ├─ 2c. Baseline fundamental questions it must answer accurately.
        ├─ 2d. Validate answers against a Power BI dashboard / known numbers.
        └─ 2e. Once baseline passes → test complex questions → mark ready.
           Effort: ~2 weeks per Genie room to fully train + be 100% sure.

STEP 3  PROMOTE GENIE ROOM → PRODUCTION  (GM IT involved)
        └─ Production Genie MUST run on GOLD tables.
           Historically ~3 weeks (2-3 weeks with strong push) for promotion.
           Bottleneck is GM IT, not the team.

STEP 4  GLEAN AGENT INTEGRATION
        ├─ Build the Glean agent; configure which question types it handles.
        ├─ Glean agent connects to the PRODUCTION Genie room.
        ├─ (Optionally) add sub-agents: SharePoint docs, web — but THIS scope
        │   is "internally on data only" per transcript (confirm Q7).
        └─ Effort: ~2-3 weeks anticipated once Genie is in production.

STEP 5  AI GOVERNANCE ASSESSMENT  (GM IT-supported)
        └─ GM AI-governance guardrails for: AI usage of Genie rooms +
           integration with Glean / any external agent. Required before go-live.
```

**Total critical path (per the meeting's own estimates):**
gold promotion (~3-4 wks, IT) + Genie training (~2 wks/room) + Glean integration (~2-3 wks) + governance assessment (parallel-ish). The team compresses this with a **4-5 person / 1-month burst**, one person per table.

---

## 5. Data readiness — the real blocker

### 5.1 Current state (stated in meeting)
- **6 data sources** total for this app. ✅
- Team utilises **4-5 SILVER sources** and creates its **own gold-standard tables** on top. ✅
- **~50-60% in gold now.** Remaining ~40-50% blocked. ✅
- Blocker specifics: **no read access to silver + masking on vehicle IDs and other columns**, so **joins return nothing**. Requests to the GM data team raised 2-3 times over **~1 month**, repeatedly **denied/parked**. ✅
- Ankit's estimate: **1-2 weeks to finish gold once access is unblocked** — but that's the standing estimate and has already slipped ("this is already being one week"). 🟡
- Gold-vs-silver nuance: the *underlying customer data exists in gold* (source gold, used by many projects, immutable). The team reads silver and **builds its own joined tables** for this app because it can't modify source gold. ✅

### 5.2 Per-category status (from the "yellow/green" walk-through)
> The team colour-codes the workbook: **green/yellow = actively working / will be gold soon**; **highlighted = not being touched, needs checking with Adam.**

| Category | In gold? | Notes |
|---|---|---|
| Behavioral data | 🟡 ~50% | GM team sourcing the other 50%; some column names not yet known |
| Customer comments | ❌ | NOT being moved to gold currently |
| Demand space data | 🟡 | "~1 week" to gold (has been ~1 week for a while) |
| Demographic data | ❓ | Unsure where it exists; not confirmed |
| Internet data | ❓ | "We don't have internet data" — check with Adam |
| Training / content data | ❓ | Nobody on team knows what this is or has seen a table; **Adam's team owns it**; may be documents not tables |

### 5.3 The 50% with no column names
- For ~half of some sources, **even column names are not yet available** — GM is still identifying the source. 🟡 This is upstream of everything.

---

## 6. Key open questions to resolve WITH GM (carry into the spec as blockers)

| # | Question | Owner | Why it matters |
|---|---|---|---|
| Q1 | **When will the remaining ~50% of tables land in gold?** | GM data/IT team | Gates STEP 1 → everything |
| Q2 | Will the access + masking issue on silver be resolved, and when? | GM data-science/IT | Joins currently return nothing |
| Q3 | Do training/content/internet data exist as **tables or documents**? | Adam & team | Determines Genie (data) vs SharePoint sub-agent (docs) |
| Q4 | Which is the exact MVP date — Sept? Aug? Feb? | Leadership | ASR gives conflicting dates; September most repeated |
| Q5 | Is the DWG gold-source BI (Ankit/James) the same source, or separate? | Adam / BI team | Avoid data redundancy; it's an extension of Experience Hub |
| Q6 | Does the GM data-science team approve gold tables based on their own logic? | Ankit → GM | Affects whether team can self-serve gold |
| Q7 | For THIS scope: data-only, or also SharePoint/web sub-agents? | Leadership | Transcript says "internally on data only" but also "documents might come into picture" |
| Q8 | One Genie room or several? | Team (leaning ONE) | ✅ Decision: ONE room, all tables referenced, model defined — see §7 |

---

## 7. Decisions already made in the meeting

| ID | Decision | Rationale |
|---|---|---|
| D1 | **ONE Genie room**, referencing all required tables, with the inter-table data model defined | Combination questions intersect multiple tables; "fewer is better in unchartered territory" |
| D2 | **Glean is the front-end.** Not Slack/Teams/Genie-UI | GM enterprise standard; possible exec mandate |
| D3 | Production Genie on **gold**; test/training can use **silver** | F4 — Glean integration needs production Genie |
| D4 | **4-5 person team, ~1 month burst; then 2 people for enhancements** | One person per table; trim toward the end |
| D5 | **Parallelise now:** build tiny Genie rooms on available data to test the flow before full access lands | "In the meantime you can test and fix bugs" — matches the synthetic-data POC already in progress |
| D6 | Team owns metadata definitions / column semantics for the Genie room | GM won't provide these |

---

## 8. Effort & team (as proposed in the meeting)

- **Team size:** 4-5 members for the MVP month. Then 2 for enhancements. ✅
- **Allocation:** ~one person per gold table (assume ~6 tables). ✅
- **Duration:** ~1 month burst for MVP, enhancements through remainder of the year. ✅
- **Historical benchmarks cited:**
  - Gold promotion to production: **~4 weeks for 3-4 tables** (GM IT bottleneck).
  - Genie room full training: **~2 weeks per room**.
  - Glean integration: **~2-3 weeks** after Genie is in production.
- **Biggest schedule risk (stated repeatedly):** **delays from GM's side in providing data / access.** Not the build itself.

---

## 9. Glossary / disambiguation (ASR → real term)

| ASR wrote | Means |
|---|---|
| Genie / GB / GBx / GB rooms / gene / génie / deemed rooms / teenager | **Databricks Genie room (space)** |
| green / clean / Glenn / giant / DWG-as-frontend | **Glean** (agent / enterprise UI) |
| DWG / double white loading / WhiteHat / white-hat | **DWG team** — GM launch-monitoring / pain-point team (likely "Dealer/Digital Workflow Group" or similar; **confirm expansion**) |
| ID / IT / ITTT / GMT | **GM IT** |
| folder / cold layer / loan layer / bold / gold there | **gold layer** |
| CIBIL / server layer | **silver layer** |
| source gold | immutable shared gold used across GM projects |
| T1-2 | the new truck program, 2027 MY, Dec 2027 release |
| MVP / NVP / MRI | **MVP** |
| AI governance assessment | GM IT AI guardrail review before external-agent go-live |

---

## 10. How this maps to work already done

- The **synthetic-data POC** (12 tables, Genie-ready, in `synthetic/`) is exactly D5 — build tiny Genie rooms on stand-in data to test the flow before access lands. It stays valid; just point the Genie room at it in TEST.
- The earlier **Genie→Glean workflow doc** aligns with §4 here, with two corrections now confirmed by this meeting:
  1. **Glean-as-mandated-frontend is certain** (was 🟡 "D-01 unconfirmed"; now ✅).
  2. **Genie must be promoted to PRODUCTION on GOLD before Glean can integrate** — this is a hard sequencing constraint that wasn't explicit before. The Custom-Action-vs-MCP question still stands, but it happens at STEP 4, after production promotion.
- The **`action_log` / `get_help_case` gap tables** we invented are validated: the DWG dashboard IS the case/metrics data, and it has no confirmed gold source yet (Q3/§5.2).

---

## 11. Immediate next actions (for the spec / for the team)

1. **Confirm the gold-table inventory:** exactly which of the 6 sources are in gold today, with column names. (Ankit to comment on the workbook.)
2. **Get a firm data-delivery date from GM** for the remaining ~50%. This is the top schedule risk.
3. **Confirm data-only vs docs** (Q7) — decides whether a SharePoint sub-agent is in MVP scope.
4. **Nail the MVP date** (Q4).
5. **Start the Genie room in TEST now** on synthetic/silver data (D5) — metadata, data model, baseline questions — so training time isn't lost waiting on access.
6. **Get Neeti's flow doc** — she has a process/activities flow that should be merged into the spec.
7. **Confirm DWG expansion** and whether the DWG gold-source BI (Ankit/James) is the same or separate source (Q5, avoid redundancy).
