# HCP Conversion Atlas — ICI Dashboard

**Healthcare Professional Conversion Atlas** powered by the Interaction Conversion Index (ICI).

## What this does

Upload masked ATU + PET Excel files → full dashboard automatically appears with:

| View | Contents |
|---|---|
| Approach | Methodology, ICI formula, clustering rules |
| Overview | Hero metrics, ATU×PET bridge, 5-cluster journey, dimension health |
| Integrated Insights | Adoption funnel, message recall by user type, cluster profiles |
| Cross-Tab Repository | 100+ cross-tabs: VA×ATU, LTIP×ATU, ServierONE×ATU, ICI×ATU — with statsig |
| Qualitative Analysis | Auto-themed voice responses, verbatim samples, theme cross-tabs |
| Custom Rep Support Card | Profile picker → dominant cluster → action flow + opener + talking points |

## Deploy to Streamlit Cloud (free)

### Step 1 — Push to GitHub

```bash
git init
git add .
git commit -m "ICI Dashboard v1"
git remote add origin https://github.com/YOUR_USERNAME/ici-dashboard.git
git push -u origin main
```

### Step 2 — Deploy on Streamlit Cloud

1. Go to **[share.streamlit.io](https://share.streamlit.io)**
2. Click **New app**
3. Select your GitHub repo
4. Set **Main file path** to `app.py`
5. Click **Deploy**

Your dashboard will be live at:
```
https://YOUR_USERNAME-ici-dashboard-app-XXXXX.streamlit.app
```

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## File structure

```
ici_dashboard/
├── app.py                    # Main Streamlit app
├── data_engine.py            # ATU+PET data extraction + ICI calculation
├── requirements.txt
├── README.md
└── views/
    ├── __init__.py
    ├── approach.py           # Methodology view
    ├── overview.py           # Hero dashboard
    ├── integrated.py         # ATU×PET adoption funnel
    ├── crosstabs.py          # 100 cross-tabs + statsig
    ├── qualitative.py        # Auto-themed voice responses
    └── envelope.py           # Custom rep support card
```

## Data requirements

Upload **masked** (de-identified) Excel files exported from LimeSurvey:

| File | Description | Quarters |
|---|---|---|
| ATU workbook | Awareness Trial Usage raw responses | Q1+Q2 (or any 2 quarters) |
| PET workbook | Promotional Effectiveness Tracker raw | Q4+Q1+Q2 (or any 3 quarters) |

The engine auto-detects question codes from row 2 of ATU and row 4 of PET (standard LimeSurvey export format). Column positions can change between quarters — the scanner matches by question code prefix, not column position.

## ICI Dimensions

| Dimension | Code | Weight | Key Questions |
|---|---|---|---|
| Awareness Conversion | AC | 14% | Q2_10Z (unaided), Q2_20Z (familiarity), Q3_300Z (patient inquiry), Q2_10Z_PET (msg recall) |
| Intent → Behavior | IBC | 25% | Q3_60Z (current/future Vora share), Q3_20Z_PET (agreed prescribe), C3_35Z_PET (LTIP) |
| Message → Belief | MBC | 20% | Q3_120Z (Vora perf), Q3_40BZ_PET (attr shift), Q2_20Z_PET (motivating score) |
| Rep Trust | RTC | 13% | Q3_70Z_PET (call quality), Q3_60Z_PET (product knowledge), Q4_30Z (rep preferred) |
| Access Barrier Resolution | ABR | 15% | Q3_260A/B (ServierONE), Q3_220Z (barriers), Q1_100Z_PET (access VAs) |
| Knowledge Conversion | KCC | 8% | Q1_00Z (NGS rate), Q4_00Z (belief align), Q2_00Z (NCCN fam) |
| Competitive Influence | CI | 5% | Q3_120Z (Vora vs competitor gap), Q2_20Z comp items |

## Statistical testing

All cross-tabs use:
- **Mann-Whitney U test** (non-parametric, for continuous metrics)
- **Chi-square** (for binary/categorical outcomes)
- **Pearson r** (for dimension correlations)
- **Effect size**: Cohen's d (small <0.5, medium 0.5–0.8, large ≥0.8)
- **Significance threshold**: p < 0.05

## Notes

- The `any_va` field = 1 if ANY of Q1_100Z items 1–10 were selected in PET
- `ltip_top2` = 1 if C3_35Z (likelihood to increase prescribing) ≥ 6
- `servier_aware` = 1 if Q3_260AZ ≥ 3 OR any Q3_260BZ item selected
- Contradiction discount: if Q3_260AZ ≥ 4 but all Q3_260BZ = 0, ABR familiarity sub-score is halved
- AC is capped at 55 if unaided awareness = 0
- MBC is capped at 45 if attribute shift = 0

---
Built by XXX · YYY Glioma ATU+PET Programme · v2026.1
