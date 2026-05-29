"""Overview — every insight statement has an expandable data-derivation blurb."""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.stats import mannwhitneyu

TEAL="#0F4C5C"; NAVY="#1E293B"; CRIMSON="#832232"; AMBER="#B8860B"; GREEN="#15803D"
LGRAY="#F8FAFC"; MGRAY="#E2E8F0"; DGRAY="#64748B"

DIMS=[("AC","Awareness Conversion",14),("IBC","Intent — Behavior",25),
      ("MBC","Message — Belief",20),("RTC","Rep Trust",13),
      ("ABR","Access Barrier Resolution",15),("KCC","Knowledge Conversion",8),
      ("CI","Competitive Influence",5)]

DIM_EVIDENCE={
    "AC":("PET Q2.10Z — 'Which of these messages do you specifically recall hearing?' [10 binary items, 1=recalled] · ATU Q2.20Z (Voranigo row) — 'How familiar are you with Voranigo?' [1=Never heard → 5=Have used] · ATU Q2.10Z — unaided treatment recall voice response (binary: does Voranigo appear?)",
          "AC = (message recall rate × 0.35) + (Voranigo familiarity, normalised 0–100, × 0.35) + (unaided mention binary × 0.20) + (topic breadth PET Q1.110Z × 0.10). All inputs normalised (raw − min) ÷ (max − min) × 100 before weighting."),
    "IBC":("PET C3.35Z — 'How likely are you to increase prescribing Voranigo based on your most recent interaction?' [1=Not at all → 7=Extremely likely] · ATU Q3.60a — current Voranigo patient count across 12 patient types · ATU Q3.60b — Voranigo allocation in next 10 patients",
           "IBC = (LTIP normalised × 0.30) + (current patient share normalised × 0.35) + (LTIP-usage alignment flag × 0.20) + (future intent ÷ 10 × 0.15). Alignment flag: LTIP≥5 + usage>0 = 1.0; LTIP≥5 + zero usage = 0 (conversion failure); LTIP<5 + zero usage = 0.5; LTIP<5 + usage>0 = 0.75."),
    "MBC":("PET Q2.10Z — message recall (10 items) · PET Q5.00Z — believability rating per message [1–7] · ATU Q3.120Z Voranigo column — attribute performance ratings [1–7, 19 attributes] · ATU Q3.110Z — attribute importance ratings [1–7, used for importance-performance gap]",
           "MBC = (priority message recall rate × 0.25) + (avg Voranigo attr performance × 0.35) + (message-belief alignment × 0.25) + (avg believability × 0.15). VA reinforcement (channel match, content relevance from PET Q1.100Z) contributes 20% to the attr performance sub-score."),
    "RTC":("PET Q3.70Z — call quality, preparedness, organisation, indication knowledge, time use [1–7, 5 items] · PET Q6.20Z — trusted partner, best in class, meaningful discussion, trusted source, listens [1–7, 5 items] · ATU Q4.30Z — in-person or virtual rep discussion selected as preferred information source [binary]",
           "RTC = (avg call quality Q3.70Z × 0.30) + (avg trusted partner Q6.20Z × 0.35) + (rep preferred source ATU Q4.30Z × 0.25) + (peer sharing PET C3.25Z × 0.10). All inputs normalised 0–100."),
    "ABR":("PET Q1.100Z — access-specific VA content shown: co-pay card, access toolkit, patient support VA [3 binary items, cap applied if none shown] · ATU Q3.260A — ServierONE familiarity [1–5] · ATU Q3.260B — ServierONE programmes known [0–5 count] · ATU Q3.220Z — barriers cited [0–9 count, inverted]",
           "ABR = (ServierONE programme awareness PET × 0.20) + (ServierONE familiarity ATU × 0.25) + (barrier resolution, inverted: 1 − barriers÷9, × 0.30) + (ServierONE effectiveness × 0.25). Cap at 35 if access VA absent AND access topic not discussed (PET Q1.110Z)."),
    "KCC":("PET Q1.16Z — DSE value rating [1–7] · PET Q3.45Z — WHO classification confidence post-interaction [1–7] · ATU Q4.00Z — clinical belief alignment [8 statements, 1–7, avg] · ATU Q1.00Z — NGS testing rate [% using NGS ÷ 100] · ATU Q2.00Z — NCCN guideline familiarity [1–5]",
           "KCC = (DSE value × 0.20) + (WHO confidence × 0.20) + (belief alignment × 0.35) + (NCCN familiarity × 0.15) + (NGS rate × 0.10). All normalised 0–100."),
    "CI":("ATU Q3.120Z — Voranigo vs Temozolomide+RT performance on HCP's highest-importance attributes [importance-weighted gap] · ATU Q2.20Z — IDH-class competitor familiarity (ivosidenib, olutasidenib) [1–5] · ATU Q3.160Z qual — clinical superiority vs uniqueness framing [coded via keyword matching]",
          "CI = (importance-weighted performance gap Vora vs best competitor × 0.50) + (IDH competitor familiarity, inverted × 0.30) + (clinical framing in qual: superiority=1, uniqueness=0.5, absent=0 × 0.20). Lower CI = harder competitive environment for this HCP."),
}

CLUSTER_NAMES={1:"Patient ID Priority",2:"Intent-Led, Access-Pending",
               3:"Evidence Gap",4:"Narrative-Building Opportunity",5:"Conviction-Led Prescriber"}
CLUSTER_COLORS={1:TEAL,2:NAVY,3:CRIMSON,4:AMBER,5:GREEN}
CLUSTER_TRIGGERS={
    1:"Low Grade 2 IDH-mutant patient load (≤2) OR Voranigo familiarity <3/5 — practice mismatch or pure awareness gap. Source: ATU S0_120Z (patient count) + ATU Q2.20Z (familiarity).",
    2:"Intent-to-Behavior Conversion dimension score reflects high LTIP but low Access Barrier Resolution, OR access not discussed in PET visit. Source: PET C3.35Z (LTIP) + PET Q1.110Z (access topic) + ATU Q3.220Z (barriers) + ATU Q3.260B (ServierONE progs).",
    3:"Importance-performance gap: attribute importance ≥6/7 in ATU AND Voranigo performance ≤4/7 on that attribute, AND the corrective message not recalled in PET. Source: ATU Q3.110Z (importance) + ATU Q3.120Z (Voranigo perf) + PET Q2.10Z (recall).",
    4:"Current prescribing exists but ATU qual voice contains uniqueness framing AND IDH-class competitor familiarity ≥4/5. Source: ATU Q3.160Z qual (keyword: 'only approved') + ATU Q2.20Z (ivosidenib/olutasidenib fam).",
    5:"All upstream gates cleared: adequate patient load, access barriers low, clinical evidence gap absent, competitive narrative established. IBC, MBC, RTC all moderate-to-high.",
}


def _blurb_dim(key, val, n, q25, q75, n_low):
    """Expandable blurb for each ICI dimension bar."""
    q_src, how = DIM_EVIDENCE[key]
    border = CRIMSON if val < 45 else (AMBER if val < 55 else GREEN)
    with st.expander(f"↳  {key} = {val}/100 — how this score was computed"):
        st.markdown(f"""
<div style="background:{LGRAY};border-left:4px solid {border};border-radius:0 12px 12px 0;padding:16px 18px">
  <div style="font-size:10px;text-transform:uppercase;letter-spacing:.2em;color:{border};font-weight:700;margin-bottom:10px">
    DATA DERIVATION · {key} · {next(nm for k,nm,_ in DIMS if k==key)} ({next(w for k,_,w in DIMS if k==key)}% of ICI)
  </div>
  <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:14px">
    <div style="background:white;border-radius:8px;padding:10px;text-align:center">
      <div style="font-size:9px;color:#94A3B8;text-transform:uppercase;letter-spacing:.12em;margin-bottom:2px">Panel avg</div>
      <div style="font-size:22px;font-weight:700;color:#0F172A">{val}</div>
    </div>
    <div style="background:white;border-radius:8px;padding:10px;text-align:center">
      <div style="font-size:9px;color:#94A3B8;text-transform:uppercase;letter-spacing:.12em;margin-bottom:2px">Q25–Q75</div>
      <div style="font-size:18px;font-weight:700;color:#0F172A">{q25}–{q75}</div>
    </div>
    <div style="background:white;border-radius:8px;padding:10px;text-align:center">
      <div style="font-size:9px;color:#94A3B8;text-transform:uppercase;letter-spacing:.12em;margin-bottom:2px">n HCPs</div>
      <div style="font-size:22px;font-weight:700;color:#0F172A">{n}</div>
    </div>
    <div style="background:{'#FEE2E2' if n_low > n//3 else '#F0FDF4'};border-radius:8px;padding:10px;text-align:center">
      <div style="font-size:9px;color:#94A3B8;text-transform:uppercase;letter-spacing:.12em;margin-bottom:2px">Score &lt;45</div>
      <div style="font-size:22px;font-weight:700;color:{'#991B1B' if n_low > n//3 else '#15803D'}">{n_low}</div>
    </div>
  </div>
  <div style="background:white;border-radius:8px;padding:12px 14px;margin-bottom:10px">
    <div style="font-size:10px;text-transform:uppercase;letter-spacing:.15em;color:{NAVY};font-weight:700;margin-bottom:6px">HOW THE SCORE IS COMPUTED</div>
    <div style="font-size:12px;color:#334155;line-height:1.65">{how}</div>
  </div>
  <div style="background:white;border-radius:8px;padding:12px 14px">
    <div style="font-size:10px;text-transform:uppercase;letter-spacing:.15em;color:{NAVY};font-weight:700;margin-bottom:6px">SOURCE QUESTIONS</div>
    <div style="font-size:12px;color:#334155;line-height:1.65;font-style:italic">{q_src}</div>
  </div>
</div>
""", unsafe_allow_html=True)


def _blurb_cluster(cid, cname, n_c, avg_ici, color):
    trigger = CLUSTER_TRIGGERS.get(cid, "")
    with st.expander(f"↳  {cname} (n={n_c}) — how HCPs are assigned here"):
        st.markdown(f"""
<div style="background:{LGRAY};border-left:4px solid {color};border-radius:0 12px 12px 0;padding:16px 18px">
  <div style="font-size:10px;text-transform:uppercase;letter-spacing:.2em;color:{color};font-weight:700;margin-bottom:10px">CLUSTER ASSIGNMENT LOGIC · SEQUENTIAL RESOLUTION TREE</div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:14px">
    <div style="background:white;border-radius:8px;padding:10px;text-align:center">
      <div style="font-size:9px;color:#94A3B8;text-transform:uppercase;letter-spacing:.12em;margin-bottom:2px">HCPs in cluster</div>
      <div style="font-size:26px;font-weight:700;color:#0F172A">{n_c}</div>
    </div>
    <div style="background:white;border-radius:8px;padding:10px;text-align:center">
      <div style="font-size:9px;color:#94A3B8;text-transform:uppercase;letter-spacing:.12em;margin-bottom:2px">Avg ICI score</div>
      <div style="font-size:26px;font-weight:700;color:#0F172A">{avg_ici}/100</div>
    </div>
  </div>
  <div style="background:white;border-radius:8px;padding:12px 14px;margin-bottom:10px">
    <div style="font-size:10px;text-transform:uppercase;letter-spacing:.15em;color:{NAVY};font-weight:700;margin-bottom:6px">TRIGGER CONDITIONS (must all be met)</div>
    <div style="font-size:12px;color:#334155;line-height:1.65">{trigger}</div>
  </div>
  <div style="background:white;border-radius:8px;padding:12px 14px">
    <div style="font-size:10px;text-transform:uppercase;letter-spacing:.15em;color:{NAVY};font-weight:700;margin-bottom:6px">SEQUENTIAL RESOLUTION PRINCIPLE</div>
    <div style="font-size:12px;color:#334155;line-height:1.65">
      Clustering is rule-based and sequential — not k-means. Each HCP walks a decision tree.
      The first blocker that fires wins. This cluster is position {cid} in the tree, meaning
      all upstream conditions (clusters 1–{cid-1}) were checked and did not trigger first.
      If two conditions both fire, the earlier cluster takes precedence (Option C: resolve the
      blocker that must come first, not the strongest one).
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


def render(eng, hcps):
    if hcps is None or hcps.empty: st.warning("No data loaded."); return
    df = hcps
    n=len(df); n_pet=eng.stats()["pet_n"]; avg_ici=round(df["ICI"].mean(),1)
    counts={cid:int((df["cluster"]==cid).sum()) for cid in range(1,6)}
    dim_avgs={k:round(df[k].mean(),1) for k,_,_ in DIMS if k in df.columns}
    dim_q25 ={k:round(df[k].quantile(.25),1) for k,_,_ in DIMS if k in df.columns}
    dim_q75 ={k:round(df[k].quantile(.75),1) for k,_,_ in DIMS if k in df.columns}
    dim_nlow={k:int((df[k]<45).sum()) for k,_,_ in DIMS if k in df.columns}
    weakest=min(dim_avgs,key=dim_avgs.get)

    st.markdown(f'<div style="font-size:10px;text-transform:uppercase;letter-spacing:.22em;color:{DGRAY};font-weight:600">OVERVIEW</div>', unsafe_allow_html=True)
    st.markdown(f"""
<h1 style="font-family:'DM Serif Display',serif;font-size:48px;font-weight:300;color:#0F172A;line-height:1.05;margin-bottom:10px">
  {n} doctors. {n_pet} interactions.<br><span style="color:{TEAL}">One conversion story.</span>
</h1>
<p style="font-size:14px;color:#475569;max-width:640px;line-height:1.65;margin-bottom:6px">
  Every Healthcare Professional completed both the Awareness Trial Usage (ATU) survey
  and was exposed to the Promotional Effectiveness Tracker (PET), then unified through the
  Interaction Conversion Index (ICI). Click any insight below to see exactly how it was derived.
</p>
""", unsafe_allow_html=True)

    c1,c2,c3,c4=st.columns(4)
    with c1: st.markdown(f'<div class="mcard"><div class="mlabel">HEALTHCARE PROFESSIONALS</div><div class="mval">{n}</div><div class="msub">Completed both surveys</div></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="mcard"><div class="mlabel">INTERACTIONS LOGGED</div><div class="mval">{n_pet}</div><div class="msub">Promotional Effectiveness Tracker</div></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="mcard"><div class="mlabel">AVG ICI SCORE</div><div class="mval">{avg_ici}<span style="font-size:20px;color:#94A3B8">/100</span></div><div class="msub">7-dimension weighted index</div></div>', unsafe_allow_html=True)
    with c4: st.markdown(f'<div class="acard"><div class="mlabel">LARGEST LEAK</div><div style="font-family:\'DM Serif Display\',serif;font-size:20px;color:white;line-height:1.2;margin:6px 0">{weakest} = {dim_avgs[weakest]}</div><div style="font-size:12px;color:rgba(255,255,255,.6)">Lowest avg ICI dimension</div></div>', unsafe_allow_html=True)

    # Avg ICI blurb
    with st.expander(f"↳  Avg ICI = {avg_ici}/100 — how the overall score is computed"):
        st.markdown(f"""
<div style="background:{LGRAY};border-left:4px solid {TEAL};border-radius:0 12px 12px 0;padding:16px 18px">
  <div style="font-size:10px;text-transform:uppercase;letter-spacing:.2em;color:{TEAL};font-weight:700;margin-bottom:10px">ICI FORMULA · WEIGHTED COMPOSITE OF 7 DIMENSIONS</div>
  <div style="background:white;border-radius:8px;padding:12px 14px;margin-bottom:10px;font-family:monospace;font-size:13px;line-height:2;color:#0F172A">
    ICI = (Awareness Conversion × 0.14)<br>
    + (Intent → Behavior × 0.25)<br>
    + (Message → Belief × 0.20)<br>
    + (Rep Trust × 0.13)<br>
    + (Access Barrier Resolution × 0.15)<br>
    + (Knowledge Conversion × 0.08)<br>
    + (Competitive Influence × 0.05)
  </div>
  <div style="background:white;border-radius:8px;padding:12px 14px">
    <div style="font-size:10px;text-transform:uppercase;letter-spacing:.15em;color:{NAVY};font-weight:700;margin-bottom:6px">WEIGHT RATIONALE</div>
    <div style="font-size:12px;color:#334155;line-height:1.65">
      Weights reflect proximity to prescribing behavior: Intent→Behavior (25%) is the outcome dimension — it directly measures whether prescribing happened.
      Message→Belief (20%) and Access Barrier Resolution (15%) are the two most actionable levers — they can be changed in a single rep call.
      Awareness (14%) and Rep Trust (13%) are foundational but slower to move. Knowledge (8%) and Competitive Influence (5%) are contextual modifiers.
      Visual Aid quality is embedded within Message→Belief and Access Barrier Resolution, not a separate dimension.
      All dimension scores are normalised 0–100 before weighting using (raw − min) ÷ (max − min) × 100.
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    lc,rc=st.columns([3,2])

    with lc:
        st.markdown(f'<div style="background:white;border:1px solid {MGRAY};border-radius:16px;padding:22px 24px"><div style="font-size:9px;text-transform:uppercase;letter-spacing:.2em;color:{DGRAY};font-weight:600;margin-bottom:2px">ICI DIMENSION HEALTH</div><div style="font-family:\'DM Serif Display\',serif;font-size:18px;color:#0F172A;margin-bottom:3px">Where the interaction works — and where it leaks</div><div style="font-size:11px;color:#94A3B8;margin-bottom:16px">Avg score 0–100 · Weight in parentheses · Click any dimension for full derivation.</div>', unsafe_allow_html=True)
        for key,name,weight in DIMS:
            if key not in df.columns: continue
            val=round(df[key].mean(),1)
            fill=GREEN if val>=70 else TEAL if val>=50 else CRIMSON
            flag="⚠ LOW SIGNAL" if val<45 else ("↗ SUSTAINED" if val>=65 else "")
            st.markdown(f'<div style="display:flex;align-items:center;gap:12px;margin-bottom:4px"><div style="width:200px;flex-shrink:0"><div style="font-size:12px;font-weight:500;color:#0F172A">{name} <span style="color:#CBD5E1">({key})</span></div><div style="font-size:9px;color:#CBD5E1;text-transform:uppercase;letter-spacing:.12em">{weight}% {flag}</div></div><div style="flex:1;height:8px;background:#F1F5F9;border-radius:99px;overflow:hidden"><div style="width:{val}%;height:100%;background:{fill};border-radius:99px"></div></div><div style="width:32px;text-align:right;font-family:\'DM Serif Display\',serif;font-size:18px;color:#0F172A">{val}</div></div>', unsafe_allow_html=True)
            _blurb_dim(key, val, n, dim_q25[key], dim_q75[key], dim_nlow[key])
        st.markdown("</div>", unsafe_allow_html=True)

    with rc:
        st.markdown(f'<div style="background:white;border:1px solid {MGRAY};border-radius:16px;padding:22px 24px"><div style="font-size:9px;text-transform:uppercase;letter-spacing:.2em;color:{DGRAY};font-weight:600;margin-bottom:2px">ENGAGEMENT STATE MIX</div><div style="font-family:\'DM Serif Display\',serif;font-size:18px;color:#0F172A;margin-bottom:4px">Healthcare Professionals per state</div><div style="font-size:11px;color:#94A3B8;margin-bottom:14px">Click any cluster to see its assignment logic.</div>', unsafe_allow_html=True)
        fig=go.Figure()
        for cid in range(1,6):
            n_c=counts.get(cid,0)
            if n_c==0: continue
            fig.add_trace(go.Bar(x=[n_c],y=[CLUSTER_NAMES[cid]],orientation="h",
                                  marker_color=CLUSTER_COLORS[cid],
                                  text=[str(n_c)],textposition="outside",name=CLUSTER_NAMES[cid]))
        fig.update_layout(height=260,showlegend=False,plot_bgcolor="white",paper_bgcolor="white",
                          font=dict(family="Inter",size=11),barmode="group",
                          xaxis=dict(showticklabels=False,showgrid=False,zeroline=False),
                          margin=dict(l=0,r=40,t=0,b=0))
        st.plotly_chart(fig,use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        # Cluster blurbs
        for cid in range(1,6):
            n_c=counts.get(cid,0)
            if n_c==0: continue
            sub=df[df['cluster']==cid]
            avg_ici_c=round(sub['ICI'].mean(),1) if len(sub)>0 else 0
            _blurb_cluster(cid, CLUSTER_NAMES[cid], n_c, avg_ici_c, CLUSTER_COLORS[cid])

    st.markdown("<br>", unsafe_allow_html=True)
    t1,t2=st.columns(2)
    with t1:
        st.markdown(f'<div style="background:white;border:1px solid {MGRAY};border-radius:14px;padding:20px 22px"><div style="font-size:9px;text-transform:uppercase;letter-spacing:.2em;color:{TEAL};font-weight:700;margin-bottom:6px">⚡ INTEGRATED INSIGHTS</div><div style="font-family:\'DM Serif Display\',serif;font-size:18px;color:#0F172A;margin-bottom:8px">Where the interaction does not translate to usage</div><div style="font-size:12px;color:{DGRAY};line-height:1.5;margin-bottom:12px">Five leakage bubbles, the visit-to-prescription funnel, and the segment × dimension heatmap.</div></div>', unsafe_allow_html=True)
        if st.button("Open Integrated Insights →", key="open_ii"): st.session_state["view"]="integrated"; st.rerun()
    with t2:
        st.markdown(f'<div style="background:white;border:1px solid {MGMT};border-radius:14px;padding:20px 22px"><div style="font-size:9px;text-transform:uppercase;letter-spacing:.2em;color:{CRIMSON};font-weight:700;margin-bottom:6px">🎤 QUALITATIVE ANALYSIS</div><div style="font-family:\'DM Serif Display\',serif;font-size:18px;color:#0F172A;margin-bottom:8px">What doctors are actually saying</div><div style="font-size:12px;color:{DGRAY};line-height:1.5;margin-bottom:12px">All ATU + PET voice responses. Doctor-only transcripts for AI interviews.</div></div>', unsafe_allow_html=True)
        if st.button("Open Qualitative Analysis →", key="open_qa"): st.session_state["view"]="qualitative"; st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f'<div style="background:{NAVY};border-radius:16px;padding:24px 32px"><div style="font-size:10px;text-transform:uppercase;letter-spacing:.2em;color:rgba(255,255,255,.5);font-weight:600;margin-bottom:6px">FOR THE FIELD TEAM</div><div style="font-family:\'DM Serif Display\',serif;font-size:24px;font-weight:300;color:white;margin-bottom:4px">Generate a custom doctor rep support card for any profile.</div><div style="font-size:13px;color:rgba(255,255,255,.6)">Pick specialty, setting, and target type. Every recommendation is derived from the integrated data.</div></div>', unsafe_allow_html=True)
    if st.button("Open the Custom Rep Support Card →", key="cta_env_ov"): st.session_state["view"]="envelope"; st.rerun()

MGMT = MGRAY  # alias
