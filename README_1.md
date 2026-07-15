# Clinical Data Management Pipeline — AYUSH Herbal Trial (RC-101)

**Design and Implementation of a Clinical Data Management (CDM) Pipeline for an
AYUSH/Herbal Drug Clinical Trial: A CDISC-Aligned Data Cleaning, Validation,
and Quality Control Framework**

Mock Phase II trial: *"A Randomized, Placebo-Controlled Phase II Study to
Evaluate the Efficacy and Safety of Rasnadi Compound (RC-101) in the
Management of Knee Osteoarthritis."* All data is synthetic.

## Why this project

Published AYUSH/Ayurvedic clinical trials (e.g. AYUSH-64 COVID-19 RCTs) follow
GCP-ASU and ICMR ethical guidelines but do not use CDISC CDASH/SDTM
structuring — that standardization is essentially universal in allopathic
pharma trials (FDA-facing submissions) but not yet routine in AYUSH research.
This project applies that CDISC rigor to a simulated AYUSH trial, including a
non-standard SUPPDM domain to capture Ayurvedic Prakriti typing, which has no
native CDISC domain.

## What's included

```
ayush_cdm_project/
├── scripts/
│   ├── 01_generate_mock_data.py       synthetic raw domains + 42 seeded errors
│   ├── 02_data_validation_pipeline.py cleaning, checks, query log generation
│   ├── 03_sdtm_mapping.py             raw -> CDISC SDTM (DM, EX, VS, LB, AE, SUPPDM)
│   └── 04_generate_dmp.js             Data Management Plan (.docx)
├── data/
│   ├── raw/        DM, EX, VS, LB, AE, CM domains + ground-truth error log
│   └── sdtm/       CDISC SDTM-mapped domains + mapping specification
├── reports/
│   ├── query_log.csv                  72 queries, DCF-style, Open/Severity tracked
│   ├── validation_summary.csv         counts by domain and severity
│   ├── pipeline_detection_check.csv   detection QC vs. ground truth (100%)
│   ├── ae_reconciliation_summary.csv  SAE + AE-Lab reconciliation summary
│   └── sae_detail_listing.csv         SAE-level detail with reporting lag
└── docs/
    ├── Protocol_Synopsis.docx         mock protocol synopsis
    ├── CRF_Templates.docx             CRF field specs for all 6 domains
    ├── Data_Management_Plan.docx      full DMP document
    └── dashboard.html                 standalone interactive dashboard (open in any browser)
```

## Pipeline results

- 80 subjects, 3 sites, 2 arms (RC-101 Test / Placebo), 7-visit schedule
- 42 deliberately embedded data quality issues across DM, EX, VS, LB, AE
- **100% detection rate** (42/42) by the automated validation pipeline
- 72 total queries raised (33 Query, 32 Critical, 3 Safety Signal,
  2 Protocol Deviation, 2 Regulatory Breach)
- 2 genuine SAEs, both correctly flagged for exceeding the 24-hour reporting
  timeline
- 4 AE-Lab reconciliation discrepancies identified via cross-domain checks
  (not explicitly seeded — found by the reconciliation logic itself)

## How to reproduce

```bash
python3 scripts/01_generate_mock_data.py        # generates data/raw/*.csv
python3 scripts/02_data_validation_pipeline.py  # generates reports/*.csv
python3 scripts/03_sdtm_mapping.py              # generates data/sdtm/*.csv
node scripts/04_generate_dmp.js                 # generates docs/*.docx
```

## Skills demonstrated

CDASH/SDTM mapping · GCP-aligned data management planning · automated data
validation (range, logic, duplicate, cross-domain checks) · AE/SAE safety
reconciliation and regulatory timeline compliance · query management
workflow · Python (pandas) · reproducible pipeline design
