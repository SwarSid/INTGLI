"""
Cross-Tab Repository — 100 cross-tabs connecting PET signals with ATU metrics.
Every stat computed from uploaded data. Full evidence blurb on every finding.
Significant results highlighted. Non-significant reported honestly.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.stats import mannwhitneyu, pearsonr

TEAL="#0F4C5C"; NAVY="#1E293B"; CRIMSON="#832232"; AMBER="#B8860B"; GREEN="#15803D"
LGRAY="#F8FAFC"; MGRAY="#E2E8F0"; DGRAY="#64748B"

ATTR_LABELS = [
    "Prolonged PFS","Tumor volume reduction","Prolonged OS","Low grade 3-4 AEs",
    "Low hepatic toxicity","Low hematological toxicity","Low neurotoxicity",
    "Low risk hypermutations","Manageable LFT monitoring","Good patient QoL",
    "Affordable","Manufacturer patient services","Easy to prescribe",
    "Convenient route","Low risk long-term SEs","Ability to preserve fertility",
    "Delays next treatment","Reduces seizures","Fair office compensation",
]

SPLIT_DEFINITIONS = {
    "VA Used vs Not": {
        "qa": "any_va==1", "qb": "any_va==0",
        "label_a": "VA Used", "label_b": "No VA",
        "pet_q": "PET Q1_100Z (any of 10 content types = 1)",
        "description": "Split on whether ANY visual aid content type was flagged as shown "
                       "during the most recent rep visit (PET Q1_100Z, 10 binary options). "
                       "VA Used = at least one content type selected.",
    },
    "LTIP Top-2 vs Non": {
        "qa": "ltip_top2==1", "qb": "ltip_top2==0",
        "label_a": "LTIP ≥6", "label_b": "LTIP <6",
        "pet_q": "PET C3_35Z (likelihood to increase prescribing, 1–7, top-2 = 6–7)",
        "description": "Likelihood to Increase Prescribing (LTIP) scored 1–7 on PET C3_35Z. "
                       "Top-2 box = score of 6 or 7. Non-Top-2 = score 1–5.",
    },
    "ServierONE Aware vs Not": {
        "qa": "s1_aware==1", "qb": "s1_aware==0",
        "label_a": "S1 Aware", "label_b": "S1 Unaware",
        "pet_q": "ATU Q3_260AZ (familiarity ≥3) OR Q3_260BZ (≥1 programme named)",
        "description": "ServierONE awareness = ATU Q3_260AZ score ≥3 (moderately familiar or above) "
                       "OR at least one programme named in Q3_260BZ. Unaware = Q3_260AZ <3 AND no programmes named.",
    },
    "High Recall vs Low": {
        "qa": "n_recalled>=5", "qb": "n_recalled<5",
        "label_a": "≥5 msgs recalled", "label_b": "<5 msgs recalled",
        "pet_q": "PET Q2_10Z (count of 10 messages recalled = 1, threshold = 5)",
        "description": "Message recall count from PET Q2_10Z (10 binary items, 1=recalled). "
                       "High Recall = 5 or more messages recalled. Low = fewer than 5.",
    },
    "Agreed to Prescribe vs Not": {
        "qa": "agreed==1", "qb": "agreed==0",
        "label_a": "Agreed to Rx", "label_b": "Did not agree",
        "pet_q": "PET Q3_20Z (agreed to prescribe after visit, Yes=1)",
        "description": "PET Q3_20Z: 'During your most recent interaction, did you agree to prescribe "
                       "[PRODUCT] for [INDICATION] for your next appropriate patient?' Yes=1, No=0.",
    },
    "Attr Shift vs No Shift": {
        "qa": "n_shift>0", "qb": "n_shift==0",
        "label_a": "≥1 attr shifted", "label_b": "No attr shifted",
        "pet_q": "PET Q3_40BZ (17 attribute perception ratings ≥6 = shifted, any>0 = shifted)",
        "description": "Attribute perception shift from PET Q3_40BZ (17 attributes rated 1–7 post-visit). "
                       "Shifted = at least one attribute rated 6 or 7. No shift = all rated 5 or below.",
    },
}

METRIC_DEFINITIONS = {
    "vora_share":    ("Current Voranigo Share %", "ATU Q3_60Z_B8 ÷ S0_120Z", "Voranigo patient count (Q3_60Z column 8, vorasidenib) divided by total Grade 2 patient load (S0_120Z). Represents current prescribing penetration among eligible patients."),
    "n_recalled":    ("Messages Recalled (0–10)", "PET Q2_10Z count", "Count of 10 brand messages (V1–V14 series) recalled as heard during most recent PET interaction. Each message = 1 binary item."),
    "n_shift":       ("Attribute Belief Shifts (0–17)", "PET Q3_40BZ count ≥6", "Number of the 17 product attributes (Q3_40BZ) rated 6 or 7 (out of 7) post-visit. Higher = more attributes with strong positive perception shift."),
    "barriers":      ("Barriers Cited (0–9)", "ATU Q3_220Z count", "Number of barriers to prescribing selected from the 9-option ATU Q3_220Z list. Lower = fewer barriers reported."),
    "progs_known":   ("ServierONE Programmes Known (0–5)", "ATU Q3_260BZ count", "Number of ServierONE support programmes named by the HCP (Q3_260BZ, 5 options: copay, bridge, PAP, QuickStart, LMN templates)."),
    "ngs_rate":      ("NGS Testing Rate (0–1)", "ATU Q1_00Z", "Combined NGS testing rate from ATU Q1_00Z: sum of % using NGS-only and % using IHC+NGS, divided by 100. Represents proportion of newly diagnosed diffuse glioma patients tested with NGS."),
    "belief_align":  ("Clinical Belief Alignment (1–7)", "ATU Q4_00Z avg (8 statements)", "Average of 8 clinical belief alignment statements from ATU Q4_00Z, each rated 1–7. Higher = stronger alignment with evidence supporting Voranigo use."),
    "nccn_fam":      ("NCCN Guideline Familiarity (1–5)", "ATU Q2_00Z", "Familiarity with NCCN CNS guidelines: 1=Never heard, 2=Heard but don't know, 3=A little familiar, 4=Somewhat familiar, 5=Very familiar."),
    "vora_fam":      ("Voranigo Familiarity (1–5)", "ATU Q2_20Z item k", "Voranigo familiarity scale from ATU Q2_20Z item k: 1=Never heard, 2=Heard but don't know, 3=Familiar not planning, 4=Planning but no opportunity, 5=Have used."),
    "unaided":       ("Unaided Awareness (0/1)", "ATU Q2_10Z text scan", "Binary: 1 if HCP mentioned 'voranigo', 'vorasidenib', or 'voras' in the unaided awareness open-end response (Q2_10Z). 0 = not mentioned."),
    "ltip":          ("LTIP Score (1–7)", "PET C3_35Z", "Raw LTIP (Likelihood to Increase Prescribing) score from PET C3_35Z, scale 1–7. Used directly as continuous variable in correlations."),
    "call_q":        ("Call Quality Score (1–7)", "PET Q3_70Z avg (5 attrs)", "Average of 5 overall call quality attributes from PET Q3_70Z: overall quality, preparedness, organisation, indication knowledge, time management."),
    "prod_k":        ("Product Knowledge Score (1–7)", "PET Q3_60Z avg (7 attrs)", "Average of 7 product knowledge attributes from PET Q3_60Z: product knowledge, treatment landscape, compelling reason, clear message, credible support, addressed questions, engagement."),
    "gr2_pl":        ("Grade 2 Patient Load", "ATU S0_120Z sum", "Total Grade 2 IDH-mutant patient load from ATU S0_120Z: sum of Grade 2 astrocytoma and Grade 2 oligodendroglioma patients currently under active management."),
    "future_intent": ("Future Voranigo Intent (0–10)", "ATU Q3_60Z_B8 next 10", "Sum of Voranigo allocations across all 12 patient types in the 'next 10 patients' question (Q3_60Z column 19), capped at 10. Higher = stronger forward-looking prescribing intent."),
    "curr_vora":     ("Current Voranigo Patients", "ATU Q3_60Z_B8 count", "Raw count of current patients on Voranigo across all 12 patient types (Q3_60Z column 8, vorasidenib-containing regimen)."),
    "rep_pref":      ("Rep as Preferred Source (0/1)", "ATU Q4_30Z", "Binary: 1 if HCP selected in-person or virtual rep discussion as a preferred information source for IDH-mutant glioma (ATU Q4_30Z first two items). 0 = rep not preferred."),
    "s1_fam":        ("ServierONE Familiarity (1–5)", "ATU Q3_260AZ", "Familiarity with ServierONE patient support programme from ATU Q3_260AZ: 1=Not at all familiar, 2=Somewhat familiar, 3=Moderately familiar, 4=Very familiar, 5=Extremely familiar."),
    "agreed":        ("Agreed to Prescribe (0/1)", "PET Q3_20Z", "Binary from PET Q3_20Z: 1 = agreed to prescribe for next appropriate patient, 0 = did not agree."),
    "peer_shared":   ("Peer Sharing (0–3)", "PET C3_25Z", "Peer sharing from PET C3_25Z: 0=No, 1=Not yet but intend to, 2=Yes within practice, 3=Yes within practice and extended network."),
    "pt_inq":        ("Patient Inquiry Frequency (1–4)", "ATU Q3_300Z", "How often patients ask about Voranigo: 1=Never, 2=Rarely, 3=Occasionally, 4=Very often."),
}


def _statsig(a_series, b_series):
    a = pd.to_numeric(a_series, errors="coerce").dropna()
    b = pd.to_numeric(b_series, errors="coerce").dropna()
    if len(a) < 3 or len(b) < 3:
        return None, False, 0, len(a), len(b)
    try:
        _, p = mannwhitneyu(a, b, alternative="two-sided")
        d = abs(a.mean() - b.mean()) / np.sqrt((a.std()**2 + b.std()**2) / 2) if (a.std() + b.std()) > 0 else 0
        effect = "Large" if d >= 0.8 else "Medium" if d >= 0.5 else "Small"
        return round(p, 3), p < 0.05, effect, len(a), len(b)
    except Exception:
        return None, False, "", len(a), len(b)


def _sig_chip(p, sig):
    if p is None:
        return '<span style="background:#F1F5F9;color:#94A3B8;padding:2px 8px;border-radius:4px;font-size:10px">insufficient n</span>'
    if sig:
        return f'<span style="background:#15803D22;color:#15803D;padding:2px 8px;border-radius:4px;font-size:10px;font-weight:700">✓ p={p} SIGNIFICANT</span>'
    return f'<span style="background:#FEF3C7;color:#92400E;padding:2px 8px;border-radius:4px;font-size:10px">p={p} not significant</span>'


def _xt_card(idx, split_name, split_def, metric_key, metric_def, df, counter):
    """Render one cross-tab card with full evidence blurb."""
    label_a = split_def["label_a"]
    label_b = split_def["label_b"]
    metric_label, metric_q, metric_desc = metric_def

    grp_a = df.query(split_def["qa"])[metric_key].dropna() if split_def["qa"] else df[metric_key].dropna()
    grp_b = df.query(split_def["qb"])[metric_key].dropna() if split_def["qb"] else pd.Series()

    if grp_a.empty or grp_b.empty:
        return

    p, sig, effect, n_a, n_b = _statsig(grp_a, grp_b)
    mean_a = round(grp_a.mean(), 2)
    mean_b = round(grp_b.mean(), 2)
    delta  = round(mean_a - mean_b, 2)

    border_color = GREEN if sig else MGRAY
    bg_color = "#F0FDF4" if sig else "white"

    st.markdown(f"""
<div style="background:{bg_color};border:1px solid {border_color};border-left:4px solid {border_color};
            border-radius:12px;padding:16px 20px;margin-bottom:10px">
  <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:12px">
    <div style="flex:1">
      <div style="font-size:9px;text-transform:uppercase;letter-spacing:.2em;
                  color:#94A3B8;font-weight:600;margin-bottom:4px">
        CROSS-TAB #{counter:03d} · {split_name} × {metric_label}
      </div>
      <div style="font-size:15px;font-weight:600;color:#0F172A;margin-bottom:4px">
        {split_name} → {metric_label}
      </div>
      <div style="font-size:12px;color:{DGRAY};line-height:1.5">
        <b>{label_a}</b> (n={n_a}): avg <b>{mean_a}</b> &nbsp;vs&nbsp;
        <b>{label_b}</b> (n={n_b}): avg <b>{mean_b}</b> &nbsp;·&nbsp;
        Δ = <b>{'+' if delta>0 else ''}{delta}</b>
      </div>
    </div>
    <div style="text-align:right;flex-shrink:0">
      {_sig_chip(p, sig)}
      {f'<div style="font-size:10px;color:#94A3B8;margin-top:4px">Effect: {effect}</div>' if effect else ''}
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    with st.expander("↳ How this number was derived — full methodology"):
        st.markdown(f"""
<div style="background:{LGRAY};border-radius:8px;padding:16px 18px;border-left:3px solid {TEAL}">
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:14px">
    <div style="background:white;border-radius:8px;padding:12px 14px">
      <div style="font-size:9px;text-transform:uppercase;letter-spacing:.18em;
                  color:#94A3B8;font-weight:600;margin-bottom:4px">GROUP A — {label_a.upper()}</div>
      <div style="font-size:24px;font-weight:700;color:#0F172A">{mean_a}</div>
      <div style="font-size:11px;color:{DGRAY}">n = {n_a} HCPs · avg {metric_label}</div>
      <div style="font-size:10px;color:#94A3B8;margin-top:4px">Filter: {split_def['qa']}</div>
    </div>
    <div style="background:white;border-radius:8px;padding:12px 14px">
      <div style="font-size:9px;text-transform:uppercase;letter-spacing:.18em;
                  color:#94A3B8;font-weight:600;margin-bottom:4px">GROUP B — {label_b.upper()}</div>
      <div style="font-size:24px;font-weight:700;color:#0F172A">{mean_b}</div>
      <div style="font-size:11px;color:{DGRAY}">n = {n_b} HCPs · avg {metric_label}</div>
      <div style="font-size:10px;color:#94A3B8;margin-top:4px">Filter: {split_def['qb']}</div>
    </div>
  </div>

  <div style="margin-bottom:12px">
    <div style="font-size:10px;text-transform:uppercase;letter-spacing:.15em;
                color:{TEAL};font-weight:700;margin-bottom:4px">HOW THE SPLIT WAS MADE</div>
    <div style="font-size:12px;color:#334155;line-height:1.6">{split_def['description']}</div>
    <div style="font-size:10px;color:#94A3B8;margin-top:4px">Source question: {split_def['pet_q']}</div>
  </div>

  <div style="margin-bottom:12px">
    <div style="font-size:10px;text-transform:uppercase;letter-spacing:.15em;
                color:{TEAL};font-weight:700;margin-bottom:4px">HOW THE METRIC WAS COMPUTED</div>
    <div style="font-size:12px;color:#334155;line-height:1.6">{metric_desc}</div>
    <div style="font-size:10px;color:#94A3B8;margin-top:4px">Source question: {metric_q}</div>
  </div>

  <div style="background:{'#F0FDF4' if sig else '#FFFBEB'};border-radius:6px;
              padding:10px 12px;border-left:3px solid {'#15803D' if sig else AMBER}">
    <div style="font-size:10px;text-transform:uppercase;letter-spacing:.15em;
                color:{'#15803D' if sig else '#92400E'};font-weight:700;margin-bottom:4px">
      STATISTICAL TEST RESULT
    </div>
    <div style="font-size:12px;color:#334155;line-height:1.6">
      <b>Test:</b> Mann-Whitney U (non-parametric, two-sided)<br>
      <b>p-value:</b> {p if p is not None else 'N/A'} &nbsp;·&nbsp;
      <b>Significant at p&lt;0.05:</b> {'Yes ✓' if sig else 'No'}<br>
      {'<b>Effect size (Cohen\'s d):</b> ' + str(effect) + '<br>' if effect else ''}
      <b>n(A):</b> {n_a} · <b>n(B):</b> {n_b} · <b>Total:</b> {n_a+n_b}<br>
      {'<b>⚠ Note:</b> This result is NOT statistically significant. The difference in means (' + str(abs(delta)) + ') could be due to chance at this sample size (n=' + str(n_a+n_b) + '). Reported as observed without adjustment.' if not sig and p is not None else ''}
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


def _perf_attr_xtabs(df, split_name, split_def, counter_start):
    """Generate cross-tabs for all 19 Voranigo performance attributes."""
    counter = counter_start
    results = []
    for attr in ATTR_LABELS:
        col = f"perf_{attr}"
        if col not in df.columns:
            continue
        grp_a = df.query(split_def["qa"])[col].dropna()
        grp_b = df.query(split_def["qb"])[col].dropna()
        if grp_a.empty or grp_b.empty:
            continue
        p, sig, effect, n_a, n_b = _statsig(grp_a, grp_b)
        results.append({
            "attr": attr, "col": col, "mean_a": round(grp_a.mean(),2),
            "mean_b": round(grp_b.mean(),2), "p": p, "sig": sig,
            "effect": effect, "n_a": n_a, "n_b": n_b,
        })
        counter += 1

    if not results:
        return counter

    # Render as a heatmap-style table
    st.markdown(f"""
<div style="background:white;border:1px solid {MGRAY};border-radius:12px;padding:16px 20px;margin-bottom:16px">
  <div style="font-size:9px;text-transform:uppercase;letter-spacing:.2em;color:#94A3B8;font-weight:600;margin-bottom:4px">
    CROSS-TABS #{counter_start:03d}–{counter:03d} · {split_name} × VORANIGO PERFORMANCE (ALL 19 ATTRIBUTES)
  </div>
  <div style="font-size:14px;font-weight:600;color:#0F172A;margin-bottom:4px">
    {split_name} → Voranigo Attribute Perception (Q3_120Z, 1–7)
  </div>
  <div style="font-size:11px;color:#94A3B8;margin-bottom:12px">
    Source: ATU Q3_120Z Voranigo column (cols 20–38). Each attribute rated 1–7 by HCPs aware of Voranigo.
  </div>
</div>
""", unsafe_allow_html=True)

    fig = go.Figure()
    attrs_sorted = sorted(results, key=lambda x: x["mean_a"] - x["mean_b"], reverse=True)
    colors_a = [GREEN if r["sig"] else TEAL for r in attrs_sorted]
    colors_b = [CRIMSON if r["sig"] else "#94A3B8" for r in attrs_sorted]

    fig.add_trace(go.Bar(
        name=split_def["label_a"], x=[r["attr"] for r in attrs_sorted],
        y=[r["mean_a"] for r in attrs_sorted], marker_color=colors_a,
        text=[f'{r["mean_a"]:.1f}{"*" if r["sig"] else ""}' for r in attrs_sorted],
        textposition="outside",
    ))
    fig.add_trace(go.Bar(
        name=split_def["label_b"], x=[r["attr"] for r in attrs_sorted],
        y=[r["mean_b"] for r in attrs_sorted], marker_color=colors_b,
        text=[f'{r["mean_b"]:.1f}' for r in attrs_sorted],
        textposition="outside",
    ))
    fig.update_layout(
        barmode="group", height=380,
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Inter", size=10),
        yaxis=dict(range=[0, 8], showgrid=True, gridcolor="#F1F5F9", title="Avg rating (1–7)"),
        xaxis_tickangle=-35,
        legend=dict(orientation="h", yanchor="bottom", y=-0.4),
        margin=dict(l=0, r=0, t=10, b=0),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('<div style="font-size:10px;color:#94A3B8">* = statistically significant (p&lt;0.05, Mann-Whitney U)</div>', unsafe_allow_html=True)

    with st.expander("↳ See individual p-values for all 19 attributes"):
        rows = ""
        for r in attrs_sorted:
            sig_txt = f'<span style="color:#15803D;font-weight:700">✓ p={r["p"]}</span>' if r["sig"] else f'p={r["p"]} n.s.'
            delta = round(r["mean_a"] - r["mean_b"], 2)
            rows += f'<tr><td style="padding:4px 8px;font-size:11px">{r["attr"]}</td><td style="padding:4px 8px;text-align:center;font-size:11px">{r["mean_a"]}</td><td style="padding:4px 8px;text-align:center;font-size:11px">{r["mean_b"]}</td><td style="padding:4px 8px;text-align:center;font-size:11px">{"+" if delta>0 else ""}{delta}</td><td style="padding:4px 8px;font-size:11px">{sig_txt}</td><td style="padding:4px 8px;text-align:center;font-size:11px">{r["n_a"]}/{r["n_b"]}</td></tr>'
        st.markdown(f'<table style="width:100%;border-collapse:collapse"><tr style="background:{LGRAY}"><th style="padding:4px 8px;text-align:left;font-size:10px">Attribute</th><th style="padding:4px 8px;font-size:10px">{split_def["label_a"]}</th><th style="padding:4px 8px;font-size:10px">{split_def["label_b"]}</th><th style="padding:4px 8px;font-size:10px">Δ</th><th style="padding:4px 8px;text-align:left;font-size:10px">p-value</th><th style="padding:4px 8px;font-size:10px">n(A/B)</th></tr>{rows}</table>', unsafe_allow_html=True)

    return counter


def render(eng):
    df = eng.hcps_df
    if df is None or df.empty:
        st.warning("No data loaded.")
        return

    n = len(df)

    # ── Header ──
    st.markdown(f"""
<div style="margin-bottom:16px">
  <div style="font-size:10px;text-transform:uppercase;letter-spacing:.28em;
              color:{CRIMSON};font-weight:600">CROSS-TAB REPOSITORY</div>
  <h1 style="font-family:'DM Serif Display',serif;font-size:44px;font-weight:300;
             color:#0F172A;line-height:1.05;margin-bottom:10px">
    Every PET signal.<br>
    <span style="color:{TEAL}">Every ATU metric. Every p-value.</span>
  </h1>
  <p style="font-size:14px;color:#475569;max-width:700px;line-height:1.65">
    {n} matched HCPs · {len(SPLIT_DEFINITIONS)} split variables (PET) ×
    {len(METRIC_DEFINITIONS)} outcome metrics (ATU) = up to {len(SPLIT_DEFINITIONS)*len(METRIC_DEFINITIONS)} cross-tabs.
    Every finding includes the exact question codes, group definitions, means,
    sample sizes, and Mann-Whitney U test result. Non-significant results reported honestly.
  </p>
</div>
""", unsafe_allow_html=True)

    # ── Summary sig table ──
    all_results = []
    for split_name, split_def in SPLIT_DEFINITIONS.items():
        for metric_key, metric_def in METRIC_DEFINITIONS.items():
            if metric_key not in df.columns:
                continue
            grp_a = df.query(split_def["qa"])[metric_key].dropna()
            grp_b = df.query(split_def["qb"])[metric_key].dropna()
            if grp_a.empty or grp_b.empty:
                continue
            p, sig, effect, n_a, n_b = _statsig(grp_a, grp_b)
            all_results.append({
                "Split": split_name, "Metric": metric_def[0],
                "Group A mean": round(grp_a.mean(), 2),
                "Group B mean": round(grp_b.mean(), 2),
                "Δ": round(grp_a.mean() - grp_b.mean(), 2),
                "n(A)": n_a, "n(B)": n_b,
                "p-value": p, "Significant": "✓" if sig else "—",
            })

    results_df = pd.DataFrame(all_results)
    sig_df  = results_df[results_df["Significant"] == "✓"]
    ns_df   = results_df[results_df["Significant"] == "—"]

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="mcard"><div class="mlabel">TOTAL CROSS-TABS</div><div class="mval">{len(all_results)}</div><div class="msub">Computed from {n} matched HCPs</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div style="background:{GREEN};border-radius:16px;padding:24px"><div style="font-size:10px;text-transform:uppercase;letter-spacing:.22em;color:rgba(255,255,255,.6);font-weight:600">SIGNIFICANT (p&lt;0.05)</div><div style="font-family:\'DM Serif Display\',serif;font-size:48px;font-weight:300;color:white;line-height:1">{len(sig_df)}</div><div style="font-size:12px;color:rgba(255,255,255,.6)">Mann-Whitney U test</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="mcard"><div class="mlabel">NOT SIGNIFICANT</div><div class="mval">{len(ns_df)}</div><div class="msub">Reported as observed</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Significant findings summary ──
    if not sig_df.empty:
        st.markdown(f"""
<div style="background:#F0FDF4;border:1px solid #15803D44;border-radius:12px;
            padding:16px 20px;margin-bottom:20px">
  <div style="font-size:10px;text-transform:uppercase;letter-spacing:.2em;
              color:#15803D;font-weight:700;margin-bottom:8px">
    ✓ {len(sig_df)} STATISTICALLY SIGNIFICANT FINDINGS FROM YOUR DATA
  </div>
""", unsafe_allow_html=True)
        for _, row in sig_df.iterrows():
            delta_str = f"+{row['Δ']}" if row['Δ'] > 0 else str(row['Δ'])
            st.markdown(f"""
<div style="display:flex;align-items:center;gap:12px;padding:6px 0;border-bottom:1px solid #BBF7D0">
  <div style="width:180px;font-size:11px;font-weight:600;color:#166534">{row['Split']}</div>
  <div style="flex:1;font-size:11px;color:#334155">→ {row['Metric']}</div>
  <div style="font-size:11px;color:#334155">{row['Group A mean']} vs {row['Group B mean']}</div>
  <div style="font-size:11px;font-weight:600;color:#15803D;width:50px">{delta_str}</div>
  <div style="font-size:10px;color:#15803D;background:#BBF7D0;padding:1px 6px;
              border-radius:3px;font-weight:700">p={row['p-value']}</div>
</div>
""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Download full table ──
    csv = results_df.to_csv(index=False)
    st.download_button("⬇ Download full cross-tab table (CSV)", data=csv,
                       file_name="ici_crosstab_all.csv", mime="text/csv")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Tabs for each split ──
    tab_labels = list(SPLIT_DEFINITIONS.keys())
    tabs = st.tabs(tab_labels + ["📊 All Attribute Perceptions", "📋 Full Summary Table"])
    counter = 1

    for tab_idx, (split_name, split_def) in enumerate(SPLIT_DEFINITIONS.items()):
        with tabs[tab_idx]:
            # Section header
            grp_a_all = df.query(split_def["qa"])
            grp_b_all = df.query(split_def["qb"])
            st.markdown(f"""
<div style="background:white;border:1px solid {MGRAY};border-radius:12px;
            padding:14px 18px;margin-bottom:16px">
  <div style="font-size:14px;font-weight:600;color:#0F172A;margin-bottom:4px">
    {split_name}
    <span style="font-size:11px;font-weight:400;color:#94A3B8;margin-left:8px">
      {split_def['label_a']}: n={len(grp_a_all)} &nbsp;|&nbsp;
      {split_def['label_b']}: n={len(grp_b_all)}
    </span>
  </div>
  <div style="font-size:12px;color:{DGRAY};margin-bottom:6px">{split_def['description']}</div>
  <div style="font-size:10px;color:#94A3B8">Source: {split_def['pet_q']}</div>
</div>
""", unsafe_allow_html=True)

            # One card per metric
            for metric_key, metric_def in METRIC_DEFINITIONS.items():
                if metric_key not in df.columns:
                    continue
                _xt_card(tab_idx, split_name, split_def,
                         metric_key, metric_def, df, counter)
                counter += 1

    # Tab: All attribute perceptions
    with tabs[len(SPLIT_DEFINITIONS)]:
        st.markdown(f"""
<div style="font-family:'DM Serif Display',serif;font-size:24px;color:#0F172A;margin-bottom:8px">
  Voranigo Attribute Perception × All Splits
</div>
<div style="font-size:12px;color:#94A3B8;margin-bottom:16px">
  All 19 product attributes from ATU Q3_120Z (Voranigo column, 1–7) broken out by each PET split variable.
  * = significant at p&lt;0.05.
</div>
""", unsafe_allow_html=True)
        for split_name, split_def in SPLIT_DEFINITIONS.items():
            st.markdown(f"### {split_name}")
            counter = _perf_attr_xtabs(df, split_name, split_def, counter)
            st.markdown("---")

    # Tab: Full summary table
    with tabs[len(SPLIT_DEFINITIONS) + 1]:
        st.markdown(f"""
<div style="font-family:'DM Serif Display',serif;font-size:22px;color:#0F172A;margin-bottom:12px">
  Full Cross-Tab Summary — {len(all_results)} comparisons
</div>
""", unsafe_allow_html=True)
        # Style significant rows
        def highlight_sig(row):
            if row["Significant"] == "✓":
                return ["background-color: #F0FDF4"] * len(row)
            return [""] * len(row)
        st.dataframe(
            results_df.style.apply(highlight_sig, axis=1),
            use_container_width=True, height=600
        )
        st.download_button("⬇ Download CSV", data=csv,
                           file_name="ici_crosstab_all.csv", mime="text/csv",
                           key="dl2")
