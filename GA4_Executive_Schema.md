# Executive GA4 Event Schema
**Source:** GA4 sheet (Excel workbook)  
**Events Covered:** `page_view`, `ux_engagement`  
**Last Updated:** June 2026  
**Purpose:** Database schema reference for Executive domain GA4 raw event data

---

## Table Overview

This schema documents raw GA4 (Google Analytics 4) event-level tracking data captured on NYPost properties. Unlike the pre-aggregated `beat_*` tables in the Editorial-Executive domain, this is **granular event-level data** — every parameter fired on every `page_view` and `ux_engagement` hit.

**Two events documented, identical parameter sets:**
- `page_view` — fires when a user loads/views a page
- `ux_engagement` — fires on qualifying engagement actions (the GA4 "engaged session" event)

Both events carry the exact same 77 parameters. This table is the raw/granular layer beneath the `beat_*` aggregated tables — useful for any query needing parameter-level detail (ad blocker status, video player behavior, Zephr paywall state, etc.) that the pre-aggregated tables don't expose.

**Grain:** One row per event per parameter (long/tall format) OR one row per event with all parameters as columns (wide format), depending on how the warehouse materializes it. Confirm actual table structure with source team before building synthetic data.

---

## Complete Parameter Reference (Alphabetical)

| Parameter Key | Data Type | Description |
|--------------|-----------|-------------|
| `ad_blocker` | String | Tracks whether an ad blocker is active for the visitor session. |
| `amp_hostname` | String | The hostname for users accessing via Accelerated Mobile Pages (AMP). |
| `aqfer_puu` | String | Unique visitor identifier token used by the Aqfer integration. |
| `batch_ordering_id` | Integer | A sequential identifier tracking event order inside a batched request payload. |
| `batch_page_id` | String | Unique ID linking multiple tracking hits belonging to the same page view action. |
| `byline` | String | The author name or editorial credit line associated with the content asset. |
| `campaign` | String | The marketing campaign name captured via standard UTM parameters. |
| `campaign_id` | String | The explicit tracker ID associated with an active marketing campaign. |
| `canonical_url` | String | The primary authoritative URL of the web page used for SEO classification. |
| `commerce_links` | String | Tracks specific details or lists of commercial links present on the page. |
| `contains_commerce_link` | String | Flag indicating if the page layout contains commercial or affiliate hyperlinks. |
| `content` | String | The marketing campaign content parameter used to track specific ad creatives. |
| `debug_mode` | Integer | Flag indicating if the event was generated in a preview/debug context (1 for true). |
| `destination` | String | The external or target URL destination clicked by the user. |
| `display_flag` | String | A tracking state parameter used to flag conditional element rendering. |
| `display_tag` | String | Specific ad or promotional campaign tag active on the user interface. |
| `display_template` | String | The specific layout template identifier utilized to render the web page content. |
| `engaged_session_event` | Integer | Flag defining if the single hit satisfied GA4 active session engagement criteria. |
| `engagement_time_msec` | Integer | The duration of user interaction on the active asset measured in milliseconds. |
| `entrances` | Integer | Flag indicating if the current page view is the landing entry point of the session. |
| `firebase_conversion` | Integer | Identifies if this page view represents a designated conversion point. |
| `ga_aut_id` | String | Custom authenticated identity string for logged-in tracking. |
| `ga_session_id` | Integer | The unique tracking session token automatically assigned by Google Analytics. |
| `ga_session_number` | Integer | The count representing the current session index sequence for this specific user. |
| `gclid` | String | The Google Click Identifier token used to tie Google Ads conversions. |
| `groups` | String | Categorized segment grouping arrays associated with the active user profile or item. |
| `has_brightcove_player` | String | Indicates if a Brightcove media player instance is loaded on the asset. |
| `has_comments` | String | Boolean flag tracking if comments are enabled or populated for this post. |
| `has_sendtonews_player` | String | Indicates if a SendToNews video player is present on the layout. |
| `ignore_referrer` | String | Flag to declare whether the specific referrer traffic should be filtered from channel credit. |
| `medium` | String | The marketing medium identifier parameter (e.g. cpc, email, organic). |
| `ncg_id` | String | National Content Group profile grouping index code. |
| `ncg_sp_id` | String | National Content Group site partner tracking token. |
| `newsbreak_domain_section` | String | Custom segment path tag representing traffic origin from the NewsBreak platform. |
| `original_title` | String | The unoptimized original editorial headline of the web post. |
| `outbrain_widgets` | String | Tracks layout presence and activity of embedded Outbrain recommendations modules. |
| `page_location` | String | The full standard URL path of the active webpage layout. |
| `page_referrer` | String | The prior URL path visited before executing navigation to the current page. |
| `page_title` | String | The text captured from the document title element of the webpage layout. |
| `page_type` | String | The overall categorical structural classification of the layout page. |
| `photo_display_type` | String | Tracks structural rendering configuration utilized for gallery displays. |
| `post_id` | String | The internal unique database identifier index for the page post content. |
| `primary_tag` | String | The main keyword category tag configured for semantic content indexing. |
| `publish_date` | String | The formal calendar date when the article content was made live. |
| `publish_time` | String | The exact timestamp recorded at the time of asset publication. |
| `recirculation` | String | Custom identifier field tracking page elements handling traffic recirculation. |
| `redesign_viewer` | String | Tracks if the active visitor is being served a new template redesign layout. |
| `screen` | String | The descriptive classification for app screens or custom screen dimensions. |
| `section` | String | The primary core category division of the site editorial architecture. |
| `session_engaged` | String | Indicates if the user session has qualified for active engagement criteria. |
| `short_title` | String | An alternate short structural variant headline for the content post. |
| `slide_number` | Integer | The exact sequential index number of the image slide active in a gallery. |
| `slide_total` | Integer | The total cumulative count of slides populated inside a media gallery deck. |
| `source_page` | String | The relative site path representing where the internal interaction path began. |
| `source_page_type` | String | The content structural template classification of the origin page. |
| `source_position` | Integer | The sequential index or position coordinates of the interacted component asset. |
| `source_unit` | String | The layout item code representing the structural widget origin container. |
| `subsection` | String | The secondary sub-category classification of the editorial site map. |
| `tags` | String | The array or list of semantic meta tags bound to the content document. |
| `term` | String | The explicit search keyword query variable parsed from marketing campaigns. |
| `title` | String | The primary headline title label associated with the target interaction context. |
| `video_embed_cplocation` | String | Positional deep link attribute context representing where the video asset resides. |
| `video_embed_location` | String | The targeted layout container string where the video frame is embedded. |
| `video_id` | String | The unique asset key identifying the embedded video player file track. |
| `video_player_ad_status` | String | Tracks if a commercial advertisement is currently streaming inside the video unit. |
| `video_player_autoplay_status` | String | Identifies if video execution was started automatically or through user choice. |
| `video_player_name` | String | The developer or vendor identity brand profile of the media player. |
| `video_player_type` | String | The structural class category of the streaming video media player framework. |
| `video_player_video_start_count` | Integer | Incremental metrics log measuring total playback initiations for the video item. |
| `video_publish_date` | String | The core calendar publication date of the specific video asset. |
| `video_tags` | String | The semantic key phrase metadata tags bound to the video item track. |
| `word_count` | Integer | The cumulative absolute text word count comprising the main article asset. |
| `zephr_credits` | Integer | The ongoing remaining user wallet credits balance tracked via Zephr paywall. |
| `zephr_status` | String | The active membership access tier or state status returned from Zephr profile. |
| `zephr_test_groups` | String | The experiment variant target bucket assigned to the session by Zephr optimization. |
| `zephr_tracking_id` | String | The specific identity tracing token generated for meter control via Zephr server. |

**Total: 77 parameters per event**

---

## Parameters by Functional Category

### Identity & Session Tracking
| Parameter | Type | Purpose |
|-----------|------|---------|
| `ga_session_id` | Integer | Unique GA4 session token |
| `ga_session_number` | Integer | Session sequence count per user |
| `ga_aut_id` | String | Logged-in user identity |
| `aqfer_puu` | String | Aqfer persistent unique user ID |
| `batch_ordering_id` | Integer | Event order within batch |
| `batch_page_id` | String | Links hits to same page view |
| `engaged_session_event` | Integer | GA4 active session flag |
| `session_engaged` | String | Engagement qualification flag |
| `entrances` | Integer | Landing page flag |

### Engagement & Conversion
| Parameter | Type | Purpose |
|-----------|------|---------|
| `engagement_time_msec` | Integer | Time spent on asset (ms) |
| `firebase_conversion` | Integer | Conversion point flag |
| `debug_mode` | Integer | Preview/debug context flag |

### Marketing Attribution (UTM)
| Parameter | Type | Purpose |
|-----------|------|---------|
| `campaign` | String | UTM campaign name |
| `campaign_id` | String | Campaign tracker ID |
| `medium` | String | UTM medium (cpc, email, organic) |
| `term` | String | UTM search keyword |
| `content` | String | UTM ad creative identifier |
| `gclid` | String | Google Ads click ID |
| `ignore_referrer` | String | Referrer exclusion flag |
| `source_page` | String | Internal traffic origin path |
| `source_page_type` | String | Origin page template type |
| `source_position` | Integer | Component position on origin page |
| `source_unit` | String | Widget container code on origin page |

### Content Identity & Metadata
| Parameter | Type | Purpose |
|-----------|------|---------|
| `post_id` | String | CMS unique article ID |
| `page_title` | String | Document title |
| `original_title` | String | Pre-optimization headline |
| `short_title` | String | Alternate short headline |
| `title` | String | Primary interaction headline |
| `byline` | String | Author/columnist name |
| `primary_tag` | String | Main semantic keyword tag |
| `tags` | String | Full semantic tag array |
| `section` | String | Top-level editorial category |
| `subsection` | String | Secondary editorial category |
| `word_count` | Integer | Article word count |
| `publish_date` | String | Article publish date |
| `publish_time` | String | Article publish timestamp |
| `canonical_url` | String | SEO authoritative URL |
| `page_location` | String | Full webpage URL |
| `page_referrer` | String | Previous page URL |
| `page_type` | String | Page layout classification |
| `display_template` | String | Rendering template ID |
| `screen` | String | App/custom screen dimension label |
| `redesign_viewer` | String | New template A/B flag |
| `recirculation` | String | Traffic recirculation tracking |

### Commerce-Related (Cross-Domain Signal)
| Parameter | Type | Purpose |
|-----------|------|---------|
| `commerce_links` | String | Commercial link details on page |
| `contains_commerce_link` | String | Boolean-style commerce link flag |

*Note: These parameters bridge GA4 event data to the Commerce domain tables (`commerce_ga_data`, `commerce_sales_data`) — useful for joining engagement events to commerce outcomes.*

### Video Player Tracking
| Parameter | Type | Purpose |
|-----------|------|---------|
| `video_id` | String | Unique video asset key |
| `video_embed_location` | String | Video container placement |
| `video_embed_cplocation` | String | Deep-link positional context |
| `video_player_name` | String | Player vendor/brand |
| `video_player_type` | String | Player framework class |
| `video_player_ad_status` | String | Ad-currently-playing flag |
| `video_player_autoplay_status` | String | Autoplay vs manual start |
| `video_player_video_start_count` | Integer | Playback initiation count |
| `video_publish_date` | String | Video publication date |
| `video_tags` | String | Video semantic tags |
| `has_brightcove_player` | String | Brightcove player presence flag |
| `has_sendtonews_player` | String | SendToNews player presence flag |

### Photo Gallery Tracking
| Parameter | Type | Purpose |
|-----------|------|---------|
| `photo_display_type` | String | Gallery rendering config |
| `slide_number` | Integer | Current slide index |
| `slide_total` | Integer | Total slides in gallery |

### Zephr Paywall / Subscription Tracking
| Parameter | Type | Purpose |
|-----------|------|---------|
| `zephr_status` | String | Current membership access tier |
| `zephr_credits` | Integer | Remaining metered article credits |
| `zephr_test_groups` | String | A/B experiment bucket |
| `zephr_tracking_id` | String | Zephr identity/meter token |

### Ad & Monetization Context
| Parameter | Type | Purpose |
|-----------|------|---------|
| `ad_blocker` | String | Ad blocker active flag |
| `display_flag` | String | Conditional element render flag |
| `display_tag` | String | Active promo/ad tag |
| `outbrain_widgets` | String | Outbrain recommendation widget tracking |
| `groups` | String | Segment grouping array |

### Syndication / Distribution Partners
| Parameter | Type | Purpose |
|-----------|------|---------|
| `ncg_id` | String | National Content Group profile code |
| `ncg_sp_id` | String | NCG site partner token |
| `newsbreak_domain_section` | String | NewsBreak platform segment tag |
| `amp_hostname` | String | AMP-specific hostname |
| `has_comments` | String | Comments-enabled flag |

### Engagement Click Targets
| Parameter | Type | Purpose |
|-----------|------|---------|
| `destination` | String | Click-through target URL |

---

## Key Notes for Building This Database

**1. Event-Parameter structure:** GA4 natively stores data as event_name + repeated parameter key/value pairs (long format). If your warehouse has flattened this into a wide table (one column per parameter), each of the 77 parameters above becomes a column. Confirm which structure exists in your sandbox before writing DDL.

**2. Two events, shared schema:** Both `page_view` and `ux_engagement` use the identical 77-parameter set. In practice, certain parameters will be NULL/empty depending on event type (e.g., `engagement_time_msec` is far more meaningful on `ux_engagement` than `page_view`). When generating synthetic data, vary fill rates by event type realistically.

**3. Relationship to beat_* tables:** This raw event table is the source data that the pre-aggregated `beat_article_level_data`, `beat_direct_users_daily`, etc. tables are built from. Columns like `post_id`, `section`, `primary_tag`, `page_title`, `device` concepts, and `hostname`-equivalent fields map directly between this raw layer and the aggregated Editorial-Executive tables.

**4. Join keys to other domains:**
   - `post_id` → joins to `beat_article_level_data.post_id`, `sportsplus_editorial_insights.post_id`
   - `page_location` / `canonical_url` → joins to `commerce_ga_data.page_url` / `clean_page_url`
   - `campaign` / `campaign_id` / `medium` → joins to `sportsplus_editorial_marketing` UTM fields
   - `byline` → joins to `beat_article_level_data.authors`, `sportsplus_editorial_insights.byline`

**5. High-cardinality / PII caution:** `ga_aut_id` and `aqfer_puu` are user-identity tokens. Treat as PII-adjacent — apply the same blocked_columns guardrail treatment used for other identity fields in the RBAC layer, even though they're hashed/tokenized rather than raw email/name.

**6. Data type caution:** Several boolean-sounding fields (`has_comments`, `contains_commerce_link`, `ignore_referrer`, `session_engaged`) are typed as **String**, not Boolean, in this source — likely storing "true"/"false" or "1"/"0" as text. Preserve this typing when generating synthetic data rather than converting to native booleans, unless you confirm otherwise with the source team.

---

## Sample Business Questions This Table Answers

1. What percentage of pageviews on articles have an active ad blocker?
2. Which articles have the highest average engagement_time_msec?
3. How many sessions are landing directly on video content (entrances + video_id present)?
4. What's the autoplay vs manual-start ratio for video player engagement?
5. Which Zephr status tier (metered, subscriber, etc.) generates the most engaged sessions?
6. How many pageviews come through AMP hostnames vs standard hostnames?
7. Which campaign_id values are driving the most firebase_conversion events?
8. What's the comment-enabled vs comment-disabled engagement difference?
9. How does gallery slide_total correlate with total engagement_time_msec?
10. Which primary_tag values have the highest contains_commerce_link rate? *(cross-domain commerce signal)*

---

## Knowledge Layer YAML (For Schema Injector)

```yaml
table_name: ga4_executive_events
domain: executive
events_included:
  - page_view
  - ux_engagement
description: >
  Raw GA4 event-level tracking data with 77 parameters per event covering
  session identity, marketing attribution, content metadata, video/photo
  gallery interaction, Zephr paywall status, and ad/monetization context.
  This is the granular source layer beneath the aggregated beat_* tables.
grain: one row per event hit (or per event+parameter if stored long-format)
join_keys:
  - post_id: joins to beat_article_level_data, sportsplus_editorial_insights
  - page_location/canonical_url: joins to commerce_ga_data.page_url
  - campaign/campaign_id/medium: joins to sportsplus_editorial_marketing
  - byline: joins to beat_article_level_data.authors

pii_adjacent_columns:
  - ga_aut_id
  - aqfer_puu

always_note:
  - has_comments, contains_commerce_link, ignore_referrer, session_engaged 
    are typed as String, not native Boolean — likely "true"/"false" text
  - engagement_time_msec is most meaningful on ux_engagement events
  - Both page_view and ux_engagement share the identical 77-parameter schema
```

---

*Extracted from GA4 sheet, rows 1–149 (covering both page_view and ux_engagement event parameter blocks). Confirm long vs wide table structure with source team before finalizing DDL.*
