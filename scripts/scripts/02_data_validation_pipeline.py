"""
02_data_validation_pipeline.py

Automated Clinical Data Management (CDM) validation pipeline for the
Rasnadi Compound (RC-101) AYUSH osteoarthritis trial.

Performs, per domain:
    - Missing data detection
    - Range / plausibility checks (protocol-defined and physiological)
    - Logic checks (visit date sequencing, AE reporting timelines)
    - Duplicate record detection
    - Unit-error heuristics (e.g. Fahrenheit entered as Celsius)

Outputs:
    - reports/query_log.csv       (DCF-style: one row per detected issue)
    - reports/validation_summary.csv (counts by domain/check type)
    - reports/pipeline_detection_check.csv (compares detected issues vs.
      the ground-truth injected error log, for pipeline QC)
"""

import pandas as pd
import numpy as np
from datetime import datetime

RAW_DIR = "/home/claude/ayush_cdm_project/data/raw"
REPORT_DIR = "/home/claude/ayush_cdm_project/reports"

query_log = []  # list of dicts -> becomes query_log.csv
query_counter = 1

def log_query(domain, subjid, field, issue, severity="Query"):
    global query_counter
    query_log.append({
        "QUERY_ID": f"Q-{query_counter:04d}",
        "DOMAIN": domain,
        "SUBJID": subjid,
        "FIELD": field,
        "ISSUE": issue,
        "STATUS": "Open",
        "SEVERITY": severity,
        "DATE_RAISED": datetime.today().strftime("%Y-%m-%d"),
    })
    query_counter += 1

# ---------------------------------------------------------------------------
# Load raw domains
# ---------------------------------------------------------------------------
dm = pd.read_csv(f"{RAW_DIR}/DM_raw.csv")
ex = pd.read_csv(f"{RAW_DIR}/EX_raw.csv")
vs = pd.read_csv(f"{RAW_DIR}/VS_raw.csv")
lb = pd.read_csv(f"{RAW_DIR}/LB_raw.csv")
ae = pd.read_csv(f"{RAW_DIR}/AE_raw.csv")
cm = pd.read_csv(f"{RAW_DIR}/CM_raw.csv")

# ---------------------------------------------------------------------------
# DM checks
# ---------------------------------------------------------------------------
# Missing age
for _, row in dm[dm["AGE"].isna()].iterrows():
    log_query("DM", row["SUBJID"], "AGE", "Missing value", "Query")

# Protocol range check: age must be 35-75 inclusive
out_of_range = dm[(dm["AGE"].notna()) & ((dm["AGE"] < 35) | (dm["AGE"] > 75))]
for _, row in out_of_range.iterrows():
    log_query("DM", row["SUBJID"], "AGE", f"Age {row['AGE']} outside protocol range (35-75)", "Protocol Deviation")

# Duplicate subject IDs
dup_ids = dm[dm.duplicated(subset=["SUBJID"], keep=False)]
for subj in dup_ids["SUBJID"].unique():
    log_query("DM", subj, "SUBJID", "Duplicate subject record found in database", "Critical")

# Invalid SEX values
valid_sex = {"Male", "Female"}
invalid_sex = dm[~dm["SEX"].isin(valid_sex)]
for _, row in invalid_sex.iterrows():
    log_query("DM", row["SUBJID"], "SEX", f"Invalid value '{row['SEX']}' - expected Male/Female", "Query")

# ---------------------------------------------------------------------------
# EX checks
# ---------------------------------------------------------------------------
# Compliance > 100%
bad_compliance = ex[ex["COMPLIANCE_PCT"] > 100]
for _, row in bad_compliance.iterrows():
    log_query("EX", row["SUBJID"], "COMPLIANCE_PCT",
               f"Compliance {row['COMPLIANCE_PCT']}% exceeds 100% at visit {row['VISIT']}", "Query")

# Missing dose form
for _, row in ex[ex["DOSE_FORM"].isna()].iterrows():
    log_query("EX", row["SUBJID"], "DOSE_FORM", f"Missing dose form at visit {row['VISIT']}", "Query")

# ---------------------------------------------------------------------------
# VS checks
# ---------------------------------------------------------------------------
# Physiologically implausible BP (protocol-independent clinical bounds)
bad_sbp = vs[(vs["SYSBP"] < 70) | (vs["SYSBP"] > 200)]
for _, row in bad_sbp.iterrows():
    log_query("VS", row["SUBJID"], "SYSBP",
               f"Systolic BP {row['SYSBP']} mmHg at {row['VISIT']} is physiologically implausible", "Query")

# Temperature unit-error heuristic (normal Celsius range ~35-40; anything 90+ suggests Fahrenheit)
bad_temp = vs[vs["TEMP_C"] > 45]
for _, row in bad_temp.iterrows():
    log_query("VS", row["SUBJID"], "TEMP_C",
               f"Temperature {row['TEMP_C']} recorded — likely entered in Fahrenheit, not Celsius", "Query")

# Missing weight
for _, row in vs[vs["WEIGHT_KG"].isna()].iterrows():
    log_query("VS", row["SUBJID"], "WEIGHT_KG", f"Missing weight at visit {row['VISIT']}", "Query")

# Visit date logic: Baseline visit date should not precede subject's enrollment date
vs_merged = vs.merge(dm[["SUBJID", "ENROLL_DATE"]], on="SUBJID", how="left")
vs_merged["VISIT_DATE"] = pd.to_datetime(vs_merged["VISIT_DATE"], errors="coerce")
vs_merged["ENROLL_DATE"] = pd.to_datetime(vs_merged["ENROLL_DATE"], errors="coerce")
bad_dates = vs_merged[(vs_merged["VISIT"] == "Baseline") & (vs_merged["VISIT_DATE"] < vs_merged["ENROLL_DATE"])]
for _, row in bad_dates.iterrows():
    log_query("VS", row["SUBJID"], "VISIT_DATE",
               f"Baseline visit date ({row['VISIT_DATE'].date()}) precedes enrollment date ({row['ENROLL_DATE'].date()})",
               "Critical")

# ---------------------------------------------------------------------------
# LB checks
# ---------------------------------------------------------------------------
# Hepatotoxicity signal: ALT normal upper limit ~40 U/L; flag >3x ULN as safety signal
alt_flag = lb[lb["ALT_U_L"] > 120]
for _, row in alt_flag.iterrows():
    log_query("LB", row["SUBJID"], "ALT_U_L",
               f"ALT {row['ALT_U_L']} U/L (>3x ULN) at {row['VISIT']} — possible hepatotoxicity signal, review for herbal-induced liver injury",
               "Safety Signal")

# Negative lab values (physically impossible)
neg_creat = lb[lb["CREATININE_MG_DL"] < 0]
for _, row in neg_creat.iterrows():
    log_query("LB", row["SUBJID"], "CREATININE_MG_DL",
               f"Negative creatinine value ({row['CREATININE_MG_DL']}) is not physically possible", "Critical")

# Missing marker compound
for _, row in lb[lb["MARKER_COMPOUND_NG_ML"].isna()].iterrows():
    log_query("LB", row["SUBJID"], "MARKER_COMPOUND_NG_ML",
               f"Missing phytochemical marker compound level at {row['VISIT']}", "Query")

# ---------------------------------------------------------------------------
# AE checks
# ---------------------------------------------------------------------------
# SAE reporting timeline (regulatory: SAEs must be reported within 24 hours / 1 day of awareness)
ae["REPORT_LAG_DAYS"] = ae["REPORTED_DATE_DAY"] - ae["ONSET_DAY"]
late_sae = ae[(ae["SERIOUS"] == "Y") & (ae["REPORT_LAG_DAYS"] > 1)]
for _, row in late_sae.iterrows():
    log_query("AE", row["SUBJID"], "REPORTED_DATE_DAY",
               f"SAE ({row['AE_TERM']}) reported {row['REPORT_LAG_DAYS']} days after onset — exceeds 24hr regulatory reporting requirement",
               "Regulatory Breach")

# Negative duration
neg_dur = ae[ae["DURATION_DAYS"] < 0]
for _, row in neg_dur.iterrows():
    log_query("AE", row["SUBJID"], "DURATION_DAYS",
               f"Negative AE duration ({row['DURATION_DAYS']} days) is not possible", "Critical")

# Missing severity
for _, row in ae[ae["SEVERITY"].isna()].iterrows():
    log_query("AE", row["SUBJID"], "SEVERITY", "Missing AE severity grading", "Query")

# ---------------------------------------------------------------------------
# Cross-domain: AE / CM reconciliation
# Flag AEs with term "Elevated liver enzymes" that have no corresponding LB
# ALT/AST elevation on record (safety data consistency check)
# ---------------------------------------------------------------------------
liver_aes = ae[ae["AE_TERM"] == "Elevated liver enzymes"]
subjects_with_lb_flag = set(alt_flag["SUBJID"].unique())
for _, row in liver_aes.iterrows():
    if row["SUBJID"] not in subjects_with_lb_flag:
        log_query("AE/LB", row["SUBJID"], "AE_TERM",
                   "AE term 'Elevated liver enzymes' recorded but no corresponding ALT elevation found in LB domain — reconciliation discrepancy",
                   "Query")

# ---------------------------------------------------------------------------
# Save query log
# ---------------------------------------------------------------------------
query_df = pd.DataFrame(query_log)
query_df.to_csv(f"{REPORT_DIR}/query_log.csv", index=False)

# ---------------------------------------------------------------------------
# Validation summary (counts by domain and severity)
# ---------------------------------------------------------------------------
summary = query_df.groupby(["DOMAIN", "SEVERITY"]).size().reset_index(name="COUNT")
summary.to_csv(f"{REPORT_DIR}/validation_summary.csv", index=False)

# ---------------------------------------------------------------------------
# Pipeline QC: compare against ground-truth injected errors
# ---------------------------------------------------------------------------
truth = pd.read_csv(f"{RAW_DIR}/_injected_errors_log.csv")
detected_subj_field = set(zip(query_df["DOMAIN"], query_df["SUBJID"], query_df["FIELD"]))
truth_subj_field = set(zip(truth["DOMAIN"], truth["SUBJID"], truth["FIELD"]))

detected_count = len(truth_subj_field & detected_subj_field)
missed = truth_subj_field - detected_subj_field

qc_rows = []
for domain, subj, field in truth_subj_field:
    qc_rows.append({
        "DOMAIN": domain, "SUBJID": subj, "FIELD": field,
        "DETECTED_BY_PIPELINE": (domain, subj, field) in detected_subj_field
    })
qc_df = pd.DataFrame(qc_rows)
qc_df.to_csv(f"{REPORT_DIR}/pipeline_detection_check.csv", index=False)

print(f"Total queries raised: {len(query_df)}")
print(f"\nQueries by domain:\n{query_df.groupby('DOMAIN').size()}")
print(f"\nQueries by severity:\n{query_df.groupby('SEVERITY').size()}")
print(f"\n--- Pipeline QC against {len(truth_subj_field)} ground-truth injected errors ---")
print(f"Detected: {detected_count} / {len(truth_subj_field)} ({100*detected_count/len(truth_subj_field):.1f}%)")
if missed:
    print(f"\nMissed (by design or field-name mismatch — reviewed below):")
    for m in missed:
        print(f"  {m}")
