# Commerce Agent — Sample Questions & Few-Shot Examples
**Domain:** Commerce  
**Source:** Subhatosh Maji (Monday 8:23 AM)  
**Purpose:** Few-shot prompt examples + chatbot testing + demo script  
**Last Updated:** June 2026

---

## How to Use This Document

1. **Few-shot examples** — Pick 2-3 questions per category and add them to `knowledge_layer/few_shot_examples/commerce_examples.yaml` so the SQL generator knows how to handle each query pattern
2. **Demo script** — Use these questions during the demo to show the chatbot's range
3. **Test cases** — Run every question against the pipeline to validate SQL correctness before demo

---

## Category 1: Revenue & Sales Performance

*Primary tables: `commerce_sales_data` — columns: `sale`, `commission`, `orders`, `date`, `fiscal_quarter`*

### From Subhatosh (Original)
1. How did our total commerce revenue for Black Friday in 2025 compare to 2026?
2. What were the top three highest-grossing content categories during the last quarter?
3. Can you give me a quick summary of yesterday's total commerce conversion and average order value?
4. Could you pull the total revenue, clicks, and conversion rate for this article?

### Additional Questions
5. What is our total commerce revenue month-to-date vs the same period last month?
6. Which fiscal quarter had the highest total sales this year?
7. What is the average order value across all merchants this week?
8. How has our daily revenue trended over the last 30 days?
9. What percentage of our revenue comes from Amazon vs other networks?
10. Show me total commission earned per affiliate network this quarter.
11. What was our best single-day revenue in the last 90 days and what drove it?
12. How does Prime Day revenue compare to Black Friday revenue historically?

---

## Category 2: Article & Content Performance

*Primary tables: `commerce_sales_data` + `commerce_ga_data` — join on `page_url` + `date`*

### From Subhatosh (Original)
13. Which article published in the last 7 days has generated the most affiliate revenue?
14. What is the average conversion rate for our "best overall" product roundup articles this month?
15. Show me the top performing articles for this merchant over the last 30 days.

### Additional Questions
16. Which 5 articles have the highest click-through rate this week?
17. What are the top 10 articles by total revenue in the last 30 days?
18. Which evergreen articles are still driving consistent revenue this month?
19. Show me articles with high pageviews but low outbound clicks — potential optimization targets.
20. Which author's articles generate the most affiliate revenue on average?
21. What is the revenue per pageview for our top 20 commerce articles?
22. Which articles published more than 6 months ago are still in the top 20 by revenue?
23. Show me the content categories that have the highest conversion rate this month.
24. What is the average time between article publication and first affiliate click?

---

## Category 3: Merchant & Product Analysis

*Primary tables: `commerce_sales_data` — columns: `merchant_name`, `product_name`, `brand`, `asin_category`, `orders`, `sale`*

### From Subhatosh (Original)
25. Show me the top performing articles for this merchant over the last 30 days.

### Additional Questions
26. Which merchant drove the most revenue last month — Amazon, Nordstrom, or Hulu?
27. What are the top 5 product categories by total orders this quarter?
28. Show me all merchants where commission dropped more than 20% week over week.
29. Which Amazon product categories are generating the highest commission?
30. What is the revenue split between Streaming Category and Other merchants this month?
31. Which brands are driving the most outbound clicks from our content?
32. Show me the top 10 products by total sales this week.
33. How does Amazon transaction volume compare to all other networks combined?
34. Which merchant has the highest average order value?
35. What products from the last Prime Day are still selling?

---

## Category 4: Traffic Source & UTM Attribution

*Primary tables: `commerce_ga_data` — columns: `default_channel_grouping`, `utm_source`, `utm_medium`, `utm_campaign`, `outbound_clicks`, `pageviews`*

### From Subhatosh (Original)
36. How does commerce revenue from organic search compare to social media referrals for this category?
37. What is the conversion rate of users coming from our weekly email?

### Additional Questions
38. Which traffic source drives the most outbound clicks to retailers this month?
39. What percentage of our commerce pageviews come from organic search vs paid?
40. Which UTM campaign drove the highest affiliate revenue last month?
41. Show me the click-through rate breakdown by default channel grouping this week.
42. How much commerce traffic are we getting from internal recirculation vs external sources?
43. Which social platform (Facebook, Twitter, etc.) drives the most commerce clicks?
44. What is the revenue per visit for email traffic vs organic search traffic?
45. Which campaign has the best conversion rate this quarter?
46. Show me week-over-week change in organic search traffic to commerce pages.
47. How does paid search traffic convert compared to organic for Amazon products?

---

## Category 5: Placement & Widget Performance

*Primary tables: `commerce_sales_data` — columns: `link_placement_subid`, `content_type_subid`, `transaction_type`, `click`, `orders`, `sale`*

### From Subhatosh (Original)
48. Could we track the performance and CTR for this module on the homepage?
49. Which product widget layout is converting better?
50. What is the total revenue driven specifically by the inline text links vs. product buttons this week?

### Additional Questions
51. What is the click-through rate for TXL (text links) vs BTNL (button links) this month?
52. Which placement type generates the highest revenue per click?
53. Show me the conversion rate breakdown by link placement type.
54. How does homepage module performance compare to in-article placements?
55. Which content type (SAL article vs NL newsletter) drives more affiliate revenue?
56. What is the average order value for CPA transactions vs CPC transactions?
57. Show me the top 5 placements by total commission this week.
58. Which transaction type (CPC, CPA, Unknown) makes up the most of our revenue?

---

## Category 6: Newsletter & Email Commerce

*Primary tables: `commerce_sales_data` + `commerce_ga_data` — filter on `utm_medium = 'email'` or `content_type_subid = 'NL'`*

### From Subhatosh (Original)
59. Could we see the newsletter commerce performance for newsletters sent on a specific date?
60. Which newsletter campaign drove the highest affiliate revenue last month?
61. What is the conversion rate of users coming from our weekly email?

### Additional Questions
62. How much revenue did our newsletter links generate last week?
63. Which newsletter send date had the highest same-day affiliate revenue?
64. What is the average commission per newsletter click vs article click?
65. Show me the top 5 merchants featured in newsletters by resulting revenue.
66. How does newsletter commerce revenue trend week over week?
67. Which products featured in newsletters have the highest conversion rate?
68. What percentage of total commerce revenue comes from newsletter traffic?

---

## Category 7: Geographic & Audience Analysis

*Primary tables: `commerce_ga_data` — columns: `region`, `pageviews`, `outbound_clicks`*

### Additional Questions
69. Which US states drive the most commerce pageviews?
70. What is the outbound click rate by country for our top commerce content?
71. Show me the top 10 cities by commerce engagement this month.
72. How does commerce performance differ between US and international traffic?
73. Which regions have the highest click-through rate on affiliate content?

---

## Category 8: Time & Fiscal Period Comparisons

*Primary tables: `commerce_sales_data` — columns: `fiscal_year`, `fiscal_quarter`, `fiscal_month`, `date`*

### Additional Questions
74. How does Q1 FY2026 revenue compare to Q1 FY2025?
75. What is our month-over-month revenue growth rate for the last 6 months?
76. Show me the revenue trend for each fiscal month this year.
77. Which day of the week consistently drives the most commerce revenue?
78. What is our year-to-date total revenue vs the same period last fiscal year?
79. Show me the seasonality pattern — which fiscal months are strongest for commerce?
80. How did holiday season (fiscal months 5-6) perform vs rest of year?

---

## Category 9: Website / Brand Split

*Primary tables: `commerce_sales_data` — columns: `website_name`, `website_subid`, `hostname`*

### Additional Questions
81. How does NYPost commerce revenue compare to PageSix and Decider?
82. Which brand (nyp, dec, pagesix) has the highest conversion rate?
83. Show me the revenue breakdown by website brand this quarter.
84. Which brand drives the most Amazon-specific revenue?
85. How does click volume differ between NYPost and Decider content?

---

## Category 10: Anomaly & Insight Questions

*These test the chatbot's ability to surface insights, not just return data*

### Additional Questions
86. Which merchants have shown the biggest revenue drop in the last 7 days?
87. Are there any articles with zero clicks but high pageviews this week?
88. Which content categories are underperforming compared to last month?
89. Show me any days in the last 30 days where revenue was unusually low.
90. Which affiliate network has improved the most in conversion rate over the last quarter?

---

## Demo Script — Recommended Question Sequence

Use this order for the live demo to show increasing complexity:

```
1. "Can you give me a quick summary of yesterday's total commerce revenue?"
   → Simple aggregation, single table, single day

2. "Which article published in the last 7 days generated the most affiliate revenue?"
   → Filter + aggregation + ordering

3. "How did our Black Friday 2025 revenue compare to 2026?"
   → Year-over-year comparison, date filtering

4. "What is the total revenue driven by inline text links vs product buttons this week?"
   → Grouping by link_placement_subid, business context needed

5. "How does commerce revenue from organic search compare to social media for this quarter?"
   → Multi-table join (commerce_ga_data + commerce_sales_data), channel grouping
```

---

## Columns Required Per Category (Quick Reference)

| Category | Tables Needed | Key Columns |
|----------|--------------|-------------|
| Revenue & Sales | `commerce_sales_data` | `sale`, `commission`, `orders`, `date` |
| Article Performance | Both tables (join) | `page_url`, `pageviews`, `outbound_clicks`, `sale` |
| Merchant/Product | `commerce_sales_data` | `merchant_name`, `brand`, `product_name`, `asin_category` |
| Traffic/UTM | `commerce_ga_data` | `utm_source`, `utm_medium`, `utm_campaign`, `default_channel_grouping` |
| Placement/Widget | `commerce_sales_data` | `link_placement_subid`, `content_type_subid`, `transaction_type` |
| Newsletter | Both tables | `utm_medium='email'`, `content_type_subid='NL'` |
| Geographic | `commerce_ga_data` | `region`, `pageviews`, `outbound_clicks` |
| Fiscal/Time | `commerce_sales_data` | `fiscal_year`, `fiscal_quarter`, `fiscal_month` |
| Brand Split | `commerce_sales_data` | `website_name`, `website_subid` |

---

*Total questions: 90 — 14 from Subhatosh (original) + 76 additional. Use for few-shot examples, test cases, and demo preparation.*
