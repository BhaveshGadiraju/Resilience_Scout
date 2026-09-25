#!/usr/bin/env python3
"""Download official OneAquaHealth FHIR IG example sources into data/raw/.

Primary source: GitHub hl7-eu/oah FSH examples (authoritative when CI build 404s).
Also attempts build.fhir.org package URLs when available.
Does not invent observations.
"""

from __future__ import annotations

import json
import re
import sys
import zipfile
from datetime import date
from io import BytesIO
from pathlib import Path

import httpx

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.models.provenance import DataClass, ProvenanceRecord, save_provenance  # noqa: E402

IG_BASE = "https://build.fhir.org/ig/hl7-eu/oah"
DOWNLOADS_URL = f"{IG_BASE}/downloads.html"
GITHUB_API_TREE = "https://api.github.com/repos/hl7-eu/oah/git/trees/master?recursive=1"
GITHUB_RAW = "https://raw.githubusercontent.com/hl7-eu/oah/master/"
OUT_DIR = REPO_ROOT / "data" / "raw" / "oah_fhir_ig_examples"
PROVENANCE_PATH = REPO_ROOT / "data" / "provenance" / "oah_fhir_ig_examples.yaml"

CANDIDATE_PACKAGE_URLS = [
    f"{IG_BASE}/examples.json.zip",
    f"{IG_BASE}/package.tgz",
]


def _try_download_package(client: httpx.Client, url: str, dest: Path) -> bool:
    print(f"Trying package {url} ...")
    try:
        resp = client.get(url, follow_redirects=True)
    except httpx.HTTPError as exc:
        print(f"  failed: {exc}")
        return False
    if resp.status_code != 200:
        print(f"  HTTP {resp.status_code}")
        return False
    if resp.content[:2] == b"PK" or url.endswith(".zip"):
        dest.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(BytesIO(resp.content)) as zf:
            zf.extractall(dest)
            print(f"  extracted {len(zf.namelist())} entries")
        return True
    print(f"  unexpected payload size={len(resp.content)}")
    return False


def _download_github_fsh(client: httpx.Client) -> int:
    tree_resp = client.get(
        GITHUB_API_TREE,
        headers={"User-Agent": "ResilienceScout-Phase1", "Accept": "application/vnd.github+json"},
    )
    tree_resp.raise_for_status()
    paths = [
        t["path"]
        for t in tree_resp.json().get("tree", [])
        if t.get("type") == "blob" and t["path"].startswith("input/fsh/examples/")
    ]
    out = OUT_DIR / "github_fsh"
    out.mkdir(parents=True, exist_ok=True)
    saved = 0
    for path in paths:
        r = client.get(GITHUB_RAW + path, headers={"User-Agent": "ResilienceScout-Phase1"})
        if r.status_code != 200:
            print(f"  fail {path} HTTP {r.status_code}")
            continue
        (out / Path(path).name).write_text(r.text, encoding="utf-8")
        saved += 1
    print(f"Saved {saved}/{len(paths)} GitHub FSH example files")
    return saved


def _build_derived_inventory() -> int:
    """Parse FSH Observation instances into a derived CSV/JSON inventory."""
    import pandas as pd

    fsh_dir = OUT_DIR / "github_fsh"
    if not fsh_dir.exists():
        return 0
    instances = []
    for fp in sorted(fsh_dir.glob("*.fsh")):
        text = fp.read_text(encoding="utf-8")
        blocks = re.split(r"\n(?=Instance:)", text)
        for block in blocks:
            if not block.strip().startswith("Instance:"):
                continue
            if re.search(r"^InstanceOf:\s*(Device|Location|Library|Group)\b", block, re.M):
                continue
            if (
                "ObservationWithCompOah" not in block
                and "ObservationIndicatorsOah" not in block
                and "InstanceOf: Observation" not in block
            ):
                continue
            m_id = re.search(r"^Instance:\s*(\S+)", block, re.M)
            m_title = re.search(r'^Title:\s*"([^"]+)"', block, re.M)
            m_code = re.search(r'\* code\.text = "([^"]+)"', block)
            if not m_code:
                m_code = re.search(r'TemporaryOahSystem#[^\s]+ "([^"]+)"', block)
            m_subj = re.search(r"\* subject = Reference\(([^)]+)\)", block)
            m_eff = re.search(r'\* effectiveDateTime = "([^"]+)"', block)
            m_start = re.search(r'\* effectivePeriod\.start = "([^"]+)"', block)
            m_end = re.search(r'\* effectivePeriod\.end = "([^"]+)"', block)
            m_val = re.search(r"\* valueQuantity = ([0-9.eE+-]+) '([^']+)'", block)
            medians = re.findall(
                r"observation-statistics#median[^\n]*\n\* component\[=\]\.valueQuantity = ([0-9.eE+-]+) '([^']+)'",
                block,
            )
            instances.append(
                {
                    "id": m_id.group(1) if m_id else None,
                    "title": m_title.group(1) if m_title else None,
                    "indicator": m_code.group(1) if m_code else None,
                    "site": m_subj.group(1).strip() if m_subj else None,
                    "effectiveDateTime": m_eff.group(1) if m_eff else None,
                    "effectivePeriod_start": m_start.group(1) if m_start else None,
                    "effectivePeriod_end": m_end.group(1) if m_end else None,
                    "value": float(m_val.group(1)) if m_val else None,
                    "unit": m_val.group(2) if m_val else None,
                    "median_value": float(medians[0][0]) if medians else None,
                    "median_unit": medians[0][1] if medians else None,
                    "source_file": fp.name,
                }
            )

    processed = REPO_ROOT / "data" / "processed"
    processed.mkdir(parents=True, exist_ok=True)
    (processed / "oah_fhir_observation_inventory.json").write_text(
        json.dumps(instances, indent=2), encoding="utf-8"
    )
    pd.DataFrame(instances).to_csv(
        processed / "oah_fhir_observation_inventory.csv", index=False
    )
    save_provenance(
        ProvenanceRecord(
            source="Derived inventory from OAH FHIR FSH examples",
            source_url="https://github.com/hl7-eu/oah/tree/master/input/fsh/examples",
            retrieval_date=date.today(),
            original_filename_or_api="data/raw/oah_fhir_ig_examples/github_fsh/*.fsh",
            license="Derived from OAH FHIR IG source examples; same upstream terms.",
            data_class=DataClass.derived,
            processing_steps=[
                "Parsed FHIR Shorthand Observation Instance blocks",
                "Extracted identifiers, indicators, sites, dates, values without altering literals",
            ],
            preserves_original_values=True,
            notes="Prefer median components for annual summaries when scales look inconsistent.",
        ),
        REPO_ROOT / "data" / "provenance" / "oah_fhir_observation_inventory.yaml",
    )
    print(f"Derived inventory with {len(instances)} Observation instances")
    return len(instances)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    downloaded_via = "unknown"
    bulk_ok = False
    saved_fsh = 0

    with httpx.Client(timeout=120.0) as client:
        for url in CANDIDATE_PACKAGE_URLS:
            if _try_download_package(client, url, OUT_DIR / "package"):
                bulk_ok = True
                downloaded_via = url
                break
        try:
            saved_fsh = _download_github_fsh(client)
            if saved_fsh:
                downloaded_via = (
                    downloaded_via
                    if bulk_ok
                    else "https://github.com/hl7-eu/oah/tree/master/input/fsh/examples"
                )
        except httpx.HTTPError as exc:
            print(f"GitHub FSH download failed: {exc}")

        manifest = {
            "downloads_page": DOWNLOADS_URL,
            "github_examples": "https://github.com/hl7-eu/oah/tree/master/input/fsh/examples",
            "bulk_package_ok": bulk_ok,
            "github_fsh_count": saved_fsh,
            "retrieval_date": date.today().isoformat(),
            "note": (
                "build.fhir.org IG may 404; GitHub FSH is the fallback authoritative source."
            ),
        }
        (OUT_DIR / "fetch_manifest.json").write_text(
            json.dumps(manifest, indent=2), encoding="utf-8"
        )

    if saved_fsh == 0 and not bulk_ok:
        print("ERROR: No FHIR examples downloaded.", file=sys.stderr)
        return 1

    _build_derived_inventory()

    save_provenance(
        ProvenanceRecord(
            source="OneAquaHealth HL7 FHIR IG source examples (GitHub hl7-eu/oah FSH)",
            source_url="https://github.com/hl7-eu/oah/tree/master/input/fsh/examples",
            retrieval_date=date.today(),
            original_filename_or_api=downloaded_via,
            license=(
                "FHIR IG source published by OneAquaHealth Project / HL7 EU; "
                "example resources — not a live surveillance API."
            ),
            data_class=DataClass.observed,
            processing_steps=[
                "Attempted build.fhir.org IG example packages",
                "Downloaded unmodified FHIR Shorthand (.fsh) example files from GitHub",
            ],
            preserves_original_values=True,
            notes=(
                "Includes Almyros/Giofyros aquatic chemistry, Benevento air pollutants, "
                "and Oslo/Benevento health prevalence examples."
            ),
        ),
        PROVENANCE_PATH,
    )
    print(f"Wrote provenance {PROVENANCE_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
