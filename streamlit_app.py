"""Multi-Drug Combination Nephrotoxicity Risk Prediction

Project lead: Sabir Ali

Verdict-first Streamlit app. It estimates the combined nephrotoxic load of a
2-5 drug regimen over 24 hours by summing hazard-weighted, dose-scaled,
peak-normalised one-compartment Bateman concentration curves:

    Load_i(t) = H_i x F_i x C_i(t)

    H_i  kidney hazard weight from the working labels (data/K01)
    F_i  dose fraction = dose given / labelled maximum single dose (data/K10)
    C_i  Bateman curve from the drug's Tmax and half-life (data/K10)

The working danger threshold is 0.75. This is a research prototype built on
working (signal-based) labels, not a clinical tool. See README.md and the
"See the science" section in the app for methods, results and limitations.
"""

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).parent / "data"
THRESHOLD = 0.75
TIMES = np.round(np.arange(0, 24.0001, 0.05), 10)

# Renal impairment multipliers, exactly as documented for the
# eGFR 15-29 band: half-life x2.0 for lisinopril and hydrochlorothiazide,
# x1.25 for ibuprofen. No multipliers are defined for other bands
# or other drugs, so none are applied there.
EGFR_BANDS = {
    "eGFR 60 or above (no adjustment)": {},
    "eGFR 30-59 (no adjustment defined yet)": {},
    "eGFR 15-29 (severe impairment multipliers)": {
        "lisinopril": 2.0,
        "hydrochlorothiazide": 2.0,
        "ibuprofen": 1.25,
    },
}

# Default regimen: the documented headline scenario
# (ibuprofen 400 mg + lisinopril 10 mg + hydrochlorothiazide 25 mg).
PRESET = [
    ("ibuprofen", 400.0),
    ("lisinopril", 10.0),
    ("hydrochlorothiazide", 25.0),
]


@st.cache_data
def load_pk_data():
    with open(DATA_DIR / "K10_Drug_PK_Data.json") as f:
        return json.load(f)["drugs"]


@st.cache_data
def load_labels():
    labels = {}
    df = pd.read_csv(DATA_DIR / "K01_Kidney_Labels.csv")
    for _, row in df.iterrows():
        labels[str(row["CompoundName"]).lower()] = {
            "tier": row["KidneyTier"],
            "hazard": float(row["HazardWeight"]),
            "mechanism": row["CuratedMechanism"] if pd.notna(row["CuratedMechanism"]) else "",
        }
    return labels


@st.cache_data
def load_metrics():
    with open(DATA_DIR / "kidney_metrics.json") as f:
        return json.load(f)


def hazard_for(key, display, labels):
    lab = labels.get(key) or labels.get(display.lower())
    if lab:
        return lab["hazard"], lab["tier"]
    return 0.15, "No signal in FAERS 2026Q3 (default)"


def bateman_curve(tmax, half_life, times):
    """Peak-normalised one-compartment Bateman curve (same method as the
    Backend: solve ka by bisection so the peak lands on Tmax)."""
    ke = math.log(2) / half_life
    lo, hi = ke * 1.0001, 50.0
    for _ in range(80):
        mid = (lo + hi) / 2
        tp = math.log(mid / ke) / (mid - ke)
        if tp > tmax:
            lo = mid
        else:
            hi = mid
    ka = (lo + hi) / 2
    raw = np.exp(-ke * times) - np.exp(-ka * times)
    peak = raw.max()
    return raw / peak if peak > 0 else raw


def run_regimen(entries):
    """entries: list of dicts with curve inputs. Returns totals and parts."""
    total = np.zeros_like(TIMES)
    parts = {}
    for e in entries:
        hl = e["half_life"] * e.get("hl_mult", 1.0)
        frac = (e["dose_mg"] / e["ref_max_single_mg"]) if e.get("ref_max_single_mg") else 1.0
        curve = np.zeros_like(TIMES)
        shifted = TIMES - e.get("delay_h", 0.0)
        mask = shifted >= 0
        curve[mask] = bateman_curve(e["tmax"], hl, shifted[mask])
        load = e["hazard"] * frac * curve
        parts[e["display"]] = load
        total += load
    return total, parts


def summarise(total):
    peak = float(total.max())
    peak_t = float(TIMES[int(np.argmax(total))])
    auc = float(np.trapezoid(total, TIMES)) if hasattr(np, "trapezoid") else float(np.trapz(total, TIMES))
    hours_above = float((total >= THRESHOLD).sum() * 0.05)
    return peak, peak_t, auc, hours_above


def main():
    st.set_page_config(page_title="Nephrotoxicity Combination Risk", layout="wide")
    st.title("Multi-Drug Combination Nephrotoxicity Risk Prediction")
    st.caption(
        "Research prototype, project lead: Sabir Ali. Working labels, not "
        "clinically verified. Not a medical tool and not medical advice."
    )

    pk = load_pk_data()
    labels = load_labels()
    usable = {
        k: v for k, v in pk.items()
        if v.get("tmax") and v.get("half_life") and v.get("ref_max_single_mg")
    }
    by_display = {v["display"]: k for k, v in usable.items()}
    display_names = sorted(by_display)

    # ---------- Regimen builder ----------
    st.subheader("Build the regimen")
    egfr_label = st.selectbox("Kidney function (eGFR band)", list(EGFR_BANDS), index=0)
    multipliers = EGFR_BANDS[egfr_label]

    n_drugs = st.slider("Number of drugs", min_value=2, max_value=5, value=3)
    entries = []
    used = set()
    cols = st.columns(n_drugs)
    for i in range(n_drugs):
        with cols[i]:
            st.markdown(f"**Drug {i + 1}**")
            if i < len(PRESET) and PRESET[i][0] in usable:
                default_display = usable[PRESET[i][0]]["display"]
                default_dose = PRESET[i][1]
            else:
                default_display = display_names[i % len(display_names)]
                default_dose = None
            display = st.selectbox(
                "Drug", display_names,
                index=display_names.index(default_display),
                key=f"drug_{i}",
            )
            key = by_display[display]
            info = usable[key]
            if default_dose is None:
                default_dose = float(info["ref_max_single_mg"]) / 2.0
            dose = st.number_input(
                "Dose (mg)", min_value=0.0,
                value=float(default_dose), step=1.0, key=f"dose_{i}",
            )
            delay = st.number_input(
                "Delay / stagger (hours)", min_value=0.0, max_value=12.0,
                value=0.0, step=0.5, key=f"delay_{i}",
            )
            hazard, tier = hazard_for(key, display, labels)
            mult = multipliers.get(key, 1.0)
            entries.append({
                "key": key, "display": display, "dose_mg": dose, "delay_h": delay,
                "tmax": float(info["tmax"]), "half_life": float(info["half_life"]),
                "ref_max_single_mg": float(info["ref_max_single_mg"]),
                "hazard": hazard, "tier": tier, "hl_mult": mult,
            })
            used.add(key)
            st.caption(
                f"Kidney tier: {tier} (weight {hazard:.2f})  \n"
                f"Tmax {info['tmax']} h, half-life {info['half_life']} h"
                + (f" x {mult} in this eGFR band" if mult != 1.0 else "")
                + f"  \nLabelled max single dose: {info['ref_max_single_mg']:g} mg"
            )

    total, parts = run_regimen(entries)
    peak, peak_t, auc, hours_above = summarise(total)

    # ---------- Verdict first ----------
    st.subheader("Verdict")
    if peak >= THRESHOLD:
        st.error(
            f"HIGH combination load. Peak load {peak:.2f} crosses the working "
            f"threshold of {THRESHOLD} at {peak_t:.2f} h and stays above it for "
            f"about {hours_above:.2f} hours. In plain words: these drugs, at these "
            "doses and timings, overlap enough that their combined kidney load is "
            "in the range this model flags as dangerous. Staggering a dose or "
            "reducing a dose lowers the peak; try it above and watch this card."
        )
    elif peak >= 0.40:
        st.warning(
            f"MODERATE combination load. Peak load {peak:.2f} at {peak_t:.2f} h stays "
            f"below the working threshold of {THRESHOLD}, but the drugs do overlap. "
            "In plain words: no danger window in this run, though the combined load "
            "is well above what any one of these drugs produces alone."
        )
    else:
        st.success(
            f"LOW combination load. Peak load {peak:.2f} at {peak_t:.2f} h, far below "
            f"the working threshold of {THRESHOLD}. In plain words: at these doses "
            "and timings the combined kidney load stays low over 24 hours."
        )

    # ---------- How to read this result (plain language) ----------
    st.subheader("How to read this result")
    if hours_above > 0:
        window_text = (
            f"In this run the combined load stays at or above 0.75 for about "
            f"{hours_above:.2f} hours, and that stretch of time is the danger "
            "window the chart below shows."
        )
    else:
        window_text = (
            "In this run the combined load never reaches 0.75, so there is no "
            "danger window: the medicines overlap only weakly at these doses "
            "and timings."
        )
    st.markdown(
        f"**Peak load** is the highest point of the combined kidney load in "
        f"24 hours; here it is {peak:.2f}, reached at {peak_t:.2f} hours after "
        "the doses are taken. The line at **0.75** is this project's working "
        "danger line: it is a modelling choice, not a medical limit, and a "
        "peak above it means the medicines overlap strongly enough, for long "
        "enough, that the combination is flagged for attention. "
        + window_text
        + " The total exposure (AUC) adds up the whole 24-hour load, so a "
        "regimen can look acceptable on peak alone yet still carry a high "
        "total if the load stays up for many hours."
    )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Peak load", f"{peak:.4f}")
    m2.metric("Peak at", f"{peak_t:.2f} h")
    m3.metric("Total exposure (AUC)", f"{auc:.4f}")
    m4.metric(f"Hours above {THRESHOLD}", f"{hours_above:.2f}")

    # ---------- 24 h chart ----------
    st.subheader("Combined load over 24 hours")
    chart_df = pd.DataFrame({"Combined load": total, "Threshold 0.75": THRESHOLD}, index=TIMES)
    chart_df.index.name = "Hours"
    st.line_chart(chart_df)

    with st.expander("Per-drug load curves and regimen details"):
        parts_df = pd.DataFrame(parts, index=TIMES)
        parts_df.index.name = "Hours"
        st.line_chart(parts_df)
        detail = pd.DataFrame([{
            "Drug": e["display"],
            "Dose (mg)": e["dose_mg"],
            "Delay (h)": e["delay_h"],
            "Dose fraction of max single dose": round(
                e["dose_mg"] / e["ref_max_single_mg"], 3) if e["ref_max_single_mg"] else None,
            "Kidney tier": e["tier"],
            "Hazard weight": e["hazard"],
            "Tmax (h)": e["tmax"],
            "Half-life used (h)": round(e["half_life"] * e["hl_mult"], 2),
        } for e in entries])
        st.dataframe(detail, use_container_width=True)

    # ---------- Science ----------
    with st.expander("See the science: method, results and limitations"):
        metrics = load_metrics()
        st.markdown(
            "**Method.** Each drug contributes Load(t) = hazard weight x dose "
            "fraction x a peak-normalised Bateman concentration curve built from "
            "its Tmax and half-life. Loads are summed on a 0-24 h grid (0.05 h "
            "steps) against a working threshold of 0.75. Hazard weights come from "
            "the kidney labels: a curated seed of established nephrotoxins "
            "(weight 1.00) plus FAERS 2026Q3 signal tiers (Possible 0.55, Weak "
            "0.30, No signal 0.15). In the eGFR 15-29 band, the model multiplies the "
            "half-lives of lisinopril and hydrochlorothiazide by 2.0 and of "
            "ibuprofen by 1.25; these are illustrative factors, to be replaced "
            "by per-drug renal clearance fractions in a planned update."
        )
        st.markdown("**Documented scenarios** (from the project results file):")
        scen = pd.read_csv(DATA_DIR / "kidney_scenarios.csv")
        st.dataframe(scen, use_container_width=True)
        st.markdown("**Structure-learning baseline (reported as-is):**")
        base_rows = []
        for name, vals in metrics.get("baselines", {}).items():
            base_rows.append({"Model": name, **vals})
        if base_rows:
            st.dataframe(pd.DataFrame(base_rows), use_container_width=True)
        st.caption(
            f"Baseline set: {metrics.get('baseline_n')} drugs "
            f"({metrics.get('baseline_pos')} established nephrotoxins vs no-signal), "
            "Morgan fingerprints (512 bits) plus 13 structural alert flags, Random "
            "Forest, stratified 5-fold cross-validation. AUROC 0.649 is weak and "
            "is reported as such: nephrotoxicity is mechanism-diverse and the "
            "labels are signal-based."
        )
        st.markdown(
            "**Honest limitations.** (1) The labels are a curated seed plus "
            "reporting signals, not verified clinical labels; FAERS counts reflect "
            "reporting, not incidence. (2) The kidney term set used to build the "
            "labels is keyword-based and includes some non-injury terms; a curated "
            "term list is planned update work. (3) The eGFR half-life multipliers are "
            "illustrative global factors, not per-drug renal clearance data. "
            "(4) The structural alert layer is generic, not kidney-specific. "
            "(5) The scenario engine is calibrated on oral dosing, while some "
            "labelled nephrotoxins are parenteral-only. Nothing here is a "
            "clinical recommendation."
        )

    # ---------- Where the numbers come from ----------
    with st.expander("Where the numbers come from"):
        st.markdown(
            "Every value in this app traces back to one of the sources below. "
            "Project modelling choices are labelled as such, so a reader can "
            "always tell a measured or published value apart from an "
            "assumption made by this project.\n\n"
            "- **Drug list (the universe of medicines):** 1,336 FDA-approved "
            "medicines, taken from a published U.S. FDA drug database. This "
            "fixed list is the set of medicines the project can choose from.\n"
            "- **Adverse-event counts:** the U.S. Food and Drug "
            "Administration's FAERS public quarterly files for 2026 Q3: "
            "421,404 reports in total, of which 14,542 carried at least one "
            "kidney term. These counts are reports, not confirmed cases, and "
            "reflect reporting rather than true incidence.\n"
            "- **Kidney labels (which medicines count as kidney-harmful, and "
            "how strongly):** two parts. First, a curated list of established "
            "nephrotoxic medicines taken from standard pharmacology "
            "references, each with its injury mechanism recorded. Second, "
            "FAERS signal tiers for the remaining medicines, based on how "
            "many kidney reports each medicine had in the quarter. These are "
            "working labels for methods development; they are not clinically "
            "verified.\n"
            "- **PK values (Tmax, half-life, labelled maximum single dose):** "
            "taken from FDA-approved drug labels (the official prescribing "
            "information for each medicine).\n"
            "- **Chemical structures:** from PubChem, the public chemistry "
            "database maintained by the U.S. National Institutes of Health.\n"
            "- **Hazard weights (Established 1.00, Possible 0.55, Weak 0.30, "
            "No signal 0.15) and the 0.75 danger threshold:** project "
            "modelling choices. They are not published clinical values; they "
            "exist so that tiers can be combined into one load number and "
            "compared against one fixed line.\n"
            "- **Kidney-function (eGFR) multipliers:** in the eGFR 15-29 "
            "band, multiplies the half-lives of lisinopril and "
            "hydrochlorothiazide by 2.0 and of ibuprofen by 1.25. These are "
            "illustrative assumptions, recorded openly, and are to be "
            "replaced by per-drug renal clearance fractions in a planned update."
        )

    # ---------- Abbreviations ----------
    with st.expander("Abbreviations used"):
        st.markdown(
            "- **FAERS**: FDA Adverse Event Reporting System, the U.S. "
            "database where doctors, patients and companies report suspected "
            "side effects of medicines.\n"
            "- **PT**: Preferred Term, the standard medical wording used to "
            "name one reported side effect in FAERS.\n"
            "- **AKI**: Acute Kidney Injury, a sudden drop in kidney "
            "function over hours to days.\n"
            "- **eGFR**: estimated Glomerular Filtration Rate, a "
            "blood-test-based estimate of how well the kidneys filter.\n"
            "- **NSAID**: Non-Steroidal Anti-Inflammatory Drug, a common "
            "painkiller group (for example ibuprofen).\n"
            "- **ACE inhibitor**: Angiotensin-Converting Enzyme inhibitor, "
            "a blood-pressure medicine group (for example lisinopril).\n"
            "- **ARB**: Angiotensin Receptor Blocker, a blood-pressure "
            "medicine group (for example losartan).\n"
            "- **AUC**: Area Under the Curve, the total combined load added "
            "up over the full 24 hours.\n"
            "- **AUROC**: Area Under the Receiver Operating Characteristic "
            "curve, how well the learning model separates harmful from "
            "non-harmful medicines (0.5 is chance, 1.0 is perfect).\n"
            "- **AUPRC**: Area Under the Precision-Recall Curve, a similar "
            "model score that focuses on the harmful cases.\n"
            "- **MCC**: Matthews Correlation Coefficient, a single model "
            "quality score from -1 (always wrong) through 0 (chance) to "
            "+1 (perfect).\n"
            "- **PK**: Pharmacokinetics, how the body absorbs, moves and "
            "removes a medicine over time.\n"
            "- **Tmax**: the time after a dose when the medicine's level in "
            "the blood is at its highest.\n"
            "- **SMILES**: Simplified Molecular Input Line Entry System, a "
            "short text code that describes a medicine's chemical "
            "structure.\n"
            "- **RDKit**: a free software toolkit used to work with "
            "chemical structures and compute structure-based values.\n"
            "- **Streamlit**: the free Python framework this web app is "
            "built and run with.\n"
            "- **GitHub**: the website where this project's code and data "
            "files are stored and version-tracked."
        )


if __name__ == "__main__":
    main()
