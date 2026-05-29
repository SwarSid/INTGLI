"""Approach view — full methodology with 6 PET→ATU chains, ICI architecture, sequential clustering."""
import streamlit as st
TEAL="#0F4C5C"; NAVY="#1E293B"; CRIMSON="#832232"; AMBER="#B8860B"; GREEN="#15803D"; MGMT="#E2E8F0"; DGRAY="#64748B"; LGRAY="#F8FAFC"

DIMS=[("AC","Awareness Conversion",14,CRIMSON,"How deeply is Voranigo in the HCP's treatment vocabulary?","PET Q2.10Z msg recall · ATU Q2.20Z familiarity · ATU Q2.10Z unaided voice"),
      ("IBC","Intent → Behavior",25,NAVY,"Does stated prescribing intent convert to real patient share?","PET Q3.35Z LTIP · ATU Q3.60a current patients · ATU Q3.60b future intent"),
      ("MBC","Message → Belief",20,CRIMSON,"Did recalled messages shift the clinical beliefs that drive prescribing? (VA reinforcement embedded here)","PET Q2.10Z recall · PET Q5.00Z believability · ATU Q3.120Z perf ratings · ATU Q3.110Z importance"),
      ("RTC","Rep Trust",13,TEAL,"Did the interaction build durable rep credibility that outlasts the call?","PET Q3.70Z call quality · PET Q6.20Z trusted partner · ATU Q4.30Z preferred source"),
      ("ABR","Access Barrier Resolution",15,NAVY,"Did the interaction actually reduce access friction? (Access VA types embedded here)","PET Q1.100Z access VAs · ATU Q3.260A/B ServierONE · ATU Q3.220Z barriers"),
      ("KCC","Knowledge & Classification",8,GREEN,"Did DSE close the knowledge gaps that block confident prescribing?","PET Q1.16Z DSE value · PET Q3.45Z WHO confidence · ATU Q4.00Z beliefs · ATU Q1.00Z NGS rate"),
      ("CI","Competitive Influence",5,AMBER,"How does Voranigo perform vs alternatives on what matters most to THIS HCP?","ATU Q3.120Z vs TMZ/RT · ATU Q2.20Z competitor familiarity · ATU Q3.160Z qual framing")]

CHAINS = [
    ("Chain 1","Awareness → Familiarity → Consideration",TEAL,
     "Did the interaction move Voranigo from peripheral to front-of-mind?",
     [("PET Q2.00","What are the primary messages you recall hearing during your most recent interaction with the Servier sales rep while discussing Voranigo for gliomas? [Voice response — unaided]",
       "ATU Q2.10Z","First, what treatments come to mind when thinking of treating IDH-mutant astrocytoma or oligodendroglioma patients? [Voice response — unaided]",
       "Does Voranigo appear unprompted in ATU treatment recall among HCPs who recalled it clearly in PET? Linguistic overlap signals genuine message internalization."),
      ("PET Q1.110","Which of the following topics were discussed during your most recent interaction? [Topics: Efficacy / Safety / Indication / Dosing / Tolerability / Patient types / MoA / Access / NCCN Guidelines / WHO Classification / Molecular testing / Disease state education]",
       "ATU Q2.20Z (Voranigo row)","How familiar are you with Voranigo as a treatment for IDH-mutant astrocytoma or oligodendroglioma? [Scale: Never heard → Heard but don't know → Familiar not planning → Planning no opportunity → Have used]",
       "Which topic combinations in PET correlate with higher familiarity in ATU? Topic breadth may matter more than any single topic.")]),
    ("Chain 2","LTIP → Actual Prescribing Behavior",NAVY,
     "Does stated prescribing intent convert to real patient share — and when it doesn't, why not?",
     [("PET Q3.30Z / Q3.35Z","Prior to your most recent interaction, please rate your likelihood to prescribe Voranigo [1=Not at all likely → 7=Extremely likely] / How likely are you to INCREASE prescribing based on your most recent interaction? [1=Not at all likely → 7=Extremely likely]",
       "ATU Q3.60a","How many of your patients of this type are currently receiving Voranigo? [Across all 12 patient types: Adjuvant GTR Astro / Adjuvant STR Astro / Adjuvant GTR Oligo / Adjuvant STR Oligo / Stable observed GTR Astro / Stable observed STR Astro / Stable observed GTR Oligo / Stable observed STR Oligo / Recurrent after observation / Maintenance post-RT/CT / Stable post-systemic therapy / Recurrent after systemic therapy]",
       "The LTIP-to-usage conversion rate. High LTIP + Non-User is the most strategically important group — they said yes to the rep but didn't follow through."),
      ("PET Q3.35A/B","You were very likely to prescribe Voranigo — please explain why in as much detail as possible. [Voice — shown if Q3.35Z ≥ 6] / You were not likely to prescribe Voranigo — please explain why. [Voice — shown if Q3.35Z ≤ 5]",
       "ATU Q3.220a / Q3.60c","What are your main barriers to prescribing Voranigo for mIDH astrocytoma or oligodendroglioma patients? [Voice — AI probe, max 2 follow-ups] / How do patient types influence your treatment decision? [Voice — AI follow-up probing on patient types]",
       "The single most diagnostic pairing in the dataset. PET explains stated intent. ATU reveals actual barriers. The gap between them is what reps are not addressing.")]),
    ("Chain 3","Message Recall → Belief Shift → Clinical Decision-Making",CRIMSON,
     "Did specific recalled messages move specific clinical beliefs?",
     [("PET Q2.10Z (all messages)","Which of these messages do you specifically recall hearing? [V1: Indication / V2: First new treatment >20 years / V3: Dual mIDH1/2 inhibitor / V5: PFS 61%/65% reduction / V6: TTNI 74% reduction / V8: Discontinuation 3.6% / V9: ALT 10% / AST 4.8% / V12: TGR −1.3% vs +14.4% / V13: Seizure rate 64% lower / V14: NCCN preferred adjuvant and recurrent]",
       "ATU Q3.120Z (Voranigo column)","How would you rate Voranigo as an adjuvant or first-line treatment on each attribute? [1=Very poor → 7=Excellent] [Attributes: PFS / Tumor volume / OS / Grade 3-4 AEs / Hepatic toxicity / Hematological toxicity / Neurotoxicity / Hypermutation risk / LFT monitoring / QoL / Affordability / Patient services / Ease of prescribing / Route / Long-term SEs / Fertility / Delays next treatment / Seizure reduction / Office compensation]",
       "Message-to-attribute performance linkage. Recalling V13 (seizure) should correlate with higher seizure reduction rating. Where recall is high but attribute rating is low — the message is heard but not believed."),
      ("PET Q5.00Z","How differentiated / believable / motivating is each Voranigo message? [1=Not at all → 7=Extremely; for all 10 messages]",
       "ATU Q3.220","Which of the following are the main barriers to prescribing Voranigo? [Institutional protocols / Prior auth / Transition of care / Limited experience / Cost and insurance / Side-effect profile / Liver toxicity monitoring / Lack of long-term data / Off-label uncertainty / Need for molecular testing / Patient age and comorbidities / Lack of caregiver support / Patient preference for established therapies]",
       "Does finding a message motivating in PET actually reduce the corresponding barrier in ATU? Finding V14 NCCN motivating but still citing institutional protocols means the NCCN message needs to change the pathway, not just inform the HCP.")]),
    ("Chain 4","Rep Quality → Trust → Information Ecosystem",TEAL,
     "Does a high-quality interaction change where HCPs go for information?",
     [("PET Q3.70Z / Q6.20Z","Rate the Servier rep: overall call quality / preparedness / organisation / indication knowledge / time use [1=Performed poorly → 7=Performed extremely well] / Servier rep is Best in Class / trusted partner / able to engage meaningfully / trusted source for glioma data / listens and reflects [1=Strongly disagree → 7=Strongly agree]",
       "ATU Q4.30Z","In the past 6 months, where have you seen or heard information on IDH-mutant astrocytoma? Where do you prefer to get information? [In-person rep discussion / Virtual rep discussion / Journal publication / Conference / CME / Colleague / Manufacturer website / Other website / Email from reps / Email from societies / NCCN / UpToDate / Opinion leaders]",
       "Does experiencing a high-quality rep interaction predict preferring rep interactions as an information source in ATU? What 'quality' means to this HCP is in the voice response."),
      ("PET Q3.71A/B","You rated rep preparedness as Highly Prepared — what specific aspects led you to rate them this way vs differently? [Voice] / You rated rep preparedness as Not Highly Prepared — what specific aspects could be improved? [Voice]",
       "ATU Q3.300Z / Q3.310Z","How often do patients ask about Voranigo as a treatment option? [Very often / Occasionally / Rarely / Never] / To what extent does patient inquiry influence your decision to prescribe? [Significantly increases / Somewhat increases / No impact / Decreases / N/A]",
       "Does rep trust create an educational ripple effect — HCPs who trust the rep discuss Voranigo more openly with patients, which generates patient inquiry, which reinforces prescribing behavior?")]),
    ("Chain 5","Access & ServierONE Discussion → Barrier Resolution",AMBER,
     "Did discussing access and support actually reduce coverage and cost barriers?",
     [("PET Q1.200 / Q1.210","What was discussed about patient support services (e.g. copay) during your most recent interaction? [Voice] / What additional information about patient support services would you like to discuss in future interactions? [Voice]",
       "ATU Q3.260A / Q3.260B","How familiar are you with the ServierOne Patient Support Program? [5=Extremely familiar → 1=Not at all familiar] / Which ServierONE services are you aware of? [Commercial Co-Pay / Bridge Program / PAP / QuickStart / LOA Templates / Not aware of any]",
       "Does having a substantive patient support conversation in PET translate to ServierONE familiarity in ATU? An HCP whose PET voice describes a detailed copay discussion but who selects 'not aware of any ServierONE services' in ATU means the access conversation happened but wasn't anchored to the programme by name."),
      ("PET Q6.45Z / Q6.51Z","Which ServierONE services are you aware of? [same options] / Rate the effectiveness of ServierONE services [1=Not at all effective → 7=Extremely effective per service]",
       "ATU Q3.290 / Q3.230","What challenges have you faced with ServierOne? [Difficult to navigate / Unclear value / Lack of training / Limited patient benefit / Not integrated / None / Haven't used it] / Common insurance issues: [High cost / Step-through / PA rejection / Not on clinical pathways / Burdensome testing / Lack of manufacturer support / Lack of practice support]",
       "Does rating ServierONE as effective in PET predict fewer access barriers in ATU? Where a HCP used QuickStart and rated it effective in PET but still cites lack of manufacturer support in ATU — something happened between visits that needs investigation.")]),
    ("Chain 6","DSE Quality → Knowledge Gaps → Testing Behavior",GREEN,
     "Did disease state education in PET address the testing and diagnostic gaps visible in ATU?",
     [("PET Q1.15Z / Q1.16Z / Q1.17a","What proportion of call time was spent on Disease State Education vs Voranigo? [Force sum 100%] / How valuable did you find the DSE content? [1=Not at all → 7=Extremely valuable] / Please describe the gaps or unmet needs identified during the DSE discussion. [Voice — shown if DSE time > 0%]",
       "ATU Q1.00Z / Q4.00Z","What % of your newly diagnosed diffuse glioma patients are initially tested for IDH status with: IHC only / IHC+NGS / IHC+other / NGS only / Other testing? [Must sum 100%] / How strongly do you agree: IDH testing should be part of initial workup / IDH-mutant is a distinct WHO subtype / IHC-negative under 55 should get sequencing [1=Strongly disagree → 7=Strongly agree]",
       "Did DSE discussions in PET close the knowledge gaps visible in ATU testing behavior? An HCP who expresses uncertainty about IDH testing in PET voice but shows strong belief alignment in ATU — that DSE worked. Reverse pattern means the gap wasn't addressed."),
      ("PET Q3.45Z","Based on your most recent interaction, how confident are you in your ability to accurately classify gliomas based on current WHO guidelines (IDH status, 1p/19q codeletion, molecular markers)? [1=Not at all confident → 7=Very confident]",
       "ATU Q2.00Z / ATU Q4.10Z","How familiar are you with the v1.2025 NCCN CNS update published in June 2025? [Never heard → Very familiar] / How certain are you in the answers you just gave? [Completely uncertain → Completely certain]",
       "Does WHO classification confidence in PET predict stronger belief alignment in ATU? Four-step causal chain: NCCN discussed in PET → NCCN familiarity in ATU → NCCN-aligned clinical belief in ATU → Voranigo usage in ATU.")]),
]

CLUSTER_NAMES = {1:"Patient ID Priority", 2:"Intent-Led, Access-Pending", 3:"Evidence Gap", 4:"Narrative-Building Opportunity", 5:"Conviction-Led Prescriber"}
CLUSTER_COLORS = {1:TEAL, 2:NAVY, 3:CRIMSON, 4:AMBER, 5:GREEN}
CLUSTER_TRIGGERS = {
    1:("Low qualifying patient load (Grade 2 IDH-mutant ≤ 2) OR Voranigo familiarity ≤ 2/5",
       "All other interventions are premature — patient volume or awareness must come first",
       "Lead with patient identification protocol and IDH testing pathway, not product messaging"),
    2:("LTIP ≥ 5 in PET BUT current Voranigo patients = 0 in ATU AND access barriers cited OR access not discussed in PET",
       "Intent exists. The operational pathway to a prescription is blocked.",
       "Access conversation must be the centrepiece. Name every ServierONE programme by name."),
    3:("Importance-performance gap: attribute importance ≥ 6/7 AND Voranigo performance ≤ 4/7 on same attribute AND corrective message not recalled in PET",
       "A specific clinical objection has not been addressed or not been made credible.",
       "Open by acknowledging the specific evidence gap. Bring the data that directly addresses it."),
    4:("ATU qual voice contains uniqueness framing ('only approved', 'only available') AND IDH-class competitor familiarity ≥ 4/5 AND clinical outcome messages not recalled",
       "Conviction exists but is built on regulatory uniqueness, not clinical superiority. Fragile.",
       "Build a clinically-grounded narrative: TTNI, TGR, seizure reduction. Outcomes, not uniqueness."),
    5:("IBC high (current prescribing strong) AND ATU qual contains clinical superiority framing AND no dominant access or evidence blocker",
       "Interaction is converting effectively across most dimensions.",
       "Stop selling. Start partnering. New data, pipeline, peer activation, advisory."),
}


def render(eng):
    # Header
    st.markdown(f'<div style="font-size:10px;text-transform:uppercase;letter-spacing:.22em;color:#94A3B8;font-weight:600;margin-bottom:8px">HOW WE BUILT THIS · METHODOLOGY</div>', unsafe_allow_html=True)
    st.markdown(f"""
<h1 style="font-family:'DM Serif Display',serif;font-size:48px;font-weight:300;color:#0F172A;line-height:1.1;margin-bottom:12px">
  Three steps from <em style="color:{TEAL}">survey data</em><br>to a doctor-specific <span style="color:{CRIMSON}">field play.</span>
</h1>
<p style="font-size:14px;color:#475569;max-width:640px;line-height:1.65;margin-bottom:28px">
  We unify the ATU survey — what doctors say they want and intend — with the PET — what they remember from the rep visit. The two datasets meet in the Interaction Conversion Index (ICI), which sorts every HCP into one of five engagement states. The output is a custom doctor rep support card, generated purely from the data.
</p>
""", unsafe_allow_html=True)

    sc = st.columns(3)
    for col,(num,title,color) in zip(sc,[("STEP 01",f"Calculate the ICI",TEAL),("STEP 02","Cluster every doctor",CRIMSON),("STEP 03","Generate custom rep card",GREEN)]):
        with col: st.markdown(f'<div style="background:white;border:1px solid {MGMT};border-radius:14px;padding:20px;border-top:4px solid {color}"><div style="font-size:10px;text-transform:uppercase;letter-spacing:.2em;color:{color};font-weight:700;margin-bottom:6px">{num}</div><div style="font-size:15px;font-weight:600;color:#0F172A">{title}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ICI Dimensions
    st.markdown(f'<div style="font-size:10px;text-transform:uppercase;letter-spacing:.2em;color:{DGRAY};font-weight:600;margin-bottom:8px">STEP 01 · THE SEVEN DIMENSIONS</div>', unsafe_allow_html=True)
    lc, rc = st.columns(2)
    with lc:
        st.markdown(f'<div style="background:white;border:1px solid {MGMT};border-radius:14px;padding:20px">', unsafe_allow_html=True)
        for key,name,weight,color,plain,sources in DIMS:
            st.markdown(f'<div style="display:flex;align-items:flex-start;gap:12px;margin-bottom:14px;padding-bottom:14px;border-bottom:1px solid #F1F5F9"><div style="width:36px;height:36px;border-radius:8px;background:{color};display:flex;align-items:center;justify-content:center;color:white;font-size:11px;font-weight:700;flex-shrink:0">{key}</div><div style="flex:1"><div style="font-size:12px;font-weight:600;color:#0F172A">{name} <span style="color:#CBD5E1">({weight}% weight)</span></div><div style="font-size:11px;color:{DGRAY};margin-top:2px;line-height:1.4">{plain}</div><div style="font-size:10px;color:#94A3B8;margin-top:4px">{sources}</div></div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with rc:
        st.markdown(f'<div style="background:{NAVY};border-radius:14px;padding:20px;font-family:monospace;font-size:12px;line-height:2.2;color:white;margin-bottom:12px"><b style="font-size:14px;font-family:Inter,sans-serif">ICI Formula</b><br>ICI = AC × 0.14<br>    + IBC × 0.25<br>    + MBC × 0.20<br>    + RTC × 0.13<br>    + ABR × 0.15<br>    + KCC × 0.08<br>    + CI × 0.05</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="background:{LGRAY};border:1px solid {MGMT};border-radius:12px;padding:14px 16px;font-size:12px;color:#334155;line-height:1.6"><b>VA (Visual Aid)</b> is embedded inside MBC (content relevance + delivery channel match) and ABR (access-specific VA content types). It is not a standalone dimension.<br><br><b>CI (Competitive Influence)</b> is a standalone dimension measuring how Voranigo performs vs alternatives on what matters most to this specific HCP.</div>', unsafe_allow_html=True)

    # 6 Chains
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:10px;text-transform:uppercase;letter-spacing:.2em;color:{DGRAY};font-weight:600;margin-bottom:8px">THE SIX PET → ATU EVIDENCE CHAINS</div>', unsafe_allow_html=True)
    st.markdown(f'<p style="font-size:13px;color:#475569;max-width:700px;line-height:1.6;margin-bottom:16px">Each chain pairs a specific PET question with a specific ATU question. Together they answer: did the interaction address the factor that is actually driving or blocking this HCP\'s prescribing behavior?</p>', unsafe_allow_html=True)

    for chain_id, chain_name, color, intent, pairs in CHAINS:
        with st.expander(f"**{chain_id}: {chain_name}**"):
            st.markdown(f'<div style="font-size:13px;color:{DGRAY};font-style:italic;margin-bottom:12px">{intent}</div>', unsafe_allow_html=True)
            for pet_q, pet_text, atu_q, atu_text, link in pairs:
                st.markdown(f"""
<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px">
  <div style="background:#F8FAFC;border:1px solid {MGMT};border-radius:10px;padding:12px">
    <div style="font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.2em;color:{NAVY};margin-bottom:6px">PET {pet_q}</div>
    <div style="font-size:11px;color:#334155;line-height:1.5;font-style:italic">"{pet_text}"</div>
  </div>
  <div style="background:#F8FAFC;border:1px solid {MGMT};border-radius:10px;padding:12px">
    <div style="font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.2em;color:{TEAL};margin-bottom:6px">ATU {atu_q}</div>
    <div style="font-size:11px;color:#334155;line-height:1.5;font-style:italic">"{atu_text}"</div>
  </div>
</div>
<div style="background:{'#F0FDF4' if color==GREEN else '#EFF6FF' if color==TEAL else '#FFF7ED'};border-radius:8px;padding:10px 12px;margin-bottom:8px;font-size:12px;color:#334155;line-height:1.5;border-left:3px solid {color}">
  <b>What the link tests:</b> {link}
</div>
""", unsafe_allow_html=True)

    # Sequential clustering
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:10px;text-transform:uppercase;letter-spacing:.2em;color:{DGRAY};font-weight:600;margin-bottom:8px">STEP 02 · SEQUENTIAL CLUSTER ASSIGNMENT</div>', unsafe_allow_html=True)
    st.markdown(f'<p style="font-size:13px;color:#475569;max-width:700px;line-height:1.6;margin-bottom:16px">Clustering is not statistical — it is rule-based and sequential. We walk each HCP down a resolution tree. The first blocker that triggers wins, and the HCP is assigned to that cluster. This guarantees clinically interpretable cluster names and stops you from chasing the wrong gap.</p>', unsafe_allow_html=True)

    for cid in range(1,6):
        trigger, rationale, action = CLUSTER_TRIGGERS[cid]
        color = CLUSTER_COLORS[cid]
        st.markdown(f"""
<div style="display:flex;align-items:flex-start;gap:12px;padding:14px;margin-bottom:8px;background:white;border:1px solid {MGMT};border-radius:12px;border-left:4px solid {color}">
  <div style="width:28px;height:28px;border-radius:50%;background:{color};display:flex;align-items:center;justify-content:center;color:white;font-weight:700;font-size:12px;flex-shrink:0">{cid}</div>
  <div style="flex:1">
    <div style="font-size:10px;text-transform:uppercase;letter-spacing:.15em;color:{color};font-weight:700;margin-bottom:3px">{CLUSTER_NAMES[cid]}</div>
    <div style="font-size:12px;color:#0F172A;margin-bottom:3px"><b>Trigger:</b> {trigger}</div>
    <div style="font-size:12px;color:{DGRAY};margin-bottom:3px"><b>Why this blocker comes first:</b> {rationale}</div>
    <div style="font-size:12px;color:{TEAL}"><b>Field implication:</b> {action}</div>
  </div>
</div>
""", unsafe_allow_html=True)

    st.markdown(f'<div style="background:{LGRAY};border:1px solid {MGMT};border-radius:12px;padding:14px 18px;font-size:12px;color:#475569;line-height:1.6;margin-top:8px"><b>When an HCP triggers two clusters:</b> Apply Option C — sequential resolution. Assign the cluster whose blocker must be resolved first before the next can be addressed. Access before belief: even if a misperception were corrected, a prior auth denial still blocks the prescription. The secondary cluster is noted as a flag on the HCP card.</div>', unsafe_allow_html=True)
