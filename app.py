"""HCP Conversion Atlas — Production Streamlit App"""
import streamlit as st
import pandas as pd

st.set_page_config(page_title="HCP Conversion Atlas · ICI", page_icon="🏥",
                   layout="wide", initial_sidebar_state="collapsed")

TEAL="#0F4C5C"; NAVY="#1E293B"; CRIMSON="#832232"; AMBER="#B8860B"; GREEN="#15803D"
LGRAY="#F8FAFC"; MGRAY="#E2E8F0"; DGRAY="#64748B"
CLUSTER_COLORS={1:TEAL,2:NAVY,3:CRIMSON,4:AMBER,5:GREEN}

st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Inter:wght@300;400;500;600;700&display=swap');
html,body,[class*="css"]{{font-family:'Inter',sans-serif;background:{LGRAY};color:#0F172A}}
h1,h2,h3,h4{{font-family:'DM Serif Display',serif;font-weight:400}}
.topbar{{position:sticky;top:0;z-index:100;background:rgba(255,255,255,.92);backdrop-filter:blur(20px);border-bottom:1px solid {MGRAY};padding:14px 32px;display:flex;align-items:center;gap:14px;margin:-1rem -1rem 0 -1rem}}
.tb-title{{font-size:17px;font-weight:600;color:#0F172A;line-height:1.1}}
.tb-sub{{font-size:10px;text-transform:uppercase;letter-spacing:.25em;color:{DGRAY};font-weight:500}}
.tb-logo{{width:40px;height:40px;border-radius:8px;background:{TEAL};display:flex;align-items:center;justify-content:center;font-size:20px;flex-shrink:0}}
.mcard{{background:white;border:1px solid {MGRAY};border-radius:16px;padding:24px}}
.mlabel{{font-size:10px;text-transform:uppercase;letter-spacing:.22em;color:{DGRAY};font-weight:600}}
.mval{{font-family:'DM Serif Display',serif;font-size:48px;font-weight:300;color:#0F172A;line-height:1;margin-top:4px}}
.msub{{font-size:12px;color:#94A3B8;margin-top:6px}}
.acard{{background:{TEAL};border-radius:16px;padding:24px;color:white}}
.acard .mlabel{{color:rgba(255,255,255,.6)}}
.xtab-card{{background:white;border:1px solid {MGRAY};border-radius:14px;padding:20px;margin-bottom:16px}}
#MainMenu,footer,header{{visibility:hidden}}
.block-container{{padding-top:0!important;max-width:1400px!important}}
div[data-testid="stSidebarCollapsedControl"]{{display:none}}
</style>""", unsafe_allow_html=True)

@st.cache_resource(show_spinner=False)
def load_project():
    import sys; sys.path.insert(0,".")
    from data_engine import DataEngine
    e=DataEngine(); e.load_project(); return e

@st.cache_resource(show_spinner=False)
def load_files(ab, pb):
    import sys; sys.path.insert(0,".")
    from data_engine import DataEngine
    e=DataEngine(); e.load_from_bytes(ab,pb); return e

def topbar(s):
    st.markdown(f"""<div class="topbar">
  <div class="tb-logo">🏥</div>
  <div><div class="tb-sub">Interaction Conversion Index · Intelligence</div>
       <div class="tb-title">Healthcare Professional Conversion Atlas</div></div>
  <div style="margin-left:auto;display:flex;gap:20px;font-size:11px;color:{DGRAY}">
    <span>👥 {s['atu_n']} Healthcare Professionals · {s['pet_n']} interactions</span>
    <span>⚡ ATU × PET · v2026.1</span>
  </div>
</div>""", unsafe_allow_html=True)

def nav():
    """Exact Emergent nav: Approach, Overview, colored cluster pills, Custom Rep Support Card"""
    cur = st.session_state.get("view","approach")
    # Map cluster views
    if cur.startswith("cluster_"):
        active_cluster = int(cur.split("_")[1])
    else:
        active_cluster = None

    cols = st.columns([1.2,1,1,1,1,1,1.5])
    nav_items = [
        (cols[0], "approach",   "Approach",            None, None),
        (cols[1], "overview",   "Overview",            None, None),
        (cols[2], "cluster_1",  "Patient ID",          1,    TEAL),
        (cols[3], "cluster_2",  "Access Pending",      2,    NAVY),
        (cols[4], "cluster_3",  "Evidence Gap",        3,    CRIMSON),
        (cols[5], "cluster_4",  "Narrative Build",     4,    AMBER),
        # (cols[?], "cluster_5","Conviction-Led",      5,    GREEN),  # condensed
        (cols[6], "envelope",   "Custom Rep Support Card", None, None),
    ]
    for col, vid, label, cid, dot_color in nav_items:
        with col:
            active = (cur == vid)
            dot = f'<span style="width:8px;height:8px;border-radius:50%;background:{dot_color};display:inline-block;margin-right:4px;flex-shrink:0"></span>' if dot_color else ""
            if st.button(f"{label}", key=f"nav_{vid}", use_container_width=True,
                         type="primary" if active else "secondary"):
                st.session_state["view"] = vid; st.rerun()

def filter_bar(hcps):
    if hcps is None or hcps.empty: return hcps
    specs=["All"]+sorted(hcps["specialty"].dropna().unique().tolist())
    setts=["All"]+sorted(hcps["setting"].dropna().unique().tolist())
    loads=["All","Low","Medium","High"]
    st.markdown(f'<div style="background:white;border:1px solid {MGRAY};border-radius:12px;padding:10px 18px;margin:12px 0">',unsafe_allow_html=True)
    r1c1,r1c2,r1c3,r1c4=st.columns([0.8,3,3,3])
    with r1c1: st.markdown(f'<div style="font-size:9px;text-transform:uppercase;letter-spacing:.2em;color:#94A3B8;font-weight:600;padding-top:10px">SPECIALTY</div>',unsafe_allow_html=True)
    with r1c2: spec=st.selectbox("Specialty",specs,label_visibility="collapsed",key="fs")
    with r1c3: sett=st.selectbox("Setting",setts,label_visibility="collapsed",key="ft")
    with r1c4: load=st.selectbox("Patient Load",loads,label_visibility="collapsed",key="fl")
    st.markdown("</div>",unsafe_allow_html=True)
    mask=pd.Series([True]*len(hcps))
    if spec!="All": mask&=hcps["specialty"]==spec
    if sett!="All": mask&=hcps["setting"]==sett
    if load!="All": mask&=hcps["load"]==load
    f=hcps[mask].copy()
    st.markdown(f'<div style="text-align:right;font-size:11px;color:#94A3B8;margin:-6px 0 8px">Showing {len(f)} HCPs</div>',unsafe_allow_html=True)
    return f

def _upload_screen():
    """Shown when no project files exist (Streamlit Cloud deployment)."""
    st.markdown(f"""
<div style="max-width:640px;margin:80px auto;text-align:center">
  <div style="width:64px;height:64px;background:{TEAL};border-radius:16px;
              display:flex;align-items:center;justify-content:center;
              font-size:32px;margin:0 auto 24px">🏥</div>
  <h1 style="font-family:'DM Serif Display',serif;font-size:40px;font-weight:300;
             color:#0F172A;margin-bottom:12px">
    Healthcare Professional<br>Conversion Atlas
  </h1>
  <p style="font-size:14px;color:#64748B;line-height:1.65;margin-bottom:32px">
    Upload your masked ATU and PET Excel files to generate the full
    ICI dashboard — cluster assignments, cross-tabs, qualitative themes,
    and custom rep support cards.
  </p>
</div>
""", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""
<div style="background:white;border:2px dashed {TEAL}44;border-radius:16px;
            padding:28px 24px;text-align:center;margin-bottom:8px">
  <div style="font-size:10px;text-transform:uppercase;letter-spacing:.2em;
              color:{TEAL};font-weight:700;margin-bottom:8px">REQUIRED</div>
  <div style="font-size:16px;font-weight:600;color:#0F172A;margin-bottom:4px">ATU Workbook</div>
  <div style="font-size:12px;color:#64748B">Q1 + Q2 · .xlsx</div>
</div>
""", unsafe_allow_html=True)
        atu_file = st.file_uploader("ATU", type=["xlsx"], key="atu_hero", label_visibility="collapsed")

    with c2:
        st.markdown(f"""
<div style="background:white;border:2px dashed {TEAL}44;border-radius:16px;
            padding:28px 24px;text-align:center;margin-bottom:8px">
  <div style="font-size:10px;text-transform:uppercase;letter-spacing:.2em;
              color:{TEAL};font-weight:700;margin-bottom:8px">REQUIRED</div>
  <div style="font-size:16px;font-weight:600;color:#0F172A;margin-bottom:4px">PET Workbook</div>
  <div style="font-size:12px;color:#64748B">Q4 + Q1 + Q2 · .xlsx</div>
</div>
""", unsafe_allow_html=True)
        pet_file = st.file_uploader("PET", type=["xlsx"], key="pet_hero", label_visibility="collapsed")

    if atu_file and pet_file:
        with st.spinner("Processing files and computing ICI scores..."):
            try:
                eng = load_files(atu_file.read(), pet_file.read())
                st.session_state["eng_loaded"] = True
                st.success(f"✓ {eng.stats()['overlap_n']} overlapping HCPs found — loading dashboard...")
                st.rerun()
            except Exception as ex:
                st.error(f"Error reading files: {ex}")
    return None


def main():
    if "view" not in st.session_state: st.session_state["view"] = "approach"
    if "bi"   not in st.session_state: st.session_state["bi"]   = 0

    import sys; sys.path.insert(0, ".")

    # ── Try loading project data (works locally, silently skips on Streamlit Cloud) ──
    eng = load_project()

    # ── Sidebar upload (always visible once eng is loaded) ──────────────────
    with st.sidebar:
        st.markdown(f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:20px"><div style="width:32px;height:32px;background:{TEAL};border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:16px">🏥</div><div style="font-weight:600;font-size:14px">ICI Atlas</div></div>', unsafe_allow_html=True)

        if eng.is_loaded:
            st.markdown(f'<div style="font-size:10px;text-transform:uppercase;letter-spacing:.15em;color:#94A3B8;font-weight:600;margin-bottom:8px">UPLOAD NEW FILES</div>', unsafe_allow_html=True)
            af = st.file_uploader("ATU workbook (.xlsx)", type=["xlsx"], key="atu_up")
            pf = st.file_uploader("PET workbook (.xlsx)", type=["xlsx"], key="pet_up")
            if af and pf:
                try:
                    eng = load_files(af.read(), pf.read())
                    st.success(f"✓ {eng.stats()['overlap_n']} HCPs loaded")
                except Exception as ex:
                    st.error(f"Error: {ex}")

            st.markdown("---")
            s = eng.stats()
            st.markdown(f'<div style="font-size:11px;color:#64748B"><div>ATU: <b>{s["atu_n"]}</b> HCPs</div><div>PET: <b>{s["pet_n"]}</b> interactions</div><div>Overlap: <b>{s["overlap_n"]}</b></div></div>', unsafe_allow_html=True)

    # ── If no data yet → show upload landing page ────────────────────────────
    if not eng.is_loaded:
        # Top bar minimal
        st.markdown(f"""<div class="topbar">
  <div class="tb-logo">🏥</div>
  <div><div class="tb-sub">Interaction Conversion Index · Intelligence</div>
       <div class="tb-title">Healthcare Professional Conversion Atlas</div></div>
</div>""", unsafe_allow_html=True)
        result = _upload_screen()
        return

    # ── Full dashboard ────────────────────────────────────────────────────────
    topbar(eng.stats())
    nav()
    st.markdown("<br>", unsafe_allow_html=True)

    cur = st.session_state["view"]
    NO_FILTER = ("approach", "envelope", "crosstabs", "qualitative")
    hcps = filter_bar(eng.hcps_df) if cur not in NO_FILTER and not cur.startswith("cluster_") else eng.hcps_df
    st.markdown("<br>", unsafe_allow_html=True)

    if cur == "approach":
        from views.approach import render; render(eng)
    elif cur == "overview":
        from views.overview import render; render(eng, hcps)
    elif cur.startswith("cluster_"):
        from views.cluster_detail import render
        cid = int(cur.split("_")[1]); render(cid, hcps, eng)
    elif cur == "integrated":
        from views.integrated import render; render(eng, hcps)
    elif cur == "crosstabs":
        from views.crosstabs import render; render(eng)
    elif cur == "qualitative":
        from views.qualitative import render; render(eng)
    elif cur == "envelope":
        from views.envelope import render; render(eng, hcps)

    st.markdown(f'<div style="font-size:11px;color:#94A3B8;border-top:1px solid {MGRAY};padding-top:14px;margin-top:40px">ATU × PET unified through the Interaction Conversion Index (ICI) · 7 dimensions · 5 engagement states · sequential resolution</div>', unsafe_allow_html=True)

if __name__=="__main__": main()
