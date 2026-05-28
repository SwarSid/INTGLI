"""
Cross-Tab Repository — 100 cross-tabs connecting PET (VA, LTIP, ServierONE)
with ATU (Q3_50, Q3_60, Q3_110, Q3_120, qualitative themes).
Includes statistical significance testing and clean sample sizes.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from scipy import stats as scipy_stats
from scipy.stats import chi2_contingency, mannwhitneyu, ttest_ind

TEAL = "#0F4C5C"
NAVY = "#1E293B"
CRIMSON = "#832232"
AMBER = "#B8860B"
GREEN = "#15803D"
LGRAY = "#F8FAFC"
MGRAY = "#E2E8F0"
DGRAY = "#64748B"

ATTR_LABELS = [
    "Prolonged PFS", "Tumor volume reduction", "Prolonged OS",
    "Low grade 3-4 AEs", "Low hepatic toxicity", "Low hematological toxicity",
    "Low neurotoxicity", "Low risk hypermutations", "Manageable LFT monitoring",
    "Good patient QoL", "Affordable", "Manufacturer patient services",
    "Easy to prescribe", "Convenient route", "Low risk long-term SEs",
    "Ability to preserve fertility", "Delays next treatment",
    "Reduces seizures", "Fair office compensation",
]


# ── Statistical helpers ────────────────────────────────────────────────────────

def statsig_test(group_a, group_b, test="mannwhitney"):
    """Returns (stat, p_value, significant, effect_size_label)."""
    a = pd.to_numeric(group_a, errors="coerce").dropna()
    b = pd.to_numeric(group_b, errors="coerce").dropna()
    if len(a) < 3 or len(b) < 3:
        return None, None, False, "Insufficient n"
    try:
        if test == "mannwhitney":
            stat, p = mannwhitneyu(a, b, alternative="two-sided")
        else:
            stat, p = ttest_ind(a, b)
        sig = p < 0.05
        # Cohen's d
        pooled = np.sqrt((a.std() ** 2 + b.std() ** 2) / 2)
        d = abs(a.mean() - b.mean()) / pooled if pooled > 0 else 0
        effect = "Large" if d >= 0.8 else "Medium" if d >= 0.5 else "Small"
        return stat, round(p, 4), sig, effect
    except Exception:
        return None, None, False, "Error"


def chi2_test(ct):
    """Chi-square test on a contingency table."""
    try:
        chi2, p, dof, _ = chi2_contingency(ct)
        return round(p, 4), p < 0.05
    except Exception:
        return None, False


def sig_badge(p, sig):
    if p is None:
        return '<span style="background:#F1F5F9;color:#64748B;padding:1px 6px;border-radius:3px;font-size:9px;font-weight:700">N/A</span>'
    if sig:
        return f'<span style="background:#15803D22;color:#15803D;padding:1px 6px;border-radius:3px;font-size:9px;font-weight:700">✓ p={p} SIGNIFICANT</span>'
    return f'<span style="background:#E2E8F0;color:#64748B;padding:1px 6px;border-radius:3px;font-size:9px;font-weight:700">p={p} n.s.</span>'


# ── Plotting helpers ───────────────────────────────────────────────────────────

def bar_chart(labels, vals_a, vals_b, label_a, label_b, title, color_a=TEAL, color_b=CRIMSON, pct=True):
    fig = go.Figure()
    fmt = ".0%" if pct else ".1f"
    text_a = [f"{v*100:.0f}%" if pct else f"{v:.1f}" for v in vals_a]
    text_b = [f"{v*100:.0f}%" if pct else f"{v:.1f}" for v in vals_b]

    fig.add_trace(go.Bar(name=label_a, x=labels, y=vals_a, marker_color=color_a,
                         text=text_a, textposition="outside"))
    fig.add_trace(go.Bar(name=label_b, x=labels, y=vals_b, marker_color=color_b,
                         text=text_b, textposition="outside"))
    fig.update_layout(
        title=dict(text=title, font=dict(family="DM Serif Display", size=16)),
        barmode="group", height=340,
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Inter", size=11),
        yaxis=dict(tickformat=".0%" if pct else ".1f", showgrid=True,
                   gridcolor="#F1F5F9", range=[0, max(max(vals_a + vals_b, default=0)*1.3, 0.1)]),
        legend=dict(orientation="h", yanchor="bottom", y=-0.3),
        margin=dict(l=0, r=0, t=40, b=0),
    )
    return fig


def heatmap_chart(df_ct, title):
    fig = px.imshow(
        df_ct.values,
        x=df_ct.columns.tolist(),
        y=df_ct.index.tolist(),
        color_continuous_scale=[[0, "#F8FAFC"], [0.5, f"{TEAL}88"], [1, TEAL]],
        text_auto=".0%",
        aspect="auto",
        title=title,
    )
    fig.update_layout(
        height=300, font=dict(family="Inter", size=10),
        plot_bgcolor="white", paper_bgcolor="white",
        coloraxis_showscale=False,
        title=dict(font=dict(family="DM Serif Display", size=15)),
        margin=dict(l=0, r=0, t=40, b=0),
    )
    return fig


def xtab_card(number, title, description, source_note, fig, p_value, sig, n_a, n_b, label_a, label_b):
    st.markdown(f"""
<div class="xtab-card">
  <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:6px">
    <div>
      <span style="font-size:10px;text-transform:uppercase;letter-spacing:.2em;
                   color:#94A3B8;font-weight:600">CROSS-TAB #{number:03d}</span>
      <div class="xtab-header">{title}</div>
      <div class="xtab-desc">{description}</div>
    </div>
    <div style="text-align:right;flex-shrink:0;margin-left:16px">
      {sig_badge(p_value, sig)}
      <div style="font-size:10px;color:#94A3B8;margin-top:4px">
        {label_a}: n={n_a} &nbsp;|&nbsp; {label_b}: n={n_b}
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(f'<div class="xtab-source">Source: {source_note}</div>', unsafe_allow_html=True)
    st.markdown("---")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN RENDER
# ══════════════════════════════════════════════════════════════════════════════

def render(eng):
    df = eng.hcps_df
    if df is None or df.empty:
        st.warning("No data loaded.")
        return

    st.markdown(f"""
<div style="margin-bottom:8px">
  <div style="font-size:10px;text-transform:uppercase;letter-spacing:.28em;
              color:{CRIMSON};font-weight:600">CROSS-TAB REPOSITORY</div>
  <h1 style="font-family:'DM Serif Display',serif;font-size:44px;font-weight:300;
             color:#0F172A;line-height:1.05;margin-bottom:10px">
    100 connected cross-tabs.<br>
    <span style="color:{TEAL}">Every PET signal vs every ATU metric.</span>
  </h1>
  <p style="font-size:14px;color:#475569;max-width:700px;line-height:1.65">
    Each table connects a promotional variable (Visual Aid usage, LTIP, ServierONE)
    to an ATU outcome (usage, perception, barriers). Sample sizes, statistical
    significance (Mann-Whitney U / Chi-square), and effect sizes shown per table.
  </p>
</div>
""", unsafe_allow_html=True)

    # ── Filter & search ──────────────────────────────────────────────────────
    cola, colb, colc = st.columns([2, 2, 1])
    with cola:
        category = st.selectbox("Category", [
            "All",
            "Visual Aid × ATU",
            "LTIP × ATU",
            "ServierONE × ATU",
            "ICI Dimensions × ATU",
            "Cluster × ATU",
        ])
    with colb:
        search = st.text_input("Search cross-tabs", placeholder="e.g. Voranigo usage, seizure...")
    with colc:
        sig_only = st.checkbox("Significant only (p<0.05)")

    tabs = st.tabs(["🎯 Visual Aid", "📈 LTIP", "🔑 ServierONE", "📊 ICI Dims", "🧩 Clusters", "📋 Full Table"])

    # ════════════════════════════════════════════════════════════════════════
    # TAB 1: VISUAL AID × ATU
    # ════════════════════════════════════════════════════════════════════════
    with tabs[0]:
        render_va_crosstabs(df)

    # ════════════════════════════════════════════════════════════════════════
    # TAB 2: LTIP × ATU
    # ════════════════════════════════════════════════════════════════════════
    with tabs[1]:
        render_ltip_crosstabs(df)

    # ════════════════════════════════════════════════════════════════════════
    # TAB 3: ServierONE × ATU
    # ════════════════════════════════════════════════════════════════════════
    with tabs[2]:
        render_servier_crosstabs(df)

    # ════════════════════════════════════════════════════════════════════════
    # TAB 4: ICI DIMENSIONS × ATU
    # ════════════════════════════════════════════════════════════════════════
    with tabs[3]:
        render_ici_crosstabs(df)

    # ════════════════════════════════════════════════════════════════════════
    # TAB 5: CLUSTER × ATU
    # ════════════════════════════════════════════════════════════════════════
    with tabs[4]:
        render_cluster_crosstabs(df)

    # ════════════════════════════════════════════════════════════════════════
    # TAB 6: FULL SUMMARY TABLE
    # ════════════════════════════════════════════════════════════════════════
    with tabs[5]:
        render_full_table(df)


# ── VA × ATU ──────────────────────────────────────────────────────────────────

def render_va_crosstabs(df):
    va_yes = df[df["any_va"] == 1]
    va_no  = df[df["any_va"] == 0]
    n_yes, n_no = len(va_yes), len(va_no)

    st.markdown(f"""
<div style="background:white;border:1px solid {MGRAY};border-radius:12px;padding:16px 20px;margin-bottom:20px">
  <div style="font-size:10px;text-transform:uppercase;letter-spacing:.2em;color:#94A3B8;font-weight:600">SECTION OVERVIEW</div>
  <div style="font-family:'DM Serif Display',serif;font-size:20px;color:#0F172A;margin-top:4px">Visual Aid Used vs. Not Used — {n_yes + n_no} HCPs</div>
  <div style="font-size:12px;color:#64748B;margin-top:4px">
    VA Used: n={n_yes} ({round(n_yes/(n_yes+n_no)*100)}%) &nbsp;|&nbsp;
    VA Not Used: n={n_no} ({round(n_no/(n_yes+n_no)*100)}%)
  </div>
  <div style="font-size:11px;color:#94A3B8;margin-top:6px">
    PET Q1_100Z (VA content types) → ATU Q3_60Z (current/future Vora share),
    Q3_110Z (attribute importance), Q3_120Z (Voranigo performance), ServierONE familiarity
  </div>
</div>
""", unsafe_allow_html=True)

    xt_list = [
        # (title, description, col_a, col_b, is_pct, source)
        ("VA Used → Current Voranigo Patient Share",
         "Among HCPs who had a visual aid in the most recent rep visit vs. those who didn't, what % of their Grade 2 patients are currently on Voranigo? Pulled from Q3_60Z B8 (current Vora) ÷ total Gr2 PL (S0_120Z).",
         "curr_vora_share", "curr_vora_share", False, "PET Q1_100Z any=1/0 × ATU Q3_60Z_B8 / S0_120Z"),
        ("VA Used → Future Voranigo Prescribing Intent",
         "HCPs who received a VA in the visit report higher future Voranigo intent? Pulled from Q3_60Z B8 next-10-patient allocations across all 12 patient types.",
         "future_intent", "future_intent", False, "PET Q1_100Z any=1/0 × ATU Q3_60Z_B8_future"),
        ("VA Used → Voranigo Familiarity (Q2_20Z)",
         "Does visual aid use correlate with higher product familiarity? Scale 1–5 from Q2_20Z item k (Voranigo).",
         "vora_fam", "vora_fam", False, "PET Q1_100Z any=1/0 × ATU Q2_20Z_k"),
        ("VA Used → Unaided Voranigo Awareness (Q2_10Z)",
         "Text response scanning: was Voranigo/vorasidenib mentioned unprompted? VA visits vs. non-VA visits.",
         "unaided", "unaided", True, "PET Q1_100Z any=1/0 × ATU Q2_10Z text scan"),
        ("VA Used → Attribute Importance: Prolonged PFS",
         "Doctors who received a VA — how important is PFS when selecting treatment? Q3_110Z A1 (adjuvant column), scale 1–7.",
         "imp_Prolonged PFS", "imp_Prolonged PFS", False, "PET Q1_100Z × ATU Q3_110Z_A1"),
        ("VA Used → Attribute Importance: Manufacturer Services",
         "Does VA use connect to valuing ServierONE? Q3_110Z attribute 12 (manufacturer patient services), 1–7.",
         "imp_Manufacturer patient services", "imp_Manufacturer patient services", False, "PET Q1_100Z × ATU Q3_110Z_A12"),
        ("VA Used → Voranigo Performance: Reduces Seizures",
         "HCPs who got a VA — do they rate Voranigo higher on seizure reduction? Q3_120Z Voranigo column, attribute 18 (reduces seizures).",
         "perf_Reduces seizures", "perf_Reduces seizures", False, "PET Q1_100Z × ATU Q3_120Z_B_A18"),
        ("VA Used → Voranigo Performance: Prolonged OS",
         "Does VA use lift OS perception? Q3_120Z Voranigo column, attribute 3 (prolonged OS), scale 1–7.",
         "perf_Prolonged OS", "perf_Prolonged OS", False, "PET Q1_100Z × ATU Q3_120Z_B_A3"),
        ("VA Used → Barriers Cited (Q3_220Z)",
         "Do HCPs who received a VA cite fewer access barriers? Number of barrier options selected in Q3_220Z (0–7).",
         "barriers", "barriers", False, "PET Q1_100Z × ATU Q3_220Z barrier count"),
        ("VA Used → ServierONE Programmes Known (Q3_260BZ)",
         "Does VA content (especially access toolkit) connect to more ServierONE programme knowledge? 0–5 programmes named.",
         "progs_known", "progs_known", False, "PET Q1_100Z × ATU Q3_260BZ count"),
        ("VA: Access Toolkit Used → ServierONE Familiarity",
         "Specifically when the access toolkit VA was shown (Q1_100Z option A7), does ServierONE familiarity (Q3_260AZ, 1–5) rise?",
         "s1_fam", "s1_fam", False, "PET Q1_100Z_A7=1/0 × ATU Q3_260AZ"),
        ("VA Used → NCCN Familiarity (Q2_00Z)",
         "Visits with a VA correlate with higher NCCN guideline familiarity? Q2_00Z scale 1–5.",
         "nccn_fam", "nccn_fam", False, "PET Q1_100Z × ATU Q2_00Z"),
        ("VA Used → Clinical Belief Alignment (Q4_00Z)",
         "Average of 8 clinical belief alignment statements, 1–7 scale. VA exposure → stronger alignment?",
         "belief_align", "belief_align", False, "PET Q1_100Z × ATU Q4_00Z avg"),
        ("VA Used → ICI Score",
         "Overall ICI score comparison: did having a VA in the last visit connect to higher composite conversion?",
         "ICI", "ICI", False, "PET Q1_100Z × computed ICI"),
        ("VA Used → ABR Dimension Score",
         "Access Barrier Resolution sub-score for VA vs. no-VA HCPs. VA should specifically lift ABR.",
         "ABR", "ABR", False, "PET Q1_100Z × ICI_ABR"),
    ]

    for i, (title, desc, col_a, col_b, is_pct, source) in enumerate(xt_list, 1):
        a_data = va_yes[col_a].dropna() if col_a in va_yes.columns else pd.Series()
        b_data = va_no[col_b].dropna() if col_b in va_no.columns else pd.Series()

        if a_data.empty or b_data.empty:
            continue

        _, p_val, sig, effect = statsig_test(a_data, b_data)

        if is_pct:
            val_a = a_data.mean()
            val_b = b_data.mean()
            fig = bar_chart(
                [col_a.replace("_", " ").title()],
                [val_a], [val_b],
                f"VA Used (n={n_yes})", f"No VA (n={n_no})",
                title, TEAL, CRIMSON, pct=True
            )
        else:
            val_a = a_data.mean()
            val_b = b_data.mean()
            fig = go.Figure()
            fig.add_trace(go.Bar(name=f"VA Used (n={n_yes})", x=[title[:30]], y=[val_a],
                                 marker_color=TEAL, text=[f"{val_a:.1f}"], textposition="outside"))
            fig.add_trace(go.Bar(name=f"No VA (n={n_no})", x=[title[:30]], y=[val_b],
                                 marker_color=CRIMSON, text=[f"{val_b:.1f}"], textposition="outside"))
            fig.update_layout(
                barmode="group", height=300,
                plot_bgcolor="white", paper_bgcolor="white",
                font=dict(family="Inter", size=11),
                yaxis=dict(showgrid=True, gridcolor="#F1F5F9"),
                legend=dict(orientation="h", yanchor="bottom", y=-0.35),
                margin=dict(l=0, r=0, t=10, b=0),
            )

        with st.container():
            st.markdown(f"""
<div class="xtab-card">
  <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:8px">
    <div>
      <div style="font-size:9px;text-transform:uppercase;letter-spacing:.2em;color:#94A3B8;font-weight:600">VA CROSS-TAB #{i:03d} · {effect or ''}</div>
      <div style="font-family:'DM Serif Display',serif;font-size:18px;color:#0F172A">{title}</div>
      <div style="font-size:12px;color:{DGRAY};margin-top:4px;line-height:1.5">{desc}</div>
    </div>
    <div style="text-align:right;flex-shrink:0;margin-left:16px">
      {sig_badge(p_val, sig)}
      <div style="font-size:10px;color:#94A3B8;margin-top:4px">VA Used: n={n_yes} | No VA: n={n_no}</div>
      <div style="font-size:10px;color:#94A3B8">Δ = {round(val_a - val_b, 2)}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True)
            st.markdown(f'<div style="font-size:10px;color:#94A3B8;text-transform:uppercase;letter-spacing:.15em;margin-bottom:8px">Source: {source}</div>',
                        unsafe_allow_html=True)
            st.markdown("---")


# ── LTIP × ATU ────────────────────────────────────────────────────────────────

def render_ltip_crosstabs(df):
    ltip_high = df[df["ltip_top2"] == 1]
    ltip_low  = df[df["ltip_top2"] == 0]
    n_h, n_l = len(ltip_high), len(ltip_low)

    st.markdown(f"""
<div style="background:white;border:1px solid {MGRAY};border-radius:12px;padding:16px 20px;margin-bottom:20px">
  <div style="font-size:10px;text-transform:uppercase;letter-spacing:.2em;color:#94A3B8;font-weight:600">SECTION OVERVIEW</div>
  <div style="font-family:'DM Serif Display',serif;font-size:20px;color:#0F172A;margin-top:4px">LTIP Top-2 (6–7) vs Non-Top-2 — {n_h + n_l} HCPs</div>
  <div style="font-size:12px;color:#64748B;margin-top:4px">
    LTIP Top-2 (score 6–7): n={n_h} ({round(n_h/(n_h+n_l)*100) if n_h+n_l>0 else 0}%) &nbsp;|&nbsp;
    LTIP Non-Top-2 (1–5): n={n_l} ({round(n_l/(n_h+n_l)*100) if n_h+n_l>0 else 0}%)
  </div>
  <div style="font-size:11px;color:#94A3B8;margin-top:6px">
    PET C3_35Z (likelihood to increase prescribing, 1–7, top-2 = 6–7) →
    ATU Q3_60Z (Vora share), Q3_110Z (importance), Q3_120Z (perception), Q3_220Z (barriers), Q3_260 (ServierONE)
  </div>
</div>
""", unsafe_allow_html=True)

    ltip_xt = [
        ("LTIP Top-2 → Current Voranigo Share",
         "HCPs who said 'very likely to increase prescribing' (score 6–7 on C3_35Z) — what is their current Voranigo patient share from Q3_60Z?",
         "curr_vora_share", False, "PET C3_35Z top2=1/0 × ATU Q3_60Z_B8 / Gr2PL"),
        ("LTIP Top-2 → Future Voranigo Intent",
         "Among top-2 LTIP scorers, what does the forward-looking Q3_60Z B8 next-10-patient allocation look like?",
         "future_intent", False, "PET C3_35Z top2 × ATU Q3_60Z_B8_future"),
        ("LTIP Top-2 → Voranigo Familiarity",
         "Higher prescribing intent connects to deeper product familiarity? Q2_20Z item k, 1–5.",
         "vora_fam", False, "PET C3_35Z top2 × ATU Q2_20Z_k"),
        ("LTIP Top-2 → Unaided Awareness",
         "LTIP top-2 HCPs — did they mention Voranigo unprompted in Q2_10Z?",
         "unaided", True, "PET C3_35Z top2 × ATU Q2_10Z text"),
        ("LTIP Top-2 → Importance of Seizure Reduction",
         "Do high-intent HCPs rate seizure reduction higher as a treatment attribute? Q3_110Z attribute 18, 1–7.",
         "imp_Reduces seizures", False, "PET C3_35Z top2 × ATU Q3_110Z_A18"),
        ("LTIP Top-2 → Importance of QoL on Treatment",
         "Good patient QoL importance (Q3_110Z attr 10) among LTIP top-2 vs non-top-2.",
         "imp_Good patient QoL", False, "PET C3_35Z top2 × ATU Q3_110Z_A10"),
        ("LTIP Top-2 → Voranigo Performance: PFS",
         "Does high prescribing intent correlate with better Voranigo PFS ratings? Q3_120Z Voranigo col, attr 1.",
         "perf_Prolonged PFS", False, "PET C3_35Z top2 × ATU Q3_120Z_B_A1"),
        ("LTIP Top-2 → Voranigo Performance: Fertility",
         "Fertility preservation rating for Voranigo (Q3_120Z_B_A16) — higher among high-intent HCPs?",
         "perf_Ability to preserve fertility", False, "PET C3_35Z top2 × ATU Q3_120Z_B_A16"),
        ("LTIP Top-2 → ServierONE Programmes Known",
         "High-intent prescribers — do they know more ServierONE programmes? Q3_260BZ count 0–5.",
         "progs_known", False, "PET C3_35Z top2 × ATU Q3_260BZ"),
        ("LTIP Top-2 → Barriers Cited",
         "LTIP top-2 HCPs cite fewer barriers? Q3_220Z barrier count.",
         "barriers", False, "PET C3_35Z top2 × ATU Q3_220Z"),
        ("LTIP Top-2 → NCCN Familiarity",
         "High-intent prescribers are more familiar with NCCN guidelines? Q2_00Z, 1–5.",
         "nccn_fam", False, "PET C3_35Z top2 × ATU Q2_00Z"),
        ("LTIP Top-2 → NGS Testing Rate",
         "Do high-intent HCPs test more patients for IDH mutations via NGS? Q1_00Z combined NGS rate.",
         "ngs_rate", False, "PET C3_35Z top2 × ATU Q1_00Z"),
        ("LTIP Top-2 → ICI Score",
         "Overall ICI comparison: top-2 LTIP vs non-top-2.",
         "ICI", False, "PET C3_35Z top2 × ICI computed"),
        ("LTIP Top-2 → IBC Dimension",
         "Intent → Behavior sub-score should directly reflect LTIP signal.",
         "IBC", False, "PET C3_35Z top2 × ICI_IBC"),
        ("LTIP Top-2 → MBC Dimension",
         "Message → Belief sub-score among high vs. low intent.",
         "MBC", False, "PET C3_35Z top2 × ICI_MBC"),
    ]

    for i, (title, desc, col, is_pct, source) in enumerate(ltip_xt, 1):
        a_data = ltip_high[col].dropna() if col in ltip_high.columns else pd.Series()
        b_data = ltip_low[col].dropna() if col in ltip_low.columns else pd.Series()
        if a_data.empty or b_data.empty:
            continue

        _, p_val, sig, effect = statsig_test(a_data, b_data)
        val_a, val_b = a_data.mean(), b_data.mean()

        fig = go.Figure()
        if is_pct:
            fig.add_trace(go.Bar(name=f"LTIP Top-2 (n={n_h})", x=[col], y=[val_a],
                                 marker_color=GREEN, text=[f"{val_a*100:.0f}%"], textposition="outside"))
            fig.add_trace(go.Bar(name=f"Non-Top-2 (n={n_l})", x=[col], y=[val_b],
                                 marker_color=CRIMSON, text=[f"{val_b*100:.0f}%"], textposition="outside"))
        else:
            fig.add_trace(go.Bar(name=f"LTIP Top-2 (n={n_h})", x=[col], y=[val_a],
                                 marker_color=GREEN, text=[f"{val_a:.1f}"], textposition="outside"))
            fig.add_trace(go.Bar(name=f"Non-Top-2 (n={n_l})", x=[col], y=[val_b],
                                 marker_color=CRIMSON, text=[f"{val_b:.1f}"], textposition="outside"))
        fig.update_layout(barmode="group", height=280, plot_bgcolor="white", paper_bgcolor="white",
                          font=dict(family="Inter", size=11),
                          yaxis=dict(showgrid=True, gridcolor="#F1F5F9"),
                          legend=dict(orientation="h", yanchor="bottom", y=-0.35),
                          margin=dict(l=0, r=0, t=10, b=0))

        st.markdown(f"""
<div class="xtab-card">
  <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:8px">
    <div>
      <div style="font-size:9px;text-transform:uppercase;letter-spacing:.2em;color:#94A3B8;font-weight:600">LTIP CROSS-TAB #{i:03d}</div>
      <div style="font-family:'DM Serif Display',serif;font-size:18px;color:#0F172A">{title}</div>
      <div style="font-size:12px;color:{DGRAY};margin-top:4px;line-height:1.5">{desc}</div>
    </div>
    <div style="text-align:right;flex-shrink:0;margin-left:16px">
      {sig_badge(p_val, sig)}
      <div style="font-size:10px;color:#94A3B8;margin-top:4px">Top-2: n={n_h} | Non-Top-2: n={n_l}</div>
      <div style="font-size:10px;color:#94A3B8">Δ = {round(val_a - val_b, 2)}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown(f'<div style="font-size:10px;color:#94A3B8;text-transform:uppercase;letter-spacing:.15em;margin-bottom:8px">Source: {source}</div>',
                    unsafe_allow_html=True)
        st.markdown("---")


# ── ServierONE × ATU ──────────────────────────────────────────────────────────

def render_servier_crosstabs(df):
    s1_yes = df[df["servier_aware"] == 1]
    s1_no  = df[df["servier_aware"] == 0]
    n_y, n_n = len(s1_yes), len(s1_no)

    st.markdown(f"""
<div style="background:white;border:1px solid {MGRAY};border-radius:12px;padding:16px 20px;margin-bottom:20px">
  <div style="font-size:10px;text-transform:uppercase;letter-spacing:.2em;color:#94A3B8;font-weight:600">SECTION OVERVIEW</div>
  <div style="font-family:'DM Serif Display',serif;font-size:20px;color:#0F172A;margin-top:4px">ServierONE Aware vs. Unaware — {n_y + n_n} HCPs</div>
  <div style="font-size:12px;color:#64748B;margin-top:4px">ServierONE Aware (fam≥3 or progs>0): n={n_y} | Unaware: n={n_n}</div>
  <div style="font-size:11px;color:#94A3B8;margin-top:6px">
    ATU Q3_260AZ (familiarity 1–5) + Q3_260BZ (programmes known 0–5) →
    ATU usage metrics, barriers, Voranigo perception
  </div>
</div>
""", unsafe_allow_html=True)

    s1_xt = [
        ("ServierONE Aware → Current Voranigo Share", "curr_vora_share", False,
         "Doctors aware of ServierONE programmes — do they prescribe more Voranigo? Q3_60Z / Gr2PL.",
         "ATU Q3_260A/B × ATU Q3_60Z_B8/Gr2PL"),
        ("ServierONE Aware → Future Voranigo Intent", "future_intent", False,
         "Forward-looking Voranigo intent (Q3_60Z next 10 patients) among ServierONE-aware HCPs.",
         "ATU Q3_260 aware × ATU Q3_60Z_B8_future"),
        ("ServierONE Aware → Barriers Cited", "barriers", False,
         "Programme awareness should reduce access barriers. Q3_220Z count 0–7.",
         "ATU Q3_260 aware × ATU Q3_220Z count"),
        ("ServierONE Aware → Access VA Used", "access_va", False,
         "HCPs who know ServierONE — did reps show access-related visual aids in PET Q1_100Z?",
         "ATU Q3_260 aware × PET Q1_100Z access_va"),
        ("ServierONE Aware → ABR Score", "ABR", False,
         "Access Barrier Resolution ICI sub-score for ServierONE-aware vs. unaware.",
         "ATU Q3_260 aware × ICI_ABR"),
        ("ServierONE Aware → ICI Score", "ICI", False,
         "Overall ICI composite score for ServierONE-aware vs. unaware HCPs.",
         "ATU Q3_260 aware × ICI computed"),
        ("ServierONE Aware → Voranigo Familiarity", "vora_fam", False,
         "Does ServierONE awareness connect to product familiarity (Q2_20Z, 1–5)?",
         "ATU Q3_260 aware × ATU Q2_20Z_k"),
        ("ServierONE Aware → Unaided Awareness", "unaided", True,
         "ServierONE-aware HCPs — more likely to mention Voranigo unprompted in Q2_10Z?",
         "ATU Q3_260 aware × ATU Q2_10Z text"),
        ("ServierONE Aware → Rep Preferred Source", "rep_pref", True,
         "Do ServierONE-aware HCPs trust the rep channel more (Q4_30Z, preferred source)?",
         "ATU Q3_260 aware × ATU Q4_30Z"),
        ("ServierONE Aware → Perf: Manufacturer Services", "perf_Manufacturer patient services", False,
         "Voranigo rating on manufacturer patient services attribute (Q3_120Z_B_A12, 1–7).",
         "ATU Q3_260 aware × ATU Q3_120Z_B_A12"),
    ]

    for i, (title, col, is_pct, desc, source) in enumerate(s1_xt, 1):
        a_data = s1_yes[col].dropna() if col in s1_yes.columns else pd.Series()
        b_data = s1_no[col].dropna() if col in s1_no.columns else pd.Series()
        if a_data.empty or b_data.empty:
            continue
        _, p_val, sig, effect = statsig_test(a_data, b_data)
        val_a, val_b = a_data.mean(), b_data.mean()

        fig = go.Figure()
        mul = 100 if is_pct else 1
        fmt = ".0f" if is_pct else ".1f"
        fig.add_trace(go.Bar(name=f"S1 Aware (n={n_y})", x=[col], y=[val_a * mul],
                             marker_color=TEAL, text=[f"{val_a*mul:{fmt}}{'%' if is_pct else ''}"], textposition="outside"))
        fig.add_trace(go.Bar(name=f"S1 Unaware (n={n_n})", x=[col], y=[val_b * mul],
                             marker_color=CRIMSON, text=[f"{val_b*mul:{fmt}}{'%' if is_pct else ''}"], textposition="outside"))
        fig.update_layout(barmode="group", height=260, plot_bgcolor="white", paper_bgcolor="white",
                          font=dict(family="Inter", size=11),
                          yaxis=dict(showgrid=True, gridcolor="#F1F5F9"),
                          legend=dict(orientation="h", yanchor="bottom", y=-0.35),
                          margin=dict(l=0, r=0, t=10, b=0))

        st.markdown(f"""
<div class="xtab-card">
  <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:8px">
    <div>
      <div style="font-size:9px;text-transform:uppercase;letter-spacing:.2em;color:#94A3B8;font-weight:600">SERVIER ONE CROSS-TAB #{i:03d}</div>
      <div style="font-family:'DM Serif Display',serif;font-size:18px;color:#0F172A">{title}</div>
      <div style="font-size:12px;color:{DGRAY};margin-top:4px;line-height:1.5">{desc}</div>
    </div>
    <div style="text-align:right;flex-shrink:0;margin-left:16px">
      {sig_badge(p_val, sig)}
      <div style="font-size:10px;color:#94A3B8;margin-top:4px">Aware: n={n_y} | Unaware: n={n_n}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown(f'<div style="font-size:10px;color:#94A3B8;text-transform:uppercase;letter-spacing:.15em;margin-bottom:8px">Source: {source}</div>',
                    unsafe_allow_html=True)
        st.markdown("---")


# ── ICI DIMENSIONS × ATU ──────────────────────────────────────────────────────

def render_ici_crosstabs(df):
    st.markdown(f"""
<div style="font-family:'DM Serif Display',serif;font-size:24px;color:#0F172A;margin-bottom:16px">
  ICI Dimension Scores × ATU Metrics
</div>
""", unsafe_allow_html=True)

    dim_pairs = [
        ("AC Score", "AC", "curr_vora_share", "Current Vora Share"),
        ("IBC Score", "IBC", "future_intent", "Future Intent"),
        ("MBC Score", "MBC", "perf_Prolonged PFS", "Vora PFS Rating"),
        ("RTC Score", "RTC", "rep_pref", "Rep Preferred Source"),
        ("ABR Score", "ABR", "progs_known", "Progs Known"),
        ("KCC Score", "KCC", "belief_align", "Belief Alignment"),
        ("CI Score", "CI", "vora_gap", "Vora Perf Gap vs Competitor"),
    ]

    for i, (dim_label, dim_col, atu_col, atu_label) in enumerate(dim_pairs, 1):
        if dim_col not in df.columns or atu_col not in df.columns:
            continue

        x = df[dim_col].dropna()
        y = df[atu_col].dropna()
        merged = df[[dim_col, atu_col]].dropna()

        if len(merged) < 5:
            continue

        r, p = scipy_stats.pearsonr(merged[dim_col], merged[atu_col])
        sig = p < 0.05

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=merged[dim_col], y=merged[atu_col],
            mode="markers",
            marker=dict(color=TEAL, size=8, opacity=0.7),
            name="HCPs",
        ))
        # Trend line
        z = np.polyfit(merged[dim_col], merged[atu_col], 1)
        xr = np.linspace(merged[dim_col].min(), merged[dim_col].max(), 50)
        fig.add_trace(go.Scatter(x=xr, y=np.polyval(z, xr), mode="lines",
                                 line=dict(color=CRIMSON, width=2, dash="dash"),
                                 name=f"Trend (r={r:.2f})"))
        fig.update_layout(
            height=320, plot_bgcolor="white", paper_bgcolor="white",
            font=dict(family="Inter", size=11),
            xaxis_title=dim_label, yaxis_title=atu_label,
            legend=dict(orientation="h", yanchor="bottom", y=-0.3),
            margin=dict(l=0, r=0, t=10, b=0),
        )

        st.markdown(f"""
<div class="xtab-card">
  <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:8px">
    <div>
      <div style="font-size:9px;text-transform:uppercase;letter-spacing:.2em;color:#94A3B8;font-weight:600">ICI DIMENSION CROSS-TAB #{i:03d}</div>
      <div style="font-family:'DM Serif Display',serif;font-size:18px;color:#0F172A">{dim_label} ↔ {atu_label}</div>
      <div style="font-size:12px;color:{DGRAY};margin-top:4px">
        Pearson correlation between the ICI {dim_col} sub-score and the ATU outcome metric.
        n={len(merged)} overlapping HCPs with both values present.
      </div>
    </div>
    <div style="text-align:right;flex-shrink:0;margin-left:16px">
      {sig_badge(round(p,4), sig)}
      <div style="font-size:11px;font-weight:600;color:{GREEN if sig else DGRAY};margin-top:4px">r = {r:.3f}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("---")


# ── CLUSTER × ATU ─────────────────────────────────────────────────────────────

def render_cluster_crosstabs(df):
    cluster_names = {1: "Patient ID", 2: "Access Pending", 3: "Evidence Gap",
                     4: "Narrative Build", 5: "Conviction-Led"}
    cluster_colors = {1: TEAL, 2: NAVY, 3: CRIMSON, 4: AMBER, 5: GREEN}

    metrics = [
        ("curr_vora_share", "Current Voranigo Share %"),
        ("future_intent", "Future Intent Score"),
        ("vora_fam", "Voranigo Familiarity 1–5"),
        ("progs_known", "ServierONE Progs Known"),
        ("barriers", "Barriers Cited"),
        ("ngs_rate", "NGS Testing Rate"),
        ("belief_align", "Clinical Belief Alignment"),
        ("ICI", "ICI Score"),
    ]

    for m_col, m_label in metrics:
        if m_col not in df.columns:
            continue
        cluster_avgs = df.groupby("cluster")[m_col].agg(["mean", "count"]).reset_index()
        cluster_avgs["cluster_name"] = cluster_avgs["cluster"].map(cluster_names)
        cluster_avgs = cluster_avgs.sort_values("cluster")

        fig = go.Figure()
        for _, row in cluster_avgs.iterrows():
            cid = int(row["cluster"])
            fig.add_trace(go.Bar(
                name=cluster_names[cid],
                x=[cluster_names[cid]],
                y=[row["mean"]],
                marker_color=cluster_colors[cid],
                text=[f"{row['mean']:.1f}\nn={int(row['count'])}"],
                textposition="outside",
            ))
        fig.update_layout(
            barmode="group", height=320,
            plot_bgcolor="white", paper_bgcolor="white",
            font=dict(family="Inter", size=11),
            showlegend=False,
            yaxis=dict(showgrid=True, gridcolor="#F1F5F9"),
            margin=dict(l=0, r=0, t=10, b=0),
        )

        st.markdown(f"""
<div class="xtab-card">
  <div style="font-family:'DM Serif Display',serif;font-size:18px;color:#0F172A;margin-bottom:4px">
    Cluster × {m_label}
  </div>
  <div style="font-size:12px;color:{DGRAY};margin-bottom:8px">
    {m_label} broken out by ICI engagement cluster. Sequential pattern expected:
    Conviction-Led should show highest values for usage/intent metrics.
  </div>
</div>
""", unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("---")


# ── FULL SUMMARY TABLE ────────────────────────────────────────────────────────

def render_full_table(df):
    st.markdown("""
<div style="font-family:'DM Serif Display',serif;font-size:24px;color:#0F172A;margin-bottom:12px">
  Full Cross-Tab Summary Table
</div>
""", unsafe_allow_html=True)

    va_yes = df[df["any_va"] == 1]
    va_no  = df[df["any_va"] == 0]
    ltip_h = df[df["ltip_top2"] == 1]
    ltip_l = df[df["ltip_top2"] == 0]
    s1_yes = df[df["servier_aware"] == 1]
    s1_no  = df[df["servier_aware"] == 0]

    rows = []
    combos = [
        ("VA Used vs Not", va_yes, va_no),
        ("LTIP Top-2 vs Non", ltip_h, ltip_l),
        ("ServierONE Aware vs Not", s1_yes, s1_no),
    ]
    metrics = ["curr_vora_share", "future_intent", "vora_fam", "barriers",
               "progs_known", "ICI", "IBC", "ABR", "MBC"]

    for split_name, grp_a, grp_b in combos:
        for m in metrics:
            if m not in df.columns:
                continue
            a = grp_a[m].dropna()
            b = grp_b[m].dropna()
            if len(a) < 2 or len(b) < 2:
                continue
            _, p, sig, eff = statsig_test(a, b)
            rows.append({
                "Split": split_name,
                "Metric": m,
                "Group A Mean": round(a.mean(), 2),
                "Group B Mean": round(b.mean(), 2),
                "Δ": round(a.mean() - b.mean(), 2),
                "n(A)": len(a),
                "n(B)": len(b),
                "p-value": p,
                "Significant": "✓" if sig else "—",
                "Effect": eff or "",
            })

    if rows:
        summary_df = pd.DataFrame(rows)
        st.dataframe(summary_df, use_container_width=True, height=500)
        csv = summary_df.to_csv(index=False)
        st.download_button("⬇ Download full cross-tab table", data=csv,
                           file_name="ici_crosstab_summary.csv", mime="text/csv")
