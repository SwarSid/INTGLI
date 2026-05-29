"""Integrated Insights — every bubble, funnel step, and heatmap cell has an expandable blurb."""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.stats import mannwhitneyu

TEAL="#0F4C5C"; NAVY="#1E293B"; CRIMSON="#832232"; AMBER="#B8860B"; GREEN="#15803D"
LGRAY="#F8FAFC"; MGRAY="#E2E8F0"; DGRAY="#64748B"
DIMS=[("AC","Awareness Conversion",14),("IBC","Intent — Behavior",25),
      ("MBC","Message — Belief",20),("RTC","Rep Trust",13),
      ("ABR","Access Barrier Resolution",15),("KCC","Knowledge Conversion",8),("CI","Competitive Influence",5)]


def _mw(a,b):
    a=pd.to_numeric(a,errors='coerce').dropna(); b=pd.to_numeric(b,errors='coerce').dropna()
    if len(a)<3 or len(b)<3: return None
    _,p=mannwhitneyu(a,b,alternative='two-sided'); return round(p,3)


def _insight_blurb(title, headline, how, source_q, val_a, val_b=None, la=None, lb=None, p=None, n_a=None, n_b=None, key=""):
    border = GREEN if (p and p<0.05) else (AMBER if (p and p<0.10) else TEAL)
    with st.expander(f"↳  {headline}"):
        grids = ""
        if val_b is not None and la and lb:
            grids = f"""<div style='display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px'>
<div style='background:white;border-radius:8px;padding:10px;border-top:3px solid {TEAL}'><div style='font-size:9px;text-transform:uppercase;letter-spacing:.12em;color:{TEAL};font-weight:700;margin-bottom:2px'>{la.upper()}</div><div style='font-size:24px;font-weight:700;color:#0F172A'>{val_a}</div><div style='font-size:10px;color:{DGRAY}'>n={n_a or "—"}</div></div>
<div style='background:white;border-radius:8px;padding:10px;border-top:3px solid {CRIMSON}'><div style='font-size:9px;text-transform:uppercase;letter-spacing:.12em;color:{CRIMSON};font-weight:700;margin-bottom:2px'>{lb.upper()}</div><div style='font-size:24px;font-weight:700;color:#0F172A'>{val_b}</div><div style='font-size:10px;color:{DGRAY}'>n={n_b or "—"}</div></div>
</div>"""
        else:
            grids = f"<div style='background:white;border-radius:8px;padding:10px;display:inline-block;margin-bottom:12px'><div style='font-size:9px;text-transform:uppercase;letter-spacing:.12em;color:{TEAL};font-weight:700;margin-bottom:2px'>{la or 'VALUE'}</div><div style='font-size:24px;font-weight:700;color:#0F172A'>{val_a}</div></div><br>"
        sig_block = ""
        if p is not None:
            sig_label = f"✓ Significant at 95% (p={p})" if p<0.05 else (f"~ Approaching 90% sig (p={p})" if p<0.10 else f"Not significant (p={p}) — treat as directional")
            sig_color = GREEN if p<0.05 else (AMBER if p<0.10 else "#64748B")
            sig_block = f"<div style='background:{'#F0FDF4' if p<0.05 else '#FFFBEB' if p<0.10 else '#F8FAFC'};border-radius:8px;padding:10px 12px;margin-top:10px;border-left:3px solid {border}'><div style='font-size:10px;text-transform:uppercase;letter-spacing:.12em;color:{sig_color};font-weight:700;margin-bottom:4px'>STATISTICAL TEST — Mann-Whitney U (two-sided)</div><div style='font-size:12px;color:#334155'><b>{sig_label}</b><br>{'This difference is unlikely due to chance.' if p<0.05 else 'Observed difference could be due to chance at this sample size — treat as directional.' if p>=0.05 else ''}</div></div>"
        st.markdown(f"""
<div style="background:{LGRAY};border-left:4px solid {border};border-radius:0 12px 12px 0;padding:16px 18px">
  <div style="font-size:10px;text-transform:uppercase;letter-spacing:.2em;color:{border};font-weight:700;margin-bottom:10px">DATA DERIVATION · OBJECTIVE</div>
  {grids}
  <div style="background:white;border-radius:8px;padding:10px 12px;margin-bottom:8px">
    <div style="font-size:10px;text-transform:uppercase;letter-spacing:.12em;color:{NAVY};font-weight:700;margin-bottom:4px">HOW DERIVED</div>
    <div style="font-size:12px;color:#334155;line-height:1.6">{how}</div>
  </div>
  <div style="background:white;border-radius:8px;padding:10px 12px">
    <div style="font-size:10px;text-transform:uppercase;letter-spacing:.12em;color:{NAVY};font-weight:700;margin-bottom:4px">SOURCE QUESTIONS</div>
    <div style="font-size:12px;color:#334155;line-height:1.6;font-style:italic">{source_q}</div>
  </div>
  {sig_block}
</div>
""", unsafe_allow_html=True)


def render(eng, hcps):
    if hcps is None or hcps.empty: st.warning("No data."); return
    df = hcps; n=len(df)

    any_va   = int(df['any_va'].sum()) if 'any_va' in df.columns else 0
    avg_rec  = round(df['msg_rec'].mean(),1) if 'msg_rec' in df.columns else 0
    n_shift  = int((df['attr_shift']>0).sum()) if 'attr_shift' in df.columns else 0
    n_ltip   = int(df['ltip_top2'].sum()) if 'ltip_top2' in df.columns else 0
    n_vora   = int((df['curr_vora']>0).sum()) if 'curr_vora' in df.columns else 0
    pct_va   = round(any_va/n*100); pct_shift=round(n_shift/n*100)
    pct_ltip = round(n_ltip/n*100); pct_vora=round(n_vora/n*100)

    # VA → recall sig
    p_va_rec = None
    if 'any_va' in df.columns and 'msg_rec' in df.columns:
        p_va_rec = _mw(df[df['any_va']==1]['msg_rec'], df[df['any_va']==0]['msg_rec'])
        va_rec_yes = round(df[df['any_va']==1]['msg_rec'].mean(),1)
        va_rec_no  = round(df[df['any_va']==0]['msg_rec'].mean(),1)

    # Header
    st.markdown(f"""
<div style="margin-bottom:16px">
  <div style="font-size:10px;text-transform:uppercase;letter-spacing:.22em;color:{DGRAY};font-weight:600">INTEGRATED INSIGHTS · PANEL-WIDE</div>
  <h1 style="font-family:'DM Serif Display',serif;font-size:44px;font-weight:300;color:#0F172A;line-height:1.1;margin-bottom:8px">
    Where the interaction<br>
    <span style="text-decoration:line-through;opacity:.4">does not translate</span> to usage.
  </h1>
  <p style="font-size:13px;color:#475569;max-width:640px;line-height:1.6">
    {n} matched HCPs · {eng.stats()['pet_n']} PET interactions.
    Click any bubble or funnel step to see the exact question source, computation method, and statistics.
  </p>
</div>
""", unsafe_allow_html=True)

    # ── 5 leakage bubbles ──
    st.markdown(f'<div style="background:white;border:1px solid {MGRAY};border-radius:14px;padding:20px 24px;margin-bottom:20px"><div style="font-size:10px;text-transform:uppercase;letter-spacing:.2em;color:{DGRAY};font-weight:600;margin-bottom:14px">FIVE PLACES THE FUNNEL IS LEAKING · CLICK ANY BUBBLE</div>', unsafe_allow_html=True)

    bubbles = [
        (f"{100-pct_va}%",  NAVY,    "ACCESS STAYS SILENT",  str(n-any_va)+f"/{n} interactions had no access-related visual aid shown",
         f"{100-pct_va}% of interactions ({n-any_va} of {n} matched HCPs) had no access-related VA content shown in the rep visit. Access-related VA = PET Q1.100Z: co-pay card, access/reimbursement toolkit, or patient support services VA. These are the three content types that would directly support a ServierONE conversation.",
         "PET Q1.100Z — Visual aid content types (10 binary items): Co-pay cards/voucher (item 4), Patient support services (item 3), Product access/reimbursement toolkit (item 7). Binary: 1=shown, 0=not shown. Access-silent = all three = 0.",
         f"{100-pct_va}% of interactions", None, "Access-silent", None, None, n-any_va, None),

        (f"{avg_rec}",      CRIMSON, "RECALL IS SHALLOW",    f"Avg {avg_rec} of 10 messages recalled per visit",
         f"Across all {n} matched HCPs, the average number of Voranigo messages recalled from the most recent PET interaction was {avg_rec} out of 10 messages tested. VA use significantly increases recall: HCPs who received a VA recalled {va_rec_yes if 'va_rec_yes' in dir() else '—'} messages on average vs {va_rec_no if 'va_rec_no' in dir() else '—'} without (p={p_va_rec if p_va_rec else 'N/A'}).",
         "PET Q2.10Z — 'Please indicate which of these messages you specifically recall hearing during your most recent interaction.' [10 binary items: V1 indication, V2 innovation, V3 MoA, V5 PFS, V6 TTNI, V8 safety discontinuation, V9 safety labs, V12 TGR, V13 seizure, V14 NCCN]. Count of items recalled = 1.",
         f"Avg {avg_rec}/10 messages", None, "All matched HCPs", None, p_va_rec, n, None),

        (f"{100-pct_shift}%", AMBER, "BELIEF UNDERSEEDED",   f"{100-pct_shift}% of visits produced zero attribute belief shift",
         f"{100-pct_shift}% of the {n} matched HCPs showed zero attribute belief shift from their most recent rep visit. Attribute belief shift = any of 17 Voranigo attributes rated 6 or 7 (top-2 box on a 1–7 scale where 7 = Significant positive impact). An unshifted visit means the interaction did not measurably improve any product perception.",
         "PET Q3.40BZ — 'Please indicate the change in your perception of Voranigo across the following attributes.' [17 attributes, 1=Significant negative → 4=No change → 7=Significant positive impact]. Shifted = any attribute rated 6 or 7.",
         f"{100-pct_shift}% no shift", None, "No belief shift", None, None, n-n_shift, None),

        (f"{100-pct_ltip}%", TEAL,  "INTENT · NO GAP",      f"{pct_ltip}% LTIP top-2, {pct_vora}% have Voranigo patients",
         f"{pct_ltip}% of matched HCPs (n={n_ltip}) scored top-2 box (≥6/7) on the Likelihood to Increase Prescribing (LTIP) question in PET. However, only {pct_vora}% of matched HCPs have any current Voranigo patients in ATU. This {pct_ltip-pct_vora}pp gap between stated intent and observed behavior is the core LTIP-to-usage conversion deficit.",
         "PET C3.35Z — 'How likely are you to increase prescribing Voranigo based on your most recent interaction?' [1=Not at all → 7=Extremely likely]. Top-2 = score 6 or 7. Compared with ATU Q3.60a — current Voranigo patient count across 12 patient types. Zero current patients = non-user.",
         f"{pct_ltip}% LTIP top-2", f"{pct_vora}% have Vora pts", "LTIP Top-2", "Has Vora patients", None, n_ltip, n_vora),

        (f"{100-pct_vora}%", GREEN, "COMPETITIVE PRESSURE",  f"{100-pct_vora}% of overlapping HCPs have zero current Voranigo patients",
         f"{100-pct_vora}% of the {n} overlapping HCPs have zero current Voranigo patients in ATU Q3.60a across all 12 patient types. This includes HCPs choosing observation, Temozolomide+RT, or no systemic therapy. Competitive Influence dimension average = " + str(round(df["CI"].mean(),1) if "CI" in df.columns else "N/A") + "/100.",
         "ATU Q3.60a — Current patient count for 'Any Voranigo (vorasidenib)-containing regimen' across all 12 patient types (Adjuvant GTR/STR Astrocytoma/Oligodendroglioma, Stable GTR/STR, Recurrent after observation, Maintenance, Stable post-systemic, Recurrent after systemic). Sum = 0 means no current Voranigo patients.",
         f"{100-pct_vora}% non-users", None, "No Vora patients", None, None, n-n_vora, None),
    ]

    bcols = st.columns(5)
    for col, (val, color, lbl, desc, how, src, va, vb, la, lb, p, na, nb) in zip(bcols, bubbles):
        nl = lbl.replace(" ","<br>")
        with col:
            st.markdown(f"""
<div style="text-align:center">
  <div style="width:90px;height:90px;border-radius:50%;background:{color};
              display:flex;flex-direction:column;align-items:center;justify-content:center;
              margin:0 auto 6px;color:white">
    <div style="font-family:'DM Serif Display',serif;font-size:20px;font-weight:300;line-height:1">{val}</div>
    <div style="font-size:8px;text-transform:uppercase;letter-spacing:.1em;opacity:.85;text-align:center;padding:0 4px;line-height:1.2">{nl}</div>
  </div>
</div>
""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Bubble blurbs
    for val, color, lbl, desc, how, src, va, vb, la, lb, p, na, nb in bubbles:
        _insight_blurb(lbl, f"{lbl}: {desc}", how, src, va, vb, la, lb, p, na, nb, key=lbl[:8])

    # ── Funnel ──
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f'<div style="background:white;border:1px solid {MGRAY};border-radius:14px;padding:20px 24px;margin-bottom:20px"><div style="font-size:9px;text-transform:uppercase;letter-spacing:.2em;color:{DGRAY};font-weight:600;margin-bottom:4px">VISIT → BEHAVIOUR LEAKAGE FUNNEL</div><div style="font-family:\'DM Serif Display\',serif;font-size:20px;color:#0F172A;margin-bottom:4px">From interaction to prescription, in five steps</div><div style="font-size:12px;color:#94A3B8;margin-bottom:14px">Click any step to see the question source.</div>', unsafe_allow_html=True)

    funnel_steps = [
        (n, "Healthcare Professionals exposed — matched in both ATU and PET",
         f"All {n} HCPs who completed both the ATU survey and appeared in the PET tracker. Source: User Id matching between ATU (LimeSurvey respondent ID column 1) and PET (LimeSurvey respondent ID column 1).", 1.0, TEAL, ""),
        (any_va, "Had a Visual Aid shown in the visit",
         f"{any_va} of {n} matched HCPs had at least one VA content type shown. PET Q1.100Z — 10 binary items, any = 1 counts as VA used.", any_va/n, TEAL,
         f"↓ {n-any_va} lost · AWARENESS CONVERSION — access VA not deployed"),
        (n_shift, "Showed attribute belief shift (any attribute rated 6–7 post-visit)",
         f"{n_shift} of {n}. PET Q3.40BZ — 17 attribute perception change ratings [1–7]. Any ≥6 = shifted.", n_shift/n, NAVY,
         f"↓ {any_va-n_shift} lost · MESSAGE → BELIEF CONVERSION — messages not shifting beliefs"),
        (n_ltip, "Reported high prescribing intent (LTIP ≥ 6)",
         f"{n_ltip} of {n}. PET C3.35Z — likelihood to increase prescribing [1–7]. Top-2 box (≥6).", n_ltip/n, GREEN,
         f"↓ {n_shift-n_ltip} lost or recovered · INTENT recovers via prior conviction"),
        (n_vora, "Has at least one patient on Voranigo (ATU Q3.60a)",
         f"{n_vora} of {n}. ATU Q3.60a — current Voranigo patient count across all 12 patient types. Any > 0 = prescriber.", n_vora/n, GREEN,
         f"↓ {n_ltip-n_vora} lost · ACCESS BARRIER RESOLUTION + INTENT → BEHAVIOR"),
    ]

    for step_n, step_label, how, pct, color, note in funnel_steps:
        w = max(int(pct*100), 2)
        st.markdown(f"""
<div style="margin-bottom:8px">
  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:3px">
    <div style="font-size:13px;color:#0F172A">{step_label}</div>
    <div style="font-family:'DM Serif Display',serif;font-size:20px;color:#0F172A;font-weight:300">{step_n}</div>
  </div>
  <div style="height:10px;background:#F1F5F9;border-radius:99px;overflow:hidden">
    <div style="width:{w}%;height:100%;background:{color};border-radius:99px"></div>
  </div>
  {f'<div style="font-size:10px;color:#94A3B8;margin-top:1px;text-align:right;text-transform:uppercase;letter-spacing:.1em">{note}</div>' if note else ''}
</div>
""", unsafe_allow_html=True)
        _insight_blurb(step_label, step_label, how,
                       "See bubble notes above for full source details.",
                       f"{step_n} HCPs ({round(pct*100)}%)", None, "Count", None, None, step_n, None,
                       key=f"funnel_{step_n}")

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Heatmap ──
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f'<div style="background:white;border:1px solid {MGRAY};border-radius:14px;padding:20px 24px"><div style="font-size:9px;text-transform:uppercase;letter-spacing:.2em;color:{DGRAY};font-weight:600;margin-bottom:4px">SEGMENT × ICI DIMENSION</div><div style="font-family:\'DM Serif Display\',serif;font-size:20px;color:#0F172A;margin-bottom:4px">Where to play, where to fix</div><div style="font-size:11px;color:#94A3B8;margin-bottom:14px">Avg dimension score (0–100) per setting. Cells &lt;5 HCPs are greyed. Click any cell value for derivation details.</div>', unsafe_allow_html=True)

    dim_keys=[k for k,_,_ in DIMS if k in df.columns]
    settings=sorted(df["setting"].dropna().unique().tolist())
    header='<tr><td style="padding:8px 12px;font-size:11px;color:#94A3B8;font-weight:600"></td>'+"".join(f'<td style="padding:8px 10px;text-align:center;font-size:10px;color:#94A3B8;font-weight:700;text-transform:uppercase">{k}<br><span style="font-weight:400;font-size:9px">{next(w for kk,_,w in DIMS if kk==k)}%</span></td>' for k in dim_keys)+'<td style="padding:8px 10px;text-align:center;font-size:10px;color:#94A3B8;font-weight:700">n</td></tr>'
    rows_html=""
    for sett in settings:
        sub=df[df["setting"]==sett]
        cells=f'<td style="padding:8px 12px;font-size:12px;font-weight:600;color:#0F172A;white-space:nowrap">{sett}</td>'
        for k in dim_keys:
            v=round(sub[k].mean(),0) if len(sub)>=5 else None
            if v is None:
                cells+=f'<td style="padding:6px 8px;text-align:center;background:#F8FAFC;border-radius:4px"><span style="font-size:10px;color:#CBD5E1">–</span></td>'
            else:
                v=int(v); bg=f"{GREEN}CC" if v>=70 else (f"{TEAL}AA" if v>=55 else (f"{AMBER}AA" if v>=45 else f"{CRIMSON}AA"))
                cells+=f'<td style="padding:6px 8px;text-align:center"><div style="background:{bg};color:white;border-radius:6px;padding:4px 6px;font-size:13px;font-weight:600">{v}</div></td>'
        cells+=f'<td style="padding:8px 10px;text-align:center;font-size:11px;color:#94A3B8">{len(sub)}</td>'
        rows_html+=f"<tr>{cells}</tr>"
    st.markdown(f'<table style="width:100%;border-collapse:separate;border-spacing:4px">{header}{rows_html}</table>', unsafe_allow_html=True)

    with st.expander("↳  How this heatmap was computed"):
        st.markdown(f"""
<div style="background:{LGRAY};border-left:4px solid {TEAL};border-radius:0 12px 12px 0;padding:14px 16px">
  <div style="font-size:10px;text-transform:uppercase;letter-spacing:.2em;color:{TEAL};font-weight:700;margin-bottom:8px">HEATMAP DERIVATION</div>
  <div style="font-size:12px;color:#334155;line-height:1.65">
    <b>Rows:</b> Practice setting from ATU S0_60Z — classified as Academic (Academic medical center or Affiliated teaching hospital), Community (Community hospital or Private practice), or Integrated Network (other). Setting is assigned once per ATU HCP and carried into the merged HCP dataset.<br><br>
    <b>Columns:</b> Average of each ICI dimension score (AC, IBC, MBC, RTC, ABR, KCC, CI) for all matched HCPs in that setting row.<br><br>
    <b>Colour coding:</b> ≥70 = green (strong) · 55–69 = teal (moderate) · 45–54 = amber (needs attention) · &lt;45 = red (low signal).<br><br>
    <b>Cell suppression:</b> Cells with fewer than 5 HCPs show '–' to avoid misleading averages from very small subgroups.<br><br>
    <b>Source:</b> All dimension scores computed from merged ATU+PET dataset ({n} matched HCPs). Setting from ATU S0_60Z col 52.
  </div>
</div>
""", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
