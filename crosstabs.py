"""HCP Conversion Atlas — Production Streamlit App"""
import streamlit as st
import pandas as pd
import sys, os, importlib.util, time

# ── Robust path setup ─────────────────────────────────────────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

# views/ may be a subfolder OR files may be flat at root (depends on how GitHub was uploaded)
_VIEWS_DIR = (
    os.path.join(_HERE, "views")
    if os.path.isdir(os.path.join(_HERE, "views"))
    else _HERE   # flat upload — view files are at same level as app.py
)

st.set_page_config(page_title="HCP Conversion Atlas · ICI", page_icon="🏥",
                   layout="wide", initial_sidebar_state="collapsed")

TEAL="#0F4C5C"; NAVY="#1E293B"; CRIMSON="#832232"; AMBER="#B8860B"; GREEN="#15803D"
LGRAY="#F8FAFC"; MGRAY="#E2E8F0"; DGRAY="#64748B"

st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Inter:wght@300;400;500;600;700&display=swap');
html,body,[class*="css"]{{font-family:'Inter',sans-serif;background:{LGRAY};color:#0F172A}}
h1,h2,h3,h4{{font-family:'DM Serif Display',serif;font-weight:400}}
.topbar{{position:sticky;top:0;z-index:100;background:rgba(255,255,255,.92);
         backdrop-filter:blur(20px);border-bottom:1px solid {MGRAY};
         padding:14px 32px;display:flex;align-items:center;gap:14px;margin:-1rem -1rem 0 -1rem}}
.tb-title{{font-size:17px;font-weight:600;color:#0F172A;line-height:1.1}}
.tb-sub{{font-size:10px;text-transform:uppercase;letter-spacing:.25em;color:{DGRAY};font-weight:500}}
.tb-logo{{width:40px;height:40px;border-radius:8px;background:{TEAL};display:flex;
          align-items:center;justify-content:center;font-size:20px;flex-shrink:0}}
.mcard{{background:white;border:1px solid {MGRAY};border-radius:16px;padding:24px}}
.mlabel{{font-size:10px;text-transform:uppercase;letter-spacing:.22em;color:{DGRAY};font-weight:600}}
.mval{{font-family:'DM Serif Display',serif;font-size:48px;font-weight:300;
       color:#0F172A;line-height:1;margin-top:4px}}
.msub{{font-size:12px;color:#94A3B8;margin-top:6px}}
.acard{{background:{TEAL};border-radius:16px;padding:24px;color:white}}
.acard .mlabel{{color:rgba(255,255,255,.6)}}
.xtab-card{{background:white;border:1px solid {MGRAY};border-radius:14px;
            padding:20px;margin-bottom:16px}}
#MainMenu,footer,header{{visibility:hidden}}
.block-container{{padding-top:0!important;max-width:1400px!important}}
div[data-testid="stSidebarCollapsedControl"]{{display:none}}
</style>""", unsafe_allow_html=True)


# ── Module loaders ────────────────────────────────────────────────────────────
def _load_module(name):
    """Load view file — works whether files are in views/ subfolder or flat at root."""
    candidates = [
        os.path.join(_VIEWS_DIR, f"{name}.py"),
        os.path.join(_HERE, f"{name}.py"),
    ]
    path = next((p for p in candidates if os.path.exists(p)), None)
    if path is None:
        root_files = os.listdir(_HERE)
        root_files = ", ".join(sorted(os.listdir(_HERE)))
        st.error(f"Cannot find {name}.py. Searched: {candidates}. Files at root: {root_files}")
        st.stop()
    spec = importlib.util.spec_from_file_location(name, path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def _load_engine_class():
    # Try both locations — subfolder or flat root
    for candidate in [
        os.path.join(_HERE, "data_engine.py"),
        os.path.join(os.path.dirname(_HERE), "data_engine.py"),
    ]:
        if os.path.exists(candidate):
            spec = importlib.util.spec_from_file_location("data_engine", candidate)
            mod  = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod.DataEngine
    raise FileNotFoundError(f"data_engine.py not found near {_HERE}")


# ── Engine stored in session_state ───────────────────────────────────────────
def _get_engine():
    if "engine" in st.session_state:
        eng = st.session_state["engine"]
        if eng is not None and eng.is_loaded:
            return eng
    # Try project files (only exists locally, not on Streamlit Cloud)
    DataEngine = _load_engine_class()
    eng = DataEngine()
    eng.load_project()
    if eng.is_loaded:
        st.session_state["engine"] = eng
    return eng

def _load_from_bytes(ab, pb):
    DataEngine = _load_engine_class()
    eng = DataEngine()
    eng.load_from_bytes(ab, pb)
    st.session_state["engine"] = eng
    return eng


# ── UI helpers ────────────────────────────────────────────────────────────────
def _topbar(s):
    atu_n    = s["atu_n"]
    pet_n    = s["pet_n"]
    overlap  = s["overlap_n"]
    st.markdown(f"""<div class="topbar">
  <div class="tb-logo">🏥</div>
  <div>
    <div class="tb-sub">Interaction Conversion Index · Intelligence</div>
    <div class="tb-title">Healthcare Professional Conversion Atlas</div>
  </div>
  <div style="margin-left:auto;display:flex;gap:20px;font-size:11px;color:{DGRAY}">
    <span>👥 {atu_n} ATU · {pet_n} PET · <b style="color:{TEAL}">{overlap} matched</b></span>
    <span>⚡ ATU × PET · v2026.1</span>
  </div>
</div>""", unsafe_allow_html=True)


def _nav():
    cur  = st.session_state.get("view", "approach")
    cols = st.columns([1.2, 1.2, 1.4, 1.4, 1.4, 1.8])
    items = [
        (cols[0], "approach",    "Approach"),
        (cols[1], "overview",    "Overview"),
        (cols[2], "integrated",  "Integrated Insights"),
        (cols[3], "crosstabs",   "Cross-Tab Repository"),
        (cols[4], "qualitative", "Qualitative Analysis"),
        (cols[5], "envelope",    "Custom Rep Support Card"),
    ]
    for col, vid, label in items:
        with col:
            active = (cur == vid)
            if st.button(label, key=f"nav_{vid}", use_container_width=True,
                         type="primary" if active else "secondary"):
                st.session_state["view"] = vid
                st.rerun()


def _filter_bar(hcps):
    if hcps is None or hcps.empty: return hcps
    specs  = ["All"] + sorted(hcps["specialty"].dropna().unique().tolist())
    setts  = ["All"] + sorted(hcps["setting"].dropna().unique().tolist())
    loads  = ["All", "Low", "Medium", "High"]
    st.markdown(f'<div style="background:white;border:1px solid {MGRAY};'
                f'border-radius:12px;padding:10px 18px;margin:12px 0">',
                unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns([1, 3, 3, 3])
    with c1:
        st.markdown(f'<div style="font-size:9px;text-transform:uppercase;'
                    f'letter-spacing:.2em;color:#94A3B8;font-weight:600;'
                    f'padding-top:10px">SEGMENT THE ATLAS</div>',
                    unsafe_allow_html=True)
    with c2: spec = st.selectbox("Specialty",     specs, label_visibility="collapsed", key="fs")
    with c3: sett = st.selectbox("Setting",       setts, label_visibility="collapsed", key="ft")
    with c4: load = st.selectbox("Patient Load",  loads, label_visibility="collapsed", key="fl")
    st.markdown("</div>", unsafe_allow_html=True)
    mask = pd.Series([True] * len(hcps))
    if spec != "All": mask &= hcps["specialty"] == spec
    if sett != "All": mask &= hcps["setting"]   == sett
    if load != "All": mask &= hcps["load"]       == load
    filtered = hcps[mask].copy()
    st.markdown(f'<div style="text-align:right;font-size:11px;color:#94A3B8;'
                f'margin:-6px 0 8px">Showing {len(filtered)} of {len(hcps)} '
                f'matched HCPs</div>', unsafe_allow_html=True)
    return filtered


def _upload_screen():
    st.markdown(f"""
<div style="max-width:640px;margin:60px auto;text-align:center;padding:0 24px">
  <div style="width:64px;height:64px;background:{TEAL};border-radius:16px;display:flex;
    align-items:center;justify-content:center;font-size:32px;margin:0 auto 24px">🏥</div>
  <h1 style="font-family:'DM Serif Display',serif;font-size:40px;font-weight:300;
    color:#0F172A;margin-bottom:12px">Healthcare Professional<br>Conversion Atlas</h1>
  <p style="font-size:14px;color:#64748B;line-height:1.65;margin-bottom:16px">
    Upload your masked ATU and PET Excel files to generate the full ICI dashboard.
  </p>
  <div style="background:{LGRAY};border-radius:10px;padding:12px 16px;font-size:12px;
    color:#64748B;margin-bottom:32px;text-align:left">
    <b>What "matched HCPs" means:</b><br>
    • <b>ATU file</b> — all HCPs who completed the Awareness Trial Usage survey (e.g. 161 HCPs)<br>
    • <b>PET file</b> — all rep interactions logged in the Promotional Effectiveness Tracker (e.g. 104 unique HCPs, 225 interactions)<br>
    • <b>Matched</b> — HCPs who appear in <em>both</em> files, allowing ATU intent to be cross-referenced with PET behaviour (e.g. 42 HCPs). All ICI scores, cross-tabs and cluster assignments use only these matched HCPs.
  </div>
</div>
""", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f'<div style="background:white;border:2px dashed {TEAL}44;'
                    f'border-radius:16px;padding:24px;text-align:center;margin-bottom:8px">'
                    f'<div style="font-size:10px;text-transform:uppercase;letter-spacing:.2em;'
                    f'color:{TEAL};font-weight:700;margin-bottom:8px">REQUIRED</div>'
                    f'<div style="font-size:16px;font-weight:600;color:#0F172A;margin-bottom:4px">'
                    f'ATU Workbook</div>'
                    f'<div style="font-size:12px;color:#64748B">Q1 + Q2 · .xlsx</div></div>',
                    unsafe_allow_html=True)
        atu_file = st.file_uploader("ATU", type=["xlsx"], key="atu_hero",
                                    label_visibility="collapsed")
    with c2:
        st.markdown(f'<div style="background:white;border:2px dashed {TEAL}44;'
                    f'border-radius:16px;padding:24px;text-align:center;margin-bottom:8px">'
                    f'<div style="font-size:10px;text-transform:uppercase;letter-spacing:.2em;'
                    f'color:{TEAL};font-weight:700;margin-bottom:8px">REQUIRED</div>'
                    f'<div style="font-size:16px;font-weight:600;color:#0F172A;margin-bottom:4px">'
                    f'PET Workbook</div>'
                    f'<div style="font-size:12px;color:#64748B">Q4 + Q1 + Q2 · .xlsx</div></div>',
                    unsafe_allow_html=True)
        pet_file = st.file_uploader("PET", type=["xlsx"], key="pet_hero",
                                    label_visibility="collapsed")

    if atu_file and pet_file:
        with st.spinner("⏳ Processing files and computing ICI scores... (30–60 seconds)"):
            try:
                eng = _load_from_bytes(atu_file.read(), pet_file.read())
                s = eng.stats()
                st.success(
                    f"✓ Files processed — "
                    f"{s['atu_n']} ATU HCPs · {s['pet_n']} PET HCPs · "
                    f"**{s['overlap_n']} matched HCPs** (appear in both files) · "
                    f"Loading dashboard..."
                )
                st.balloons()
                time.sleep(1)
                st.rerun()
            except Exception as ex:
                st.error(f"Error reading files: {ex}")
                st.info("Make sure both files are raw LimeSurvey .xlsx exports with a User Id column.")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
def main():
    if "view" not in st.session_state: st.session_state["view"] = "approach"
    if "bi"   not in st.session_state: st.session_state["bi"]   = 0

    eng = _get_engine()

    # Sidebar
    with st.sidebar:
        st.markdown(f'<div style="display:flex;align-items:center;gap:10px;'
                    f'margin-bottom:16px"><div style="width:32px;height:32px;'
                    f'background:{TEAL};border-radius:6px;display:flex;'
                    f'align-items:center;justify-content:center;font-size:16px">🏥</div>'
                    f'<div style="font-weight:600;font-size:14px">ICI Atlas</div></div>',
                    unsafe_allow_html=True)

        if eng.is_loaded:
            s = eng.stats()
            # Clear stats explanation
            st.markdown(f"""
<div style="background:{LGRAY};border-radius:8px;padding:10px 12px;
            font-size:11px;color:#475569;margin-bottom:12px;line-height:1.6">
  <div style="font-weight:700;color:#0F172A;margin-bottom:4px">DATA SUMMARY</div>
  <div>📋 <b>{s['atu_n']}</b> HCPs in ATU survey</div>
  <div>📊 <b>{s['pet_n']}</b> HCPs in PET tracker</div>
  <div style="border-top:1px solid {MGRAY};margin:6px 0;padding-top:6px">
    🎯 <b style="color:{TEAL}">{s['overlap_n']}</b> HCPs matched in both<br>
    <span style="font-size:10px;color:#94A3B8">
      Only matched HCPs have full ICI scores, cross-tabs, and cluster assignments
    </span>
  </div>
</div>
""", unsafe_allow_html=True)
            st.markdown(f'<div style="font-size:10px;text-transform:uppercase;'
                        f'letter-spacing:.15em;color:#94A3B8;font-weight:600;'
                        f'margin-bottom:8px">UPLOAD NEW DATA</div>',
                        unsafe_allow_html=True)
            af = st.file_uploader("ATU (.xlsx)", type=["xlsx"], key="atu_side")
            pf = st.file_uploader("PET (.xlsx)", type=["xlsx"], key="pet_side")
            if af and pf:
                with st.spinner("Processing..."):
                    try:
                        eng = _load_from_bytes(af.read(), pf.read())
                        st.success(f"✓ {eng.stats()['overlap_n']} matched HCPs loaded")
                        st.rerun()
                    except Exception as ex:
                        st.error(f"Error: {ex}")
        else:
            st.info("Upload ATU + PET files on the main screen to begin.")

    # No data — show upload landing
    if not eng.is_loaded:
        st.markdown(f'<div class="topbar"><div class="tb-logo">🏥</div>'
                    f'<div><div class="tb-sub">Interaction Conversion Index · Intelligence</div>'
                    f'<div class="tb-title">Healthcare Professional Conversion Atlas</div>'
                    f'</div></div>', unsafe_allow_html=True)
        _upload_screen()
        return

    # Full dashboard
    _topbar(eng.stats())
    _nav()
    st.markdown("<br>", unsafe_allow_html=True)

    cur      = st.session_state["view"]
    NO_FILTER = ("approach", "overview", "envelope", "crosstabs", "qualitative", "integrated")
    hcps     = (_filter_bar(eng.hcps_df)
                if cur not in NO_FILTER and not cur.startswith("cluster_")
                else eng.hcps_df)
    st.markdown("<br>", unsafe_allow_html=True)

    if cur == "approach":
        _load_module("approach").render(eng)
    elif cur == "overview":
        _load_module("overview").render(eng, hcps)
    elif cur == "integrated":
        _load_module("integrated").render(eng, eng.hcps_df)
    elif cur == "crosstabs":
        _load_module("crosstabs").render(eng)
    elif cur == "qualitative":
        _load_module("qualitative").render(eng)
    elif cur == "envelope":
        _load_module("envelope").render(eng, hcps)
    else:
        _load_module("overview").render(eng, hcps)

    st.markdown(
        f'<div style="font-size:11px;color:#94A3B8;border-top:1px solid {MGRAY};'
        f'padding-top:14px;margin-top:40px">'
        f'ATU × PET unified through the Interaction Conversion Index (ICI) · '
        f'7 dimensions · 5 engagement states · sequential resolution'
        f'</div>',
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
