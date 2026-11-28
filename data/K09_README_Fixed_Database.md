# Kidney Project: Fixed Database (21 November 2026)

Read-only. Models read these files; they never edit them. Any change creates a new version.
Labels in K01 are WORKING labels (curated seed + FAERS signal), not verified clinical labels.

- K00_Drug_Universe.csv: the 1,336-drug scaffold universe for this project, taken from a published FDA drug list.
- K01_Kidney_Labels.csv: per-drug kidney tier, hazard weight, FAERS kidney/total report counts, curated mechanism for seed drugs. Tiers: Established 46, Possible 341, Weak 524, No signal 425.
- K02_FAERS_2026Q3_Kidney_Combinations.csv: 3,753 reports with 2-4 mapped drugs.
- K03_FAERS_2026Q3_Kidney_Drug_Rows_Mapped.csv: 71,046 mapped drug rows from 14,542 kidney-PT reports.
- K04_FAERS_2026Q3_Kidney_PT_Counts.csv: 263 PTs captured by the keyword set (includes some non-injury terms; curation is planned update work).
- K05_Structure_Table_PubChem.csv: structures (PubChem; 1,230 of 1,336).
- K06_PK_Table_v1.csv: pharmacokinetic table v1 (label-sourced and verified).
- K07_Metabolites_v1.csv: metabolite list.
- K08_Structure_Alert_Matches.csv: 13-alert RDKit matches.
- K10_Drug_PK_Data.json: per-drug pharmacokinetic data file (Tmax, half-life, labelled maximum single dose) used by the temporal scenario engine.
