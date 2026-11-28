# Nephro Project: A Simple Guide

**Project:** Multi-Drug Combination Nephrotoxicity Risk Prediction (working name: NephMAT)
**Project lead:** Sabir Ali
**Date:** November 2026
**Code and data:** GitHub, ali7248-ui/NEPHRO-TOXICITY-RISK-PREDICTION (public, MIT License)
**Working files:** Google Drive, folder "Kidney Project" (Final work and Raw work)

This guide explains the whole project in simple words: what it is, how the computer calculates the risk, where every number came from, and what is still left to improve. It is written so that anyone can explain the project from it, including in front of a professor.

## 1. What is this project?

Some medicines are safe alone but can damage the kidneys when they are taken together. The best-known example is called the "triple whammy": a painkiller of the NSAID type (like ibuprofen), a blood-pressure medicine of the ACE inhibitor or ARB type (like lisinopril or losartan), and a water tablet, meaning a diuretic (like hydrochlorothiazide). Each one is routine. Together, they can cause acute kidney injury.

This project builds a computer model that takes a combination of 2 to 5 medicines and estimates the kidney risk of that combination over 24 hours. The output is simple: how high the combined kidney load rises, at what time it is highest, and for how many hours it stays above a danger line.

There is no ready-made, verified list in the world that ranks medicines by kidney damage, the way ranked lists exist for some other organs. That is why this project had to build its own database first, from public sources. Building that database honestly, and saying clearly which parts are verified and which parts are working assumptions, is a main part of this project.

## 2. How does the calculation work?

The model works in four layers. Think of it like cooking: first collect the ingredients (data), then weigh them (hazard), then follow the recipe over time (the 24-hour curve), then taste and check (the learning test).

**Layer 0, the fixed database.** All the raw material is collected once and frozen into files named K00 to K10. The rule of the project is strict: the model only reads these files, it never changes them. If anything is corrected, a new version is made. This makes every result repeatable.

**Layer 1, structure notes.** Every medicine has a chemical structure. The computer checks each structure against 13 known reactive patterns, called structural alerts. These are kept as notes, like warning flags on a file. They are not yet specific to the kidney, and the project says so openly.

**Layer 2, the 24-hour load, the heart of the project.** For each medicine in the combination, the computer draws a curve of how much of that medicine is in the body over 24 hours. The curve rises to a peak and then falls, using the standard one-compartment Bateman equation of pharmacokinetics. Each curve is then weighted:

Load of one medicine = hazard weight x dose fraction x curve height

- The hazard weight says how strongly that medicine is linked to kidney damage (see Section 3).
- The dose fraction is the dose given divided by the maximum single dose printed on the medicine's official label. A full dose counts fully, a half dose counts half.
- The curves of all the medicines are added together, hour by hour. The sum is the combined load.

From the combined curve, four numbers are read out: the peak load (the highest point), the time of the peak, the AUC (total exposure, the area under the curve), and the hours above the danger line of 0.75.

Kidney function is included as a patient factor. Kidney function is described in eGFR bands. In the severe impairment band (eGFR 15 to 29), medicines that leave the body through the kidney stay longer, so their half-lives are stretched in the model. This stretching currently uses simple fixed multipliers (see Section 3). This is marked as an assumption to be replaced by exact per-drug data in .

**Layer 3, the learning test.** Separately, a machine-learning model (Random Forest) is given only the chemical structure of each medicine and the 13 alert flags, and is asked: can you guess which medicines are established kidney-damaging ones? This tests how much signal is inside the structures alone. In the answer is: only a weak signal. That weak result is reported honestly, not hidden, because it tells us structure alone is not enough and the load model of Layer 2 is the real contribution.

## 3. Every important value, and where it came from

This is the most important section for a viva or a professor meeting. Every value in the project is either taken from an authentic public source, computed from such a source, or declared openly as a project assumption. Nothing is invented silently.

| Value | What it is | Authentic source |
|---|---|---|
| 1,336 medicines | The fixed drug list (universe) of the project | A published U.S. FDA drug database list of approved medicines (project file K00) |
| 421,404 reports | Total adverse-event reports processed | U.S. FDA FAERS quarterly data files, 2026 Q3, free public download from the FDA website |
| 14,542 reports | Reports that mention a kidney problem | Computed by the project code from the FAERS files, using a kidney keyword list (kidney, renal, nephr-, creatinine, glomerular, proteinuria, albuminuria, anuria, oliguria, dialysis, tubulointerstitial, blood urea increased) matched against the report terms (PTs) |
| 263 kidney terms (PTs) | Distinct kidney-related problem terms found | Computed from FAERS 2026 Q3 |
| 71,046 drug rows | Medicine entries inside the kidney reports, matched to the 1,336-drug list | Computed from FAERS 2026 Q3 |
| 3,753 reports | Reports containing 2 to 4 of the listed medicines together, the combination set | Computed from FAERS 2026 Q3 |
| 3,413 / 1,926 / 1,231 / 1,102 | Counts of the most common kidney terms: acute kidney injury, renal impairment, renal failure, blood creatinine increased | FAERS 2026 Q3, counted by the project code (full list in file K04) |
| 47 medicines (46 matched) | The seed list of established kidney-damaging medicines, each with its damage mechanism written down | Curated by the project from standard pharmacology references (textbook-level knowledge: aminoglycosides, vancomycin, amphotericin B, cisplatin, calcineurin inhibitors, lithium, tenofovir, NSAIDs, ACE inhibitors, ARBs, diuretics, methotrexate, acyclovir, and others), file K01 |
| 341 / 524 / 425 medicines | Label tiers "Possible", "Weak signal", "No signal" for the remaining medicines | Computed from FAERS counts: Possible means 20 or more kidney reports in the quarter, Weak means 1 to 19, No signal means 0 |
| 1.00 / 0.55 / 0.30 / 0.15 | Hazard weights of the four tiers (Established, Possible, Weak, No signal) | Project modelling choice, declared openly. There is no published weight table for this, so the project chose simple, explainable weights |
| Tmax, half-life, maximum single dose of each medicine | The pharmacokinetic values used to draw every curve | The official FDA-approved drug labels (prescribing information) of each medicine, compiled in files K06 and K10 |
| 1,230 medicines | Medicines for which a chemical structure was available | PubChem, the public chemistry database of the U.S. National Institutes of Health; structures stored as canonical SMILES text |
| 13 structural alerts | Reactive chemical patterns checked in every structure | Matched with the RDKit cheminformatics toolkit, a standard open-source tool (file K08) |
| 0.75 | The danger line (threshold) for the combined load | Project working threshold for , declared openly as a modelling choice |
| 0 to 24 hours, step 0.05 hours | The time grid of the calculation | Project computation setting |
| Half-life x2.0 (lisinopril, hydrochlorothiazide) and x1.25 (ibuprofen) in eGFR 15 to 29 | How much longer medicines stay in the body when kidney function is severely low | Illustrative project assumption, declared openly. A planned update will replace it with the exact renal clearance fraction of each drug from its label |
| All scenario results in Section 4 | Peak loads, peak times, AUC, hours above the line | Computed by the project code (file: kidney_temporal_and_baselines.py), run on 21 November 2026, results saved in Final work |
| AUROC 0.649, AUPRC 0.290, MCC -0.007 | Score of the learning test (Layer 3) | Computed by the project: Random Forest in scikit-learn, molecular fingerprints of 512 bits made by RDKit, 5-fold cross-validation, random seed 42, on 430 medicines (45 established, 385 no-signal) |
| AUROC 0.552 | Score when only the 13 alert flags are used, without fingerprints | Same computation as above |

One honest warning that belongs with this table: FAERS is a reporting system. A high count means a problem was reported often, not that it happens often in real patients. Counts are affected by how famous a medicine is and why it was given. The project uses FAERS as a signal source, never as proof of how common kidney damage is.

## 4. Results: what the model found

Danger line: 0.75. "Hours above" means hours spent above that line.

| Combination tested | Peak load | Peak at | AUC | Hours above |
|---|---|---|---|
| Triple whammy, all together: ibuprofen 400 mg + lisinopril 10 mg + hydrochlorothiazide 25 mg | 1.0648 | 1.70 h | 11.2037 | 4.30 |
| Triple whammy, ibuprofen delayed by 6 hours | 0.9763 | 7.40 h | 11.1992 | 3.25 |
| Triple whammy, severe kidney impairment (eGFR 15 to 29) | 1.0709 | 1.70 h | 13.7089 | 5.25 |
| Tenofovir 300 mg + ibuprofen 400 mg | 1.4902 | 1.35 h | 18.2299 | 9.40 |
| Ibuprofen 400 mg alone | 0.5000 | 1.50 h | 2.3682 | 0.00 |
| Control test: triple whammy + vitamin B12 (hazard set to 0 on purpose) | 1.0648 | 1.70 h | 11.2037 | 4.30 |

What these results say, in simple words:

1. The triple whammy crosses the danger line for 4.3 hours, while ibuprofen alone never crosses it. This is exactly the combination effect the project was built to catch: the danger is in the combination, not in one medicine.
2. Delaying the painkiller by 6 hours lowers the peak a little and shortens the danger time. Spacing medicines helps, but only a little here, because the other two medicines stay in the body for a long time.
3. In severe kidney impairment, the peak barely changes but the total exposure (AUC) rises from 11.20 to 13.71 and the danger time stretches from 4.30 to 5.25 hours. This is the accumulation effect: a weak kidney cannot clear medicines on time.
4. Tenofovir plus ibuprofen is the strongest combination tested, above the line for 9.4 hours.
5. The control test passes exactly: adding a medicine with hazard 0 changes nothing, which proves the addition logic of the model is working correctly.
6. The learning test (Layer 3) is weak: AUROC 0.649. Kidney damage happens by many different mechanisms (blood-flow, direct tube damage, allergy-type inflammation, crystals, and others), so one structure-based test cannot separate the medicines well. The project reports this honestly instead of decorating it.

## 5. Abbreviations used in this project

| Short form | Full form | Simple meaning |
|---|---|---|
| ACE inhibitor | Angiotensin-Converting Enzyme inhibitor | A blood-pressure medicine class (lisinopril, enalapril) |
| AKI | Acute Kidney Injury | Sudden kidney damage over hours to days |
| ARB | Angiotensin Receptor Blocker | A blood-pressure medicine class (losartan, valsartan) |
| AUC | Area Under the Curve | Total exposure of the body to the combined load over 24 hours |
| AUPRC | Area Under the Precision-Recall Curve | A score for the learning test, useful when positive cases are few |
| AUROC | Area Under the Receiver Operating Characteristic curve | The standard score of a prediction test: 0.5 is guessing, 1.0 is perfect |
| CSV | Comma-Separated Values | A simple table file format used for the project data |
| eGFR | estimated Glomerular Filtration Rate | The standard estimate of how well the kidneys filter blood, in mL/min/1.73 m2 |
| FAERS | FDA Adverse Event Reporting System | The U.S. FDA public database of reported medicine side effects |
| FDA | Food and Drug Administration | The U.S. medicine regulator |
| MCC | Matthews Correlation Coefficient | A balanced score of a prediction test, from -1 to +1 |
| MedDRA | Medical Dictionary for Regulatory Activities | The standard dictionary of medical terms used in FAERS reports |
| NIH | National Institutes of Health | The U.S. health research agency that runs PubChem |
| NSAID | Non-Steroidal Anti-Inflammatory Drug | Painkiller class (ibuprofen, diclofenac, naproxen) |
| PK | Pharmacokinetics | The study of how the body handles a medicine over time |
| PT | Preferred Term | One standard problem term in a FAERS report, for example "Acute kidney injury" |
| RDKit | RDKit cheminformatics toolkit | The open-source software used for structures, fingerprints and alerts |
| RF | Random Forest | The machine-learning method used in the learning test |
| SMARTS | SMILES Arbitrary Target Specification | The written pattern language used to search chemical structures |
| SMILES | Simplified Molecular Input Line Entry System | A chemical structure written as a line of text |
| Tmax | Time to maximum concentration | The time at which a medicine reaches its highest level in the blood |

## 6. What is complete, and what is next

**Complete now:** the fixed database (K00 to K10), the label system, the 24-hour load engine, the scenario results, the learning baseline, the full written compilation, a public GitHub repository with the code, data, README and MIT License, and a working demonstration website (Streamlit app) where anyone can build a combination and see its load curve and verdict.

**Honest limitations, and the improvement plan for each:**

1. The labels are working labels (a curated seed plus reporting signals), not clinically verified labels. A hand-checked kidney term list will replace the keyword list, which also caught a few non-injury terms like kidney stones (nephrolithiasis, 1,123 rows).
2. The kidney-function effect uses simple multipliers. The exact fraction of each drug removed by the kidney, taken from its official label.
3. The structural alerts are general, not kidney-specific. Kidney-specific mechanism classes (blood-flow, tube damage, inflammation, crystal, filtering-unit damage) as model features.
4. The scenario engine is calibrated on oral (by mouth) dosing, while some strong nephrotoxins in the list are given by injection.

**Data that would speed up the planned update, if asked for in a viva:** a checked list of kidney injury terms (MedDRA PTs), per-drug renal clearance fractions from labels for the main nephrotoxic medicines, and any hospital or literature dataset of verified nephrotoxic medicines to test the labels against.

## 7. Questions a professor may ask, with short answers

**Why FAERS?** Because it is the largest free, public, authentic source of real-world medicine side-effect reports, published by the U.S. FDA itself. We use it for signals, and we state its reporting limits openly.

**Why these hazard weights?** No published weight table exists for kidney combinations. We chose simple weights tied to evidence strength (established knowledge 1.00 down to no signal 0.15) and declared them as a modelling choice, so anyone can change them and repeat the work.

**Why is the threshold 0.75?** It is a working line for , chosen so that single routine medicines stay below it and known dangerous combinations cross it. The ibuprofen-alone and triple-whammy results show it behaving that way. Fixing a clinical threshold needs clinical data, which is future work.

**What is new in this project?** Three things: a kidney-first database built from public sources where none existed, a 24-hour combined-load method that adds the medicines' curves with hazard and dose weighting, and a kidney-function (eGFR) factor inside that load, tested on the classic triple-whammy combination.

**Why is the machine-learning score low?** Because kidney damage has many mechanisms and the labels are signal-based. We report 0.649 as it is. The load model, not the classifier, is the contribution of this work.

**Can anyone repeat this work?** Yes. Every source is public, the database files are frozen and named (K00 to K10), the code is on GitHub under the MIT License, and the control test (vitamin B12, hazard 0) verifies the engine's addition logic.

## 8. Where everything is kept

- **Google Drive, "Kidney Project" folder:** Final work holds the compilation, this guide, and the result files. Raw work holds the Databases (K00 to K10) and the Code (3 Python files).
- **GitHub:** github.com/ali7248-ui/NEPHRO-TOXICITY-RISK-PREDICTION, public, MIT License, copyright Sabir Ali. The website (Streamlit app) runs from this repository and updates automatically whenever the repository is updated.
- **Main files to know:** Kidney_Project_Compilation (the full technical document), Nephro_Project_Guide (this simple guide), kidney_scenarios.csv and kidney_metrics.json (the result files).
