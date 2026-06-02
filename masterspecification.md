# AUDIENCE INTELLIGENCE PLATFORM — MASTER SPECIFICATION DOCUMENT

**Version:** 1.0
**Status:** APPROVED FOR ENGINEERING
**Primary Source:** `.claude/spec-source.md` (Spec v3.0 + Blueprint v2.0 merged)
**Date:** 2026-05-30
**Scope:** All 15 engineering phases, 9 database tables, 46 ML features, 9 personas, 4 API endpoints

> Every architectural claim in this document is traceable to `spec-source.md`. Claims that extend beyond the source documents are marked **[ARCHITECTURAL DECISION]** with rationale. Conflicts between source documents are flagged in Section 15 (Open Questions).

---

## TABLE OF CONTENTS

1. Executive Summary
2. Business Problem Definition
3. Stakeholders
4. User Personas (System Users)
5. Functional Requirements
6. Non-Functional Requirements
7. ML System Requirements
8. Data Requirements
9. Platform Requirements
10. Success Metrics
11. Project Phases and Milestones
12. Constraints
13. Assumptions
14. Risks
15. Open Questions
16. Engineering Standards

---

## SECTION 1: EXECUTIVE SUMMARY

The Audience Intelligence Platform (AIP) is an ML-powered audience segmentation and propensity scoring system purpose-built for digital publishers. It ingests behavioural, subscription, email, social, push notification, and commerce data from eight source systems; constructs a 46-feature user-level matrix; trains an unsupervised clustering pipeline to assign one of nine human-readable persona labels per registered user; and exposes those assignments in real time via a FastAPI microservice backed by Redis. The platform replaces editorial guesswork with data-discovered behavioural archetypes, giving publishers a single unified reader view they can activate across newsletters, programmatic advertising, subscription upsell, and churn prevention.

### Three Core Systems

**Data Platform.** Eight source connectors (Zephr, GA4/BigQuery, Braintree, Sailthru, Pushly, OpenWeb, Trackonomics, Transunion) feed nine PostgreSQL staging tables. An Airflow DAG orchestrates nine sequential pipeline steps — ingestion, identity stitching, feature engineering, validation, scaling, algorithm evaluation, clustering, write-back, and cache refresh — on a weekly cadence. The data platform produces a feature store with one row per registered user containing 46 normalised numeric ML features.

**ML Platform.** A four-stage algorithm evaluation framework (HDBSCAN discovery → BisectingKMeans + GMM evaluation → composite-score selection → weekly production runs) selects the optimal algorithm and cluster count K per client deployment. Five algorithms are available: BisectingKMeans, KMeans, GaussianMixture, HDBSCAN, and Ensemble. Three propensity scores (subscription, churn, commerce) are computed from centroid distances and scaled feature combinations — not from supervised models. Every run is tracked in MLflow with full artifact and metric logging, enabling rollback.

**Serving Platform.** A FastAPI microservice reads persona assignments from Redis (TTL 7 days) and returns persona labels, cluster IDs, propensity scores, and soft GMM scores at p99 < 10 ms for single-user requests and p99 < 100 ms for batch requests of up to 1,000 user IDs. Users absent from the cache are handled by a rule-based cold-start path that returns a deterministic persona label without hitting the database.

### Business Model

AIP is sold as a B2B SaaS product to digital publishers of all sizes. Each client receives an isolated deployment: their own PostgreSQL schema, their own pipeline run, and their own algorithm selection. The platform is vendor-agnostic; it requires no specific CMS, ad server, or email platform. Source system connectors are the only integration surface.

### NYPost Validation Benchmark

The platform architecture is directly derived from the New York Post Data Labs initiative, which segmented 66 million users across 8 source systems using Bisecting K-Means and discovered 9 behavioural personas. AIP extends that foundation with a multi-algorithm evaluation framework and a propensity scoring layer. The NYPost scale (50–100M users, 200–500M GA4 events/year) is the large-client design target. Development and testing use a 100,000-user synthetic dataset that mirrors real-world persona proportions.

### Expected Business Outcomes

| Goal | Mechanism | Target |
|------|-----------|--------|
| Subscription revenue | Identify Subscription-Focused readers before they churn; trigger upsell at behavioural signal | +15–25% subscription conversion rate vs non-personalised baseline |
| Ad revenue | Serve advertisers verified high-intent segments commanding premium CPMs | +20–40% CPM uplift on segmented vs run-of-site inventory |
| Newsletter engagement | Personalise newsletter content per persona — each reader receives articles matching proven content affinity | +30–50% CTR improvement on segmented newsletters |
| Churn reduction | Identify Low Engagers and dormant users early, trigger re-engagement before they leave | −20% annual churn rate on identified at-risk segments |

---

## SECTION 2: BUSINESS PROBLEM DEFINITION

### Why Digital Publishers Fail to Monetise Their Audience Data

Digital publishers own massive reader datasets spanning web behaviour, email engagement, social interactions, push notifications, and commerce — yet monetise them as if these datasets do not exist. Audience segments are editorial guesses hardcoded into CMS rules: defined by humans, not discovered from data. A sports editor believes the sports section audience is homogeneous; in reality it contains loyalist subscribers, casual mobile readers, social engagers sharing match results, and commerce users clicking affiliate gear links. Without ML-discovered segments, every monetisation trigger fires indiscriminately at the wrong people at the wrong moment.

### Five Revenue Leakage Points

1. **Newsletters reach the wrong readers.** When all registered users receive the same newsletter, open rates and CTRs reflect the average of nine heterogeneous personas. A Sports-Focused reader receiving celebrity content unsubscribes. A Loyalist receiving a generic re-engagement email that ignores their 12-month subscription history churns faster than one receiving a renewal incentive. The cost is measurable: every mismatched send erodes the sender reputation and accelerates list decay.

2. **Ad inventory is sold at run-of-site CPMs.** Without verified audience segments, publishers cannot credibly package premium inventory. Advertisers pay $3–5 CPMs for run-of-site when they would pay $15–30 CPMs for a verified Sports-Focused segment aged 18–34 with push opt-in. The gap is real and quantified by the NYPost experience where persona-verified inventory commanded 20–40% CPM premiums.

3. **Subscription upsells trigger at random moments to unqualified users.** Without propensity scores, upsell banners fire on every page load for every user including users who churned three months ago and Low Engagers who will never convert. This wastes marketing budget and trains users to dismiss upsell prompts. The subscription_propensity_score surfaces the 2.8% of users who are Subscription-Focused before they churn, enabling precisely timed upsell sequences.

4. **Churn is detected too late.** Publishers discover a subscriber has cancelled only when the Braintree event fires. By that point the subscriber has already mentally departed — days_since_last_visit has been climbing for weeks and bounce_rate has been rising. The churn_propensity_score detects this drift 30 days before cancellation, giving the re-engagement team actionable lead time.

5. **High-value readers are invisible and therefore untargeted.** The Loyalist persona (738K at NYPost scale) generates disproportionate revenue per user: long subscription tenure, high email engagement, high commerce conversion. Without segmentation they are invisible in the average. Without targeted retention campaigns they churn at the same rate as Low Engagers despite being worth 5× more per user in annual revenue.

### Why Editorial Segmentation Fails vs ML-Discovered Segments

Editorial segments are defined by journalists and product managers who understand content, not behaviour. They segment by content category read, not by the combination of recency, frequency, monetisation signals, and social participation that actually separates high-value readers from low-value ones. A user reading sports content could be a Loyalist subscriber, a Sports-Focused casual reader, or a Social Engager primarily sharing match content on social — three completely different activation strategies. Content-based segments collapse these distinctions. ML clustering finds the boundaries that actually exist in the data.

### Run-of-Site vs Persona-Verified CPMs

Run-of-site inventory is priced on context (the article being read) not audience (who is reading it). Programmatic buyers bid low because they cannot verify the reader's characteristics. When a publisher can verifiably assert "this impression is served to a Sports-Focused user aged 18–34 with a push opt-in and a sports newsletter subscription and an active Braintree subscription," the CPM floor moves from $3–5 to $15–30. The technical requirement to make this assertion credible is a real-time persona API that the ad server can call at impression time — exactly what the Serving Platform provides.

### Vendor-Agnostic and Deployable to Any Publisher

The platform makes no assumptions about which CMS, ad server, email platform, or subscription management system a publisher uses. Source system connectors are the integration surface; the feature store, ML pipeline, and API are independent of downstream systems. A publisher running WordPress, FreeWheel, and Klaviyo can deploy AIP with the same pipeline as one running Arc, GAM, and Sailthru. The only hard dependency is a GA4 BigQuery export, which is the native GA4 data path for all Google Analytics customers.

### Secondary Goals

- Build adaptive segments that evolve automatically as new data is ingested, requiring no manual reconfiguration when audience behaviour shifts seasonally or following a major editorial pivot.
- Surface hidden micro-segments that editorial teams would never define manually — the Occasional Buyer who is not a committed commerce user but who clicks affiliate links when content is contextually relevant is a segment no editor would define but a clustering algorithm will always discover.
- Provide a single unified reader view: one row per user aggregating signals from eight source systems that have never previously been joined at the user level.
- Support flexible cluster counts — K=5 for small niche publishers, K=12–15 for multi-brand publishers — without re-architecting the pipeline.

---

## SECTION 3: STAKEHOLDERS

For each stakeholder type: role, what they need from the platform, interaction frequency, what failure looks like, what success looks like.

### 3.1 Data Engineers

**Role and Responsibilities.** Build and maintain the Airflow DAG, source system connectors, identity stitching logic, and feature engineering pipeline. Own pipeline reliability, data quality monitoring, and source system integrations. Configure GA4 BigQuery export, Sailthru API connections, and Transunion batch job scheduling.

**What They Need.** A fully instrumented pipeline where every step logs its row counts, duration, and deviation metrics. Clear failure modes that abort safely rather than silently producing corrupt feature stores. Per-step runtime tracking so anomalies surface in Grafana before they cause downstream ML quality issues.

**Interaction Frequency.** Daily — monitoring pipeline alerts, investigating data quality deviations, maintaining source integrations. Weekly — reviewing full pipeline run logs and silhouette trend alongside ML engineers.

**Failure.** A pipeline step writes a partial feature store without triggering an alert, producing silently corrupted clustering output that takes two weekly runs to discover. Or a GA4 coverage drop from 95% to 82% goes undetected because monitoring thresholds were not configured, resulting in feature-sparse clustering that mislabels thousands of Sports-Focused users as Casual Readers.

**Success.** The weekly pipeline runs end-to-end without manual intervention 49 out of 52 weeks per year. When a source system fails, the pipeline aborts at the correct gate, fires the appropriate PagerDuty alert, and retains the prior week's persona assignments — leaving users correctly labelled rather than unlabelled.

### 3.2 ML Engineers / Data Scientists

**Role and Responsibilities.** Own the clustering model and algorithm evaluation framework. Tune K, evaluate silhouette scores, run HDBSCAN discovery, and name personas. Own the MLflow model registry and retraining triggers. Add new features to improve cluster quality as new source systems become available.

**What They Need.** Reproducible experiments (random_state=42, scaler.pkl in every MLflow run). A composite scoring framework that documents *why* BisectingKMeans K=9 was selected over GMM K=8 so the decision can be audited and reversed. Feature importance per cluster (F-32) so they can explain to the editorial team why Cluster 3 is named Sports-Focused and not Sports-Adjacent.

**Interaction Frequency.** Weekly — review clustering outputs, evaluate model drift, run experiments for new clients. On-demand — when stability drops below 80% for three consecutive weeks and Stage 2 re-evaluation is triggered.

**Failure.** A silhouette score drops from 0.41 to 0.28 with no alert, the prior week's assignments are silently retained for two more weeks, and the business team runs three mis-targeted campaigns before anyone notices the persona distribution has shifted. Or a new engineer re-fits the StandardScaler on inference data, producing a scaler that deviates from the training-time scaler and systematically mislabels new users.

**Success.** Every MLflow run is fully reproducible: same data, same config, same random_state → same cluster assignments. The model registry shows six months of silhouette history, every dip is explained by a corresponding data quality event, and the rollback procedure has been tested at least once in a staging environment.

### 3.3 Backend / API Engineers

**Role and Responsibilities.** Build and maintain the FastAPI persona serving microservice, Redis cache management, API key authentication middleware, and downstream integration webhooks (Sailthru, ad server, CMS). Ensure the < 10 ms p99 SLA is met continuously.

**What They Need.** A Redis cache that is always populated (7-day TTL ensures no gap between weekly pipeline runs). A cold-start path that never returns a 404 for a valid user_id. A batch endpoint that handles up to 1,000 user IDs in a single Redis pipeline call with predictable latency.

**Interaction Frequency.** Sprint-based for feature development. On-call for API uptime incidents. Weekly for cache health checks and Redis memory utilisation review.

**Failure.** The Redis TTL is set incorrectly to 6 days, creating a 24-hour window each week where high-traffic users get cache misses. Every cache miss hits cold_start.py rule evaluation, slowing response times from 5 ms to 80 ms during the ad serving peak and causing SLA breaches.

**Success.** The API serves 10,000 requests/second at p99 < 10 ms. The cold-start path serves all valid user IDs with is_cold_start: true within 5 ms. The health endpoint accurately reflects pipeline_last_run timestamp so monitoring dashboards have a single truth source.

### 3.4 Analytics / BI Engineers

**Role and Responsibilities.** Build Grafana dashboards for cluster stability, persona distribution trend, feature coverage, pipeline runtime, and business KPIs. Build self-serve reporting for business stakeholders. Own A/B test measurement infrastructure for segmented vs control campaigns.

**What They Need.** MLflow API access to pull run metrics into Grafana panels. SQL access to the feature store for custom persona cohort analysis. A clear definition of the persona distribution drift metric (F-31) so the dashboard representation matches the alert logic.

**Interaction Frequency.** Weekly — dashboard maintenance, ad-hoc analyses for revenue and editorial teams. Per campaign — A/B lift measurement.

**Failure.** The Grafana persona stability chart shows week-over-week persona counts rather than percentage overlap, misleading stakeholders into thinking stability is high when it is actually degraded. Or the silhouette trend panel has a stale data connection and shows last month's score as current.

**Success.** Business stakeholders can open a single Grafana dashboard and understand in 30 seconds whether the pipeline ran successfully, whether cluster quality is within SLA, and what the business performance trend is for each persona segment.

### 3.5 Newsletter / Email Team

**Role and Responsibilities.** Use persona labels to segment Sailthru send lists. Configure which content template each persona receives. Review CTR performance reports. Request persona-specific newsletter products.

**What They Need.** A reliable weekly persona refresh so send lists are built from current assignments. An API or database query they can use to pull the list of user IDs per persona label. CTR reporting segmented by persona so they can validate that Sports-Focused users receiving sports-heavy content outperform the control group.

**Interaction Frequency.** Daily — send scheduling and performance review. Weekly — list segmentation refresh after pipeline run.

**Failure.** A pipeline failure leaves persona assignments 14 days stale. The newsletter team continues sending persona-segmented content, but 15% of users have shifted persona (e.g. lapsed subscribers moving from Loyalist to Low Engager) and are receiving renewal upsell emails that are no longer appropriate.

**Success.** Newsletter CTR for segmented sends is consistently 30–50% above the unsegmented control. The team can build send lists in Sailthru by querying persona_label and have confidence the data was refreshed in the past 7 days.

### 3.6 Advertising / Revenue Team

**Role and Responsibilities.** Package persona segments as premium audience inventory in the ad server (GAM/Xandr). Build the media kit with persona reach statistics. Set CPM floor prices per persona segment.

**What They Need.** Stable, reproducible persona counts per segment so the media kit numbers do not change week-to-week by more than the natural distribution drift threshold. Confidence that Sports-Focused (6.6M at NYPost scale) is a genuinely distinct, verifiable audience — not an editorial guess.

**Interaction Frequency.** Weekly — campaign planning and campaign performance reporting. Monthly — rate card updates and advertiser reporting.

**Failure.** An algorithm re-evaluation switches from BisectingKMeans K=9 to GMM K=8, collapsing the Sports-Focused and Social-Engager clusters into a single Sports-Social segment. The revenue team has already sold a Sports-Focused campaign at a CPM premium; the merged segment does not meet the advertiser's targeting criteria.

**Success.** The persona distribution has < 30% relative week-over-week drift for all non-Low-Engager segments (F-31). The ad server receives a real-time API call at impression time confirming persona_label, enabling verified programmatic targeting.

### 3.7 Subscription / Growth Team

**Role and Responsibilities.** Use subscription_propensity_score to trigger upsell banners and email sequences. Monitor conversion rate by persona. Design win-back flows for cancelled Subscription-Focused users.

**What They Need.** A subscription_propensity_score between 0.0 and 1.0 for every registered user, updated weekly. A threshold from which to trigger upsell (configurable, suggested 0.65+). The is_cold_start flag in the API response so upsell logic is not mistakenly triggered for rule-based cold-start users who have not yet accumulated sufficient session data.

**Interaction Frequency.** Weekly — campaign setup and conversion funnel review. Monthly — cohort churn analysis.

**Failure.** The subscription_propensity_score formula weights are hardcoded in Python rather than loaded from configs/base.yaml. A weight change intended to boost recall for lapsed subscribers is applied in the wrong environment, miscalibrating scores for 3,500 users in a production upsell sequence.

**Success.** Subscription conversion rate for users with propensity_score > 0.65 is 15–25% above the unsegmented baseline. Churn rate for actively targeted Loyalist and Subscription-Focused users is 20% below the overall subscriber churn rate.

### 3.8 Editorial / Content Team

**Role and Responsibilities.** Use content affinity ratios to understand what drives which audience segments. Inform editorial commissioning decisions — knowing Sports-Focused is 6.6M users justifies investment in sports coverage. Configure homepage personalisation rules.

**What They Need.** The ratio_* feature values per persona (the centroid values per cluster for content affinity features), communicated in plain language: "Sports-Focused users spend 51% of their time on sports content." Feature importance per cluster (F-32) expressed as a dashboard panel they can read without ML knowledge.

**Interaction Frequency.** Monthly — content strategy reviews and persona briefings.

**Failure.** The feature importance computation (F-32) is not surfaced in the Grafana dashboard, leaving the editorial team with opaque cluster numbers and no mechanism to understand why Cluster 4 has been renamed from Sports-Focused to Sports-Social.

**Success.** The editorial team can open the persona dashboard and see, for each cluster: the top five defining features, the estimated user count, the dominant content affinity ratio, and a plain-language label. Content commissioning decisions are validated against persona size and engagement metrics, not editorial intuition.

### 3.9 Product Managers

**Role and Responsibilities.** Own the platform roadmap. Prioritise new data sources, new personas, and new activation channels. Define new KPIs. Liaise between technical and business teams.

**What They Need.** A clear phase tracker showing implementation status. A single source of truth for what the platform does and does not do — this master specification document serves that function. Business KPI dashboards that do not require ML knowledge to interpret.

**Interaction Frequency.** Weekly — roadmap reviews and stakeholder alignment. Quarterly — KPI target reviews.

**Failure.** Phase 3 (ETL ingestion) is completed before the database schema (Phase 2) is finalised, creating an ingestion module that writes to a table structure that subsequently changes. The Product Manager approved the Phase 3 start without verifying Phase 2 was fully merged to main.

**Success.** Every phase is gated on the prior phase's merge to main. The phase tracker in CLAUDE.md reflects ground truth. No phase contains a TODO, placeholder, or pseudo-code comment in committed files.

### 3.10 Publishing Client Data Team (SaaS Deployment)

**Role and Responsibilities.** Connect source systems for the client publisher, monitor pipeline health, review persona and algorithm quality each week. Typically one or two data engineers embedded at the client.

**What They Need.** Clear documentation of the required source system connections, the data format expected for each connector, and the integration test suite they can run to validate connectivity before the first pipeline run.

**Interaction Frequency.** Daily during onboarding (first 2 weeks). Weekly thereafter.

**Failure.** The client's GA4 BigQuery export is in a non-standard table format (nested JSON rather than flattened events). The etl/ingestion/ga4.py connector fails silently on the first run, producing a feature store with zero GA4 features for all users. All users are clustered primarily on subscription and email signals alone.

**Success.** The client's source systems are validated within 2 weeks of onboarding. The first live pipeline run completes with GA4 coverage > 90%, and the resulting persona distribution matches the expected ranges for the client's publisher type and size.

### 3.11 Publishing Client Business Team (SaaS Activation)

**Role and Responsibilities.** Configure newsletter templates, ad targeting segments, and upsell flows per persona. Consume the persona API for campaign activation.

**What They Need.** A stable API with a published OpenAPI spec. Persona labels that are human-readable and consistent week-to-week. Business-facing documentation explaining what each persona means in plain language and what activation strategies are recommended.

**Interaction Frequency.** Weekly — campaign configuration and performance reporting.

**Failure.** A deployment update changes the persona_label string values (e.g. from `sports_focused` to `sports-focused` with a hyphen). All downstream systems that hardcoded the label string as a targeting key silently stop matching users.

**Success.** Persona label strings are stable and versioned. Any label change is treated as a breaking API change with a migration notice period.

### 3.12 Platform Support Team

**Role and Responsibilities.** Onboard new clients, handle integration issues, monitor cross-client infrastructure. Typically one data engineer plus one ML engineer per ten clients at launch.

**What They Need.** Cross-client infrastructure dashboards (Grafana) showing pipeline health per client schema without exposing cross-client data. Runbooks for common failure modes: GA4 coverage drop, silhouette gate failure, Redis TTL misconfiguration.

**Interaction Frequency.** Daily during onboarding. Weekly thereafter for monitoring.

**Failure.** Two clients share the same PostgreSQL schema name due to a misconfigured configs/clients/{client}.yaml. Their feature stores are written to the same schema, corrupting both clients' persona assignments.

**Success.** Schema isolation is enforced at the ORM level (`__table_args__` schema parameter) and validated by an integration test that verifies cross-schema access is rejected. No client can read or write to another client's schema.

### 3.13 End Readers (Experience Output, Never Interact Directly)

**Role.** Registered readers of the publisher's platform. They experience the output of the platform — personalised newsletters, reordered homepage modules, calibrated subscription offers — without ever interacting with the AIP directly.

**What They Experience.** Relevant content, fewer irrelevant upsell prompts, newsletter topics that match their demonstrated reading behaviour. A Sports-Focused reader receives the sports newsletter and the Sports+ upsell prompt; they do not receive the celebrity newsletter or the home delivery offer.

**Scale.** 66M registered users at NYPost scale. 500K to 100M depending on publisher size.

**Failure.** An anonymous visitor whose user_pseudo_id was incorrectly resolved to an existing user_id receives a different user's persona label, resulting in Sports-Focused content being served to a Celebrity-Entertainment reader.

**Success.** Personalisation is indistinguishable from the reader's perspective from editorial curation — it simply feels like the platform understands them.

### 3.14 Advertisers (Purchase Segments, Never Interact Directly)

**Role.** Brands and agencies that purchase premium audience inventory. Sports brands, retail brands, lifestyle brands, and financial services brands each target specific personas.

**What They Need.** Verifiable audience segment definitions, reach numbers that are stable week-to-week, and confidence that the persona labels reflect real behavioural distinctions — not editorial labels applied by hand.

**Interaction Frequency.** Campaign planning cycles (monthly) and real-time impression delivery (continuous).

**Failure.** A Sports-Focused audience package is sold to a sports brand at a $22 CPM floor. The next pipeline run switches the algorithm, merging Sports-Focused with Social-Engager into a combined segment with diluted sports intent. The advertiser's brand safety and contextual targeting tools reject the expanded audience definition.

**Success.** Sports-Focused persona definition is stable for ≥ 12 consecutive weeks. CPM premium is maintained because the segment is reproducibly identifiable and verifiably distinct.

---

## SECTION 4: USER PERSONAS (SYSTEM USERS)

This section profiles the human operators of the AIP platform — not the reader personas the ML model discovers.

### 4.1 Data Engineer

**Primary Workflow.** Monday morning: review Sunday's pipeline run log in Airflow UI. Check Grafana for step runtime anomalies, row count deviations, and GA4 coverage metric. If all green, close. If any step flagged: investigate the specific step's structlog output, identify whether the issue is at the source connector, the identity stitcher, or the feature engineering transform. Escalate to ML Engineer if the issue is downstream of Step 4.

**Tools.** Apache Airflow (DAG monitoring), Python (connector maintenance), Grafana (pipeline dashboards), BigQuery console (GA4 source validation), structlog JSON output (step-level debugging), PostgreSQL psql (schema inspection), Docker Compose (local service management).

**Pain Points Solved.** Before AIP: eight disconnected source systems with no common identifier, no validation gates, and no audit trail. After AIP: a single DAG with nine instrumented steps, each logging rows processed, duration, and deviation percentage to MLflow.

**Interaction Frequency.** Daily monitoring. Deep investigation approximately twice per month when a pipeline step deviates. Integration work during new client onboarding (approximately two weeks per new client).

**Good Day.** Pipeline runs Sunday 02:00–05:30 UTC, all nine steps green, Grafana shows silhouette and stability within SLA, no PagerDuty alerts. Data engineer opens the dashboard at 09:00 Monday and closes the tab.

**Bad Day.** GA4 BigQuery export schema changes (Google periodically adds new event parameters). Step 1 (Source Ingestion) processes a partial export, row count deviation is 22% (above the 20% threshold), pipeline aborts. Data engineer must identify the schema change, update the GA4 connector, re-run the DAG manually, and verify the recovered feature store before the business team's Monday 10:00 campaign planning meeting.

### 4.2 ML Engineer / Data Scientist

**Primary Workflow.** Weekly: review MLflow run for the latest pipeline execution — check overall silhouette score, per-cluster silhouette scores, persona stability WoW, and feature importance top-5 per cluster. If all within SLA, document in the weekly model health report. Monthly: review whether the algorithm+K selection is still optimal or whether a Stage 2 re-evaluation is warranted based on accumulated drift signals.

**Tools.** MLflow UI (experiment tracking, artifact inspection, model registry), Jupyter notebooks (ad-hoc cluster profiling), scikit-learn (algorithm evaluation), HDBSCAN library (discovery phase), Python (pipeline development), Grafana (silhouette trend panel), Optuna (K and hyperparameter tuning), pytest (ML pipeline unit and integration tests).

**Pain Points Solved.** Before AIP: no reproducible experiment tracking, algorithm selection was ad-hoc and undocumented, no systematic way to compare BisectingKMeans K=9 against GMM K=8 on the same data. After AIP: every run in MLflow has the algorithm, K, silhouette, per-cluster metrics, feature importance JSON, and scaler artifact — full audit trail.

**Interaction Frequency.** Weekly review of pipeline outputs. Deep algorithm work approximately once per quarter when a new client deployment triggers Stage 1 (HDBSCAN discovery).

**Good Day.** Weekly pipeline produced silhouette=0.42 (above 0.35 target), stability=88% (above 85%), no persona distribution drift above 30% relative. Feature importance top-5 for Cluster 3 shows ratio_sports as rank-1 and nl_sports_alerts as rank-2, confirming Sports-Focused label is well-grounded.

**Bad Day.** Silhouette drops to 0.27 (below the 0.30 safety gate). Pipeline correctly aborts write-back and fires a P1 PagerDuty alert. ML engineer must investigate: is the drop due to a feature drift (Step 4 should have caught this), a data quality issue (new_user rate unexpectedly high), or a genuine shift in audience behaviour that warrants a Stage 2 re-evaluation? Root cause must be documented in MLflow run tags before any manual override.

### 4.3 Backend / API Engineer

**Primary Workflow.** Sprint-based: implement new API features, maintain Redis cache management, add new webhook integrations. Weekly on-call rotation: respond to API uptime alerts, investigate Redis memory spikes, validate that cache TTLs are correct after each pipeline run.

**Tools.** FastAPI, Uvicorn, Redis CLI, Docker Compose, Prometheus (API latency histograms), Grafana (API latency dashboards), pytest (endpoint integration tests), locust (load testing), GitHub Actions (CI/CD pipeline).

**Pain Points Solved.** The cold-start problem — previously any unrecognised user_id returned a 404 or required a database lookup. After AIP: cold_start.py applies rule-based logic in < 1 ms using only the features available at request time (passed by the caller or retrieved from a lightweight profile call).

**Interaction Frequency.** Sprint cadence (2 weeks) for feature work. On-call rotation for production incidents.

**Good Day.** API serves 9,800 requests/second at p99 = 7 ms during the morning ad serving peak. Zero PagerDuty incidents. Load test in CI passes with 10,000 req/s target.

**Bad Day.** Redis runs out of memory at 03:00 UTC during the weekly pipeline cache refresh (Step 9 pushes 95,000 user records into Redis simultaneously). Half the cache is evicted under the maxmemory-policy configuration before Step 9 completes. Users in the evicted half get cold-start responses from 03:00 until 09:00, generating anomalous is_cold_start: true spikes in the API log.

### 4.4 Analytics / BI Engineer

**Primary Workflow.** Weekly: refresh Grafana dashboards for the business stakeholder review. Verify that MLflow API is returning current run data. Check that persona distribution drift panel (F-31) is accurate. Monthly: build cohort analysis queries for the revenue team comparing RPU by persona over a rolling 6-month window.

**Tools.** SQL (PostgreSQL feature store queries), Grafana (dashboard authoring), MLflow API (metric retrieval), Python (ad-hoc analysis), Jupyter notebooks (cohort analysis), dbt (optional transformation layer for BI queries).

**Pain Points Solved.** Before AIP: no consistent definition of a "Sports-Focused" reader across teams — the editorial team used one definition, the newsletter team used another, and the ad team used a third. After AIP: one canonical persona_label per user, updated weekly, accessible via SQL and API.

**Interaction Frequency.** Weekly for dashboard maintenance. Daily for ad-hoc business team requests during campaign season.

**Good Day.** Grafana shows stable personas, silhouette above target, and newsletter CTR lift of 38% for Sports-Focused vs the unsegmented control group. Revenue team has all the numbers they need for the Monday advertiser call.

**Bad Day.** MLflow API returns a 503 error because the MLflow Docker container ran out of disk space storing artifact blobs. Grafana panels that pull from MLflow show stale data from last week. Analytics engineer must manually restart the MLflow container, reclaim disk space, and verify dashboard data freshness before the 10:00 stakeholder meeting.

---
<!-- END_SECTION_4 -->

---

## SECTION 5: FUNCTIONAL REQUIREMENTS

Requirements are numbered F-01 through F-32 using the canonical numbering from spec-source.md v3.0. Each requirement includes: statement, rationale, acceptance criteria, and dependencies.

---

### 5.1 Data Ingestion

**F-01** [v3.0 CORRECTED]
**Requirement.** Ingest delta data from exactly 8 source tables: `zephr_users`, `ga4_events`, `braintree_subscriptions`, `sailthru_newsletter`, `pushly_subscribers`, `openweb_engagement`, `trackonomics_clicks`, `transunion_demographics`. The `feature_store` table is a pipeline output written in Step 8 and is **never** an ETL source input.

**Rationale.** A previous version of the spec incorrectly listed `feature_store` as an input. Any engineer reading the corrected spec must understand that only 8 source tables flow into the pipeline; reading from `feature_store` as input would create a circular dependency.

**Acceptance Criteria.**
- The Airflow Step 1 DAG task connects to exactly 8 source tables.
- No `feature_store` read appears in any `etl/ingestion/` module.
- Each connector logs `rows_ingested`, `start_time`, `end_time`, and `mode` (incremental or full_refresh) to structlog.

**Dependencies.** Phase 2 (database schema DDL) must be merged before Phase 6 (ETL ingestion) begins.

---

**F-02**
**Requirement.** Resolve all source-specific identifiers to the universal `user_id` (UUID) via identity stitching. The resolution map is: GA4 `user_pseudo_id` → `user_id` via login bridge table; Sailthru `email` → `user_id` via `zephr_users.email`; Transunion `hashed_email` → `user_id` via `zephr_users.hashed_email`; Pushly `external_id` = `user_id` (set at push opt-in, direct equality); OpenWeb `user_id` = `user_id` via SSO (direct FK, no resolution required); Trackonomics `user_id` passed as URL parameter (direct FK); Braintree `customer_id` = `user_id` (set programmatically at subscription creation); Zephr `user_id` is the primary key and source of truth.

**Rationale.** Without a universal identifier, features from different sources cannot be joined into a single row per user in the feature store. Unresolved IDs reduce feature coverage and degrade clustering quality.

**Acceptance Criteria.**
- `etl/identity/stitcher.py` implements all 8 resolution paths.
- Unresolved ID rate per source is logged to MLflow after each identity stitching run.
- Integration test verifies resolution succeeds for ≥ 95% of synthetic data users.

**Dependencies.** F-01 (source ingestion must complete before stitching). Bridge table for GA4 `user_pseudo_id` → `user_id` must exist in the database schema (Phase 2).

---

**F-03**
**Requirement.** Validate row counts and schema on every ingestion run. Abort the entire pipeline if any source deviates more than 20% from the prior week's row count for that source. Log the deviation percentage per source to MLflow as a run metric.

**Rationale.** A sudden drop in row counts is the earliest signal of a source system failure (API outage, schema change, access revocation). Aborting early prevents a degraded feature matrix from flowing into clustering. The 20% threshold is configurable in `configs/base.yaml` as `etl.row_count_deviation_threshold`.

**Acceptance Criteria.**
- If any source row count deviates > 20%, the DAG task fails with a descriptive error message naming the source and the deviation percentage.
- MLflow logs `source_name`, `prior_week_rows`, `current_rows`, `deviation_pct` for each source after every run.
- Unit test verifies the abort logic fires correctly at the 20% threshold using mocked row counts.

**Dependencies.** MLflow run must be initialised before Step 1 completes. Prior week's row counts must be persisted between runs (stored as MLflow metrics or in a pipeline audit table).

---

**F-04**
**Requirement.** Support full-refresh and incremental (delta) ingestion modes per source. The mode for each source is configured in `configs/base.yaml` under `etl.sources.{source_name}.mode`. Default modes: `zephr` incremental, `ga4` incremental, `braintree` incremental, `sailthru` full_refresh, `pushly` incremental, `openweb` incremental, `trackonomics` incremental, `transunion` full_refresh.

**Rationale.** Sailthru and Transunion provide aggregate snapshots; their connectors must replace all rows on each run (full_refresh). The remaining six sources provide event-based or state-change data; their connectors must only process new or changed records since the last run (incremental) to stay within the 4-hour batch window.

**Acceptance Criteria.**
- Each connector reads its mode from config and branches accordingly — no hardcoded mode in Python.
- Incremental connectors accept a `since_timestamp` parameter and return only records updated after that timestamp.
- Full-refresh connectors truncate the staging table before inserting the new snapshot.
- Integration test verifies that a second run of a full-refresh connector produces the same row count as the first (idempotent).

**Dependencies.** Phase 2 (DDL with staging table `updated_at` columns). `configs/base.yaml` `etl.sources` section.

---

**F-05**
**Requirement.** Apply a match confidence filter to Transunion demographic data. Exclude records where `match_confidence < 0.70` from the ML feature matrix. Records are stored in `transunion_demographics` and flagged with a `excluded` boolean column. The ETL step logs the match rate and exclusion count.

**Rationale.** Low-confidence Transunion matches introduce demographic noise into the 46-feature matrix. The 0.70 threshold is the minimum confidence Transunion specifies for reliable demographic attribution. This threshold is configurable in `configs/base.yaml` as `etl.transunion_min_confidence`.

**Acceptance Criteria.**
- Records with `match_confidence < 0.70` are stored in `transunion_demographics` with `excluded = TRUE`.
- The feature store write for excluded users sets `age_score`, `income_score`, `has_children` to 0 (null imputation, consistent with F-08).
- ETL logs `transunion_match_rate`, `transunion_excluded_count` per run.

**Dependencies.** F-01 (Transunion ingestion). Phase 2 (transunion_demographics DDL with `match_confidence` and `excluded` columns).

---

### 5.2 Feature Engineering

**F-06**
**Requirement.** Aggregate GA4 event-level rows to one user-level summary row per user. Computed aggregates: `total_sessions`, `total_pageviews`, `active_days`, `avg_session_duration` (seconds), `avg_pages_per_session`, `bounce_rate` (single-page-view sessions with duration < 10 s divided by total sessions), `mobile_ratio` (mobile sessions / total sessions), `desktop_ratio` (desktop sessions / total sessions), `pageviews_per_session` (total_pageviews / total_sessions), `days_since_last_visit` (reference date minus max event_date), and all 8 `ratio_*` content affinity features (pageviews in category / total pageviews for each of: sports, entertainment, celebrity, shopping, opinion, world_news, business, lifestyle).

**Rationale.** GA4 produces event-level rows (150–500 events per user per year at NYPost scale). The clustering algorithm requires one row per user. All session-level signals must be computed at the aggregation step and cannot be recomputed at inference time.

**Acceptance Criteria.**
- `ml/feature_store/builder.py` produces exactly one output row per user_id after GA4 aggregation.
- `bounce_rate` equals zero for users with no single-page sessions under 10 s.
- All 8 `ratio_*` features sum to ≤ 1.0 per user (they may sum to < 1.0 if some pageviews fall in uncategorised pages).
- Unit test verifies all aggregates against a fixture of known GA4 events.

**Dependencies.** F-02 (identity stitching to resolve `user_pseudo_id` → `user_id` before aggregation). Phase 2 (ga4_events DDL).

---

**F-07**
**Requirement.** Apply `log1p` transformation before StandardScaler to the following right-skewed features: `total_sessions`, `total_pageviews`, `total_affiliate_clicks`, `total_comments`. The list of features requiring log1p transformation is stored in `configs/base.yaml` as `ml.features.log1p_features`. `log1p(0) = 0`, so zero-imputed null users are unaffected by this transformation.

**Rationale.** These four features have heavy right tails — a small number of power users with thousands of sessions or pageviews would dominate the Euclidean distances used by K-Means and GMM if not transformed. log1p compresses the tail while preserving the zero value for users who are absent from the source.

**Acceptance Criteria.**
- `ml/feature_store/builder.py` applies `np.log1p()` to the four features listed in config before passing the matrix to StandardScaler.
- The list of log1p features is read from config, never hardcoded.
- Unit test verifies that a user with `total_sessions=0` has `log1p_total_sessions=0.0` in the transformed matrix.

**Dependencies.** F-06 (aggregated feature matrix must exist before transforms are applied).

---

**F-08**
**Requirement.** Apply null imputation: users absent from optional source systems (Pushly: 35% coverage, OpenWeb: 23%, Trackonomics: 16%) receive 0 for all numeric features in that source block. Users absent from Transunion (30% not matched) receive 0 for `age_score`, `income_score`, and `has_children`. Never drop a user from the feature matrix solely because they are missing from one or more optional sources.

**Rationale.** Dropping users with incomplete source coverage would systematically remove low-engagement users (who have no commerce or social signals) from clustering — introducing survivorship bias that would distort all persona proportions. Zero imputation is the correct strategy because it means "no observed activity," which is itself a valid signal.

**Acceptance Criteria.**
- The output feature store contains one row for every user in `zephr_users` (excluding new_users per F-09).
- For any user absent from Pushly, all Pushly-derived features are exactly 0.0 in the feature matrix.
- Integration test verifies that 100K synthetic users produce ~95K feature store rows (5% excluded as new_user).

**Dependencies.** F-02 (identity resolution must complete before null imputation logic can identify which sources a user is absent from).

---

**F-09**
**Requirement.** Exclude new users from clustering. A user is classified as `is_new_user = TRUE` if `total_sessions ≤ 4` AND they have no commerce, social, or subscription data from any source (i.e. `total_affiliate_clicks = 0 AND total_comments = 0 AND has_subscription = FALSE`). New users receive `persona_label = 'new_user'` and skip all clustering steps (Steps 6–8). The session threshold is configurable in `configs/base.yaml` as `etl.new_user_session_threshold` (default: 4).

**Rationale.** Users with ≤ 4 sessions have insufficient behavioural signal for meaningful clustering. Including them would create a degenerate large cluster of low-signal users that would absorb the Low-Engager cluster and reduce silhouette scores. They are handled by the cold-start path (F-25) instead.

**Acceptance Criteria.**
- The feature store upsert sets `is_new_user = TRUE` for users meeting the criteria.
- New users are excluded from the feature matrix passed to the StandardScaler (Step 5).
- New users continue to receive the persona API response `persona_label = 'new_user'` with `is_cold_start = true`.

**Dependencies.** F-06, F-07, F-08 (feature matrix must be fully constructed before new_user flag is evaluated).

---

**F-10**
**Requirement.** Compute the `social_engagement_score` derived feature using the formula: `social_engagement_score = (total_comments × 3) + (total_likes_given × 1) + (total_shares × 2)`. This computation is applied after the source join, before StandardScaler scaling.

**Rationale.** The three raw social signals (comments, likes, shares) have different magnitudes and behavioural significance. Comments require the most intent (composing text), shares have medium intent (one-click), and likes have low intent (passive). The weighted composite creates a single signal that ranks Social Engagers on total community participation.

**Acceptance Criteria.**
- `ml/feature_store/builder.py` computes `social_engagement_score` from the three raw columns before the scaler step.
- A user with `total_comments=10, total_likes_given=5, total_shares=3` produces `social_engagement_score = (10×3)+(5×1)+(3×2) = 41`.
- Unit test verifies the formula against known inputs.

**Dependencies.** F-02 (OpenWeb features must be resolved and joined before this derived feature can be computed).

---

**F-11**
**Requirement.** Compute the `email_engagement_score` ordinal feature using the following threshold encoding: 0 if `open_rate < 0.15` (low engagement), 1 if `0.15 ≤ open_rate ≤ 0.35` (medium engagement), 2 if `open_rate > 0.35` (high engagement). Thresholds are configurable in `configs/base.yaml` as `email_engagement.low_threshold` (0.15) and `email_engagement.high_threshold` (0.35).

**Rationale.** The raw `open_rate` float and the ordinal `email_engagement_score` carry different information. The ordinal encoding maps the continuous signal to a three-level categorical that maps cleanly to the low/medium/high engagement tiers used in downstream campaign logic. Both features are in the ML matrix because they capture different aspects of email behaviour.

**Acceptance Criteria.**
- `email_engagement_score = 0` for all users with `open_rate = 0` (absent from Sailthru, null-imputed to 0).
- Thresholds are read from config, never hardcoded.
- Unit test verifies boundary conditions: open_rate=0.149 → 0, open_rate=0.150 → 1, open_rate=0.351 → 2.

**Dependencies.** F-02 (Sailthru features must be resolved before this derivation).

---

**F-12**
**Requirement.** Expand the `subscribed_newsletters` pipe-delimited text field from Sailthru into individual binary newsletter flag columns. The 6 binary flags that enter the 46-feature ML matrix are: `nl_sports_alerts`, `nl_morning_report`, `nl_page_six_daily`, `nl_celebrity_news`, `nl_evening_update`, `nl_post_opinion`. Additional newsletter flags (nl_breaking_news, nl_real_estate, nl_tech_news, nl_lifestyle_weekly) are stored in the feature store as metadata columns but do not enter the ML matrix. A missing newsletter subscription is encoded as 0.

**Rationale.** The pipe-delimited text field is not a valid ML input. Binary expansion into individual columns enables K-Means and GMM to compute distances on each newsletter subscription independently. The canonical 46-feature list (Fix 3 of spec-source.md) lists exactly 6 nl_* features; additional newsletter flags are stored for completeness but are excluded from clustering to keep the feature matrix at exactly 46 columns.

**Acceptance Criteria.**
- The feature matrix passed to the StandardScaler contains exactly 6 nl_* binary columns, matching `configs/base.yaml ml.features.matrix`.
- A user subscribed to `nl_sports_alerts|nl_morning_report` has `nl_sports_alerts=1`, `nl_morning_report=1`, all other nl_* flags = 0.
- Additional newsletter flags (nl_breaking_news etc.) are present as columns in the feature_store table but are absent from the list in `ml.features.matrix`.

**Dependencies.** F-01 (Sailthru ingestion), F-02 (email → user_id resolution).

---

### 5.3 ML Pipeline

**F-13**
**Requirement.** Implement a 4-stage algorithm evaluation pipeline per client deployment. Stage 1: HDBSCAN discovery — run on the full feature matrix with no K specified, letting the algorithm reveal the natural number of dense groups. Stage 2: BisectingKMeans + GMM evaluated across K = (natural_K ± 3), minimum K=5, maximum K=15. Stage 3: best algorithm+K selected by composite score (silhouette 40% + interpretability 40% + stability 20%). Stage 4: weekly production runs with monitoring.

**Rationale.** A single-algorithm, fixed-K approach locks the platform to assumptions that differ across publishers. A sports-vertical publisher may have K=6 natural clusters; a general-interest publisher may have K=9. The 4-stage pipeline ensures the algorithm and K are data-driven for each client, not arbitrary.

**Acceptance Criteria.**
- `ml/pipelines/clustering_pipeline.py` executes all four stages in order on a new client deployment.
- Stage 3 logs the composite score breakdown (silhouette component, interpretability component, stability component) to MLflow run tags.
- Stage 4 skips Stage 2 if the algorithm+K config is unchanged from the prior week and silhouette has not degraded.

**Dependencies.** F-16 (StandardScaler must be fitted before any clustering algorithm runs). MLflow tracking server must be running (Phase 10).

---

**F-14**
**Requirement.** Compute the composite selection score for algorithm+K evaluation as: `composite = (silhouette_score × 0.40) + (interpretability_score × 0.40) + (stability_score × 0.20)`. Selection weights are stored in `configs/base.yaml` as `ml.clustering.selection_weights`. A cluster passes the interpretability check if it has a distinct nameable behavioural profile, a distinct activation strategy that differs from adjacent clusters, and contains ≥ 0.5% of total users (`ml.clustering.min_cluster_size_pct`).

**Rationale.** Silhouette alone optimises for mathematical cluster separation, which can produce statistically clean but business-meaningless clusters. The 40% interpretability weight forces the selection to favour configurations that produce nameable personas with actionable differences. Stability ensures the selected configuration is not a local optimum that shifts dramatically with different random seeds.

**Acceptance Criteria.**
- `ml/training/evaluation/metrics.py` computes composite score using weights from config.
- Any cluster with < 0.5% of total users fails the interpretability check and the configuration is penalised.
- MLflow logs the composite score and its components (silhouette, interpretability, stability) for every evaluated algorithm+K combination.

**Dependencies.** F-13 (evaluation pipeline must be running). F-32 (feature importance computation used in interpretability scoring).

---

**F-15**
**Requirement.** Support exactly 5 clustering algorithms: `BisectingKMeans` (from `sklearn.cluster`), `KMeans` (from `sklearn.cluster`), `GaussianMixture` (from `sklearn.mixture`), `HDBSCAN` (from the `hdbscan` library), and `Ensemble` (majority vote across KMeans + GMM + HDBSCAN implemented in `ml/training/algorithms/ensemble.py`). Each algorithm is encapsulated in its own module under `ml/training/algorithms/`.

**Rationale.** Different publisher data profiles favour different algorithms. BisectingKMeans is best for large publishers (10M+ users) due to scalability. GMM is best when soft persona scores are required. HDBSCAN is the discovery tool. The Ensemble option is for premium deployments where accuracy outweighs compute cost.

**Acceptance Criteria.**
- Each algorithm module implements a common interface: `fit(X: np.ndarray, k: int) -> ClusterResult` where `ClusterResult` contains `labels`, `centroids` (or component means for GMM, medians for HDBSCAN), and `score`.
- Unit tests for each algorithm verify it produces the correct output shape on a 100×46 synthetic feature matrix.
- The algorithm name string written to `feature_store.algorithm_used` matches the registry key (`kmeans`, `bisecting_kmeans`, `gmm`, `hdbscan`, `ensemble`).

**Dependencies.** F-16 (scaled feature matrix). Phase 9 (ML training phase).

---

**F-16**
**Requirement.** Fit a `StandardScaler` on the 46-feature ML matrix after log1p transformations have been applied (F-07). Persist the fitted scaler as an MLflow artifact named `scaler.pkl` with every run. Inference always loads the training-time scaler — the scaler is never re-fitted on new data mid-pipeline or at inference time.

**Rationale.** StandardScaler normalises feature scales so that high-magnitude features (e.g. `total_pageviews` in the thousands) do not dominate the Euclidean distance calculation relative to low-magnitude features (e.g. `has_subscription` = 0 or 1). The scaler must be fitted once on training data and applied consistently; re-fitting on new data would shift the feature space and make prior cluster centroids invalid.

**Acceptance Criteria.**
- `ml/pipelines/feature_pipeline.py` calls `scaler.fit_transform(X)` exactly once per run.
- The fitted scaler is logged as `mlflow.sklearn.log_model(scaler, artifact_path="scaler.pkl")`.
- Inference code in `ml/inference/predict.py` loads the scaler from the MLflow run ID using `mlflow.sklearn.load_model()`.
- Unit test verifies that fitting on a 100-row matrix and transforming the same matrix produces zero mean and unit variance per feature.

**Dependencies.** F-07 (log1p transforms must precede scaler fit). MLflow tracking (Phase 10).

---

**F-17**
**Requirement.** Write back clustering results to `feature_store` after each successful run using an upsert pattern: `INSERT INTO {schema}.feature_store (...) ON CONFLICT (user_id) DO UPDATE SET persona_label=..., cluster_id=..., algorithm_used=..., cluster_score=..., last_updated=NOW()`. Never truncate and reload. Never append new rows for existing users.

**Rationale.** The upsert pattern ensures that if the silhouette gate (F-20) fires and aborts the write-back, the prior week's assignments remain intact for all users. A truncate-reload pattern would leave users with no persona assignment during the gate-triggered abort.

**Acceptance Criteria.**
- `ml/pipelines/clustering_pipeline.py` uses `INSERT ... ON CONFLICT DO UPDATE` SQL — never `DELETE` followed by `INSERT`.
- A test that runs write-back twice verifies that each user_id has exactly one row after both runs (upsert, not append).
- Write-back is atomic per user_id — partial writes are not possible within a single database transaction.

**Dependencies.** F-13 (clustering must complete before write-back). Phase 2 (feature_store DDL with `user_id` UNIQUE constraint enabling ON CONFLICT).

---

**F-18a** [v3.0 CORRECTED]
**Requirement.** Compute `subscription_propensity_score` per user using the formula:

```
subscription_propensity_score = sigmoid(
    w1 × newsletter_count_scaled
  + w2 × open_rate_scaled
  + w3 × (1 − days_since_last_visit_scaled)
  + w4 × dist_to_subscription_focused_centroid_inverted
)
```

where `sigmoid(x) = 1 / (1 + e^(−x))`, weights are `w1=0.30, w2=0.25, w3=0.25, w4=0.20` (stored in `configs/base.yaml` under `ml.propensity.subscription.weights`), and `dist_to_subscription_focused_centroid_inverted = 1 − normalised_euclidean_distance_to_subscription_focused_centroid`. Output range: 0.0–1.0.

**Rationale.** This score is NOT a supervised model. It is a weighted linear combination of features known to predict subscription intent, passed through a sigmoid to produce a calibrated probability. The centroid distance term captures overall proximity to the Subscription-Focused persona. Weights were calibrated against held-out Braintree conversion labels in offline evaluation.

**Acceptance Criteria.**
- Weights are loaded from config. Zero weights may be hardcoded.
- A user with `newsletter_count_scaled=1.0, open_rate_scaled=1.0, days_since_last_visit_scaled=0.0, dist=0.0` (perfect subscription signal) produces a score close to `sigmoid(0.30 + 0.25 + 0.25 + 0.20) = sigmoid(1.0) ≈ 0.731`.
- Unit test verifies formula against known inputs.
- Score is stored in `feature_store` and returned in the API response.

**Dependencies.** F-16 (scaler produces scaled feature values). F-17 (clustering must produce centroid positions before distance is computable).

---

**F-18b** [v3.0 CORRECTED]
**Requirement.** Compute `churn_propensity_score` per user using the formula:

```
churn_propensity_score = sigmoid(
    w1 × days_since_last_visit_scaled
  + w2 × bounce_rate_scaled
  + w3 × (1 − total_billing_cycles_scaled)
)
```

where weights are `w1=0.40, w2=0.30, w3=0.30` (stored in `configs/base.yaml` under `ml.propensity.churn.weights`). High `days_since_last_visit` and high `bounce_rate` with few `total_billing_cycles` signal imminent churn.

**Rationale.** The three signals are the earliest available churn precursors: recency (days_since_last_visit) captures drift before cancellation; bounce_rate captures content disengagement; total_billing_cycles_inverted captures new subscribers who have not yet committed long-term.

**Acceptance Criteria.**
- Same structural acceptance criteria as F-18a.
- A current subscriber with `days_since_last_visit=0, bounce_rate=0, total_billing_cycles=24` (loyal, engaged, long-tenure) produces a score close to `sigmoid(0 + 0 + 0.30 × 0) = sigmoid(0.0) = 0.50` — neutral, not churning.
- A user with maximum recency, maximum bounce, and zero billing cycles produces a score close to 1.0.

**Dependencies.** F-16, F-17.

---

**F-18c** [v3.0 CORRECTED]
**Requirement.** Compute `commerce_propensity_score` per user using the formula:

```
commerce_propensity_score = sigmoid(
    w1 × ratio_shopping_scaled
  + w2 × total_affiliate_clicks_scaled
  + w3 × dist_to_high_value_shopper_centroid_inverted
)
```

where weights are `w1=0.35, w2=0.30, w3=0.35` (stored in `configs/base.yaml` under `ml.propensity.commerce.weights`). The centroid distance to the High Value Shopper persona is the dominant signal (combined 70% weight with ratio_shopping).

**Rationale.** Commerce propensity requires both behavioural intent (shopping content ratio, affiliate click history) and position relative to the High Value Shopper archetype. Users who read shopping content but have never clicked an affiliate link have different propensity profiles from users who have high click volumes with low conversion rates.

**Acceptance Criteria.**
- Same structural acceptance criteria as F-18a.
- Weights sum to 1.0: `0.35 + 0.30 + 0.35 = 1.00`.
- Score for a user absent from Trackonomics (all commerce features = 0) reflects only the shopping content ratio component.

**Dependencies.** F-16, F-17.

---

**F-19**
**Requirement.** When GaussianMixture is the selected production algorithm, compute `soft_persona_scores`: a 9-element float array where each element is the posterior probability (`predict_proba`) of membership in each cluster. The array must sum to 1.0. Store as a JSON string in `feature_store.soft_persona_scores`. Return in the API response under the `soft_scores` field. For all other algorithms, `soft_scores` is null in the API response.

**Rationale.** Hard cluster assignments lose information for borderline users — a user who is 65% Loyalist and 30% Subscription-Focused has a different activation profile than a pure Loyalist. Soft scores enable nuanced targeting: send the renewal campaign AND the subscription upsell, weighted by persona probability.

**Acceptance Criteria.**
- `GaussianMixture.predict_proba(X_scaled)` output is stored per user as a JSON array `[0.65, 0.0, ..., 0.30, ...]` with exactly 9 elements.
- Array elements sum to 1.0 (±0.001 floating point tolerance).
- API response includes `soft_scores: [float, ...]` when `algorithm_used == 'gmm'` and `soft_scores: null` otherwise.

**Dependencies.** F-15 (GMM algorithm module). F-21 (API schema must include `soft_scores` field).

---

**F-20**
**Requirement.** Apply a silhouette gate after production clustering (Step 7): if the overall silhouette score is < 0.30, do NOT write new persona assignments to the feature store. Retain the prior week's assignments. Send a P1 PagerDuty alert. Log the incident to MLflow with full diagnostics (silhouette value, K, algorithm, prior week value, delta). The 0.30 threshold is configurable in `configs/base.yaml` as `ml.clustering.silhouette_threshold`.

**Rationale.** A silhouette score below 0.30 indicates that cluster boundaries are poorly defined — users are as similar to adjacent clusters as to their own. Writing such assignments would silently degrade downstream campaign quality. Failing safe (retaining prior week) is preferable to silently corrupting the serving layer.

**Acceptance Criteria.**
- `ml/pipelines/clustering_pipeline.py` checks silhouette before calling the write-back module.
- A test simulates a clustering run producing silhouette=0.28 and verifies: feature_store is not modified, PagerDuty alert is triggered, MLflow incident log is created.
- Prior week's `last_updated` timestamp is preserved in feature_store (not overwritten) when gate fires.

**Dependencies.** F-17 (write-back module must be callable but conditionally bypassed). PagerDuty webhook configuration (Phase 14).

---

### 5.4 Propensity Scoring

*(See F-18a, F-18b, F-18c above. This domain introduces no additional F-XX requirements beyond those corrected in v3.0.)*

---

### 5.5 Persona Serving API

**F-21**
**Requirement.** Implement `GET /api/v1/persona/{user_id}`. Returns a JSON object containing: `persona_label` (string, one of 9 labels or a cold-start label), `cluster_id` (integer), `propensity_scores` (object with `subscription`, `churn`, `commerce` float fields), `soft_scores` (9-element float array or null), `algorithm_used` (string), `last_updated` (ISO 8601 timestamp), `is_cold_start` (boolean). All response fields must be validated by a Pydantic v2 model.

**Rationale.** This is the primary API endpoint. Every downstream consumer (newsletter platform, ad server, CMS, subscription engine) calls this endpoint at request time to retrieve persona and propensity data. The response schema must be stable and versioned.

**Acceptance Criteria.**
- Endpoint reads exclusively from Redis cache using `user_id` as key.
- If `user_id` not in Redis, cold-start path (F-25) is invoked and response includes `is_cold_start: true`.
- Response time p99 < 10 ms under 10,000 req/sec load (measured by locust in CI).
- Integration test verifies all response fields are present and type-correct for both cache-hit and cold-start paths.

**Dependencies.** F-25 (cold-start logic). Redis cache (populated by Step 9). Phase 12 (API layer phase).

---

**F-22**
**Requirement.** Implement `GET /api/v1/personas/batch`. Request body: `{"user_ids": [UUID, ...]}` with a maximum of 1,000 user IDs per request (configurable via `api.batch_max_size` in `configs/base.yaml`). Returns a map of `user_id → persona_response` for all requested IDs. Batch reads execute as a single Redis pipeline call (one round-trip to Redis for the entire batch).

**Rationale.** Ad servers and newsletter platforms batch persona lookups to reduce API call overhead. A single Redis pipeline command for 1,000 keys is approximately 100× faster than 1,000 individual GET calls.

**Acceptance Criteria.**
- Batch endpoint uses `redis.pipeline()` to fetch all keys in a single round-trip.
- Returns p99 < 100 ms for a batch of 1,000 user IDs.
- Users not in Redis cache are processed through the cold-start path and included in the batch response with `is_cold_start: true`.
- Requests exceeding 1,000 user IDs return HTTP 422 with a descriptive error.

**Dependencies.** F-21 (single-user persona response schema is reused). F-25 (cold-start path invoked for cache misses within batch).

---

**F-23**
**Requirement.** Implement `GET /api/v1/health`. Returns: `pipeline_last_run` (ISO 8601 timestamp of last successful pipeline run), `silhouette_score` (float from last run), `persona_coverage_pct` (percentage of registered users with an ML persona), `redis_connected` (boolean), `db_connected` (boolean).

**Rationale.** Downstream systems (ad servers, CMS) must be able to verify the health of the persona serving layer without access to internal monitoring systems. The health endpoint also serves as the primary liveness probe for the Docker container.

**Acceptance Criteria.**
- Endpoint reads `pipeline_last_run` and `silhouette_score` from a pipeline metadata table (written by Step 9) or from MLflow.
- Returns HTTP 200 when both Redis and DB are connected, regardless of pipeline run status.
- Returns HTTP 503 if either Redis or DB is unreachable.
- `persona_coverage_pct` is computed from the ratio of users with `is_new_user = FALSE` who have a non-null `persona_label` in the feature store.

**Dependencies.** Phase 2 (pipeline metadata table or MLflow integration for last run data). Phase 12 (API layer phase).

---

**F-24**
**Requirement.** Implement `POST /api/v1/admin/pipeline/trigger`. Requires admin API key authentication (X-API-Key header). Triggers an Airflow DAG run via the Airflow REST API. Returns `dag_run_id` (string) for tracking. The Airflow REST API URL and admin key are configuration values loaded from environment variables, never from YAML files.

**Rationale.** Manual pipeline triggers are needed for: initial client onboarding, investigation of data quality issues, and emergency persona refresh after a source system incident. The Airflow REST API provides a clean separation between the serving API and the orchestration layer.

**Acceptance Criteria.**
- Endpoint is only accessible with a valid admin API key.
- Returns HTTP 202 with `{"dag_run_id": "..."}` on successful Airflow trigger.
- Returns HTTP 401 for missing or invalid API key.
- Returns HTTP 502 if the Airflow REST API is unreachable.
- Integration test mocks the Airflow REST API and verifies the request payload structure.

**Dependencies.** Phase 13 (Airflow DAG must exist). API key middleware (app/core/security.py).

---

**F-25** [v3.0 CORRECTED]
**Requirement.** Implement the cold-start path in `app/utils/cold_start.py`. When a `user_id` is not found in the Redis cache, apply the cold-start rules defined in `configs/base.yaml` under `cold_start.rules` in strict priority order (first match wins):

| Priority | Condition | Assigned persona_label |
|----------|-----------|------------------------|
| 1 | `ratio_sports > 0.50` | `sports_cold_start` |
| 2 | `(ratio_celebrity + ratio_entertainment) > 0.50` | `celebrity_cold_start` |
| 3 | `has_subscription == True` | `subscription_cold_start` |
| 4 | `newsletter_count > 0` | `newsletter_cold_start` |
| 5 | (default) | `new_user` |

The API response for cold-start users always includes `is_cold_start: true`. Never return HTTP 404 for a valid `user_id`.

**Rationale.** Users with 2–4 sessions have insufficient data for ML clustering but enough data for rule-based segmentation. Without a cold-start path, these users would receive no personalisation and ad servers would get 404 errors, breaking impression pipelines.

**Acceptance Criteria.**
- Rules are loaded from config at startup — no rule conditions are hardcoded in Python.
- A user with `ratio_sports=0.55` receives `sports_cold_start` even if `has_subscription=True` (priority 1 wins over priority 3).
- Unit tests verify all 5 rule branches, including the default case.
- A valid user_id that is not in Redis and has no available feature data returns `new_user` (the default rule) — never a 404.

**Dependencies.** F-21 (cold-start response uses the same Pydantic schema). `configs/base.yaml` cold_start.rules section.

---

### 5.6 Experiment Tracking

**F-26** [renumbered from original monitoring block; distinct from F-26 below — see note]

> **Note:** The original spec-source.md uses F-26 through F-32 for monitoring requirements. This document preserves that numbering and places experiment tracking requirements here as design context rather than separate F-XX codes, consistent with the source document.

MLflow must log the following per pipeline run: algorithm name and version, K value, overall silhouette score, per-cluster silhouette scores (as a JSON artifact), persona distribution (as a JSON artifact), feature importance top-5 per cluster (as a JSON artifact, per F-32), scaler as a binary artifact (`scaler.pkl`), inertia curve across K=5 to K=15 (as a JSON artifact), trigger source (manual or scheduled), rationale for algorithm+K selection (as MLflow run tags).

The MLflow model registry must store at least the last 4 production runs for rollback capability. Rollback procedure: load the prior week's `scaler.pkl` and centroid artifact, re-run the write-back step with prior week's assignments.

---

### 5.7 Pipeline Orchestration

**F-27** (Airflow DAG 9-step specification)

The Airflow DAG `audience_intelligence_dag` must implement exactly the following 9 sequential steps with the specified fail behaviours:

| Step | Name | Description | Fail Behaviour |
|------|------|-------------|---------------|
| 1 | Source Ingestion | Pull delta data from all 8 sources; validate row counts ±20% | Abort pipeline; fire P2 alert |
| 2 | Identity Stitching | Resolve all source IDs to user_id; log unresolved rates | Continue with resolved users; log unresolved rate |
| 3 | Feature Engineering | Aggregate GA4 to user level; compute ratio_*, bounce_rate, log1p transforms, derived features | Abort if feature matrix row count < 80% of prior week |
| 4 | Feature Validation | Check feature distributions for drift; flag if > 20% mean shift on any feature; abort if > 3 features drift simultaneously | Abort pipeline; use prior week; P1 alert |
| 5 | StandardScaler Fit | Fit scaler on ML feature matrix; save to MLflow; apply log1p (already done in Step 3) | Abort if scaler fit fails (data shape mismatch) |
| 6 | Algorithm Evaluation | Run BisectingKMeans + GMM for K=5 to K=15; compute silhouette + interpretability; select best config; skip if same config as prior week | Use prior week's config if evaluation fails |
| 7 | Production Clustering | Run selected algorithm at chosen K; compute silhouette; if < 0.30, abort write-back | Abort write-back; keep prior week; P1 alert |
| 8 | Write-Back | Upsert persona_label, cluster_id, algorithm_used, cluster_score, last_updated; log persona distribution (F-31); log feature importance (F-32) | Abort and alert; do not partial-write |
| 9 | Cache Refresh + Notify | Push updated records to Redis (TTL=7d); fire webhooks to Sailthru, ad server, CMS | Continue even if webhook fails; log failure |

**Dependencies.** Phase 13 (Airflow DAG phase). All ML pipeline modules (Phases 9–11).

---

### 5.8 Monitoring and Alerting

**F-26** (Silhouette monitoring)
**Requirement.** Log the weekly overall silhouette score to Grafana. Fire a PagerDuty P2 alert if the silhouette score drops more than 0.05 compared to the prior week's score. The alert threshold is configurable in `configs/base.yaml` as `ml.clustering.silhouette_alert_delta`.

**F-27** (Persona stability monitoring)
**Requirement.** Track persona stability (percentage of users with the same persona label as the prior week). If stability falls below 80% (`ml.clustering.stability_threshold`) for 3 consecutive weeks, automatically trigger a Stage 2 algorithm re-evaluation.

**F-28** (Feature coverage monitoring)
**Requirement.** Track feature coverage (percentage of users with data from each source system) daily. Fire a PagerDuty P1 alert if GA4 coverage falls below 90% (`monitoring.ga4_coverage_alert_threshold`). Fire a PagerDuty P2 alert if Transunion coverage falls below 60% (`monitoring.transunion_coverage_alert_threshold`).

**F-29** (Pipeline runtime monitoring)
**Requirement.** Track pipeline step runtime per execution. Fire a PagerDuty P2 alert if any step runtime exceeds 2× its rolling median runtime over the last 4 runs (`monitoring.pipeline_runtime_multiplier`).

**F-30** (MLflow run completeness)
**Requirement.** Each MLflow run must log: algorithm used, K selected, overall silhouette score, per-cluster silhouette scores, persona distribution (% per persona), feature importance top-5 per cluster, scaler artifact, inertia curve across K=5 to K=15.

**F-31** [v3.0 NEW]
**Requirement.** Log weekly persona distribution (percentage of users per persona) to MLflow as a JSON artifact and surface in Grafana as a stacked-bar trend chart. Fire a PagerDuty P2 alert if any persona changes by more than 30% relative week-over-week. Formula: `abs(this_week_pct − last_week_pct) / last_week_pct > 0.30`. The Low Engager persona is exempt from this alert due to its naturally high variance. The drift threshold is configurable per client in `configs/clients/{client}.yaml` under `monitoring.persona_distribution_drift_threshold`.

**Acceptance Criteria.**
- Distribution dict computed in Step 8 after write-back; logged via `mlflow_logger.log_persona_distribution()`.
- PagerDuty alert includes: persona name, current %, prior week %, relative change %, Grafana panel link.
- False positive mitigation: Low Engager exempted; threshold configurable per client.

**F-32** [v3.0 NEW]
**Requirement.** After each clustering run, compute per-cluster feature importance using the formula: `importance[cluster][feature] = abs(centroid[cluster][feature] − global_mean[feature]) / global_std[feature]`. Log the top-5 features per cluster to MLflow as a JSON artifact in the format `{cluster_id: [[feature_name, importance_score], ...]}`. Write the JSON string to `feature_store.cluster_top_features` for API access.

For algorithm variants: K-Means/BisectingKMeans use cluster centroids directly; GMM uses component means; HDBSCAN uses per-cluster feature medians (no centroids in HDBSCAN).

**Acceptance Criteria.**
- Implemented in `ml/training/evaluation/interpretability.py` as `compute_feature_importance(centroids, feature_names, global_stats) → dict`.
- Top-5 features per cluster logged to MLflow after every production run.
- Grafana dashboard panel shows the top-5 feature bars per persona.
- The persona naming logic in `interpretability.py` uses the top-5 feature list and the `personas.naming_rules` lookup table in `configs/base.yaml` to assign the human-readable label.

---

### 5.9 Multi-Tenancy

**F-33** [ARCHITECTURAL DECISION — extends spec-source.md requirements]
**Requirement.** Implement schema-per-client isolation. Every SQL DDL file must use the `{schema}` placeholder in all table references. Every SQLAlchemy ORM model must include `__table_args__ = {"schema": settings.database.schema}`. Client schema name is set in `configs/clients/{client}.yaml` under `database.schema`. The development default schema is `"public"` (set in `configs/base.yaml`).

**Acceptance Criteria.**
- `grep -r "CREATE TABLE" sql/ddl/` produces only lines containing `{schema}`.
- Integration test verifies that a session configured for schema `client_a` cannot query tables in schema `client_b`.
- CI grep check fails the build if any ORM model lacks `__table_args__`.

**Dependencies.** Phase 2 (database schema DDL).

---

### 5.10 Cold-Start Handling

*(Covered in F-25 above. Session threshold details: 0–1 sessions → new_user (no rules applied); 2–4 sessions → rule-based cold-start; 5–9 sessions → included in next weekly batch run, ML persona assigned within 3–10 days; 10+ sessions → stable ML persona, full propensity scores.)*

<!-- END_SECTION_5 -->

---

## SECTION 6: NON-FUNCTIONAL REQUIREMENTS

Each NFR specifies: requirement, measurement method, target, failure threshold.

### NFR-01: Latency

**Requirement.** The `GET /api/v1/persona/{user_id}` endpoint must respond within 10 ms at the 99th percentile. The `GET /api/v1/personas/batch` endpoint (1,000 user IDs) must respond within 100 ms at the 99th percentile.

**Measurement Method.** Prometheus histogram `http_request_duration_seconds` with quantile labels, scraped by Grafana. Load testing via locust in CI on every PR to main.

**Target.** p99 < 10 ms (single), p99 < 100 ms (batch 1,000).

**Failure Threshold.** p99 > 15 ms sustained for 5 minutes triggers a PagerDuty P2 alert. p99 > 50 ms triggers P1 (SLA breach). Root cause is typically Redis connection pool exhaustion or a cold-start path computation bottleneck.

---

### NFR-02: Throughput

**Requirement.** The persona serving API must handle 10,000 requests per second at peak ad serving load without latency degradation.

**Measurement Method.** locust load test in CI: `--users 10000 --spawn-rate 500 --run-time 60s` targeting the single-user endpoint. Pass condition: p99 < 10 ms throughout the 60-second window.

**Target.** 10,000 req/sec.

**Failure Threshold.** If throughput falls below 8,000 req/sec before p99 degrades, the Redis connection pool (`redis.max_connections` in base.yaml, default 50) should be increased. If Redis is the bottleneck, Redis Cluster deployment is the scaling path.

---

### NFR-03: Availability

**Requirement.** The persona serving API must maintain 99.9% uptime (≤ 8.77 hours downtime per year). Planned maintenance is acceptable only within the weekly batch window (Sunday 02:00–06:00 UTC).

**Measurement Method.** Uptime Robot external health checks against `GET /api/v1/health` every 60 seconds.

**Target.** 99.9% uptime.

**Failure Threshold.** Any unplanned outage > 30 minutes is a P1 incident. The serving API is not on the pipeline critical path — a pipeline failure must never take down the API. Redis TTL of 7 days ensures the cache remains populated even if the pipeline misses one weekly run.

---

### NFR-04: Scalability

**Requirement.** Feature engineering must support 1M to 100M users via a backend swap driven by a single config flag. The `feature_engineering.backend` value in `configs/base.yaml` selects the implementation: `"pandas"` (dev, < 1M users), `"dask"` (mid, 1M–10M users), `"pyspark"` (large, 10M+ users). The interface presented to `ml/feature_store/builder.py` must be identical regardless of backend.

**Measurement Method.** Integration test verifies that the same input dataset produces identical output when processed by the pandas and dask backends.

**Target.** Same logical output from all three backends. Backend switch requires zero Python code changes.

**Failure Threshold.** If Step 3 (Feature Engineering) exceeds 30 minutes consistently for 3 consecutive weeks on the current backend, the backend should be upgraded to the next tier.

---

### NFR-05: Security

**Requirement.** (a) PII fields (`first_name`, `last_name`, `email`, `address_state`, `address_zip`) must be masked in analytics environments; they must never appear in API responses or MLflow artifacts. (b) `hashed_email` must never be exposed via any API endpoint. (c) All API endpoints require an `X-API-Key` header; admin endpoints require an admin-tier API key. (d) API keys are rotated quarterly. (e) A CI step runs an automated PII scan on all staged files to prevent accidental PII exposure.

**Measurement Method.** Automated PII scan in CI (grep for email patterns and known PII field names in MLflow artifact JSON). API key middleware unit test verifies 401 responses for missing/invalid keys.

**Target.** Zero PII fields exposed in any API response or MLflow artifact. 100% of API calls require a valid key.

**Failure Threshold.** Any PII field appearing in an API response or MLflow artifact is a P0 security incident requiring immediate rollback.

---

### NFR-06: Reproducibility

**Requirement.** All ML pipeline runs must be fully reproducible: given the same input data, the same `configs/base.yaml` settings, and the same MLflow run ID (for scaler and centroid artifacts), the output persona assignments must be identical. `random_state=42` is set everywhere (configurable in `configs/base.yaml` as `ml.clustering.random_state`). The K selection rationale must be documented in MLflow run tags.

**Measurement Method.** MLflow run comparison: run the pipeline twice on the same synthetic dataset snapshot, compare `feature_store.persona_label` assignments. Expect 100% agreement.

**Target.** 100% assignment agreement on identical inputs.

**Failure Threshold.** Any non-determinism in the pipeline (beyond HDBSCAN, which is inherently non-deterministic) indicates a bug. HDBSCAN results are validated by checking that cluster counts agree within ±1 across three seeds.

---

### NFR-07: Multi-Tenancy

**Requirement.** Each client deployment must have complete PostgreSQL schema isolation. No ORM query in any client's session must be able to read or write to another client's schema. The `__table_args__ = {"schema": settings.database.schema}` pattern enforced in every ORM model is the implementation mechanism.

**Measurement Method.** Integration test: create two client sessions (`client_a` and `client_b`), write a user to `client_a.feature_store`, verify that a `client_b` session query for the same user_id returns no results.

**Target.** Zero cross-client data access. Verified by integration test on every CI run.

**Failure Threshold.** Any cross-client data access detected in testing is a P0 security defect that blocks the release.

---

### NFR-08: Auditability

**Requirement.** Every clustering run must log to MLflow: trigger source (manual or scheduled), algorithm selected and rationale, silhouette score, delta vs prior week, persona distribution, feature importance per cluster. The MLflow audit trail must be queryable and must retain at least 12 months of run history.

**Measurement Method.** MLflow UI run comparison. Integration test verifies all required run tags and metrics are present after each pipeline execution.

**Target.** 100% of production runs have complete MLflow audit records.

**Failure Threshold.** Any run missing a required metric or artifact is flagged in the post-run validation step. Pipeline is not considered complete until MLflow logging succeeds.

---

### NFR-09: Testability

**Requirement.** Test coverage must be ≥ 80% on ETL, feature engineering, and API code. All ML pipeline steps must have integration tests that run against the synthetic dataset. Unit tests must not require a live database or Redis connection (use mocks). Integration tests run against Docker Compose services.

**Measurement Method.** `pytest-cov` report in CI. Coverage gate: fail the build if coverage drops below 80% on any of the three code areas (ETL, feature engineering, API).

**Target.** ≥ 80% coverage on ETL, feature engineering, and API modules. 100% of Airflow DAG steps covered by at least one integration test.

**Failure Threshold.** PR blocked by CI if coverage falls below 80%.

---

### NFR-10: Config-Driven

**Requirement.** No tunable parameter (K range, algorithm choice, feature list, threshold, weight) may be hardcoded in Python. All parameters must be read from `configs/base.yaml` (or client-level overrides) via the `settings` object. A CI grep check enforces this: the build fails if any Python file outside of config loading code contains numeric literals that match known configurable values (e.g. `0.30`, `0.40`, `42`, `1000`).

**Measurement Method.** CI grep check: `grep -r "silhouette.*0\.30\|k_max.*15\|random_state.*42" app/ ml/ etl/` — any match fails the build. The grep pattern set is maintained in the CI configuration.

**Target.** Zero hardcoded configurable values in production code.

**Failure Threshold.** Any CI grep match is a blocking build failure.

---

## SECTION 7: ML SYSTEM REQUIREMENTS

### 7.1 Problem Framing

The Audience Intelligence Platform solves an **unsupervised clustering** problem. No ground-truth persona labels exist for training. The algorithm discovers natural behavioural segments from the 46-feature matrix. Quality is measured by mathematical cluster separation (silhouette score), cluster interpretability (feature importance + naming logic), and week-over-week assignment stability. There is no train/test split. There is no supervised loss function. The propensity scores are derived formulas (centroid distances + scaled features through sigmoid), not separate supervised classifiers.

This framing has two important consequences. First, the model cannot overfit in the traditional sense; the risk is instead that it over-segments (too many small, similar clusters) or under-segments (too few large, diffuse clusters). The composite selection score (silhouette + interpretability + stability) is designed to balance these failure modes. Second, the absence of ground-truth labels means validation requires domain expertise — the ML engineer and editorial team must jointly verify that cluster 3's top features (ratio_sports, nl_sports_alerts) justify the "Sports-Focused" label.

---

### 7.2 Feature Requirements — All 46 Features

The canonical ML feature matrix contains exactly 46 numeric columns. This list is the single source of truth, cross-validated against `configs/base.yaml ml.features.matrix`.

| # | Feature Name | Source System | Data Type | Transformation | Null Handling |
|---|-------------|--------------|-----------|---------------|--------------|
| 1 | total_sessions | GA4 | INTEGER | log1p | 0 if absent from GA4 |
| 2 | total_pageviews | GA4 | INTEGER | log1p | 0 |
| 3 | active_days | GA4 | INTEGER | none | 0 |
| 4 | avg_session_duration | GA4 | FLOAT | none | 0 |
| 5 | avg_pages_per_session | GA4 | FLOAT | none | 0 |
| 6 | bounce_rate | GA4 | FLOAT (0–1) | none | 0 |
| 7 | mobile_ratio | GA4 | FLOAT (0–1) | none | 0 |
| 8 | desktop_ratio | GA4 | FLOAT (0–1) | none | 0 |
| 9 | pageviews_per_session | GA4 | FLOAT | derived (total_pageviews/total_sessions) | 0 |
| 10 | days_since_last_visit | GA4 | INTEGER | none | 0 |
| 11 | account_age_days | Zephr | INTEGER | none | required (never null) |
| 12 | ratio_sports | GA4 | FLOAT (0–1) | none | 0 |
| 13 | ratio_entertainment | GA4 | FLOAT (0–1) | none | 0 |
| 14 | ratio_celebrity | GA4 | FLOAT (0–1) | none | 0 |
| 15 | ratio_shopping | GA4 | FLOAT (0–1) | none | 0 |
| 16 | ratio_opinion | GA4 | FLOAT (0–1) | none | 0 |
| 17 | ratio_world_news | GA4 | FLOAT (0–1) | none | 0 |
| 18 | ratio_business | GA4 | FLOAT (0–1) | none | 0 |
| 19 | ratio_lifestyle | GA4 | FLOAT (0–1) | none | 0 |
| 20 | has_subscription | Braintree+Zephr | BINARY (0/1) | none | 0 |
| 21 | subscription_amount | Braintree | FLOAT | none | 0 |
| 22 | total_billing_cycles | Braintree | INTEGER | none | 0 |
| 23 | days_until_renewal | Braintree | INTEGER | none | 0 |
| 24 | newsletter_count | Sailthru | SMALLINT | none | 0 |
| 25 | open_rate | Sailthru | FLOAT (0–1) | none | 0 |
| 26 | click_through_rate | Sailthru | FLOAT (0–1) | none | 0 |
| 27 | email_engagement_score | Sailthru | SMALLINT (0/1/2) | derived (ordinal encoding of open_rate) | 0 |
| 28 | nl_sports_alerts | Sailthru | BINARY (0/1) | derived (binary flag from subscribed_newsletters) | 0 |
| 29 | nl_morning_report | Sailthru | BINARY (0/1) | derived | 0 |
| 30 | nl_page_six_daily | Sailthru | BINARY (0/1) | derived | 0 |
| 31 | nl_celebrity_news | Sailthru | BINARY (0/1) | derived | 0 |
| 32 | nl_evening_update | Sailthru | BINARY (0/1) | derived | 0 |
| 33 | nl_post_opinion | Sailthru | BINARY (0/1) | derived | 0 |
| 34 | total_comments | OpenWeb | INTEGER | log1p | 0 if absent from OpenWeb (23% coverage) |
| 35 | total_likes_given | OpenWeb | INTEGER | none | 0 |
| 36 | total_shares | OpenWeb | INTEGER | none | 0 |
| 37 | social_engagement_score | OpenWeb | INTEGER | derived: (comments×3)+(likes×1)+(shares×2) | 0 |
| 38 | total_affiliate_clicks | Trackonomics | INTEGER | log1p | 0 if absent from Trackonomics (16% coverage) |
| 39 | total_transactions | Trackonomics | INTEGER | none | 0 |
| 40 | total_revenue_generated | Trackonomics | FLOAT | none | 0 |
| 41 | conversion_rate | Trackonomics | FLOAT (0–1) | none | 0 |
| 42 | avg_transaction_value | Trackonomics | FLOAT | none | 0 |
| 43 | unique_advertisers_clicked | Trackonomics | INTEGER | none | 0 |
| 44 | age_score | Transunion | SMALLINT (1–6) | derived (ordinal encoding of age_range) | 0 if excluded (match_confidence < 0.70) |
| 45 | income_score | Transunion | SMALLINT (1–6) | derived (ordinal encoding of income_range) | 0 |
| 46 | has_children | Transunion | BINARY (0/1) | none | 0 |

**Columns excluded from the ML matrix** (stored in feature_store but not fed to clustering): `user_id`, `email`, `persona_label`, `cluster_id`, `algorithm_used`, `cluster_score`, `last_updated`, `subscription_plan`, `push_opted_in`, `push_is_active`, `push_platform_*`, `soft_persona_scores`, `cluster_top_features`, `is_new_user`.

---

### 7.3 Algorithm Requirements

All five algorithms are implemented under `ml/training/algorithms/`. Each implements the common interface described in F-15.

| Algorithm | Mechanism | Strengths | Weaknesses | Primary Use Case |
|-----------|-----------|-----------|-----------|-----------------|
| BisectingKMeans | Recursively divides the largest cluster until K is reached | Fast and scalable to 100M+ users; deterministic; well-separated compact clusters | Assumes spherical clusters; sensitive to outliers; requires K pre-specification | Large publishers (10M+ users) needing fast reproducible weekly runs |
| KMeans | Iteratively assigns points to nearest centroid until convergence | Well-understood; good interpretability; works well with balanced cluster sizes | Same spherical assumption; local minima risk (mitigated by `n_init=3`) | Mid-size publishers (1M–10M) with roughly balanced persona distributions |
| GaussianMixture | Probabilistic soft-membership assignments | Handles elliptical clusters; produces confidence scores natively; captures overlapping personas | Slower; sensitive to initialisation; risk of degenerate solutions without regularisation | Publishers wanting soft persona scores for nuanced targeting |
| HDBSCAN | Density-based hierarchical clustering; finds dense regions as clusters | Does not require K pre-specification; handles non-spherical clusters; identifies outliers as noise | Non-deterministic; slower at very large scale; Low Engagers may be classified as noise | Stage 1 (discovery): reveals natural K before running parametric algorithms |
| Ensemble | Majority vote across KMeans + GMM + HDBSCAN | Most robust; reduces variance from any single algorithm's weaknesses; confidence = fraction of agreeing algorithms | 3× compute cost; highest pipeline complexity | Premium client deployments where accuracy outweighs speed |

---

### 7.4 Evaluation Requirements

**Silhouette Score.** Target: overall > 0.35; per-cluster > 0.25. Alert: P2 if overall drops > 0.05 vs prior week. Safety gate: abort write-back if overall < 0.30. Computed using `sklearn.metrics.silhouette_score` with `sample_size=50000` for speed on large datasets.

**Davies-Bouldin Index.** Lower is better (0 is perfect). Logged to MLflow per run as a secondary quality metric. No automated alert threshold; used for comparative analysis across K values during Stage 2 evaluation.

**Inertia (Elbow Method).** Logged for K=5 to K=15 as a JSON array to MLflow. The elbow point confirms the composite-score selection. Inertia alone is insufficient for K selection — it always decreases with increasing K.

**Business Interpretability Score.** A cluster earns an interpretability score of 1.0 if it meets all three criteria: (a) it has a distinct, nameable behavioural profile identified by the `personas.naming_rules` lookup in `configs/base.yaml`; (b) it has a distinct activation strategy that differs from the nearest adjacent cluster; (c) it contains ≥ 0.5% of total users. Clusters failing any criterion score 0. The interpretability score per configuration is the fraction of clusters that pass all three criteria.

**Persona Stability.** Target: > 85% of users retain the same persona label week-over-week. Trigger Stage 2 re-evaluation if stability < 80% for 3 consecutive weeks.

---

### 7.5 Propensity Score Requirements

All three propensity scores use `sigmoid(x) = 1 / (1 + e^(−x))` to produce outputs in the range 0.0–1.0. Centroid distances are Euclidean distances in the scaled feature space, normalised to [0, 1] by dividing by the maximum observed distance, then inverted (`1 − normalised_distance`) so proximity to the target persona centroid = high score.

**Critical constraint:** These are NOT supervised models. No labelled training data is used. No train/test split exists. The scores are deterministic formulas applied to scaled features and centroid positions. This means they cannot be evaluated with classification metrics (AUC, precision, recall) — they are validated by comparing high-scoring user cohorts against Braintree conversion event rates in offline evaluation.

All weights are stored in `configs/base.yaml` under `ml.propensity.{type}.weights` and may be overridden per client in `configs/clients/{client}.yaml`. No weight values are hardcoded in Python.

---

### 7.6 Model Governance

Every production clustering run is tracked in MLflow with a unique `run_id`. The MLflow model registry retains at least the last 4 production runs. Rollback procedure: if the current week's silhouette score falls below 0.30 (safety gate fires), the prior week's `run_id` is retrieved from MLflow, its `scaler.pkl` and centroid artifact are loaded, and the write-back step is executed with the prior week's assignments. This rollback is automated within the Airflow DAG (Step 7 fail behaviour).

Algorithm selection is re-triggered (Stage 2 re-evaluation) when any of the following conditions are met:
- Overall silhouette drops > 0.05 vs prior week (F-26).
- Persona stability < 80% for 3 consecutive weeks (F-27).
- Persona distribution drift > 30% relative for any non-Low-Engager persona (F-31).

---

### 7.7 Retraining Schedule and Drift Triggers

**Scheduled retraining:** The production clustering run (Stage 4) executes weekly on Sunday at 02:00 UTC, orchestrated by the Airflow DAG. The feature store is rebuilt from fresh source ingestion on the same schedule.

**Drift triggers:** Algorithm+K re-evaluation (Stage 2) is triggered automatically when the conditions in Section 7.6 are met. Manual trigger is available via `POST /api/v1/admin/pipeline/trigger` (F-24).

**Cold-start re-evaluation:** New users are evaluated in each weekly batch run. Users who cross the `min_sessions_for_ml=5` threshold are picked up in the next scheduled run (no real-time re-evaluation).

---

### 7.8 Synthetic Data Strategy

**Persona injection.** Every synthetic user is pre-assigned a ground-truth persona label during generation in `scripts/generate_synthetic_data.py`. Feature distributions are drawn from persona-specific parameter sets (e.g. Loyalists: `total_sessions ~ Normal(150, 30)`, Low Engagers: `total_sessions ~ Normal(3, 1.5)`). This enables validation that the unsupervised pipeline recovers a cluster distribution close to the injected distribution.

**Class imbalance.** Persona proportions mirror documented real-world distributions:

| Persona | Approx % of Total Users | Approx Count (100K synthetic) |
|---------|------------------------|-------------------------------|
| low_engager | 50.6% | 50,600 |
| casual_reader | 15.4% | 15,400 |
| sports_focused | 10.1% | 10,100 |
| celebrity_entertainment | 9.7% | 9,700 |
| social_engager | 7.7% | 7,700 |
| subscription_focused | 2.8% | 2,800 |
| occasional_buyer | 2.9% | 2,900 |
| loyalist | 1.1% | 1,100 |
| high_value_shopper | 0.6% | 600 |

**Coverage gaps.** Pushly 35%, OpenWeb 23%, Trackonomics 16%, Transunion 70% match rate. Users absent from a source receive NULL in the raw staging table and 0 in the feature matrix after imputation.

**Outliers.** 1–2% of users are anomalous: bot-like users (thousands of sessions in short windows), power users (top 0.01% pageviews), payment failures. These test pipeline robustness without breaking the clustering quality gates.

**Referential integrity.** All foreign keys resolve. Every user_id in child tables exists in `zephr_users`. No orphan records. Identity stitching succeeds on ≥ 95% of synthetic records.

<!-- END_SECTION_7 -->

---

## SECTION 8: DATA REQUIREMENTS

### 8.1 Source System Inventory

| Source Table | Rows/Year per 1M Registered Users | Refresh Pattern | Join Key to user_id | Coverage |
|-------------|----------------------------------|-----------------|-------------------|---------|
| zephr_users | 1M (1 row per user) | Registration write + incremental state updates | user_id (PK — this IS user_id) | 100% |
| ga4_events | 200M–500M (200–500 events/user/year) | Daily BigQuery export, partitioned by event_date | user_pseudo_id → user_id via login bridge table | ~60% (anonymous visitors never resolve) |
| braintree_subscriptions | 50K–150K (5–15% subscription rate) | Event-driven on state change | customer_id = user_id (set at subscription creation) | ~10% |
| sailthru_newsletter | 1M (1 aggregate row per user) | Weekly full-refresh or daily delta | email → user_id via zephr_users.email | ~100% of registered emails |
| pushly_subscribers | 300K–400K (30–40% opt-in rate) | Daily delta sync | external_id = user_id (set at push opt-in) | ~35% |
| openweb_engagement | 200K–250K (20–25% of users) | Daily delta sync | user_id via SSO token (direct FK, no resolution) | ~23% |
| trackonomics_clicks | 5M–15M (multiple clicks per commerce user) | Daily SFTP export | user_id passed as URL parameter | ~16% user coverage |
| transunion_demographics | 700K (70% match rate) | Monthly batch refresh | hashed_email → user_id via zephr_users.hashed_email | ~70% match rate; exclude < 0.70 confidence |

---

### 8.2 Identity Resolution

Each source system uses a different identifier that must be resolved to the universal `user_id` (UUID) issued by Zephr at registration.

| Source | Resolution Method | Confidence |
|--------|------------------|-----------|
| Zephr | `user_id` is the primary key — no resolution needed | 100% |
| GA4 | `user_pseudo_id` → `user_id` via login bridge table (populated when user logs in to GA4-tracked session) | ~60% of total sessions (anonymous sessions never resolve; anonymous users are excluded from clustering) |
| Braintree | `customer_id` = `user_id` set programmatically at subscription creation from Zephr flow | 100% of subscriptions |
| Sailthru | `email` → `user_id` via `zephr_users.email` exact lowercase match | ~100% of newsletter records |
| Pushly | `external_id` = `user_id` set at push opt-in time | 100% of push records |
| OpenWeb | `user_id` direct FK via SSO token — most reliable, no resolution step required | 100% of OpenWeb records |
| Trackonomics | `user_id` passed as URL parameter in affiliate links; NULL for anonymous clicks | 100% of attributed clicks; anonymous clicks excluded |
| Transunion | `hashed_email` (SHA-256) batch-matched to Transunion TruAudience API | ~70% match rate; records below 0.70 confidence excluded |

The identity stitching step (`etl/identity/stitcher.py`) logs the unresolved rate per source to MLflow after each run. Unresolved records are stored in their source staging table but are excluded from the feature matrix join.

---

### 8.3 Data Quality Requirements

**Null imputation.** Users absent from any optional source (Pushly, OpenWeb, Trackonomics, Transunion) receive 0 for all numeric features from that source block. This is the authoritative null strategy — no mean imputation, no median imputation, no row deletion. Zero is semantically meaningful: it represents absence of observed activity.

**Outlier handling.** 1–2% of anomalous users (bot-like session volumes, extreme pageview counts, payment edge cases) are retained in the dataset and used to test pipeline robustness. They are not filtered before clustering; if they form a distinct cluster, that cluster will fail the minimum-size interpretability check (< 0.5% of users) and be merged back.

**Feature drift validation.** Step 4 (Feature Validation) checks each feature's mean value against the prior week. If any feature shifts by more than 20% relative (`monitoring.feature_drift_threshold`), it is flagged. If more than 3 features drift simultaneously (`monitoring.max_drifting_features`), the pipeline aborts and a P1 alert fires, because simultaneous multi-feature drift indicates a source system failure rather than genuine audience behaviour change.

**Row count validation.** Each source is validated against the prior week's row count with a ±20% tolerance (`etl.row_count_deviation_threshold`). Deviations above this threshold indicate source system failures (API outage, schema change, access revocation) and cause pipeline abort at Step 1.

---

### 8.4 Feature Store Design

The `feature_store` table is the single ML-ready output table of the pipeline. It contains one row per registered user. Structure:

- **46 ML feature columns** (the feature matrix described in Section 7.2)
- **5 ML output columns** (written back after clustering): `persona_label`, `cluster_id`, `algorithm_used`, `cluster_score`, `last_updated`
- **Propensity score columns**: `subscription_propensity_score`, `churn_propensity_score`, `commerce_propensity_score`
- **GMM output column**: `soft_persona_scores` (JSON string, null for non-GMM algorithms)
- **Interpretability column**: `cluster_top_features` (JSON string, top-5 features per cluster)
- **Status columns**: `is_new_user` (boolean), `last_updated` (timestamp)

**Upsert pattern.** All writes are `INSERT ... ON CONFLICT (user_id) DO UPDATE SET ...`. The `user_id` column has a UNIQUE constraint. This ensures that a silhouette gate failure (F-20) leaves all existing assignments intact rather than leaving some users with NULL assignments.

**New user exclusion.** Users with `is_new_user = TRUE` have a row in `feature_store` but their `persona_label` is set to `'new_user'` and their clustering columns are null. They are included in every subsequent weekly run until they accumulate > 4 sessions and other source data.

**Retention.** The feature store is retained indefinitely with versioning via MLflow run IDs. The `last_updated` timestamp allows point-in-time reconstruction of the persona state at any prior week.

---

### 8.5 Data Volume Expectations

| Deployment Tier | Users | GA4 Events/Year | Feature Store Rows | Pipeline Step 3 Duration |
|-----------------|-------|-----------------|-------------------|--------------------------|
| Dev / Synthetic | 100K | 15M | ~95K | < 2 min (pandas) |
| Small publisher | < 1M | 200M–500M | ~950K | < 10 min (pandas) |
| Mid publisher | 1M–10M | 200M–5B | ~9.5M | < 30 min (dask) |
| Large publisher | 10M–50M | 2B–25B | ~47.5M | < 2 hours (pyspark) |
| NYPost scale | 50M–100M | 10B–50B | ~66M | 3–4 hours (pyspark) |

---

### 8.6 Data Retention Policy

| Data Layer | Retention Period | Notes |
|-----------|-----------------|-------|
| Raw source staging tables | 30 days rolling | Older rows archived or deleted to control table sizes |
| Processed feature store | Indefinite (versioned by last_updated) | One row per user; historical state via MLflow run IDs |
| MLflow run artifacts | 1 year | scaler.pkl, centroids, feature importance JSON, persona distribution JSON |
| MLflow run metrics | Indefinite | Silhouette, stability, persona distribution percentages |
| Pipeline audit logs | 1 year | Step-level structlog output |
| Redis cache | 7 days TTL per key | Refreshed weekly by Step 9 |

---

### 8.7 PII Handling

**PII fields** in the platform: `email`, `hashed_email`, `first_name`, `last_name`, `address_state`, `address_zip` (from zephr_users), `gender` (from transunion_demographics), `home_ownership`, `education`, `state` (from transunion_demographics).

**Rules:**
- PII fields are stored in source staging tables but are masked (replaced with `[REDACTED]`) in analytics environments and in any data exported to notebooks or BI tools.
- `hashed_email` is a SHA-256 hash used only as a join key to Transunion. It must never appear in any API response field.
- `first_name`, `last_name`, `email` must never appear in MLflow artifacts, Grafana dashboards, or API responses.
- The feature store contains only numeric and binary ML features — no raw PII fields.
- A CI step scans all staged files for email patterns (`[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}`) and blocks commits containing real email addresses.

---

## SECTION 9: PLATFORM REQUIREMENTS

### 9.1 Infrastructure Components

| Component | Technology | Version | Purpose | Uptime SLA |
|-----------|-----------|---------|---------|-----------|
| Application DB | PostgreSQL | 15 | Stores all 9 tables including feature_store | 99.9% in production |
| Feature Engineering | Pandas (dev) / Dask (mid) / PySpark (large) | 2.2 / latest / 3.5 | Steps 3–5 of Airflow DAG | Complete within batch window |
| ML Training | scikit-learn / hdbscan / Spark MLlib | 1.4 / 0.8 / 3.5 | Steps 6–7: algorithm evaluation + clustering | Complete within batch window |
| Model Registry | MLflow | 2.13 | Artifact storage, experiment tracking, model versioning | Best effort (not on serving path) |
| Orchestration | Apache Airflow | 2.x | 9-step DAG with validation gates | Weekly trigger reliability |
| Persona Serving API | FastAPI + Uvicorn | 0.111 | Real-time persona retrieval | p99 < 10ms; 99.9% uptime |
| Cache Layer | Redis | 7 | Persona + propensity per user_id, TTL = 7 days | p99 < 1ms read |
| Monitoring | Grafana + Prometheus | latest | Pipeline metrics, silhouette trend, business KPIs | Alerts within 5 min of trigger |
| Alerting | PagerDuty | — | P1/P2 alerts from pipeline and API monitoring | — |
| ORM / Migrations | SQLAlchemy 2.0 / Alembic | 2.0 / 1.13 | Database access layer | — |
| Config | Pydantic-settings | 2.7 | Type-safe config loading from YAML + env vars | — |
| Logging | structlog | 24.1 | JSON structured logs in all pipeline steps | — |

**[ARCHITECTURAL DECISION]** Redis 7 is the authoritative version per spec-source.md technology decision log. CLAUDE.md references Redis 5.0, which is superseded by this specification.

---

### 9.2 Deployment Architecture

**Development (Docker Compose).** All seven services run locally via `docker-compose.yml`:

```
Services:
1. postgres   — PostgreSQL 15 (port 5432)
2. redis      — Redis 7 (port 6379)
3. mlflow     — MLflow tracking server (port 5000)
4. airflow    — Airflow webserver + scheduler (ports 8080/8793)
5. api        — FastAPI persona serving (port 8000)
6. grafana    — Grafana dashboard (port 3000)
7. prometheus — Metrics collection (port 9090)
```

**Cloud path (production).** MWAA (AWS Managed Airflow) or Cloud Composer (GCP) for Airflow; RDS for PostgreSQL; ElastiCache for Redis. The SQLAlchemy + Pydantic-settings abstraction ensures the application code requires no changes when moving from Docker Compose to cloud services — only environment variables change.

---

### 9.3 Multi-Tenant Deployment

Each publishing client gets:
- A dedicated PostgreSQL schema (`configs/clients/{client}.yaml → database.schema`).
- An isolated Airflow DAG run (per-client DAG parameterisation).
- A separate API key for `GET /api/v1/persona/{user_id}` access.
- A separate Grafana organisation (or Grafana folders with RBAC) showing only their pipeline metrics.

No cross-client queries are possible at the ORM level. The schema isolation is verified by the integration test described in NFR-07.

Client configuration files (`configs/clients/{client}.yaml`) are **never committed to git** (except `configs/clients/example.yaml`, which is a template with placeholder values). The `.gitignore` rule `configs/clients/*.yaml` with the exception `!configs/clients/example.yaml` enforces this.

---

### 9.4 CI/CD Pipeline

**GitHub Actions — CI (`ci.yml`, runs on every PR):**

```
1. Lint:       black --check (line-length=88) + isort --check (profile=black) + flake8
2. Type check: mypy --strict on app/, etl/, ml/
3. Tests:      pytest tests/unit/ (no DB/Redis required)
               pytest tests/integration/ (requires Docker services via docker-compose up -d)
4. Coverage:   pytest-cov — fail if coverage < 80% on ETL, feature engineering, API code
5. Grep check: fail if hardcoded configurable values detected in app/, ml/, etl/
6. PII scan:   fail if email patterns found in staged Python files
```

**GitHub Actions — CD (`cd.yml`, runs on merge to main):**

```
1. Build Docker images: Dockerfile.api, Dockerfile.pipeline, Dockerfile.mlflow
2. Push to container registry (configured in repository secrets)
3. No automatic deployment to production (manual approval gate)
```

**Pre-commit hooks (`.pre-commit-config.yaml`):** Credential scan (patterns matching API keys, passwords, connection strings), trailing whitespace, end-of-file fix. Added in Phase 14.

---

### 9.5 Observability

**Grafana dashboards (one per panel group):**

| Dashboard | Panels | Data Source |
|-----------|--------|-------------|
| Pipeline Health | Step runtime, row count per source, step status (pass/fail) | Prometheus + structlog |
| ML Quality | Silhouette score trend, per-cluster silhouette, persona stability WoW, inertia curve | MLflow API |
| Persona Distribution | Stacked bar of user % per persona WoW (F-31) | MLflow API |
| Feature Coverage | % users with data per source (GA4, Transunion, Pushly, OpenWeb, Trackonomics) | Feature store SQL query |
| API Performance | Request rate, p50/p99 latency, error rate, cold-start rate | Prometheus |
| Business KPIs | Newsletter CTR by persona, subscription conversion by persona | Feature store SQL + campaign data |

**PagerDuty alert levels:**

| Severity | Condition |
|----------|-----------|
| P1 | Silhouette gate fire (< 0.30); GA4 coverage < 90%; feature drift > 3 features simultaneously; API p99 > 50 ms sustained |
| P2 | Silhouette drop > 0.05 WoW; persona stability < 80%; Transunion coverage < 60%; persona distribution drift > 30% relative; pipeline step runtime > 2× median |

---

### 9.6 Disaster Recovery

**Pipeline fail-safe.** If the silhouette gate fires (F-20), the prior week's persona assignments are retained in the feature store and Redis (TTL has not yet expired). Users are never left without a persona assignment as long as the pipeline has run at least once.

**Redis TTL.** The 7-day TTL ensures that even if the pipeline misses one weekly run, all users retain their persona assignment in the cache until the next successful run. If the pipeline misses two consecutive runs, Redis cache will start expiring. Cold-start rules (F-25) handle these users.

**MLflow rollback.** The rollback procedure for a silhouette gate failure is automated in the Airflow DAG: Step 7 loads the prior week's `run_id` from MLflow, restores the `scaler.pkl` and centroid artifact, and executes the write-back with prior assignments.

**Database backup.** PostgreSQL point-in-time recovery is enabled in production. Feature store is backed up daily. RPO: 24 hours. RTO: 4 hours.

---

## SECTION 10: SUCCESS METRICS

### 10.1 ML KPIs

| KPI | Target | Cadence | Alert Rule | Measurement Tool |
|-----|--------|---------|-----------|-----------------|
| Silhouette score (overall) | > 0.35 | Weekly | P2 if drops > 0.05 vs prior week | MLflow + Grafana |
| Silhouette score (per cluster) | > 0.25 for all clusters | Weekly | P2 if any cluster < 0.20 | MLflow + Grafana |
| Persona stability (WoW) | > 85% users same persona | Weekly | Trigger Stage 2 re-evaluation if < 80% for 3 consecutive weeks | MLflow + Grafana |
| Algorithm consistency (KMeans vs GMM) | > 75% agreement on non-Low-Engager users | Weekly | Trigger ensemble mode if < 70% agreement | MLflow comparison run |
| Feature coverage — GA4 | > 95% | Daily | P1 alert if < 90% | Feature store SQL + Grafana |
| Feature coverage — Transunion | > 65% | Monthly | P2 alert if < 60% | Feature store SQL + Grafana |
| Cluster size balance | Largest cluster < 60% of total users | Weekly | Re-evaluate K if Low Engager > 60% | MLflow persona distribution |
| Persona distribution drift (F-31) | No persona changes > 30% relative WoW (Low Engager exempt) | Weekly | P2 alert per F-31 specification | MLflow + Grafana + PagerDuty |

---

### 10.2 Business KPIs

| KPI | Target | Cadence | Alert Rule | Measurement Tool |
|-----|--------|---------|-----------|-----------------|
| Newsletter CTR by persona | +30–50% CTR lift vs unsegmented control | Per send / weekly | Flag if lift < 15% for 3 consecutive weeks | Sailthru reporting + Grafana |
| Subscription conversion rate | +15–25% vs non-segmented baseline | Monthly | Alert if rate drops > 5% vs prior month | Braintree + Zephr data + Grafana |
| Ad CPM by segment | +20–40% premium for Sports Focused and High Value Shoppers | Monthly | Monthly revenue team report | Ad server reporting |
| Revenue per user (RPU) | High Value Shoppers RPU > 5× Low Engager RPU | Monthly | Track cohort RPU trend over 6 months | Feature store SQL + finance data |
| Churn rate by persona | Overall churn −20% YoY after activation | Monthly | Alert if any persona churn > 5% in a month | Braintree cancellation events |
| Re-engagement rate (Low Engager) | 5–10% re-engagement rate per campaign | Per campaign | Benchmark each campaign vs prior | GA4 session reactivation events |
| Persona coverage | ≥ 80% of registered users have ML persona | Weekly | Alert if coverage drops below 75% | Feature store SQL + Grafana |
| Commerce conversion rate lift | +25% conversion lift vs non-segmented | Monthly | Monthly affiliate performance report | Trackonomics data |

---

### 10.3 Platform KPIs

| KPI | Target | Cadence | Measurement Tool |
|-----|--------|---------|-----------------|
| API p99 latency (single) | < 10 ms | Continuous | Prometheus + Grafana |
| API p99 latency (batch 1K) | < 100 ms | Continuous | Prometheus + Grafana |
| Pipeline reliability | ≥ 49 successful runs / 52 weeks | Weekly | Airflow DAG run history |
| Test coverage | ≥ 80% on ETL, feature engineering, API code | Per PR | pytest-cov in GitHub Actions CI |
| Pre-commit pass rate | 100% of commits pass pre-commit hooks | Per commit | GitHub Actions CI |
| MLflow audit completeness | 100% of production runs have all required metrics and artifacts | Weekly | Post-run validation step in DAG |

---

### 10.4 Measurement Tools Summary

| Tool | What It Measures | Access |
|------|-----------------|--------|
| Grafana | API latency, pipeline runtime, silhouette trend, persona stability, distribution drift, business KPIs | Internal dashboard (port 3000 in Docker Compose) |
| MLflow UI | Experiment metrics, artifact comparison, model registry, run history | Internal dashboard (port 5000 in Docker Compose) |
| Prometheus | Raw metrics: API request rate, latency histograms, Redis hit rate | Internal metrics server (port 9090) |
| pytest-cov | Code test coverage percentage | GitHub Actions CI report |
| locust | API throughput (10,000 req/sec) and latency under load | CI load test (runs on PR to main) |
| Uptime Robot | API availability (99.9% SLA) | External health check |
| PagerDuty | P1/P2 alert delivery and acknowledgement tracking | PagerDuty dashboard |

<!-- END_SECTION_10 -->

---

## SECTION 11: PROJECT PHASES AND MILESTONES

### Phase Numbering Reconciliation

**[ARCHITECTURAL DECISION]** Two phase numbering systems exist:
- `spec-source.md` roadmap phases (1=SPEC through 15=TESTING) — the full product milestone view.
- `CLAUDE.md` phase tracker (1=environment-setup through 9=monitoring) — the current engineering sprint breakdown.

This document uses the **spec-source.md 15-phase roadmap** as the authoritative structure. The CLAUDE.md tracker covers phases 1–9 of this roadmap, with phases 10–15 to be added as work progresses.

---

| Phase | Name | Status | Branch |
|-------|------|--------|--------|
| 1 | SPEC — Specification | COMPLETE | feature/phase1-environment-setup |
| 2 | DESIGN — Architecture Diagrams | IN PROGRESS | feature/phase2-database-schema |
| 3 | TASKS — Task Breakdown | PENDING | (to be created) |
| 4 | DATABASE — DDL + ORM | PENDING | feature/phase3-etl-ingestion (next) |
| 5 | SYNTHETIC DATA | PENDING | feature/phase4-feature-engineering |
| 6 | ETL PIPELINE | PENDING | feature/phase5-ml-training |
| 7 | FEATURE ENGINEERING | PENDING | feature/phase6-ml-inference |
| 8 | EDA — Notebooks | PENDING | feature/phase7-api-layer |
| 9 | ML TRAINING | PENDING | feature/phase8-airflow-dags |
| 10 | MLFLOW Integration | PENDING | feature/phase9-monitoring |
| 11 | PROPENSITY SCORES | PENDING | (to be created) |
| 12 | FASTAPI Layer | PENDING | (to be created) |
| 13 | AIRFLOW DAG | PENDING | (to be created) |
| 14 | DOCKER + CI/CD | PENDING | (to be created) |
| 15 | TESTING + DOCS | PENDING | (to be created) |

---

### Phase 1: SPEC — Specification
**Deliverables.** This master specification document. All 8 peer-review corrections applied. `configs/base.yaml` with canonical 46-feature list, propensity weights, cold-start rules, clustering parameters.
**Definition of Done.** Master specification approved. `configs/base.yaml` committed to main. No TODOs in committed files.
**Dependencies.** None.
**Effort.** 2 days.
**Risk.** Low — specification work only.

### Phase 2: DESIGN — Architecture Diagrams and OpenAPI Contract
**Deliverables.** System sequence diagrams for all 9 Airflow steps. Full OpenAPI contract for all 4 API endpoints. Database ERD for all 9 tables. Component interaction diagrams. Detailed design for the FeatureEngineering backend abstraction layer.
**Definition of Done.** All diagrams committed. OpenAPI contract committed to `docs/openapi.yaml`. ERD committed to `docs/erd.png`. Architecture decision log committed.
**Dependencies.** Phase 1 approved.
**Effort.** 3 days.
**Risk.** Medium — design decisions made here lock the API contract for all downstream phases.

### Phase 3: TASKS — File-by-File Build Plan
**Deliverables.** Full task breakdown by file. Acceptance criteria per file. Dependency graph. CI/CD scaffold (`.github/workflows/ci.yml` stub).
**Definition of Done.** Every file in the target folder structure has an assigned task with acceptance criteria.
**Dependencies.** Phase 2 approved.
**Effort.** 2 days.
**Risk.** Low.

### Phase 4: DATABASE — 9 DDL Scripts + ORM Models
**Deliverables.** 9 SQL DDL scripts in `sql/ddl/` (all using `{schema}` placeholder). 9 SQLAlchemy ORM model files in `app/models/orm/` (all with `__table_args__`). Index definitions. Alembic migration scripts. `configs/clients/example.yaml` template.
**Definition of Done.** `db-check` skill passes — every table column in DDL has a matching ORM attribute and vice versa. All 9 migrations apply cleanly to a fresh PostgreSQL schema. Integration test verifies schema isolation between two client schemas.
**Dependencies.** Phase 3.
**Effort.** 4 days.
**Risk.** High — schema changes after this phase require migrations and may break downstream phases. The table naming conflict (CLAUDE.md vs spec-source.md) must be resolved definitively in this phase.

### Phase 5: SYNTHETIC DATA — Data Generation
**Deliverables.** `scripts/generate_synthetic_data.py` — generates all 9 tables with persona injection, realistic distributions, referential integrity, and source coverage gaps. `scripts/seed_database.py` — populates the dev database from generated files. `data/synthetic/` committed files for dev use.
**Definition of Done.** 100K users generated across all 9 tables with correct persona proportions. Referential integrity 100% (no orphan records). Coverage rates: Pushly 35%, OpenWeb 23%, Trackonomics 16%, Transunion 70%. `seed_database.py` runs without errors on a fresh schema.
**Dependencies.** Phase 4 (DDL must exist before data generation scripts can run).
**Effort.** 4 days.
**Risk.** Medium — synthetic data quality directly affects clustering validation in Phase 9.

### Phase 6: ETL PIPELINE — 8 Source Connectors
**Deliverables.** 8 ingestion modules in `etl/ingestion/` (one per source). `etl/identity/stitcher.py`. Row count validation (F-03). Incremental vs full-refresh mode logic (F-04). Transunion match confidence filter (F-05). BigQuery connection for GA4.
**Definition of Done.** All 8 connectors run against synthetic data without errors. Identity stitching resolves ≥ 95% of synthetic users. Row count validation correctly aborts on a 25% deviation test case. All connectors log structlog JSON output.
**Dependencies.** Phase 5 (synthetic data needed for integration tests).
**Effort.** 5 days.
**Risk.** High — GA4 BigQuery connector requires google-cloud-bigquery library and BigQuery project credentials (even for synthetic testing). Identity resolution logic is complex and error-prone.

### Phase 7: FEATURE ENGINEERING
**Deliverables.** `ml/feature_store/builder.py` — assembles 46-feature matrix from joined source tables. `ml/feature_store/validator.py` — feature drift detection (Step 4). log1p transforms (F-07). Null imputation (F-08). New user exclusion (F-09). Derived features: social_engagement_score (F-10), email_engagement_score (F-11), newsletter binary flags (F-12), pageviews_per_session (F-06).
**Definition of Done.** Builder produces exactly 46-column output matching `configs/base.yaml ml.features.matrix`. New user exclusion correctly removes ~5% of 100K synthetic users. Feature drift validator correctly aborts on a simulated 25% feature shift. All transforms verified by unit tests.
**Dependencies.** Phase 6 (identity-stitched source data must be available).
**Effort.** 4 days.
**Risk.** Medium — the 46-feature list must exactly match base.yaml. Any discrepancy between DDL, ORM, builder.py, and base.yaml will be caught by the `ml-check` skill.

### Phase 8: EDA — Exploratory Data Analysis
**Deliverables.** 4 Jupyter notebooks in `notebooks/`: `01_eda.ipynb` (feature distributions), `02_feature_analysis.ipynb` (correlations, coverage), `03_algorithm_evaluation.ipynb` (preliminary clustering on synthetic data), `04_persona_profiling.ipynb` (cluster characterisation).
**Definition of Done.** All 4 notebooks run end-to-end without errors on the synthetic dataset. Notebook 03 shows a silhouette score > 0.30 on synthetic data (validating that the persona injection in Phase 5 is recoverable by clustering). Notebook 04 shows that at least 7 of 9 injected personas are recoverable by name.
**Dependencies.** Phase 7 (feature store must be populated).
**Effort.** 3 days.
**Risk.** Low — EDA is exploratory; no code correctness gates.

### Phase 9: ML TRAINING — Clustering Pipeline
**Deliverables.** 5 algorithm modules in `ml/training/algorithms/`. `ml/training/evaluation/metrics.py` (silhouette, Davies-Bouldin, inertia). `ml/training/evaluation/interpretability.py` (F-32 feature importance, persona naming). `ml/pipelines/clustering_pipeline.py`. K selection logic. 4-stage pipeline (F-13, F-14, F-15).
**Definition of Done.** Full 4-stage pipeline runs on synthetic data. Composite score computed for at least 3 algorithm+K configurations. Selected configuration logged to MLflow. Silhouette gate tested with a simulated below-threshold result. Feature importance top-5 per cluster written to MLflow artifact.
**Dependencies.** Phase 8 (EDA provides baseline cluster count estimates). Phase 10 (MLflow must be running — order may be swapped with Phase 10).
**Effort.** 6 days.
**Risk.** High — most complex algorithmic phase. HDBSCAN on synthetic data must produce a natural K estimate that is reasonable for the data distribution.

### Phase 10: MLFLOW Integration
**Deliverables.** `ml/experiments/mlflow_logger.py`. MLflow tracking server configured in `docker-compose.yml`. All required metrics and artifacts logged per F-30. Model registry setup. Scaler persistence (F-16). Rollback procedure documented and tested.
**Definition of Done.** MLflow UI shows all required metrics and artifacts for a pipeline run. Rollback procedure: load prior run's scaler.pkl and rerun write-back — verified in integration test. `mlflow_logger.log_persona_distribution()` produces correct JSON artifact.
**Dependencies.** Phase 9.
**Effort.** 3 days.
**Risk.** Medium — MLflow artifact store configuration (local filesystem vs MinIO) must be decided before this phase starts.

### Phase 11: PROPENSITY SCORES
**Deliverables.** Propensity score computation modules implementing F-18a (subscription), F-18b (churn), F-18c (commerce). Integration with feature_store write-back. Sigmoid function. Centroid distance computation and normalisation.
**Definition of Done.** All 3 propensity scores computed for 100K synthetic users. Scores are in range [0.0, 1.0]. Weights loaded from config (no hardcoded values). Unit tests verify all three formulas against known inputs.
**Dependencies.** Phase 9 (centroid positions required for distance computation). Phase 10 (MLflow for weight logging).
**Effort.** 3 days.
**Risk.** Low — formulas are precisely specified in F-18a/b/c.

### Phase 12: FASTAPI Layer — Persona Serving API
**Deliverables.** 4 API endpoints (F-21 through F-24). Redis cache service (`app/services/cache_service.py`). Cold-start logic (`app/utils/cold_start.py`) per F-25. Pydantic v2 response schemas. API key middleware (`app/core/security.py`). Batch endpoint with Redis pipeline.
**Definition of Done.** All 4 endpoints return correct responses in integration tests. Cold-start path returns correct labels for all 5 rule branches. Batch endpoint returns p99 < 100 ms for 1,000 user IDs in load test. API health endpoint correctly reflects Redis and DB connection status.
**Dependencies.** Phase 11 (propensity scores must be in feature_store and Redis). Phase 9 (persona assignments must exist).
**Effort.** 4 days.
**Risk.** Medium — the cold-start path must handle all edge cases gracefully (valid user not in Redis, valid user with no feature data).

### Phase 13: AIRFLOW DAG — 9-Step Orchestration
**Deliverables.** `dags/audience_intelligence_dag.py` implementing all 9 steps with correct fail behaviours per F-27. Validation gates. Fail-safe fallback to prior week. Persona distribution logging (F-31). Pipeline trigger endpoint integration (F-24).
**Definition of Done.** DAG runs end-to-end on synthetic data via Docker Compose Airflow. All 9 steps pass. Simulated step failures produce the correct abort/continue behaviour per the step table. PagerDuty webhook integration tested (mock webhook).
**Dependencies.** Phase 12 (all pipeline steps must be implemented).
**Effort.** 4 days.
**Risk.** Medium — Airflow DAG complexity. Fail behaviours must be tested explicitly for each of the 9 steps.

### Phase 14: DOCKER + CI/CD
**Deliverables.** 3 Dockerfiles (`Dockerfile.api`, `Dockerfile.pipeline`, `Dockerfile.mlflow`). `docker-compose.yml` for all 7 services. GitHub Actions `ci.yml` (lint + type check + tests + coverage + grep check). GitHub Actions `cd.yml` (Docker build + push). `.pre-commit-config.yaml` with credential scan. `.gitignore` updates (`configs/clients/*.yaml` except example).
**Definition of Done.** `docker-compose up` starts all 7 services without errors. CI pipeline passes on a clean PR. Pre-commit hook blocks a commit containing a simulated API key pattern. `configs/clients/nypost.yaml` (if created locally) is not tracked by git.
**Dependencies.** Phase 13.
**Effort.** 4 days.
**Risk.** Medium — Docker build size and layer caching optimisation for the pipeline image (heavy ML dependencies).

### Phase 15: TESTING + DOCS
**Deliverables.** Complete pytest suite achieving ≥ 80% coverage. README with local setup instructions. API reference documentation. Architecture decision log. `tests/unit/` (no DB/Redis) and `tests/integration/` (Docker services required).
**Definition of Done.** `pytest --cov` reports ≥ 80% coverage on ETL, feature engineering, and API code. README allows a new engineer to set up the dev environment from scratch in < 30 minutes. All integration tests pass against Docker Compose services.
**Dependencies.** Phase 14.
**Effort.** 5 days.
**Risk.** Low — documentation and test completion; no new features.

---

## SECTION 12: CONSTRAINTS

### 12.1 Infrastructure

Docker Compose is the only infrastructure until the first paying client is acquired. No cloud spend in development. All seven services (PostgreSQL, Redis, MLflow, Airflow, FastAPI, Grafana, Prometheus) must run on a single developer machine with 16 GB RAM. AWS/GCP is the intended production cloud path but no cloud resources are provisioned until a paying client requires it.

### 12.2 Data

Synthetic data only in development. No real publisher PII or reader data may be used in the development environment. No real client configurations may be stored in the git repository. Google BigQuery read access for GA4 requires a real GCP project — synthetic GA4 data is loaded into the local PostgreSQL staging tables directly (bypassing the BigQuery connector in the development pipeline).

### 12.3 Timeline

Phases are strictly sequential. No parallel phase branches. A phase branch is cut from `main` only after the prior phase has been merged. This ensures the folder structure and config files are stable before the next phase builds on them. The rule is enforced by the branch protection settings and the phase naming convention in CLAUDE.md.

### 12.4 Technology Stack

The technology stack is locked to the versions specified in `requirements/base.txt` and `requirements/dev.txt`. No framework substitutions are permitted without a documented architectural decision record. The versions are: FastAPI 0.111, SQLAlchemy 2.0, Alembic 1.13, Pandas 2.2, NumPy 1.26, scikit-learn 1.4, HDBSCAN 0.8, MLflow 2.13, Redis 7, Pydantic-settings 2.7, structlog 24.1, Python 3.11+.

### 12.5 Security

No real client configuration files may be committed to git (`configs/clients/*.yaml` gitignored except `example.yaml`). The pre-commit credential scan is mandatory from Phase 14 onwards. No real API keys, database credentials, or PII may appear in any committed file. The `.env` file is gitignored; environment secrets are injected at runtime only.

---

## SECTION 13: ASSUMPTIONS

The following assumptions are stated explicitly. Each is sourced from spec-source.md or flagged as an architectural assumption.

1. **Source coverage rates are as documented.** Pushly 35%, OpenWeb 23%, Trackonomics 16%, Transunion 70% match rate — sourced from spec-source.md Section 5.1. These rates are used in synthetic data generation and are not validated against any specific publisher's actual data.

2. **Silhouette target > 0.35 is achievable on real publisher data.** The NYPost initiative achieved this with Bisecting K-Means on 66M users. Synthetic data generates persona-injected distributions specifically designed to be recoverable by clustering. Real publisher data may have noisier distributions that produce lower silhouette scores — the 0.30 safety gate is the operational floor.

3. **user_id is truly universal across all 8 source systems.** Zephr issues the user_id at registration. All other systems are assumed to have the user_id available at the time of first interaction: Braintree receives it from the subscription creation flow, Pushly receives it at opt-in, Trackonomics receives it via URL parameter. If any source system does not consistently pass user_id, the identity stitching step will produce lower coverage for that source. [ARCHITECTURAL DECISION: The GA4 anonymous user path explicitly does not assume user_id is available; it uses the bridge table approach.]

4. **GA4 BigQuery export is available for every client.** GA4 BigQuery export is the native GA4 data path and is available at no additional cost for clients on Google Analytics 4. Publishers not using GA4 would require a custom connector — not in scope for the initial product.

5. **Transunion batch file delivery is monthly.** The monthly refresh cadence for Transunion demographic data is the standard Transunion TruAudience delivery schedule. Publishers with higher-frequency demographic refresh needs would require a custom Transunion API integration — not in scope.

6. **Redis TTL of 7 days is sufficient given weekly pipeline cadence.** The pipeline runs every 7 days. The Redis TTL is set to exactly 7 days (604,800 seconds in base.yaml). This assumes the pipeline never misses two consecutive weekly runs. If it does, some users will begin receiving cold-start responses. The 7-day TTL matches the pipeline cadence — any change to pipeline frequency requires a matching TTL change.

7. **Docker Compose is sufficient for development and demo deployments.** The 7-service Docker Compose configuration is designed for a single-machine developer setup and for client demo deployments at small publisher scale (< 100K users). Production deployments at mid or large scale require the cloud infrastructure path described in Section 9.2.

8. **All 9 personas are present in every publisher's data.** The persona naming rules in `configs/base.yaml` assume that all 9 archetypes exist in the publisher's audience. A sports-only publisher may not have a Celebrity-Entertainment cluster; K selection and interpretability checks are designed to handle this by merging under-sized clusters.

9. **Client data teams can connect source systems within 2 weeks of onboarding.** Onboarding timeline assumes that the client's data team has access credentials for all 8 source systems and can configure the connectors in `etl/ingestion/` with their system-specific endpoints. Source systems requiring custom API development are not in scope for the standard onboarding.

10. **The phase numbering in CLAUDE.md (9 phases) maps to a subset of the spec-source.md 15-phase roadmap.** CLAUDE.md phases 1–9 correspond to spec-source.md phases 1–9 with different naming. Phases 10–15 of the spec-source.md roadmap will be added to CLAUDE.md as work progresses.

<!-- END_SECTION_13 -->

---

## SECTION 14: RISKS

### Risk 1: GA4 Identity Resolution Failures (Anonymous Users)
**Description.** GA4 assigns a `user_pseudo_id` to every session, but this is only resolved to `user_id` when the user logs in. Publishers with low registration rates (< 40%) will have large numbers of anonymous sessions that cannot be attributed to a registered user. These sessions are excluded from clustering.

**Likelihood.** High — anonymous user rates of 40–60% are typical for general-interest publishers.

**Impact.** Medium — the platform explicitly excludes anonymous users. The risk is that coverage metrics look acceptable (GA4 coverage > 95% of registered users) while the underlying recommendation quality is limited by the registration rate.

**Risk Owner.** Data Engineer.

**Mitigation.** Log the anonymous session rate as a separate metric in the Airflow pipeline. Surface the registration rate in the Grafana "Feature Coverage" dashboard panel. Include in onboarding documentation: publishers should have a registration incentive strategy to maximise the proportion of sessions attributed to registered users.

**Contingency.** If anonymous session rate exceeds 60% and editorial teams require coverage, explore anonymous user segmentation using session-level GA4 signals only — a separate, non-user_id-based segmentation path is a future phase.

---

### Risk 2: Low Engager Cluster Dominates (> 60% of Users)
**Description.** The Low Engager persona represents ~50% of users at NYPost scale. For publishers with lower overall engagement (content verticals, B2B publishers), this proportion could exceed 60%, triggering the cluster size balance alert and forcing K re-evaluation.

**Likelihood.** Medium — dependent on publisher type and audience quality.

**Impact.** High — a single dominant cluster reduces the business utility of the segmentation. Advertisers cannot buy a 60%-share "Low Engager" exclusion segment effectively.

**Risk Owner.** ML Engineer.

**Mitigation.** The cluster size balance KPI (largest cluster < 60% of total users) automatically triggers K re-evaluation. At higher K values, Low Engagers can be sub-clustered into 2–3 more specific groups (e.g. "dormant subscribers", "bounce-only visitors", "seasonal readers").

**Contingency.** If re-evaluation at higher K still produces > 60% in a single cluster, the publisher may be genuinely low-signal and the platform KPIs should be re-baselined to reflect their data quality.

---

### Risk 3: Silhouette Score Below 0.30 Safety Threshold
**Description.** A production clustering run produces silhouette < 0.30, triggering the safety gate. The prior week's assignments are retained, but the business team cannot run new campaigns on fresh data until the issue is resolved.

**Likelihood.** Medium — can be caused by feature drift, data quality issues, or genuine audience behaviour change.

**Impact.** High — campaign quality degrades silently if the gate is not configured correctly; conversely, frequent gate fires degrade trust in the platform.

**Risk Owner.** ML Engineer.

**Mitigation.** Step 4 (Feature Validation) is designed to catch the most common upstream causes of silhouette degradation (multi-feature drift from a source failure) before they reach Step 7. F-31 (distribution drift alert) catches distribution shifts. If Step 4 and F-31 are both correctly implemented, Step 7 gate fires should be rare and attributable to genuine data quality events.

**Contingency.** Automated rollback to prior week's run (automated in Step 7 fail behaviour). ML engineer investigation within 24 hours of P1 alert.

---

### Risk 4: Transunion Match Rate Below 65%
**Description.** The Transunion monthly batch match rate falls below 65%, triggering a P2 alert and reducing the quality of the three demographic features (age_score, income_score, has_children).

**Likelihood.** Low — Transunion hashed email match rates are typically stable at 65–75%.

**Impact.** Medium — demographic features are supplementary (3 of 46). The pipeline continues without them. Missing demographics → 0 imputation, which biases these features toward the cluster means.

**Risk Owner.** Data Engineer.

**Mitigation.** Monitor match rate monthly. Investigate email hash mismatch issues (normalisation inconsistencies) when rate drops. Transunion contract should include a minimum match rate SLA.

**Contingency.** If match rate falls below 50%, exclude demographic features from the ML matrix for that month's run to prevent zero-imputation bias from distorting clustering.

---

### Risk 5: Pipeline Runtime Exceeds SLA at Growing Data Volumes
**Description.** As a publisher's user base grows from 100K to 1M+, the pandas-based feature engineering step exceeds 30 minutes, breaching the 4-hour batch window.

**Likelihood.** Medium — gradual growth is predictable; the backend swap is designed-in but requires implementation work.

**Impact.** Medium — the Dask backend is the designed upgrade path. Implementation is a config flag change plus integration testing.

**Risk Owner.** Data Engineer / ML Engineer.

**Mitigation.** The `feature_engineering.backend` config flag in `configs/base.yaml` supports `"pandas"`, `"dask"`, and `"pyspark"` backends. The interface is identical. F-29 (pipeline runtime monitoring) alerts when any step exceeds 2× its median runtime, providing early warning before the SLA is breached.

**Contingency.** Switch backend to dask when Step 3 consistently exceeds 30 minutes. Document the switching procedure in the runbook.

---

### Risk 6: Persona Drift from Data Quality Issue (Not Modelling Issue)
**Description.** A source system failure causes feature distributions to shift — for example, the Trackonomics SFTP export stops delivering for two weeks, dropping all commerce features to 0 for all users. The pipeline runs but produces incorrect clustering because the feature matrix no longer reflects true behaviour.

**Likelihood.** Medium — source system integrations are the most fragile component of the pipeline.

**Impact.** High — without the Step 4 validation gate, this would silently corrupt persona assignments for all users.

**Risk Owner.** Data Engineer.

**Mitigation.** Step 4 (Feature Validation) specifically detects this: if Trackonomics commerce features drop to 0 for all users, the mean shift exceeds 20% on multiple features simultaneously, triggering the abort condition (> 3 features drifting together). The pipeline aborts and fires a P1 alert before writing any corrupted assignments.

**Contingency.** Prior week's assignments retained. Source system investigation and manual pipeline re-run after issue resolution.

---

### Risk 7: Real Client API Credentials Committed to Git
**Description.** A developer creates a `configs/clients/{client}.yaml` with real API keys or database credentials and accidentally stages it for commit.

**Likelihood.** Low — the `.gitignore` rule prevents automatic staging. But `git add -f` or IDE "add all" shortcuts can bypass it.

**Impact.** Critical — real credentials exposed in git history require immediate rotation, security incident response, and potential breach notification.

**Risk Owner.** All developers. Enforced by pre-commit hook.

**Mitigation.** Three layers: (1) `.gitignore` excludes `configs/clients/*.yaml` except `example.yaml`; (2) pre-commit hook scans staged files for credential patterns (API key formats, connection string patterns, password fields); (3) GitHub Actions CI runs the same credential scan on every push.

**Contingency.** Immediate `git filter-branch` or BFG Repo Cleaner to remove the commit from history. Rotate all exposed credentials within 1 hour. File security incident report.

---

### Risk 8: Cluster Interpretability Fails — Unnamed Clusters
**Description.** After clustering, one or more clusters cannot be matched to a persona label by the `personas.naming_rules` lookup in `configs/base.yaml`. The cluster is assigned a numeric ID with no human-readable label.

**Likelihood.** Low — the naming rules are designed to cover all 9 persona archetypes. However, a publisher with unusual content mix (e.g. no sports coverage) will produce clusters that don't match the sports-focused naming rule.

**Impact.** Medium — unnamed clusters cannot be activated by the business team. They appear as `cluster_4` in Sailthru and cannot be used for premium ad inventory.

**Risk Owner.** ML Engineer.

**Mitigation.** F-32 (feature importance per cluster) and the interpretability scoring (F-14) together guarantee that every cluster either gets a label from the naming rules or fails the interpretability check and is merged back. A `casual_reader` default label (the `"default"` naming rule in base.yaml) catches any cluster that does not match a specific rule.

**Contingency.** Unnamed clusters are labelled `casual_reader` by the default naming rule. The ML engineer reviews and can update `personas.naming_rules` in base.yaml to handle publisher-specific archetypes.

---

### Risk 9: .venv Folder Committed to Git
**Description.** A second virtual environment was created at `.venv/` (observed in the project directory alongside `venv/`). Either directory committed to git would add hundreds of MB of binary files and potentially expose system information.

**Likelihood.** Low — CLAUDE.md explicitly states "NEVER commit `venv/` or `.venv/` to git." The `.gitignore` should cover both.

**Impact.** Medium — git repository bloat; potentially sensitive library version information exposed; repository becomes unusable for other developers until the files are removed from history.

**Risk Owner.** All developers.

**Mitigation.** Verify `.gitignore` includes both `venv/` and `.venv/`. The pre-commit hook should include a check for large binary files. **[OPEN QUESTION — see Section 15, Q1: the .venv folder should be deleted if it is a duplicate environment.]**

**Contingency.** If committed: `git filter-branch` or BFG Repo Cleaner to remove the directory from history.

---

### Risk 10: Real Client Data Used in Development Environment
**Description.** A developer with access to a real publisher's source systems connects a local development environment to live data to accelerate testing, importing real PII into a laptop-hosted database.

**Likelihood.** Low — the development environment is explicitly designed for synthetic data only.

**Impact.** Critical — GDPR/CCPA compliance breach. Real PII in an uncontrolled development environment is a reportable data breach.

**Risk Owner.** All developers. Enforced by data governance policy and onboarding documentation.

**Mitigation.** All database connections in development use only the Docker Compose PostgreSQL instance seeded with synthetic data. The `.env.example` file uses only localhost connection strings. No real BigQuery project credentials should be in the development environment. Pre-commit PII scan catches email patterns.

**Contingency.** Immediate data deletion and security incident report per applicable data protection regulation.

---

### Risk 11: HDBSCAN Compute Time at 66M User Scale
**Description.** HDBSCAN's time complexity is approximately O(n log n) to O(n²) depending on data density. At 66M users with 46 features, the Stage 1 discovery run may take 12–24 hours rather than the target < 2 hours.

**Likelihood.** Medium at NYPost scale. Low at development (100K) and small publisher (< 1M) scale.

**Impact.** Medium — Stage 1 is a one-time deployment step, not a weekly recurring cost. A 24-hour Stage 1 run delays initial persona deployment by one day.

**Risk Owner.** ML Engineer.

**Mitigation.** At large publisher scale (> 10M users), HDBSCAN runs on a 10% random sample rather than the full dataset. The sample is sufficient to discover the natural K value. This is explicitly documented in the spec-source.md scaling tier table. The `feature_engineering.backend` Spark path enables distributed feature preparation before sampling.

**Contingency.** If HDBSCAN on the 10% sample still exceeds 4 hours, skip Stage 1 and use the K range from the publisher size guidelines table directly (e.g. K=9–12 for a 66M-user general publisher).

---

### Risk 12: Feature Store DDL and ORM Model Schema Mismatch
**Description.** The `feature_store` DDL (`sql/ddl/009_create_feature_store.sql`) and the ORM model (`app/models/orm/feature_store.py`) fall out of sync as features are added or renamed during development. Migrations are not run after a column rename, causing SQLAlchemy to produce silent query errors.

**Likelihood.** Medium — this is a common source of bugs in multi-engineer projects.

**Impact.** High — a mismatch between DDL and ORM causes silent data corruption or runtime errors that are difficult to diagnose.

**Risk Owner.** Backend Engineers.

**Mitigation.** The `db-check` skill is designed to detect DDL ↔ ORM parity issues. It must be run after every schema change and before every PR merge that touches `sql/ddl/` or `app/models/orm/`. The CI pipeline should include a check that Alembic migration history is clean (no uncommitted schema changes).

**Contingency.** If a mismatch is detected in production: immediate rollback of the ORM change or DDL migration. `db-check` added to CI as a mandatory step.

---

### Risk 13: Redis Cache Staleness After Pipeline Failure
**Description.** The pipeline fails at Step 8 (Write-Back) or Step 9 (Cache Refresh). The feature store is updated but Redis is not refreshed. Users in Redis have assignments from the prior week while the feature store has new assignments.

**Likelihood.** Low — Step 9 is designed to continue even if webhooks fail, and the cache refresh is atomic per user.

**Impact.** Medium — 7-day TTL means the staleness is bounded. Redis assignments drift from the feature store for up to 7 days.

**Risk Owner.** Backend Engineer / Data Engineer.

**Mitigation.** Step 9 (Cache Refresh) does not fail atomically — it pushes user records individually. If Step 9 is interrupted, the next full pipeline run (within 7 days) will complete the refresh. PagerDuty alert on Step 9 failure allows manual re-run of only Step 9.

**Contingency.** Manual cache refresh script: reads from feature store and pushes to Redis without running the full 9-step pipeline. Add as `scripts/refresh_cache.py`.

---

### Risk 14: Airflow DAG Failure Leaving Feature Store Partially Updated
**Description.** The Airflow Step 8 (Write-Back) fails mid-execution after updating some users but before updating all users. The feature store has a mix of old and new assignments.

**Likelihood.** Low — the upsert pattern and database transaction wrapping are designed to prevent partial writes.

**Impact.** High — a partially updated feature store produces inconsistent persona assignments across users.

**Risk Owner.** Data Engineer.

**Mitigation.** Step 8 must execute its writes inside a single database transaction: `BEGIN; [all upserts]; COMMIT;`. If any upsert fails, the transaction rolls back. The entire write-back either succeeds or fails atomically. The fail behaviour specified for Step 8 in F-27 is "Abort and alert. Do not partial-write."

**Contingency.** If partial write is detected (last_updated timestamps are inconsistent across users after a run), the rollback procedure (load prior week's MLflow run) restores consistency.

---

## SECTION 15: RESOLVED DECISIONS

All questions identified during specification drafting have been resolved. Decisions are binding for all implementation phases.

---

**Q1 — .venv directory [RESOLVED: Non-issue]**

Inspection of the repository working tree confirmed no `.venv/` directory is tracked by git and none exists in the working directory. The `.gitignore` already excludes both `venv/` and `.venv/` (confirmed in repo root `.gitignore`). No action required. The canonical virtual environment path for this project is `venv/` (created by `python -m venv venv`). Both paths remain gitignored.

---

**Q2 — Feature store DDL cross-validation [RESOLVED: Gate on Phase 4]**

Inspection confirmed that `sql/ddl/` contains only `.gitkeep` — no DDL files have been written yet. Phase 4 (DATABASE) is the gate at which all 9 DDL scripts are authored. The `db-check` skill must be run as the Phase 4 definition-of-done check, cross-validating every DDL column against its ORM model attribute.

The `feature_store` DDL must include two column groups beyond the 46 ML features:

*ML output columns (written by Step 8):*
`persona_label VARCHAR(50)`, `cluster_id SMALLINT`, `algorithm_used VARCHAR(50)`, `cluster_score FLOAT`, `last_updated TIMESTAMP`, `subscription_propensity_score FLOAT`, `churn_propensity_score FLOAT`, `commerce_propensity_score FLOAT`, `soft_persona_scores TEXT` (JSON string, nullable), `cluster_top_features TEXT` (JSON string)

*Status / metadata columns:*
`is_new_user BOOLEAN DEFAULT FALSE`, `created_at TIMESTAMP DEFAULT NOW()`, `updated_at TIMESTAMP DEFAULT NOW()`

Additionally, the 4 extra newsletter flags (nl_breaking_news, nl_real_estate, nl_tech_news, nl_lifestyle_weekly — see Q7 resolution below) must be stored as `BOOLEAN DEFAULT FALSE` columns in the DDL but must NOT appear in `configs/base.yaml ml.features.matrix`.

---

**Q3 — CLAUDE.md completeness [RESOLVED: Updated]**

[ARCHITECTURAL DECISION] CLAUDE.md has been updated to: (1) extend the phase tracker to all 15 phases; (2) correct the Redis version from 5.0 to 7; (3) replace the logical table names in the Database Schema section with the canonical source-system names from spec-source.md; (4) add the Airflow 2.9.3 version. The update was applied directly to `.claude/CLAUDE.md`.

---

**Q4 — Apache Airflow version [RESOLVED: requirements/airflow.txt]**

[ARCHITECTURAL DECISION] Apache Airflow is NOT added to `requirements/base.txt`. Airflow's dependency tree (SQLAlchemy pinning, Flask, Connexion, FAB) conflicts with the project's base ML and API dependencies. The canonical solution for this project is a dedicated `requirements/airflow.txt` pinned to `apache-airflow==2.9.3` (latest stable 2.x as of this specification). The Airflow Docker service in `docker-compose.yml` (Phase 14) uses the official `apache/airflow:2.9.3` Docker image and does not install from `requirements/airflow.txt` directly — that file exists for local DAG development and testing outside Docker.

File created: `requirements/airflow.txt` with `apache-airflow==2.9.3` and `apache-airflow-providers-postgres==5.10.2`.

---

**Q5 — MLflow artifact store backend [RESOLVED: Local filesystem for dev]**

[ARCHITECTURAL DECISION] The Docker Compose development environment uses **local filesystem** storage for MLflow artifacts (`./mlruns` mounted volume). Rationale: (1) one fewer Docker service to maintain; (2) no MinIO credentials to configure; (3) the `mlruns/` directory is already gitignored; (4) migration to S3/MinIO in production requires only changing the `MLFLOW_ARTIFACT_ROOT` environment variable — zero code changes.

The `docker-compose.yml` (Phase 14) must set `MLFLOW_ARTIFACT_ROOT=/mlflow/artifacts` and mount a local volume. For production, this env var is overridden to point to an S3 bucket or MinIO endpoint.

---

**Q6 — Table naming canonical form [RESOLVED: spec-source.md names are canonical]**

[ARCHITECTURAL DECISION] The physical DDL and ORM table names follow **spec-source.md** naming exactly:

| Physical Table Name (DDL/ORM) | Previous CLAUDE.md Name | Primary Source |
|-------------------------------|------------------------|----------------|
| `zephr_users` | user_profiles | Zephr |
| `ga4_events` | user_sessions + content_affinity | GA4 |
| `braintree_subscriptions` | subscriptions | Braintree |
| `sailthru_newsletter` | email_engagement | Sailthru |
| `pushly_subscribers` | (part of email_engagement) | Pushly |
| `openweb_engagement` | social_activity | OpenWeb |
| `trackonomics_clicks` | commerce_activity | Trackonomics |
| `transunion_demographics` | (no equivalent) | Transunion |
| `feature_store` | feature_store + persona_assignments | Computed (pipeline output) |

Note: CLAUDE.md's logical schema grouped Sailthru + Pushly into one table and split feature_store + persona_assignments. The canonical physical schema keeps all 8 source tables separate (matching their source systems) and merges feature_store + persona_assignments into a single output table. CLAUDE.md has been updated to reflect these physical names.

---

**Q7 — Newsletter flag count [RESOLVED: 6 in ML matrix; 4 as metadata]**

[ARCHITECTURAL DECISION] The ML feature matrix remains exactly **46 features** as defined in `configs/base.yaml ml.features.matrix`. The 6 newsletter flags in the matrix are: `nl_sports_alerts`, `nl_morning_report`, `nl_page_six_daily`, `nl_celebrity_news`, `nl_evening_update`, `nl_post_opinion`.

The 4 additional flags (`nl_breaking_news`, `nl_real_estate`, `nl_tech_news`, `nl_lifestyle_weekly`) are stored as `BOOLEAN DEFAULT FALSE` columns in the `feature_store` DDL and populated by the ETL pipeline (F-12), but they do NOT enter the StandardScaler or any clustering algorithm. They are available for direct SQL queries and API extension in future phases.

Rationale for not extending the ML matrix to 50: adding 4 low-coverage binary features would dilute the clustering signal without adding interpretability. The 6 current newsletter flags cover the highest-signal newsletters. If a specific publisher's data shows strong clustering signal in the additional flags, they can be added to `configs/clients/{client}.yaml ml.features.matrix` as a per-client override in a future phase.

---

## SECTION 16: ENGINEERING STANDARDS

### 16.1 Python Standards

Every function signature must have type hints — including `self` parameters in class methods. No `Any` types — use `Union`, generic types, or `TypeVar`. No `# type: ignore` without an inline comment explaining why mypy cannot infer the type. f-strings only (no `.format()` or `%` string formatting). Maximum function length: 50 lines. If a function exceeds 50 lines, decompose it. All imports sorted by isort with `profile=black`. Code formatted by black at `line-length=88`.

No bare `except:` — always catch specific exceptions (`except ValueError`, `except KeyError`, etc.). If an exception must be caught broadly, use `except Exception as e:` and log the traceback.

```python
# CORRECT
def compute_silhouette(labels: np.ndarray, X: np.ndarray, sample_size: int) -> float:
    ...

# WRONG — missing return type, no type hints
def compute_silhouette(labels, X, sample_size):
    ...
```

---

### 16.2 SQL Standards

Every DDL file must use `{schema}` placeholder in all table and schema references. Parameterised queries only — no string interpolation in SQL. One DDL file per table under `sql/ddl/`. All analytical queries under `sql/analytics/`. No `SELECT *` — always name columns explicitly.

```sql
-- CORRECT
CREATE TABLE {schema}.zephr_users (
    user_id UUID PRIMARY KEY,
    ...
);

-- WRONG — hardcoded schema
CREATE TABLE public.zephr_users (
    ...
);
```

---

### 16.3 API Standards

All routes are under `/api/v1/` prefix. All request and response models are Pydantic v2 `BaseModel` subclasses. Never return raw SQLAlchemy ORM objects from endpoints — convert to Pydantic schemas in the service layer. Business logic lives exclusively in `app/services/` — endpoints are thin wrappers that call service functions and return their output. All endpoints require API key authentication via the `X-API-Key` header middleware.

```python
# CORRECT — endpoint is thin; logic is in service
@router.get("/persona/{user_id}", response_model=PersonaResponse)
async def get_persona(user_id: UUID, service: PersonaService = Depends()) -> PersonaResponse:
    return await service.get_persona(user_id)

# WRONG — business logic in endpoint
@router.get("/persona/{user_id}")
async def get_persona(user_id: UUID) -> dict:
    result = await db.execute(select(FeatureStore).where(...))
    ...
```

---

### 16.4 Git Standards

Conventional commits format: `feat:`, `fix:`, `chore:`, `docs:`, `test:`, `refactor:`. Branch names: `feature/phaseN-short-name`, `fix/short-description`, `chore/short-description`. No direct pushes to `main`. Every PR must: (1) pass CI (lint + type check + tests + coverage + grep check), (2) include the phase number in the PR title, (3) reference the deliverables from the roadmap in the PR description. Squash merge only. No merge commits.

---

### 16.5 Configuration Standards

All tunable parameters must be in `configs/base.yaml`. Client-specific overrides go in `configs/clients/{client}.yaml`. Environment secrets (connection strings, API keys) go only in `.env` files — never in YAML. Config is loaded via `app/core/config.py` using Pydantic-settings, which merges YAML defaults with environment variable overrides.

```python
# CORRECT — reads from settings object
silhouette_threshold = settings.ml.clustering.silhouette_threshold

# WRONG — hardcoded
silhouette_threshold = 0.30
```

---

### 16.6 Testing Standards

Unit tests in `tests/unit/` — no live database or Redis connections, all external dependencies mocked. Integration tests in `tests/integration/` — require Docker Compose services running (PostgreSQL, Redis). Test filenames mirror the module they test: `app/utils/cold_start.py` → `tests/unit/test_cold_start.py`. Use `pytest.fixture` for shared test data. Use `Faker` for generating realistic synthetic test inputs. Every test function has a descriptive docstring stating what it verifies.

```python
# CORRECT
def test_cold_start_sports_rule_fires_before_subscription_rule() -> None:
    """Verify priority 1 (sports) wins when user has both sports ratio and subscription."""
    ...
```

---

### 16.7 Logging Standards

All logging uses structlog with JSON output format. No bare `print()` in production code. Every pipeline step (Airflow task) logs a structured record at start and end containing: `step_name`, `start_time`, `end_time`, `duration_seconds`, `rows_processed`, `status` ("success" or "failure"), `error` (exception message, if any).

```python
# CORRECT
logger.info("feature_engineering_complete",
            step_name="feature_engineering",
            duration_seconds=45.2,
            rows_processed=95000,
            status="success")

# WRONG
print(f"Feature engineering done: 95000 rows in 45s")
```

---

### 16.8 Documentation Standards

Every module must have a module-level docstring describing the module's purpose in one or two sentences. Every public function must have a docstring with `Args:`, `Returns:`, and `Raises:` sections (Google style).

```python
# CORRECT
def compute_feature_importance(
    centroids: np.ndarray,
    feature_names: list[str],
    global_stats: dict[str, float],
) -> dict[int, list[tuple[str, float]]]:
    """Compute per-cluster feature importance as normalised centroid deviation.

    Args:
        centroids: Array of shape (n_clusters, n_features) with cluster centroid values.
        feature_names: List of feature names matching the column order in centroids.
        global_stats: Dict with keys "{feature}_mean" and "{feature}_std" for all features.

    Returns:
        Dict mapping cluster_id to a list of (feature_name, importance_score) tuples,
        sorted by importance descending, limited to the top 5 features per cluster.

    Raises:
        ValueError: If centroids shape does not match len(feature_names).
    """
    ...
```

---

## COMPLETION SUMMARY

╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌
Master Specification complete ✅  (all decisions resolved)
╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌
Saved to: .claude/specs/master-specification.md
Primary source: .claude/spec-source.md (both documents merged)
Sections completed: 16
Total F-XX requirements defined: 37 (F-01 through F-33, F-18 split into F-18a/b/c)
Total risks identified: 14
Open questions: 7 raised → 7 resolved (Section 15)
Total architectural decisions made: 11
  — Redis 7 (not 5.0)
  — spec-source.md table names canonical for DDL/ORM
  — ML matrix stays at 46 features; 4 extra nl_* flags as metadata
  — Airflow in requirements/airflow.txt (not base.txt); pin 2.9.3
  — MLflow artifact store: local filesystem for dev; MinIO path for production
  — Phase numbering: spec-source.md 15-phase roadmap is authoritative
  — CLAUDE.md updated to reflect all resolved decisions
  — feature_store DDL extra columns defined (Section 15 Q2)
  — Table naming reconciliation (Section 15 Q6)
  — Cold-start rules loaded from config (base.yaml cold_start.rules)
  — Propensity scores are derived formulas, NOT supervised models
╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌
Next step: CLAUDE.md updated. requirements/airflow.txt created.
Phase 2 (database-schema) can proceed — all schema decisions are locked.
╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌
