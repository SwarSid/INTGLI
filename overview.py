"""Overview view — exact replica of Emergent hero dashboard."""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

TEAL="#0F4C5C"; NAVY="#1E293B"; CRIMSON="#832232"; AMBER="#B8860B"; GREEN="#15803D"
LGRAY="#F8FAFC"; MGRAY="#E2E8F0"; DGRAY="#64748B"
CLUSTER_COLORS={1:TEAL,2:NAVY,3:CRIMSON,4:AMBER,5:GREEN}
CLUSTER_NAMES={1:"Patient ID Priority",2:"Intent Led Access Pending",3:"Evidence Gap",4:"Narrative Building Opportunity",5:"Conviction-Led Prescriber"}
CLUSTER_SHORT={1:"Patient ID",2:"Access Pending",3:"Evidence Gap",4:"Narrative Build",5:"Conviction-Led"}
DIMS=[("AC","Awareness Conversion",14,CRIMSON),("IBC","Intent — Behavior",25,NAVY),
      ("MBC","Message — Belief",20,CRIMSON),("RTC","Rep Trust",13,TEAL),
      ("ABR","Access Barrier Resolution",15,NAVY),("KCC","Knowledge Conversion",8,GREEN),
      ("CI","Competitive Influence",5,AMBER)]

# HCP avatars from Pexels (royalty-free)
AVATARS={
    1:"https://images.unsplash.com/photo-1612531385446-f7e6d131e1d0?w=120&h=120&fit=crop&crop=face",
    2:"https://images.unsplash.com/photo-1594824476967-48c8b964273f?w=120&h=120&fit=crop&crop=face",
    3:"https://images.unsplash.com/photo-1642541724244-83d49288a86b?w=120&h=120&fit=crop&crop=face",
    4:"https://images.unsplash.com/photo-1594824476967-48c8b964273f?w=120&h=120&fit=crop&crop=face",
    5:"https://images.unsplash.com/photo-1612531385446-f7e6d131e1d0?w=120&h=120&fit=crop&crop=face",
}
INSIGHTS={
    1:{"pet":"Brand messages × 14","atu":"Patient identification protocol","quote":"\"Doesn't see the patient yet.\"","pet_tag":"misaligned pitch","atu_tag":"patient identification protocol"},
    2:{"pet":"Efficacy pitch","atu":"Reimbursement details","quote":"\"Wants to prescribe. Access is locked.\"","pet_tag":"efficacy pitch","atu_tag":"reimbursement details"},
    3:{"pet":"Top-line efficacy","atu":"Long-term PFS data","quote":"\"Carries one specific misbelief.\"","pet_tag":"top-line efficacy","atu_tag":"long-term PFS data"},
    4:{"pet":"Rotating brand stories","atu":"One memorable hook","quote":"\"Belief is shallow. Story doesn't stick.\"","pet_tag":"rotating brand stories","atu_tag":"durable narrative focus"},
    5:{"pet":"Standard sales aids","atu":"Pipeline + advisory invite","quote":"\"Already prescribing. Wants partnership.\"","pet_tag":"standard sales aids","atu_tag":"pipeline + advisory"},
}


def render(eng, hcps):
    if hcps is None or hcps.empty: st.warning("No data."); return

    total = len(hcps) or 1
    counts = {cid: int((hcps["cluster"]==cid).sum()) for cid in range(1,6)}
    avg_ici = round(hcps["ICI"].mean(),1)
    conviction_pct = round(counts[5]/total*100)
    access_pct = round(counts[2]/total*100)

    # ── Headline ──
    st.markdown(f'<div style="font-size:10px;text-transform:uppercase;letter-spacing:.28em;color:{CRIMSON};font-weight:600;margin-bottom:6px;display:flex;align-items:center;gap:8px">HERO OVERVIEW <span style="flex:1;height:1px;background:linear-gradient(to right,{CRIMSON}44,transparent)"></span></div>', unsafe_allow_html=True)
    st.markdown(f"""
<h1 style="font-family:'DM Serif Display',serif;font-size:52px;font-weight:300;color:#0F172A;line-height:1.05;margin-bottom:10px">
  The 360° conversion story,<br><span style="color:{TEAL}">told in five acts.</span>
</h1>
<p style="font-size:15px;color:#475569;max-width:640px;line-height:1.65;margin-bottom:28px">
  {total} Healthcare Professionals (HCPs) who completed both Awareness Trial Usage (ATU) and
  Promotional Effectiveness Tracker (PET) surveys, resolved through the Interaction Conversion
  Index (ICI) into five sequential engagement states.
</p>""", unsafe_allow_html=True)

    # ── 4 Metric Cards ──
    c1,c2,c3,c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="mcard"><div class="mlabel">HCPs IN VIEW</div><div class="mval">{total}</div><div class="msub">Completed Awareness Trial Usage × Promotional Effectiveness Tracker</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="mcard"><div class="mlabel">AVG INTERACTION CONVERSION INDEX</div><div class="mval">{avg_ici}<span style="font-size:22px;color:#94A3B8">/100</span></div><div class="msub">7-dimension weighted</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="mcard"><div class="mlabel">CONVICTION-LED</div><div class="mval">{conviction_pct}<span style="font-size:22px;color:#94A3B8">%</span></div><div class="msub">Franchise advocates</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="acard"><div class="mlabel">PRIMARY BLOCKER</div><div style="font-family:\'DM Serif Display\',serif;font-size:28px;color:white;line-height:1.1;margin:6px 0">Access Pending</div><div class="msub">{access_pct}% of Healthcare Professionals · largest single state</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── ATU × PET Bridge ──
    _render_bridge(hcps)
    st.markdown("<br>", unsafe_allow_html=True)

    # ── Conversion Journey ──
    st.markdown(f"""
<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px">
  <div>
    <div style="font-size:10px;text-transform:uppercase;letter-spacing:.22em;color:{DGRAY};font-weight:600">THE CONVERSION JOURNEY</div>
    <h2 style="font-family:'DM Serif Display',serif;font-size:24px;color:#0F172A;margin:4px 0">
      Sequential resolution from patient identification to conviction
    </h2>
  </div>
  <div style="font-size:11px;color:#94A3B8">Clicking cluster to open rep card →</div>
</div>""", unsafe_allow_html=True)

    # Segmented bar
    bar = '<div style="display:flex;height:56px;border-radius:12px;overflow:hidden;border:1px solid #E2E8F0;box-shadow:0 1px 4px rgba(0,0,0,.06);margin-bottom:20px">'
    for cid in range(1,6):
        n=counts.get(cid,0); pct=round(n/total*100); fl=max(pct,4)
        bar+=f'<div style="background:{CLUSTER_COLORS[cid]};flex:{fl};display:flex;flex-direction:column;justify-content:center;padding:0 12px;color:white"><div style="font-size:10px;text-transform:uppercase;letter-spacing:.15em;opacity:.8;font-weight:600;white-space:nowrap;overflow:hidden">{cid} · {CLUSTER_SHORT[cid]}</div><div style="font-family:DM Serif Display,serif;font-size:22px;line-height:1">{pct}%</div></div>'
    bar+="</div>"
    st.markdown(bar, unsafe_allow_html=True)

    # Cluster rows (with avatar, 12-col layout)
    for cid in range(1,6):
        n=counts.get(cid,0); color=CLUSTER_COLORS[cid]; ins=INSIGHTS[cid]
        avatar=AVATARS[cid]
        if st.button(f"  Act {cid} · {CLUSTER_NAMES[cid]}  ", key=f"cl_btn_{cid}", use_container_width=False):
            st.session_state["view"]=f"cluster_{cid}"; st.rerun()
        st.markdown(f"""
<div style="background:white;border:1px solid {MGRAY};border-radius:16px;padding:14px 20px;margin-bottom:8px;margin-top:-8px;cursor:pointer"
     onclick="">
  <div style="display:grid;grid-template-columns:200px 1fr 80px;gap:14px;align-items:center">
    <!-- HCP avatar + cluster label -->
    <div style="display:flex;align-items:center;gap:10px">
      <div style="position:relative;flex-shrink:0">
        <div style="position:absolute;inset:-2px;border-radius:50%;opacity:.25;filter:blur(4px);background:{color}"></div>
        <img src="{avatar}" style="position:relative;width:44px;height:44px;border-radius:50%;object-fit:cover;border:2px solid {color}" onerror="this.style.display='none'">
      </div>
      <div>
        <div style="display:flex;align-items:center;gap:4px">
          <div style="font-size:10px;text-transform:uppercase;letter-spacing:.15em;color:#94A3B8;font-weight:600">Act {cid}</div>
        </div>
        <div style="font-size:13px;font-weight:600;color:#0F172A;line-height:1.2">{CLUSTER_NAMES[cid]}</div>
      </div>
    </div>
    <!-- PET insight ATU 3-column -->
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;align-items:center">
      <div style="text-align:right">
        <span style="background:{NAVY};color:white;padding:1px 6px;border-radius:3px;font-size:8px;font-weight:700">PET</span>
        <div style="font-size:11px;color:#64748B;margin-top:2px">{ins['pet_tag']}</div>
      </div>
      <div style="text-align:center;padding:0 8px;border-left:1px solid #F1F5F9;border-right:1px solid #F1F5F9">
        <div style="font-size:12px;font-weight:600;color:{color}">{ins['quote']}</div>
      </div>
      <div>
        <span style="background:{TEAL};color:white;padding:1px 6px;border-radius:3px;font-size:8px;font-weight:700">ATU</span>
        <div style="font-size:11px;color:#64748B;margin-top:2px">{ins['atu_tag']}</div>
      </div>
    </div>
    <!-- Count -->
    <div style="text-align:right">
      <div style="font-family:'DM Serif Display',serif;font-size:28px;color:#0F172A;line-height:1">{n}</div>
      <div style="font-size:10px;color:#94A3B8;text-transform:uppercase">HCPs</div>
    </div>
  </div>
</div>
<br>""", unsafe_allow_html=True)

    # ── ICI Dimension health + cluster distribution ──
    st.markdown("<br>", unsafe_allow_html=True)
    lc, rc = st.columns([3,2])
    with lc:
        st.markdown(f"""<div style="background:white;border:1px solid {MGRAY};border-radius:16px;padding:20px 24px">
<div style="font-size:10px;text-transform:uppercase;letter-spacing:.22em;color:{DGRAY};font-weight:600;margin-bottom:2px">INTERACTION CONVERSION INDEX · DIMENSION HEALTH</div>
<h3 style="font-family:'DM Serif Display',serif;font-size:20px;color:#0F172A;margin:4px 0 4px">Where the interaction works — and where it leaks</h3>
<p style="font-size:11px;color:#94A3B8;margin-bottom:16px">Average score (0–100) across the filtered Healthcare Professional set. Weight shown in parentheses.</p>""", unsafe_allow_html=True)
        for key,name,weight,color in DIMS:
            if key in hcps.columns:
                avg=round(hcps[key].mean(),1)
                fill=GREEN if avg>=70 else TEAL if avg>=50 else CRIMSON
                st.markdown(f"""<div style="display:flex;align-items:center;gap:12px;margin-bottom:12px">
  <div style="width:200px;flex-shrink:0">
    <div style="font-size:12px;font-weight:500;color:#0F172A">{name} <span style="color:#CBD5E1">({key})</span></div>
    <div style="font-size:10px;color:#CBD5E1;text-transform:uppercase;letter-spacing:.12em">{weight}% weight</div>
  </div>
  <div style="flex:1;height:10px;background:#F1F5F9;border-radius:99px;overflow:hidden">
    <div style="width:{avg}%;height:100%;background:{fill};border-radius:99px"></div>
  </div>
  <div style="width:36px;text-align:right;font-family:'DM Serif Display',serif;font-size:18px;font-weight:300;color:#0F172A">{avg}</div>
</div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with rc:
        cd=[{"n":CLUSTER_SHORT[cid],"v":counts.get(cid,0),"c":CLUSTER_COLORS[cid]} for cid in range(1,6)]
        fig=go.Figure()
        for d in cd:
            fig.add_trace(go.Bar(x=[d["v"]],y=[d["n"]],orientation="h",marker_color=d["c"],
                                 text=[d["v"]],textposition="outside",name=d["n"]))
        fig.update_layout(height=300,showlegend=False,plot_bgcolor="white",paper_bgcolor="white",
                          font=dict(family="Inter",size=11),barmode="group",
                          xaxis=dict(showticklabels=False,showgrid=False,zeroline=False),
                          margin=dict(l=0,r=40,t=10,b=0),
                          title=dict(text="Cluster Distribution\nHealthcare Professionals per engagement state",
                                     font=dict(family="DM Serif Display",size=16)))
        st.plotly_chart(fig,use_container_width=True)


def _render_bridge(hcps):
    voices=[
        {"name":"Dr. Sarah Patel","spec":"Medical Oncology · Academic","quote":"I asked for reimbursement information. Three visits later, I still don't have it. My patient is waiting.","pet":["Efficacy pitch","Sample request form","Comparator data"],"atu":["Copay card details · ABR","Prior auth checklist · ABR","Patient support contact · ABR"],"gap":"ABR","gapnote":"Access Barrier Resolution (15% of ICI · capped at 55)","cid":2},
        {"name":"Dr. David Kim","spec":"Neuro-Oncology · Community","quote":"Help me find the patient before you sell me the therapy. I rarely see Grade 2 IDH-mutant cases — show me where they are.","pet":["Brand messages × 14","Mechanism visual aid","Efficacy data deck"],"atu":["Patient ID protocol · AC","Testing pathway guidance · KCC","Eligible patient criteria · AC"],"gap":"AC","gapnote":"Awareness Conversion (14% of ICI)","cid":1},
        {"name":"Dr. James Wilson","spec":"Neuro-Oncology · Academic","quote":"I'm already prescribing. Stop pitching me — invite me into the conversation.","pet":["Repeat efficacy pitch","Standard sales aids","Volume reminders"],"atu":["Pipeline + next readouts · KCC","Advisory / speaker invite · RTC","Competitive vigilance · CI"],"gap":"RTC","gapnote":"Rep Trust Conversion — channel partnership opportunity","cid":5},
    ]
    bv=voices[st.session_state.get("bi",0)%len(voices)]
    color=CLUSTER_COLORS[bv["cid"]]

    st.markdown(f'<div style="font-size:10px;text-transform:uppercase;letter-spacing:.22em;color:{DGRAY};font-weight:600">THE CONVERSION GAP · WALKED THROUGH BY THE HCP</div>', unsafe_allow_html=True)
    st.markdown(f'<h2 style="font-family:\'DM Serif Display\',serif;font-size:24px;color:#0F172A;margin:4px 0 16px">What the rep delivered <span style="color:#94A3B8">vs.</span> what the doctor actually wanted</h2>', unsafe_allow_html=True)

    pet_html="".join(f'<div style="background:white;border:1px solid {MGRAY};border-radius:12px;padding:10px 14px;margin-bottom:8px;display:flex;align-items:center;gap:10px"><div style="width:8px;height:8px;border-radius:50%;background:{NAVY};flex-shrink:0"></div><div style="font-size:13px;color:#334155">{i}</div></div>' for i in bv["pet"])
    atu_html="".join(f'<div style="background:white;border:1px solid {MGRAY};border-radius:12px;padding:10px 14px;margin-bottom:8px;display:flex;align-items:center;justify-content:flex-end;gap:10px;text-align:right"><div style="font-size:13px;color:#334155">{i}</div><div style="width:8px;height:8px;border-radius:50%;background:{TEAL};flex-shrink:0"></div></div>' for i in bv["atu"])

    st.markdown(f"""
<div style="background:linear-gradient(135deg,white,{LGRAY});border:1px solid {MGRAY};border-radius:24px;padding:28px 36px;position:relative;overflow:hidden">
  <div style="position:absolute;top:-60px;right:-60px;width:300px;height:300px;border-radius:50%;background:{color};opacity:.07;pointer-events:none"></div>
  <div style="display:grid;grid-template-columns:1fr auto 1fr;gap:32px;align-items:center">
    <div>
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px">
        <span style="background:{NAVY};color:white;padding:2px 8px;border-radius:4px;font-size:9px;font-weight:700">PET</span>
        <span style="font-size:11px;color:#64748B">What the visit delivered</span>
      </div>
      {pet_html}
    </div>
    <div style="text-align:center;min-width:180px">
      <div style="position:relative;display:inline-block;margin-bottom:12px">
        <div style="position:absolute;inset:-6px;border-radius:50%;background:{color};opacity:.2;filter:blur(8px)"></div>
        <div style="position:relative;width:80px;height:80px;border-radius:50%;background:{color};display:flex;align-items:center;justify-content:center;font-size:30px;border:4px solid white;margin:0 auto">👩‍⚕️</div>
        <div style="position:absolute;bottom:-8px;left:50%;transform:translateX(-50%);background:{color};color:white;border-radius:999px;padding:2px 8px;font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.15em;white-space:nowrap">State {bv['cid']}</div>
      </div>
      <div style="font-family:'DM Serif Display',serif;font-size:16px;color:#0F172A;margin-top:16px">{bv['name']}</div>
      <div style="font-size:10px;text-transform:uppercase;letter-spacing:.15em;color:#94A3B8;margin-bottom:12px">{bv['spec']}</div>
      <div style="background:white;border:1px solid {MGRAY};border-radius:14px;padding:12px 16px;box-shadow:0 4px 20px rgba(15,76,92,.08);font-size:12px;font-style:italic;color:#334155;line-height:1.6;">
        "{bv['quote']}"
      </div>
      <div style="margin-top:10px;display:inline-flex;align-items:center;gap:6px;background:{CRIMSON};color:white;border-radius:999px;padding:5px 12px;font-size:11px;font-weight:600">
        Conversion gap → {bv['gap']}
        <span style="opacity:.7;font-size:9px">{bv['gapnote']}</span>
      </div>
    </div>
    <div>
      <div style="display:flex;align-items:center;justify-content:flex-end;gap:8px;margin-bottom:12px">
        <span style="font-size:11px;color:#64748B">What the HCP wanted</span>
        <span style="background:{TEAL};color:white;padding:2px 8px;border-radius:4px;font-size:9px;font-weight:700">ATU</span>
      </div>
      {atu_html}
    </div>
  </div>
  <div style="display:flex;justify-content:space-between;margin-top:20px;padding-top:16px;border-top:1px solid #F1F5F9;font-size:10px;text-transform:uppercase;letter-spacing:.2em;color:#CBD5E1;font-weight:600">
    <span>Promotional Effectiveness Tracker</span><span>— ICI bridge —</span><span>Awareness Trial Usage</span>
  </div>
</div>""", unsafe_allow_html=True)

    bc1,bc2,bc3=st.columns([1,8,1])
    with bc1:
        if st.button("←",key="bprev_ov"): st.session_state["bi"]=st.session_state.get("bi",0)-1; st.rerun()
    with bc3:
        if st.button("→",key="bnext_ov"): st.session_state["bi"]=st.session_state.get("bi",0)+1; st.rerun()
    dots="".join(f'<span style="width:{"32px" if i==st.session_state.get("bi",0)%3 else "6px"};height:6px;border-radius:99px;background:{"#0F172A" if i==st.session_state.get("bi",0)%3 else "#CBD5E1"};display:inline-block;margin:0 2px;transition:all .2s"></span>' for i in range(3))
    st.markdown(f'<div style="text-align:center;margin-top:10px">{dots}</div>',unsafe_allow_html=True)
