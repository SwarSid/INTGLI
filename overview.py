"""Overview view — matches Emergent image 2. 100% data-driven."""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

TEAL="#0F4C5C"; NAVY="#1E293B"; CRIMSON="#832232"; AMBER="#B8860B"; GREEN="#15803D"
LGRAY="#F8FAFC"; MGRAY="#E2E8F0"; DGRAY="#64748B"
DIMS=[("AC","Awareness Conversion",14),("IBC","Intent — Behavior",25),
      ("MBC","Message — Belief",20),("RTC","Rep Trust",13),
      ("ABR","Access Barrier Resolution",15),("KCC","Knowledge Conversion",8),("CI","Competitive Influence",5)]
CLUSTER_COLORS={1:TEAL,2:NAVY,3:CRIMSON,4:AMBER,5:GREEN}
CLUSTER_NAMES={1:"Patient ID Priority",2:"Access Pending",3:"Evidence Gap",4:"Narrative Build",5:"Conviction-Led"}

def render(eng, hcps):
    if hcps is None or hcps.empty: st.warning("No data loaded."); return
    df = hcps
    n_hcps=len(df); n_pet=eng.stats()["pet_n"]; avg_ici=round(df["ICI"].mean(),1)
    counts={cid:int((df["cluster"]==cid).sum()) for cid in range(1,6)}
    dim_avgs={k:round(df[k].mean(),1) for k,_,_ in DIMS if k in df.columns}
    weakest=min(dim_avgs,key=dim_avgs.get); weakest_val=dim_avgs[weakest]
    largest=max(counts,key=counts.get); largest_pct=round(counts[largest]/n_hcps*100)

    st.markdown(f'<div style="font-size:10px;text-transform:uppercase;letter-spacing:.22em;color:{DGRAY};font-weight:600">OVERVIEW</div>', unsafe_allow_html=True)
    st.markdown(f"""
<h1 style="font-family:'DM Serif Display',serif;font-size:48px;font-weight:300;color:#0F172A;line-height:1.05;margin-bottom:10px">
  {n_hcps} doctors. {n_pet} interactions.<br><span style="color:{TEAL}">One conversion story.</span>
</h1>
<p style="font-size:14px;color:#475569;max-width:640px;line-height:1.65;margin-bottom:28px">
  Every Healthcare Professional completed both the Awareness Trial Usage (ATU) survey
  and was exposed to the Promotional Effectiveness Tracker (PET), then unified through the
  Interaction Conversion Index (ICI).
</p>""", unsafe_allow_html=True)

    c1,c2,c3,c4=st.columns(4)
    with c1: st.markdown(f'<div class="mcard"><div class="mlabel">HEALTHCARE PROFESSIONALS</div><div class="mval">{n_hcps}</div><div class="msub">Completed both surveys</div></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="mcard"><div class="mlabel">INTERACTIONS LOGGED</div><div class="mval">{n_pet}</div><div class="msub">Promotional Effectiveness Tracker</div></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="mcard"><div class="mlabel">AVG ICI SCORE</div><div class="mval">{avg_ici}<span style="font-size:20px;color:#94A3B8">/100</span></div><div class="msub">7-dimension weighted</div></div>', unsafe_allow_html=True)
    with c4: st.markdown(f'<div class="acard"><div class="mlabel">LARGEST LEAK</div><div style="font-family:\'DM Serif Display\',serif;font-size:20px;color:white;line-height:1.2;margin:6px 0">{weakest} stays silent</div><div style="font-size:12px;color:rgba(255,255,255,.6)">{largest_pct}% of interactions never raise it</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    t1,t2=st.columns(2)
    with t1:
        st.markdown(f'<div style="background:white;border:1px solid {MGRAY};border-radius:14px;padding:20px 22px"><div style="font-size:9px;text-transform:uppercase;letter-spacing:.2em;color:{TEAL};font-weight:700;margin-bottom:6px">⚡ INTEGRATED INSIGHTS</div><div style="font-family:\'DM Serif Display\',serif;font-size:18px;color:#0F172A;margin-bottom:8px">Where the interaction does not translate to usage</div><div style="font-size:12px;color:{DGRAY};line-height:1.5;margin-bottom:12px">Five problem-area bricks, the visit-to-prescription leakage funnel, and the segment × dimension heatmap.</div></div>', unsafe_allow_html=True)
        if st.button("Open Integrated Insights →", key="open_ii"): st.session_state["view"]="integrated"; st.rerun()
    with t2:
        st.markdown(f'<div style="background:white;border:1px solid {MGRAY};border-radius:14px;padding:20px 22px"><div style="font-size:9px;text-transform:uppercase;letter-spacing:.2em;color:{CRIMSON};font-weight:700;margin-bottom:6px">🎤 QUALITATIVE ANALYSIS</div><div style="font-family:\'DM Serif Display\',serif;font-size:18px;color:#0F172A;margin-bottom:8px">What {n_hcps} doctors are actually saying</div><div style="font-size:12px;color:{DGRAY};line-height:1.5;margin-bottom:12px">Theme bubbles by sentiment and prescribing intent, the LTIP chart, and a quote wall from the data.</div></div>', unsafe_allow_html=True)
        if st.button("Open Qualitative Analysis →", key="open_qa"): st.session_state["view"]="qualitative"; st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    lc,rc=st.columns([3,2])
    with lc:
        st.markdown(f'<div style="background:white;border:1px solid {MGRAY};border-radius:16px;padding:22px 24px"><div style="font-size:9px;text-transform:uppercase;letter-spacing:.2em;color:{DGRAY};font-weight:600;margin-bottom:2px">ICI DIMENSION HEALTH</div><div style="font-family:\'DM Serif Display\',serif;font-size:18px;color:#0F172A;margin-bottom:3px">Where the interaction works — and where it leaks</div><div style="font-size:11px;color:#94A3B8;margin-bottom:16px">Average score (0–100). Weight shown in parentheses.</div>', unsafe_allow_html=True)
        for key,name,weight in DIMS:
            if key not in df.columns: continue
            val=round(df[key].mean(),1)
            fill=GREEN if val>=70 else TEAL if val>=50 else CRIMSON
            flag="⚠ LOW SIGNAL" if val<45 else ("↗ SUSTAINED" if val>=65 else "")
            st.markdown(f'<div style="display:flex;align-items:center;gap:12px;margin-bottom:12px"><div style="width:200px;flex-shrink:0"><div style="font-size:12px;font-weight:500;color:#0F172A">{name} <span style="color:#CBD5E1">({key})</span></div><div style="font-size:9px;color:#CBD5E1;text-transform:uppercase;letter-spacing:.12em">{weight}% weight {flag}</div></div><div style="flex:1;height:8px;background:#F1F5F9;border-radius:99px;overflow:hidden"><div style="width:{val}%;height:100%;background:{fill};border-radius:99px"></div></div><div style="width:32px;text-align:right;font-family:\'DM Serif Display\',serif;font-size:18px;color:#0F172A">{val}</div></div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with rc:
        st.markdown(f'<div style="background:white;border:1px solid {MGRAY};border-radius:16px;padding:22px 24px"><div style="font-size:9px;text-transform:uppercase;letter-spacing:.2em;color:{DGRAY};font-weight:600;margin-bottom:2px">ENGAGEMENT STATE MIX</div><div style="font-family:\'DM Serif Display\',serif;font-size:18px;color:#0F172A;margin-bottom:14px">Healthcare Professionals per state</div>', unsafe_allow_html=True)
        fig=go.Figure()
        for cid in range(1,6):
            n=counts.get(cid,0)
            fig.add_trace(go.Bar(x=[n],y=[CLUSTER_NAMES[cid]],orientation="h",marker_color=CLUSTER_COLORS[cid],text=[str(n)],textposition="outside",name=CLUSTER_NAMES[cid]))
        fig.update_layout(height=260,showlegend=False,plot_bgcolor="white",paper_bgcolor="white",font=dict(family="Inter",size=11),barmode="group",xaxis=dict(showticklabels=False,showgrid=False,zeroline=False),margin=dict(l=0,r=40,t=0,b=0))
        st.plotly_chart(fig,use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f'<div style="background:{NAVY};border-radius:16px;padding:24px 32px"><div style="font-size:10px;text-transform:uppercase;letter-spacing:.2em;color:rgba(255,255,255,.5);font-weight:600;margin-bottom:6px">FOR THE FIELD TEAM</div><div style="font-family:\'DM Serif Display\',serif;font-size:24px;font-weight:300;color:white;margin-bottom:4px">Generate a custom doctor rep support card for any profile.</div><div style="font-size:13px;color:rgba(255,255,255,.6)">Pick specialty, setting, and target type. The system pulls every insight from the integrated data.</div></div>', unsafe_allow_html=True)
    if st.button("Open the Custom Rep Support Card →", key="cta_env_ov"): st.session_state["view"]="envelope"; st.rerun()
