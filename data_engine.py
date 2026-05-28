"""
DataEngine: reads raw ATU + PET files by question-code scanning,
computes ICI sub-scores, clusters every HCP, and builds the
cross-tab/qualitative datasets.
"""

import pandas as pd
import numpy as np
import io
import re
from pathlib import Path
from scipy import stats as scipy_stats


# ── Label maps ─────────────────────────────────────────────────────────────────
FAM_MAP = {
    "Never heard of it": 1,
    "Heard of it, but don't know anything about it": 2,
    "Familiar with it, but not yet planning to use": 3,
    "Planning to use, but have not yet had opportunity": 4,
    "Have used it to treat IDH-mutant astrocytoma or oligodendroglioma": 5,
}
NCCN_MAP = {
    "Never heard of it": 1,
    "Heard of it, but don't know anything about it": 2,
    "A little familiar": 3,
    "Somewhat familiar": 4,
    "Very familiar": 5,
}
PTINQ_MAP = {"Very often": 4, "Occasionally": 3, "Rarely": 2, "Never": 1}
PEER_MAP = {
    "Yes, but only within my practice": 2,
    "Yes, with my practice and my extended peer network": 3,
    "No": 0,
    "Not yet, but intend to": 1,
}

VA_LABELS = {
    79: "Product brochure",
    80: "Package insert / PI",
    81: "Patient support services",
    82: "Co-pay cards / voucher",
    83: "Patient brochures",
    84: "Disease state info",
    85: "Product access / reimbursement toolkit",
    86: "Product distribution info",
    87: "Product admin / mgmt guide",
    88: "Product summary / flashcard",
}

ATTR_LABELS = [
    "Prolonged PFS", "Reduction in tumor volume", "Prolonged OS",
    "Low grade 3-4 AEs", "Low hepatic toxicity", "Low hematological toxicity",
    "Low neurotoxicity", "Low risk hypermutations", "Manageable LFT monitoring",
    "Good patient QoL", "Affordable", "Manufacturer patient services",
    "Easy to prescribe", "Convenient route", "Low risk long-term SEs",
    "Ability to preserve fertility", "Delays next treatment",
    "Reduces seizures", "Fair office compensation",
]


def _tn(v, d=0):
    try:
        return float(v)
    except Exception:
        return d


def _ms(v, mapping, d=0):
    if pd.isna(v):
        return d
    sv = str(v).strip()
    return mapping.get(sv, d)


def _read_raw(src):
    """Read Excel, return (raw_df, qcode_row_idx, data_start_idx)."""
    if isinstance(src, (str, Path)):
        raw = pd.read_excel(src, header=None)
    else:
        raw = pd.read_excel(io.BytesIO(src), header=None)
    return raw


def _find_qcode_row(raw):
    """Return row index where question codes like Q2_10Z appear."""
    for i in range(min(8, len(raw))):
        row = raw.iloc[i]
        if any(re.match(r"[QCS]\d+_\d+", str(v)) for v in row.values):
            return i
    return 2  # default


class DataEngine:
    def __init__(self):
        self.atu_raw = None
        self.pet_raw = None
        self.atu_qcodes = None
        self.pet_qcodes = None
        self.atu = None
        self.pet = None
        self.hcps_df = None
        self.xtab_df = None
        self._errors = []

    # ── Loading ───────────────────────────────────────────────────────────────
    def load_project(self):
        """Load from /mnt/project if running locally. On Streamlit Cloud this
        path won't exist — return an empty engine so the upload UI shows."""
        p = Path("/mnt/project")
        atu_path = p / "GLIOMA_ATU_Q126_Q226.xlsx"
        pet_path = p / "GLIOMA_PET_Q425_Q126_Q226.xlsx"
        if atu_path.exists() and pet_path.exists():
            self._load(atu_path, pet_path)
        # If files don't exist (Streamlit Cloud), engine stays empty —
        # app.py will show the upload UI instead.

    def load_from_bytes(self, atu_bytes, pet_bytes):
        self._load(atu_bytes, pet_bytes)

    @property
    def is_loaded(self):
        return self.hcps_df is not None and not self.hcps_df.empty

    def _load(self, atu_src, pet_src):
        self.atu_raw = _read_raw(atu_src)
        self.pet_raw = _read_raw(pet_src)

        atu_qrow = _find_qcode_row(self.atu_raw)
        pet_qrow = _find_qcode_row(self.pet_raw)

        self.atu_qcodes = self.atu_raw.iloc[atu_qrow].values
        self.pet_qcodes = self.pet_raw.iloc[pet_qrow].values

        self.atu = self.atu_raw.iloc[atu_qrow + 1:].reset_index(drop=True)
        self.pet = self.pet_raw.iloc[pet_qrow + 1:].reset_index(drop=True)

        # Normalize User Id — col index 1 may be int or str depending on platform
        def _get_uid_col(df):
            for key in [1, "1"]:
                if key in df.columns:
                    return df[key]
            return df.iloc[:, 1]

        self.atu["uid"] = pd.to_numeric(_get_uid_col(self.atu), errors="coerce")
        self.pet["uid"] = pd.to_numeric(_get_uid_col(self.pet), errors="coerce")
        self.atu = self.atu.dropna(subset=["uid"])
        self.pet = self.pet.dropna(subset=["uid"])
        self.atu["uid"] = self.atu["uid"].astype(int)
        self.pet["uid"] = self.pet["uid"].astype(int)

        self._build_hcps()
        self._build_xtab_dataset()

    # ── Column helpers ────────────────────────────────────────────────────────
    def _ac(self, prefix):
        return [i for i, v in enumerate(self.atu_qcodes) if str(v).startswith(prefix)]

    def _pc(self, prefix):
        return [i for i, v in enumerate(self.pet_qcodes) if str(v).startswith(prefix)]

    # ── HCP extraction ────────────────────────────────────────────────────────
    def _build_hcps(self):
        overlap_ids = sorted(set(self.atu["uid"]) & set(self.pet["uid"]))
        q220a = self._ac("Q2_20Z")
        q3120a = self._ac("Q3_120Z")
        q4300a = self._ac("Q4_30Z")

        records = []
        for uid in overlap_ids:
            a = self.atu[self.atu["uid"] == uid].iloc[0]
            p = self.pet[self.pet["uid"] == uid].iloc[0]

            # Patient load
            gc = self._ac("S0_120Z")
            gr2_pl = max(
                _tn(a[gc[0]] if gc else 0, 0)
                + _tn(a[gc[1]] if len(gc) > 1 else 0, 0),
                1,
            )

            # ── AC inputs ──
            unaided = int(
                any(
                    t in str(a[c] if not pd.isna(a[c]) else "").lower()
                    for c in self._ac("Q2_10Z")
                    for t in ["voranigo", "vorasidenib", "voras"]
                )
            )
            vf = q220a[10] if len(q220a) > 10 else None
            vora_fam = _ms(a[vf] if vf is not None else np.nan, FAM_MAP) or 1
            pt_inq = _ms(a[612] if 612 < len(a) else np.nan, PTINQ_MAP) or 1
            q210p = self._pc("Q2_10Z")
            msg_rec = sum(1 for c in q210p if _tn(p[c], 0) == 1)

            # ── IBC inputs ──
            curr_vora = min(
                sum(
                    _tn(a[self._ac(f"Q3_60Z_{pt}")[7]], 0)
                    for pt in range(1, 13)
                    if len(self._ac(f"Q3_60Z_{pt}")) > 7
                ),
                gr2_pl,
            )
            fut = sum(
                _tn(a[self._ac(f"Q3_60Z_{pt}")[19]], 0)
                for pt in range(1, 13)
                if len(self._ac(f"Q3_60Z_{pt}")) > 19
            )
            future_intent = min(fut / 10.0, 10.0)
            agreed = 1 if str(p[165] if 165 < len(p) else "N").strip().upper() in ["Y", "YES", "1"] else 0
            peer_shared = PEER_MAP.get(str(p[167] if 167 < len(p) else "").strip(), 0)
            like_inc = _tn(p[169] if 169 < len(p) else 4, 4)

            # ── MBC inputs ──
            vp = [_tn(a[c], np.nan) for c in q3120a[20:39]]
            vp = [v for v in vp if not np.isnan(v) and v > 0]
            top_attr_perf = np.mean(vp) if vp else 4.0
            q340p = self._pc("Q3_40BZ")
            attr_shift = sum(1 for c in q340p if _tn(p[c], 0) >= 6)
            q220p = self._pc("Q2_20Z")
            mv = [_tn(p[c], 0) for c in q220p if _tn(p[c], 0) > 0]
            motiv_score = np.mean(mv) if mv else 3.0
            q1100p = self._pc("Q1_100Z")
            access_va = min(sum(1 for c in q1100p if _tn(p[c], 0) == 1), 3)

            # ── RTC inputs ──
            q370p = self._pc("Q3_70Z")
            cqv = [_tn(p[c], np.nan) for c in q370p]
            cqv = [v for v in cqv if not np.isnan(v) and v > 0]
            call_quality = np.mean(cqv) if cqv else 5.0
            q360p = self._pc("Q3_60Z")
            pkv = [_tn(p[c], np.nan) for c in q360p]
            pkv = [v for v in pkv if not np.isnan(v) and v > 0]
            prod_knowledge = np.mean(pkv) if pkv else 5.0
            rep_pref = 1 if any(_tn(a[c], 0) == 1 for c in q4300a[:2]) else 0

            # ── ABR inputs ──
            s1_fam = _tn(a[586] if 586 < len(a) else 1, 1)
            q3260b = self._ac("Q3_260BZ")
            progs_known = sum(1 for c in q3260b if _tn(a[c], 0) == 1)
            q3220a = self._ac("Q3_220Z")[:9]
            barriers = sum(1 for c in q3220a if _tn(a[c], 0) == 1)
            access_concern = max(0, 3 - access_va)

            # ── KCC inputs ──
            q100a = self._ac("Q1_00Z")
            ngs_rate = min(max(sum(_tn(a[c], 0) for c in q100a[1:3]) / 100.0, 0), 1)
            q170a = self._ac("Q1_70Z")[:12]
            markers_50 = sum(1 for c in q170a if _tn(a[c], 0) > 50)
            q400a = self._ac("Q4_00Z")[:8]
            bv = [_tn(a[c], np.nan) for c in q400a]
            bv = [v for v in bv if not np.isnan(v) and v > 0]
            belief_align = np.mean(bv) if bv else 4.5
            nccn_fam = _ms(a[129] if 129 < len(a) else np.nan, NCCN_MAP) or 3
            dse = 1 if "Apply it" in str(p[50] if 50 < len(p) else "") else 0

            # ── CI inputs ──
            ip = [_tn(a[c], np.nan) for c in q3120a[40:59]]
            ip = [v for v in ip if not np.isnan(v) and v > 0]
            ivo_avg = np.mean(ip) if ip else 4.0
            vora_gap = round((np.mean(vp) if vp else 4.0) - ivo_avg, 2)
            cf = [q220a[4], q220a[6], q220a[7]] if len(q220a) > 7 else []
            comp_fam = round(np.mean([_tn(a[c], 1) for c in cf]) if cf else 2.5, 2)

            # ── VA flags ──
            va_used = {VA_LABELS.get(c, f"VA{c}"): int(_tn(p[c], 0) == 1) for c in range(79, 89) if c < len(p)}
            any_va = int(any(va_used.values()))

            # ── LTIP (top2 = 6,7) ──
            ltip_raw = _tn(p[169] if 169 < len(p) else 4, 4)
            ltip_top2 = int(ltip_raw >= 6)

            # ── ServierONE ──
            servier_aware = int(progs_known > 0 or s1_fam >= 3)

            # ── Specialty / setting ──
            specialty = str(a[48] if 48 < len(a) else "").strip()
            if not specialty or specialty == "nan":
                specialty = "Unknown"
            setting_raw = str(a[52] if 52 < len(a) else "").strip()
            if "Academic" in setting_raw or "Teaching" in setting_raw:
                setting = "Academic"
            elif "Community" in setting_raw or "Private" in setting_raw:
                setting = "Community"
            elif "VA" in setting_raw or "Network" in setting_raw:
                setting = "Integrated Network"
            else:
                setting = "Other"

            load_str = "High" if gr2_pl >= 15 else "Medium" if gr2_pl >= 6 else "Low"

            # ── ICI calculation ──
            ac_raw = (
                unaided * 100 * 0.4
                + (vora_fam - 1) / 4 * 100 * 0.3
                + (pt_inq - 1) / 3 * 100 * 0.1
                + msg_rec / 14 * 100 * 0.2
            )
            ac = min(ac_raw, 55) if unaided == 0 else ac_raw

            ibc = (
                min(curr_vora / gr2_pl, 1) * 100 * 0.35
                + future_intent / 10 * 100 * 0.25
                + (5.0 - 1) / 6 * 100 * 0.05
                + agreed * 100 * 0.2
                + peer_shared / 3 * 100 * 0.1
                + (like_inc - 1) / 6 * 100 * 0.05
            )

            mbc_raw = (
                msg_rec / 10 * 100 * 0.2
                + motiv_score / 5 * 100 * 0.3
                + (top_attr_perf - 1) / 6 * 100 * 0.3
                + attr_shift / 16 * 100 * 0.2
            )
            mbc = min(mbc_raw, 45) if attr_shift == 0 else mbc_raw

            rtc = (
                call_quality / 7 * 100 * 0.35
                + prod_knowledge / 7 * 100 * 0.35
                + rep_pref * 100 * 0.2
                + peer_shared / 3 * 100 * 0.1
            )

            fam_s = (s1_fam - 1) / 4 * 100 * (
                0.5 if (s1_fam >= 4 and progs_known == 0) else 1.0
            )
            abr = (
                progs_known / 5 * 100 * 0.30
                + fam_s * 0.20
                + max(0, 100 - barriers * 14.3) * 0.25
                + access_va / 3 * 100 * 0.15
                + max(0, 100 - access_concern * 20) * 0.10
            )

            kcc = (
                ngs_rate * 100 * 0.20
                + markers_50 / 12 * 100 * 0.20
                + (belief_align - 1) / 6 * 100 * 0.25
                + (nccn_fam - 1) / 4 * 100 * 0.20
                + dse * 100 * 0.15
            )

            ci = (
                max(0, min((vora_gap + 1.5) / 5 * 100, 100)) * 0.40
                + max(0, 100 - (comp_fam - 1) / 4 * 100) * 0.30
                + 50 * 0.30
            )

            ici = (
                ac * 0.14 + ibc * 0.25 + mbc * 0.20
                + rtc * 0.13 + abr * 0.15 + kcc * 0.08 + ci * 0.05
            )

            # ── Cluster ──
            if ibc < 35 or gr2_pl < 3:
                cluster = 1
            elif ibc >= 35 and abr < 45:
                cluster = 2
            elif mbc < 35 and rtc < 55:
                cluster = 3
            elif ac >= 50 and mbc < 55 and ibc < 70:
                cluster = 4
            else:
                cluster = 5

            # Q3_110Z importance ratings (adjuvant column group A1)
            q3110a = self._ac("Q3_110Z")
            attr_importance = {}
            for idx, label in enumerate(ATTR_LABELS):
                c_idx = q3110a[idx] if idx < len(q3110a) else None
                attr_importance[f"imp_{label}"] = _tn(a[c_idx], np.nan) if c_idx else np.nan

            # Q3_120Z Voranigo performance
            vora_perf = {}
            for idx, label in enumerate(ATTR_LABELS[:19]):
                c_idx = q3120a[20 + idx] if (20 + idx) < len(q3120a) else None
                vora_perf[f"perf_{label}"] = _tn(a[c_idx], np.nan) if c_idx else np.nan

            # Q3_50Z patient counts
            q350a = self._ac("Q3_50Z")
            total_gr2 = sum(_tn(a[c], 0) for c in q350a[:6]) if q350a else gr2_pl

            rec = {
                "uid": uid,
                "specialty": specialty,
                "setting": setting,
                "load": load_str,
                "gr2_pl": gr2_pl,
                "unaided": unaided,
                "vora_fam": vora_fam,
                "pt_inq": pt_inq,
                "msg_rec": msg_rec,
                "curr_vora": curr_vora,
                "curr_vora_share": round(curr_vora / max(gr2_pl, 1) * 100, 1),
                "future_intent": round(future_intent, 1),
                "agreed": agreed,
                "peer_shared": peer_shared,
                "like_inc": round(like_inc, 1),
                "ltip_top2": ltip_top2,
                "top_attr_perf": round(top_attr_perf, 2),
                "attr_shift": attr_shift,
                "motiv_score": round(motiv_score, 2),
                "any_va": any_va,
                "access_va": access_va,
                "call_quality": round(call_quality, 2),
                "prod_knowledge": round(prod_knowledge, 2),
                "rep_pref": rep_pref,
                "progs_known": progs_known,
                "s1_fam": s1_fam,
                "servier_aware": servier_aware,
                "barriers": barriers,
                "ngs_rate": round(ngs_rate, 2),
                "markers_50": markers_50,
                "belief_align": round(belief_align, 2),
                "nccn_fam": nccn_fam,
                "dse": dse,
                "vora_gap": vora_gap,
                "comp_fam": comp_fam,
                "AC": round(ac, 1),
                "IBC": round(ibc, 1),
                "MBC": round(mbc, 1),
                "RTC": round(rtc, 1),
                "ABR": round(abr, 1),
                "KCC": round(kcc, 1),
                "CI": round(ci, 1),
                "ICI": round(ici, 1),
                "cluster": cluster,
                "cluster_name": {
                    1: "Patient ID Priority",
                    2: "Access Pending",
                    3: "Evidence Gap",
                    4: "Narrative Build",
                    5: "Conviction-Led",
                }[cluster],
                "total_gr2_q350": total_gr2,
            }
            rec.update(va_used)
            rec.update(attr_importance)
            rec.update(vora_perf)
            records.append(rec)

        self.hcps_df = pd.DataFrame(records)

    def _build_xtab_dataset(self):
        """Merge ATU + PET on uid for cross-tab analysis."""
        if self.hcps_df is None:
            return
        self.xtab_df = self.hcps_df.copy()

    # ── Stats ─────────────────────────────────────────────────────────────────
    def stats(self):
        atu_n = self.atu["uid"].nunique() if self.atu is not None else 0
        pet_n = self.pet["uid"].nunique() if self.pet is not None else 0
        ov_n = len(self.hcps_df) if self.hcps_df is not None else 0
        return {
            "atu_n": atu_n,
            "pet_n": pet_n,
            "overlap_n": ov_n,
            "atu_waves": "Q1+Q2",
            "pet_waves": "Q4+Q1+Q2",
        }
