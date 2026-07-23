-- one row per VIN | layer: gold | schema confirmed: True
CREATE TABLE IF NOT EXISTS aftersales_prod.gold_enterprise_experience_engine_e3_gmna.e3_vin_detail (
  vin STRING,
  brand STRING,
  model_name STRING,
  model_year BIGINT,
  model_trim STRING,
  vehicle_type STRING,
  body_style STRING,
  vehicle_segment STRING,
  vehicle_category STRING,
  t1_2_program_flag STRING,
  build_date STRING
) USING DELTA;

-- one row per individual | layer: gold | schema confirmed: True
CREATE TABLE IF NOT EXISTS aftersales_prod.gold_enterprise_experience_engine_e3_gmna.e3_indiv_detail (
  individual_id STRING,
  loyalty_status STRING,
  loyalty_points BIGINT,
  first_purchase_date STRING,
  is_current_customer STRING
) USING DELTA;

-- one row per VIN | layer: gold | schema confirmed: True
CREATE TABLE IF NOT EXISTS marketing_prod.gold_customer_feature_store_gmna.vehicle_attributes (
  vin STRING,
  vehicle_mileage BIGINT,
  vehicle_segment STRING,
  body_style STRING,
  vehicle_category STRING,
  mileage_asof_date STRING
) USING DELTA;

-- one row per ownership record | layer: gold | schema confirmed: True
CREATE TABLE IF NOT EXISTS sales_prod.gold_vehicle_ownership_gmna.vehicle_ownership (
  ownership_id STRING,
  individual_id STRING,
  vin STRING,
  ownership_status STRING,
  ownership_sequence BIGINT,
  ownership_start_date STRING,
  ownership_end_date STRING,
  purchase_type STRING,
  dealer_id STRING
) USING DELTA;

-- one row per survey response | layer: silver | schema confirmed: True
CREATE TABLE IF NOT EXISTS aftersales_prod.silver_enterprise_experience_engine_e3_gmna.survey_hub_inmoment_us_vw (
  response_id STRING,
  individual_id STRING,
  vin STRING,
  survey_type STRING,
  survey_date STRING,
  nps_score BIGINT,
  nps_category STRING,
  csat_score BIGINT,
  verbatim_text STRING,
  dealer_id STRING,
  region STRING,
  region_scope STRING
) USING DELTA;

-- one row per survey response | layer: silver | schema confirmed: True
CREATE TABLE IF NOT EXISTS aftersales_prod.silver_enterprise_experience_engine_e3_gmna.survey_hub_inmoment_global_vw (
  response_id STRING,
  individual_id STRING,
  vin STRING,
  survey_type STRING,
  survey_date STRING,
  nps_score BIGINT,
  nps_category STRING,
  csat_score BIGINT,
  verbatim_text STRING,
  dealer_id STRING,
  region STRING,
  region_scope STRING
) USING DELTA;

-- one row per individual | layer: silver | schema confirmed: True
CREATE TABLE IF NOT EXISTS customer_prod.silver_individual_gmna.acxiom_survived_individual_demographic (
  individual_id STRING,
  customer_age_group STRING,
  age_range STRING,
  household_income_band STRING,
  is_current_customer STRING,
  state STRING
) USING DELTA;

-- one row per individual | layer: silver | schema confirmed: True
CREATE TABLE IF NOT EXISTS customer_prod.silver_individual_gmna.consolidated_customer (
  individual_id STRING,
  region STRING,
  gender_code STRING,
  zip_code STRING,
  num_children BIGINT,
  children_flag STRING
) USING DELTA;

-- one row per support case | layer: gold(proposed) | schema confirmed: False
CREATE TABLE IF NOT EXISTS t1_2_dev.gold_cx.get_help_case (
  case_id STRING,
  individual_id STRING,
  vin STRING,
  case_type STRING,
  call_driver STRING,
  channel STRING,
  case_open_ts STRING,
  case_close_ts STRING,
  days_to_close DOUBLE,
  closed_within_24h STRING,
  first_contact_resolution STRING,
  csat_score BIGINT,
  region STRING,
  case_month STRING
) USING DELTA;

-- one row per content interaction | layer: gold(proposed) | schema confirmed: False
CREATE TABLE IF NOT EXISTS t1_2_dev.gold_cx.content_engagement (
  engagement_id STRING,
  individual_id STRING,
  content_id STRING,
  content_title STRING,
  content_type STRING,
  channel STRING,
  engagement_ts STRING,
  engagement_depth_pct BIGINT,
  completed_flag STRING
) USING DELTA;

-- one row per training completion | layer: gold(proposed) | schema confirmed: False
CREATE TABLE IF NOT EXISTS t1_2_dev.gold_cx.training_participation (
  participation_id STRING,
  individual_id STRING,
  dealer_id STRING,
  training_id STRING,
  training_name STRING,
  training_date STRING,
  completed_flag STRING
) USING DELTA;

-- one row per CX intervention | layer: gold(proposed) | schema confirmed: False
CREATE TABLE IF NOT EXISTS t1_2_dev.gold_cx.action_log (
  action_id STRING,
  action_name STRING,
  case_type STRING,
  action_owner STRING,
  action_date STRING,
  action_status STRING,
  description STRING
) USING DELTA;
