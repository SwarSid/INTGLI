"""
Qualitative Analysis — ALL voice responses from ATU and PET.
Speaker B / Doctor responses extracted from AI interviews.
Theme coding with 12-theme rubric from methodology.
"""
import streamlit as st
import pandas as pd
import numpy as np
import re
from collections import Counter

TEAL="#0F4C5C"; NAVY="#1E293B"; CRIMSON="#832232"; AMBER="#B8860B"; GREEN="#15803D"
LGRAY="#F8FAFC"; MGRAY="#E2E8F0"; DGRAY="#64748B"

THEMES = {
    "OS data concern":             (CRIMSON, ["overall survival","os data","survival data","mature data","os result","long-term survival","overall survival data"]),
    "Relapse / progression concern":(NAVY,   ["relapse","progression","progress sooner","relapse sooner","recur","resistance","come back","grow back"]),
    "Liver / LFT burden":          (AMBER,   ["liver","lft","hepatic","alt","ast","ggt","enzyme","monitoring","transaminase","liver toxicity"]),
    "Insurance / PA barrier":      (CRIMSON, ["insurance","prior auth","pa","coverage","payer","denial","denied","formulary","approval","reimburse"]),
    "ServierONE unawareness":      (NAVY,    ["servierone","servier one","support program","copay","co-pay","patient assistance","quickstart","bridge program","pap","letter of medical"]),
    "Reimbursement / practice cost":(AMBER,  ["reimbursement","practice","cost","affordable","expense","j-code","infusion","compensation","office"]),
    "Patient selection uncertainty":(TEAL,   ["which patient","patient selection","appropriate patient","eligible","who to treat","patient criteria","select","identify patient"]),
    "Clinical superiority framing": (GREEN,  ["seizure","pfs","progression free","ttni","next intervention","tumor growth","tgr","64%","61%","74%","mechanism","idh","voranigo work"]),
    "Uniqueness framing":           (TEAL,   ["only","approved","available","no other","alternative","option","nothing else"]),
    "NCCN as primary driver":       (GREEN,  ["nccn","guideline","preferred","category","recommendation","protocol"]),
    "Patient volume / practice fit":(DGRAY,  ["don't see","few patient","rarely see","volume","practice","not common","specialist","refer","glioma patient"]),
    "Rep interaction value":        (NAVY,   ["representative","rep","servier","visit","interaction","improve","better","more information","discuss"]),
}

ATU_VR_QUESTIONS = [
    ("Q2_10Z", 130, "Unaided treatment recall",
     "What treatments come to mind when thinking of treating IDH-mutant astrocytoma or oligodendroglioma patients?",
     "ATU Q2_10Z — Open-end, unaided. Captures treatment vocabulary without any prompting."),
    ("Q3_60cZ", 407, "Patient type influence on treatment decision",
     "How do patient types influence your treatment decision for grade 2 IDH-mutant astrocytoma or oligodendroglioma?",
     "ATU Q3_60cZ — Open-end AI follow-up. Probes patient selection logic."),
    ("Q3_90Z", 431, "MRI monitoring practices",
     "Please elaborate on your MRI monitoring practices for these patients.",
     "ATU Q3_90Z — Open-end. Captures disease management intensity and monitoring behavior."),
    ("Q3_160Z", 571, "VORANIGO prescribing drivers (AI interview)",
     "What factors have the largest impact on your decision to prescribe VORANIGO (vorasidenib)?",
     "ATU Q3_160Z — ZoomRx AI moderator interview. Doctor responses extracted from full transcript."),
    ("Q3_220Z", 571, "Barriers to prescribing VORANIGO (AI interview)",
     "What prevents or creates hesitation for you when considering Voranigo for mIDH glioma patients?",
     "ATU Q3_220Z — ZoomRx AI moderator interview. Doctor responses (Speaker: Doctor) extracted."),
    ("Q3_330Z", 615, "Handling patient preference conflicts",
     "If a patient's treatment preference differs from your recommendation, how would you handle this?",
     "ATU Q3_330Z — Open-end. Captures shared decision-making approach and patient communication style."),
]

PET_VR_QUESTIONS = [
    ("C3_74Z", 220, "Interaction improvement feedback",
     "How could your interaction with the Servier representative for Voranigo have been improved?",
     "PET C3_74Z — Open-end AI follow-up. Unprompted rep interaction feedback."),
    ("Q1_200Z", 131, "Patient support services discussed",
     "What was discussed about patient support services (e.g. copay) during your most recent interaction?",
     "PET Q1_200Z — Open-end. Captures depth of ServierONE access conversation."),
    ("Q1_210Z", 132, "Additional patient support information needed",
     "What additional information about patient support services would you like to discuss in future interactions?",
     "PET Q1_210Z — Open-end. Direct unmet need statement from the HCP."),
]


def _clean_responses(raw_series, is_interview=False):
    """Extract clean responses. For interviews, extract Doctor/Speaker B turns only."""
    if raw_series is None:
        return pd.Series([], dtype=str)
    vals = raw_series.dropna().astype(str)

    if is_interview:
        # Extract all Doctor: ... turns from AI interview transcripts
        doctor_responses = []
        for text in vals:
            if len(text) < 50:
                continue
            # Find all Doctor / Speaker B responses
            patterns = [
                r'Doctor:\s*(.+?)(?=AI Moderator:|Doctor:|$)',
                r'Speaker B:\s*(.+?)(?=Speaker A:|Speaker B:|AI Moderator:|$)',
                r'HCP:\s*(.+?)(?=Moderator:|HCP:|$)',
            ]
            found = False
            for pat in patterns:
                matches = re.findall(pat, text, re.IGNORECASE | re.DOTALL)
                for m in matches:
                    clean = m.strip().replace('\n', ' ')
                    skip_phrases = ['start interview', 'stop interview', 'next question', 'click', 'please respond']
                    if len(clean) > 10 and not any(s in clean.lower() for s in skip_phrases):
                        doctor_responses.append(clean[:400])
                        found = True
            if not found and len(text) > 80 and 'AI Moderator' not in text and 'question aims' not in text:
                # Plain text response not in interview format
                clean = text.strip()[:400]
                if len(clean) > 15:
                    doctor_responses.append(clean)
        return pd.Series(doctor_responses)
    else:
        # Standard open-end
        filtered = vals[vals.str.len() > 15]
        skip = ['Long Free Text', '-N-', 'How do', 'How could', 'Please', 'Question', 'What treat',
                'What was discussed', 'If a patient', 'What factors', 'What preven']
        for s in skip:
            filtered = filtered[~filtered.str.contains(s, na=False, case=False)]
        return filtered[filtered.str.strip().str.len() > 0].reset_index(drop=True)


def _assign_themes(text):
    if not text or pd.isna(text):
        return []
    t = str(text).lower()
    return [name for name, (color, kws) in THEMES.items() if any(k in t for k in kws)] or ["Other"]


def _theme_badge(theme):
    color = THEMES.get(theme, (DGRAY, []))[0]
    return f'<span style="background:{color}22;color:{color};padding:2px 7px;border-radius:3px;font-size:9px;font-weight:700;white-space:nowrap">{theme}</span>'


def _render_vr_section(qcode, col_idx, title, full_question, source_note, raw_df, is_interview=False, is_pet=False):
    """Render one VR question section with all responses, themes, and stats."""
    col_series = raw_df[col_idx] if col_idx < len(raw_df.columns) else None
    responses = _clean_responses(col_series, is_interview=is_interview)

    # Filter to Speaker B (Doctor) only for interviews
    n_resp = len(responses)
    if n_resp == 0:
        return

    # Theme distribution
    all_themes = []
    for r in responses:
        all_themes.extend(_assign_themes(r))
    theme_counts = Counter(all_themes)
    total = sum(theme_counts.values()) or 1

    badge_color = TEAL if not is_pet else CRIMSON
    survey_label = "PET" if is_pet else "ATU"

    with st.expander(f"**{survey_label} {qcode} — {title}** · {n_resp} responses"):
        # Question header
        st.markdown(f"""
<div style="background:{LGRAY};border-radius:10px;padding:14px 16px;margin-bottom:16px;border-left:3px solid {badge_color}">
  <div style="font-size:9px;text-transform:uppercase;letter-spacing:.2em;color:{badge_color};font-weight:700;margin-bottom:4px">{survey_label} {qcode} · {n_resp} RESPONSES</div>
  <div style="font-size:14px;font-weight:600;color:#0F172A;margin-bottom:4px;font-style:italic">"{full_question}"</div>
  <div style="font-size:10px;color:#94A3B8">{source_note}</div>
</div>
""", unsafe_allow_html=True)

        # Theme distribution bar
        if theme_counts and "Other" not in list(theme_counts.keys())[:1]:
            top_themes = [(t, c) for t, c in theme_counts.most_common(8) if t != "Other"]
            if top_themes:
                st.markdown(f'<div style="font-size:10px;text-transform:uppercase;letter-spacing:.18em;color:{DGRAY};font-weight:600;margin-bottom:8px">THEME DISTRIBUTION</div>', unsafe_allow_html=True)
                cols_t = st.columns(min(len(top_themes), 4))
                for i, (theme, count) in enumerate(top_themes[:4]):
                    color = THEMES.get(theme, (DGRAY, []))[0]
                    pct = round(count / total * 100)
                    with cols_t[i]:
                        st.markdown(f"""
<div style="background:{color}15;border:1px solid {color}33;border-radius:8px;padding:10px;text-align:center">
  <div style="font-size:18px;font-weight:700;color:{color}">{pct}%</div>
  <div style="font-size:9px;color:{DGRAY};margin-top:2px;line-height:1.3">{theme}</div>
  <div style="font-size:9px;color:#94A3B8">{count} mentions</div>
</div>
""", unsafe_allow_html=True)

        # All responses in a scrollable list
        st.markdown(f'<div style="font-size:10px;text-transform:uppercase;letter-spacing:.18em;color:{DGRAY};font-weight:600;margin:14px 0 8px">ALL RESPONSES ({n_resp})</div>', unsafe_allow_html=True)

        for i, resp in enumerate(responses):
            themes = _assign_themes(resp)
            theme_badges = " ".join(_theme_badge(t) for t in themes[:3] if t != "Other")
            resp_text = str(resp).strip()
            if not resp_text or len(resp_text) < 5:
                continue
            # Capitalize first letter
            resp_text = resp_text[0].upper() + resp_text[1:]

            st.markdown(f"""
<div style="background:white;border:1px solid {MGRAY};border-radius:10px;padding:12px 14px;margin-bottom:8px">
  <div style="display:flex;align-items:flex-start;gap:10px">
    <div style="width:24px;height:24px;border-radius:50%;background:{badge_color}15;display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:10px;font-weight:700;color:{badge_color}">{i+1}</div>
    <div style="flex:1">
      <div style="font-size:12px;color:#334155;line-height:1.55;margin-bottom:6px">{resp_text}</div>
      <div style="display:flex;gap:4px;flex-wrap:wrap">{theme_badges}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


def render(eng):
    atu_raw = eng.atu_raw if hasattr(eng, 'atu_raw') else None
    pet_raw = eng.pet_raw if hasattr(eng, 'pet_raw') else None

    if atu_raw is None:
        st.warning("No data loaded."); return

    n_atu = len(eng.stats().get('atu_n', 0)) if isinstance(eng.stats().get('atu_n'), list) else eng.stats().get('atu_n', 0)

    # Header
    st.markdown(f"""
<div style="margin-bottom:16px">
  <div style="font-size:10px;text-transform:uppercase;letter-spacing:.22em;color:{DGRAY};font-weight:600">QUALITATIVE ANALYSIS · THE VOICE OF THE DOCTOR</div>
  <h1 style="font-family:'DM Serif Display',serif;font-size:44px;font-weight:300;color:#0F172A;line-height:1.1;margin-bottom:8px">
    What doctors are<br><span style="color:{TEAL}">actually saying.</span>
  </h1>
  <p style="font-size:14px;color:#475569;max-width:640px;line-height:1.65">
    All voice response (VR) and open-end questions from ATU and PET surveys.
    For AI-moderated interviews, only Doctor / Speaker B responses are shown — moderator turns are removed.
    Themes assigned via keyword matching against the 12-theme rubric.
  </p>
</div>
""", unsafe_allow_html=True)

    # Stats row
    c1, c2, c3 = st.columns(3)
    # Count all responses
    atu_counts = {}
    for qcode, col, title, _, _ in ATU_VR_QUESTIONS:
        is_int = col == 571
        resp = _clean_responses(atu_raw[col] if col < len(atu_raw.columns) else None, is_interview=is_int)
        atu_counts[qcode] = len(resp)
    pet_counts = {}
    for qcode, col, title, _, _ in PET_VR_QUESTIONS:
        resp = _clean_responses(pet_raw[col] if pet_raw is not None and col < len(pet_raw.columns) else None)
        pet_counts[qcode] = len(resp)

    total_atu = sum(atu_counts.values())
    total_pet = sum(pet_counts.values())
    with c1: st.markdown(f'<div class="mcard"><div class="mlabel">ATU VOICE RESPONSES</div><div class="mval">{total_atu}</div><div class="msub">{len(ATU_VR_QUESTIONS)} open-end questions</div></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="mcard"><div class="mlabel">PET VOICE RESPONSES</div><div class="mval">{total_pet}</div><div class="msub">{len(PET_VR_QUESTIONS)} open-end questions</div></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div style="background:{TEAL};border-radius:16px;padding:24px"><div style="font-size:10px;text-transform:uppercase;letter-spacing:.22em;color:rgba(255,255,255,.6);font-weight:600">DOCTOR / SPEAKER B ONLY</div><div style="font-family:\'DM Serif Display\',serif;font-size:36px;font-weight:300;color:white;line-height:1">AI interview<br>responses extracted</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Tabs
    tab_atu, tab_pet = st.tabs(["📋 ATU Voice Responses", "📊 PET Voice Responses"])

    with tab_atu:
        st.markdown(f"""
<div style="background:{LGRAY};border:1px solid {MGRAY};border-radius:10px;padding:12px 16px;margin-bottom:16px;font-size:12px;color:#475569;line-height:1.6">
  <b>Data source:</b> Awareness Trial Usage (ATU) survey · {eng.stats().get('atu_n',0)} Healthcare Professionals ·
  Q3_160Z and Q3_220Z are ZoomRx AI-moderated interviews — only Doctor responses are shown, AI moderator turns are removed.
  All other questions are standard open-end responses.
</div>
""", unsafe_allow_html=True)

        for qcode, col, title, full_q, source in ATU_VR_QUESTIONS:
            is_int = (col == 571)
            _render_vr_section(qcode, col, title, full_q, source, atu_raw, is_interview=is_int, is_pet=False)

    with tab_pet:
        if pet_raw is None:
            st.info("PET data not loaded.")
            return
        st.markdown(f"""
<div style="background:{LGRAY};border:1px solid {MGRAY};border-radius:10px;padding:12px 16px;margin-bottom:16px;font-size:12px;color:#475569;line-height:1.6">
  <b>Data source:</b> Promotional Effectiveness Tracker (PET) survey · {eng.stats().get('pet_n',0)} interactions ·
  All open-end responses shown verbatim from uploaded data. No AI interpretation — themes assigned by keyword matching only.
</div>
""", unsafe_allow_html=True)

        for qcode, col, title, full_q, source in PET_VR_QUESTIONS:
            _render_vr_section(qcode, col, title, full_q, source, pet_raw, is_interview=False, is_pet=True)

    st.markdown(f"""
<div style="background:{LGRAY};border-radius:8px;padding:12px 16px;margin-top:16px;font-size:11px;color:#94A3B8">
  ⚠ All responses are verbatim from uploaded data files. Themes assigned via keyword matching only — no AI interpretation or editing applied.
  AI interview transcripts (Q3_160Z, Q3_220Z): Doctor responses extracted by identifying text following "Doctor:" or "Speaker B:" markers.
</div>
""", unsafe_allow_html=True)
