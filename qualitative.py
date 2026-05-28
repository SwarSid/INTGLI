"""Qualitative analysis — auto-themes voice response questions."""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re
from collections import Counter

TEAL="#0F4C5C"; NAVY="#1E293B"; CRIMSON="#832232"; AMBER="#B8860B"; GREEN="#15803D"
MGRAY="#E2E8F0"; DGRAY="#64748B"; LGRAY="#F8FAFC"

QUAL_THEMES = {
    "Efficacy / PFS / OS": ["pfs","progression","survival","efficacy","response","tumor","growth","shrink","disease control"],
    "Safety / Toxicity":   ["toxic","liver","hepat","alt","ast","safe","side effect","adverse","tolera"],
    "Access / Insurance":  ["access","insurance","prior auth","pa","reimburse","copay","cost","afford","coverage","deny","denied"],
    "Patient ID / Testing":["find","patient","identify","ngs","testing","idh","mutant","eligible","diagnos","molecular"],
    "ServierONE / Support":["servierone","support program","copay card","patient support","bridge","quickstart","pap"],
    "NCCN / Guidelines":   ["nccn","guideline","recommended","preferred","label","indication","approved"],
    "Seizures / QoL":      ["seizure","quality of life","qol","function","daily","cognitive","neuro"],
    "Fertility / Long-term":["fertil","long-term","young","preservation","future"],
    "Competitive":         ["competitor","tibsovo","ivosidenib","olutasidenib","rezlidhia","compared","versus"],
    "Rep Relationship":    ["rep","representative","visit","discussion","partner","speaker","kol"],
}


def _auto_theme(text: str) -> list:
    if not text or pd.isna(text): return ["Unclassified"]
    t = str(text).lower()
    themes = [label for label, kws in QUAL_THEMES.items() if any(k in t for k in kws)]
    return themes if themes else ["Unclassified"]


def render(eng):
    st.markdown(f"""
<div style="margin-bottom:16px">
  <div style="font-size:10px;text-transform:uppercase;letter-spacing:.28em;color:{CRIMSON};font-weight:600">QUALITATIVE ANALYSIS</div>
  <h1 style="font-family:'DM Serif Display',serif;font-size:44px;font-weight:300;color:#0F172A;margin-bottom:10px">
    Voice responses, auto-bucketed.<br>
    <span style="color:{TEAL}">Themes extracted, not transcribed.</span>
  </h1>
  <p style="font-size:14px;color:#475569;max-width:640px;line-height:1.65">
    All voice-response questions from ATU and PET are auto-themed using keyword
    matching. Each response is tagged to one or more of 10 themes. Counts and
    cross-tabulations shown below.
  </p>
</div>
""", unsafe_allow_html=True)

    # Load raw qual data from ATU/PET
    qual_tabs = st.tabs([
        "🎤 ATU Q3_60c — Patient Type Influence",
        "🎤 ATU Q3_125 — Tumor Volume Decisions",
        "🎤 ATU Q3_220a — Main Barriers",
        "🎤 PET Q3_74 — Interaction Improvement",
        "🎤 PET Q1_200 — Patient Support Discussion",
        "🔍 Theme Cross-Tab",
    ])

    atu = eng.atu if eng.atu is not None else pd.DataFrame()
    pet = eng.pet if eng.pet is not None else pd.DataFrame()

    def _get_qual_col(df, qcodes, prefix):
        cols = [i for i, v in enumerate(qcodes) if str(v).startswith(prefix)]
        return cols[0] if cols else None

    atu_qcodes = eng.atu_qcodes if eng.atu_qcodes is not None else []
    pet_qcodes = eng.pet_qcodes if eng.pet_qcodes is not None else []

    qual_sources = [
        ("ATU Q3_60cZ", atu, atu_qcodes, "Q3_60cZ", "How do patient types influence your treatment decision for grade 2 IDH-mutant astrocytoma or oligodendroglioma?"),
        ("ATU Q3_125Z", atu, atu_qcodes, "Q3_125Z", "When considering treatments for grade 2 IDH-mutant, how does evidence of tumor volume reduction influence your decisions?"),
        ("ATU Q3_220Z_QUAL", atu, atu_qcodes, "Q3_220Z_QUAL", "What are your main barriers to prescribing VORANIGO?"),
        ("PET Q3_74", pet, pet_qcodes, "C3_74Z", "How could your interaction with the Servier rep be improved?"),
        ("PET Q1_200Z", pet, pet_qcodes, "Q1_200Z", "What was discussed about patient support services during your most recent interaction?"),
    ]

    theme_counts_all = Counter()
    theme_by_source = {}

    for tab_idx, (tab_label, df_src, qcodes, prefix, q_text) in enumerate(qual_sources):
        col_idx = _get_qual_col(df_src, qcodes, prefix)

        with qual_tabs[tab_idx]:
            st.markdown(f"""
<div style="background:white;border:1px solid {MGRAY};border-radius:12px;padding:16px 20px;margin-bottom:16px">
  <div style="font-size:9px;text-transform:uppercase;letter-spacing:.2em;color:#94A3B8;font-weight:600">QUESTION</div>
  <div style="font-size:14px;font-weight:500;color:#0F172A;margin-top:4px">{q_text}</div>
  <div style="font-size:10px;color:#94A3B8;margin-top:6px">Source: {tab_label} | Auto-themed using {len(QUAL_THEMES)} theme categories</div>
</div>
""", unsafe_allow_html=True)

            if col_idx is None or df_src.empty:
                st.info("Question not found in uploaded data. This view populates when real masked files are uploaded.")
                _show_demo_themes(tab_label)
                continue

            # Extract responses
            responses = df_src.iloc[:, col_idx].dropna()
            # Filter out header rows (text very long = question text)
            responses = responses[responses.str.len() < 500] if hasattr(responses, 'str') else responses
            responses = responses[~responses.str.contains("Please", na=False)] if hasattr(responses, 'str') else responses
            responses = responses[responses.str.strip() != ""] if hasattr(responses, 'str') else responses

            if responses.empty:
                st.info("No qualifying responses found for this question.")
                _show_demo_themes(tab_label)
                continue

            # Auto-theme
            all_themes = []
            themed_records = []
            for resp in responses:
                themes = _auto_theme(str(resp))
                all_themes.extend(themes)
                themed_records.append({"response": str(resp)[:200], "themes": ", ".join(themes)})
                theme_counts_all.update(themes)

            theme_by_source[tab_label] = Counter(all_themes)

            theme_counts = Counter(all_themes)
            df_themes = pd.DataFrame(list(theme_counts.items()), columns=["Theme", "Count"])
            df_themes["% of responses"] = (df_themes["Count"] / len(responses) * 100).round(1)
            df_themes = df_themes.sort_values("Count", ascending=False)

            st.markdown(f'<div style="font-size:12px;color:{DGRAY};margin-bottom:10px">n={len(responses)} responses auto-themed | Multiple themes per response allowed</div>', unsafe_allow_html=True)

            fig = go.Figure()
            colors = [TEAL, NAVY, CRIMSON, AMBER, GREEN, "#7C3AED", "#0369A1", "#C2410C", "#047857", "#92400E"]
            for i, row in df_themes.iterrows():
                c = colors[list(df_themes["Theme"]).index(row["Theme"]) % len(colors)]
                fig.add_trace(go.Bar(x=[row["Theme"]], y=[row["Count"]], marker_color=c,
                                     text=[f'{row["Count"]}\n({row["% of responses"]}%)'], textposition="outside",
                                     name=row["Theme"]))
            fig.update_layout(showlegend=False, height=340, plot_bgcolor="white", paper_bgcolor="white",
                              font=dict(family="Inter",size=10), xaxis_tickangle=-20,
                              yaxis=dict(showgrid=True,gridcolor="#F1F5F9"),
                              margin=dict(l=0,r=0,t=10,b=0))
            st.plotly_chart(fig, use_container_width=True)

            # Sample verbatims
            st.markdown(f'<div style="font-size:10px;text-transform:uppercase;letter-spacing:.2em;color:#94A3B8;font-weight:600;margin-bottom:8px">SAMPLE VERBATIMS (first 10)</div>', unsafe_allow_html=True)
            for rec in themed_records[:10]:
                theme_pills = "".join(f'<span style="background:{TEAL}22;color:{TEAL};padding:1px 6px;border-radius:3px;font-size:9px;font-weight:600;margin-right:4px">{t}</span>' for t in rec["themes"].split(", "))
                st.markdown(f"""
<div style="background:{LGRAY};border-radius:8px;padding:10px 14px;margin-bottom:6px;border-left:3px solid {TEAL}">
  <div style="font-size:12px;color:#334155;font-style:italic;margin-bottom:6px">"{rec['response']}"</div>
  <div>{theme_pills}</div>
</div>
""", unsafe_allow_html=True)

    # Theme cross-tab
    with qual_tabs[5]:
        st.markdown(f'<h2 style="font-family:\'DM Serif Display\',serif;font-size:24px;color:#0F172A;margin-bottom:12px">Theme Distribution Across All Qual Questions</h2>', unsafe_allow_html=True)

        if theme_counts_all:
            all_df = pd.DataFrame(list(theme_counts_all.items()), columns=["Theme", "Total Mentions"])
            all_df = all_df.sort_values("Total Mentions", ascending=True)

            fig = go.Figure(go.Bar(x=all_df["Total Mentions"], y=all_df["Theme"],
                                   orientation="h", marker_color=TEAL,
                                   text=all_df["Total Mentions"], textposition="outside"))
            fig.update_layout(height=400, plot_bgcolor="white", paper_bgcolor="white",
                              font=dict(family="Inter",size=11),
                              xaxis=dict(showgrid=True,gridcolor="#F1F5F9"),
                              margin=dict(l=0,r=60,t=10,b=0))
            st.plotly_chart(fig, use_container_width=True)
        else:
            _show_overall_demo()


def _show_demo_themes(label):
    """Show reference theme distribution from integrated slides."""
    demo = {
        "Access / Insurance": 36,
        "Efficacy / PFS / OS": 29,
        "Safety / Toxicity": 25,
        "Patient ID / Testing": 21,
        "ServierONE / Support": 18,
        "NCCN / Guidelines": 15,
        "Competitive": 12,
        "Seizures / QoL": 10,
    }
    st.markdown(f'<div style="font-size:10px;color:#94A3B8;margin-bottom:8px">Reference distribution (from FY26 Q2 integrated slides) — upload masked data to see real responses</div>', unsafe_allow_html=True)
    fig = go.Figure()
    for i, (theme, count) in enumerate(sorted(demo.items(), key=lambda x: -x[1])):
        colors = [TEAL, NAVY, CRIMSON, AMBER, GREEN, "#7C3AED", "#0369A1", "#C2410C"]
        fig.add_trace(go.Bar(x=[theme], y=[count], marker_color=colors[i % len(colors)],
                             text=[f"{count}%"], textposition="outside", name=theme))
    fig.update_layout(showlegend=False, height=300, plot_bgcolor="white", paper_bgcolor="white",
                      font=dict(family="Inter",size=10), xaxis_tickangle=-20,
                      yaxis=dict(showgrid=True,gridcolor="#F1F5F9", ticksuffix="%"),
                      margin=dict(l=0,r=0,t=10,b=0))
    st.plotly_chart(fig, use_container_width=True)


def _show_overall_demo():
    st.info("Upload masked ATU + PET files to see auto-themed qualitative analysis across all voice-response questions.")
