# Multi-Drug Combination Nephrotoxicity Risk Prediction

**Project lead:** Sabir Ali
**Status:** research prototype. Working labels, not clinically verified. Not a medical tool and not medical advice.

## What it does

Single drugs are routinely checked for kidney risk; combinations rarely are. This project estimates the **combined nephrotoxic load** of a regimen of 2-5 drugs over 24 hours, so that overlaps which are invisible drug-by-drug become visible:

- Each drug contributes `Load(t) = hazard weight x dose fraction x C(t)`, where `C(t)` is a peak-normalised one-compartment Bateman concentration curve built from the drug's Tmax and half-life, the dose fraction is the dose given divided by the labelled maximum single dose, and the hazard weight comes from the kidney labels.
- Loads are summed on a 0-24 h grid (0.05 h steps) and compared with a working threshold of **0.75**.
- The Streamlit app is verdict-first: a plain-language risk card, the peak load, peak time, total exposure (AUC) and hours above threshold, plus a 24-hour load chart. Doses can be staggered to see the effect of delaying a drug, and an eGFR band selector applies the renal impairment half-life multipliers (in the eGFR 15-29 band: half-life x2.0 for lisinopril and hydrochlorothiazide, x1.25 for ibuprofen; illustrative factors, documented as such).

The best-known combination injury in clinical pharmacology is renal: the "triple whammy" of an NSAID, an ACE inhibitor or ARB, and a diuretic. It is the headline test case below.

## Data sources

| File | Contents | Source |
|---|---|---|
| `data/K01_Kidney_Labels_.csv` | Per-drug kidney tier and hazard weight: curated seed of 46 established nephrotoxins with mechanisms, plus FAERS signal tiers (Possible 341, Weak 524, No signal 425) | Curated pharmacology seed + FAERS 2026Q3 |
| `data/K10_Drug_PK_Data.json` | Per-drug Tmax, half-life, labelled maximum single and daily dose, formulation, structural alert note (785 drugs; cleaned extract with the fields the app uses) | Drug labels |
| `data/K02_FAERS_2026Q3_Kidney_Combinations.csv` | 3,753 FAERS reports containing 2-4 mapped drugs | FDA FAERS 2026Q3 (421,404 reports; 14,542 with a kidney term) |
| `data/K05_Structure_Table_PubChem.csv` | Structures (SMILES) for 1,230 drugs, used by the baseline model | PubChem |
| `data/kidney_metrics.json`, `data/kidney_scenarios.csv` | computed results (below) | This project |
| `data/K09_README_Fixed_Database.md` | Fixed-database notes | This project |

Not shipped in this repo, to keep it light and app-focused: the row-level FAERS file (about 2.1 MB), the raw source-universe and metabolite tables, and the raw structural-alert match table. The app does not use them; the alert and structure information behind the published baseline is summarised in `kidney_metrics.json`, and the PK fields the app needs are in the cleaned K10 extract.

## results

Temporal scenarios (threshold 0.75):

| Scenario | Peak load | Peak at | AUC | Hours above |
|---|---|---|---|---|
| Triple whammy together (ibuprofen 400 mg + lisinopril 10 mg + hydrochlorothiazide 25 mg) | 1.0648 | 1.70 h | 11.2037 | 4.30 |
| Triple whammy, NSAID delayed 6 h | 0.9763 | 7.40 h | 11.1992 | 3.25 |
| Triple whammy, severe renal impairment (eGFR 15-29) | 1.0709 | 1.70 h | 13.7089 | 5.25 |
| Tenofovir 300 mg + ibuprofen 400 mg | 1.4902 | 1.35 h | 18.2299 | 9.40 |
| Ibuprofen 400 mg alone | 0.5000 | 1.50 h | 2.3682 | 0.00 |
| Control: triple whammy + vitamin B12 (hazard 0 by design) | 1.0648 | 1.70 h | 11.2037 | 4.30 |

Readings: the triple whammy crosses the threshold for hours while ibuprofen alone never does, which is the combination effect the project exists to capture. Severe renal impairment barely moves the peak but raises total exposure (AUC 11.20 to 13.71) and lengthens the danger window (4.30 to 5.25 h). Tenofovir plus an NSAID is the highest-load scenario tested. The zero-hazard control passes exactly.

Structure-learning baseline (established vs no-signal drugs, 430 drugs: 45 positive, 385 negative; Morgan fingerprints, 512 bits, plus 13 structural alert flags; Random Forest, stratified 5-fold cross-validation):

| Model | AUROC | AUPRC | MCC |
|---|---|---|---|
| Fingerprints + alerts | 0.649 | 0.290 | -0.007 |
| Alerts only | 0.552 | 0.140 | 0.000 |

These are weak numbers and are reported as such: nephrotoxicity is mechanism-diverse (haemodynamic, tubular, interstitial, crystal, glomerular), a single structure classifier is not expected to separate it, and the labels themselves are signal-based. The baseline exists to be beaten by later layers.

## Honest limitations

1. Labels are a curated seed plus reporting signals, not verified clinical labels; FAERS counts reflect reporting, not incidence, and are confounded by indication and notoriety.
2. The kidney term set used to build the labels is keyword-based and includes some non-injury terms; counts will change when the curated term list of replaces it.
3. The eGFR half-life multipliers are illustrative global factors, not per-drug renal clearance data.
4. The structural alert layer is generic and is not kidney-specific.
5. Parenteral-only nephrotoxins (aminoglycosides, vancomycin) are in the label set, but the scenario engine is calibrated on oral dosing.
6. No verified, ranked nephrotoxicity dataset exists; building one is the central difficulty of this project.

Next steps (): curated kidney term list and labels; per-drug renal clearance fractions from labels; kidney-specific mechanism classes as model features.

## Run it

Locally:

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

On Streamlit Cloud: create an app from this repository with `streamlit_app.py` as the entry point; `requirements.txt` and the `data/` folder are all it needs.

Dependencies are deliberately light: `streamlit`, `pandas`, `numpy`. The app itself needs no other packages; the baseline model behind the published metrics was computed offline.

## Repository layout

```
streamlit_app.py            the app (verdict-first)
requirements.txt
data/
  K01_Kidney_Labels_.csv
  K02_FAERS_2026Q3_Kidney_Combinations.csv
  K05_Structure_Table_PubChem.csv
  K09_README_Fixed_Database.md
  K10_Drug_PK_Data.json
  kidney_metrics.json
  kidney_scenarios.csv
```

## Licence and citation

Code in this repository is released under the MIT License (see `LICENSE`),
copyright Sabir Ali. The derived data tables in `data/` are shared under
CC BY 4.0: reuse is welcome with attribution to this project. Source data
remains under its original terms (FAERS is a public FDA resource; structures
are from PubChem).

To cite this work, use the "Cite this repository" button on GitHub, which
reads `CITATION.cff`.
