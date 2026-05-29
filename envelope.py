"""Custom Rep Support Card — envelope view."""
import streamlit as st
import pandas as pd
from collections import Counter

TEAL="#0F4C5C"; NAVY="#1E293B"; CRIMSON="#832232"; AMBER="#B8860B"; GREEN="#15803D"
MGRAY="#E2E8F0"; DGRAY="#64748B"; LGRAY="#F8FAFC"
CLUSTER_COLORS={1:TEAL,2:NAVY,3:CRIMSON,4:AMBER,5:GREEN}
CLUSTER_NAMES={1:"Patient ID Priority",2:"Access Pending",3:"Evidence Gap",4:"Narrative Build",5:"Conviction-Led"}

ACTION_FLOWS={
    1:"Lead with patient identification. Bring NGS testing pathway and patient-finding protocol. Save efficacy for call 2 once the patient exists.",
    2:"Lead with access, not efficacy. Bring physical access toolkit (copay card + PA checklist + patient support hotline). Walk through one live enrolment together.",
    3:"Name the misbelief in the first 90 seconds. Bring long-term PFS curves + subgroup forest plot. Counter the competitor frame directly.",
    4:"Pick ONE message and repeat every visit. Deploy a single visual anchor. Invite to peer KOL event. No deck rotation.",
    5:"Stop selling. Start partnering. Advisory board invite, pipeline briefing, competitive vigilance brief.",
}
OPENERS={
    1:"Where do your Grade 2 IDH-mutant patients come from — referral or self-identified?",
    2:"What's the biggest friction point in getting patients started today?",
    3:"I want to address the relapse data head-on — can I show you the long-term curves?",
    4:"If you had to describe VORANIGO in one sentence to a colleague, what would you say?",
    5:"We're putting together an advisory board on the next readout — would you be interested?",
}
STARTERS={
    1:["Have you tried the molecular testing pathway?","What % of glioma patients do you NGS test at diagnosis?","What does your current patient identification workflow look like?"],
    2:["Have you used ServierONE programmes by name for a specific patient?","What happened the last time you submitted a PA for VORANIGO?","What's the biggest friction point in getting patients started?"],
    3:["I want to address the relapse data — can I show you the 36-month curves?","What specific data point would shift your view?","Have you seen the competitor vs. VORANIGO subgroup analysis?"],
    4:["Which of our clinical claims do you find most credible?","When did you last prescribe, and what made you choose it that time?","If you had to describe VORANIGO in one sentence, what would you say?"],
    5:["We're putting together an advisory board — would you be interested?","What data from the next readout would most change your practice?","Who in your peer network has asked you about VORANIGO recently?"],
}
MSG_PRIORITIES={
    1:["V1: Indication — Grade 2, IDH-mutant, post-surgery","V14: NCCN preferred","Name three ServierONE programmes by name"],
    2:["V6: TTNI — 74% reduction in risk of next intervention","V5: PFS — 61%/65%↓ risk of progression","V13: Seizure — 64% lower rate vs. placebo"],
    3:["V5: PFS — extended analysis 65%↓","V12: TGR — −1.3% vs +14.4% placebo","V9: Safety — ALT 10%, AST 4.8% (address directly)"],
    4:["V2: Innovation — first new Gr2 treatment in 20+ years","V6: TTNI — 74% (most motivating for non-users)","V13: Seizure reduction (QoL anchor)"],
    5:["Pipeline readout timeline","Competitive intelligence summary","Advisory board / speaker program details"],
}
VISUAL_AIDS={
    1:["Patient identification checklist (laminated, leave behind)","NGS Testing Pathway flowchart","Access Toolkit One-Pager"],
    2:["Access Toolkit One-Pager (copay + PA + patient support)","PA checklist + Reimbursement Process Flowchart","Case-closed examples — PA overturned in 72 hours"],
    3:["Long-term PFS curves (36-month extended analysis)","Subgroup forest plot","Competitor head-to-head data slide"],
    4:["Single-message visual anchor (TTNI or Innovation — pick one)","Peer KOL endorsement quote card","Seizure reduction infographic"],
    5:["Pipeline readout one-pager","Competitive vigilance briefing","Advisory board / speaker faculty program details"],
}


def render(eng, hcps):
    st.markdown(f"""
<div style="margin-bottom:16px">
  <div style="font-size:10px;text-transform:uppercase;letter-spacing:.22em;color:{DGRAY};font-weight:600">CUSTOM DOCTOR REP SUPPORT CARD · DATA-DRIVEN</div>
  <h1 style="font-family:'DM Serif Display',serif;font-size:42px;font-weight:300;color:#0F172A;margin:4px 0">Pick a profile.</h1>
  <h2 style="font-family:'DM Serif Display',serif;font-size:26px;font-weight:300;color:#0F172A">Get the play, generated from real Healthcare Professionals.</h2>
</div>
""", unsafe_allow_html=True)

    if hcps is None or hcps.empty:
        st.warning("No data loaded."); return

    fa, fb, fc = st.columns(3)
    with fa:
        st.markdown('<div style="font-size:10px;text-transform:uppercase;letter-spacing:.2em;color:#94A3B8;font-weight:600;margin-bottom:4px">SPECIALTY</div>', unsafe_allow_html=True)
        spec_opts = ["All"] + sorted(hcps["specialty"].dropna().unique().tolist())
        spec = st.selectbox("Specialty", spec_opts, label_visibility="collapsed", key="env_spec")
    with fb:
        st.markdown('<div style="font-size:10px;text-transform:uppercase;letter-spacing:.2em;color:#94A3B8;font-weight:600;margin-bottom:4px">SETTING</div>', unsafe_allow_html=True)
        sett_opts = ["All"] + sorted(hcps["setting"].dropna().unique().tolist())
        sett = st.selectbox("Setting", sett_opts, label_visibility="collapsed", key="env_sett")
    with fc:
        st.markdown('<div style="font-size:10px;text-transform:uppercase;letter-spacing:.2em;color:#94A3B8;font-weight:600;margin-bottom:4px">PATIENT LOAD</div>', unsafe_allow_html=True)
        load = st.selectbox("Load", ["All","Low","Medium","High"], label_visibility="collapsed", key="env_load")

    matched = hcps.copy()
    if spec != "All": matched = matched[matched["specialty"] == spec]
    if sett != "All": matched = matched[matched["setting"] == sett]
    if load != "All": matched = matched[matched["load"] == load]

    if matched.empty:
        st.warning("No HCPs match this profile. Try adjusting filters."); return

    cc = Counter(matched["cluster"].tolist())
    dom = cc.most_common(1)[0][0]
    dom_pct = round(cc[dom] / len(matched) * 100)
    color = CLUSTER_COLORS[dom]

    avg_ici = round(matched["ICI"].mean(), 1) if "ICI" in matched.columns else 0
    weak_dim = min(["AC","IBC","MBC","RTC","ABR","KCC","CI"], key=lambda d: matched[d].mean() if d in matched.columns else 100)
    strong_dim = max(["AC","IBC","MBC","RTC","ABR","KCC","CI"], key=lambda d: matched[d].mean() if d in matched.columns else 0)

    # Cluster mix bar
    bar = '<div style="display:flex;height:42px;border-radius:10px;overflow:hidden;border:1px solid #E2E8F0;margin-bottom:20px">'
    for cid in range(1,6):
        n = cc.get(cid,0); fl = max(n,1)
        bar += f'<div style="background:{CLUSTER_COLORS[cid]};flex:{fl};display:flex;flex-direction:column;justify-content:center;padding:0 8px;color:white"><div style="font-size:8px;text-transform:uppercase;opacity:.8">{CLUSTER_NAMES[cid][:12]}</div><div style="font-size:16px;font-family:DM Serif Display,serif">{n}</div></div>'
    bar += "</div>"

    ref_li = lambda items: "".join(f'<li style="font-size:12px;color:#475569;margin-bottom:4px;line-height:1.5">{i}</li>' for i in items)

    st.markdown(f"""
<div style="background:white;border:1px solid {MGRAY};border-radius:18px;padding:28px;margin-top:16px">
  <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px">
    <div style="font-size:13px;font-weight:600;color:#0F172A">Generated from {len(matched)} Healthcare Professionals</div>
    <div style="margin-left:auto;background:#F1F5F9;padding:3px 10px;border-radius:6px;font-size:11px;font-weight:600;color:#475569">{sett if sett != 'All' else 'All Settings'}</div>
  </div>
  <div style="background:#FFFBEB;border:1px solid #FCD34D;border-radius:8px;padding:10px 14px;font-size:12px;color:#92400E;margin-bottom:18px">
    ⚠ Performance note: This action card is derived from {len(matched)} HCPs in the surveyed panel matching the selected profile. Field re-ordering — not a script. Adapt to individual doctor, then follow the data.
  </div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:24px;margin-bottom:24px">
    <div>
      <div style="font-size:10px;text-transform:uppercase;letter-spacing:.2em;color:#94A3B8;font-weight:600;margin-bottom:6px">MOST LIKELY ENGAGEMENT STATE</div>
      <div style="font-size:22px;font-weight:700;color:#0F172A;margin-bottom:6px">{CLUSTER_NAMES[dom]}</div>
      <div style="font-size:14px;color:#64748B;margin-bottom:14px"><span style="font-size:28px;font-family:'DM Serif Display',serif;color:{color}">{dom_pct}%</span> of matched HCPs fit here</div>
      <div style="display:flex;gap:20px">
        <div><div style="font-size:10px;color:#94A3B8;letter-spacing:.12em;text-transform:uppercase">ICI</div><div style="font-family:'DM Serif Display',serif;font-size:24px">{avg_ici}</div></div>
        <div><div style="font-size:10px;color:#94A3B8;letter-spacing:.12em;text-transform:uppercase">WEAKEST</div><div style="font-weight:700;color:{CRIMSON}">{weak_dim}</div></div>
        <div><div style="font-size:10px;color:#94A3B8;letter-spacing:.12em;text-transform:uppercase">STRONGEST</div><div style="font-weight:700;color:{GREEN}">{strong_dim}</div></div>
      </div>
    </div>
    <div>
      <div style="font-size:10px;text-transform:uppercase;letter-spacing:.2em;color:#94A3B8;font-weight:600;margin-bottom:8px">MOST RECOMMENDED ACTION FLOW</div>
      <div style="background:{TEAL};color:white;border-radius:12px;padding:16px 20px;font-size:13px;line-height:1.65;margin-bottom:10px">{ACTION_FLOWS[dom]}</div>
      <div style="background:linear-gradient(135deg,{TEAL}14,{TEAL}08);border:1px solid {TEAL}22;border-radius:10px;padding:12px 16px;font-size:13px;font-weight:500;color:{TEAL}">
        💬 Suggested opener:<br><span style="font-style:italic">"{OPENERS[dom]}"</span>
      </div>
    </div>
  </div>
  <div style="font-size:10px;text-transform:uppercase;letter-spacing:.2em;color:#94A3B8;font-weight:600;margin-bottom:8px">CLUSTER MIX IN THIS SAMPLE</div>
  {bar}
  <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-top:20px;padding-top:16px;border-top:1px solid #F1F5F9">
    <div>
      <div style="font-size:10px;text-transform:uppercase;letter-spacing:.15em;color:#94A3B8;font-weight:600;margin-bottom:6px">CONVERSATION STARTERS</div>
      <ul style="padding-left:16px;margin:0">{ref_li(STARTERS[dom])}</ul>
    </div>
    <div>
      <div style="font-size:10px;text-transform:uppercase;letter-spacing:.15em;color:#94A3B8;font-weight:600;margin-bottom:6px">KEY TALKING POINTS</div>
      <ul style="padding-left:16px;margin:0">{ref_li(MSG_PRIORITIES[dom])}</ul>
    </div>
    <div>
      <div style="font-size:10px;text-transform:uppercase;letter-spacing:.15em;color:#94A3B8;font-weight:600;margin-bottom:6px">MESSAGE PRIORITIES</div>
      <ul style="padding-left:16px;margin:0">{ref_li(MSG_PRIORITIES[dom])}</ul>
    </div>
    <div>
      <div style="font-size:10px;text-transform:uppercase;letter-spacing:.15em;color:#94A3B8;font-weight:600;margin-bottom:6px">VISUAL AIDS TO RECOMMEND</div>
      <ul style="padding-left:16px;margin:0">{ref_li(VISUAL_AIDS[dom])}</ul>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)
