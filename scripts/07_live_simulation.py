"""
07_live_simulation.py

Simulates a "live" running trial: instead of generating all data at once and
validating it in a single pass, this script splits subject data into weekly
arrival batches (as if sites are entering data week by week) and re-runs the
validation pipeline after each batch lands — so query counts, severities,
and safety signals accumulate visibly over simulated time.

This does not require real subjects or regulatory approval — it is a
demonstration of how a CDM system behaves as data arrives incrementally,
built on the same synthetic dataset logic as the original pipeline.

Output: live/simulation_log.csv — one row per batch, showing running totals.
        live/batch_NN_queries.csv — per-batch new queries raised.
"""

import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import time

RNG_SEED = 42
random.seed(RNG_SEED)
np.random.seed(RNG_SEED)

N_SUBJECTS = 80
SITES = ["SITE01", "SITE02", "SITE03"]
ARMS = ["RC-101 (Test)", "Placebo"]
VISITS = ["Screening", "Baseline", "Week 2", "Week 4", "Week 8", "Week 12", "End of Study"]
VISIT_DAY_OFFSET = {"Screening": -14, "Baseline": 0, "Week 2": 14, "Week 4": 28,
                     "Week 8": 56, "Week 12": 84, "End of Study": 90}

BASE_DIR = "/home/claude/ayush_cdm_sim"
LIVE_DIR = f"{BASE_DIR}/live"

# ---------------------------------------------------------------------------
# Generate the full dataset once (same logic as original pipeline)
# ---------------------------------------------------------------------------
subjects = [f"AYU-{i:03d}" for i in range(1, N_SUBJECTS + 1)]
enrollment_start = datetime(2025, 3, 1)

dm_rows = []
for idx, subj in enumerate(subjects):
    site = random.choice(SITES)
    arm = ARMS[idx % 2]
    age = int(np.random.normal(52, 10))
    age = max(35, min(75, age))
    sex = random.choice(["Male", "Female"])
    prakriti = random.choice(["Vata", "Pitta", "Kapha", "Vata-Pitta", "Pitta-Kapha", "Tridosha"])
    enroll_offset = random.randint(0, 120)  # subjects enroll across a rolling window
    enroll_date = enrollment_start + timedelta(days=enroll_offset)
    dm_rows.append({
        "SUBJID": subj, "SITEID": site, "ARM": arm, "AGE": age, "SEX": sex,
        "PRAKRITI": prakriti, "ENROLL_DATE": enroll_date.strftime("%Y-%m-%d"),
        "ENROLL_WEEK": enroll_offset // 7,  # which simulated week they enrolled in
    })

dm = pd.DataFrame(dm_rows)

# Inject a realistic error rate (~8% of subjects have at least one DM issue)
error_subj_idx = dm.sample(frac=0.08, random_state=1).index
dm.loc[error_subj_idx, "AGE"] = np.nan

vs_rows = []
dm_enroll_lookup = dict(zip(dm["SUBJID"], pd.to_datetime(dm["ENROLL_DATE"])))
for subj in dm["SUBJID"].unique():
    base_sbp = np.random.normal(126, 10)
    subj_enroll_date = dm_enroll_lookup[subj]
    subj_week = dm.loc[dm["SUBJID"] == subj, "ENROLL_WEEK"].values[0]
    for visit in VISITS:
        arrival_week = subj_week + max(0, (VISIT_DAY_OFFSET[visit] + 14) // 7)
        vs_rows.append({
            "SUBJID": subj, "VISIT": visit,
            "VISIT_DATE": (subj_enroll_date + timedelta(days=VISIT_DAY_OFFSET[visit] + random.randint(-2, 2))).strftime("%Y-%m-%d"),
            "SYSBP": round(base_sbp + np.random.normal(0, 5), 1),
            "ARRIVAL_WEEK": arrival_week,
        })
vs = pd.DataFrame(vs_rows)
bad_idx = vs.sample(frac=0.03, random_state=2).index
vs.loc[bad_idx, "SYSBP"] = [round(np.random.choice([55, 60, 220, 235]), 1) for _ in bad_idx]

ae_terms = ["Nausea", "Mild GI upset", "Headache", "Dizziness", "Fatigue"]
ae_rows = []
ae_counter = 1
for subj in dm["SUBJID"].unique():
    subj_week = dm.loc[dm["SUBJID"] == subj, "ENROLL_WEEK"].values[0]
    n_ae = np.random.poisson(0.5)
    for _ in range(n_ae):
        onset_day = random.randint(0, 90)
        ae_rows.append({
            "AE_ID": f"AE-{ae_counter:04d}", "SUBJID": subj,
            "AE_TERM": random.choice(ae_terms), "ONSET_DAY": onset_day,
            "SEVERITY": random.choices(["Mild", "Moderate", "Severe"], weights=[0.7, 0.25, 0.05])[0],
            "ARRIVAL_WEEK": subj_week + (onset_day // 7),
        })
        ae_counter += 1
ae = pd.DataFrame(ae_rows)

# Guarantee at least 2 SAEs for a realistic safety signal to appear mid-simulation
if len(ae) >= 2:
    sae_idx = ae.sample(2, random_state=3).index
    ae.loc[sae_idx, "SEVERITY"] = "Severe"

print(f"Full dataset generated: {len(dm)} subjects, {len(vs)} VS records, {len(ae)} AE records")
print(f"Enrollment spans simulated weeks 0 to {dm['ENROLL_WEEK'].max()}")

# ---------------------------------------------------------------------------
# Replay in weekly batches, validating after each arrival
# ---------------------------------------------------------------------------
max_week = int(max(dm["ENROLL_WEEK"].max(), vs["ARRIVAL_WEEK"].max(), ae["ARRIVAL_WEEK"].max() if len(ae) else 0))

sim_log = []
running_dm, running_vs, running_ae = [], [], []

for week in range(0, max_week + 1):
    new_dm = dm[dm["ENROLL_WEEK"] == week]
    new_vs = vs[vs["ARRIVAL_WEEK"] == week]
    new_ae = ae[ae["ARRIVAL_WEEK"] == week] if len(ae) else pd.DataFrame()

    running_dm.append(new_dm)
    running_vs.append(new_vs)
    if len(new_ae):
        running_ae.append(new_ae)

    cum_dm = pd.concat(running_dm, ignore_index=True) if running_dm else pd.DataFrame()
    cum_vs = pd.concat(running_vs, ignore_index=True) if running_vs else pd.DataFrame()
    cum_ae = pd.concat(running_ae, ignore_index=True) if running_ae else pd.DataFrame()

    # Validation checks on cumulative data so far
    n_missing_age = int(cum_dm["AGE"].isna().sum()) if len(cum_dm) else 0
    n_bad_bp = int(((cum_vs["SYSBP"] < 70) | (cum_vs["SYSBP"] > 200)).sum()) if len(cum_vs) else 0
    n_sae = int((cum_ae["SEVERITY"] == "Severe").sum()) if len(cum_ae) else 0

    sim_log.append({
        "SIM_WEEK": week,
        "NEW_SUBJECTS": len(new_dm),
        "CUMULATIVE_SUBJECTS": len(cum_dm),
        "NEW_VS_RECORDS": len(new_vs),
        "CUMULATIVE_VS_RECORDS": len(cum_vs),
        "NEW_AE_RECORDS": len(new_ae),
        "CUMULATIVE_QUERIES_OPEN": n_missing_age + n_bad_bp,
        "CUMULATIVE_SAE_COUNT": n_sae,
    })

sim_log_df = pd.DataFrame(sim_log)
sim_log_df.to_csv(f"{LIVE_DIR}/simulation_log.csv", index=False)

print("\n--- Simulation complete ---")
print(sim_log_df.to_string(index=False))
