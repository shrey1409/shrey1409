"""
T1-2 Experience Agent — Synthetic Data Generator
=================================================
Purpose: produce a small, referentially-consistent, schema-faithful mock of the
Gold (and required Silver) tables so the team can build and test a Databricks
Genie space + Glean agent integration BEFORE Databricks access lands.

Design rules
------------
1. Schema-faithful, volume-tiny. Same catalog.schema.table names, same column
   names. When real access arrives you swap the source, not the code.
2. Referentially consistent. VIN and INDIVIDUAL_ID join across every table.
   Genie's entire value is joins; disconnected random tables prove nothing.
3. Distributions match the June 2026 deck (case mix, FCR, CSAT, NPS shape,
   Hardware Replacement 2,413 -> 11,998 ramp) so Genie answers can be
   sanity-checked against a number a stakeholder already believes.
4. Zero real PII. Everything is fabricated -> demoable with no Glenda approval.
5. SCHEMA is a single dict at the top. Column names are PROVISIONAL guesses.
   After `DESCRIBE TABLE`, correct them here only.

Usage
-----
    python generate_synthetic_data.py --out ./synthetic --individuals 150
    python generate_synthetic_data.py --out ./synthetic --format parquet

Output: one CSV/Parquet per table, plus create_tables.sql and a manifest.
"""

import argparse
import json
import os
import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

SEED = 42

# --------------------------------------------------------------------------
# TABLE REGISTRY  -- edit ONLY this block once real schemas are known
# --------------------------------------------------------------------------
TABLES = {
    # ---------- GOLD (productionise through these) ----------
    "e3_vin_detail": {
        "fqn": "aftersales_prod.gold_enterprise_experience_engine_e3_gmna.e3_vin_detail",
        "layer": "gold", "grain": "one row per VIN", "confirmed": True,
    },
    "e3_indiv_detail": {
        "fqn": "aftersales_prod.gold_enterprise_experience_engine_e3_gmna.e3_indiv_detail",
        "layer": "gold", "grain": "one row per individual", "confirmed": True,
    },
    "vehicle_attributes": {
        "fqn": "marketing_prod.gold_customer_feature_store_gmna.vehicle_attributes",
        "layer": "gold", "grain": "one row per VIN", "confirmed": True,
    },
    "vehicle_ownership": {
        "fqn": "sales_prod.gold_vehicle_ownership_gmna.vehicle_ownership",
        "layer": "gold", "grain": "one row per ownership record", "confirmed": True,
    },
    # ---------- SILVER (needed: verbatims + demographics have no Gold yet) ----------
    "survey_hub_inmoment_us_vw": {
        "fqn": "aftersales_prod.silver_enterprise_experience_engine_e3_gmna.survey_hub_inmoment_us_vw",
        "layer": "silver", "grain": "one row per survey response", "confirmed": True,
    },
    "survey_hub_inmoment_global_vw": {
        "fqn": "aftersales_prod.silver_enterprise_experience_engine_e3_gmna.survey_hub_inmoment_global_vw",
        "layer": "silver", "grain": "one row per survey response", "confirmed": True,
    },
    "acxiom_survived_individual_demographic": {
        "fqn": "customer_prod.silver_individual_gmna.acxiom_survived_individual_demographic",
        "layer": "silver", "grain": "one row per individual", "confirmed": True,
    },
    "consolidated_customer": {
        "fqn": "customer_prod.silver_individual_gmna.consolidated_customer",
        "layer": "silver", "grain": "one row per individual", "confirmed": True,
    },
    # ---------- GAP TABLES (NO SOURCE IDENTIFIED - we are proposing the shape) ----------
    "get_help_case": {
        "fqn": "t1_2_dev.gold_cx.get_help_case",
        "layer": "gold(proposed)", "grain": "one row per support case", "confirmed": False,
    },
    "content_engagement": {
        "fqn": "t1_2_dev.gold_cx.content_engagement",
        "layer": "gold(proposed)", "grain": "one row per content interaction", "confirmed": False,
    },
    "training_participation": {
        "fqn": "t1_2_dev.gold_cx.training_participation",
        "layer": "gold(proposed)", "grain": "one row per training completion", "confirmed": False,
    },
    "action_log": {
        "fqn": "t1_2_dev.gold_cx.action_log",
        "layer": "gold(proposed)", "grain": "one row per CX intervention", "confirmed": False,
    },
}

# --------------------------------------------------------------------------
# Reference values
# --------------------------------------------------------------------------
BRANDS = ["Chevrolet", "GMC"]
MODELS = {
    "Chevrolet": ["Silverado 1500", "Silverado 2500HD", "Colorado"],
    "GMC": ["Sierra 1500", "Sierra 2500HD", "Canyon"],
}
TRIMS = ["WT", "Custom", "LT", "RST", "LTZ", "High Country", "AT4", "Denali", "Elevation"]
BODY_STYLES = ["Crew Cab", "Double Cab", "Regular Cab"]
VEHICLE_TYPES = ["Pickup Truck"]
SEGMENTS = ["Full-Size Pickup", "Mid-Size Pickup", "Heavy Duty Pickup"]
CATEGORIES = ["Truck"]
REGIONS = ["Northeast", "Southeast", "Midwest", "Southwest", "West"]
STATES = {
    "Northeast": ["NY", "PA", "MA"], "Southeast": ["FL", "GA", "NC"],
    "Midwest": ["MI", "OH", "IL"], "Southwest": ["TX", "AZ", "NM"],
    "West": ["CA", "WA", "CO"],
}
LOYALTY = ["None", "Bronze", "Silver", "Gold", "Platinum"]
AGE_GROUPS = ["25-34", "35-44", "45-54", "55-64", "65+"]
INCOME_BANDS = ["<50K", "50K-75K", "75K-100K", "100K-150K", "150K+"]
OWNERSHIP_STATUS = ["Active", "Sold", "Traded-In", "Lease Ended"]
SURVEY_TYPES = ["Sales", "Service", "Dealership"]

# June-2026 case mix from the deck
CASE_TYPES = {"WiFi": 23043, "OnBoarding": 31123, "Infotainment": 12757}
CALL_DRIVERS = {
    "WiFi": ["No / Slow Internet", "Hotspot: SSID and Password",
             "Hotspot: Data Not Shared / Disabled", "Other"],
    "OnBoarding": ["Hardware Replacement", "Enroll Vehicle", "BBWC", "Other"],
    "Infotainment": ["App Not Working", "On Screen Messages",
                     "DIC (Driver Information Center)", "Other"],
}
CHANNELS = ["Phone", "Chat", "Mobile App", "Dealer", "IVR"]

VERBATIM_POS = [
    "Dealer walked me through every feature before I drove off. Excellent onboarding.",
    "Truck has been flawless. The app connects instantly every time.",
    "Service advisor called me proactively about the software update. Impressed.",
    "Hotspot works better than my home internet on job sites.",
    "Whole buying process took under two hours. No pressure at all.",
]
VERBATIM_NEU = [
    "Vehicle is fine. Setup took longer than expected but got there.",
    "No complaints about the truck. The app is average.",
    "Service was completed on time. Nothing exceptional either way.",
]
VERBATIM_NEG = [
    "Wifi drops constantly on the highway. Third call to support this month.",
    "Had to replace the connectivity module twice. Nobody explained why.",
    "Nobody showed me how to enroll the vehicle. Figured it out from YouTube.",
    "Screen freezes when I use CarPlay. Dealer says it is a known issue.",
    "Waited three weeks for a part. Zero communication from the dealer.",
    "Hotspot data will not share to my other devices. Support could not fix it.",
]

# Real interventions lifted from the June 2026 deck (Key Actions column)
ACTIONS = [
    ("ACT-001", "Telus Order Fix",                  "WiFi",         "Connectivity", "2026-06-10", "Complete",
     "Telus ordering defect fixed 6/10"),
    ("ACT-002", "AT&T / Jasper Toggle Containment", "WiFi",         "Connectivity", "2026-04-15", "In Progress",
     "Containment for AT&T / Jasper toggle entitlement issues"),
    ("ACT-003", "Canadian Plan Issue Remediation",  "WiFi",         "Connectivity", "2026-05-01", "In Progress",
     "Canadian plan mismatch target in progress"),
    ("ACT-004", "Entitlement Issue Containment",    "WiFi",         "Connectivity", "2026-03-20", "In Progress",
     "Entitlement containment in progress"),
    ("ACT-005", "Telus Gen 11 Containment",         "OnBoarding",   "Connectivity", "2026-05-20", "Complete",
     "Telus Gen 11 containment complete"),
    ("ACT-006", "AT&T Connectivity Improvement",    "OnBoarding",   "Connectivity", "2026-04-01", "Complete",
     "AT&T IMS improvement complete"),
    ("ACT-007", "Gen 12 Software Update",           "OnBoarding",   "Connectivity", "2026-06-25", "In Progress",
     "Software update for Gen 12 in progress"),
    ("ACT-008", "Tech Line Connect Modernization",  "OnBoarding",   "Support Ops",  "2026-10-01", "Planned",
     "Tech Line Connect modernization scheduled October"),
    ("ACT-009", "Profile Swap Country Code Fix",    "OnBoarding",   "Software",     "2026-05-10", "In Progress",
     "Profile swap country code defects target in progress"),
    ("ACT-010", "Google Assistant Nav Commands Fix","Infotainment", "Software",     "2026-06-05", "Complete",
     "Google Assistant navigation commands resolved June"),
    ("ACT-011", "Vehicle App Integration",          "Infotainment", "Software",     "2026-06-15", "In Progress",
     "Vehicle app integration workstream"),
]

CONTENT_ITEMS = [
    ("CNT-01", "T1-2 First Drive Walkthrough", "Video",     "Email"),
    ("CNT-02", "Connecting Your Hotspot",      "Article",   "Mobile App"),
    ("CNT-03", "myChevrolet App Setup Guide",  "Guide",     "Mobile App"),
    ("CNT-04", "Trailering Basics",            "Video",     "Web"),
    ("CNT-05", "Scheduling Your First Service","Article",   "Email"),
    ("CNT-06", "Infotainment Quick Tips",      "Interactive","Web"),
]
TRAININGS = [
    ("TRN-01", "Dealer Delivery Excellence"),
    ("TRN-02", "Connected Services Onboarding"),
    ("TRN-03", "Infotainment Troubleshooting"),
]


def month_starts(start="2026-01-01", n=6):
    d = datetime.fromisoformat(start)
    out = []
    for i in range(n):
        out.append(datetime(d.year + (d.month - 1 + i) // 12,
                            (d.month - 1 + i) % 12 + 1, 1))
    return out


def build(n_individuals: int):
    rng = np.random.default_rng(SEED)
    random.seed(SEED)
    out = {}

    n_vin = int(n_individuals * 1.2)
    ind_ids = [f"IND{100000 + i}" for i in range(n_individuals)]
    vins = [f"1GC{rng.integers(10**11, 10**12 - 1)}" for _ in range(n_vin)]

    # ---------------- e3_vin_detail (GOLD) ----------------
    rows = []
    for v in vins:
        b = random.choice(BRANDS)
        rows.append({
            "vin": v, "brand": b, "model_name": random.choice(MODELS[b]),
            "model_year": int(rng.choice([2024, 2025, 2026], p=[0.25, 0.40, 0.35])),
            "model_trim": random.choice(TRIMS),
            "vehicle_type": random.choice(VEHICLE_TYPES),
            "body_style": random.choice(BODY_STYLES),
            "vehicle_segment": str(rng.choice(SEGMENTS, p=[0.6, 0.2, 0.2])),
            "vehicle_category": random.choice(CATEGORIES),
            "t1_2_program_flag": "Y",
            "build_date": (datetime(2024, 1, 1) + timedelta(days=int(rng.integers(0, 730)))).date(),
        })
    out["e3_vin_detail"] = pd.DataFrame(rows)

    # ---------------- e3_indiv_detail (GOLD) ----------------
    out["e3_indiv_detail"] = pd.DataFrame([{
        "individual_id": i,
        "loyalty_status": str(rng.choice(LOYALTY, p=[0.30, 0.25, 0.20, 0.15, 0.10])),
        "loyalty_points": int(rng.integers(0, 25000)),
        "first_purchase_date": (datetime(2019, 1, 1) + timedelta(days=int(rng.integers(0, 2500)))).date(),
        "is_current_customer": str(rng.choice(["Y", "N"], p=[0.85, 0.15])),
    } for i in ind_ids])

    # ---------------- vehicle_attributes (GOLD) ----------------
    vd = out["e3_vin_detail"]
    out["vehicle_attributes"] = pd.DataFrame({
        "vin": vd["vin"],
        "vehicle_mileage": rng.integers(500, 85000, len(vd)),
        "vehicle_segment": vd["vehicle_segment"],
        "body_style": vd["body_style"],
        "vehicle_category": vd["vehicle_category"],
        "mileage_asof_date": pd.Timestamp("2026-06-30").date(),
    })

    # ---------------- vehicle_ownership (GOLD) ----------------
    rows = []
    for k, v in enumerate(vins):
        owner = ind_ids[k % n_individuals]
        start = datetime(2024, 1, 1) + timedelta(days=int(rng.integers(0, 800)))
        status = str(rng.choice(OWNERSHIP_STATUS, p=[0.78, 0.10, 0.08, 0.04]))
        rows.append({
            "ownership_id": f"OWN{500000 + k}", "individual_id": owner, "vin": v,
            "ownership_status": status, "ownership_sequence": 1,
            "ownership_start_date": start.date(),
            "ownership_end_date": None if status == "Active"
                else (start + timedelta(days=int(rng.integers(200, 700)))).date(),
            "purchase_type": str(rng.choice(["Purchase", "Lease", "Finance"], p=[0.35, 0.25, 0.40])),
            "dealer_id": f"DLR{rng.integers(1000, 1200)}",
        })
    out["vehicle_ownership"] = pd.DataFrame(rows)

    # ---------------- survey hub (SILVER) ----------------
    def survey(n, scope):
        rows = []
        for j in range(n):
            k = int(rng.integers(0, n_vin))
            nps = int(rng.choice(range(11),
                      p=np.array([3,2,2,3,4,6,9,13,18,20,20]) / 100))
            if nps >= 9:   cat, txt = "Promoter", random.choice(VERBATIM_POS)
            elif nps >= 7: cat, txt = "Passive",  random.choice(VERBATIM_NEU)
            else:          cat, txt = "Detractor", random.choice(VERBATIM_NEG)
            reg = random.choice(REGIONS)
            rows.append({
                "response_id": f"RSP{scope[:2].upper()}{700000 + j}",
                "individual_id": ind_ids[k % n_individuals], "vin": vins[k],
                "survey_type": random.choice(SURVEY_TYPES),
                "survey_date": (datetime(2026, 1, 1) + timedelta(days=int(rng.integers(0, 180)))).date(),
                "nps_score": nps, "nps_category": cat,
                "csat_score": int(np.clip(round(rng.normal(4.1, 0.9)), 1, 5)),
                "verbatim_text": txt,
                "dealer_id": f"DLR{rng.integers(1000, 1200)}",
                "region": reg, "region_scope": scope,
            })
        return pd.DataFrame(rows)

    out["survey_hub_inmoment_us_vw"] = survey(int(n_individuals * 1.3), "US")
    out["survey_hub_inmoment_global_vw"] = survey(int(n_individuals * 0.4), "GLOBAL")

    # ---------------- demographics (SILVER) ----------------
    regions_by_ind = {i: random.choice(REGIONS) for i in ind_ids}
    out["acxiom_survived_individual_demographic"] = pd.DataFrame([{
        "individual_id": i,
        "customer_age_group": str(rng.choice(AGE_GROUPS, p=[0.12, 0.24, 0.27, 0.24, 0.13])),
        "age_range": None,
        "household_income_band": str(rng.choice(INCOME_BANDS, p=[0.10, 0.20, 0.25, 0.28, 0.17])),
        "is_current_customer": "Y",
        "state": random.choice(STATES[regions_by_ind[i]]),
    } for i in ind_ids])
    out["acxiom_survived_individual_demographic"]["age_range"] = \
        out["acxiom_survived_individual_demographic"]["customer_age_group"]

    out["consolidated_customer"] = pd.DataFrame([{
        "individual_id": i, "region": regions_by_ind[i],
        "gender_code": str(rng.choice(["M", "F", "U"], p=[0.62, 0.35, 0.03])),
        "zip_code": f"{rng.integers(10000, 99999)}",
        "num_children": int(rng.choice([0, 1, 2, 3], p=[0.42, 0.24, 0.24, 0.10])),
    } for i in ind_ids])
    out["consolidated_customer"]["children_flag"] = np.where(
        out["consolidated_customer"]["num_children"] > 0, "Y", "N")

    # ---------------- get_help_case (GAP) ----------------
    months = month_starts()
    mix = np.array(list(CASE_TYPES.values()), dtype=float)
    mix = mix / mix.sum()
    # Hardware Replacement ramp 2,413 -> 11,998 over Jan..Jun
    hw_share = np.linspace(0.10, 0.42, 6)
    rows, cid = [], 0
    for mi, m in enumerate(months):
        # each intervention that has already landed lifts FCR slightly
        landed = sum(1 for a in ACTIONS
                     if a[4] <= m.strftime("%Y-%m-%d") and a[5] == "Complete")
        for _ in range(int(n_individuals * 1.1)):
            ct = str(rng.choice(list(CASE_TYPES), p=mix))
            drivers = CALL_DRIVERS[ct]
            if ct == "OnBoarding":
                p = [hw_share[mi], 0.28, 0.12, 1 - hw_share[mi] - 0.40]
                p = np.clip(p, 0.01, None); p = p / sum(p)
            elif ct == "WiFi":
                p = [0.55, 0.16, 0.13, 0.16]
            else:
                p = [0.45, 0.20, 0.15, 0.20]
            k = int(rng.integers(0, n_vin))
            opened = m + timedelta(days=int(rng.integers(0, 27)),
                                   hours=int(rng.integers(0, 24)))
            days = float(np.clip(rng.exponential(0.9), 0.02, 14))
            fcr_p = min(0.72 + 0.012 * landed, 0.90)
            rows.append({
                "case_id": f"CASE{900000 + cid}",
                "individual_id": ind_ids[k % n_individuals], "vin": vins[k],
                "case_type": ct, "call_driver": str(rng.choice(drivers, p=p)),
                "channel": str(rng.choice(CHANNELS, p=[0.42, 0.20, 0.18, 0.12, 0.08])),
                "case_open_ts": opened,
                "case_close_ts": opened + timedelta(days=days),
                "days_to_close": round(days, 2),
                "closed_within_24h": "Y" if days <= 1 else "N",
                "first_contact_resolution": "Y" if rng.random() < fcr_p else "N",
                "csat_score": int(np.clip(round(rng.normal(4.1, 1.0)), 1, 5)),
                "region": regions_by_ind[ind_ids[k % n_individuals]],
                "case_month": m.date(),
            })
            cid += 1
    out["get_help_case"] = pd.DataFrame(rows)

    # ---------------- content_engagement (GAP) ----------------
    rows = []
    for j in range(int(n_individuals * 2.0)):
        c = random.choice(CONTENT_ITEMS)
        rows.append({
            "engagement_id": f"ENG{300000 + j}",
            "individual_id": random.choice(ind_ids),
            "content_id": c[0], "content_title": c[1], "content_type": c[2],
            "channel": c[3],
            "engagement_ts": datetime(2026, 1, 1) + timedelta(days=int(rng.integers(0, 180))),
            "engagement_depth_pct": int(np.clip(rng.normal(62, 26), 1, 100)),
        })
    ce = pd.DataFrame(rows)
    ce["completed_flag"] = np.where(ce["engagement_depth_pct"] >= 80, "Y", "N")
    out["content_engagement"] = ce

    # ---------------- training_participation (GAP) ----------------
    rows = []
    for j in range(int(n_individuals * 0.5)):
        t = random.choice(TRAININGS)
        rows.append({
            "participation_id": f"TRP{200000 + j}",
            "individual_id": random.choice(ind_ids),
            "dealer_id": f"DLR{rng.integers(1000, 1200)}",
            "training_id": t[0], "training_name": t[1],
            "training_date": (datetime(2026, 1, 1) + timedelta(days=int(rng.integers(0, 180)))).date(),
            "completed_flag": str(rng.choice(["Y", "N"], p=[0.8, 0.2])),
        })
    out["training_participation"] = pd.DataFrame(rows)

    # ---------------- action_log (GAP) ----------------
    out["action_log"] = pd.DataFrame([{
        "action_id": a[0], "action_name": a[1], "case_type": a[2],
        "action_owner": a[3], "action_date": a[4], "action_status": a[5],
        "description": a[6],
    } for a in ACTIONS])

    return out


SQL_TYPE = {"int64": "BIGINT", "Int64": "BIGINT", "float64": "DOUBLE",
            "bool": "BOOLEAN", "datetime64[ns]": "TIMESTAMP", "object": "STRING"}


def to_ddl(name, df):
    meta = TABLES[name]
    cols = ",\n".join(
        f"  {c} {SQL_TYPE.get(str(df[c].dtype), 'STRING')}" for c in df.columns)
    return (f"-- {meta['grain']} | layer: {meta['layer']} | "
            f"schema confirmed: {meta['confirmed']}\n"
            f"CREATE TABLE IF NOT EXISTS {meta['fqn']} (\n{cols}\n) USING DELTA;\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="./synthetic")
    ap.add_argument("--individuals", type=int, default=150)
    ap.add_argument("--format", choices=["csv", "parquet"], default="csv")
    a = ap.parse_args()

    os.makedirs(a.out, exist_ok=True)
    data = build(a.individuals)

    manifest, ddl = [], []
    for name, df in data.items():
        path = os.path.join(a.out, f"{name}.{a.format}")
        df.to_parquet(path, index=False) if a.format == "parquet" else df.to_csv(path, index=False)
        ddl.append(to_ddl(name, df))
        manifest.append({"table": name, "fqn": TABLES[name]["fqn"],
                         "layer": TABLES[name]["layer"], "rows": len(df),
                         "columns": list(df.columns),
                         "schema_confirmed": TABLES[name]["confirmed"]})
        print(f"{len(df):>6} rows  {TABLES[name]['fqn']}")

    with open(os.path.join(a.out, "create_tables.sql"), "w") as f:
        f.write("\n".join(ddl))
    with open(os.path.join(a.out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2, default=str)
    print(f"\nWrote {len(data)} tables + create_tables.sql + manifest.json -> {a.out}")


if __name__ == "__main__":
    main()
