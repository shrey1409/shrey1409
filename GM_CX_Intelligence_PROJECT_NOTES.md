# GM Experience Hub / T1-2 Experience Agent — Project Notes

> **Living document.** Updated as Shrey shares documents, table names, and decisions.
> Last updated: 2026-07-23 · **Revision: 5**

---

## 0. Log of Updates

| Rev | Date | What was added | Source |
|-----|------|----------------|--------|
| 1 | 2026-07-23 | Seed file from scope-list decode | Scope message (OCR) |
| 2 | 2026-07-23 | Full table inventory from Experience Hub Agentic workbook (3 tabs), people map, access tracker, glossary, risk register | 6 photos, Neeti Asthana 12:06 AM |
| 3 | 2026-07-23 | **T1-2 Experience Agent Proposal in full** — exec summary, timeline, stakeholders, dependencies, objectives, capabilities 3.1–3.3.5, Section 4 primary metrics with June 2026 actuals. Name corrections. Major architecture + timeline findings | 9 photos, Neeti Asthana 12:20 AM + Abhiroop Sarkar 12:15 AM |
| 5 | 2026-07-23 | **Manager call decoded.** Databricks access lands next week (1 Aug is onboarding/billing, not project start). Task: synthetic data for the Gold tables (100–200 rows) → Genie → Glean agents. Team has **zero Glean experience**. Anticipated data issue = duplication, deferred past MVP. Full workflow + generator produced in a separate doc | Hinglish transcript, manager call |
| 4 | 2026-07-23 | **Team Responsibilities & Delivery Plan** — three workstreams incl. Power BI, full DE/DS/BI responsibility split, 11 primary metrics, 7 MVP deliverables, resource plan, 8–10 week estimate. **Timeline conflict identified.** Origin of the original scope list confirmed | 4 photos, `T1_2_Experie…oles_Plan (1)`, owner Neeti Asthana |

---

## 1. Project Identity

| Field | Value | Confidence |
|-------|-------|-----------|
| Client | GM (General Motors) | Confirmed |
| **Product name** | **T1-2 Experience Agent** | Confirmed |
| Parent system | **Experience Hub** knowledge base — the agent *extends* it | Confirmed |
| Teams channel | "Experience Hub Agentic" | Confirmed |
| **Delivery surface** | **Glean** (Glean APIs listed as a dependency; conceptual mock is a Glean-style agent card) | High — see D-01 |
| Data platform | Databricks / Unity Catalog | High |
| **BI layer** | **Power BI** — dedicated team, own workstream | Confirmed |
| Implementation stack (as stated) | **Databricks + GenAI + Power BI** | Confirmed |
| Segment | **T1-2 truck customers** — early stages of the journey | Confirmed |
| **MVP due** | **Conflicting:** Proposal says late Aug / early Sep; Delivery Plan says 8–10 weeks (≈ mid-Sep to early Oct) | ⚠️ **See R-13** |
| Enhancements | Continue for remainder of 2026 | Confirmed |
| Access-control system | Glenda | Confirmed |
| Cloud | AWS vs Azure — **UNKNOWN** | Open |
| Shrey's role | DE + DS vs screening — **UNKNOWN** | Open |

**Executive summary (as written):** The T1-2 Experience Agent will extend the Experience Hub knowledge base by providing a simple, centralized way to gather T1-2 customer insights, metrics, and research. It will identify where in the journey T1-2 issues are arising, inform improved messaging and experiences, and measure success in the earliest stages of the T1-2 truck customer journey.

**Conceptual UX (from the mock-up):** User enters Brand(s), Vehicle(s) and Trim Level(s); the agent then asks a few refining questions before responding. Card is branded "Experience Hub Team", "Updated September 1st".

---

## 2. Timeline, Team & Stakeholders

### 2.1 Timeline — two documents disagree

| Source | Statement | If counted from 23 Jul 2026 |
|--------|-----------|----------------------------|
| Proposal §1.2 | MVP ready by **late August / early September** | ≈ 5–6 weeks |
| Delivery Plan | **8–10 weeks for MVP**, enhancement releases through the rest of 2026 | ≈ mid-Sep to early Oct |

> ⚠️ **The two are 3–5 weeks apart.** Both are current documents from the same team. Nobody appears to have reconciled them. See **R-13** — this is the single most useful thing to raise, because it is a factual discrepancy rather than an opinion, and resolving it forces the scope conversation.

### 2.2 Suggested Resource Plan

| Role | Headcount |
|------|-----------|
| Data Engineers | 2–3 |
| Data Scientists / GenAI Engineers | 2 |
| Power BI Developers | 1–2 |
| Databricks Architect | 1 |
| Product Owner / SME | 1–2 |
| QA / UAT | 1 |
| **Total** | **8–11** |

> Shrey is most likely one of the 2 DS/GenAI Engineers, or a hybrid DE+DS — consistent with being told to brush up on *both* halves. There is a dedicated **Databricks Architect** role: that person, not Shrey, should own decision **D-01**.

### 2.3 Stakeholders

*(all GM-side; note four Product Owners)*

| Name | Title | Role on project |
|------|-------|----------------|
| Laura Thorton | Executive Director, Customer Engagement | Product Owner |
| Neelie O'Connor | Executive Director, Customer Experience | Product Owner |
| Ralf Nickel | Director, Customer Experience | Product Owner |
| Kimon Andreou | Sr. Group Analytics Solution Manager | Product Owner |
| Nichole Dilone | Manager, Customer Experience | Manager |

**Dependencies (§1.3)**
- **Glean APIs**
- **MTM Data** (Moments that Matter)
- **VOC Data Integrated**

---

## 3. Objectives (§2)

The T1-2 Experience Agent will:
1. Identify journey stages where T1-2 customers are experiencing **friction or unmet needs**.
2. Translate those insights into **opportunities for improved messaging and experiences**.
3. Enable **measurement of the impact of changes** in the early stages of the T1-2 truck customer journey.
4. Provide **consistent, research-backed answers** based on the Experience Hub knowledge base.

> Objective 3 is the causal-inference bullet. Objective 4 is the RAG bullet. Objectives 1–2 are the insight-generation engine.

---

## 4. Scope and Key Capabilities (§3)

### 3.1 Guided Customer Intelligence Configurator
- Propose a **guided series of questions** that help users filter to the right view of customers.
- Reuse the **existing Experience Hub Customer Filters and Filter Refinement options** — all filterable attributes: Brand, Vehicle, Trim, Region, and others as applicable.

> Maps directly onto the *Vehicle & Customer Info* workbook tab (Brand, Model Name, Model Trim, Region, etc. — all Gold, all accessible). This is the most build-ready capability.

### 3.2 Top Customer Insights Analysis
Connect **VOC data** to the Experience Hub knowledge base so results incorporate:
- Customer comments
- Demand space data
- **Archetype data** ← ⚠️ **not present in the workbook** (see R-10)
- Behavioral data
- Demographic data
- Current research
- Moments that Matter

### 3.3 Reports

**3.3.1 — NOT CAPTURED.** Missing from the photos; request it.

**3.3.2 Pre- and Post-Action Measurement Report**
- When an experience is modified or added, generate a pre/post-action report that measures the effects of those changes on key outcomes.
- Example given: if a new piece of content is added, show whether it influenced engagement, feature usage, or other behaviours.

**3.3.3 Content, Training, and Channel Efficacy Report**
- Provide visibility into engagement with: **Content**, **Training**, **Channels**.
- Enable understanding, over time, of which **combinations** of content, training and channels lead to success.
- Example given: customers who engage with specific onboarding materials *and* participate in a dealer training may be more likely to have a higher NPS score after the first scheduled maintenance visit.

> 🔑 **This resolves the workbook's "need clarity from Adam" items.** Content, Training and Channels aren't content repositories — they're **engagement/usage signals** feeding an efficacy model. That reframes what data to ask Adam for.

**3.3.4 Pre-Built Prompts for Common Actions**
- Offer pre-built prompts corresponding to the reports above, producing consistent, shareable output.
- Allow the user to generate each standard report by pressing a **single button**.

**3.3.5 Data Interrogation via Free-Form Questions**
- Allow users to ask free-form questions so they can interrogate the underlying data.
- Derive answers from the **Experience Hub knowledge base** to ensure consistent, research-backed responses.

> **Architecture read:** 3.3.4 = deterministic, templated report generation. 3.3.5 = open-ended NL query. These are two different execution paths behind one interface — exactly the router argument from the NY Post chatbot. 3.3.4 should almost certainly be parameterised SQL/templates, *not* free LLM generation, because "consistent, shareable output" is the stated requirement.

---

## 4A. Team Responsibilities & Delivery Plan

**Document:** `T1_2_Experie…oles_Plan (1)` — *"T1-2 Experience Agent MVP — Team Responsibilities & Delivery Plan"*
**Subtitle:** *Databricks + GenAI + Power BI Implementation* · **Owner:** Neeti Asthana

> 🔑 **This is the source of the original scope list Shrey was told to "brush up on".** The DE and DS sections below are that list, verbatim — meaning Shrey was sent an extract of the team responsibilities doc. The OCR'd version he received **dropped the first two DE bullets** (Delta Lake architecture, and the ingest bullet). Those are recovered below.

### 4A.1 Data Engineering (DE) — 6 responsibilities

1. **Build Bronze, Silver, and Gold Delta Lake architecture** ← *new, missing from the original extract*
2. **Ingest VOC, survey, customer, behavioral, content, and training data** ← *new, missing from the original extract*
3. Create ETL/ELT pipelines using Databricks Workflows
4. Maintain Unity Catalog — data governance, lineage, and security
5. Prepare curated datasets for reporting and GenAI consumption
6. Data quality checks and monitoring

> Bullet 2 names **content and training data** as ingest targets — further confirmation that Content/Training/Channels are engagement datasets, not content repositories (matches §3.3.3).

### 4A.2 Data Science / GenAI (DS) — 7 responsibilities

1. Build RAG solution using Experience Hub documents
2. Create Vector Search indexes and embedding pipelines
3. Sentiment analysis, topic extraction, pain-point identification
4. Develop customer insight generation engine
5. Implement conversational AI and free-form Q&A
6. Design pre/post action measurement analytics and efficacy models
7. Create prompt library and AI guardrails

### 4A.3 Power BI Team — 6 responsibilities *(new workstream)*

1. Build executive dashboards and KPI scorecards
2. Top Customer Insights dashboard
3. Pre vs Post Action Measurement dashboard
4. Content, Training and Channel Efficacy dashboard
5. Journey friction analysis reports
6. Drill-through by **Brand, Vehicle, Region, Segment and Trim**

> ⚠️ **Overlap with the agent.** Power BI items 2, 3 and 4 are the same three reports the agent delivers in §3.3.2–3.3.4. Two teams are building the same reports on two surfaces. See **R-14**.
> The drill-through dimensions are identical to the §3.1 Guided Configurator filters — one conformed dimension set should serve both.

### 4A.4 Primary Metrics to Track — full list (11)

**Case / contact-centre metrics** *(match the §4.1 Get Help report)*
1. Case Volume
2. Closed within 24 hours (%)
3. First Contact Resolution (%)
4. CSAT / NPS
5. Average Days to Close
6. Open Defects / Features
7. Top Drivers / Pain Points

**Engagement metrics** *(new — not in the §4.1 report)*
8. Content Engagement
9. Training Participation
10. Feature Adoption
11. Channel Effectiveness

> Metrics 8–11 are the inputs to the §3.3.3 efficacy model. **None of the 11 has a confirmed source table** in the workbook. See R-11.

### 4A.5 MVP Deliverables (7) — treat as the scope contract

| # | Deliverable | Maps to | Owner |
|---|-------------|---------|-------|
| 1 | Guided Customer Intelligence Configurator | §3.1 | DS |
| 2 | Top Customer Insights Analysis | §3.2 | DS |
| 3 | Free-form Question Answering Agent | §3.3.5 | DS |
| 4 | Pre-built Prompt Library | §3.3.4 | DS |
| 5 | Pre/Post Action Reports | §3.3.2 | DS + BI |
| 6 | Content and Training Efficacy Reports | §3.3.3 | DS + BI |
| 7 | Power BI Dashboards | §4A.3 | BI |

> Minor inconsistency: deliverable 6 is *"Content and Training"*; §3.3.3 and the Power BI list both say *"Content, Training **and Channel**"*. Confirm whether Channel is in or out of MVP.
> All 7 deliverables map cleanly to known sections — which suggests the missing **§3.3.1** is either a header/intro or a report already covered. Still worth requesting.

---

## 5. Primary Metrics to Track (§4.1)

**Report:** *Get Help — Top 3 Case Types* | June 2026 Performance with 6-Month Trend (Jan 2026 → Jun 2026)

Three case types tracked: **WiFi**, **OnBoarding**, **Infotainment**.

### Metric set (identical across all three)
`Case Volume` · `% Closed in 24 hrs` · `First Contact Resolution` · `CSAT` · `Expert Support Avg Days to Close` · `Open Defects / Features` · `Top 3 Call Drivers` · `Key Actions`

### June 2026 actuals

| Metric | WiFi | OnBoarding | Infotainment |
|--------|------|-----------|--------------|
| Headline | Volume growing; FCR below Jan baseline | Hardware Replacement now the dominant volume driver | First volume reversal in 6 months; CSAT surged |
| Case Volume | 23,043 ▲ | 31,123 ▲ | 12,757 ▼ |
| % Closed in 24 hrs | 95.4% ▲ | 94.8% ▲ | 92.9% ▲ |
| First Contact Resolution | 77.6% ▼ | 77.6% ▲ | 77.0% ▲ |
| CSAT | 82.6% ▲ | N/A | 81.9% ▲ |
| Expert Support Avg Days to Close | 0.66 ▼ | 1.26 ▼ | 1.7 ▼ |
| Open Defects / Features | In Progress | 8 open | In Progress |

### Top 3 call drivers (June 2026, vs Jan-26)

| # | WiFi | OnBoarding | Infotainment |
|---|------|-----------|--------------|
| 1 | No / Slow Internet — 9,372 ▲ (+18%) | **Hardware Replacement — 11,998 ▲ (+397%, 2,413 → 11,998)** | App Not Working — 3,426 ▲ (+5%) |
| 2 | Hotspot: SSID and Password — 1,224 ▲ (+45%) | Enroll Vehicle — 3,218 ▲ (+9%) | On Screen Messages — 1,293 ▼ (−16%) |
| 3 | Hotspot: Data Not Shared / Disabled — 950 ▼ (−3%) | BBWC — 1,134 ▼ (−14%) | DIC (Driver Information Center) — 674 ▼ (−5%) |

### Key actions listed

**WiFi:** Entitlement Issues (containment in progress) · Canadian Plan Issues (target in progress) · AT&T / Jasper Toggles (containment in progress) · Telus Order (fixed 6/10)

**OnBoarding:** Hardware Replacement (epic target date in progress, IVR opportunity) · Tech Line Connect Modernization (October) · Profile Swap Country Code Defects (target in progress) · Connectivity / IMS (AT&T improvement complete; Telus Gen 11 containment complete; software update for Gen 12 in progress)

**Infotainment:** Google Assistant navigation commands (resolved June) · Vehicle App Integration

> 🔑 **Critical gap:** none of these metrics map to a table in the workbook inventory. See R-11.
> 🔑 The **Hardware Replacement +397% jump** is the single loudest signal in the deck, and the "Key Actions" column is literally the pre/post-action list that §3.3.2 is meant to measure. That is the natural first demo: *did the AT&T improvement / Telus containment actually move WiFi FCR?*

---

## 6. The Experience Hub Agentic Workbook

**Source:** Neeti Asthana, 12:06 AM. Original file shared by **Adam**. Three tabs.

**Neeti's three points:**
1. Tab 1 = tables for the **AI Glean/DWG Chatbot** (from Adam's file). Working with **Silver**; **Tim** to obtain **Gold** access.
2. Tab 2 = tables for **Journey Phases**. Following up with Tim — **Glenda roles** pending.
3. Tab 3 = **vehicle** and **customer/demographic** tables. Need Tim for Gold layer.

### 6.1 Tab 1 — AI Chatbot (Glean)

| # | Category | Gold? | Access? | Source Table | Comment |
|---|----------|-------|---------|--------------|---------|
| 1 | Customer Comments | N | Y | `customer_prod.silver_individual_gmna.acxiom_survived_individual_demographic` | ⚠️ **source looks wrong — R-01** |
| 2 | Demand Spaces | Y/N | Y | — | Combination of Vehicle + Customer details; refer *Vehicle & Customer Info* tab |
| 3 | Behavioral Data | N | Y | 🔗 **Gold Source Lucid Chart for Behaviors** | Table created by inserting values from the Lucid Chart ⚠️ **R-02** |
| 4 | Demographic Data | N | Y | `customer_prod.silver_individual_gmna.acxiom_survived_individual_demographic` | |
| 5 | Current Research | — | — | — | Need exact details / what kind of data |
| 6 | Moments that Matter | N | Y | 🔗 **Experience Hub Gold Source.xlsx** | Excel is the Gold source inserted into the final table ⚠️ **R-02** |
| 7 | Needs | N | N | — | **Updiks and Sarada (GM)** working on Experience Source data |
| 8 | Content | N | N | — | Need clarity from Adam → **now clarified by §3.3.3** |
| 9 | Training | N | N | — | Need clarity from Adam → **now clarified by §3.3.3** |
| 10 | Channels | N | N | — | Need clarity from Adam → **now clarified by §3.3.3** |
| 11 | NPS Score | N | Y | `aftersales_prod.silver_enterprise_experience_engine_e3_gmna.survey_hub_inmoment_global_vw`<br>`…survey_hub_inmoment_us_vw` | Need Tim for Gold |

> Comment-to-row alignment is approximate (photo offset; 12 comment strings for 11 rows).

### 6.2 Tab 2 — Journey Stages

Category for all rows: **Journey Stages**. Catalog-level entry: `connected_services_prod.*.*`

| # | Source Table | Access | Gold? | Glenda | Comment |
|---|--------------|--------|-------|--------|---------|
| 1 | `connected_services_prod.bronze_a221498_cob_atcobp_gmi_oepp.enrlmnt_reqst` | Y | N | Approved | |
| 2 | `onstar_subscription_services_product_prod.gold_onstar_subscribed_customer_revenue_gmna.member_base_history` | Y | N | Approved | |
| 3 | `mktg_dmp_silver_prod.a186354_mw_webst_anlyt.cust_engage_actv_detail` | Y | Y | Approved | |
| 4 | `marketing_prod.gold_loyalty_program_rewards_modeling_edai_gmna.omdb_accy_ecom_omdb_txn` | N | N | **Pending** | Glenda role Pending |
| 5 | `marketing_prod.gold_loyalty_program_rewards_reporting_gmna.member` | Y | Y | Approved | |
| 6 | `marketing_prod.silver_clickstream.silver_unpacked_<brandnm>_brand_site_data` | Y | Y | Approved | ⚠️ `<brandnm>` placeholder — per-brand tables |
| 7 | *(table name not captured)* | N | N | **Not showing** | Glenda role missing in My Access Portal for **Abhishek Anand**; Tim contacted |
| 8 | `dataproducts.silver_customer_experience_e3` (E3 Survey Hub — gold NPS) | Y | N | Approved | Have `aftersales_test`, awaiting `aftersales_prod` — **Flora** |
| 9 | `aftersales_prod` — repair order / service history gold tables | N | Need to check | **Pending** | Need exact schema name; **Varun Rajpurohit** to provide access |
| 10 | `marketing_prod.gold_loyalty_program_rewards_modeling_edai_gmna.loyalty_myr_member_ecomm_purchases` | Y | Y | Approved | |
| 11 | `marketing_prod.gold_loyalty_program_rewards_reporting_gmna.member` + loyalty earn/redemption tables | Y | Y | Approved | |
| 12 | `gmdataassets.dl_edge_base_everest_14608_base_crmanltp_gm_adata.individual_vehicle_tb` | Y | Need to check | Approved | Not a Mesh table; check Tim for Mesh version |
| 13 | `aftersales_prod` / `work.cdao_aace_gcs_dev.itv_servicelane_daily_cnt` | N | Need to check | Approved | Role approved but table not visible |
| 14 | `dataproducts.silver_customer_experience_e3` (VoC/NPS) + contact-centre feeds in `connected_services_prod` | Y | N | Approved | Have Silver; need Tim for Gold |
| 15 | `gold_vehicle_warranty_claims_gbl` — warranty coverage / expiration | Y | Y | Approved | Need exact table details |
| 16 | `aftersales_prod` / `gmdataassets.dl_edge_base_everest_14608_base_crmanltp_gm_adata` (CMDS/CRM) | N | Need to check | Approved | Role approved, table not visible |
| 17 | `sales_prod.gold_vehicle_ownership_gmna.vehicle_ownership` | Y | Y | Approved | |

> Status columns are medium-low confidence (steep photo angle). Table names are high confidence.

### 6.3 Tab 3 — Vehicle & Customer Info

**Vehicle attributes 1–10 — all Gold, all accessible**

| # | Category | Source Table |
|---|----------|--------------|
| 1–5 | Vehicle Types, Brand, Model Name, Model Year, Model Trim | `aftersales_prod.gold_enterprise_experience_engine_e3_gmna.e3_vin_detail` |
| 6 | Loyality Status *(sic)* | `…e3_vin_detail` or `…e3_indiv_detail` — verify |
| 7 | Vehicle Mileage | `…e3_indiv_detail` or `marketing_prod.gold_customer_feature_store_gmna.vehicle_attributes` — verify |
| 8–10 | Vehicle Segement *(sic)*, Body Style, Vehicle Categories | `marketing_prod.gold_customer_feature_store_gmna.vehicle_attributes` |

**NPS / verbatims 11–15 — Silver only, no Gold**

11 Dealership NPS · 12 Sales NPS · 13 Dealer NPS Score · 14 Customer Comments · 15 Sales NPS Score
→ all from `aftersales_prod.silver_enterprise_experience_engine_e3_gmna.survey_hub_inmoment_global_vw` + `…_us_vw`
→ *"Need to check with Tim or Updiks for Gold table"*

**Customer / demographic 16–29**

| # | Category | Gold? | Source |
|---|----------|-------|--------|
| 16–20 | Customer Age Group, Age Range, House Hold Income, Is_Current_Customer, State | N | `customer_prod.silver_individual_gmna.acxiom_survived_individual_demographic` |
| 21–25 | Region, Gender Code, Zip Code, No. of Children, Children Flag | N | `customer_prod.silver_individual_gmna.consolidated_customer` |
| 26–27 | Ownership Status, Ownership History | **Y** | `sales_prod.gold_vehicle_ownership_gmna.vehicle_ownership` |
| 28–29 | CallCenter Engagement, Purchased Accessories | N | **none** — *"Need to confirm with Adam, John and Tim"* |

> ⚠️ **CallCenter Engagement having no source is now much more serious** — §4 makes contact-centre case data the primary metric set. See R-11.

---

## 7. Catalog Inventory

| Catalog | Layers | Contains |
|---------|--------|----------|
| `aftersales_prod` | gold, silver | E3 Enterprise Experience Engine: VIN detail, individual detail, InMoment survey hub (NPS + verbatims), repair order / service history |
| `aftersales_test` | — | Test env; team has access here but not prod |
| `customer_prod` | silver | Individual GMNA: Acxiom demographics, consolidated customer |
| `marketing_prod` | gold, silver | Loyalty rewards (modeling + reporting), customer feature store, clickstream |
| `mktg_dmp_silver_prod` | silver | Web analytics, customer engagement activity detail |
| `sales_prod` | gold | Vehicle ownership |
| `connected_services_prod` | bronze | Enrollment requests, contact-centre feeds |
| `onstar_subscription_services_product_prod` | gold | OnStar subscribed customer revenue, member base history |
| `dataproducts` | silver | Customer experience E3 (VoC / NPS survey hub) |
| `gmdataassets` | — | `dl_edge_base_everest_14608_base_crmanltp_gm_adata` — individual vehicle, CMDS/CRM |
| `work` | — | `cdao_aace_gcs_dev` — service lane daily counts (dev/scratch) |

**Naming convention:** `<domain>_<env>.<layer>_<subject_area>_<region/program>.<table>`. Layer lives in the **schema** name, not the catalog. `gmna` = GM North America.

---

## 8. People Map

### GM stakeholders (from the proposal)
| Name | Title |
|------|-------|
| Laura Thorton | Exec Director, Customer Engagement — Product Owner |
| Neelie O'Connor | Exec Director, Customer Experience — Product Owner |
| Ralf Nickel | Director, Customer Experience — Product Owner |
| Kimon Andreou | Sr. Group Analytics Solution Manager — Product Owner |
| Nichole Dilone | Manager, Customer Experience — Manager |

### Delivery team & data contacts
| Person | Role / what they own |
|--------|---------------------|
| **Neeti Asthana** *(corrected spelling)* | Shares datasets and proposal docs; coordinating |
| **Abhiroop Sarkar** | Shared the project outline images; asking for the Word doc and video to be circulated |
| **Adam** | Owns the original source file and category definitions |
| **Tim** | **Gold layer access gatekeeper** — named in nearly every blocker; also Mesh tables |
| **Updiks** *(spelling TBC)* | GM-side; Experience Source data; Gold table contact |
| **Sarada** | GM-side; Experience Source data with Updiks |
| **Flora** | `aftersales_prod` access (vs `aftersales_test`) |
| **Varun Rajpurohit** | Grants access once exact schema names are supplied |
| **Abhishek Anand** | Team member; Glenda role not appearing in My Access Portal |
| **John** | Confirm CallCenter Engagement / Purchased Accessories scope |

---

## 9. Access Status Tracker

| Status | Items |
|--------|-------|
| ✅ Approved + accessible | Vehicle attributes (all 10), vehicle ownership, loyalty reporting/modeling, clickstream, OnStar member base, enrolment requests |
| ⚠️ Approved but table not visible | `work.cdao_aace_gcs_dev.itv_servicelane_daily_cnt`; CMDS/CRM `gmdataassets…` |
| ⏳ Glenda role Pending | `…omdb_accy_ecom_omdb_txn`; aftersales repair order / service history |
| ❌ Role not showing at all | One journey-stage table (Abhishek Anand) |
| 🔍 Env mismatch | Have `aftersales_test`, need `aftersales_prod` (Flora) |
| 🚫 No source defined | Needs, Content, Training, Channels, CallCenter Engagement, Purchased Accessories, **Archetype data**, **all of §4 Get Help metrics** |

**Critical path is access, not engineering.**

---

## 10. Risk Register

| ID | Risk | Why it matters | Suggested action |
|----|------|---------------|------------------|
| **R-13** | **Two current documents give different MVP dates** — Proposal says late Aug / early Sep, Delivery Plan says 8–10 weeks (mid-Sep to early Oct). | A 3–5 week gap that nobody has reconciled. Whichever is wrong, someone's expectations are already misaligned. It is a factual discrepancy, so it's safe to raise. | Ask which date the Product Owners are working to. Use the answer to force the scope conversation |
| **R-09** | **MVP due in 5–10 weeks while Gold access is still pending and 6+ categories have no source at all.** | The schedule assumes data that isn't in hand. Glenda approvals are not fast. | Escalate access as the #1 dependency now; propose a de-scoped MVP on the confirmed-accessible Gold set (vehicle attributes + ownership + loyalty) plus Silver verbatims |
| **R-14** | **The agent and Power BI are building the same three reports** — Top Customer Insights, Pre/Post Action Measurement, Content-Training-Channel Efficacy each appear in both workstreams. | Duplicated effort, and worse, two implementations of the same metric that will disagree in front of executives. | Agree a split: BI owns the canonical numbers and the semantic layer; the agent queries them rather than recomputing. Raise before either team starts building |
| **R-16** | **Nobody on the team has hands-on Glean experience** — stated directly by the manager ("nobody has seen it, right? All of us"). | The integration everyone is assuming will work is the one nobody has done. Glean sits on the critical path for every MVP deliverable. | Spike the Databricks-MCP-into-Glean path in week 1; get a Glean admin named; treat Glean unfamiliarity as a schedule line item, not a background worry |
| **R-15** | **Resource plan calls for 8–11 people incl. a Databricks Architect, a QA/UAT role and 1–2 Power BI devs.** | If the team as staffed is smaller than this, the 8–10 week estimate does not hold — it was sized against this roster. | Compare the plan against who is actually allocated |
| **R-10** | **Archetype data** appears in §3.2 but nowhere in the workbook. | A named MVP input with no identified source. | Ask Adam / Kimon where archetype data lives |
| **R-11** | **§4 primary metrics (case volume, FCR, CSAT, call drivers, Expert Support days) have no mapped table.** Closest is "contact-centre feeds in `connected_services_prod`" and "CallCenter Engagement" which has no source. | The metrics the tool is judged on can't currently be computed. | Find the Get Help / case-management source system and its Databricks landing zone. This is arguably a bigger blocker than the Gold layer |
| **R-01** | Tab 1 maps **Customer Comments** to `acxiom_survived_individual_demographic` — a demographics table with no verbatims. Tab 3 maps it to `survey_hub_inmoment_*`. | The agent's most important unstructured input may point at the wrong table. | Confirm with Adam |
| **R-02** | "Gold" for **Behavioral Data** and **Moments that Matter** was manually inserted from a **Lucid Chart** and an **Excel file**. MTM is a named §1.3 dependency. | No pipeline, lineage, refresh or governance on a stated MVP dependency. | Promote to real UC tables with a defined refresh path |
| **R-03** | **Acxiom** is licensed third-party data. | Licences often restrict derivative use and model training; a vector index over it may breach terms. | Governance/legal check before embedding |
| **R-04** | Zip + Gender + Age + Household Income + No. of Children + VIN in one retrieval surface. | Highly re-identifiable; VIN links to an individual. | UC column masks + row filters before any retrieval layer |
| **R-05** | Four near-duplicate NPS categories from the same two views. | Conflicting answers from the agent. | Get metric definitions; build one conformed NPS fact |
| **R-06** | `survey_hub_inmoment_global_vw` **and** `_us_vw` used together everywhere. | Is US a subset of global? Double counting. | Determine relationship before union |
| **R-07** | `silver_unpacked_<brandnm>_brand_site_data` placeholder. | Per-brand table proliferation. | Get the brand list |
| **R-08** | §3.3.1 not captured; a Word doc and a **video** exist that the team hasn't circulated. | Unknown scope sitting in un-shared artefacts. | Abhiroop already asked Neeti for these — follow up |
| **R-12** | Four Product Owners across two orgs (Customer Engagement + Customer Experience) plus an Analytics PO. | Competing definitions of done on a 6-week MVP. | Get one accountable decision-maker for scope calls |

---

## 10A. Current Task (as of 23 Jul)

**Assigned:** build synthetic data for the Gold tables from the workbook, stand up a Databricks Genie space on it, and work out how it connects to Glean agents. 100–200 rows, explicitly small, POC only.

**Purpose (manager's words):** a quick refresher for the team now, and speed later — when real access arrives the team swaps the data source rather than starting the integration.

**Constraints stated:** productionisation must run through **Gold** tables, but not all Gold tables are available; use Silver only where no Gold exists. Duplication/entity resolution is the anticipated data problem and is **deliberately deferred** until after MVP.

**Access:** Databricks accesses begin arriving **next week** (w/c 27 Jul). 1 August relates to onboarding/billing/account linking, **not** the project start.

**Deliverable:** `T1_2_Synthetic_Data_Genie_Glean_Workflow.md` + `generate_synthetic_data.py` + 12 synthetic tables.

**Check-in:** evening progress update expected.

---

## 11. Architecture Decisions & Reads

| ID | Item | Read | Status |
|----|------|------|--------|
| **D-01** | **Where does the agent run?** | "Glean APIs" is a §1.3 dependency and the conceptual mock is a Glean agent card — strongly implies **Glean is the delivery surface** and Databricks is the data/analytics layer behind it. If true, Mosaic AI Agent Framework / Model Serving may *not* be the serving path, and the integration is Glean → Databricks (SQL Warehouse / API). | **Unconfirmed — the Databricks Architect role should own this** |
| **D-02** | 3.3.4 vs 3.3.5 execution paths | 3.3.4 (pre-built prompts, one-button reports, "consistent shareable output") should be **parameterised/templated queries**, not free LLM generation. 3.3.5 (free-form) is the genuine NL path. Two paths, one interface, a router in between. | Proposed |
| **D-03** | Three retrieval surfaces | Unstructured verbatims (RAG) · journey event tables (text-to-SQL) · vehicle/customer attributes (structured filters). Matches the three workbook tabs. Supports the router argument from NY Post. | Proposed |
| — | *(no formal ADRs recorded yet)* | | |

---

## 12. Open Questions

| # | Question | Owner | Asked? |
|---|----------|-------|--------|
| 1 | **Which MVP date is real — late Aug/early Sep, or 8–10 weeks? (R-13)** | Product Owners | No |
| 2 | **Is Glean the delivery surface, with Databricks as the data layer? (D-01)** | Databricks Architect / Kimon | No |
| 3 | **Who owns the canonical metric definitions — Power BI or the agent? (R-14)** | Kimon Andreou | No |
| 4 | Is Shrey DE, DS, or hybrid within the 8–11 person roster? | Neeti | No |
| 3 | **What is the source system + Databricks table for the §4 Get Help case metrics? (R-11)** | Adam / John / Tim | No |
| 4 | **Where does Archetype data live? (R-10)** | Adam / Kimon | No |
| 5 | Is Customer Comments → acxiom demographic a mistake? (R-01) | Adam | No |
| 6 | What exactly is §3.3.1? | Neeti | No |
| 7 | Can we get the Word doc and the video Abhiroop referenced? | Neeti | Abhiroop asked 12:15 AM |
| 8 | What does **T1-2** designate precisely — which truck programs/model years? | Any PO | No |
| 9 | Relationship between `_global_vw` and `_us_vw`? | Tim / Updiks | No |
| 10 | Full brand list for `<brandnm>` clickstream tables | Marketing | No |
| 11 | What is DWG in "AI Glean/DWG Chatbot"? | Neeti | No |
| 12 | Exact schema name for aftersales repair order / service history | Varun Rajpurohit needs this | No |
| 13 | Which is the Mesh equivalent of `individual_vehicle_tb`? | Tim | No |
| 14 | AWS or Azure Databricks? | — | No |
| 15 | Acxiom licence terms re: GenAI use (R-03) | Legal / governance | No |
| 16 | Given the MVP date, what is the agreed minimum scope? (R-09) | Product Owners | No |

---

## 13. Glossary

| Term | Meaning |
|------|---------|
| **T1-2** | GM truck platform/program designation; the customer segment this agent serves. Exact scope TBC |
| **Experience Hub** | GM's CX knowledge base. The agent extends it. Also has "Customer Filters" and "Filter Refinement" UI the agent must reuse |
| **T1-2 Experience Agent** | The product being built |
| **E3** | Enterprise Experience Engine — GM CX platform; appears in schema names and as "E3 Survey Hub" |
| **Glean** | Enterprise search/assistant platform. "Glean APIs" is a hard dependency |
| **Glenda** | GM's access-role provisioning system; roles must be approved before a table is visible ("My Access Portal") |
| **MTM** | Moments that Matter — CX framework term, and a §1.3 dependency |
| **VOC** | Voice of Customer |
| **DWG** | Unexpanded acronym in "AI Glean/DWG Chatbot" |
| **GMNA** | GM North America |
| **InMoment** | Third-party CX/survey vendor — NPS + verbatims |
| **Acxiom** | Third-party consumer demographic data provider |
| **Demand Spaces** | Marketing segmentation concept — vehicle + customer attribute combination |
| **Archetype** | Customer segmentation concept named in §3.2; source unknown |
| **Get Help** | GM's customer support / case management channel — source of §4 metrics |
| **FCR** | First Contact Resolution |
| **CSAT** | Customer Satisfaction |
| **BBWC** | Call driver under OnBoarding; expansion unknown |
| **DIC** | Driver Information Center |
| **IVR** | Interactive Voice Response |
| **IMS** | Connectivity subsystem referenced in OnBoarding key actions |
| **Tech Line Connect** | GM system undergoing modernization (October) |
| **Gen 11 / Gen 12** | Connectivity hardware generations |
| **Mesh table** | GM's data-mesh-registered version of a table |
| **CMDS** | GM CRM/customer master data system |
| **Everest / dl_edge_base** | Legacy GM data-lake naming in `gmdataassets` |

---

## 14. Referenced Artefacts (not yet in hand)

| Artefact | Why it matters | Have it? |
|----------|---------------|----------|
| **Video walkthrough** | Abhiroop: "the video will give more context" | ❌ **Request — highest value** |
| **Neeti's Word doc** | Abhiroop: "your word doc also had some important info" | ❓ Possibly the Delivery Plan — now captured. Confirm there isn't a second doc |
| §3.3.1 of the proposal | Missing capability section | ❌ Request |
| `Experience Hub Gold Source.xlsx` | Source of truth for Moments that Matter | ❌ Request |
| `Gold Source Lucid Chart for Behaviors` | Source of truth for Behavioral Data | ❌ Request |
| The workbook `.xlsx` itself | Resolve photo alignment ambiguities | ❌ Request |
| Adam's original file | Parent of the workbook | ❌ Request |
| Experience Hub Customer Filters spec | §3.1 says to reuse existing filters | ❌ Request |

---

## 15. Databricks Component Map

| Need | Databricks component | Replaces (Shrey's usual stack) |
|------|---------------------|-------------------------------|
| Ingestion | Lakeflow Connect | Custom ingest / Airflow |
| Declarative pipelines | Lakeflow Declarative Pipelines (ex-DLT) | Airflow DAGs |
| Orchestration | Lakeflow Jobs (ex-Workflows) | Airflow |
| Governance | Unity Catalog | Manual RBAC |
| Retrieval | Mosaic AI Vector Search (Delta Sync index) | Postgres + Redis |
| Serving | Mosaic AI Model Serving — ⚠️ *may be Glean instead, see D-01* | FastAPI |
| Batch LLM | `ai_query` / AI Functions in SQL | — (no equivalent) |
| Agents | Mosaic AI Agent Framework (LangGraph first-class) | LangGraph standalone |
| Guardrails | AI Gateway guardrails | Hand-rolled |
| Tracking/eval | MLflow 3 + Agent Evaluation | MLflow |
| Text-to-SQL BI | Genie / AI-BI — ⚠️ *but **Power BI** is the stated BI layer, so Databricks SQL Warehouse → Power BI is the likely path* | Persona SQL generation |

**Naming alert:** say *Lakeflow*, not *DLT* or *Workflows*.

---

## 16. Prep Priority *(re-ordered after Rev 3)*

1. **Causal inference / experiment design** ← promoted. §3.3.2 and §3.3.3 are now fully specified and are the differentiating capability. DiD, matched controls, interrupted time series, uplift/combination effects
2. **Unity Catalog security** — masks, row filters, ABAC (Glenda + PII)
3. Lakeflow Declarative Pipelines — expectations, streaming tables vs MVs, AUTO CDC
4. `ai_query` / AI Functions — for verbatim sentiment/topic extraction on `survey_hub_inmoment_*`
5. Vector Search Delta Sync
6. **Glean API integration patterns** ← new, pending D-01
7. Agent Framework + MLflow 3 eval
8. AI Gateway guardrails
9. **Databricks → Power BI integration** (SQL Warehouse connector, DirectQuery vs Import, semantic model design) ← new, given the third workstream

---

## 17. Parking Lot

- **Best first demo:** the §4 "Key Actions" list is literally a set of interventions with dates (Telus Order fixed 6/10, AT&T improvement complete, Google Assistant resolved June). Pair one of those with the corresponding metric trend and you have a working §3.3.2 pre/post report using data that already exists.
- FordDirect built a near-identical unified chatbot over proprietary data with Unity Catalog syncing vector indexes — closest public analogue.
- The three workbook tabs map cleanly to three retrieval surfaces (see D-03).
- Doc numbering bug: two sections are labelled **1.2** (Timeline and Stakeholders).
