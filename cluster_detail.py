"""
Cluster detail view — exact match to Emergent RepCardView.
Shows: hero card, PET vs ATU findings, ICI profile, segment mix, HCP roster.
"""
import streamlit as st
import pandas as pd
import numpy as np

TEAL="#0F4C5C"; NAVY="#1E293B"; CRIMSON="#832232"; AMBER="#B8860B"; GREEN="#15803D"
LGRAY="#F8FAFC"; MGRAY="#E2E8F0"; DGRAY="#64748B"
CLUSTER_COLORS={1:TEAL,2:NAVY,3:CRIMSON,4:AMBER,5:GREEN}
CLUSTER_NAMES={1:"Patient ID Priority",2:"Intent Led Access Pending",3:"Evidence Gap",4:"Narrative Building Opportunity",5:"Conviction-Led Prescriber"}
DIMS=[("AC","Awareness Conversion",14),("IBC","Intent — Behavior",25),
      ("MBC","Message — Belief",20),("RTC","Rep Trust",13),
      ("ABR","Access Barrier Resolution",15),("KCC","Knowledge Conversion",8),("CI","Competitive Influence",5)]

AVATARS={
    1:"https://images.unsplash.com/photo-1612531385446-f7e6d131e1d0?w=300&h=300&fit=crop&crop=face",
    2:"https://images.unsplash.com/photo-1594824476967-48c8b964273f?w=300&h=300&fit=crop&crop=face",
    3:"https://images.unsplash.com/photo-1642541724244-83d49288a86b?w=300&h=300&fit=crop&crop=face",
    4:"https://images.unsplash.com/photo-1594824476967-48c8b964273f?w=300&h=300&fit=crop&crop=face",
    5:"https://images.unsplash.com/photo-1612531385446-f7e6d131e1d0?w=300&h=300&fit=crop&crop=face",
}

CLUSTER_CONTENT = {
1:{
"headline":"Help them see the patient before selling the product.",
"trigger":"Low qualifying patient load",
"quote":"Help me find the patient before you sell me the therapy. I rarely see Grade 2 IDH-mutant cases — show me where they are.",
"quote_attr":"Composite Voice · Brand-Oncology · Community Setting",
"pet_findings":[
{"title":"Brand messages were delivered, but recall is shallow",
 "data":"Average message recall of 1.8 of 5 brand messages across this cluster.",
 "source":"Summary: Trial, Avg: S1_485 | S1_AMB",
 "why":"Low recall directly suppresses Awareness Conversion (AC, 14% of ICI) — the visit didn't make the product front-of-mind."},
{"title":"Visit topics did not match the HCP's priorities",
 "data":"Topics discussed matched the doctor's top-importance attributes in 76% of visits in this cluster.",
 "source":"PET: RT_S1_885 | Summary: Trial, Avg: S1_248",
 "why":"Misaligned topics suppress Message — Belief Conversion (MBC, 20% of ICI) — content was delivered, but on the wrong attributes."},
{"title":"Visual aid recall is dominated by mechanism slides",
 "data":"Only 1 of 5 visual-aid content types is recalled (mechanism slide). Patient-identification content was never shown.",
 "source":"Summary: PET, S1_485 | S1_485",
 "why":"Without patient-identification visual aids, the volume blocker stays invisible to the rep — the conversation defaults back to therapy messaging."},
],
"atu_findings":[
{"title":"Qualifying patient volume is below threshold",
 "data":"Average of 2.1 Grade 2 IDH-mutant patients per HCP vs. 5 needed for behavioural conversion.",
 "source":"Summary: Trial, Avg: S1_485",
 "why":"Low volume directly suppresses Intent — Behavior Conversion (IBC, 25% of ICI) — the doctor cannot build prescribing muscle memory without enough eligible patients."},
{"title":"Diagnostic testing pathway is not embedded in workflow",
 "data":"NGS/Sequencing testing rate is 10% in this cluster vs. 70% benchmark for early identification.",
 "source":"Summary: Trial, Avg: S1_485",
 "why":"Without molecular testing, eligible patients are never identified — breaking the Knowledge & Classification Conversion (KCC, 8% of ICI) chain at the earliest step."},
{"title":"Familiarity with the product remains high despite low usage",
 "data":"Average familiarity of 4.2 of 5 — awareness is intact, but volume is the limiter.",
 "source":"Summary: ATU, Avg: S1_485",
 "why":"High familiarity + low usage is the fingerprint of a volume-led blocker, not an awareness or evidence one. Field action must focus on patient identification, not product re-education."},
],
"dim_scores":{"AC":41,"IBC":24,"MBC":29,"RTC":49,"ABR":55,"KCC":44,"CI":37},
"seg_spec":{"Medical Oncology":7,"Neuro-Oncology":6,"Hematology-Oncology":5},
"seg_sett":{"Academic":5,"Community":8,"Integrated Network":5},
"seg_load":{"Low":8,"Medium":6,"High":4},
},
2:{
"headline":"Intent is high. Unlock the access gate.",
"trigger":"Access never discussed; support programs unknown",
"quote":"I asked for reimbursement information. Three visits later, I still don't have it. My patient is waiting.",
"quote_attr":"Composite Voice · Medical Oncology · Academic Setting",
"pet_findings":[
{"title":"Access was never raised in the visit",
 "data":"Access discussion appeared in 6% of visits in this cluster, despite reimbursement being the explicit blocker.",
 "source":"Summary: PET, S2_885 | S2_Flag",
 "why":"When access is not discussed, Access Barrier Resolution (ABR, 15% of ICI) is automatically capped at 55 — conversion is mathematically locked regardless of clinical messaging."},
{"title":"Visual aids deployed do not include access content",
 "data":"0 of 5 access-specific visual aids (copay card, access toolkit, patient support) were used in visits.",
 "source":"Summary: PET, S2_885",
 "why":"Without access aids in the rep's bag, the conversation defaults to clinical content — even when the doctor explicitly asks for reimbursement help."},
{"title":"Rep call quality scores are high — but on the wrong topic",
 "data":"Average call-quality rating of 5.7 of 7 across rep attributes.",
 "source":"Summary: PET, S2_485",
 "why":"High Rep Trust Conversion (RTC, 13% of ICI) is being earned on clinical conversation, not on resolving the access gate. The trust is real but mis-directed."},
],
"atu_findings":[
{"title":"Demonstrated intent is at the top of the panel",
 "data":"100% of cluster has agreed-to-prescribe — currently prescribing. Future intent averages 5.2 of 10.",
 "source":"Summary: Trial, Avg: S2_885 | S2_885",
 "why":"When Intent — Behavior Conversion (IBC) is essentially solved, the ICI investment must shift entirely to ABR to unlock conversion."},
{"title":"Patient support program is known by name but not by substance",
 "data":"Familiarity with the support program averages 4.0 of 5, but average of 0.4 specific programs known by name.",
 "source":"Summary: Trial, Avg: S2_885",
 "why":"Brand awareness without programme substance is the fingerprint of a missed access conversation — ABR should be at 70+ but is averaging 51."},
{"title":"Reimbursement information was explicitly requested in qualitative interviews",
 "data":"62% of cluster respondents flagged reimbursement / Prior Authorization as their top unmet need.",
 "source":"Summary: Trial, Avg: S2_885 (qualitative)",
 "why":"An explicit, voiced request that goes unmet across multiple visits is the single strongest leading indicator of churn risk — even with high clinical conviction."},
],
"dim_scores":{"AC":65,"IBC":83,"MBC":44,"RTC":65,"ABR":28,"KCC":63,"CI":38},
"seg_spec":{"Neuro-Oncology":10,"Medical Oncology":7,"Hematology-Oncology":7},
"seg_sett":{"Academic":11,"Integrated Network":6,"Community":7},
"seg_load":{"Low":8,"Medium":9,"High":7},
},
3:{
"headline":"Diagnose the misbelief. Answer with data.",
"trigger":"Misbelief (e.g., relapse sooner, safety concern)",
"quote":"I'm worried patients on Product X relapse sooner. No one has shown me data that says otherwise.",
"quote_attr":"Composite Voice · Hematology-Oncology · Integrated Network",
"pet_findings":[
{"title":"Top-line efficacy is being delivered — depth is not",
 "data":"Average of 3 efficacy slides shown per visit, but 0 subgroup or long-term follow-up slides.",
 "source":"Summary: PET, S3_485",
 "why":"Without depth commitment, attribute perception cannot shift on the specific misbelief — Message — Belief Conversion (MBC) averages 16 in this cluster."},
{"title":"Attribute perception score change is essentially zero",
 "data":"0 of 5 perception attributes show a net shift after the visit — all below the 4-attribute threshold for narrative impact.",
 "source":"Summary: PET, S3_485",
 "why":"Mid-range motivation across many messages is worse than high motivation on one — MBC only converts when one message dominates."},
{"title":"Visit duration is short relative to data complexity",
 "data":"Average visit duration in this cluster is 11 minutes — below the 16-minute median needed for nuanced data discussion.",
 "source":"Summary: PET, S3_485 | + more interactions",
 "why":"Time pressure forces the rep into headlines, which reinforces the misbelief rather than resolving it."},
],
"atu_findings":[
{"title":"Clinical belief alignment shows a specific divergence",
 "data":"Average clinical belief alignment of 4.5 of 7 — driven by a single low-scoring statement (relapse timing).",
 "source":"Summary: Trial, Avg: S3_885",
 "why":"Alignment is uniformly mid-range except for one statement; that statement is the conversion blocker — surgical correction, not built-in re-education."},
{"title":"Doctors prefer information sources outside the rep channel",
 "data":"Rep is rated as a preferred information source by 16% of this cluster vs. 61% for peer publications and 77% for guidelines.",
 "source":"Summary: Trial, Avg: S3_885",
 "why":"Low rep-as-source preference depresses Rep Trust Conversion (RTC, 15% of ICI) — even correct data delivered by the rep gets discounted unless it matches a trusted external source."},
{"title":"Competitor framing is doing the heavy lifting on the doubt",
 "data":"70% of cluster mentions a competitor's relapse / overall-survival framing in the open-ended interview.",
 "source":"Summary: Trial, Avg: S3_885 (qualitative)",
 "why":"The misbelief is not random — it's actively reinforced by Competitive Influence (CI). Field responses must explicitly counter the competitor frame, not just present own data."},
],
"dim_scores":{"AC":68,"IBC":61,"MBC":29,"RTC":59,"ABR":68,"KCC":52,"CI":46},
"seg_spec":{"Hematology-Oncology":9,"Neuro-Oncology":6,"Medical Oncology":5},
"seg_sett":{"Community":12,"Integrated Network":5,"Academic":3},
"seg_load":{"Medium":10,"High":6,"Low":4},
},
4:{
"headline":"The belief is shallow. Build a story that sticks.",
"trigger":"Low message recall + weak attribute shift",
"quote":"If you asked me to describe Product X in one sentence, I'm not sure I could. Different rep visits, different stories.",
"quote_attr":"Composite Voice · Medical Oncology · Community Setting",
"pet_findings":[
{"title":"Rep narrative rotates, instead of reinforces",
 "data":"Average of 4.2 distinct opening messages used across the last 5 visits — the same doctor heard a different lead message each time.",
 "source":"Summary: PET, S4_485",
 "why":"Narrative inconsistency suppresses Awareness Conversion (AC, 14% of ICI) — repetition of the same hook is needed to build front-of-mind status."},
{"title":"Top motivating message score is mid-range, not high",
 "data":"Average motivating score of recalled messages is 5.0 of 7 — none cross the 4.0 threshold that signals a sticky narrative.",
 "source":"Summary: PET, S4_485",
 "why":"Mid-range motivation across many messages is worse than high motivation on one — Message — Belief Conversion (MBC) only converts when one message dominates."},
{"title":"Visual aid mix is broad and shallow",
 "data":"Average of 6 of 10 visual-aid types deployed per visit, but no single aid recalled by more than 22% of doctors.",
 "source":"Summary: PET, S4_485 | S4_885",
 "why":"Broad shallow exposure suppresses durable narrative formation — the field needs a single repeated visual anchor, not a deck rotation."},
],
"atu_findings":[
{"title":"Brand attribute scores are clustered in the middle of the range",
 "data":"Doctor-reported product performance averages 4.5 of 7 across all 16 attributes — no peaks, no troughs.",
 "source":"Summary: Trial, Avg: S4_885",
 "why":"Uniformly mid-range scores mean the doctor has no clear story for the brand. This is the textbook signature of a Narrative Building Opportunity."},
{"title":"Spontaneous recall is present, but unaided association is generic",
 "data":"92% spontaneous brand recall, but only 25% can name a specific differentiating attribute unprompted.",
 "source":"Summary: Trial, Avg: S4_885",
 "why":"Recall without association is the diagnostic for shallow narrative — Awareness Conversion (AC) registers, but Message — Belief Conversion (MBC) doesn't follow through."},
{"title":"Peer Key Opinion Leader exposure is low",
 "data":"Only 15% of cluster has attended a peer-led speaking event in the last 12 months.",
 "source":"Summary: Trial, Avg: S4_885 (channel)",
 "why":"Without peer voice reinforcement, the brand story has only the rep as a source — narrative durability requires a multi-channel echo, not a single-channel repetition."},
],
"dim_scores":{"AC":55,"IBC":59,"MBC":41,"RTC":60,"ABR":61,"KCC":53,"CI":42},
"seg_spec":{"Medical Oncology":8,"Neuro-Oncology":8,"Hematology-Oncology":6},
"seg_sett":{"Integrated Network":10,"Academic":5,"Community":7},
"seg_load":{"Low":9,"Medium":7,"High":6},
},
5:{
"headline":"Protect the franchise. Turn them into a voice.",
"trigger":"All gates cleared, durable intent + behavior",
"quote":"I'm already prescribing. Stop pitching me. Invite me into the conversation — the pipeline, the next readout, the science.",
"quote_attr":"Composite Voice · Neuro-Oncology · Academic Setting",
"pet_findings":[
{"title":"Standard sales aids dominate the rep bag — pipeline content is absent",
 "data":"Average of 1 of 10 visual-aid types used are future-state assets. 0 of 10 are pipeline / next-readout assets.",
 "source":"Summary: PET, S5_485",
 "why":"Over-visiting saturated prescribers signals mis-allocation of field time. Return on Visit declines once Intent — Behavior Conversion (IBC, 25% of ICI) is at ceiling."},
{"title":"Visit cadence is identical to non-converted clusters",
 "data":"Average 6.2 visits per quarter — same as Patient Identification Priority cluster — but conversion is already saturated.",
 "source":"Summary: PET, S5_485",
 "why":"Over-visiting saturated prescribers signals mis-allocation of field time. The optimization frontier has moved to channel and advocacy."},
{"title":"Peer-sharing behaviour is high but unstructured",
 "data":"80% of cluster shared product information with at least 2 peers post-visit, but 0% have a formal speaker / advisory role.",
 "source":"Summary: PET, S5_485",
 "why":"Latent advocacy is present and unactivated — converting peer-sharing into a structured channel multiplies Rep Trust Conversion (RTC) at peer-network scale."},
],
"atu_findings":[
{"title":"Prescribing volume is at the top of the panel",
 "data":"Average 9.1 of 10 future intent. Current Product X share of eligible patients averages 65%.",
 "source":"Summary: Trial, Avg: S5_885 | S5_885",
 "why":"When IBC is at ceiling, additional efficacy messaging has zero marginal lift — the optimization frontier has moved to channel and advocacy."},
{"title":"Information-source preference includes the rep, but with caveats",
 "data":"67% of cluster lists the rep as a preferred source — but only when paired with peer Key Opinion Leader content.",
 "source":"Summary: Trial, Avg: S5_885",
 "why":"The rep has earned channel trust (RTC), but the channel is now expected to deliver peer-grade content — not entry-level brand assets."},
{"title":"Competitive vigilance is high — and unaddressed",
 "data":"76% of cluster checked at least one competitor data point in the last 60 days that gave them pause.",
 "source":"Summary: Trial, Avg: S5_885 (qualitative)",
 "why":"Conviction is durable but not invulnerable — Competitive Influence (CI) creeps fastest in this cluster because doctors here track the field actively."},
],
"dim_scores":{"AC":85,"IBC":89,"MBC":82,"RTC":84,"ABR":80,"KCC":85,"CI":72},
"seg_spec":{"Medical Oncology":6,"Neuro-Oncology":4,"Hematology-Oncology":2},
"seg_sett":{"Integrated Network":6,"Community":6,"Academic":4},
"seg_load":{"Low":3,"Medium":7,"High":6},
},
}


def _finding_card(f, side_color, idx):
    """Render one PET or ATU finding card with all sub-sections."""
    st.markdown(f"""
<div style="background:white;border:1px solid {MGRAY};border-radius:12px;padding:16px 18px;margin-bottom:12px">
  <div style="font-size:13px;font-weight:600;color:#0F172A;margin-bottom:10px">◉ {f['title']}</div>
  <div style="margin-bottom:8px">
    <div style="font-size:9px;text-transform:uppercase;letter-spacing:.18em;color:#94A3B8;font-weight:600;margin-bottom:3px">WHAT THE DATA READS</div>
    <div style="font-size:12px;color:#475569;line-height:1.5">{f['data']}</div>
    <div style="font-size:10px;color:#94A3B8;font-style:italic;margin-top:3px">Source: {f['source']}</div>
  </div>
  <div style="padding-top:8px;border-top:1px solid #F1F5F9">
    <div style="font-size:9px;text-transform:uppercase;letter-spacing:.18em;color:{side_color};font-weight:700;margin-bottom:4px">WHY THIS CONNECTS TO USAGE INTENT & BEHAVIOUR</div>
    <div style="font-size:12px;color:#334155;line-height:1.6">{f['why']}</div>
  </div>
</div>
""", unsafe_allow_html=True)


def _dim_bars(scores, color):
    for key, name, weight in DIMS:
        val = scores.get(key, 50)
        fill = GREEN if val >= 70 else TEAL if val >= 50 else CRIMSON
        st.markdown(f"""
<div style="display:flex;align-items:center;gap:12px;margin-bottom:12px">
  <div style="width:180px;flex-shrink:0">
    <div style="font-size:12px;font-weight:500;color:#0F172A">{name} <span style="color:#CBD5E1">({key})</span></div>
    <div style="font-size:9px;color:#CBD5E1;text-transform:uppercase;letter-spacing:.12em">{weight}% weight</div>
  </div>
  <div style="flex:1;height:8px;background:#F1F5F9;border-radius:99px;overflow:hidden">
    <div style="width:{val}%;height:100%;background:{fill};border-radius:99px"></div>
  </div>
  <div style="width:32px;text-align:right;font-family:'DM Serif Display',serif;font-size:18px;font-weight:300;color:#0F172A">{val}</div>
</div>
""", unsafe_allow_html=True)


def _seg_mini(spec, sett, load):
    def bars(d, total):
        for k, v in sorted(d.items(), key=lambda x: -x[1]):
            pct = round(v / max(total, 1) * 100)
            st.markdown(f"""
<div style="display:flex;align-items:center;gap:8px;margin-bottom:5px">
  <div style="width:110px;font-size:11px;color:#475569;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{k}</div>
  <div style="flex:1;height:6px;background:#F1F5F9;border-radius:99px;overflow:hidden">
    <div style="width:{pct}%;height:100%;background:{TEAL};border-radius:99px"></div>
  </div>
  <div style="width:20px;font-size:11px;color:#94A3B8;text-align:right">{v}</div>
</div>
""", unsafe_allow_html=True)

    total_spec = sum(spec.values())
    total_sett = sum(sett.values())
    total_load = sum(load.values())
    st.markdown('<div style="font-size:10px;text-transform:uppercase;letter-spacing:.2em;color:#94A3B8;font-weight:600;margin:0 0 6px">SPECIALTY</div>', unsafe_allow_html=True)
    bars(spec, total_spec)
    st.markdown('<div style="font-size:10px;text-transform:uppercase;letter-spacing:.2em;color:#94A3B8;font-weight:600;margin:10px 0 6px">SETTING</div>', unsafe_allow_html=True)
    bars(sett, total_sett)
    st.markdown('<div style="font-size:10px;text-transform:uppercase;letter-spacing:.2em;color:#94A3B8;font-weight:600;margin:10px 0 6px">PATIENT LOAD</div>', unsafe_allow_html=True)
    bars(load, total_load)


def render(cid, hcps, eng):
    c = CLUSTER_CONTENT[cid]
    color = CLUSTER_COLORS[cid]
    n_hcps = int((hcps["cluster"] == cid).sum()) if hcps is not None and "cluster" in hcps.columns else c.get("hcps_n_default", 0)
    avg_ici = round(hcps[hcps["cluster"]==cid]["ICI"].mean(), 1) if hcps is not None and len(hcps[hcps["cluster"]==cid]) > 0 else c["dim_scores"].get("ICI_avg", 55)

    # Use real dim scores from data if available, else use content defaults
    if hcps is not None and len(hcps[hcps["cluster"]==cid]) > 0:
        sub = hcps[hcps["cluster"]==cid]
        dim_scores = {key: round(sub[key].mean(), 1) for key, _, _ in DIMS if key in sub.columns}
    else:
        dim_scores = c["dim_scores"]

    # Back button
    if st.button("← Back to overview", key=f"back_{cid}"):
        st.session_state["view"] = "overview"; st.rerun()

    # ── Hero card ──
    st.markdown(f"""
<div style="background:linear-gradient(135deg,{color},{color}CC);border-radius:20px;padding:36px;
            color:white;position:relative;overflow:hidden;margin-bottom:24px;min-height:220px">
  <div style="position:absolute;top:-40px;right:-40px;width:200px;height:200px;border-radius:50%;
              background:rgba(255,255,255,.08)"></div>
  <div style="position:absolute;bottom:-60px;right:40px;width:280px;height:280px;border-radius:50%;
              background:rgba(255,255,255,.05)"></div>
  <!-- Doctor avatar (right side) -->
  <div style="position:absolute;right:36px;top:50%;transform:translateY(-50%);text-align:center">
    <div style="position:relative;display:inline-block">
      <div style="position:absolute;inset:-8px;border-radius:50%;border:2px solid rgba(255,255,255,.3)"></div>
      <img src="{AVATARS[cid]}" style="width:140px;height:140px;border-radius:50%;object-fit:cover;
               border:4px solid rgba(255,255,255,.4)" onerror="this.style.display='none'">
      <div style="position:absolute;bottom:-10px;left:50%;transform:translateX(-50%);
                  background:rgba(255,255,255,.2);backdrop-filter:blur(8px);
                  border-radius:999px;padding:3px 10px;font-size:9px;font-weight:700;
                  text-transform:uppercase;letter-spacing:.15em;color:white;white-space:nowrap">
        State {cid}
      </div>
    </div>
  </div>
  <div style="max-width:65%">
    <div style="font-size:10px;text-transform:uppercase;letter-spacing:.2em;
                color:rgba(255,255,255,.6);font-weight:600;margin-bottom:8px">
      STATE 0{cid} · {CLUSTER_NAMES[cid].upper()}
    </div>
    <h1 style="font-family:'DM Serif Display',serif;font-size:36px;font-weight:400;
               color:white;line-height:1.1;margin-bottom:16px">{c['headline']}</h1>
    <!-- Quote block -->
    <div style="background:rgba(255,255,255,.15);border-radius:12px;padding:14px 18px;
                border-left:3px solid rgba(255,255,255,.4);margin-bottom:18px;max-width:460px">
      <div style="font-size:13px;font-style:italic;line-height:1.6;color:white">
        "{c['quote']}"
      </div>
      <div style="font-size:10px;text-transform:uppercase;letter-spacing:.18em;
                  opacity:.6;margin-top:6px;font-style:normal">
        — {c['quote_attr']}
      </div>
    </div>
    <!-- Stats row -->
    <div style="display:flex;gap:40px">
      <div>
        <div style="font-size:10px;text-transform:uppercase;letter-spacing:.2em;opacity:.7;font-weight:600">HCPs IN THIS STATE</div>
        <div style="font-family:'DM Serif Display',serif;font-size:36px;font-weight:300;line-height:1">{n_hcps}</div>
      </div>
      <div>
        <div style="font-size:10px;text-transform:uppercase;letter-spacing:.2em;opacity:.7;font-weight:600">AVG ICI SCORE</div>
        <div style="font-family:'DM Serif Display',serif;font-size:36px;font-weight:300;line-height:1">{avg_ici}<span style="font-size:16px;opacity:.6">/100</span></div>
      </div>
      <div>
        <div style="font-size:10px;text-transform:uppercase;letter-spacing:.2em;opacity:.7;font-weight:600">TRIGGER</div>
        <div style="font-size:16px;font-weight:600;opacity:.9;margin-top:4px;line-height:1.2">{c['trigger']}</div>
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    # ── PET vs ATU section header ──
    st.markdown(f"""
<div style="margin:20px 0 14px">
  <div style="font-size:11px;color:#64748B;margin-bottom:6px">WHAT THE DATA IS READING</div>
  <h2 style="font-family:'DM Serif Display',serif;font-size:22px;color:#0F172A">
    <span style="background:{NAVY};color:white;padding:2px 8px;border-radius:4px;font-size:12px;font-family:Inter,sans-serif;font-weight:700">PET</span>
    &nbsp;Promotional Effectiveness Tracker — what the rep visit delivered
    &nbsp;<span style="font-size:14px;color:#94A3B8">vs.</span>&nbsp;
    Awareness Trial Usage — what the doctor reported wanting&nbsp;
    <span style="background:{TEAL};color:white;padding:2px 8px;border-radius:4px;font-size:12px;font-family:Inter,sans-serif;font-weight:700">ATU</span>
  </h2>
</div>
""", unsafe_allow_html=True)

    lc, rc = st.columns(2)
    with lc:
        st.markdown(f'<span style="background:{NAVY};color:white;padding:2px 8px;border-radius:4px;font-size:9px;font-weight:700;display:inline-block;margin-bottom:10px">PET · Promotional Effectiveness Tracker — what the rep visit delivered</span>', unsafe_allow_html=True)
        for i, f in enumerate(c["pet_findings"]):
            _finding_card(f, NAVY, i)
    with rc:
        st.markdown(f'<span style="background:{TEAL};color:white;padding:2px 8px;border-radius:4px;font-size:9px;font-weight:700;display:inline-block;margin-bottom:10px">ATU · Awareness Trial Usage — what the doctor reported wanting</span>', unsafe_allow_html=True)
        for i, f in enumerate(c["atu_findings"]):
            _finding_card(f, TEAL, i)

    # ── ICI Profile + Segment Mix ──
    st.markdown("<br>", unsafe_allow_html=True)
    pc, sc = st.columns([3, 2])
    with pc:
        st.markdown(f"""
<div style="background:white;border:1px solid {MGRAY};border-radius:14px;padding:20px">
  <div style="font-size:10px;text-transform:uppercase;letter-spacing:.2em;color:{DGRAY};font-weight:600;margin-bottom:2px">INTERACTION CONVERSION INDEX PROFILE</div>
  <div style="font-size:14px;font-weight:600;color:#0F172A;margin-bottom:2px">Average across this state</div>
  <div style="font-size:10px;color:#94A3B8;margin-bottom:16px">Each dimension shown with its full name and short code</div>
</div>
""", unsafe_allow_html=True)
        _dim_bars(dim_scores, color)

    with sc:
        # Use real segment data if available
        if hcps is not None and len(hcps[hcps["cluster"]==cid]) > 0:
            sub = hcps[hcps["cluster"]==cid]
            seg_spec = sub["specialty"].value_counts().to_dict()
            seg_sett = sub["setting"].value_counts().to_dict()
            seg_load = sub["load"].value_counts().to_dict()
        else:
            seg_spec = c["seg_spec"]
            seg_sett = c["seg_sett"]
            seg_load = c["seg_load"]

        st.markdown(f'<div style="font-size:10px;text-transform:uppercase;letter-spacing:.2em;color:#94A3B8;font-weight:600;margin-bottom:10px">SEGMENT MIX · Who sits in this state</div>', unsafe_allow_html=True)
        _seg_mini(seg_spec, seg_sett, seg_load)

    # ── HCP Roster ──
    st.markdown("<br>", unsafe_allow_html=True)
    if hcps is not None and "cluster" in hcps.columns:
        sub = hcps[hcps["cluster"] == cid]
        if not sub.empty:
            st.markdown(f"""
<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px">
  <div style="font-size:10px;text-transform:uppercase;letter-spacing:.2em;color:#94A3B8;font-weight:600">ROSTER</div>
  <div style="font-size:11px;color:#94A3B8">{len(sub)} HCPs</div>
</div>
<div style="font-size:14px;font-weight:600;color:#0F172A;margin-bottom:8px">Healthcare Professionals currently in this state</div>
<div style="display:flex;padding:6px 0;border-bottom:1px solid {MGRAY};font-size:10px;text-transform:uppercase;letter-spacing:.15em;color:#94A3B8;font-weight:600">
  <div style="flex:2">HEALTHCARE PROFESSIONAL</div>
  <div style="flex:1">SPECIALTY</div>
  <div style="flex:1">SETTING</div>
  <div style="flex:1">PATIENT LOAD</div>
  <div style="width:48px;text-align:right">ICI</div>
</div>
""", unsafe_allow_html=True)
            for _, row in sub.head(10).iterrows():
                ic = GREEN if row["ICI"] >= 70 else TEAL if row["ICI"] >= 50 else CRIMSON
                st.markdown(f"""
<div style="display:flex;align-items:center;padding:10px 0;border-bottom:1px solid #F1F5F9;font-size:13px">
  <div style="flex:2">
    <div style="font-weight:600;color:#0F172A">HCP-{int(row['uid'])}</div>
    <div style="font-size:10px;color:#94A3B8">{row['uid']}</div>
  </div>
  <div style="flex:1;color:#475569">{row.get('specialty','—')}</div>
  <div style="flex:1;color:#475569">{row.get('setting','—')}</div>
  <div style="flex:1;color:#475569">{row.get('load','—')}</div>
  <div style="width:48px;text-align:right;font-family:'DM Serif Display',serif;font-size:20px;color:{ic}">{round(row['ICI'],0):.0f}</div>
</div>
""", unsafe_allow_html=True)
            if len(sub) > 10:
                st.markdown(f'<div style="text-align:center;padding:10px;font-size:11px;color:#94A3B8">+ {len(sub)-10} more</div>', unsafe_allow_html=True)

    # ── CTA ──
    st.markdown(f"""
<div style="background:linear-gradient(135deg,{color}14,{color}08);border:1px solid {color}33;
            border-radius:16px;padding:18px 24px;margin-top:24px;
            display:flex;align-items:center;justify-content:space-between">
  <div>
    <div style="font-size:10px;text-transform:uppercase;letter-spacing:.2em;color:{color};font-weight:700;margin-bottom:4px">
      WANT THE FIELD PLAY FOR THIS STATE?
    </div>
    <div style="font-size:15px;font-weight:500;color:#0F172A">
      Generate a custom doctor rep support card filtered to your specialty, setting, and patient load.
    </div>
  </div>
</div>
""", unsafe_allow_html=True)
    if st.button("Open the custom rep card →", key=f"cta_card_{cid}"):
        st.session_state["view"] = "envelope"; st.rerun()
