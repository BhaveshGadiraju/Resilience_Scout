# Provenance sidecar schema

Every dataset under `data/raw/` or `data/processed/` should have a matching YAML file in `data/provenance/`.

## Required fields

| Field | Type | Description |
|-------|------|-------------|
| `source` | string | Human-readable source name |
| `source_url` | string | Official URL |
| `retrieval_date` | ISO date | When we retrieved it |
| `original_filename_or_api` | string | Filename or API path |
| `license` | string \| null | License / usage note |
| `data_class` | enum | `observed` \| `derived` \| `predicted` \| `simulated` |
| `processing_steps` | string[] | What we did after retrieval |
| `preserves_original_values` | bool | True if values unchanged from source |
| `notes` | string \| null | Caveats |

## Implementation

Pydantic model: `backend/app/models/provenance.py`  
Helpers: `load_provenance`, `save_provenance`
