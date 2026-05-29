"""
Cross-Tab Repository — T2B % with conditional formatting, 90% and 95% sig levels.
Voranigo performance only (no Temozolomide/Radiation+CT).
Importance: First-Line vs Adjuvant separately.
10-bullet summary per segment. All abbreviations expanded.
Single bar chart with all 19 attributes per segment.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.stats import mannwhitneyu

TEAL="#0F4C5C"; NAVY="#1E293B"; CRIMSON="#832232"; AMBER="#B8860B"; GREEN="#15803D"
LGRAY="#F8FAFC"; MGRAY="#E2E8F0"; DGRAY="#64748B"

ATTRS = [
    "Prolonged PFS","Tumor volume reduction","Prolonged OS","Low grade 3-4 AEs",
    "Low hepatic toxicity","Low hematological toxicity","Low neurotoxicity",
    "Low risk hypermutations","Manageable LFT monitoring","Good patient QoL",
    "Affordable","Manufacturer patient services","Easy to prescribe",
    "Convenient route","Low risk long-term SEs","Ability to preserve fertility",
    "Delays next treatment","Reduces seizures","Fair office compensation",
]

VORA_PERF_COLS = list(range(492, 511))  # Q3_120Z Voranigo cols 20-38
IMP_ADJ_COLS   = list(range(432, 451))  # Q3_110Z adjuvant cols 0-18
IMP_FL_COLS    = list(range(451, 470))  # Q3_110Z first-line cols 19-37


def _build_merged(eng):
    """Build merged ATU+PET dataframe with all T2B columns."""
    if not hasattr(eng, 'atu_raw') or eng.atu_raw is None:
        return None
    atu_raw = eng.atu_raw
    pet_raw = eng.pet_raw
    atu_qcodes = atu_raw.iloc[2].values
    pet_qcodes = pet_raw.iloc[4].values
    atu = atu_raw.iloc[3:].reset_index(drop=True)
    pet = pet_raw.iloc[5:].reset_index(drop=True)

    def pcols(p): return [i for i,v in enumerate(pet_qcodes) if str(v).startswith(p)]

    atu['uid'] = pd.to_numeric(atu[1], errors='coerce')
    pet['uid'] = pd.to_numeric(pet[1], errors='coerce')
    atu = atu.dropna(subset=['uid']); pet = pet.dropna(subset=['uid'])
    atu['uid'] = atu['uid'].astype(int); pet['uid'] = pet['uid'].astype(int)
    overlap = sorted(set(atu['uid']) & set(pet['uid']))

    va_cols = pcols('Q1_100Z')
    ltip_col = 169

    records = []
    for uid in overlap:
        a = atu[atu['uid']==uid].iloc[0]
        p = pet[pet['uid']==uid].iloc[0]

        any_va = int((pd.to_numeric(pd.Series([p[c] for c in va_cols]), errors='coerce').fillna(0)==1).any())
        ltip = pd.to_numeric(p[ltip_col], errors='coerce') if ltip_col < len(p) else np.nan
        ltip_t2 = int(ltip >= 6) if not pd.isna(ltip) else 0

        r = {'uid': uid, 'any_va': any_va, 'ltip_top2': ltip_t2,
             'label_va': 'VA Used' if any_va else 'No VA',
             'label_ltip': 'LTIP Top-2 (≥6)' if ltip_t2 else 'LTIP Non-Top-2 (<6)'}

        for i, (attr, col) in enumerate(zip(ATTRS, VORA_PERF_COLS)):
            v = pd.to_numeric(a[col], errors='coerce') if col < len(a) else np.nan
            r[f'perf_{i}'] = v
            r[f't2b_perf_{i}'] = int(v >= 6) if not pd.isna(v) else np.nan

        for i, (attr, col) in enumerate(zip(ATTRS, IMP_ADJ_COLS)):
            v = pd.to_numeric(a[col], errors='coerce') if col < len(a) else np.nan
            r[f'imp_adj_{i}'] = v
            r[f't2b_imp_adj_{i}'] = int(v >= 6) if not pd.isna(v) else np.nan

        for i, (attr, col) in enumerate(zip(ATTRS, IMP_FL_COLS)):
            v = pd.to_numeric(a[col], errors='coerce') if col < len(a) else np.nan
            r[f'imp_fl_{i}'] = v
            r[f't2b_imp_fl_{i}'] = int(v >= 6) if not pd.isna(v) else np.nan

        records.append(r)

    return pd.DataFrame(records)


def _mw_t2b(grp_a, grp_b):
    """Mann-Whitney on raw scores. Returns (p, sig90, sig95)."""
    a = pd.to_numeric(grp_a, errors='coerce').dropna()
    b = pd.to_numeric(grp_b, errors='coerce').dropna()
    if len(a) < 3 or len(b) < 3:
        return None, False, False
    try:
        _, p = mannwhitneyu(a, b, alternative='two-sided')
        return round(p, 3), p < 0.10, p < 0.05
    except:
        return None, False, False


def _cell_color(pct, baseline=None):
    """Return background color for T2B cell with conditional formatting."""
    if baseline is not None:
        delta = pct - baseline
        if delta >= 15: return "#15803D", "white"
        if delta >= 8:  return "#86EFAC", "#0F172A"
        if delta <= -15: return "#B91C1C", "white"
        if delta <= -8:  return "#FCA5A5", "#0F172A"
    # Absolute thresholds
    if pct >= 70: return "#15803D22", "#15803D"
    if pct >= 55: return "#FEF9C3", "#713F12"
    return "#FEE2E2", "#991B1B"


def _sig_chip(p, sig90, sig95):
    if p is None:
        return '<span style="color:#94A3B8;font-size:9px">n/a</span>'
    if sig95:
        return f'<span style="background:#15803D;color:white;padding:1px 6px;border-radius:3px;font-size:9px;font-weight:700">p={p} ✓95%</span>'
    if sig90:
        return f'<span style="background:#FBBF24;color:#0F172A;padding:1px 6px;border-radius:3px;font-size:9px;font-weight:700">p={p} ✓90%</span>'
    return f'<span style="background:#F1F5F9;color:#64748B;padding:1px 6px;border-radius:3px;font-size:9px">p={p} n.s.</span>'


def _bar_chart_19(t2b_a, t2b_b, label_a, label_b, n_a, n_b, sig_flags, title):
    """Single bar chart with all 19 attributes side by side."""
    fig = go.Figure()
    colors_a = []
    colors_b = []
    for i, (s90, s95) in enumerate(sig_flags):
        colors_a.append(GREEN if s95 else (AMBER if s90 else TEAL))
        colors_b.append("#CBD5E1")

    fig.add_trace(go.Bar(
        name=f"{label_a} (n={n_a})",
        x=ATTRS, y=t2b_a,
        marker_color=colors_a,
        text=[f"{v:.0f}%" for v in t2b_a],
        textposition="outside",
        textfont=dict(size=9),
    ))
    fig.add_trace(go.Bar(
        name=f"{label_b} (n={n_b})",
        x=ATTRS, y=t2b_b,
        marker_color="#94A3B8",
        text=[f"{v:.0f}%" for v in t2b_b],
        textposition="outside",
        textfont=dict(size=9),
    ))
    fig.update_layout(
        barmode="group",
        height=420,
        title=dict(text=title, font=dict(family="DM Serif Display", size=16, color="#0F172A")),
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Inter", size=10, color="#0F172A"),
        yaxis=dict(range=[0, 115], showgrid=True, gridcolor="#F1F5F9",
                   title="% Top-2 Box (ratings 6–7 out of 7)"),
        xaxis_tickangle=-40,
        legend=dict(orientation="h", yanchor="bottom", y=-0.45, font=dict(size=11)),
        margin=dict(l=0, r=0, t=40, b=10),
        annotations=[
            dict(x=0.01, y=1.06, xref="paper", yref="paper",
                 text="<b>Green</b> = sig at 95% · <b>Yellow</b> = sig at 90% · <b>Grey</b> = not significant",
                 showarrow=False, font=dict(size=10, color=DGRAY)),
        ]
    )
    return fig


def _evidence_block(attr, col_key, t2b_a, t2b_b, n_a, n_b, label_a, label_b,
                    p, sig90, sig95, split_desc, metric_desc):
    """Expandable evidence block for each attribute row."""
    with st.expander(f"↳ {attr} — full methodology & data source"):
        st.markdown(f"""
<div style="background:{LGRAY};border-radius:10px;padding:14px 16px;border-left:3px solid {TEAL}">
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px">
    <div style="background:white;border-radius:8px;padding:12px;border-top:3px solid {TEAL}">
      <div style="font-size:9px;text-transform:uppercase;letter-spacing:.18em;color:{TEAL};font-weight:700;margin-bottom:4px">{label_a.upper()}</div>
      <div style="font-size:28px;font-weight:700;color:#0F172A">{t2b_a:.0f}%</div>
      <div style="font-size:11px;color:{DGRAY}">n = {n_a} HCPs · Top-2 Box (ratings 6 or 7 out of 7)</div>
    </div>
    <div style="background:white;border-radius:8px;padding:12px;border-top:3px solid {CRIMSON}">
      <div style="font-size:9px;text-transform:uppercase;letter-spacing:.18em;color:{CRIMSON};font-weight:700;margin-bottom:4px">{label_b.upper()}</div>
      <div style="font-size:28px;font-weight:700;color:#0F172A">{t2b_b:.0f}%</div>
      <div style="font-size:11px;color:{DGRAY}">n = {n_b} HCPs · Top-2 Box (ratings 6 or 7 out of 7)</div>
    </div>
  </div>
  <div style="background:white;border-radius:8px;padding:10px 12px;margin-bottom:10px">
    <div style="font-size:10px;text-transform:uppercase;letter-spacing:.15em;color:{NAVY};font-weight:700;margin-bottom:4px">HOW THE SPLIT WAS DEFINED</div>
    <div style="font-size:12px;color:#334155;line-height:1.6">{split_desc}</div>
  </div>
  <div style="background:white;border-radius:8px;padding:10px 12px;margin-bottom:10px">
    <div style="font-size:10px;text-transform:uppercase;letter-spacing:.15em;color:{NAVY};font-weight:700;margin-bottom:4px">HOW THE METRIC WAS COMPUTED</div>
    <div style="font-size:12px;color:#334155;line-height:1.6">{metric_desc}</div>
    <div style="font-size:10px;color:#94A3B8;margin-top:4px">Source: ATU Q3_120Z (Voranigo column, attribute {col_key+1} of 19) — absolute column {VORA_PERF_COLS[col_key]}</div>
  </div>
  <div style="background:{'#F0FDF4' if sig95 else '#FFFBEB' if sig90 else '#F8FAFC'};border-radius:8px;padding:10px 12px;border-left:3px solid {'#15803D' if sig95 else AMBER if sig90 else MGRAY}">
    <div style="font-size:10px;text-transform:uppercase;letter-spacing:.15em;color:{'#15803D' if sig95 else '#92400E' if sig90 else '#64748B'};font-weight:700;margin-bottom:4px">
      STATISTICAL TEST — Mann-Whitney U (two-sided, non-parametric)
    </div>
    <div style="font-size:12px;color:#334155;line-height:1.7">
      p-value: <b>{p if p is not None else 'N/A'}</b><br>
      Significant at 95% (p&lt;0.05): <b>{'Yes ✓' if sig95 else 'No'}</b><br>
      Significant at 90% (p&lt;0.10): <b>{'Yes ✓' if sig90 else 'No'}</b><br>
      Delta (A−B): <b>{'+' if t2b_a-t2b_b>0 else ''}{t2b_a-t2b_b:.0f} percentage points</b><br>
      {('<b>⚠ Not significant:</b> The observed delta of ' + f'{abs(t2b_a-t2b_b):.0f}pp' + ' could be due to chance at n=' + str(n_a+n_b) + '. Reported as-is without inference.') if not sig90 and p is not None else ('<b>✓ Significant at ' + ('95%' if sig95 else '90%') + ':</b> This difference is statistically meaningful at p=' + str(p) + '.') if p is not None else ''}
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


def _detail_table(df, grp_a, grp_b, label_a, label_b, split_desc, col_prefix, attr_prefix, imp_setting=None):
    """Full attribute table with T2B%, delta, sig, and evidence expander."""
    n_a = len(grp_a); n_b = len(grp_b)

    t2b_a_list = []; t2b_b_list = []; sig_flags = []
    rows_html = ""

    for i, attr in enumerate(ATTRS):
        col = f"{attr_prefix}{i}"
        raw_col = f"{col_prefix}{i}"
        va_t2 = grp_a[col].dropna(); nv_t2 = grp_b[col].dropna()
        va_raw = grp_a[raw_col].dropna() if raw_col in grp_a.columns else va_t2
        nv_raw = grp_b[raw_col].dropna() if raw_col in grp_b.columns else nv_t2

        t2_a = va_t2.mean() * 100 if len(va_t2) > 0 else 0
        t2_b = nv_t2.mean() * 100 if len(nv_t2) > 0 else 0
        delta = t2_a - t2_b

        p, sig90, sig95 = _mw_t2b(va_raw, nv_raw)
        sig_flags.append((sig90, sig95))
        t2b_a_list.append(t2_a); t2b_b_list.append(t2_b)

        # Cell colors
        bg_a, fg_a = _cell_color(t2_a, t2_b)
        bg_b, fg_b = _cell_color(t2_b)
        delta_color = GREEN if delta >= 10 else (CRIMSON if delta <= -10 else DGRAY)

        rows_html += f"""
<tr style="border-bottom:1px solid {MGRAY}">
  <td style="padding:8px 10px;font-size:12px;color:#0F172A;font-weight:500">{attr}</td>
  <td style="padding:8px 10px;text-align:center">
    <span style="background:{bg_a};color:{fg_a};padding:3px 10px;border-radius:4px;font-size:12px;font-weight:700">{t2_a:.0f}%</span>
  </td>
  <td style="padding:8px 10px;text-align:center">
    <span style="background:{bg_b};color:{fg_b};padding:3px 10px;border-radius:4px;font-size:12px;font-weight:700">{t2_b:.0f}%</span>
  </td>
  <td style="padding:8px 10px;text-align:center;font-size:12px;font-weight:700;color:{delta_color}">
    {'+' if delta>0 else ''}{delta:.0f}pp
  </td>
  <td style="padding:8px 10px;text-align:center">{_sig_chip(p, sig90, sig95)}</td>
</tr>"""

    # Render table
    header = f"""
<table style="width:100%;border-collapse:collapse;font-family:Inter,sans-serif">
  <thead>
    <tr style="background:{LGRAY}">
      <th style="padding:8px 10px;text-align:left;font-size:10px;color:#64748B;font-weight:600;text-transform:uppercase;letter-spacing:.12em">Attribute</th>
      <th style="padding:8px 10px;text-align:center;font-size:10px;color:{TEAL};font-weight:700;text-transform:uppercase;letter-spacing:.12em">{label_a}<br><span style="font-weight:400;color:#94A3B8">n={n_a}</span></th>
      <th style="padding:8px 10px;text-align:center;font-size:10px;color:{CRIMSON};font-weight:700;text-transform:uppercase;letter-spacing:.12em">{label_b}<br><span style="font-weight:400;color:#94A3B8">n={n_b}</span></th>
      <th style="padding:8px 10px;text-align:center;font-size:10px;color:{DGRAY};font-weight:600;text-transform:uppercase;letter-spacing:.12em">Δ (A−B)</th>
      <th style="padding:8px 10px;text-align:center;font-size:10px;color:{DGRAY};font-weight:600;text-transform:uppercase;letter-spacing:.12em">Significance</th>
    </tr>
  </thead>
  <tbody>{rows_html}</tbody>
</table>"""
    st.markdown(header, unsafe_allow_html=True)

    # Color legend
    st.markdown(f"""
<div style="display:flex;gap:12px;margin-top:8px;flex-wrap:wrap;font-size:10px;color:{DGRAY}">
  <span><span style="background:#15803D;color:white;padding:1px 6px;border-radius:3px;font-size:9px">Green</span> ≥70% T2B or +15pp delta</span>
  <span><span style="background:#FEF9C3;color:#713F12;padding:1px 6px;border-radius:3px;font-size:9px">Yellow</span> 55–69% T2B or +8–14pp</span>
  <span><span style="background:#FEE2E2;color:#991B1B;padding:1px 6px;border-radius:3px;font-size:9px">Red</span> &lt;55% T2B or negative delta</span>
</div>
""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Bar chart
    setting_label = f"— {imp_setting}" if imp_setting else ""
    chart_title = f"Voranigo Top-2 Box %: {label_a} vs {label_b}{setting_label}<br><sup>ATU Q3_120Z (19 attributes, 1–7 scale, T2B = rated 6 or 7) · Voranigo only</sup>"
    fig = _bar_chart_19(t2b_a_list, t2b_b_list, label_a, label_b, n_a, n_b, sig_flags, chart_title)
    st.plotly_chart(fig, use_container_width=True)

    # Evidence expanders for each attribute
    st.markdown(f'<div style="font-size:10px;text-transform:uppercase;letter-spacing:.18em;color:{DGRAY};font-weight:600;margin-bottom:8px">EXPAND ANY ATTRIBUTE FOR FULL DATA SOURCE & METHODOLOGY</div>', unsafe_allow_html=True)
    for i, attr in enumerate(ATTRS):
        col = f"{attr_prefix}{i}"
        raw_col = f"{col_prefix}{i}"
        va_t2 = grp_a[col].dropna(); nv_t2 = grp_b[col].dropna()
        va_raw = grp_a[raw_col].dropna() if raw_col in grp_a.columns else va_t2
        nv_raw = grp_b[raw_col].dropna() if raw_col in grp_b.columns else nv_t2
        p, sig90, sig95 = _mw_t2b(va_raw, nv_raw)
        t2_a = va_t2.mean()*100 if len(va_t2)>0 else 0
        t2_b = nv_t2.mean()*100 if len(nv_t2)>0 else 0
        _evidence_block(attr, i, t2_a, t2_b, len(va_t2), len(nv_t2),
                        label_a, label_b, p, sig90, sig95, split_desc,
                        f"Top-2 Box: % of HCPs rating Voranigo 6 or 7 out of 7 on '{attr}'. "
                        f"Source: ATU Q3_120Z — 'How would you rate each of the following regimens as an adjuvant or first-line treatment for grade 2 IDH-mutant astrocytoma or oligodendroglioma on each attribute?' "
                        f"[1=Very poor → 7=Excellent]. Voranigo (vorasidenib) column only — Temozolomide and Radiation+CT are excluded from this view.")

    return t2b_a_list, t2b_b_list, sig_flags


def _ten_bullet_summary(t2b_a, t2b_b, sig_flags, label_a, label_b, n_a, n_b, split_name):
    """Generate 10 data-derived bullet points summarising the cross-tab."""
    sig95_attrs = [ATTRS[i] for i,(s90,s95) in enumerate(sig_flags) if s95]
    sig90_attrs = [ATTRS[i] for i,(s90,s95) in enumerate(sig_flags) if s90 and not s95]
    biggest_pos = sorted([(ATTRS[i], t2b_a[i]-t2b_b[i]) for i in range(len(ATTRS))], key=lambda x:-x[1])
    biggest_neg = sorted([(ATTRS[i], t2b_a[i]-t2b_b[i]) for i in range(len(ATTRS))], key=lambda x:x[1])
    highest_a = sorted([(ATTRS[i], t2b_a[i]) for i in range(len(ATTRS))], key=lambda x:-x[1])[:3]
    lowest_a  = sorted([(ATTRS[i], t2b_a[i]) for i in range(len(ATTRS))], key=lambda x:x[1])[:3]
    highest_b = sorted([(ATTRS[i], t2b_b[i]) for i in range(len(ATTRS))], key=lambda x:-x[1])[:2]
    over60_a = [(a,v) for a,v in zip(ATTRS,t2b_a) if v>=60]
    under40_a = [(a,v) for a,v in zip(ATTRS,t2b_a) if v<40]
    equal_attrs = [ATTRS[i] for i in range(len(ATTRS)) if abs(t2b_a[i]-t2b_b[i])<=5]
    avg_a = sum(t2b_a)/len(t2b_a); avg_b = sum(t2b_b)/len(t2b_b)
    overall_dir = "higher" if avg_a > avg_b else "lower" if avg_a < avg_b else "similar"

    bullets = []
    bullets.append(f"Overall Voranigo performance ratings are {overall_dir} among {label_a} HCPs (avg {avg_a:.0f}% T2B) compared to {label_b} (avg {avg_b:.0f}% T2B) across all 19 attributes.")
    if sig95_attrs:
        bullets.append(f"Statistically significant at 95% confidence (p<0.05): {', '.join(sig95_attrs)} — these differences are unlikely due to chance.")
    else:
        bullets.append(f"No attributes reach statistical significance at the 95% level (p<0.05) in this {n_a+n_b}-HCP sample — observed differences should be treated as directional only.")
    if sig90_attrs:
        bullets.append(f"Approaching significance at 90% confidence (p<0.10): {', '.join(sig90_attrs)} — worth monitoring in a larger sample.")
    if biggest_pos[0][1] >= 10:
        a, d = biggest_pos[0]
        bullets.append(f"Largest positive delta: '{a}' shows {d:+.0f}pp advantage for {label_a} ({t2b_a[ATTRS.index(a)]:.0f}% vs {t2b_b[ATTRS.index(a)]:.0f}%).")
    if biggest_neg[0][1] <= -10:
        a, d = biggest_neg[0]
        bullets.append(f"Only attribute where {label_b} leads: '{a}' ({t2b_b[ATTRS.index(a)]:.0f}% vs {t2b_a[ATTRS.index(a)]:.0f}%, delta {d:+.0f}pp) — warrants investigation.")
    bullets.append(f"Highest-rated attributes for {label_a}: {highest_a[0][0]} ({highest_a[0][1]:.0f}%), {highest_a[1][0]} ({highest_a[1][1]:.0f}%), {highest_a[2][0]} ({highest_a[2][1]:.0f}%).")
    bullets.append(f"Lowest-rated attributes for {label_a}: {lowest_a[0][0]} ({lowest_a[0][1]:.0f}%), {lowest_a[1][0]} ({lowest_a[1][1]:.0f}%) — potential areas where the clinical case needs strengthening.")
    if len(over60_a) > 0:
        bullets.append(f"{len(over60_a)} of 19 attributes clear the 60% T2B threshold for {label_a}: {', '.join([a for a,_ in over60_a[:4]])}{'...' if len(over60_a)>4 else ''}.")
    if len(under40_a) > 0:
        bullets.append(f"{len(under40_a)} attribute(s) below 40% T2B for {label_a}: {', '.join([a for a,_ in under40_a])} — these are where perception work is most needed.")
    if len(equal_attrs) > 0:
        bullets.append(f"{len(equal_attrs)} attributes show minimal difference (≤5pp) between groups: {', '.join(equal_attrs[:3])}{'...' if len(equal_attrs)>3 else ''} — {split_name} does not appear to influence these perceptions.")

    while len(bullets) < 10:
        bullets.append(f"Sample sizes: {label_a} n={n_a}, {label_b} n={n_b}. All findings based on the {n_a+n_b} overlapping HCPs who completed both ATU and PET surveys.")

    return bullets[:10]


def _render_summary_10(bullets, split_name):
    st.markdown(f"""
<div style="background:white;border:1px solid {MGRAY};border-radius:14px;padding:20px 24px;margin-bottom:20px">
  <div style="font-size:10px;text-transform:uppercase;letter-spacing:.2em;color:{TEAL};font-weight:700;margin-bottom:10px">
    10-POINT DATA SUMMARY — {split_name.upper()}
  </div>
""", unsafe_allow_html=True)
    for i, b in enumerate(bullets):
        st.markdown(f"""
<div style="display:flex;align-items:flex-start;gap:10px;margin-bottom:8px">
  <div style="width:22px;height:22px;border-radius:50%;background:{TEAL};color:white;font-size:10px;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0">{i+1}</div>
  <div style="font-size:12px;color:#334155;line-height:1.55">{b}</div>
</div>
""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render(eng):
    df = _build_merged(eng)
    if df is None or df.empty:
        st.warning("No data loaded."); return

    n = len(df)
    n_va = int(df['any_va'].sum())
    n_nva = int((df['any_va']==0).sum())
    n_ltip = int(df['ltip_top2'].sum())

    # Header
    st.markdown(f"""
<div style="margin-bottom:16px">
  <div style="font-size:10px;text-transform:uppercase;letter-spacing:.28em;color:{CRIMSON};font-weight:600">CROSS-TAB REPOSITORY</div>
  <h1 style="font-family:'DM Serif Display',serif;font-size:44px;font-weight:300;color:#0F172A;line-height:1.05;margin-bottom:10px">
    Voranigo performance &amp; importance.<br>
    <span style="color:{TEAL}">Every attribute. Every significance level.</span>
  </h1>
  <p style="font-size:14px;color:#475569;max-width:700px;line-height:1.65">
    {n} matched HCPs from ATU × PET. Top-2 Box % (ratings 6 or 7 out of 7) for Voranigo performance only —
    Temozolomide and Radiation+CT are excluded. Importance shown separately for Adjuvant and First-Line settings.
    Conditional formatting: green = strong, yellow = moderate, red = weak or negative delta.
    Every finding has an expandable full data source and methodology note.
  </p>
</div>
""", unsafe_allow_html=True)

    c1,c2,c3,c4 = st.columns(4)
    with c1: st.markdown(f'<div class="mcard"><div class="mlabel">MATCHED HCPs</div><div class="mval">{n}</div><div class="msub">Both ATU + PET</div></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="mcard"><div class="mlabel">VISUAL AID USED</div><div class="mval">{n_va}</div><div class="msub">vs {n_nva} no VA</div></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="mcard"><div class="mlabel">LTIP TOP-2 (≥6)</div><div class="mval">{n_ltip}</div><div class="msub">vs {n-n_ltip} non-top-2</div></div>', unsafe_allow_html=True)
    with c4: st.markdown(f'<div style="background:{TEAL};border-radius:16px;padding:24px"><div style="font-size:10px;text-transform:uppercase;letter-spacing:.22em;color:rgba(255,255,255,.6);font-weight:600">RATING SCALE</div><div style="font-family:\'DM Serif Display\',serif;font-size:22px;font-weight:300;color:white">1=Very poor<br>→ 7=Excellent<br>T2B = 6 or 7</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Main tabs
    tabs = st.tabs([
        "🎯 VA Used vs No VA — Performance",
        "📈 LTIP Top-2 vs Non — Performance",
        "⭐ Importance: Adjuvant vs First-Line",
        "🔬 VA Used vs No VA — Importance (Adjuvant)",
        "📋 All Results CSV",
    ])

    # ── TAB 1: VA vs No VA — Voranigo Performance ──────────────────────────
    with tabs[0]:
        va_yes = df[df['any_va']==1]
        va_no  = df[df['any_va']==0]

        st.markdown(f"""
<div style="background:white;border:1px solid {MGRAY};border-radius:12px;padding:14px 18px;margin-bottom:16px">
  <div style="font-size:14px;font-weight:600;color:#0F172A;margin-bottom:4px">Visual Aid Used vs Not Used — Voranigo Attribute Performance</div>
  <div style="font-size:12px;color:{DGRAY};margin-bottom:4px">
    <b>Split definition:</b> "Visual Aid Used" = at least one of 10 content types in PET Q1_100Z was flagged as shown during the rep visit (value=1). 
    Visual Aid Not Used = all 10 content types = 0 or missing.
  </div>
  <div style="font-size:10px;color:#94A3B8">Source: PET Q1_100Z · 10 binary items (product brochure, PI, patient support services, co-pay cards, patient brochures, disease state info, access toolkit, distribution info, admin guide, product summary/flashcard)</div>
</div>
""", unsafe_allow_html=True)

        split_desc = ("Visual Aid Used: PET Q1_100Z — at least one of 10 content types = 1 during most recent rep visit. "
                      "No VA: all 10 content types = 0. Note: reps may use VAs more selectively with lower-volume or lower-familiarity HCPs, "
                      "so this is an observed association, not necessarily causal.")

        t2b_a, t2b_b, sig_flags = _detail_table(
            df, va_yes, va_no,
            "VA Used", "No VA",
            split_desc,
            col_prefix="perf_", attr_prefix="t2b_perf_"
        )

        bullets = _ten_bullet_summary(t2b_a, t2b_b, sig_flags, "VA Used", "No VA", n_va, n_nva, "Visual Aid Used vs Not Used")
        _render_summary_10(bullets, "Visual Aid Used vs Not Used — Voranigo Performance")

    # ── TAB 2: LTIP Top-2 vs Non ──────────────────────────────────────────
    with tabs[1]:
        lt_yes = df[df['ltip_top2']==1]
        lt_no  = df[df['ltip_top2']==0]

        st.markdown(f"""
<div style="background:white;border:1px solid {MGRAY};border-radius:12px;padding:14px 18px;margin-bottom:16px">
  <div style="font-size:14px;font-weight:600;color:#0F172A;margin-bottom:4px">Likelihood to Increase Prescribing Top-2 Box vs Non-Top-2 — Voranigo Attribute Performance</div>
  <div style="font-size:12px;color:{DGRAY};margin-bottom:4px">
    <b>Split definition:</b> "Likelihood to Increase Prescribing (LTIP) Top-2 Box" = PET C3_35Z score of 6 or 7 out of 7 
    ("Extremely likely" or "Very likely" to increase prescribing based on the most recent rep interaction).
    Non-Top-2 = score 1–5.
  </div>
  <div style="font-size:10px;color:#94A3B8">Source: PET C3_35Z — "How likely are you to increase prescribing of Voranigo for gliomas based on your most recent interaction with the Servier representative?" [1=Not at all likely → 7=Extremely likely]</div>
</div>
""", unsafe_allow_html=True)

        split_desc = ("Likelihood to Increase Prescribing (LTIP) Top-2 Box: PET C3_35Z ≥6. "
                      "Non-Top-2: PET C3_35Z 1–5. The LTIP question captures post-interaction prescribing intent, "
                      "not actual behavior — it reflects willingness expressed to the rep in the moment of the visit.")

        t2b_a2, t2b_b2, sig_flags2 = _detail_table(
            df, lt_yes, lt_no,
            "LTIP Top-2 (≥6)", "LTIP Non-Top-2 (<6)",
            split_desc,
            col_prefix="perf_", attr_prefix="t2b_perf_"
        )

        bullets2 = _ten_bullet_summary(t2b_a2, t2b_b2, sig_flags2, "LTIP Top-2", "LTIP Non-Top-2", n_ltip, n-n_ltip, "LTIP Top-2 vs Non-Top-2 — Voranigo Performance")
        _render_summary_10(bullets2, "Likelihood to Increase Prescribing Top-2 Box vs Non — Voranigo Performance")

    # ── TAB 3: IMPORTANCE Adjuvant vs First-Line ──────────────────────────
    with tabs[2]:
        st.markdown(f"""
<div style="background:white;border:1px solid {MGRAY};border-radius:12px;padding:14px 18px;margin-bottom:16px">
  <div style="font-size:14px;font-weight:600;color:#0F172A;margin-bottom:4px">Attribute Importance — Adjuvant Setting vs First-Line Setting</div>
  <div style="font-size:12px;color:{DGRAY};margin-bottom:4px">
    <b>How importance is measured:</b> ATU Q3_110Z — "Rate the importance of each attribute when selecting a treatment for grade 2 IDH-mutant astrocytoma or oligodendroglioma patients in each of the settings shown." 
    [1=Not very important → 7=Extremely important]. Shown separately for Adjuvant and First-Line settings.
    Top-2 Box = rated 6 or 7 out of 7.
  </div>
  <div style="font-size:10px;color:#94A3B8">Source: ATU Q3_110Z — Adjuvant cols 0–18 (absolute cols 432–450) · First-Line cols 19–37 (absolute cols 451–469) · All {n} matched HCPs</div>
</div>
""", unsafe_allow_html=True)

        # Build importance comparison
        t2b_adj = []; t2b_fl = []; sig_flags3 = []
        rows_html = ""

        for i, attr in enumerate(ATTRS):
            adj = df[f't2b_imp_adj_{i}'].dropna(); fl = df[f't2b_imp_fl_{i}'].dropna()
            adj_r = df[f'imp_adj_{i}'].dropna(); fl_r = df[f'imp_fl_{i}'].dropna()
            t2_adj = adj.mean()*100 if len(adj)>0 else 0
            t2_fl  = fl.mean()*100  if len(fl)>0  else 0
            p, sig90, sig95 = _mw_t2b(adj_r, fl_r)
            t2b_adj.append(t2_adj); t2b_fl.append(t2_fl); sig_flags3.append((sig90,sig95))
            delta = t2_fl - t2_adj
            bg_adj, fg_adj = _cell_color(t2_adj)
            bg_fl,  fg_fl  = _cell_color(t2_fl)
            dc = GREEN if delta >= 10 else (CRIMSON if delta <= -10 else DGRAY)
            rows_html += f"""<tr style="border-bottom:1px solid {MGRAY}">
  <td style="padding:8px 10px;font-size:12px;color:#0F172A;font-weight:500">{attr}</td>
  <td style="padding:8px 10px;text-align:center"><span style="background:{bg_adj};color:{fg_adj};padding:3px 10px;border-radius:4px;font-size:12px;font-weight:700">{t2_adj:.0f}%</span></td>
  <td style="padding:8px 10px;text-align:center"><span style="background:{bg_fl};color:{fg_fl};padding:3px 10px;border-radius:4px;font-size:12px;font-weight:700">{t2_fl:.0f}%</span></td>
  <td style="padding:8px 10px;text-align:center;font-size:12px;font-weight:700;color:{dc}">{'+' if delta>0 else ''}{delta:.0f}pp</td>
  <td style="padding:8px 10px;text-align:center">{_sig_chip(p,sig90,sig95)}</td>
</tr>"""

        header = f"""<table style="width:100%;border-collapse:collapse;font-family:Inter,sans-serif">
  <thead><tr style="background:{LGRAY}">
    <th style="padding:8px 10px;text-align:left;font-size:10px;color:#64748B;font-weight:600;text-transform:uppercase;letter-spacing:.12em">Attribute</th>
    <th style="padding:8px 10px;text-align:center;font-size:10px;color:{TEAL};font-weight:700;text-transform:uppercase;letter-spacing:.12em">Adjuvant<br><span style="font-weight:400;color:#94A3B8">n={n}</span></th>
    <th style="padding:8px 10px;text-align:center;font-size:10px;color:{CRIMSON};font-weight:700;text-transform:uppercase;letter-spacing:.12em">First-Line<br><span style="font-weight:400;color:#94A3B8">n={n}</span></th>
    <th style="padding:8px 10px;text-align:center;font-size:10px;color:{DGRAY};font-weight:600;text-transform:uppercase;letter-spacing:.12em">Δ (FL−Adj)</th>
    <th style="padding:8px 10px;text-align:center;font-size:10px;color:{DGRAY};font-weight:600;text-transform:uppercase;letter-spacing:.12em">Significance</th>
  </tr></thead><tbody>{rows_html}</tbody></table>"""
        st.markdown(header, unsafe_allow_html=True)
        st.markdown(f'<div style="display:flex;gap:12px;margin-top:8px;flex-wrap:wrap;font-size:10px;color:{DGRAY}"><span><span style="background:#15803D;color:white;padding:1px 6px;border-radius:3px;font-size:9px">Green</span> ≥70% T2B</span><span><span style="background:#FEF9C3;color:#713F12;padding:1px 6px;border-radius:3px;font-size:9px">Yellow</span> 55–69%</span><span><span style="background:#FEE2E2;color:#991B1B;padding:1px 6px;border-radius:3px;font-size:9px">Red</span> &lt;55%</span></div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        # Bar chart importance
        fig3 = _bar_chart_19(t2b_adj, t2b_fl, "Adjuvant", "First-Line", n, n, sig_flags3,
                             "Attribute Importance Top-2 Box %: Adjuvant vs First-Line Setting<br><sup>ATU Q3_110Z (19 attributes, 1–7 scale, T2B = 6 or 7)</sup>")
        st.plotly_chart(fig3, use_container_width=True)

        # 10-bullet summary
        adj_bullets = _ten_bullet_summary(t2b_adj, t2b_fl, sig_flags3, "Adjuvant", "First-Line", n, n, "Importance Adjuvant vs First-Line")
        _render_summary_10(adj_bullets, "Importance — Adjuvant vs First-Line Setting")

    # ── TAB 4: VA vs No VA — Importance (Adjuvant) ────────────────────────
    with tabs[3]:
        st.markdown(f"""
<div style="background:white;border:1px solid {MGRAY};border-radius:12px;padding:14px 18px;margin-bottom:16px">
  <div style="font-size:14px;font-weight:600;color:#0F172A;margin-bottom:4px">Attribute Importance (Adjuvant Setting) — Visual Aid Used vs Not Used</div>
  <div style="font-size:12px;color:{DGRAY}">Does receiving a visual aid in the rep visit connect to different attribute importance priorities in ATU? Adjuvant setting shown.</div>
</div>
""", unsafe_allow_html=True)

        va_yes2 = df[df['any_va']==1]; va_no2 = df[df['any_va']==0]
        split_desc4 = "Visual Aid Used: PET Q1_100Z any content type = 1. No VA: all = 0. Importance measured by ATU Q3_110Z adjuvant setting, Top-2 Box."

        t2b_a4, t2b_b4, sig_flags4 = _detail_table(
            df, va_yes2, va_no2,
            "VA Used", "No VA",
            split_desc4,
            col_prefix="imp_adj_", attr_prefix="t2b_imp_adj_",
            imp_setting="Adjuvant"
        )
        bullets4 = _ten_bullet_summary(t2b_a4, t2b_b4, sig_flags4, "VA Used", "No VA", n_va, n_nva, "VA Used vs Not Used — Importance Adjuvant")
        _render_summary_10(bullets4, "Visual Aid Used vs Not Used — Importance (Adjuvant Setting)")

    # ── TAB 5: Download CSV ────────────────────────────────────────────────
    with tabs[4]:
        rows = []
        for split_name, grp_a, grp_b, la, lb, col_pref, attr_pref in [
            ("VA Used vs No VA — Performance", df[df['any_va']==1], df[df['any_va']==0], "VA Used", "No VA", "perf_", "t2b_perf_"),
            ("LTIP Top-2 vs Non — Performance", df[df['ltip_top2']==1], df[df['ltip_top2']==0], "LTIP Top-2", "LTIP Non-Top-2", "perf_", "t2b_perf_"),
            ("Importance Adjuvant vs First-Line", df, df, "Adjuvant", "First-Line", "imp_adj_", "t2b_imp_adj_"),
        ]:
            for i, attr in enumerate(ATTRS):
                if split_name.startswith("Importance"):
                    a_col = f"t2b_imp_adj_{i}"; b_col = f"t2b_imp_fl_{i}"
                    a_raw = f"imp_adj_{i}";   b_raw = f"imp_fl_{i}"
                else:
                    a_col = f"t2b_perf_{i}"; b_col = f"t2b_perf_{i}"
                    a_raw = f"perf_{i}";     b_raw = f"perf_{i}"
                a_t2 = grp_a[a_col].dropna().mean()*100 if a_col in grp_a.columns and len(grp_a[a_col].dropna())>0 else 0
                b_t2 = grp_b[b_col].dropna().mean()*100 if b_col in grp_b.columns and len(grp_b[b_col].dropna())>0 else 0
                p, sig90, sig95 = _mw_t2b(grp_a[a_raw].dropna() if a_raw in grp_a.columns else pd.Series(),
                                           grp_b[b_raw].dropna() if b_raw in grp_b.columns else pd.Series())
                rows.append({"Split": split_name, "Attribute": attr,
                             la: f"{a_t2:.0f}%", lb: f"{b_t2:.0f}%",
                             "Delta (A-B)": f"{a_t2-b_t2:+.0f}pp",
                             "p-value": p, "Sig at 90%": "Yes" if sig90 else "No",
                             "Sig at 95%": "Yes" if sig95 else "No",
                             "n(A)": len(grp_a), "n(B)": len(grp_b)})
        out_df = pd.DataFrame(rows)
        st.markdown(f'<div style="font-family:\'DM Serif Display\',serif;font-size:22px;color:#0F172A;margin-bottom:12px">Full Results — {len(out_df)} comparisons</div>', unsafe_allow_html=True)
        st.dataframe(out_df, use_container_width=True, height=600)
        st.download_button("⬇ Download full results (CSV)", data=out_df.to_csv(index=False),
                           file_name="voranigo_crosstabs.csv", mime="text/csv")
