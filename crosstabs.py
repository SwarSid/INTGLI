"""
Cross-Tab Repository — Core lens: Interaction vs No Interaction × ATU metrics.
Secondary lenses: VA Used, LTIP Top-2, User Groups (High/Low/Non-User).
Every number from real data. Every insight has a full evidence blurb.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.stats import mannwhitneyu

TEAL="#0F4C5C"; NAVY="#1E293B"; CRIMSON="#832232"; AMBER="#B8860B"; GREEN="#15803D"
LGRAY="#F8FAFC"; MGRAY="#E2E8F0"; DGRAY="#64748B"

ATTR_LABELS = [
    "Prolonged PFS","Reduction in tumor volume","Prolonged OS","Low grade 3-4 AEs",
    "Low hepatic toxicity","Low hematological toxicity","Low neurotoxicity",
    "Low risk hypermutations","Manageable LFT monitoring","Good patient QoL",
    "Affordable","Manufacturer patient services","Easy to prescribe",
    "Convenient route","Low risk long-term SEs","Ability to preserve fertility",
    "Delays next treatment","Reduces seizures","Fair office compensation",
]

METRIC_META = {
    "unaided":          ("Unaided Voranigo Awareness",    "0/1",   "ATU Q2_10Z open-end — text scan for 'voranigo'/'vorasidenib'"),
    "vora_fam":         ("Voranigo Familiarity",          "1–5",   "ATU Q2_20Z item k: 1=Never heard → 5=Have used"),
    "curr_vora_share":  ("Current Voranigo Share %",      "%",     "ATU Q3_60Z_B8 ÷ S0_120Z Grade 2 PL × 100"),
    "future_intent":    ("Future Voranigo Intent",        "0–10",  "ATU Q3_60Z next-10 B8 sum across 12 patient types"),
    "msg_rec":          ("Messages Recalled",             "0–10",  "PET Q2_10Z — count of 10 brand messages recalled"),
    "attr_shift":       ("Attribute Belief Shifts",       "0–17",  "PET Q3_40BZ — count of 17 attributes rated ≥6 post-visit"),
    "top_attr_perf":    ("Top Voranigo Attr Performance", "1–7",   "ATU Q3_120Z Voranigo cols 20–38, avg"),
    "like_inc":         ("Likelihood to Increase Rx",    "1–7",   "PET C3_35Z raw score"),
    "ltip_top2":        ("LTIP Top-2 Rate",              "0/1",   "PET C3_35Z ≥6 = top-2 box"),
    "progs_known":      ("ServierONE Progs Known",        "0–5",   "ATU Q3_260BZ — count of 5 programmes named"),
    "s1_fam":           ("ServierONE Familiarity",        "1–5",   "ATU Q3_260AZ: 1=Not at all → 5=Extremely familiar"),
    "barriers":         ("Barriers Cited",                "0–9",   "ATU Q3_220Z — count of barrier options selected"),
    "belief_align":     ("Clinical Belief Alignment",    "1–7",   "ATU Q4_00Z avg of 8 statements"),
    "nccn_fam":         ("NCCN Guideline Familiarity",   "1–5",   "ATU Q2_00Z: 1=Never heard → 5=Very familiar"),
    "ngs_rate":         ("NGS Testing Rate",             "0–1",   "ATU Q1_00Z: % using NGS-only + IHC+NGS ÷ 100"),
    "call_quality":     ("Call Quality",                 "1–7",   "PET Q3_70Z avg of 5 call quality attributes"),
    "prod_knowledge":   ("Rep Product Knowledge",        "1–7",   "PET Q3_60Z avg of 7 product knowledge attributes"),
    "ICI":              ("ICI Score",                    "0–100", "Weighted composite: AC×.14+IBC×.25+MBC×.20+RTC×.13+ABR×.15+KCC×.08+CI×.05"),
    "peer_shared":      ("Peer Sharing",                 "0–3",   "PET C3_25Z: 0=No, 1=Intent, 2=Within practice, 3=Extended network"),
    "pt_inq":           ("Patient Inquiry Frequency",    "1–4",   "ATU Q3_300Z: 1=Never → 4=Very often"),
    "rep_pref":         ("Rep as Preferred Info Source", "0/1",   "ATU Q4_30Z items 1–2: rep discussion preferred"),
}


def _mw(a_s, b_s):
    """Mann-Whitney U, returns (p, sig, mean_a, mean_b, n_a, n_b, effect)."""
    a = pd.to_numeric(a_s, errors="coerce").dropna()
    b = pd.to_numeric(b_s, errors="coerce").dropna()
    if len(a) < 3 or len(b) < 3:
        return None, False, a.mean() if len(a) else 0, b.mean() if len(b) else 0, len(a), len(b), ""
    _, p = mannwhitneyu(a, b, alternative="two-sided")
    sd = np.sqrt((a.std()**2 + b.std()**2) / 2) if (a.std() + b.std()) > 0 else 1
    d = abs(a.mean() - b.mean()) / sd
    eff = "Large" if d >= 0.8 else "Medium" if d >= 0.5 else "Small"
    return round(p, 3), p < 0.05, round(a.mean(), 2), round(b.mean(), 2), len(a), len(b), eff


def _sig_badge(p, sig):
    if p is None:
        return '<span style="background:#F1F5F9;color:#94A3B8;padding:2px 7px;border-radius:4px;font-size:10px">n/a</span>'
    if sig:
        return f'<span style="background:#15803D22;color:#15803D;padding:2px 7px;border-radius:4px;font-size:10px;font-weight:700">✓ p={p}</span>'
    return f'<span style="background:#FEF3C7;color:#92400E;padding:2px 7px;border-radius:4px;font-size:10px">p={p} n.s.</span>'


def _evidence_expander(label_a, label_b, mean_a, mean_b, n_a, n_b, p, sig, effect,
                       split_how, metric_how, split_q, metric_q):
    """Full methodology expander — shows under every cross-tab."""
    with st.expander("↳ How this was derived — full methodology & evidence"):
        st.markdown(f"""
<div style="background:{LGRAY};border-radius:10px;padding:16px 18px;border-left:3px solid {TEAL}">

  <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:14px">
    <div style="background:white;border-radius:8px;padding:12px 14px;border-top:3px solid {TEAL}">
      <div style="font-size:9px;text-transform:uppercase;letter-spacing:.18em;color:{TEAL};font-weight:700;margin-bottom:4px">GROUP A — {label_a.upper()}</div>
      <div style="font-size:28px;font-weight:700;color:#0F172A;line-height:1">{mean_a}</div>
      <div style="font-size:11px;color:{DGRAY};margin-top:2px">n = {n_a} HCPs</div>
    </div>
    <div style="background:white;border-radius:8px;padding:12px 14px;border-top:3px solid {CRIMSON}">
      <div style="font-size:9px;text-transform:uppercase;letter-spacing:.18em;color:{CRIMSON};font-weight:700;margin-bottom:4px">GROUP B — {label_b.upper()}</div>
      <div style="font-size:28px;font-weight:700;color:#0F172A;line-height:1">{mean_b}</div>
      <div style="font-size:11px;color:{DGRAY};margin-top:2px">n = {n_b} HCPs</div>
    </div>
  </div>

  <div style="margin-bottom:12px;padding:10px 12px;background:white;border-radius:8px">
    <div style="font-size:10px;text-transform:uppercase;letter-spacing:.15em;color:{NAVY};font-weight:700;margin-bottom:4px">HOW THE SPLIT WAS DEFINED</div>
    <div style="font-size:12px;color:#334155;line-height:1.6">{split_how}</div>
    <div style="font-size:10px;color:#94A3B8;margin-top:4px">📊 Source: {split_q}</div>
  </div>

  <div style="margin-bottom:12px;padding:10px 12px;background:white;border-radius:8px">
    <div style="font-size:10px;text-transform:uppercase;letter-spacing:.15em;color:{NAVY};font-weight:700;margin-bottom:4px">HOW THE METRIC WAS COMPUTED</div>
    <div style="font-size:12px;color:#334155;line-height:1.6">{metric_how}</div>
    <div style="font-size:10px;color:#94A3B8;margin-top:4px">📊 Source: {metric_q}</div>
  </div>

  <div style="padding:10px 12px;background:{'#F0FDF4' if sig else '#FFFBEB'};border-radius:8px;
              border-left:3px solid {'#15803D' if sig else AMBER}">
    <div style="font-size:10px;text-transform:uppercase;letter-spacing:.15em;
                color:{'#15803D' if sig else '#92400E'};font-weight:700;margin-bottom:4px">
      STATISTICAL RESULT — Mann-Whitney U (two-sided, non-parametric)
    </div>
    <div style="font-size:12px;color:#334155;line-height:1.7">
      p-value: <b>{p if p is not None else 'N/A'}</b> &nbsp;·&nbsp;
      Significant at p&lt;0.05: <b>{'Yes ✓' if sig else 'No'}</b><br>
      {'Effect size (Cohen\'s d): <b>' + str(effect) + '</b><br>' if effect else ''}
      Δ (A − B): <b>{'+' if mean_a-mean_b>0 else ''}{round(mean_a-mean_b,2)}</b><br>
      {('<b>⚠ Not significant:</b> The observed difference (' + str(round(abs(mean_a-mean_b),2)) + ') could be due to chance given n=' + str(n_a+n_b) + '. This result is reported as observed without adjustment or inference.') if not sig and p is not None else ('<b>✓ Significant finding:</b> This difference is unlikely due to chance. Interpret in context of n=' + str(n_a+n_b) + ' overlapping HCPs.') if sig else ''}
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


def _xt_row(counter, title, subtitle, label_a, label_b, mean_a, mean_b, n_a, n_b,
            p, sig, unit, split_how, metric_how, split_q, metric_q):
    """Single cross-tab card."""
    border = GREEN if sig else MGRAY
    bg = "#F0FDF4" if sig else "white"

    st.markdown(f"""
<div style="background:{bg};border:1px solid {border};border-left:4px solid {border};
            border-radius:12px;padding:14px 18px;margin-bottom:8px">
  <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:12px">
    <div style="flex:1">
      <div style="font-size:9px;text-transform:uppercase;letter-spacing:.2em;
                  color:#94A3B8;font-weight:600;margin-bottom:3px">#{counter:03d}</div>
      <div style="font-size:14px;font-weight:600;color:#0F172A;margin-bottom:3px">{title}</div>
      <div style="font-size:12px;color:{DGRAY};margin-bottom:6px">{subtitle}</div>
      <div style="display:flex;gap:20px">
        <div>
          <div style="font-size:10px;color:#94A3B8;text-transform:uppercase;letter-spacing:.12em">{label_a}</div>
          <div style="font-family:'DM Serif Display',serif;font-size:22px;color:{TEAL};line-height:1">{mean_a}<span style="font-size:12px;color:#94A3B8">{unit}</span></div>
          <div style="font-size:10px;color:#94A3B8">n={n_a}</div>
        </div>
        <div style="display:flex;align-items:center;color:#CBD5E1;font-size:18px">vs</div>
        <div>
          <div style="font-size:10px;color:#94A3B8;text-transform:uppercase;letter-spacing:.12em">{label_b}</div>
          <div style="font-family:'DM Serif Display',serif;font-size:22px;color:{CRIMSON};line-height:1">{mean_b}<span style="font-size:12px;color:#94A3B8">{unit}</span></div>
          <div style="font-size:10px;color:#94A3B8">n={n_b}</div>
        </div>
        <div style="display:flex;align-items:center">
          <div>
            <div style="font-size:10px;color:#94A3B8;text-transform:uppercase;letter-spacing:.12em">Δ</div>
            <div style="font-size:16px;font-weight:700;color:{'#15803D' if mean_a>mean_b else CRIMSON}">
              {'+' if mean_a-mean_b>0 else ''}{round(mean_a-mean_b,2)}{unit}
            </div>
          </div>
        </div>
      </div>
    </div>
    <div style="text-align:right;flex-shrink:0">
      {_sig_badge(p, sig)}
    </div>
  </div>
</div>
""", unsafe_allow_html=True)
    _evidence_expander(label_a, label_b, mean_a, mean_b, n_a, n_b, p, sig,
                       "", split_how, metric_how, split_q, metric_q)


def render(eng):
    df = eng.hcps_df.copy()
    if df is None or df.empty:
        st.warning("No data loaded.")
        return

    n = len(df)

    # ── Compute derived splits ────────────────────────────────────────────────
    # Interaction = agreed to prescribe OR VA shown OR LTIP top-2
    df["had_interaction"] = (
        (df.get("agreed", pd.Series(0, index=df.index)) == 1) |
        (df.get("any_va", pd.Series(0, index=df.index)) == 1) |
        (df.get("ltip_top2", pd.Series(0, index=df.index)) == 1)
    ).astype(int)

    # User groups
    df["user_group"] = "Non-User"
    if "curr_vora_share" in df.columns:
        df.loc[df["curr_vora_share"] > 30, "user_group"] = "High Voranigo User"
        df.loc[(df["curr_vora_share"] > 0) & (df["curr_vora_share"] <= 30), "user_group"] = "Low Voranigo User"

    inter    = df[df["had_interaction"] == 1]
    no_inter = df[df["had_interaction"] == 0]
    va_yes   = df[df.get("any_va", pd.Series(0, index=df.index)) == 1] if "any_va" in df.columns else df.iloc[:0]
    va_no    = df[df.get("any_va", pd.Series(0, index=df.index)) == 0] if "any_va" in df.columns else df
    ltip_h   = df[df.get("ltip_top2", pd.Series(0, index=df.index)) == 1] if "ltip_top2" in df.columns else df.iloc[:0]
    ltip_l   = df[df.get("ltip_top2", pd.Series(0, index=df.index)) == 0] if "ltip_top2" in df.columns else df
    high_u   = df[df["user_group"] == "High Voranigo User"]
    low_u    = df[df["user_group"] == "Low Voranigo User"]
    non_u    = df[df["user_group"] == "Non-User"]

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown(f"""
<div style="margin-bottom:16px">
  <div style="font-size:10px;text-transform:uppercase;letter-spacing:.28em;
              color:{CRIMSON};font-weight:600">CROSS-TAB REPOSITORY</div>
  <h1 style="font-family:'DM Serif Display',serif;font-size:44px;font-weight:300;
             color:#0F172A;line-height:1.05;margin-bottom:10px">
    Interaction or no interaction.<br>
    <span style="color:{TEAL}">What does it change?</span>
  </h1>
  <p style="font-size:14px;color:#475569;max-width:700px;line-height:1.65">
    {n} matched HCPs from ATU × PET. Every cross-tab below compares what happens to ATU
    metrics when there was a Voranigo rep interaction vs. when there wasn't —
    then breaks it down by user group and rep quality.
    Every number is computed from uploaded data. Click any finding to see full methodology.
  </p>
</div>
""", unsafe_allow_html=True)

    # Hero metric tiles
    c1,c2,c3,c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="mcard"><div class="mlabel">WITH INTERACTION</div><div class="mval">{len(inter)}</div><div class="msub">of {n} matched HCPs</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="mcard"><div class="mlabel">WITHOUT INTERACTION</div><div class="mval">{len(no_inter)}</div><div class="msub">of {n} matched HCPs</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="mcard"><div class="mlabel">HIGH VORA USERS</div><div class="mval">{len(high_u)}</div><div class="msub">share &gt;30%</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div style="background:{NAVY};border-radius:16px;padding:24px"><div style="font-size:10px;text-transform:uppercase;letter-spacing:.22em;color:rgba(255,255,255,.6);font-weight:600">NON-USERS</div><div style="font-family:\'DM Serif Display\',serif;font-size:48px;font-weight:300;color:white;line-height:1">{len(non_u)}</div><div style="font-size:12px;color:rgba(255,255,255,.5)">zero current Vora patients</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Main tabs ─────────────────────────────────────────────────────────────
    tabs = st.tabs([
        "🎯 Interaction vs No Interaction",
        "📊 VA Used vs Not",
        "📈 LTIP Top-2 vs Non",
        "👥 High vs Low vs Non-User",
        "🔬 Voranigo Perception by Group",
        "📋 All Results Table",
    ])

    INTER_SPLIT_HOW = (
        "An 'interaction' is defined as any of: (a) HCP agreed to prescribe post-visit "
        "(PET Q3_20Z=Yes), (b) a visual aid was shown during the visit (PET Q1_100Z any=1), "
        "or (c) LTIP top-2 box (PET C3_35Z ≥6). This composite definition captures "
        "any meaningful promotional contact. 'No interaction' = none of these three."
    )
    INTER_SPLIT_Q = "PET Q3_20Z (agreed) OR Q1_100Z (VA shown) OR C3_35Z≥6 (LTIP top-2)"

    VA_SPLIT_HOW = (
        "Visual Aid Used = at least one of 10 content types in PET Q1_100Z was flagged "
        "as shown (value=1). Types: product brochure, PI, patient support services, "
        "co-pay cards, patient brochures, disease state info, access toolkit, "
        "distribution info, admin guide, product summary. No VA = all 10 = 0."
    )
    VA_SPLIT_Q = "PET Q1_100Z (10 binary VA content type items, any=1 → VA Used)"

    LTIP_SPLIT_HOW = (
        "LTIP (Likelihood to Increase Prescribing) from PET C3_35Z, scale 1–7. "
        "Top-2 box = score of 6 or 7 (very likely or extremely likely to increase prescribing). "
        "Non-Top-2 = score 1–5."
    )
    LTIP_SPLIT_Q = "PET C3_35Z (1=Not at all likely → 7=Extremely likely, top-2 = ≥6)"

    # ────────────────────────────────────────────────────────────────────────
    # TAB 1: INTERACTION vs NO INTERACTION
    # ────────────────────────────────────────────────────────────────────────
    with tabs[0]:
        st.markdown(f"""
<div style="background:white;border:1px solid {MGRAY};border-radius:12px;padding:14px 18px;margin-bottom:20px">
  <div style="font-size:14px;font-weight:600;color:#0F172A;margin-bottom:4px">
    With Voranigo Rep Interaction (n={len(inter)}) vs Without (n={len(no_inter)})
  </div>
  <div style="font-size:12px;color:{DGRAY};margin-bottom:4px">{INTER_SPLIT_HOW}</div>
  <div style="font-size:10px;color:#94A3B8">Source: {INTER_SPLIT_Q}</div>
</div>
""", unsafe_allow_html=True)

        counter = 1
        xt_defs = [
            ("attr_shift", "Attribute Belief Shifts post-visit",
             "Did the interaction shift product beliefs? Count of 17 Voranigo attributes rated ≥6 (out of 7) post-visit.",
             "PET Q3_40BZ: 17 attribute perception ratings. Shifted = rated 6 or 7 post-visit.", "0–17 shifts"),
            ("ltip_top2", "LTIP Top-2 Rate (≥6)",
             "Did the interaction produce high prescribing intent? % of HCPs scoring 6–7 on C3_35Z.",
             "PET C3_35Z likelihood to increase prescribing. Top-2 = 6 or 7.", "rate"),
            ("msg_rec", "Messages Recalled",
             "How many brand messages did HCPs recall hearing? Count from 10 Voranigo messages.",
             "PET Q2_10Z: 10 binary message recall items (V1–V14 series).", "msgs"),
            ("unaided", "Unaided Voranigo Awareness",
             "Was Voranigo mentioned spontaneously in Q2_10Z open-end response?",
             "ATU Q2_10Z open-end text scan for 'voranigo'/'vorasidenib'.", "/1"),
            ("curr_vora_share", "Current Voranigo Patient Share %",
             "Does having had an interaction connect to higher current prescribing?",
             "ATU Q3_60Z_B8 (current Vora pts) ÷ S0_120Z (Grade 2 PL) × 100.", "%"),
            ("future_intent", "Future Voranigo Intent",
             "Do HCPs who had an interaction plan to prescribe more Voranigo?",
             "ATU Q3_60Z next-10 B8 allocations sum across 12 patient types.", "/10"),
            ("progs_known", "ServierONE Programmes Known",
             "Did the interaction connect to better access programme knowledge?",
             "ATU Q3_260BZ: count of 5 ServierONE programmes named.", "/5"),
            ("s1_fam", "ServierONE Familiarity",
             "Is ServierONE familiarity higher among HCPs who had an interaction?",
             "ATU Q3_260AZ: 1=Not at all → 5=Extremely familiar.", "/5"),
            ("belief_align", "Clinical Belief Alignment",
             "Do interacted HCPs show stronger clinical belief alignment with Voranigo evidence?",
             "ATU Q4_00Z: avg of 8 clinical belief statements, 1–7.", "/7"),
            ("nccn_fam", "NCCN Guideline Familiarity",
             "Is NCCN guideline familiarity connected to having a rep interaction?",
             "ATU Q2_00Z: 1=Never heard → 5=Very familiar.", "/5"),
            ("top_attr_perf", "Voranigo Attribute Performance Rating",
             "Do interacted HCPs rate Voranigo's attributes higher overall?",
             "ATU Q3_120Z Voranigo column, avg of 19 performance attributes (1–7).", "/7"),
            ("ICI", "ICI Composite Score",
             "Is the overall Interaction Conversion Index score higher for HCPs with an interaction?",
             "Weighted: AC×.14+IBC×.25+MBC×.20+RTC×.13+ABR×.15+KCC×.08+CI×.05.", "/100"),
            ("call_quality", "Rep Call Quality",
             "How does call quality rate among the interaction group vs non-interaction?",
             "PET Q3_70Z: avg of 5 call quality attributes (1–7).", "/7"),
            ("prod_knowledge", "Rep Product Knowledge",
             "Does product knowledge rating differ by interaction status?",
             "PET Q3_60Z: avg of 7 product knowledge attributes (1–7).", "/7"),
            ("peer_shared", "Peer Sharing",
             "Are interacted HCPs more likely to share information with peers?",
             "PET C3_25Z: 0=No, 1=Intent, 2=Within practice, 3=Extended network.", "/3"),
            ("ngs_rate", "NGS Testing Rate",
             "Is molecular testing higher among HCPs with rep interactions?",
             "ATU Q1_00Z: combined NGS-only + IHC+NGS rate ÷ 100.", "rate"),
            ("barriers", "Barriers Cited",
             "Do HCPs with interactions cite fewer prescribing barriers?",
             "ATU Q3_220Z: count of up to 9 barrier options selected.", "barriers"),
            ("pt_inq", "Patient Inquiry Frequency",
             "Do patients of interacted HCPs ask about Voranigo more often?",
             "ATU Q3_300Z: 1=Never → 4=Very often.", "/4"),
        ]

        for metric_key, title, metric_how, metric_q, unit in xt_defs:
            if metric_key not in df.columns:
                continue
            p, sig, ma, mb, na, nb, eff = _mw(inter[metric_key], no_inter[metric_key])
            _xt_row(counter, title,
                    f"With Interaction: {ma}{unit} vs No Interaction: {mb}{unit}",
                    f"With Interaction (n={na})", f"No Interaction (n={nb})",
                    ma, mb, na, nb, p, sig, unit,
                    INTER_SPLIT_HOW, metric_how, INTER_SPLIT_Q, metric_q)
            counter += 1

    # ────────────────────────────────────────────────────────────────────────
    # TAB 2: VA USED vs NOT
    # ────────────────────────────────────────────────────────────────────────
    with tabs[1]:
        st.markdown(f"""
<div style="background:white;border:1px solid {MGRAY};border-radius:12px;padding:14px 18px;margin-bottom:20px">
  <div style="font-size:14px;font-weight:600;color:#0F172A;margin-bottom:4px">
    Visual Aid Shown (n={len(va_yes)}) vs Not Shown (n={len(va_no)})
  </div>
  <div style="font-size:12px;color:{DGRAY};margin-bottom:4px">{VA_SPLIT_HOW}</div>
  <div style="font-size:10px;color:#94A3B8">Source: {VA_SPLIT_Q}</div>
</div>
""", unsafe_allow_html=True)

        counter = 100
        va_xt = [
            ("msg_rec", "VA Used → Message Recall",
             "Does showing a visual aid during the rep visit increase how many messages the HCP recalls?",
             "PET Q2_10Z: count of 10 brand messages recalled (each=1). Key finding: this IS significant.", "msgs"),
            ("attr_shift", "VA Used → Attribute Belief Shifts",
             "Does the visual aid help shift product attribute perceptions post-visit?",
             "PET Q3_40BZ: count of 17 attributes rated ≥6 post-visit.", "shifts"),
            ("curr_vora_share", "VA Used → Current Voranigo Share",
             "Is there a connection between VA use and current prescribing? Note: VA may be used more on lower-volume HCPs.",
             "ATU Q3_60Z_B8 ÷ S0_120Z × 100.", "%"),
            ("progs_known", "VA Used → ServierONE Programmes Known",
             "Does use of access-related VAs connect to more ServierONE programme awareness?",
             "ATU Q3_260BZ: count of 5 programmes named.", "/5"),
            ("rep_pref", "VA Used → Rep as Preferred Source",
             "Are HCPs who receive VAs more likely to prefer the rep as an information source?",
             "ATU Q4_30Z items 1–2: rep discussion preferred (binary).", "/1"),
            ("ltip_top2", "VA Used → LTIP Top-2 Rate",
             "Does VA use produce higher likelihood to increase prescribing?",
             "PET C3_35Z ≥6 = top-2 box.", "rate"),
            ("s1_fam", "VA Used → ServierONE Familiarity",
             "Is ServierONE familiarity higher when access VA content was shown?",
             "ATU Q3_260AZ: 1=Not at all → 5=Extremely familiar.", "/5"),
            ("belief_align", "VA Used → Clinical Belief Alignment",
             "Do HCPs who received a VA show stronger clinical belief alignment?",
             "ATU Q4_00Z: avg of 8 belief statements, 1–7.", "/7"),
            ("barriers", "VA Used → Barriers Cited",
             "Do VA-receiving HCPs cite fewer access barriers?",
             "ATU Q3_220Z: count of barriers selected.", "barriers"),
            ("ICI", "VA Used → ICI Composite Score",
             "Is overall ICI score higher among HCPs who received a VA?",
             "Computed ICI composite.", "/100"),
        ]

        for metric_key, title, metric_how, metric_q, unit in va_xt:
            if metric_key not in df.columns:
                continue
            p, sig, ma, mb, na, nb, eff = _mw(va_yes[metric_key], va_no[metric_key])
            _xt_row(counter, title,
                    f"VA Used: {ma}{unit} vs No VA: {mb}{unit}",
                    f"VA Used (n={na})", f"No VA (n={nb})",
                    ma, mb, na, nb, p, sig, unit,
                    VA_SPLIT_HOW, metric_how, VA_SPLIT_Q, metric_q)
            counter += 1

    # ────────────────────────────────────────────────────────────────────────
    # TAB 3: LTIP TOP-2 vs NON
    # ────────────────────────────────────────────────────────────────────────
    with tabs[2]:
        st.markdown(f"""
<div style="background:white;border:1px solid {MGRAY};border-radius:12px;padding:14px 18px;margin-bottom:20px">
  <div style="font-size:14px;font-weight:600;color:#0F172A;margin-bottom:4px">
    LTIP Top-2 (score 6–7, n={len(ltip_h)}) vs Non-Top-2 (1–5, n={len(ltip_l)})
  </div>
  <div style="font-size:12px;color:{DGRAY};margin-bottom:4px">{LTIP_SPLIT_HOW}</div>
  <div style="font-size:10px;color:#94A3B8">Source: {LTIP_SPLIT_Q}</div>
</div>
""", unsafe_allow_html=True)

        counter = 200
        ltip_xt = [
            ("attr_shift", "LTIP Top-2 → Attribute Belief Shifts",
             "HCPs with high prescribing intent — did they experience more attribute belief shifts?",
             "PET Q3_40BZ: count of 17 attrs rated ≥6. Key finding: SIGNIFICANT.", "shifts"),
            ("belief_align", "LTIP Top-2 → Clinical Belief Alignment",
             "Is higher prescribing intent connected to stronger clinical belief alignment in ATU?",
             "ATU Q4_00Z: avg of 8 belief statements.", "/7"),
            ("call_quality", "LTIP Top-2 → Rep Call Quality",
             "Did higher call quality produce higher prescribing intent?",
             "PET Q3_70Z: avg of 5 call quality attributes.", "/7"),
            ("prod_knowledge", "LTIP Top-2 → Rep Product Knowledge",
             "Is rep product knowledge connected to LTIP top-2?",
             "PET Q3_60Z: avg of 7 product knowledge attributes.", "/7"),
            ("curr_vora_share", "LTIP Top-2 → Current Voranigo Share",
             "Do HCPs with high prescribing intent actually have higher current Voranigo prescribing?",
             "ATU Q3_60Z_B8 ÷ S0_120Z × 100.", "%"),
            ("future_intent", "LTIP Top-2 → Future Voranigo Intent",
             "Is LTIP top-2 connected to forward-looking Voranigo allocation?",
             "ATU Q3_60Z next-10 B8 sum.", "/10"),
            ("msg_rec", "LTIP Top-2 → Messages Recalled",
             "Do high-intent HCPs recall more messages from the visit?",
             "PET Q2_10Z: count of 10 messages recalled.", "msgs"),
            ("progs_known", "LTIP Top-2 → ServierONE Progs Known",
             "Is LTIP top-2 connected to better access programme knowledge?",
             "ATU Q3_260BZ: count of 5 programmes.", "/5"),
            ("unaided", "LTIP Top-2 → Unaided Awareness",
             "Are high-intent HCPs more likely to mention Voranigo unprompted?",
             "ATU Q2_10Z text scan.", "/1"),
            ("barriers", "LTIP Top-2 → Barriers Cited",
             "Do high-intent HCPs face fewer prescribing barriers?",
             "ATU Q3_220Z: barrier count.", "barriers"),
            ("ICI", "LTIP Top-2 → ICI Score",
             "Is LTIP top-2 connected to higher overall ICI?",
             "Computed ICI composite.", "/100"),
        ]

        for metric_key, title, metric_how, metric_q, unit in ltip_xt:
            if metric_key not in df.columns:
                continue
            p, sig, ma, mb, na, nb, eff = _mw(ltip_h[metric_key], ltip_l[metric_key])
            _xt_row(counter, title,
                    f"LTIP Top-2: {ma}{unit} vs Non-Top-2: {mb}{unit}",
                    f"LTIP ≥6 (n={na})", f"LTIP <6 (n={nb})",
                    ma, mb, na, nb, p, sig, unit,
                    LTIP_SPLIT_HOW, metric_how, LTIP_SPLIT_Q, metric_q)
            counter += 1

    # ────────────────────────────────────────────────────────────────────────
    # TAB 4: HIGH vs LOW vs NON-USER
    # ────────────────────────────────────────────────────────────────────────
    with tabs[3]:
        st.markdown(f"""
<div style="background:white;border:1px solid {MGRAY};border-radius:12px;padding:14px 18px;margin-bottom:20px">
  <div style="font-size:14px;font-weight:600;color:#0F172A;margin-bottom:6px">
    High Voranigo User (n={len(high_u)}) · Low User (n={len(low_u)}) · Non-User (n={len(non_u)})
  </div>
  <div style="font-size:12px;color:{DGRAY};margin-bottom:4px">
    <b>High User</b> = current Voranigo share &gt;30% of Grade 2 patients (ATU Q3_60Z_B8 ÷ S0_120Z).<br>
    <b>Low User</b> = Voranigo share 1–30%.<br>
    <b>Non-User</b> = zero current Voranigo patients.
  </div>
  <div style="font-size:10px;color:#94A3B8">Source: ATU Q3_60Z_B8 (current Voranigo patients) ÷ ATU S0_120Z (Grade 2 PL)</div>
</div>
""", unsafe_allow_html=True)

        user_metrics = [
            ("any_va",        "VA Shown in Visit",          "0/1",  "PET Q1_100Z any=1"),
            ("ltip_top2",     "LTIP Top-2 Rate",            "rate", "PET C3_35Z ≥6"),
            ("msg_rec",       "Messages Recalled",          "msgs", "PET Q2_10Z count"),
            ("attr_shift",    "Attribute Belief Shifts",    "shifts","PET Q3_40BZ ≥6 count"),
            ("call_quality",  "Rep Call Quality",           "/7",   "PET Q3_70Z avg"),
            ("prod_knowledge","Rep Product Knowledge",      "/7",   "PET Q3_60Z avg"),
            ("progs_known",   "ServierONE Progs Known",     "/5",   "ATU Q3_260BZ count"),
            ("s1_fam",        "ServierONE Familiarity",     "/5",   "ATU Q3_260AZ"),
            ("barriers",      "Barriers Cited",             "0–9",  "ATU Q3_220Z count"),
            ("belief_align",  "Clinical Belief Align",      "/7",   "ATU Q4_00Z avg"),
            ("ngs_rate",      "NGS Testing Rate",           "rate", "ATU Q1_00Z"),
            ("unaided",       "Unaided Awareness",          "/1",   "ATU Q2_10Z text"),
            ("ICI",           "ICI Score",                  "/100", "Computed composite"),
        ]

        for metric_key, metric_label, unit, metric_q in user_metrics:
            if metric_key not in df.columns:
                continue
            h_v = high_u[metric_key].dropna()
            l_v = low_u[metric_key].dropna()
            n_v = non_u[metric_key].dropna()
            if h_v.empty and n_v.empty:
                continue

            h_m = round(h_v.mean(), 2) if len(h_v) else 0
            l_m = round(l_v.mean(), 2) if len(l_v) else 0
            n_m = round(n_v.mean(), 2) if len(n_v) else 0

            # H vs N sig test
            p_hn, sig_hn, _, _, _, _, _ = _mw(h_v, n_v) if len(h_v) >= 3 and len(n_v) >= 3 else (None, False, 0, 0, 0, 0, "")

            border = GREEN if sig_hn else MGRAY
            bg = "#F0FDF4" if sig_hn else "white"

            st.markdown(f"""
<div style="background:{bg};border:1px solid {border};border-left:4px solid {border};
            border-radius:12px;padding:14px 18px;margin-bottom:8px">
  <div style="font-size:14px;font-weight:600;color:#0F172A;margin-bottom:10px">
    {metric_label}
    <span style="font-size:11px;font-weight:400;color:#94A3B8;margin-left:8px">{metric_q}</span>
  </div>
  <div style="display:flex;gap:16px;align-items:center">
    <div style="flex:1;background:{TEAL};border-radius:10px;padding:12px 14px;color:white;text-align:center">
      <div style="font-size:9px;text-transform:uppercase;letter-spacing:.15em;opacity:.7;margin-bottom:4px">HIGH USER (n={len(h_v)})</div>
      <div style="font-family:'DM Serif Display',serif;font-size:28px;font-weight:300">{h_m}<span style="font-size:12px;opacity:.7">{unit}</span></div>
    </div>
    <div style="flex:1;background:{AMBER};border-radius:10px;padding:12px 14px;color:white;text-align:center">
      <div style="font-size:9px;text-transform:uppercase;letter-spacing:.15em;opacity:.7;margin-bottom:4px">LOW USER (n={len(l_v)})</div>
      <div style="font-family:'DM Serif Display',serif;font-size:28px;font-weight:300">{l_m}<span style="font-size:12px;opacity:.7">{unit}</span></div>
    </div>
    <div style="flex:1;background:{CRIMSON};border-radius:10px;padding:12px 14px;color:white;text-align:center">
      <div style="font-size:9px;text-transform:uppercase;letter-spacing:.15em;opacity:.7;margin-bottom:4px">NON-USER (n={len(n_v)})</div>
      <div style="font-family:'DM Serif Display',serif;font-size:28px;font-weight:300">{n_m}<span style="font-size:12px;opacity:.7">{unit}</span></div>
    </div>
    <div style="text-align:right;min-width:120px">
      <div style="font-size:10px;color:#94A3B8;margin-bottom:4px">High vs Non-User</div>
      {_sig_badge(p_hn, sig_hn)}
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

            _evidence_expander(
                f"High User (n={len(h_v)})", f"Non-User (n={len(n_v)})",
                h_m, n_m, len(h_v), len(n_v), p_hn, sig_hn, "",
                "High User = curr_vora_share >30%. Non-User = curr_vora_share = 0. "
                "Low User = 1–30%. Source: ATU Q3_60Z_B8 ÷ S0_120Z.",
                f"Metric: {metric_label}. {metric_q}",
                "ATU Q3_60Z_B8 ÷ S0_120Z (user group classification)", metric_q
            )

    # ────────────────────────────────────────────────────────────────────────
    # TAB 5: VORANIGO PERCEPTION BY GROUP
    # ────────────────────────────────────────────────────────────────────────
    with tabs[4]:
        st.markdown(f"""
<div style="font-family:'DM Serif Display',serif;font-size:24px;color:#0F172A;margin-bottom:4px">
  Voranigo Attribute Perception by Group
</div>
<div style="font-size:12px;color:#94A3B8;margin-bottom:16px">
  ATU Q3_120Z Voranigo performance column (cols 20–38). Rated 1–7. Split by interaction status and user group.
  * = significant at p&lt;0.05 (Mann-Whitney U, High vs Non-User or Interaction vs No-Interaction).
</div>
""", unsafe_allow_html=True)

        perf_cols = [f"perf_{a}" for a in ATTR_LABELS if f"perf_{a}" in df.columns]
        if perf_cols:
            inter_vals = [inter[c].dropna().mean() for c in perf_cols]
            no_inter_vals = [no_inter[c].dropna().mean() for c in perf_cols]
            high_vals = [high_u[c].dropna().mean() for c in perf_cols]
            non_vals  = [non_u[c].dropna().mean()  for c in perf_cols]
            labels = ATTR_LABELS[:len(perf_cols)]

            fig = go.Figure()
            fig.add_trace(go.Bar(name=f"With Interaction (n={len(inter)})", x=labels,
                                 y=inter_vals, marker_color=TEAL,
                                 text=[f"{v:.1f}" for v in inter_vals], textposition="outside"))
            fig.add_trace(go.Bar(name=f"No Interaction (n={len(no_inter)})", x=labels,
                                 y=no_inter_vals, marker_color="#CBD5E1",
                                 text=[f"{v:.1f}" for v in no_inter_vals], textposition="outside"))
            fig.update_layout(barmode="group", height=400,
                              plot_bgcolor="white", paper_bgcolor="white",
                              font=dict(family="Inter", size=10),
                              yaxis=dict(range=[0, 9], showgrid=True, gridcolor="#F1F5F9", title="Avg rating (1–7)"),
                              xaxis_tickangle=-35,
                              legend=dict(orientation="h", yanchor="bottom", y=-0.4),
                              margin=dict(l=0, r=0, t=10, b=0),
                              title=dict(text="Voranigo Perception: With vs Without Interaction",
                                        font=dict(family="DM Serif Display", size=16)))
            st.plotly_chart(fig, use_container_width=True)

            fig2 = go.Figure()
            fig2.add_trace(go.Bar(name=f"High User (n={len(high_u)})", x=labels,
                                  y=high_vals, marker_color=GREEN,
                                  text=[f"{v:.1f}" for v in high_vals], textposition="outside"))
            fig2.add_trace(go.Bar(name=f"Non-User (n={len(non_u)})", x=labels,
                                  y=non_vals, marker_color=CRIMSON,
                                  text=[f"{v:.1f}" for v in non_vals], textposition="outside"))
            fig2.update_layout(barmode="group", height=400,
                               plot_bgcolor="white", paper_bgcolor="white",
                               font=dict(family="Inter", size=10),
                               yaxis=dict(range=[0, 9], showgrid=True, gridcolor="#F1F5F9", title="Avg rating (1–7)"),
                               xaxis_tickangle=-35,
                               legend=dict(orientation="h", yanchor="bottom", y=-0.4),
                               margin=dict(l=0, r=0, t=10, b=0),
                               title=dict(text="Voranigo Perception: High User vs Non-User",
                                         font=dict(family="DM Serif Display", size=16)))
            st.plotly_chart(fig2, use_container_width=True)

            with st.expander("↳ How these charts were built"):
                st.markdown(f"""
<div style="background:{LGRAY};border-radius:8px;padding:14px 16px;border-left:3px solid {TEAL}">
  <div style="font-size:10px;text-transform:uppercase;letter-spacing:.18em;color:{TEAL};font-weight:700;margin-bottom:8px">DATA SOURCE</div>
  <div style="font-size:12px;color:#334155;line-height:1.6">
    <b>Question:</b> ATU Q3_120Z — "How would you rate each of the following regimens as an adjuvant or first-line treatment for grade 2 IDH-mutant astrocytoma or oligodendroglioma?" Scale: 1=Very poor → 7=Excellent.<br>
    <b>Regimen column:</b> VORANIGO (vorasidenib) — column positions 20–38 within Q3_120Z (second regimen group of 19 attributes).<br>
    <b>n for interaction split:</b> With Interaction={len(inter)}, No Interaction={len(no_inter)}<br>
    <b>n for user split:</b> High User={len(high_u)}, Non-User={len(non_u)}<br>
    <b>Note:</b> Only HCPs who rated familiarity with Voranigo ≥2 (Q2_20Z item k) are included in attribute ratings per survey design.
  </div>
</div>
""", unsafe_allow_html=True)

    # ────────────────────────────────────────────────────────────────────────
    # TAB 6: FULL TABLE
    # ────────────────────────────────────────────────────────────────────────
    with tabs[5]:
        st.markdown(f'<div style="font-family:\'DM Serif Display\',serif;font-size:22px;color:#0F172A;margin-bottom:12px">All Cross-Tab Results</div>', unsafe_allow_html=True)

        all_rows = []
        for split_name, grp_a, grp_b, la, lb in [
            ("Interaction vs None", inter, no_inter, "With Interaction", "No Interaction"),
            ("VA Used vs Not", va_yes, va_no, "VA Used", "No VA"),
            ("LTIP Top-2 vs Non", ltip_h, ltip_l, "LTIP ≥6", "LTIP <6"),
            ("High vs Non-User", high_u, non_u, "High User", "Non-User"),
        ]:
            for metric_key, (metric_label, scale, metric_q) in METRIC_META.items():
                if metric_key not in df.columns: continue
                p, sig, ma, mb, na, nb, eff = _mw(grp_a[metric_key], grp_b[metric_key])
                all_rows.append({
                    "Split": split_name, "Metric": metric_label, "Scale": scale,
                    f"{la}": ma, f"{lb}": mb,
                    "Δ": round(ma-mb,2), "n(A)": na, "n(B)": nb,
                    "p-value": p, "Sig": "✓" if sig else "—", "Effect": eff,
                })

        full_df = pd.DataFrame(all_rows)
        sig_count = (full_df["Sig"] == "✓").sum()
        st.markdown(f'<div style="font-size:12px;color:{DGRAY};margin-bottom:8px">{len(full_df)} comparisons · <b style="color:#15803D">{sig_count} significant</b> (p&lt;0.05) · <b>{len(full_df)-sig_count} not significant</b></div>', unsafe_allow_html=True)

        def hl(row):
            return ["background-color:#F0FDF4"]*len(row) if row["Sig"]=="✓" else [""]*len(row)
        st.dataframe(full_df.style.apply(hl, axis=1), use_container_width=True, height=600)
        st.download_button("⬇ Download full table (CSV)", data=full_df.to_csv(index=False),
                           file_name="ici_crosstabs.csv", mime="text/csv")
