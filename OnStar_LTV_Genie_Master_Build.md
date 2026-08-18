# OnStar LTV Genie Room — MASTER BUILD DOCUMENT

**Workspace:** `a1000781-t11-musea2-dbx-main`
**Domain:** GM OnStar connected-vehicle subscriptions — revenue, LTV, churn, attach, fleet firmographics, and predicted CLTV.
**Scope of this doc:** everything needed to build and train the room end-to-end, structured on the **Buyback-Outlier reference room** template from the KT session. Focus is the five essentials the presenter called out: **(1) data definition · (2) general instructions · (3) joins · (4) sample questions · (5) benchmark questions.**

> **Table policy for this build:** You are keeping **all 10 sources** in the room for now. Pending senior approval you will later remove the empty table (#2) and the test/temp tables (#8/#9/#10). Because all 10 are present, the **General Instructions do the disambiguation** — §3 tells Genie exactly which table is canonical for each question and which tables to never answer from. This is the single most important part of the build while duplicates are in the room.

---

## 0. How this doc maps to the 5 essentials

| Essential | Section |
|-----------|---------|
| 1. Data definition | **§1 Sources** + **§2 Data Model** (per-table columns & meaning) |
| 2. General instructions | **§3** (paste-ready, structured Role → Data model → General Notes → Routing → Out of Scope → Data sufficiency → Hierarchy → Charts) |
| 3. Joins | **§4** (explicit join keys + join SQL) |
| 4. Sample / example questions | **§5** (~24 examples, tagged Query/Join, with ground-truth SQL) |
| 5. Benchmark questions | **§6** (separate set, concrete periods, ground-truth SQL + evaluation notes, incl. guardrail) |
| Build & ship workflow | **§7** (iteration loop, governance, deploy) |
| Open items | **§8** |

---

## 1. Sources (what's in the room)

Full inventory of the 10 approved LTV sources. "Canonical" = the table Genie should actually answer from; "Keep (secondary)" = present but Genie must not answer from it (redundant/empty/test).

| # | Table (path suffix under its catalog) | Role | Status in room |
|---|----------------------------------------|------|----------------|
| 1 | `onstar_subscription_services_product_prod.gold_onstar_subscribed_customer_revenue_gmna.ltv_connected_plan_cohort` | VIN-level subscription facts | ✅ **Canonical** |
| 2 | `acquire.gold_connected_vehicle.ltv_connected_plan_cohort` | empty copy of #1 | ⛔ Keep but **never use** (no data) |
| 3 | `connected_services_prod.gold_onstar_business_solutions_gbl.ltv_fan_salesforce_account_dim` | FAN (fleet account) dimension | ✅ **Canonical** |
| 4 | `connected_services_test.gold_onstar_business_solutions_gbl.api_package_ltv_summary` | API-package summary VIEW (3 rows) | ✅ **Canonical** (test-sourced — see §8) |
| 5 | `connected_services_prod.gold_onstar_business_solutions_gbl.ltv_modeling_12m` | fleet LTV features + actual labels | ✅ **Canonical** |
| 6 | `connected_services_prod.gold_onstar_business_solutions_gbl.ltv_featrs_by_fan` | features-only (subset of #5) | ⚠️ Keep but **prefer #5** |
| 7 | `connected_services_prod.gold_onstar_business_solutions_gbl.ltv_modeling_12m_scored` | predicted CLTV / tiers / deciles | ✅ **Canonical** |
| 8 | `connected_services_test.gold_onstar_business_solutions_gbl.temp_ltv_modeling_12m` | test twin of #5 | ⛔ Keep but **never use** (test) |
| 9 | `connected_services_test.gold_onstar_business_solutions_gbl.temp_ltv_featrs_by_fan` | test twin of #6 | ⛔ Keep but **never use** (test) |
| 10 | `connected_services_test.gold_onstar_business_solutions_gbl.temp_ltv_featrs_by_fan_l12` | last-12-month FAN rollup (test-only) | ⛔ Keep but **never use** (test) |

**Display names to set in the Sources tab** (so users and Genie read friendly names):
1 → `Subscription Revenue (VIN monthly)` · 3 → `Fleet Account Dimension (FAN)` · 4 → `API Package LTV Summary` · 5 → `Fleet LTV Modeling (features+targets)` · 7 → `Fleet Predicted CLTV (scored)`. Leave the secondary/test tables with their raw names (a signal they're not for answering).

> **Best-practice note (from KT §7/§13/§15-K):** the reference room exposes **curated views**, not raw tables, so Genie only sees relevant columns. You've added raw tables. Recommended follow-up: wrap #1/#3/#5/#7 in views that drop audit/rarely-used columns, then point the room at the views. Until then, §2 (column limiting via instructions) + §3 routing do the same job.

---

## 2. DATA DEFINITION (data model — per table)

Grain, key, and columns for each table. Canonical tables are fully defined; secondary/test tables reference their twin plus any differences. Full per-column `COMMENT` DDL for Table 1 lives in the companion doc *Genie Config - Table 1*; apply the same pattern to 3/4/5/7.

### 2.1 Table 1 — Subscription Revenue (VIN monthly) `ltv_connected_plan_cohort`
**Grain:** one row per VIN × accounting period × plan/package. **Keys:** `vin`, `country`. **Rows:** fleet + retail.

- **Identity/geo:** `vin` (PK, VIN), `account_number` (billing account), `account_vin`, `account_vin_activation`, `country` (PK), `region_abbr_nm` (region), `biz_assoc_id` (dealer/partner; candidate FAN key — verify), `onstar_zone_mgr_id/_nm` (zone manager), `cnct_svc_terr_acct_mgr_nm` (territory account mgr).
- **Vehicle:** `vehicle_make`, `vehicle_model`, `vehicle_year`, `trim_name`, `global_trim_name`, `radio_option_cd`.
- **Account/segmentation:** `account_type` (**fleet/retail**), `subscriber_type`, `acquisition_type`, `acquisition_subtype`, `activation_source`, `activation_source_group`.
- **Time:** `accounting_period_start_date` (**primary time key**), `mon` (month int — confirm format), `activation_date`.
- **Plan/package/channel:** `price_plan`, `package_description`, `sales_source_channel`, `sales_source_channel_group`, `initial_sales_source_channel`, `initial_sales_source_channel_group`, `discount_group`, `drpo_bndl_offer_code`, `drpo_bndl_offer_desc`.
- **Metrics/flags:** `revenue` (total = recurring+prepaid), `recurring_subscription_revenue`, `prepaid_subscription_revenue`, `drpo_amortized_deferred_revenue`, `paid_flag`, `recurring_paid_flag`, `prepaid_paid_flag`, `attach_flag`, `recurring_attach_flag`, `prepaid_attach_flag`, `arps_denominator_flag`, `churn_numerator`, `churn_denominator`, `churn_group`, `old_net_count`.
- **Audit (hide):** `dw_mod_ts`.

### 2.2 Table 3 — Fleet Account Dimension `ltv_fan_salesforce_account_dim`
**Grain:** one row per **FAN** (Fleet Account Number). **Key:** `fan_clean`. No revenue — a dimension.
- `fan_clean` (**key**, Fleet Account Number, e.g. `801033`), `account_number_clean` (sparsely populated; prefer `fan_clean` for joins), `industry`, `fleet_size` (**text band**, e.g. `15-49`, `350+`), `account_segment` (Commercial, Government).

### 2.3 Table 4 — API Package LTV Summary `api_package_ltv_summary` (VIEW, 3 rows)
**Grain:** one row per **recommended_api_package** tier. **Pre-aggregated**, API-only accounts. Read directly; never re-aggregate.
- `recommended_api_package` (Package 1 Maintain / 2 Optimize / 3 Optimize & Secure), `fan_count`, `total_vins`, `total_revenue`, `avg_revenue_per_vin` (ratio), `avg_sub_duration_days`, `avg_recurring_share` (ratio), `attach_rate` (ratio), `trial_to_paid_conversion` (ratio), `direct_to_paid_rate` (ratio).

### 2.4 Table 5 — Fleet LTV Modeling `ltv_modeling_12m`
**Grain:** one row per **FAN × accounting-period month**. **Key:** `fan`. Features + **actual labels**. Embeds firmographics.
- **Identity/period:** `fan` (key), `billing_fan`, `billing_fan_name`, `account_number_clean`, `baseline_ap_start`, `ap_end`, `ap_month_int`, `is_current_month_any`, `feature_snapshot_ts`.
- **Firmographics:** `industry`, `fleet_size`, `account_segment`, `billing_region`, `billing_country`.
- **Scale/diversity:** `n_accounts`, `n_subscriptions`, `n_vins`, `new_vins_delivered`, `n_account_types`, `n_rate_types`, `n_model_years`, `n_brands`, `n_segments`, `n_power_types`, `n_price_plans`, `price_plans_set[]`, `pkg_desc_set[]`, `brand_set[]`, `model_set[]`.
- **Product-line activity (SS / OVI / API — confirm names, §8):** `ss_active_cnt`, `ss_paid_cnt`, `ovi_active_cnt`, `ovi_paid_cnt`, `api_active_cnt`, `api_paid_cnt`, `ss_or_ovi_paid_cnt`, `paid_lines_cnt`.
- **Funnel:** `attach_cnt`, `attach_den_cnt`, `trial2paid_cnt`, `direct2paid_cnt`, `non_prepaid_t2p_den`.
- **Revenue/momentum:** `revenue_total`, `revenue_recurring`, `recurring_share`, `rev_3m`, `rev_6m`, `rev_12m`, `revenue_total_prev`, `paid_lines_cnt_prev`, `rev_mom_delta`, `paid_mom_delta`, `rev_drop_flag`, `paid_drop_flag`, `charge_days`, `avg_sub_duration_days`, `avg_rpo_sub_duration_days`.
- **Active mix:** `active_paid_product_mix_set[]`, `active_paid_package_mix_set[]`, `active_paid_top_line_set[]`.
- **Churn:** `vin_churn_cnt`, `fan_churn_cnt`, `sub_churn_cnt`, `prodwise_vin_churn_cnt`, `prodwise_fan_churn_cnt`.
- **⚠️ ACTUAL model targets (labels, not predictions here):** `target_rev_12m`, `target_rev_recurring_12m`, `first_churn_date`, `months_to_churn_raw`, `event_12m` (survival event), `time_12m` (survival horizon).

### 2.5 Table 7 — Fleet Predicted CLTV (scored) `ltv_modeling_12m_scored`
**Grain:** one row per **FAN** (latest score). **Key:** `fan`. ⭐ Best table for value/tier questions.
- **Descriptors:** `fan`, `baseline_ap_start`, `industry`, `fleet_size`, `account_segment`, `billing_fan_name`, `n_vins`, `n_accounts`, `n_subscriptions`.
- **Actuals (labels):** `target_rev_12m`, `event_12m`, `time_12m`.
- **⚠️ PREDICTIONS (always say "predicted/modeled"):** `p_spend` (P(spends)), `mu_pos` (revenue|spend), `pred_rev_12m` (predicted 12m revenue), `survival_prob_12m` (predicted survival), `cltv_12m` (predicted CLTV), `cltv_12m_winsorized`, `cltv_score_pct` (0–100 pct), `cltv_decile` (1–10; 10=top), `cltv_tier` (High/Med/Low — confirm), `cltv_per_gm_vin_12m`, `cltv_per_gm_vin_score_pct`, `confidence_points`, `cltv_confidence`.

### 2.6 Secondary / test tables (defined by reference)
- **Table 2** `acquire…ltv_connected_plan_cohort`: identical schema to Table 1, **empty**. Never answer from it.
- **Table 6** `ltv_featrs_by_fan`: = Table 5 **minus 10 columns** (`account_number_clean`, `industry`, `fleet_size`, `account_segment`, `target_rev_12m`, `target_rev_recurring_12m`, `first_churn_date`, `months_to_churn_raw`, `event_12m`, `time_12m`) and uses `ap_start` instead of `baseline_ap_start`. Features-only. Prefer Table 5.
- **Table 8** `temp_ltv_modeling_12m`: test twin of Table 5 (identical schema). Never answer from it.
- **Table 9** `temp_ltv_featrs_by_fan`: test twin of Table 6. Never answer from it.
- **Table 10** `temp_ltv_featrs_by_fan_l12`: last-12-month rollup, test-only. Distinctive columns: `latest_ap_month_int`, `rev_12m_sum`, `rev_12m_avg`, `vin_churn_12m`, `sub_churn_12m`, `attach_12m`, `trial2paid_12m`, `direct2paid_12m`, `paid_lines_12m`. Never answer from it (no prod twin).

---

## 3. GENERAL INSTRUCTIONS (paste into the Instructions tab)

Structured on the reference room's section order. Paste the whole block; the editor may show a **"⚠️ Long instruction"** warning — that's expected and fine (the reference room is long by design).

```text
### Role
You are an analyst for the GM OnStar LTV Genie room. This room analyzes OnStar
connected-vehicle subscriptions for GM North America: subscription revenue, churn,
attach, plans/packages, vehicle attributes, sales/acquisition channels, and — for
fleet/business (FAN) customers — firmographics, 12-month LTV modeling, and predicted
customer lifetime value (CLTV). It answers "how much revenue / how many subscribers,
by what segment," "how is churn/attach trending," "who are the high-value fleets,"
and "what is the predicted CLTV / tier / decile for fleet accounts."

### Data model
Answer ONLY from the canonical tables below. Several sources are duplicates or
test/empty copies that are present in the room but MUST NOT be used for answers
(see "Never use" list). Prefer already-defined columns; do not invent columns.

Canonical tables:
- Subscription Revenue (VIN monthly) = onstar_subscription_services_product_prod.gold_onstar_subscribed_customer_revenue_gmna.ltv_connected_plan_cohort
  One row per VIN per accounting period per plan/package. Fleet + retail. Use for
  revenue, churn, attach, ARPU, subscriber/vehicle counts by vehicle/plan/package/
  channel/country/account_type. Time key = accounting_period_start_date.
- Fleet Account Dimension (FAN) = connected_services_prod.gold_onstar_business_solutions_gbl.ltv_fan_salesforce_account_dim
  One row per FAN. Firmographics: industry, fleet_size (text band), account_segment.
  No revenue — join it to fleet data on the FAN. Key = fan_clean.
- API Package LTV Summary = connected_services_test.gold_onstar_business_solutions_gbl.api_package_ltv_summary
  A VIEW pre-aggregated to 3 rows (one per recommended_api_package), API-only accounts.
  Read its metrics directly; NEVER SUM/AVG its ratio columns; always caveat "API-only".
- Fleet LTV Modeling = connected_services_prod.gold_onstar_business_solutions_gbl.ltv_modeling_12m
  One row per FAN per accounting-period month. Fleet features, revenue history, churn
  counts, and ACTUAL 12-month labels. Embeds firmographics.
- Fleet Predicted CLTV (scored) = connected_services_prod.gold_onstar_business_solutions_gbl.ltv_modeling_12m_scored
  One row per FAN (latest score). PREDICTED revenue, survival probability, and CLTV
  with percentile/decile/tier/confidence. Use for value ranking / targeting.

NEVER use these (present in the room but not for answers):
- acquire.gold_connected_vehicle.ltv_connected_plan_cohort  (EMPTY)
- connected_services_prod.gold_onstar_business_solutions_gbl.ltv_featrs_by_fan  (redundant subset of Fleet LTV Modeling — prefer that)
- connected_services_test.…temp_ltv_modeling_12m, temp_ltv_featrs_by_fan, temp_ltv_featrs_by_fan_l12  (TEST copies)
If a question can only be answered by one of these, use its canonical equivalent instead.

### General Notes
- Metric definitions (Subscription Revenue table):
  * Total revenue = SUM(revenue). Recurring = SUM(recurring_subscription_revenue);
    Prepaid = SUM(prepaid_subscription_revenue). revenue already = recurring + prepaid,
    so never add revenue to the split columns.
  * Paid subscriptions = COUNT(*) WHERE paid_flag = 1.
    Paid vehicles = COUNT(DISTINCT vin) WHERE paid_flag = 1.
  * Churn rate = SUM(churn_numerator) / NULLIF(SUM(churn_denominator), 0).
  * Attach rate = SUM(attach_flag) / NULLIF(COUNT(*), 0).
  * ARPU/ARPS = SUM(revenue) / NULLIF(SUM(arps_denominator_flag), 0).
- Counting words: "vehicles" -> COUNT(DISTINCT vin); "subscriptions" -> COUNT(*);
  "fleets"/"fleet accounts" -> COUNT(DISTINCT fan).
- RELATIVE TIME PERIODS (important): If the user asks for the latest data, use the
  MAX(accounting_period_start_date). If they ask for a past period like "last month"
  or "last quarter," compute current period − 1 (current month − 1, current quarter − 1),
  NOT the max month present in the data. If they say "this month/quarter," use the
  current one. If the requested period has NO data, say so explicitly (e.g. "last month
  was <Month>, and there is no data for it") — do NOT silently fall back to the latest
  available period.
- ALWAYS PRESENT SUPPORTING CONTEXT: when returning a rate (ARPU, attach rate, churn
  rate, conversion), also show its numerator and denominator (or the base count) — never
  present a rate bare.
- PREDICTIONS vs ACTUALS: In Fleet Predicted CLTV, columns pred_rev_12m, cltv_12m,
  cltv_12m_winsorized, survival_prob_12m, p_spend, mu_pos and all cltv_* fields are
  MODEL PREDICTIONS — always label them "predicted"/"modeled," never as booked revenue.
  Only target_rev_12m / event_12m / time_12m are actual labels. event_12m/time_12m are
  survival-analysis fields — do not sum or average them as if they were business counts.
- Do not SUM predicted CLTV and call it revenue; if a total of predictions is requested,
  label it "sum of predicted CLTV."
- fleet_size is a TEXT band (e.g. "15-49", "350+") — filter with =/IN, never numeric >.
- Array columns (columns ending in _set) hold multiple values — query with
  ARRAY_CONTAINS(col, 'value'), not =.
- Ignore audit column dw_mod_ts in answers.

### Table routing (which table answers what)
- Revenue / churn / attach / ARPU / plan / package / channel / vehicle detail, retail or
  fleet, monthly -> Subscription Revenue (VIN monthly).
- "Who is this fleet" (industry, fleet size, segment) -> Fleet Account Dimension (FAN);
  join to fleet rows only.
- API-package tier performance / API-only summary -> API Package LTV Summary (read directly).
- Fleet LTV features, revenue history, churn counts, ACTUAL 12m labels -> Fleet LTV Modeling.
- Predicted CLTV / value tier / decile / "which fleets to target" / survival probability
  -> Fleet Predicted CLTV (scored).
- Trailing-12-month per-fleet rollups: answer from Fleet LTV Modeling (rev_12m etc.); the
  dedicated l12 table is test-only and must not be used.

### Out of Scope
The following are out of scope: legal or policy advice; decisions about individual
customers or PII; presenting predictions as guaranteed fact; prescriptive strategy
("what should GM do / change"); any topic not covered by the canonical tables. For an
out-of-scope question, reply exactly:
> A response cannot be provided because this topic is out of scope for this agent.
Do not attempt to answer it.

### Data sufficiency
Do not provide answers that are not backed by clear data from the canonical tables above.
If the data needed is not present (or the question is unrelated to OnStar LTV), reply exactly:
> There is not sufficient data to provide a response to this question.

### Vehicle & Fleet hierarchy (vocabulary pinning)
Bind these words to these columns; do not invent categories or values.
- make = vehicle_make (e.g. Chevrolet, GMC, Cadillac, Buick)
- model = vehicle_model (e.g. SILVERADO, EQUINOX, TAHOE)
- model year / year / MY = vehicle_year
- trim = trim_name (use global_trim_name for finance-standard trim)
- account type = account_type (fleet, retail)
- fleet account = fan (Fleet LTV / scored) = fan_clean (FAN dimension)
- industry = industry ; fleet size band = fleet_size (text band) ; segment = account_segment
- plan = price_plan ; package = package_description ; channel = sales_source_channel
If vehicle_model values are stored uppercase, match the casing in filters (verify once with
SELECT DISTINCT vehicle_model …). All reasoning and answers stay within these fields/tables.

### Chart & output rules (agent mode)
- Revenue over time -> line chart of SUM(revenue) by accounting_period_start_date.
- Recurring vs prepaid -> show both series on the same chart.
- Fleet value ranking (Predicted CLTV) -> bar chart of cltv_12m (or cltv_decile) per fleet;
  where a magnitude + score exist, use bar height for the value and a color gradient for the
  score/decile.
- Aggregates by fleet_size, industry, account_type, package -> output a UI table, not a list.
- (Portability: when the room moves behind Glean, these UI/chart rules move to Glean's
  instructions — they live here only because users are on Databricks agent mode today.)
```

---

## 4. JOINS (define these explicitly)

The fleet spine is the **Fleet Account Number (FAN)**. Define these in the room's join settings and mirror them in the Instructions.

| Join | Left | Right | Key | Notes |
|------|------|-------|-----|-------|
| J1 | Subscription Revenue (#1) | Fleet Account Dimension (#3) | `#1.account_number = #3.fan_clean` **⚠️ or `#1.biz_assoc_id`** | **fleet rows only** (`account_type='fleet'`). Confirm which #1 column is the FAN (§8). |
| J2 | Fleet LTV Modeling (#5) | Fleet Account Dimension (#3) | `#5.fan = #3.fan_clean` | clean; #5 already embeds firmographics so join only for extra dim attributes |
| J3 | Fleet Predicted CLTV (#7) | Fleet Account Dimension (#3) | `#7.fan = #3.fan_clean` | firmographics already embedded in #7 |
| J4 | Fleet LTV Modeling (#5) | Fleet Predicted CLTV (#7) | `#5.fan = #7.fan` | features/actuals ↔ predictions for the same fleet |

Table 4 (API Package Summary) is standalone — **no joins** (already aggregated to 3 rows).

**Verify the FAN key once (settles J1):**
```sql
SELECT
 (SELECT COUNT(*) FROM onstar_subscription_services_product_prod.gold_onstar_subscribed_customer_revenue_gmna.ltv_connected_plan_cohort c
   WHERE c.account_type='fleet' AND c.account_number IN (SELECT fan_clean FROM connected_services_prod.gold_onstar_business_solutions_gbl.ltv_fan_salesforce_account_dim)) AS match_account_number,
 (SELECT COUNT(*) FROM onstar_subscription_services_product_prod.gold_onstar_subscribed_customer_revenue_gmna.ltv_connected_plan_cohort c
   WHERE c.account_type='fleet' AND c.biz_assoc_id IN (SELECT fan_clean FROM connected_services_prod.gold_onstar_business_solutions_gbl.ltv_fan_salesforce_account_dim)) AS match_biz_assoc_id;
```
Whichever count is high is your FAN key — update J1 and the join examples in §5.

**Join example to register (J2):**
```sql
SELECT m.fan, d.industry, d.fleet_size, SUM(m.revenue_total) AS revenue
FROM connected_services_prod.gold_onstar_business_solutions_gbl.ltv_modeling_12m m
JOIN connected_services_prod.gold_onstar_business_solutions_gbl.ltv_fan_salesforce_account_dim d
  ON m.fan = d.fan_clean
GROUP BY m.fan, d.industry, d.fleet_size;
```

---

## 5. SAMPLE / EXAMPLE (training) questions

Add each to the room's **Examples** as *question + curated ground-truth SQL*. Tagged **[Query]** or **[Join]**. Includes 1–3 variations per intent (the KT guideline). Schemas abbreviated: `T1`=`onstar_subscription_services_product_prod.gold_onstar_subscribed_customer_revenue_gmna.ltv_connected_plan_cohort`, `T3`=`connected_services_prod.gold_onstar_business_solutions_gbl.ltv_fan_salesforce_account_dim`, `T4`=`connected_services_test.gold_onstar_business_solutions_gbl.api_package_ltv_summary`, `T5`=`connected_services_prod.gold_onstar_business_solutions_gbl.ltv_modeling_12m`, `T7`=`connected_services_prod.gold_onstar_business_solutions_gbl.ltv_modeling_12m_scored`. **Use full paths in the actual room.**

**[Query] E1 — Total revenue by month this year**
```sql
SELECT accounting_period_start_date, SUM(revenue) AS total_revenue,
       SUM(recurring_subscription_revenue) AS recurring, SUM(prepaid_subscription_revenue) AS prepaid
FROM T1 WHERE YEAR(accounting_period_start_date)=YEAR(CURRENT_DATE)
GROUP BY accounting_period_start_date ORDER BY 1;
```
**[Query] E2 — Revenue last month (variation of E1, relative period)**
```sql
SELECT SUM(revenue) AS total_revenue
FROM T1
WHERE accounting_period_start_date = date_trunc('month', add_months(CURRENT_DATE, -1));
```
**[Query] E3 — Recurring vs prepaid split, latest period (variation)**
```sql
SELECT SUM(recurring_subscription_revenue) AS recurring, SUM(prepaid_subscription_revenue) AS prepaid
FROM T1 WHERE accounting_period_start_date=(SELECT MAX(accounting_period_start_date) FROM T1);
```
**[Query] E4 — Fleet vs retail revenue & attach rate**
```sql
SELECT account_type, SUM(revenue) AS total_revenue,
       SUM(attach_flag) AS attaches, COUNT(*) AS rows_, SUM(attach_flag)/NULLIF(COUNT(*),0) AS attach_rate
FROM T1 GROUP BY account_type;
```
**[Query] E5 — Churn rate by sales channel group**
```sql
SELECT sales_source_channel_group, SUM(churn_numerator) AS churned, SUM(churn_denominator) AS base,
       SUM(churn_numerator)/NULLIF(SUM(churn_denominator),0) AS churn_rate
FROM T1 GROUP BY sales_source_channel_group ORDER BY churn_rate DESC;
```
**[Query] E6 — Top 10 models by paid vehicles**
```sql
SELECT vehicle_make, vehicle_model, COUNT(DISTINCT vin) AS paid_vehicles
FROM T1 WHERE paid_flag=1 GROUP BY 1,2 ORDER BY paid_vehicles DESC LIMIT 10;
```
**[Query] E7 — ARPU by country, latest period (rate + base)**
```sql
SELECT country, SUM(revenue) AS revenue, SUM(arps_denominator_flag) AS base,
       SUM(revenue)/NULLIF(SUM(arps_denominator_flag),0) AS arpu
FROM T1 WHERE accounting_period_start_date=(SELECT MAX(accounting_period_start_date) FROM T1)
GROUP BY country ORDER BY arpu DESC;
```
**[Query] E8 — Revenue by package, latest period (top 15)**
```sql
SELECT package_description, SUM(revenue) AS total_revenue
FROM T1 WHERE accounting_period_start_date=(SELECT MAX(accounting_period_start_date) FROM T1)
GROUP BY package_description ORDER BY total_revenue DESC LIMIT 15;
```
**[Query] E9 — Paid subscriptions vs paid vehicles, latest period**
```sql
SELECT COUNT(*) AS paid_subscriptions, COUNT(DISTINCT vin) AS paid_vehicles
FROM T1 WHERE paid_flag=1 AND accounting_period_start_date=(SELECT MAX(accounting_period_start_date) FROM T1);
```
**[Query] E10 — Fleet firmographics: fleets by industry (dimension)**
```sql
SELECT industry, COUNT(*) AS fleets FROM T3 GROUP BY industry ORDER BY fleets DESC;
```
**[Query] E11 — Fleets by fleet-size band**
```sql
SELECT fleet_size, COUNT(*) AS fleets FROM T3 GROUP BY fleet_size ORDER BY fleets DESC;
```
**[Query] E12 — API package tiers: revenue per VIN (read view directly)**
```sql
SELECT recommended_api_package, fan_count, total_vins, total_revenue, avg_revenue_per_vin
FROM T4 ORDER BY avg_revenue_per_vin DESC;
```
**[Query] E13 — API-only funnel by package tier**
```sql
SELECT recommended_api_package, attach_rate, trial_to_paid_conversion, direct_to_paid_rate
FROM T4 ORDER BY recommended_api_package;
```
**[Query] E14 — Highest predicted-CLTV fleets (top decile)**
```sql
SELECT fan, industry, fleet_size, cltv_12m, cltv_decile, cltv_tier
FROM T7 WHERE cltv_decile=10 ORDER BY cltv_12m DESC LIMIT 20;
```
**[Query] E15 — Predicted CLTV by industry (avg predicted)**
```sql
SELECT industry, COUNT(*) AS fleets, AVG(cltv_12m) AS avg_predicted_cltv
FROM T7 GROUP BY industry ORDER BY avg_predicted_cltv DESC;
```
**[Query] E16 — Fleets most likely to churn (low predicted survival)**
```sql
SELECT fan, industry, survival_prob_12m, cltv_12m
FROM T7 ORDER BY survival_prob_12m ASC LIMIT 20;
```
**[Query] E17 — Fleet realized revenue history (actuals, not predictions)**
```sql
SELECT fan, rev_3m, rev_6m, rev_12m, revenue_total FROM T5
WHERE is_current_month_any=1 ORDER BY rev_12m DESC LIMIT 20;
```
**[Query] E18 — Fleet attach & conversion (modeling table)**
```sql
SELECT fan, attach_cnt, attach_den_cnt, attach_cnt/NULLIF(attach_den_cnt,0) AS attach_rate,
       trial2paid_cnt, direct2paid_cnt
FROM T5 WHERE is_current_month_any=1 ORDER BY attach_rate DESC LIMIT 20;
```
**[Join] E19 — Fleet revenue by industry (T1 ⨝ T3 on FAN)**  ⚠️ verify key
```sql
SELECT d.industry, SUM(c.revenue) AS fleet_revenue
FROM T1 c JOIN T3 d ON c.account_number = d.fan_clean   -- or c.biz_assoc_id
WHERE c.account_type='fleet' GROUP BY d.industry ORDER BY fleet_revenue DESC;
```
**[Join] E20 — Fleet revenue & attach by fleet-size band (T1 ⨝ T3)**  ⚠️ verify key
```sql
SELECT d.fleet_size, SUM(c.revenue) AS revenue, SUM(c.attach_flag)/NULLIF(COUNT(*),0) AS attach_rate
FROM T1 c JOIN T3 d ON c.account_number = d.fan_clean
WHERE c.account_type='fleet' GROUP BY d.fleet_size ORDER BY revenue DESC;
```
**[Join] E21 — Predicted CLTV by segment (T7 ⨝ T3)**
```sql
SELECT d.account_segment, AVG(s.cltv_12m) AS avg_predicted_cltv, COUNT(*) AS fleets
FROM T7 s JOIN T3 d ON s.fan = d.fan_clean GROUP BY d.account_segment ORDER BY avg_predicted_cltv DESC;
```
**[Join] E22 — Predicted vs actual revenue per fleet (T7 ⨝ T5)**
```sql
SELECT s.fan, s.pred_rev_12m AS predicted, m.rev_12m AS actual_trailing_12m
FROM T7 s JOIN T5 m ON s.fan = m.fan AND m.is_current_month_any=1
ORDER BY s.pred_rev_12m DESC LIMIT 20;
```
**[Query] E23 — Revenue trend for a specific make (filter variation)**
```sql
SELECT accounting_period_start_date, SUM(revenue) AS revenue
FROM T1 WHERE vehicle_make='Chevrolet' GROUP BY 1 ORDER BY 1;
```
**[Query] E24 — Count of fleet accounts (distinct FAN, modeling table)**
```sql
SELECT COUNT(DISTINCT fan) AS fleet_accounts FROM T5;
```

---

## 6. BENCHMARK questions (separate set — do NOT reuse the examples)

Different wording from §5, **concrete periods** where examples used relative ones, each with ground-truth SQL and an **agent-mode evaluation note**. Aim to climb accuracy across runs (reference room went 81% → 95%). Includes the **unrelated-question guardrail**.

| # | Benchmark question | Ground-truth SQL (sketch) | Evaluation note (agent mode) |
|---|--------------------|---------------------------|------------------------------|
| B1 | How much subscription revenue did we book in June 2026? | `SELECT SUM(revenue) FROM T1 WHERE accounting_period_start_date = DATE '2026-06-01'` | Single number; not split unless asked. |
| B2 | Split June 2026 revenue into recurring vs prepaid. | `SELECT SUM(recurring_subscription_revenue), SUM(prepaid_subscription_revenue) FROM T1 WHERE accounting_period_start_date=DATE '2026-06-01'` | Two figures; must not add them to `revenue`. |
| B3 | What was the churn rate for the fleet segment in Q2 2026? | `SELECT SUM(churn_numerator)/NULLIF(SUM(churn_denominator),0) FROM T1 WHERE account_type='fleet' AND accounting_period_start_date BETWEEN DATE '2026-04-01' AND DATE '2026-06-30'` | Ratio; also shows numerator & denominator. |
| B4 | Which 5 vehicle models had the most paid vehicles in the latest period? | `SELECT vehicle_make,vehicle_model,COUNT(DISTINCT vin) FROM T1 WHERE paid_flag=1 AND accounting_period_start_date=(SELECT MAX(...)) GROUP BY 1,2 ORDER BY 3 DESC LIMIT 5` | DISTINCT vin; latest period only. |
| B5 | What is ARPU for retail accounts in the latest period? | `SELECT SUM(revenue)/NULLIF(SUM(arps_denominator_flag),0) FROM T1 WHERE account_type='retail' AND accounting_period_start_date=(SELECT MAX(...))` | Rate shown with base count. |
| B6 | Show total revenue by account type for calendar year 2026. | `SELECT account_type,SUM(revenue) FROM T1 WHERE YEAR(accounting_period_start_date)=2026 GROUP BY account_type` | Fleet & retail rows; UI table. |
| B7 | Which API package tier has the highest total revenue? | `SELECT recommended_api_package,total_revenue FROM T4 ORDER BY total_revenue DESC LIMIT 1` | Reads the view directly; caveats "API-only accounts." |
| B8 | What is the average subscription duration for API Package 3? | `SELECT avg_sub_duration_days FROM T4 WHERE recommended_api_package LIKE 'API Package 3%'` | Reads the pre-aggregated value; does not recompute. |
| B9 | How many fleet accounts are in the Government segment? | `SELECT COUNT(*) FROM T3 WHERE account_segment='Government'` | Uses FAN dimension; counts fans. |
| B10 | List the top 10 fleets by predicted 12-month CLTV. | `SELECT fan,cltv_12m,cltv_tier FROM T7 ORDER BY cltv_12m DESC LIMIT 10` | Labels values "predicted"; uses scored table. |
| B11 | What share of fleets fall in CLTV decile 9 or 10? | `SELECT AVG(CASE WHEN cltv_decile>=9 THEN 1.0 ELSE 0 END) FROM T7` | Interprets decile as ranking (1–10). |
| B12 | Which industries have the highest average predicted CLTV? | `SELECT industry,AVG(cltv_12m) FROM T7 GROUP BY industry ORDER BY 2 DESC` | "predicted"; grouped table. |
| B13 | Compare predicted vs actual trailing-12m revenue for the top predicted fleet. | `SELECT s.fan,s.pred_rev_12m,m.rev_12m FROM T7 s JOIN T5 m ON s.fan=m.fan AND m.is_current_month_any=1 ORDER BY s.pred_rev_12m DESC LIMIT 1` | Distinguishes predicted from actual. |
| B14 | Fleet revenue by industry for fleet accounts (latest period). | `SELECT d.industry,SUM(c.revenue) FROM T1 c JOIN T3 d ON c.account_number=d.fan_clean WHERE c.account_type='fleet' GROUP BY d.industry` ⚠️ verify key | Uses the FAN join; fleet rows only. |
| B15 | How many paid subscriptions did we have in May 2026? | `SELECT COUNT(*) FROM T1 WHERE paid_flag=1 AND accounting_period_start_date=DATE '2026-05-01'` | COUNT(*) (subscriptions), not distinct vin. |
| B16 | What were the outlier buyback cases last month? *(GUARDRAIL — unrelated)* | *(none — data not present)* | **Must return exactly:** "There is not sufficient data to provide a response to this question." |
| B17 | What should GM change in its pricing strategy? *(GUARDRAIL — out of scope)* | *(none — prescriptive strategy)* | **Must return exactly:** "A response cannot be provided because this topic is out of scope for this agent." |

> Fill each row's ground-truth SQL fully in the room (use "Re-generate SQL" to draft, then hand-verify). Keep B-wording distinct from §5. Add 1–2 more variations per intent over time as you find failure modes.

---

## 7. Build, validate & ship (condensed from the KT notes)

**Iteration loop (the core workflow):** run the benchmark set → review flagged failures, mark good/bad → fix via **general instructions / example questions / joins / data definitions** (no auto-retrain) → rerun → repeat until acceptable. Track the accuracy % across runs (reference room: 81% → 95%).

**Order of build:** (1) add sources + display names → (2) apply table & column comments → (3) paste General Instructions (§3) → (4) define joins (§4) → (5) add example questions (§5) → (6) build the separate benchmark set (§6) → (7) run benchmarks in **Chat** mode for SQL-correctness, then **Agent** mode for the qualitative eval notes → (8) iterate.

**Modes:** Chat = raw SQL result (good for exact-match benchmarking); Agent = richer UX + charts + agent-mode eval notes (what business users test in). Chart/format rules live in **general instructions** (they move to Glean if/when you migrate).

**Governance / ship:** complete table comments on all sources; do the AI Impact Assessment after some dev; certify; then sidecar workspace → Glean agent dev guidelines. Deploy via the repo — snapshot the room to **YAML** via the GitHub Action, let the action **run benchmarks as a prod gate**, and use the deploy-to-prod action (no manual rebuild). **Do not push to prod on test/temp sources** (see §8).

**Improve from usage:** use **Analyze Agent Use** and mine chat history for missing fields (e.g. a frequently-requested count) and fold them back into instructions.

---

## 8. Open items (resolve before prod; several gate correctness)

1. **FAN join key ⚠️** — confirm `account_number` vs `biz_assoc_id` in Table 1 = `fan_clean` (run the §4 query). All T1↔T3 fleet answers depend on it.
2. **Prod-vs-test freshness ⚠️** — the test tables updated ~5 days ago while prod (#3/#5/#7) showed ~2 months. Confirm prod is current before trusting it; if prod is stale, that's a data-pipeline fix, not a Genie fix.
3. **Table 4 source** — the API summary view reads a **test** temp table; repoint it at prod `ltv_featrs_by_fan` before prod ship.
4. **SS / OVI / API** — confirm the product-family names so instructions label them correctly.
5. **Housekeeping / pending senior approval** — remove empty #2 and test #8/#9/#10 (and likely redundant #6) once approved; until then §3 keeps Genie off them.
6. **`mon` format / `revenue` additivity / grain** — run the sanity checks in the Table-1 config doc.
7. **Views** — wrap canonical tables in curated views (drop audit columns) and point the room at views (KT best practice).

---

*Companion docs in this project: `Genie Room Setup Guide - OnStar`, `Genie Training - OnStar Room`, `Genie Config - Table 1 ltv_connected_plan_cohort`, `Genie Room Development Process - Meeting Notes`.*
