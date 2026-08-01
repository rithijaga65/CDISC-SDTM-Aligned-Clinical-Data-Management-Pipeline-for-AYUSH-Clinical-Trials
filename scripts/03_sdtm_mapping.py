"""
03_sdtm_mapping.py

Maps raw CRF-level domains (DM, EX, VS, LB, AE) into CDISC SDTM-aligned
structures for the RC-101 AYUSH osteoarthritis trial.

This is a simplified, illustrative SDTM mapping (not a full regulatory
submission-ready implementation) intended to demonstrate CDISC structuring
principles applied to AYUSH trial data — a combination not found in
currently published AYUSH trial literature.

Standard SDTM variables used (subset, illustrative):
    DM: STUDYID, DOMAIN, USUBJID, SUBJID, SITEID, AGE, AGEU, SEX, ARM, RFSTDTC
    EX: STUDYID, DOMAIN, USUBJID, EXTRT, EXDOSE, EXDOSU, EXDOSFRM, VISIT
    VS: STUDYID, DOMAIN, USUBJID, VSTESTCD, VSTEST, VSORRES, VSORRESU, VISIT, VSDTC
    LB: STUDYID, DOMAIN, USUBJID, LBTESTCD, LBTEST, LBORRES, LBORRESU, VISIT
    AE: STUDYID, DOMAIN, USUBJID, AETERM, AESEV, AESER, AEREL, AEOUT, AESTDY

A custom non-standard SUPPQUAL-style supplemental domain (SUPPDM) is
included to capture the AYUSH-specific PRAKRITI variable, since CDISC SDTM
has no native domain for Ayurvedic constitutional typing — illustrating
where existing CDISC standards fall short for traditional medicine trials
and how sponsors typically extend them (via SUPPQUAL) to capture
therapeutically relevant, system-specific variables.
"""

import pandas as pd

RAW_DIR = "/home/claude/ayush_cdm_project/data/raw"
SDTM_DIR = "/home/claude/ayush_cdm_project/data/sdtm"
STUDYID = "RC101-OA-P2"

dm_raw = pd.read_csv(f"{RAW_DIR}/DM_raw.csv")
ex_raw = pd.read_csv(f"{RAW_DIR}/EX_raw.csv")
vs_raw = pd.read_csv(f"{RAW_DIR}/VS_raw.csv")
lb_raw = pd.read_csv(f"{RAW_DIR}/LB_raw.csv")
ae_raw = pd.read_csv(f"{RAW_DIR}/AE_raw.csv")

# Drop the duplicate DM record before SDTM mapping (data management would
# resolve this via query resolution prior to lock; here we keep first
# occurrence and note it was flagged in the query log)
dm_raw = dm_raw.drop_duplicates(subset=["SUBJID"], keep="first").reset_index(drop=True)

# ---------------------------------------------------------------------------
# DM domain
# ---------------------------------------------------------------------------
dm_sdtm = pd.DataFrame({
    "STUDYID": STUDYID,
    "DOMAIN": "DM",
    "USUBJID": STUDYID + "-" + dm_raw["SUBJID"],
    "SUBJID": dm_raw["SUBJID"],
    "SITEID": dm_raw["SITEID"],
    "AGE": dm_raw["AGE"],
    "AGEU": "YEARS",
    "SEX": dm_raw["SEX"].map({"Male": "M", "Female": "F"}),  # non-conformant values -> NaN, flagged separately
    "ARM": dm_raw["ARM"],
    "ARMCD": dm_raw["ARM"].map({"RC-101 (Test)": "TEST", "Placebo": "PBO"}),
    "RFSTDTC": dm_raw["ENROLL_DATE"],
})
dm_sdtm.to_csv(f"{SDTM_DIR}/DM.csv", index=False)

# ---------------------------------------------------------------------------
# SUPPDM - non-standard AYUSH-specific supplemental qualifier (Prakriti)
# ---------------------------------------------------------------------------
suppdm = pd.DataFrame({
    "STUDYID": STUDYID,
    "RDOMAIN": "DM",
    "USUBJID": STUDYID + "-" + dm_raw["SUBJID"],
    "QNAM": "PRAKRITI",
    "QLABEL": "Ayurvedic Constitutional Type (Prakriti)",
    "QVAL": dm_raw["PRAKRITI"],
})
suppdm.to_csv(f"{SDTM_DIR}/SUPPDM.csv", index=False)

# ---------------------------------------------------------------------------
# EX domain
# ---------------------------------------------------------------------------
ex_sdtm = pd.DataFrame({
    "STUDYID": STUDYID,
    "DOMAIN": "EX",
    "USUBJID": STUDYID + "-" + ex_raw["SUBJID"],
    "EXTRT": "RASNADI COMPOUND (RC-101)",
    "EXDOSE": ex_raw["PLANNED_DOSE_MG"],
    "EXDOSU": "mg",
    "EXDOSFRM": ex_raw["DOSE_FORM"],
    "VISIT": ex_raw["VISIT"],
    "EXCOMPLY_PCT": ex_raw["COMPLIANCE_PCT"],  # non-standard qualifier, kept alongside for compliance tracking
})
ex_sdtm.to_csv(f"{SDTM_DIR}/EX.csv", index=False)

# ---------------------------------------------------------------------------
# VS domain (melted to one-row-per-test, standard SDTM long format)
# ---------------------------------------------------------------------------
vs_test_map = {
    "SYSBP": ("Systolic Blood Pressure", "mmHg"),
    "DIABP": ("Diastolic Blood Pressure", "mmHg"),
    "HR": ("Heart Rate", "beats/min"),
    "TEMP_C": ("Temperature", "C"),
    "WEIGHT_KG": ("Weight", "kg"),
}
vs_long_rows = []
for _, row in vs_raw.iterrows():
    for testcd, (testname, unit) in vs_test_map.items():
        vs_long_rows.append({
            "STUDYID": STUDYID,
            "DOMAIN": "VS",
            "USUBJID": STUDYID + "-" + row["SUBJID"],
            "VISIT": row["VISIT"],
            "VSDTC": row["VISIT_DATE"],
            "VSTESTCD": testcd,
            "VSTEST": testname,
            "VSORRES": row[testcd],
            "VSORRESU": unit,
        })
vs_sdtm = pd.DataFrame(vs_long_rows)
vs_sdtm.to_csv(f"{SDTM_DIR}/VS.csv", index=False)

# ---------------------------------------------------------------------------
# LB domain (melted, long format)
# ---------------------------------------------------------------------------
lb_test_map = {
    "ALT_U_L": ("Alanine Aminotransferase", "U/L"),
    "AST_U_L": ("Aspartate Aminotransferase", "U/L"),
    "CREATININE_MG_DL": ("Creatinine", "mg/dL"),
    "HSCRP_MG_L": ("High Sensitivity C-Reactive Protein", "mg/L"),
    "MARKER_COMPOUND_NG_ML": ("Phytochemical Marker Compound", "ng/mL"),
}
lb_long_rows = []
for _, row in lb_raw.iterrows():
    for testcd, (testname, unit) in lb_test_map.items():
        lb_long_rows.append({
            "STUDYID": STUDYID,
            "DOMAIN": "LB",
            "USUBJID": STUDYID + "-" + row["SUBJID"],
            "VISIT": row["VISIT"],
            "LBTESTCD": testcd,
            "LBTEST": testname,
            "LBORRES": row[testcd],
            "LBORRESU": unit,
        })
lb_sdtm = pd.DataFrame(lb_long_rows)
lb_sdtm.to_csv(f"{SDTM_DIR}/LB.csv", index=False)

# ---------------------------------------------------------------------------
# AE domain
# ---------------------------------------------------------------------------
ae_sdtm = pd.DataFrame({
    "STUDYID": STUDYID,
    "DOMAIN": "AE",
    "USUBJID": STUDYID + "-" + ae_raw["SUBJID"],
    "AETERM": ae_raw["AE_TERM"],
    "AESEV": ae_raw["SEVERITY"],
    "AESER": ae_raw["SERIOUS"],
    "AEREL": ae_raw["RELATED_TO_STUDY_DRUG"],
    "AEOUT": ae_raw["OUTCOME"],
    "AESTDY": ae_raw["ONSET_DAY"],
    "AEDUR_DAYS": ae_raw["DURATION_DAYS"],
})
ae_sdtm.to_csv(f"{SDTM_DIR}/AE.csv", index=False)

# ---------------------------------------------------------------------------
# Mapping specification document (raw variable -> SDTM variable)
# ---------------------------------------------------------------------------
mapping_spec = pd.DataFrame([
    ("DM", "SUBJID", "DM", "SUBJID", "Direct copy"),
    ("DM", "SITEID", "DM", "SITEID", "Direct copy"),
    ("DM", "AGE", "DM", "AGE", "Direct copy; AGEU set to 'YEARS'"),
    ("DM", "SEX", "DM", "SEX", "Recoded Male->M, Female->F; non-conformant values yield null, routed to query log"),
    ("DM", "ARM", "DM", "ARM / ARMCD", "Direct copy + coded ARMCD (TEST/PBO)"),
    ("DM", "ENROLL_DATE", "DM", "RFSTDTC", "Direct copy, ISO 8601 date"),
    ("DM", "PRAKRITI", "SUPPDM", "QVAL (QNAM=PRAKRITI)", "Non-standard AYUSH variable; captured via supplemental qualifier since no native CDISC domain exists"),
    ("EX", "DOSE_FORM", "EX", "EXDOSFRM", "Direct copy"),
    ("EX", "PLANNED_DOSE_MG", "EX", "EXDOSE", "Direct copy; EXDOSU = 'mg'"),
    ("EX", "COMPLIANCE_PCT", "EX", "EXCOMPLY_PCT", "Non-standard compliance qualifier retained alongside core EX variables"),
    ("VS", "SYSBP/DIABP/HR/TEMP_C/WEIGHT_KG", "VS", "VSTESTCD/VSTEST/VSORRES/VSORRESU", "Wide-to-long melt into standard SDTM one-record-per-test structure"),
    ("LB", "ALT_U_L/AST_U_L/CREATININE.../MARKER_COMPOUND_NG_ML", "LB", "LBTESTCD/LBTEST/LBORRES/LBORRESU", "Wide-to-long melt; phytochemical marker included as a custom LBTESTCD"),
    ("AE", "AE_TERM", "AE", "AETERM", "Direct copy"),
    ("AE", "SEVERITY", "AE", "AESEV", "Direct copy"),
    ("AE", "SERIOUS", "AE", "AESER", "Direct copy (Y/N)"),
    ("AE", "RELATED_TO_STUDY_DRUG", "AE", "AEREL", "Direct copy"),
    ("AE", "ONSET_DAY", "AE", "AESTDY", "Direct copy (study day relative to RFSTDTC)"),
], columns=["Source Domain", "Raw Variable", "Target Domain", "SDTM Variable", "Mapping Logic / Notes"])

mapping_spec.to_csv(f"{SDTM_DIR}/_mapping_specification.csv", index=False)

print("SDTM mapping complete.")
print(f"DM: {len(dm_sdtm)} records | SUPPDM: {len(suppdm)} records")
print(f"EX: {len(ex_sdtm)} records")
print(f"VS: {len(vs_sdtm)} records (melted long format)")
print(f"LB: {len(lb_sdtm)} records (melted long format)")
print(f"AE: {len(ae_sdtm)} records")
