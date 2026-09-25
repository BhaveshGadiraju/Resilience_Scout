# DATA AUDIT — OneAquaHealth sources for Resilience Scout

**Audit date:** 2026-09-25  
**Rule:** Separate **VERIFIED FACTS** from assumptions. Anything not confirmed is marked **UNVERIFIED — DO NOT BUILD AROUND THIS YET**.

---

## Summary table

| Dataset | Official source | Real data? | Access | Locations | Indicators | Date range | Resolution | Candidate for Scout? |
| ------- | --------------- | ---------- | ------ | --------- | ---------- | ---------- | ---------- | -------------------- |
| OAH FHIR IG examples (FSH) | [github.com/hl7-eu/oah](https://github.com/hl7-eu/oah/tree/master/input/fsh/examples) | Yes — published example Observations | Public git raw download; no auth | Almyros, Giofyros, Benevento sites 01–12, Nordre Aker (Oslo) | Water chemistry, air pollutants, health prevalence (see below) | 2013-01-01 → 2025-04-14 | Annual summaries + point samples | **Yes — primary (Almyros)** |
| Resilience Map cities/sites API | [api.enora-oah.eu](https://api.enora-oah.eu/api/cities/all) | Yes — site registry | Public GET JSON; no auth observed | Coimbra, Toulouse, Ghent, Benevento, Oslo (106 sites) | Site metadata only | n/a | Spatial sites | Yes — for site context |
| Resilience Map health-risks | [api.enora-oah.eu/.../health-risks](https://api.enora-oah.eu/api/resilience-map/health-risks) | Yes — scored risks | Public GET JSON | 96 Benevento `BN*` site codes | healthRiskScore, scaledArgRisk, scaledFecalRisk, scaledPathogenRisk | 2023-05-05 → 2024-08-05 | Per sampling date | Yes — early-warning signal |
| Resilience Map urban-parameters | [api.enora-oah.eu/.../urban-parameters](https://api.enora-oah.eu/api/resilience-map/urban-parameters) | Yes — spatial covariates | Public GET JSON | 104 rows / researchSiteCode | Impervious %, urban %, veg cover, human density proxies, distances | samplingDate mostly null | Site-level (buffers 50–2000 m) | Yes — context / covariates |
| Resilience Map weather | `GET .../weather?siteCode=&start=&end=` | Yes — daily meteorology | Public GET with query params (ZonedDateTime) | Verified for site `C1` (Coimbra); pattern for other codes | t2m, RH, precip, wind, pressure, cloud, ssrd | Verified 2023-01-01 → 2024-12-31 (731 days for C1) | Daily | Yes — environmental drivers |
| Resilience Map UI CSV export | [apps.oneaquahealth.eu/resmap/v2](https://apps.oneaquahealth.eu/resmap/v2) | Client-side Blob from loaded data | No login for UI; CSV built in browser (`text/csv` Blob), not a bulk REST dump | Same as selected sites in UI | Depends on loaded panel | Selected date range | Client export | Partial — works after data load; no public bulk CSV API |
| HAF factsheets (Zenodo) | [DOI 10.5281/zenodo.20345207](https://doi.org/10.5281/zenodo.20345207) | Methodology PDF | Public download; CC BY 4.0 | Framework (multi-city intent) | Indicator definitions | n/a | n/a | Yes — candidate pool defs |
| HAF field sampling protocols | [DOI 10.5281/zenodo.20344420](https://doi.org/10.5281/zenodo.20344420) | Methodology PDF | Public download | Multi-site protocols | Sampling guidance | n/a | n/a | Supporting only |
| GEOSSIP | [oneaquahealth.eu/geossip](https://www.oneaquahealth.eu/geossip/) | Platform for authorized users | Auth required (documented) | Unknown publicly | Unknown publicly | Unknown | Unknown | **UNVERIFIED for Scout** |
| Citizen Science App | OAH Solutions / hackathon session | App exists | Public app; **no public observation dump verified** | Unknown | Unknown | Unknown | Unknown | **UNVERIFIED** |
| Live FHIR REST server | Mentioned in IG narrative | Unknown | No public base URL verified | — | — | — | — | **UNVERIFIED** |
| Published FHIR IG HTML/JSON package | [build.fhir.org/ig/hl7-eu/oah](https://build.fhir.org/ig/hl7-eu/oah/) | Was previously available | **HTTP 404 on 2026-09-25** for toc/downloads/examples.zip | — | — | — | — | Use GitHub FSH until CI build returns |

Stored copies: `data/raw/oah_fhir_ig_examples/`, `data/raw/resilience_map_api/`, provenance under `data/provenance/`.

---

## A. OAH FHIR implementation / data (VERIFIED from GitHub FSH)

**Source:** [hl7-eu/oah](https://github.com/hl7-eu/oah) `input/fsh/examples/` (25 example FSH files downloaded 2026-09-25).

**Access method:** HTTPS raw GitHub; no authentication.  
**Format:** FHIR Shorthand (`.fsh`) Observation / Location / Library / Group examples.  
**Note:** `build.fhir.org/ig/hl7-eu/oah` returned **404** at audit time; do not depend on the CI build URL until it recovers.

### Parsed inventory (derived)

Regex parse of Observation instances → `data/processed/oah_fhir_observation_inventory.csv` (**data_class: derived**; originals preserved in raw FSH).

| Metric | Value |
|--------|-------|
| Observation instances | **385** |
| Almyros (`Loc-Almyros`) | **135** |
| Giofyros | **6** |
| Date span | **2013-01-01 → 2025-04-14** |

### Sites with FHIR examples

| Site | Evidence | Role |
|------|----------|------|
| Almyros monitoring reach (Crete) | `water_tmp.fsh`, `almyros_gov_chem.fsh` | Primary aquatic chemistry |
| Giofyros reaches (Crete) | `water_tmp.fsh`, `ec_tmp.fsh` | Temp + conductivity point samples |
| Benevento monitoring sites 01–12 | `benevento_pollutant_*.fsh` | Air pollutants (not stream chemistry) |
| Nordre Aker (Oslo) | `os_*` examples | Health prevalence |

**Not present in FHIR example Locations:** Coimbra, Ghent, Toulouse aquatic series. Those cities **are** present in the Resilience Map sites API (see below).

### Almyros indicators (VERIFIED in FSH)

Water temperature; Conductivity / Electrical conductivity; Dissolved Oxygen; pH; Nitrate; Nitrite; Ammonium; Total phosphates; Chloride; Sulphate; Calcium; Magnesium; Sodium; Potassium; Carbonates; HCO3; metals (Al, As, Cd, Cr, Cr6+, Cu, Fe, Pb, Mn, Hg, Ni, Zn).

Mix of **annual government chemical summaries** (2013–2020) and **handheld point samples** (2024-11-21, 2025-04-14).

**Data quality flag (VERIFIED anomaly, do not silently fix):** For many annual summaries, Average/Max/Min component values are orders of magnitude larger than Median (e.g. DO, nitrate). Prefer **median** for analysis until OAH clarifies units/scaling.

### Giofyros indicators (VERIFIED)

Water temperature; Conductivity — point samples 2024-11-21 and 2025-04-14 (upper + lower reach where coded).

### Benevento FHIR (VERIFIED)

Benzene, NO2, O3, PM10, PM2.5 annual summaries (~2018–2019) + disease-prevalence cohort Observations.

### Oslo FHIR (VERIFIED)

Health prevalence (e.g. mental health issues by age/sex) for Nordre Aker — **not** aquatic physico-chemistry.

---

## B. Resilience Map (VERIFIED + partial)

**UI:** https://apps.oneaquahealth.eu/resmap/v2 — loads without login.  
**Backend base:** `https://api.enora-oah.eu/api` (discovered from frontend bundle).

### Cities (VERIFIED)

| id | name |
|----|------|
| CO | Coimbra |
| TO | Toulouse |
| GH | Ghent |
| BE | Benevento |
| OS | Oslo |

**106 research sites** (counts: Toulouse 24, Ghent 22, Coimbra 20, Benevento 20, Oslo 20).

**Crete (Almyros/Giofyros) is not in this city list.** User-generated sites endpoint returned additional named points (e.g. Agia) — treat as citizen/extra, not core research grid, until documented.

### Layers (from UI + JS paths)

| Layer group | Public API verified? | Notes |
|-------------|----------------------|-------|
| Health & Ecosystem / health-risks | Yes | Pathogen/fecal/ARG risk scores |
| Urban parameters | Yes | Urbanization / vegetation / density buffers |
| Weather | Yes with `siteCode`, `start`, `end` (ZonedDateTime) | Daily meteorological fields |
| Earth Observation | **UNVERIFIED** as public | Paths referenced in UI; GETs returned 401 or not confirmed |
| health-indicators | **UNVERIFIED** | HTTP 401 without auth |

### CSV export (VERIFIED behavior)

- Frontend builds CSV via `Blob([..], {type:"text/csv..."})` and triggers download (e.g. `health_risk_${site}_${dates}.csv`).
- This is **client-side export of already-fetched JSON**, not a separate authenticated bulk file server.
- Dedicated `/export` style API paths returned **HTTP 401** without credentials.

### Historical time series

- Health-risks: ~2023–2024 sampling dates (96 records).
- Weather: daily series when queried (731 days for C1 over 2023–2024 verified).
- Urban parameters: site covariates; `samplingDate` often null in downloaded JSON.

---

## C. Health Assessment Framework (VERIFIED as methodology)

- Project page: https://www.oneaquahealth.eu/health-assessment-framework-for-urban-aquatic-ecosystems/
- Factsheets: Zenodo DOI 10.5281/zenodo.20345207 (CC BY 4.0)
- Protocols: DOI 10.5281/zenodo.20344420
- Logical model in repo FSH: `IndicatorsOah.fsh` — biological, hydromorphological, water quality, bio-risk, remote sensing themes

These define **candidate next observations** for Scout. They are **not** themselves time-series datasets.

---

## Recommended first dataset for Phase 2 engine design

1. **Primary:** Almyros FHIR aquatic chemistry (135 Observations, 2013–2025) — richest verified stream chemistry.  
2. **Secondary:** Resilience Map health-risks + weather for Coimbra/Benevento sites — denser temporal coverage for early-warning prototyping.  
3. **Do not merge** Crete FHIR and ResMap five-city API as one spatial frame without an explicit join key (they do not share verified site IDs).

---

## UNVERIFIED — DO NOT BUILD AROUND THIS YET

- Live public FHIR R4 search server for OAH
- Resilience Map Earth Observation public time series / overlay APIs
- GEOSSIP downloads for hackathon participants without credentials
- Citizen Science App bulk observation export/API
- Coimbra/Ghent/Toulouse **aquatic chemistry** in FHIR examples (cities exist in ResMap only)
- Oslo aquatic monitoring in FHIR examples
- Formal license text for `api.enora-oah.eu` responses (UI is public; license not stated in JSON)
- Unit-corrected government summary averages (scale inconsistency vs medians)

---

## Evidence / local paths

| Artifact | Path |
|----------|------|
| FHIR FSH raw | `data/raw/oah_fhir_ig_examples/github_fsh/` |
| FHIR fetch manifest | `data/raw/oah_fhir_ig_examples/fetch_manifest.json` |
| ResMap API JSON | `data/raw/resilience_map_api/` |
| Derived observation inventory | `data/processed/oah_fhir_observation_inventory.csv` |
| Provenance sidecars | `data/provenance/*.yaml` |
| Indicator registry | `data/indicator_registry.yaml` |
