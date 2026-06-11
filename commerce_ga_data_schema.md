# Commerce GA Data — Table Schema
**Domain:** Commerce  
**Table Name:** `commerce_ga_data`  
**Source:** Subhatosh Maji (Team Shared)  
**Last Updated:** June 2026

---

## Table Overview

The `commerce_ga_data` table contains **Google Analytics behavioral data** scoped specifically to commerce pages on NYPost properties. It tracks how readers arrive at and interact with commerce content — pageviews, outbound affiliate clicks, traffic sources, and geographic data — before a transaction occurs.

**Relationship to `commerce_sales_data`:** This table captures the **top of the commerce funnel** (traffic + clicks), while `commerce_sales_data` captures the **bottom of the funnel** (orders + revenue). They can be joined via `page_url` / `clean_page_url` and `date` for full funnel analysis.

**Primary Use:** Commerce agent queries — traffic source analysis, outbound click tracking, content performance, UTM campaign attribution, geographic audience insights.

---

## Complete Column Reference

| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| `clean_page_url` | varchar | The cleaned article/page URL with protocol and query parameters removed. Use this for joins — more reliable than raw `page_url`. |
| `date` | varchar | The date the transaction or interaction occurred. |
| `default_channel_grouping` | varchar | Automated GA classification bucketing traffic into broad categories: Organic Search, Paid Search, Social, or Direct. |
| `hostname` | varchar | Standardized brand name for consistent reporting across sources. |
| `outbound_clicks` | bigint | Count of clicks on affiliate links (e.g., "Buy Now" buttons for Amazon or Walmart) that take the reader off the NYPost site to a retailer. |
| `page_url` | varchar | The specific raw web address of the article. |
| `pageviews` | bigint | Total number of times a commerce page was loaded or reloaded. |
| `region` | varchar | Geographic location of the viewer (Country, State, or City). |
| `utm_campaign` | varchar | Identifies the specific marketing push or theme driving the traffic. |
| `utm_medium` | varchar | Identifies the vehicle or type of link used (e.g., social, email, cpc for paid ads, or referral). |
| `utm_source` | varchar | Identifies the platform sending the traffic (e.g., facebook, google, twitter, or internal_recirc). |

---

## Key Metrics Columns

| Column | Type | Business Use |
|--------|------|-------------|
| `pageviews` | bigint | **Volume metric** — how much traffic commerce content receives |
| `outbound_clicks` | bigint | **Engagement metric** — readers clicking through to retailers |

**Derived metric (calculate from both tables):**
```sql
-- Click-through rate on commerce content
SELECT 
    clean_page_url,
    SUM(outbound_clicks)::float / NULLIF(SUM(pageviews), 0) AS click_through_rate
FROM commerce_ga_data
GROUP BY clean_page_url
ORDER BY click_through_rate DESC;
```

---

## UTM Parameters Decoded

UTM parameters identify exactly where traffic came from and which campaign drove it.

| Column | What It Tells You | Example Values |
|--------|------------------|----------------|
| `utm_source` | The platform that sent the traffic | `facebook`, `google`, `twitter`, `internal_recirc` |
| `utm_medium` | The type of link/channel used | `social`, `email`, `cpc`, `referral` |
| `utm_campaign` | The specific campaign or theme | campaign names, seasonal pushes |

**Combined example:** A row with `utm_source = 'facebook'`, `utm_medium = 'social'`, `utm_campaign = 'blackfriday2025'` means the reader came from a Black Friday Facebook post.

---

## Traffic Channel Reference

The `default_channel_grouping` values (set by Google Analytics):

| Value | Meaning |
|-------|---------|
| `Organic Search` | Reader found content via Google/Bing search naturally |
| `Paid Search` | Reader came via a paid search ad (Google Ads etc.) |
| `Social` | Reader came from a social platform (Facebook, Twitter, etc.) |
| `Direct` | Reader typed URL directly or no referrer data |
| `Referral` | Reader came from another website linking to NYPost |
| `Email` | Reader came from an email/newsletter link |

---

## Join Strategy with commerce_sales_data

These two tables form the **complete commerce funnel**:

```
commerce_ga_data          commerce_sales_data
(Traffic + Clicks)   →    (Orders + Revenue)
     pageviews                  orders
  outbound_clicks               sale
                                commission

Join on: clean_page_url = page_url AND date
```

```sql
-- Full funnel: traffic → clicks → revenue per article
SELECT 
    g.clean_page_url,
    SUM(g.pageviews)          AS total_pageviews,
    SUM(g.outbound_clicks)    AS total_clicks,
    SUM(s.orders)             AS total_orders,
    SUM(s.sale)               AS total_revenue,
    SUM(s.commission)         AS total_commission
FROM commerce_ga_data g
LEFT JOIN commerce_sales_data s 
    ON g.clean_page_url = s.page_url 
    AND g.date = s.date::varchar
GROUP BY g.clean_page_url
ORDER BY total_revenue DESC;
```

---

## Sample Business Questions This Table Answers

- "Which traffic source drives the most outbound clicks to retailers?"
- "What is the click-through rate on our Amazon content this week?"
- "Which UTM campaign is generating the most commerce pageviews?"
- "What region has the highest commerce content engagement?"
- "How much organic search traffic are our commerce pages getting?"
- "Which articles have high pageviews but low outbound clicks?" *(content optimization)*
- "How does social vs email traffic convert to affiliate clicks?"

---

## Knowledge Layer YAML (For Schema Injector)

```yaml
table_name: commerce_ga_data
domain: commerce
description: >
  Google Analytics behavioral data scoped to commerce pages on NYPost properties.
  Tracks top-of-funnel activity: pageviews, outbound affiliate clicks, traffic
  sources (UTM), channel groupings, and geographic data. Pairs with
  commerce_sales_data for full funnel analysis.
grain: one row per page + date + traffic source combination
join_key: clean_page_url (join to commerce_sales_data.page_url) + date

key_metrics:
  - pageviews: Traffic volume to commerce content
  - outbound_clicks: Affiliate link clicks leaving NYPost to retailers

join_with:
  - table: commerce_sales_data
    on: "clean_page_url = page_url AND date"
    use_for: Full funnel analysis (traffic → revenue)

always_note:
  - Use clean_page_url (not page_url) for joins — protocol and params stripped
  - default_channel_grouping is GA-automated, not manually tagged
  - outbound_clicks = reader left NYPost site to go to Amazon/Walmart/etc.
  - utm_source 'internal_recirc' means traffic from within NYPost itself
```

---

*Document generated from schema shared by Subhatosh Maji. Add to `knowledge_layer/tables/commerce_ga_data.yaml` in the project repo.*
