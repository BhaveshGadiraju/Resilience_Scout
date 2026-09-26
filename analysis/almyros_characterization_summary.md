# Almyros characterization summary (Phase 2B)

- characterization_version: `2b.1`
- input rows: **587**
- indicators: **28**
- scale_anomaly rows: **448**
- years present: [2013, 2014, 2015, 2018, 2019, 2020, 2024, 2025]
- exploratory Spearman pairs (median, ≥4 yrs): **171**

## Modeling readiness (interpretive)

- **candidate** (19): aluminium_dissolved, ammonium, arsenic_dissolved, cadmium_dissolved, chloride, chromium_6, chromium_dissolved, copper_dissolved, dissolved_oxygen, electrical_conductivity, iron_dissolved, lead_dissolved, manganese_dissolved, mercury_dissolved, nickel_dissolved, nitrate, nitrite, sulphate, water_temperature
- **limited** (9): bicarbonate_hco3, calcium, carbonates, magnesium, ph, potassium, sodium, total_phosphates, zinc_dissolved
- **exclude** (0): none

## Primary statistic rule

- Prefer `median` for annual chemistry.
- Never use `mean` / `minimum` / `maximum` as primary when designing the future engine while `scale_anomaly` remains unresolved.
- Do not pool point samples with annual medians.

- output dir: `/Users/bhaveshgadiraju/Documents/Resilience_Scout/data/processed/almyros/characterization`
- provenance: `/Users/bhaveshgadiraju/Documents/Resilience_Scout/data/provenance/almyros_characterization.yaml`

See `docs/DATA_CHARACTERIZATION.md`. No observation values were rewritten.
