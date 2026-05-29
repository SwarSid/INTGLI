"""
Shared blurb utility — used by every view.
_blurb(label, body, source_q, value_a, value_b=None, label_a=None, label_b=None, p=None, n_a=None, n_b=None)
Renders a clickable insight chip that expands into a full data-derivation panel.
100% objective — every field maps to a real survey question or computed value.
"""
import streamlit as st

TEAL="#0F4C5C"; NAVY="#1E293B"; CRIMSON="#832232"; AMBER="#B8860B"; GREEN="#15803D"
LGRAY="#F8FAFC"; MGRAY="#E2E8F0"; DGRAY="#64748B"

_counter = [0]  # module-level counter for unique keys

def _sig_badge(p):
    if p is None: return ""
    if p < 0.05:
        return f'<span style="background:#15803D;color:white;padding:2px 8px;border-radius:4px;font-size:10px;font-weight:700">✓ Significant p={p}</span>'
    if p < 0.10:
        return f'<span style="background:#FBBF24;color:#0F172A;padding:2px 8px;border-radius:4px;font-size:10px;font-weight:700">~ Approaching sig p={p}</span>'
    return f'<span style="background:#F1F5F9;color:#64748B;padding:2px 8px;border-radius:4px;font-size:10px">p={p} not significant</span>'


def insight(label, headline, how_derived, source_q, value_a, value_b=None,
            label_a=None, label_b=None, p=None, n_a=None, n_b=None,
            key_suffix=None, sig_note=None):
    """
    Render a clickable insight row.

    label       : short chip label shown inline (e.g. "IBC = 26.9")
    headline    : one-sentence plain-English statement (the insight)
    how_derived : paragraph explaining the exact computation step by step
    source_q    : survey question code(s) and full question text
    value_a     : primary value shown (Group A mean / overall figure)
    value_b     : comparison value (Group B mean), optional
    label_a/b   : group labels
    p           : p-value from statistical test, optional
    n_a/n_b     : sample sizes
    key_suffix  : string to make expander key unique
    sig_note    : override note on significance interpretation
    """
    _counter[0] += 1
    uid = key_suffix or str(_counter[0])

    # Determine border color based on significance
    if p is not None and p < 0.05:
        border = GREEN
    elif p is not None and p < 0.10:
        border = AMBER
    else:
        border = TEAL

    # Inline chip row
    delta_html = ""
    if value_b is not None and label_a and label_b:
        try:
            delta = float(str(value_a).replace('%','')) - float(str(value_b).replace('%',''))
            delta_color = GREEN if delta > 0 else CRIMSON
            delta_html = f'&nbsp;<span style="color:{delta_color};font-weight:700">{"+"+str(round(delta,1)) if delta>0 else round(delta,1)}</span>'
        except: pass

    with st.expander(f"↳  {headline}"):
        st.markdown(f"""
<div style="background:{LGRAY};border-left:4px solid {border};border-radius:0 12px 12px 0;padding:18px 20px">

  <div style="font-size:10px;text-transform:uppercase;letter-spacing:.22em;color:{border};font-weight:700;margin-bottom:10px">
    DATA DERIVATION · OBJECTIVE · FROM UPLOADED FILES ONLY
  </div>

  {"<div style='display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:14px'>" +
   f"<div style='background:white;border-radius:8px;padding:12px 14px;border-top:3px solid {TEAL}'><div style='font-size:9px;text-transform:uppercase;letter-spacing:.15em;color:{TEAL};font-weight:700;margin-bottom:4px'>{label_a.upper() if label_a else 'VALUE A'}</div><div style='font-size:28px;font-weight:700;color:#0F172A;line-height:1'>{value_a}</div><div style='font-size:11px;color:{DGRAY};margin-top:2px'>n = {n_a if n_a else '—'}</div></div>" +
   f"<div style='background:white;border-radius:8px;padding:12px 14px;border-top:3px solid {CRIMSON}'><div style='font-size:9px;text-transform:uppercase;letter-spacing:.15em;color:{CRIMSON};font-weight:700;margin-bottom:4px'>{label_b.upper() if label_b else 'VALUE B'}</div><div style='font-size:28px;font-weight:700;color:#0F172A;line-height:1'>{value_b}</div><div style='font-size:11px;color:{DGRAY};margin-top:2px'>n = {n_b if n_b else '—'}</div></div>" +
   "</div>"
   if value_b is not None and label_a and label_b else
   f"<div style='background:white;border-radius:8px;padding:12px 14px;border-top:3px solid {TEAL};display:inline-block;margin-bottom:14px'><div style='font-size:9px;text-transform:uppercase;letter-spacing:.15em;color:{TEAL};font-weight:700;margin-bottom:4px'>{label_a.upper() if label_a else 'VALUE'}</div><div style='font-size:28px;font-weight:700;color:#0F172A'>{value_a}</div>{'<div style=font-size:11px;color:' + DGRAY + ';margin-top:2px>n = ' + str(n_a) + '</div>' if n_a else ''}</div><br>"}

  <div style="background:white;border-radius:8px;padding:12px 14px;margin-bottom:12px">
    <div style="font-size:10px;text-transform:uppercase;letter-spacing:.15em;color:{NAVY};font-weight:700;margin-bottom:6px">HOW THIS NUMBER WAS DERIVED</div>
    <div style="font-size:12px;color:#334155;line-height:1.65">{how_derived}</div>
  </div>

  <div style="background:white;border-radius:8px;padding:12px 14px;margin-bottom:12px">
    <div style="font-size:10px;text-transform:uppercase;letter-spacing:.15em;color:{NAVY};font-weight:700;margin-bottom:6px">EXACT SOURCE QUESTION(S)</div>
    <div style="font-size:12px;color:#334155;line-height:1.65;font-style:italic">{source_q}</div>
  </div>

  {f'<div style="background:#F0FDF4;border-radius:8px;padding:10px 14px;border-left:3px solid {border}">'
   f'<div style="font-size:10px;text-transform:uppercase;letter-spacing:.15em;color:{border};font-weight:700;margin-bottom:4px">STATISTICAL TEST</div>'
   f'<div style="font-size:12px;color:#334155">{_sig_badge(p)} &nbsp; {sig_note or ("Statistically significant at p<0.05 — this difference is unlikely due to chance." if p is not None and p < 0.05 else "Not statistically significant at p<0.05. Treat as directional only." if p is not None else "")}</div>'
   f'</div>'
   if p is not None else ""}

</div>
""", unsafe_allow_html=True)
