# Commerce Sales Data — Table Schema
**Domain:** Commerce  
**Table Name:** `commerce_sales_data`  
**Source:** Subhatosh Maji (Team Shared)  
**Last Updated:** June 2026

---

## Table Overview

The `commerce_sales_data` table contains affiliate and commerce transaction data for NYPost's commerce team. It tracks clicks, orders, commissions, and sales across multiple affiliate networks (Amazon, Impact, CJ, Rakuten, LS, VividSeats, etc.) enriched with product, content, and fiscal metadata.

**Primary Use:** Commerce agent queries — affiliate performance, revenue tracking, merchant analysis, content-to-commerce attribution.

---

## Complete Column Reference

| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| `asin` | varchar | Extracted 10-digit Amazon Standard Identification Number. Defaults to 'Others' for non-Amazon sources. |
| `asin_category` | varchar | Product category enriched from the ASIN master table. |
| `authors_updated` | varchar | Cleaned author field resolving specific aliases (e.g., mapping 'rkingnyp' to 'Dana Wood'). |
| `brand` | varchar | Product brand name enriched from the ASIN master table. |
| `category` | varchar | Identifies if the merchant belongs to 'Streaming Category' or 'Other'. |
| `click` | double | Total count of clicks recorded. |
| `commission` | double | Net commission earned from the sale. |
| `content_type_subid` | varchar | Extracted content category from SubID (e.g., 'SAL', 'NL'). |
| `date` | date | The date the transaction or interaction occurred. |
| `event` | varchar | Significant commerce events (e.g., holiday sales) joined by date. |
| `evergreen_articles_ind` | boolean | TRUE if the article URL exists in the evergreen articles master list. |
| `fiscal_month` | varchar | Fiscal month index (July = 1, August = 2, etc.). |
| `fiscal_quarter` | varchar | Fiscal quarter (Q1–Q4) based on the July–June cycle. |
| `fiscal_year` | varchar | Fiscal year based on a July–June cycle. |
| `hostname` | varchar | Standardized brand name for consistent reporting across sources. |
| `is_amazon_data` | boolean | TRUE if the link is identified as an Amazon-sourced transaction. |
| `is_blackfriday` | boolean | TRUE if the content relates to the Black Friday shopping event. |
| `is_primeday` | boolean | TRUE if the content or date relates to the Amazon Prime Day event. |
| `link` | varchar | The specific outbound affiliate link clicked. |
| `link_placement_subid` | varchar | Extracted placement location from SubID (e.g., 'TXL', 'BTNL'). |
| `merchant_name` | varchar | The name of the retailer/merchant (e.g., Nordstrom, Hulu, Amazon). |
| `ncaurl_ind` | boolean | TRUE if the article URL exists in the NCAURL master list. |
| `network_name` | varchar | The affiliate network (e.g., Impact, CJ, Rakuten, Amazon, LS). |
| `orders` | double | Total count of successful transactions/orders. |
| `page_url` | varchar | The cleaned article/page URL (protocol and query parameters removed). |
| `primary_author` | varchar | The first author listed in the cleaned authors string. |
| `primary_tag` | varchar | The primary content tag assigned to the article in GA. |
| `primary_tag_updated` | varchar | Cleaned primary tag with fallbacks to network name if missing. |
| `product_group` | varchar | Product grouping enriched from the ASIN master table. |
| `product_name` | varchar | The name of the product involved in the transaction. |
| `pub_date` | date | The original publication date of the article from GA metadata. |
| `sale` | double | Gross sales volume (Revenue). |
| `source` | varchar | The data origin (e.g., 'TRX', 'Amazon', 'VividSeats'). |
| `sub_id` | varchar | The raw tracking ID string (e.g., 'nyp-SAL-TXL--'). |
| `title` | varchar | Specific product title enriched from the ASIN master table. |
| `transaction_type` | varchar | Categorization of the payout model (CPC, CPA, or Unknown). |
| `valid_sub_id` | boolean | TRUE if the SubID contains at least one recognized brand, content type, or placement code. |
| `website_name` | varchar | The high-level brand (NY Post, PageSix, Decider) based on URL patterns. |
| `website_subid` | varchar | Extracted brand code from SubID (e.g., 'nyp', 'dec'). |

---

## Key Metrics Columns

| Column | Type | Business Use |
|--------|------|-------------|
| `sale` | double | **Primary revenue metric** — gross sales volume |
| `commission` | double | Net commission earned — profitability metric |
| `orders` | double | Transaction count — volume metric |
| `click` | double | Click count — engagement/funnel top metric |

---

## Key Dimension Columns

| Column | Business Use |
|--------|-------------|
| `merchant_name` | Filter/group by retailer (Amazon, Nordstrom, Hulu...) |
| `network_name` | Filter by affiliate network (Impact, CJ, Rakuten, Amazon, LS) |
| `transaction_type` | Filter by payout model (CPC, CPA, Unknown) |
| `website_name` | Split by NYPost brand (NY Post, PageSix, Decider) |
| `date` | Time-series analysis |
| `fiscal_year` / `fiscal_quarter` / `fiscal_month` | Fiscal period reporting (July–June cycle) |

---

## Important Boolean Flags

| Column | Meaning |
|--------|---------|
| `is_amazon_data` | Isolate Amazon transactions only |
| `is_blackfriday` | Filter to Black Friday period |
| `is_primeday` | Filter to Amazon Prime Day period |
| `evergreen_articles_ind` | Identify evergreen content driving commerce |
| `ncaurl_ind` | Articles in NCAURL master list |
| `valid_sub_id` | Quality flag — SubID is properly formatted |

---

## SubID Decoded

The `sub_id` field (e.g., `'nyp-SAL-TXL--'`) encodes multiple dimensions:

| Extracted Column | What It Captures | Example Values |
|-----------------|-----------------|----------------|
| `website_subid` | Brand code | `nyp`, `dec`, `pagesix` |
| `content_type_subid` | Content type | `SAL` (article sale), `NL` (newsletter) |
| `link_placement_subid` | Placement location | `TXL` (text link), `BTNL` (button link) |

---

## Fiscal Calendar Note

NYPost uses a **non-standard fiscal year (July–June cycle)**:

| Fiscal Month | Calendar Month |
|-------------|----------------|
| 1 | July |
| 2 | August |
| 3 | September |
| ... | ... |
| 12 | June |

Always use `fiscal_year`, `fiscal_quarter`, `fiscal_month` for period-over-period reporting. Do NOT use calendar year groupings for financial comparisons.

---

## Sample Business Questions This Table Answers

- "What was our total commission revenue last fiscal quarter?"
- "Which merchant drove the most orders this month?"
- "How did Black Friday sales compare to Prime Day?"
- "Which affiliate network has the highest conversion rate?"
- "What is the top performing article by revenue this week?"
- "Show me CPA vs CPC transaction breakdown for Q2"
- "Which website (NYPost vs PageSix vs Decider) drives the most commerce?"

---

## Knowledge Layer YAML (For Schema Injector)

```yaml
table_name: commerce_sales_data
domain: commerce
description: >
  Affiliate and commerce transaction table. One row per click/transaction event.
  Tracks sales, commissions, orders, and clicks across all affiliate networks
  enriched with product, content, fiscal, and event metadata.
grain: one row per transaction/click event
join_key: none (standalone commerce fact table, link via page_url or date)
fiscal_calendar: July-June cycle (fiscal_month 1 = July)

key_metrics:
  - sale: Gross revenue
  - commission: Net commission earned
  - orders: Transaction count
  - click: Click volume

always_note:
  - Fiscal year runs July-June, not January-December
  - is_amazon_data flag separates Amazon vs other network transactions
  - valid_sub_id = FALSE rows have unreliable attribution data
  - For revenue queries, use SUM(sale); for profitability use SUM(commission)
```

---

*Document generated from schema shared by Subhatosh Maji. Add to `knowledge_layer/tables/commerce_sales_data.yaml` in the project repo.*
