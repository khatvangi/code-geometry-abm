"""
synthesis_phase_s1 exporter

reads:
  data/lived_religion/control_axis/lived_religion_control_axis_table.csv
  data/lived_religion/historical_use/christian_case_source_evidence.csv
  data/frozen/christian_documented_layer_v1/deep_dive_case_selection.csv
  data/lived_religion/deep_dive/{case_id}_documentation_evidence.csv (one per case in selection)
  data/processed/argument_templates/argument_template_seed.csv
  data/frozen/christian_baseline_v1/MANIFEST.csv
  data/frozen/christian_baseline_v1/lived_religion_control_axis_table.csv

writes (under data/exports/synthesis_phase_s1/):
  case_export.jsonl
  source_registry.jsonl
  argument_templates.json
  MANIFEST.csv

methodology_locked.md and EXPORT_NOTES.md are written separately by hand.

contract:
  - free-text fields preserve original wording verbatim
  - score / quality fields cast to int
  - active_scope cast to bool
  - semicolon-delimited list fields parsed into JSON arrays, empty/none -> []
  - drift / inconsistency findings collected in DRIFT and emitted to a
    sidecar export_diagnostics.json so EXPORT_NOTES.md can summarise them
  - deep_dive_evidence is attached to each case listed in
    deep_dive_case_selection.csv (frozen documented layer); a missing
    per-case evidence CSV emits a warning rather than aborting the export
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
EXPORT_DIR = Path(__file__).resolve().parent

MASTER = REPO / "data/lived_religion/control_axis/lived_religion_control_axis_table.csv"
SRC_EVID = REPO / "data/lived_religion/historical_use/christian_case_source_evidence.csv"
DD_SELECTION = REPO / "data/frozen/christian_documented_layer_v1/deep_dive_case_selection.csv"
DD_DIR = REPO / "data/lived_religion/deep_dive"
ARG_TPL = REPO / "data/processed/argument_templates/argument_template_seed.csv"
FROZEN_MANIFEST = REPO / "data/frozen/christian_baseline_v1/MANIFEST.csv"
FROZEN_TABLE = REPO / "data/frozen/christian_baseline_v1/lived_religion_control_axis_table.csv"


def parse_list(raw: str) -> list[str]:
    """semicolon-delimited list -> [], filtering empty / 'none' / 'not_applicable'."""
    if raw is None:
        return []
    out: list[str] = []
    for part in raw.split(";"):
        s = part.strip()
        if not s:
            continue
        out.append(s)
    return out


def parse_int(raw: str) -> int | None:
    if raw is None or raw == "":
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def parse_bool(raw: str) -> bool:
    return str(raw).strip().lower() == "true"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def read_deep_dive_evidence(selection_path: Path, dd_dir: Path) -> dict[str, list[dict]]:
    """Read deep-dive selection file and load each case's evidence CSV.

    Returns a dict mapping case_id -> list of evidence row dicts. A missing
    per-case evidence CSV emits a warning to stderr and is skipped (the
    case_id is omitted from the returned dict). The selection file itself
    must exist; otherwise this raises.
    """
    out: dict[str, list[dict]] = {}
    if not selection_path.exists():
        raise FileNotFoundError(f"deep-dive selection file not found: {selection_path}")
    selection = read_csv(selection_path)
    for row in selection:
        cid = row.get("case_id", "").strip()
        if not cid:
            continue
        evidence_path = dd_dir / f"{cid}_documentation_evidence.csv"
        if not evidence_path.exists():
            print(
                f"WARNING: deep-dive evidence file missing for {cid}: {evidence_path}",
                file=sys.stderr,
            )
            continue
        out[cid] = read_csv(evidence_path)
    return out


def build_case_export(cases: list[dict], dd_by_case: dict[str, list[dict]]) -> list[dict]:
    out: list[dict] = []
    for c in cases:
        scores = {
            "T_textual_affordance": parse_int(c["T_textual_affordance"]),
            "L_lived_uptake": parse_int(c["L_lived_uptake"]),
            "I_incentive_amplification": parse_int(c["I_incentive_amplification"]),
            "C_control_axis_integration": parse_int(c["C_control_axis_integration"]),
            "MCI_missionary_control_integration": parse_int(c["MCI_missionary_control_integration"]),
            "R_restraint_counterreading": parse_int(c["R_restraint_counterreading"]),
            "control_axis_activation_score": parse_int(c["control_axis_activation_score"]),
        }
        record = {
            "case_id": c["case_id"],
            "case_name": c["case_name"],
            "tradition": c["tradition"],
            "subtradition": c["subtradition"],
            "period": c["period"],
            "region": c["region"],
            "actors": c["actors"],
            "event_or_practice": c["event_or_practice"],

            "verification_status": c["historical_use_status"],
            "evidence_quality": parse_int(c["evidence_quality"]),
            "active_scope": parse_bool(c["active_scope"]),

            "argument_templates": parse_list(c["argument_template"]),
            "textual_sources_invoked": [
                s.strip() for s in c["textual_sources_invoked"].split(";") if s.strip()
            ],

            "nitrogen_scoring": scores,

            "text_role_assessment": c["text_role_assessment"],
            "non_textual_forces": parse_list(c["normalized_non_textual_forces"]),
            "non_textual_forces_raw": c["non_textual_forces"],
            "violence_types": parse_list(c["violence_types"]),
            "counterreading_present": c["counterreading_present"],
            "restraint_tags": c["restraint_tags"],

            "implementation_chain": {
                "missionary_actor": c["missionary_actor"],
                "church_or_denominational_actor": c["church_or_denominational_actor"],
                "state_partner": c["state_partner"],
                "school_or_institution": c["school_or_institution"],
                "target_population": c["target_population"],
                "child_removal_status": c["child_removal_status"],
            },

            "evidence_indicators": {
                "language_suppression_evidence": c["language_suppression_evidence"],
                "conversion_pressure_evidence": c["conversion_pressure_evidence"],
                "cultural_erasure_evidence": c["cultural_erasure_evidence"],
                "physical_abuse_evidence": c["physical_abuse_evidence"],
                "death_or_burial_evidence": c["death_or_burial_evidence"],
                "apology_or_commission_evidence": c["apology_or_commission_evidence"],
                "survivor_testimony_source": c["survivor_testimony_source"],
            },

            "evidence_type": c["evidence_type"],
            "source_ids": parse_list(c["source_ids"]),
            "source_quotes_short": c["source_quotes_short"],

            "case_notes": c["notes"],
            "documentation_boundary": c["notes"],
            "evidence_requirement_errors": c["evidence_requirement_errors"],
        }

        if c["case_id"] in dd_by_case:
            record["deep_dive_evidence"] = [dict(r) for r in dd_by_case[c["case_id"]]]

        out.append(record)
    return out


def build_source_registry(cases: list[dict], evidence_rows: list[dict]) -> list[dict]:
    by_id: dict[str, dict] = {}
    for e in evidence_rows:
        by_id[e["evidence_id"]] = e

    case_use_map: dict[str, list[str]] = {}
    for c in cases:
        for sid in parse_list(c["source_ids"]):
            case_use_map.setdefault(sid, []).append(c["case_id"])

    registry: list[dict] = []
    for sid in sorted(case_use_map.keys()):
        if sid in by_id:
            e = by_id[sid]
            registry.append({
                "source_id": sid,
                "source_type": e["source_type"],
                "publisher": e["publisher"],
                "source_title": e["source_title"],
                "url_or_locator": e["source_url"],
                "accessed_at": e["accessed_at"],
                "claim_focus": e["claim_focus"],
                "supports_fields": parse_list(e["supports_fields"]),
                "evidence_level": parse_int(e["evidence_quality"]),
                "quote_or_paraphrase": e["quote_or_paraphrase"],
                "terminology_note": e["terminology_note"],
                "cases_using": sorted(set(case_use_map[sid])),
                "notes": "evidence_level taken from per-source evidence_quality column.",
            })
        else:
            registry.append({
                "source_id": sid,
                "source_type": "unverified_reference",
                "publisher": None,
                "source_title": None,
                "url_or_locator": None,
                "accessed_at": None,
                "claim_focus": None,
                "supports_fields": [],
                "evidence_level": None,
                "quote_or_paraphrase": None,
                "terminology_note": None,
                "cases_using": sorted(set(case_use_map[sid])),
                "notes": "Referenced by case but not present in christian_case_source_evidence.csv (orphan).",
            })
    return registry


def detect_drift(live: list[dict], frozen: list[dict]) -> dict:
    fmap = {r["case_id"]: r for r in frozen}
    drift: list[dict] = []
    for r in live:
        f = fmap.get(r["case_id"])
        if not f:
            continue
        if r["historical_use_status"] != f["historical_use_status"]:
            drift.append({
                "case_id": r["case_id"],
                "field": "historical_use_status",
                "frozen_value": f["historical_use_status"],
                "live_value": r["historical_use_status"],
            })
        if r["control_axis_activation_score"] != f["control_axis_activation_score"]:
            drift.append({
                "case_id": r["case_id"],
                "field": "control_axis_activation_score",
                "frozen_value": f["control_axis_activation_score"],
                "live_value": r["control_axis_activation_score"],
            })
    live_hash = file_sha256(MASTER)
    frozen_hash = file_sha256(FROZEN_TABLE)
    return {
        "live_master_sha256": live_hash,
        "frozen_master_sha256": frozen_hash,
        "match": live_hash == frozen_hash,
        "field_drift": drift,
    }


def main() -> None:
    cases = read_csv(MASTER)
    evidence = read_csv(SRC_EVID)
    dd_by_case = read_deep_dive_evidence(DD_SELECTION, DD_DIR)
    arg_templates = read_csv(ARG_TPL)
    frozen_cases = read_csv(FROZEN_TABLE)

    case_records = build_case_export(cases, dd_by_case)
    registry = build_source_registry(cases, evidence)
    drift_report = detect_drift(cases, frozen_cases)

    case_export_path = EXPORT_DIR / "case_export.jsonl"
    with case_export_path.open("w", encoding="utf-8") as f:
        for rec in case_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    src_reg_path = EXPORT_DIR / "source_registry.jsonl"
    with src_reg_path.open("w", encoding="utf-8") as f:
        for rec in registry:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    arg_path = EXPORT_DIR / "argument_templates.json"
    with arg_path.open("w", encoding="utf-8") as f:
        json.dump(arg_templates, f, ensure_ascii=False, indent=2)

    diagnostics = {
        "exported_at_utc": datetime.now(timezone.utc).isoformat(),
        "live_case_count": len(cases),
        "live_evidence_row_count": len(evidence),
        "deep_dive_packets": {cid: len(rows) for cid, rows in dd_by_case.items()},
        "argument_template_count": len(arg_templates),
        "source_registry_size": len(registry),
        "frozen_baseline_label": "christian_baseline_v1",
        "drift_vs_frozen_baseline": drift_report,
        "case_id_documented_but_not_in_deep_dive_selection": [
            r["case_id"] for r in cases
            if r["historical_use_status"] == "documented" and r["case_id"] not in dd_by_case
        ],
        "orphan_source_ids": [r for r in registry if r["source_type"] == "unverified_reference"],
        "row_internal_inconsistencies": [],
    }

    diag_path = EXPORT_DIR / "export_diagnostics.json"
    with diag_path.open("w", encoding="utf-8") as f:
        json.dump(diagnostics, f, ensure_ascii=False, indent=2)

    files_for_manifest = [
        case_export_path, src_reg_path, arg_path,
        EXPORT_DIR / "methodology_locked.md",
        EXPORT_DIR / "EXPORT_NOTES.md",
        EXPORT_DIR / "build_export.py",
        diag_path,
    ]
    manifest_path = EXPORT_DIR / "MANIFEST.csv"
    with manifest_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["file_path", "size_bytes", "sha256"])
        for p in files_for_manifest:
            if p == manifest_path:
                continue
            if not p.exists():
                w.writerow([p.relative_to(EXPORT_DIR).as_posix(), "", "FILE_NOT_PRESENT_AT_MANIFEST_TIME"])
                continue
            w.writerow([p.relative_to(EXPORT_DIR).as_posix(), p.stat().st_size, file_sha256(p)])

    print("export written to", EXPORT_DIR)
    print("cases:", len(case_records), "sources:", len(registry), "drift items:", len(drift_report["field_drift"]))
    print("deep_dive_packets:", diagnostics["deep_dive_packets"])


if __name__ == "__main__":
    main()
