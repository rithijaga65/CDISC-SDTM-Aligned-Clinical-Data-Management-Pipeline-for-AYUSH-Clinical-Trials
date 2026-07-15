"""
01_generate_mock_data.py

Generates synthetic raw clinical trial data for a mock Phase II AYUSH/Ayurvedic
herbal trial:

    "A Randomized, Placebo-Controlled Phase II Study to Evaluate the Efficacy
    and Safety of Rasnadi Compound (Herbal Formulation RC-101) in the
    Management of Knee Osteoarthritis"

Domains generated (raw/CRF-level, pre-SDTM):
    - DM  (Demographics)
    - EX  (Exposure / Dosing - herbal formulation)
    - AE  (Adverse Events)
    - VS  (Vital Signs)
    - LB  (Lab Values + Phytochemical Marker Levels)
    - CM  (Concomitant Medications)

Data errors are DELIBERATELY embedded so the cleaning/validation pipeline
(script 02) has real issues to detect. Every injected error is logged to
data/raw/_injected_errors_log.csv so we can verify pipeline detection rate.
"""

import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

RNG_SEED = 42
random.seed(RNG_SEED)
np.random.seed(RNG_SEED)

N_SUBJECTS = 80
SITES = ["SITE01", "SITE02", "SITE03"]
ARMS = ["RC-101 (Test)", "Placebo"]
VISITS = ["Screening", "Baseline", "Week 2", "Week 4", "Week 8", "Week 12", "End of Study"]
VISIT_DAY_OFFSET = {"Screening": -14, "Baseline": 0, "Week 2": 14, "Week 4": 28,
                     "Week 8": 56, "Week 12": 84, "End of Study": 90}

OUT_DIR = "/home/claude/ayush_cdm_project/data/raw"
injected_errors = []  # (domain, subject_id, field, issue_description)

# ---------------------------------------------------------------------------
# 1. DEMOGRAPHICS (DM)
# ---------------------------------------------------------------------------
subjects = [f"AYU-{i:03d}" for i in range(1, N_SUBJECTS + 1)]
dm_rows = []
enrollment_start = datetime(2025, 3, 1)

for idx, subj in enumerate(subjects):
    site = random.choice(SITES)
    arm = ARMS[idx % 2]  # balanced randomization
    age = int(np.random.normal(52, 10))
    age = max(35, min(75, age))  # protocol: age 35-75
    sex = random.choice(["Male", "Female"])
    prakriti = random.choice(["Vata", "Pitta", "Kapha", "Vata-Pitta", "Pitta-Kapha", "Tridosha"])
    enroll_date = enrollment_start + timedelta(days=random.randint(0, 120))

    dm_rows.append({
        "SUBJID": subj,
        "SITEID": site,
        "ARM": arm,
        "AGE": age,
        "SEX": sex,
        "PRAKRITI": prakriti,
        "ENROLL_DATE": enroll_date.strftime("%Y-%m-%d"),
        "INFORMED_CONSENT": "Y",
    })

dm = pd.DataFrame(dm_rows)

# Inject errors into DM
# 1a. Missing age
bad_idx = dm.sample(3, random_state=1).index
dm.loc[bad_idx, "AGE"] = np.nan
for i in bad_idx:
    injected_errors.append(("DM", dm.loc[i, "SUBJID"], "AGE", "Missing value"))

# 1b. Out-of-protocol age (protocol range 35-75)
out_idx = dm.sample(2, random_state=2).index
dm.loc[out_idx, "AGE"] = [22, 81]
for i in out_idx:
    injected_errors.append(("DM", dm.loc[i, "SUBJID"], "AGE", "Out of protocol range (35-75)"))

# 1c. Duplicate subject record
dup_row = dm.iloc[5].copy()
dm = pd.concat([dm, pd.DataFrame([dup_row])], ignore_index=True)
injected_errors.append(("DM", dup_row["SUBJID"], "SUBJID", "Duplicate subject record"))

# 1d. Invalid SEX value (data entry error)
typo_idx = dm.sample(1, random_state=3).index
dm.loc[typo_idx, "SEX"] = "M ale"
for i in typo_idx:
    injected_errors.append(("DM", dm.loc[i, "SUBJID"], "SEX", "Invalid free-text entry"))

dm.to_csv(f"{OUT_DIR}/DM_raw.csv", index=False)

# ---------------------------------------------------------------------------
# 2. EXPOSURE / DOSING (EX) - herbal formulation compliance
# ---------------------------------------------------------------------------
ex_rows = []
for subj in dm["SUBJID"].unique():
    arm = dm.loc[dm["SUBJID"] == subj, "ARM"].values[0]
    dose_form = random.choice(["Tablet", "Churna (Powder)", "Kashayam (Decoction)"])
    planned_dose_mg = 500 if dose_form == "Tablet" else random.choice([1000, 1500])
    for visit in ["Baseline", "Week 2", "Week 4", "Week 8", "Week 12"]:
        compliance_pct = round(np.random.normal(92, 8), 1)
        compliance_pct = max(0, min(100, compliance_pct))
        ex_rows.append({
            "SUBJID": subj,
            "VISIT": visit,
            "DOSE_FORM": dose_form,
            "PLANNED_DOSE_MG": planned_dose_mg,
            "COMPLIANCE_PCT": compliance_pct,
            "ARM": arm,
        })

ex = pd.DataFrame(ex_rows)

# Inject errors into EX
# 2a. Compliance > 100% (impossible)
imp_idx = ex.sample(4, random_state=4).index
ex.loc[imp_idx, "COMPLIANCE_PCT"] = [110.0, 145.0, 132.0, 101.5]
for i in imp_idx:
    injected_errors.append(("EX", ex.loc[i, "SUBJID"], "COMPLIANCE_PCT", "Value exceeds 100% (impossible)"))

# 2b. Missing dose form
miss_idx = ex.sample(3, random_state=5).index
ex.loc[miss_idx, "DOSE_FORM"] = np.nan
for i in miss_idx:
    injected_errors.append(("EX", ex.loc[i, "SUBJID"], "DOSE_FORM", "Missing value"))

ex.to_csv(f"{OUT_DIR}/EX_raw.csv", index=False)

# ---------------------------------------------------------------------------
# 3. VITAL SIGNS (VS)
# ---------------------------------------------------------------------------
vs_rows = []
dm_enroll_lookup = dict(zip(dm["SUBJID"], pd.to_datetime(dm["ENROLL_DATE"])))
for subj in dm["SUBJID"].unique():
    base_sbp = np.random.normal(126, 10)
    base_dbp = np.random.normal(80, 8)
    base_hr = np.random.normal(76, 8)
    subj_enroll_date = dm_enroll_lookup[subj]
    for visit in VISITS:
        vs_rows.append({
            "SUBJID": subj,
            "VISIT": visit,
            "VISIT_DATE": (subj_enroll_date + timedelta(days=VISIT_DAY_OFFSET[visit] + random.randint(-2, 2))).strftime("%Y-%m-%d"),
            "SYSBP": round(base_sbp + np.random.normal(0, 5), 1),
            "DIABP": round(base_dbp + np.random.normal(0, 4), 1),
            "HR": round(base_hr + np.random.normal(0, 6), 1),
            "TEMP_C": round(np.random.normal(36.8, 0.3), 1),
            "WEIGHT_KG": round(np.random.normal(68, 12), 1),
        })

vs = pd.DataFrame(vs_rows)

# Inject errors into VS
# 3a. Physiologically impossible BP (out of range)
imp_idx = vs.sample(4, random_state=6).index
vs.loc[imp_idx, "SYSBP"] = [220.0, 60.0, 250.0, 55.0]
for i in imp_idx:
    injected_errors.append(("VS", vs.loc[i, "SUBJID"], "SYSBP", "Physiologically implausible value"))

# 3b. Impossible temperature (data entry error, e.g. F instead of C)
temp_idx = vs.sample(3, random_state=7).index
vs.loc[temp_idx, "TEMP_C"] = [98.6, 99.1, 101.4]  # entered in Fahrenheit by mistake
for i in temp_idx:
    injected_errors.append(("VS", vs.loc[i, "SUBJID"], "TEMP_C", "Likely unit error (Fahrenheit entered as Celsius)"))

# 3c. Missing weight
wt_idx = vs.sample(5, random_state=8).index
vs.loc[wt_idx, "WEIGHT_KG"] = np.nan
for i in wt_idx:
    injected_errors.append(("VS", vs.loc[i, "SUBJID"], "WEIGHT_KG", "Missing value"))

# 3d. Visit date before enrollment (logic error) - corrupt a few Baseline dates
logic_idx = vs[vs["VISIT"] == "Baseline"].sample(3, random_state=9).index
vs.loc[logic_idx, "VISIT_DATE"] = "2024-01-15"  # before any enrollment
for i in logic_idx:
    injected_errors.append(("VS", vs.loc[i, "SUBJID"], "VISIT_DATE", "Visit date precedes enrollment date"))

vs.to_csv(f"{OUT_DIR}/VS_raw.csv", index=False)

# ---------------------------------------------------------------------------
# 4. LAB VALUES incl. Phytochemical Marker (LB)
# ---------------------------------------------------------------------------
lb_rows = []
for subj in dm["SUBJID"].unique():
    for visit in ["Screening", "Baseline", "Week 4", "Week 8", "Week 12"]:
        lb_rows.append({
            "SUBJID": subj,
            "VISIT": visit,
            "ALT_U_L": round(np.random.normal(28, 8), 1),          # liver enzyme
            "AST_U_L": round(np.random.normal(26, 7), 1),
            "CREATININE_MG_DL": round(np.random.normal(0.9, 0.2), 2),
            "HSCRP_MG_L": round(abs(np.random.normal(2.1, 1.2)), 2),  # inflammation marker
            "MARKER_COMPOUND_NG_ML": round(abs(np.random.normal(45, 15)), 1),  # phytochemical marker (e.g., withanolide-type)
        })

lb = pd.DataFrame(lb_rows)

# Inject errors into LB
# 4a. Hepatotoxicity signal (ALT/AST way out of normal range - clinically relevant for herbal safety)
hep_idx = lb.sample(3, random_state=10).index
lb.loc[hep_idx, "ALT_U_L"] = [180.0, 210.0, 150.0]
for i in hep_idx:
    injected_errors.append(("LB", lb.loc[i, "SUBJID"], "ALT_U_L", "Marked elevation - possible hepatotoxicity signal"))

# 4b. Negative lab value (impossible)
neg_idx = lb.sample(2, random_state=11).index
lb.loc[neg_idx, "CREATININE_MG_DL"] = [-0.5, -1.1]
for i in neg_idx:
    injected_errors.append(("LB", lb.loc[i, "SUBJID"], "CREATININE_MG_DL", "Negative value (impossible)"))

# 4c. Missing marker compound level
miss_idx = lb.sample(4, random_state=12).index
lb.loc[miss_idx, "MARKER_COMPOUND_NG_ML"] = np.nan
for i in miss_idx:
    injected_errors.append(("LB", lb.loc[i, "SUBJID"], "MARKER_COMPOUND_NG_ML", "Missing value"))

lb.to_csv(f"{OUT_DIR}/LB_raw.csv", index=False)

# ---------------------------------------------------------------------------
# 5. ADVERSE EVENTS (AE)
# ---------------------------------------------------------------------------
ae_terms = ["Nausea", "Mild GI upset", "Headache", "Diarrhoea", "Dizziness",
            "Skin rash", "Fatigue", "Constipation", "Elevated liver enzymes"]
severities = ["Mild", "Moderate", "Severe"]

ae_rows = []
ae_id_counter = 1
for subj in dm["SUBJID"].unique():
    n_ae = np.random.poisson(0.6)  # most subjects have 0-1 AEs
    for _ in range(n_ae):
        onset_day = random.randint(0, 90)
        duration = random.randint(1, 14)
        severity = random.choices(severities, weights=[0.7, 0.25, 0.05])[0]
        serious = "Y" if severity == "Severe" and random.random() < 0.3 else "N"
        ae_rows.append({
            "AE_ID": f"AE-{ae_id_counter:04d}",
            "SUBJID": subj,
            "AE_TERM": random.choice(ae_terms),
            "ONSET_DAY": onset_day,
            "DURATION_DAYS": duration,
            "SEVERITY": severity,
            "SERIOUS": serious,
            "RELATED_TO_STUDY_DRUG": random.choice(["Related", "Not Related", "Possibly Related"]),
            "OUTCOME": random.choice(["Resolved", "Resolving", "Ongoing"]),
            "REPORTED_DATE_DAY": onset_day + random.randint(0, 3),  # days after onset that it was reported
        })
        ae_id_counter += 1

ae = pd.DataFrame(ae_rows)

# Guarantee at least 2 genuine SAEs exist, so SAE-timeline logic is always
# exercised regardless of random draw (rather than depending on chance,
# which previously could silently yield zero SAEs on some runs).
if len(ae) >= 2:
    guaranteed_sae_idx = ae.sample(2, random_state=20).index
    ae.loc[guaranteed_sae_idx, "SEVERITY"] = "Severe"
    ae.loc[guaranteed_sae_idx, "SERIOUS"] = "Y"

# Inject errors into AE
# 5a. SAE reported late (protocol requires SAE reporting within 1 day / 24hr rule)
if len(ae[ae["SERIOUS"] == "Y"]) > 0:
    sae_idx = ae[ae["SERIOUS"] == "Y"].index
    for i in sae_idx[:min(2, len(sae_idx))]:
        ae.loc[i, "REPORTED_DATE_DAY"] = ae.loc[i, "ONSET_DAY"] + 5  # reported 5 days late
        injected_errors.append(("AE", ae.loc[i, "SUBJID"], "REPORTED_DATE_DAY", "SAE reported >24hrs after onset (regulatory breach)"))

# 5b. Negative duration (impossible / data entry error)
if len(ae) > 3:
    neg_idx = ae.sample(2, random_state=13).index
    ae.loc[neg_idx, "DURATION_DAYS"] = [-3, -1]
    for i in neg_idx:
        injected_errors.append(("AE", ae.loc[i, "SUBJID"], "DURATION_DAYS", "Negative duration (impossible)"))

# 5c. Missing severity
if len(ae) > 5:
    miss_idx = ae.sample(2, random_state=14).index
    ae.loc[miss_idx, "SEVERITY"] = np.nan
    for i in miss_idx:
        injected_errors.append(("AE", ae.loc[i, "SUBJID"], "SEVERITY", "Missing value"))

ae.to_csv(f"{OUT_DIR}/AE_raw.csv", index=False)

# ---------------------------------------------------------------------------
# 6. CONCOMITANT MEDICATIONS (CM)
# ---------------------------------------------------------------------------
cm_meds = ["Paracetamol", "Omeprazole", "Metformin", "Amlodipine", "Vitamin D3", "Calcium supplement"]
cm_rows = []
for subj in dm["SUBJID"].unique():
    n_cm = np.random.poisson(0.8)
    for _ in range(n_cm):
        cm_rows.append({
            "SUBJID": subj,
            "CM_NAME": random.choice(cm_meds),
            "START_DAY": random.randint(-30, 60),
            "ONGOING": random.choice(["Y", "N"]),
        })

cm = pd.DataFrame(cm_rows)
cm.to_csv(f"{OUT_DIR}/CM_raw.csv", index=False)

# ---------------------------------------------------------------------------
# Save the injected error log (ground truth for pipeline validation)
# ---------------------------------------------------------------------------
err_log = pd.DataFrame(injected_errors, columns=["DOMAIN", "SUBJID", "FIELD", "ISSUE_DESCRIPTION"])
err_log.to_csv(f"{OUT_DIR}/_injected_errors_log.csv", index=False)

print(f"Generated {len(dm)} DM records, {len(ex)} EX records, {len(vs)} VS records,")
print(f"{len(lb)} LB records, {len(ae)} AE records, {len(cm)} CM records.")
print(f"Total deliberately injected errors: {len(err_log)}")
print("\nDomain breakdown of injected errors:")
print(err_log.groupby("DOMAIN").size())
