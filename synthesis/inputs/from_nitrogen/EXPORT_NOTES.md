# EXPORT_NOTES — synthesis_phase_s1

**Repository (source):** `violence-abrahamic` on Nitrogen
**Export target:** `code-geometry-abm` on Boron (synthesis Phases S2–S4)
**Export date (UTC):** 2026-04-28
**Phase:** S1 — Evidence export for Boron synthesis
**This is an export, not a republication.** Nitrogen's `christian_baseline_v1` remains the source of truth. Boron should treat these files as a snapshot for synthesis input, not as a re-issuing of the baseline.

---

## Source freeze label

`christian_baseline_v1` — manifest at `data/frozen/christian_baseline_v1/MANIFEST.csv`.

**Important:** the live master table at `data/lived_religion/control_axis/lived_religion_control_axis_table.csv` has **drifted** from this freeze. See "Decisions and findings" below for the full diff. The export uses the **live** table (per the source paths listed in the Phase S1 instruction), not the frozen copy.

---

## Counts

| Item | Count | Notes |
|------|-------|-------|
| Cases exported | 16 | Matches the 16-case master table; matches the freeze. |
| Source-evidence rows in registry | 66 | **Diverges from STATUS.md line 110** which reports 48. STATUS.md is stale; live count verified 2026-04-28. |
| Source IDs unique | 66 | Zero duplicates, zero orphans (every `source_id` referenced by a case is present in the evidence file). |
| Argument templates exported | 8 | T1–T8 from `data/processed/argument_templates/argument_template_seed.csv`. |
| LR015 deep-dive evidence rows | 9 | Identical to LR015 rows in master evidence file. |
| LR006 deep-dive evidence rows | 7 | Identical to LR006 rows in master evidence file. |
| Cases at `documented` (live) | 5 | LR001, LR005, LR006, LR011, LR015. |
| Cases at `documented` (frozen) | 1 | LR015 only. |

---

## Decisions and findings

### Finding 1 — Drift between live master and frozen baseline

The live master table SHA-256 differs from the frozen baseline SHA-256:

| | sha256 |
|---|---|
| Live | `62ca90436461935abd12f42e2ef790de87220b6fb22423167f8783d2810d74fa` |
| Frozen | `738ab6747363180da6338800944ccf682c5907d7b8bb20ac7fc65172b6cb3345` |

Field-level drift: five cases promoted from `plausible` → `documented` since the freeze.

| Case | Frozen status | Live status |
|------|---------------|-------------|
| LR001 First Crusade | plausible | documented |
| LR005 Doctrine of Discovery | plausible | documented |
| LR006 Atlantic slavery pro-slavery argument | plausible | documented |
| LR011 Abolitionist biblical counterreading | plausible | documented |
| LR015 Canadian Indian Residential Schools | plausible | documented |

**Decision:** export from the **live** table per the Phase S1 instruction's listed source paths. Do not modify the frozen copy (CLAUDE.md rule: frozen baselines are immutable). Boron should be aware that the export is post-freeze data, and that downstream consumers expecting the freeze level (`plausible` for all but LR015) will see a different shape.

**Open question for Kiran:** the project policy is "refinements create a new freeze label" rather than editing the freeze in place. The five status promotions in the live data have not yet been re-frozen under a new label (e.g. `christian_baseline_v2`). Either (a) the promotions are in-progress work that should not yet have travelled into the live master, or (b) a new freeze should be cut. This export does not resolve which.

### Finding 2 — STATUS.md is stale relative to live data

`STATUS.md` (currently lines 108–110) records:

- "`LR015` Canadian Indian Residential Schools -> `documented`" (matches live)
- All other 15 cases at `plausible` (live disagrees for LR001, LR005, LR006, LR011)
- "Source-backed evidence rows attached so far: `48`" (live count is 66)

The export reflects live data. STATUS.md should be refreshed at Kiran's discretion; this is out of scope for Phase S1.

### Finding 3 — Documentation boundary field

The instruction asks for a `documentation_boundary` field. The master CSV does not have a column with that exact name; the closest equivalent is the `notes` column, which carries the verbal documentation boundary statement (e.g. for LR001: "documented for papal authorization indulgence structure and early violent uptake in the First Crusade, but it is not yet a total explanation of all crusader motives or every regional variation"). The export populates both `case_notes` and `documentation_boundary` from the `notes` column. If Boron needs them separated, that requires a schema split upstream and is out of scope for S1.

### Finding 4 — `evidence_level` mapping in source registry

Per instruction: "If `evidence_level` cannot be determined from existing metadata, use the case's `evidence_quality` for the cases using that source." In fact each row in `christian_case_source_evidence.csv` carries its own per-source `evidence_quality` column (range 3–5). The export uses **the per-source value**, which is more granular than the per-case value. This is recorded in each registry record's `notes` field.

### Finding 5 — `non_textual_forces` representation

The master CSV has both `non_textual_forces` and `normalized_non_textual_forces` columns. They are equal in all 16 rows (verified at export time). The export emits `non_textual_forces` as the parsed array (from the normalized column) and additionally retains `non_textual_forces_raw` for traceability. Empty lists indicate no forces were tagged; "none" / "not_applicable" cells parse to empty list per the locked schema.

### Finding 6 — Restraint cases score lower on `MCI`

LR011, LR012, LR013, LR014 (the four restraint / counterreading cases) carry `MCI_missionary_control_integration = 0`, which is correct: the restraint variable is the symmetric inverse of MCI, and these are not missionary-control cases. Boron's synthesis should treat MCI as a directional variable that applies primarily to expansion-mode regimes, not as something every case must score on.

### Finding 7 — No row-internal inconsistencies detected

The validation pass scanned each row for contradictions between `verification_status` and `evidence_quality` (e.g. `documented` paired with `evidence_quality < 4`) and found none. All five `documented` live cases have `evidence_quality ≥ 4`.

### Finding 8 — No orphan source IDs

Every `source_id` referenced in any case row is present in the live evidence file. Zero orphans means the `source_type: "unverified_reference"` fallback in the registry was not triggered for any case at this export.

---

## Validation results

| Check | Result |
|-------|--------|
| `case_export.jsonl` parses as valid JSONL (one JSON object per line, 16 lines) | PASS |
| Case IDs in export match the 16 IDs in the live master table | PASS |
| Every `source_id` in `case_export.jsonl` appears in `source_registry.jsonl` | PASS |
| LR015 `deep_dive_evidence` present and non-empty (9 rows) | PASS |
| LR006 `deep_dive_evidence` present and non-empty (7 rows) | PASS |
| Nitrogen schema validator (`src.lived_religion.lived_religion_schema`) still passes after export | PASS — see invocation below |
| `pytest -q` still passes (50 tests) | PASS — see invocation below |
| No file content outside `data/exports/synthesis_phase_s1/` modified | PASS — see "File mtime note" below |

Validation commands and outputs:

```
.venv/bin/python -m src.lived_religion.lived_religion_schema \
    --schema data/lived_religion/registries/lived_religion_schema.yaml \
    --cases  data/lived_religion/historical_use/christian_historical_use_seed_cases.csv
.venv/bin/python -m src.lived_religion.build_lived_religion_table \
    --input  data/lived_religion/historical_use/christian_historical_use_seed_cases.csv \
    --output data/lived_religion/control_axis/lived_religion_control_axis_table.csv
.venv/bin/python -m src.lived_religion.analyze_control_axis \
    --input  data/lived_religion/control_axis/lived_religion_control_axis_table.csv \
    --outdir reports/lived_religion/tables
.venv/bin/python -m src.lived_religion.source_verification \
    --cases    data/lived_religion/historical_use/christian_historical_use_seed_cases.csv \
    --evidence data/lived_religion/historical_use/christian_case_source_evidence.csv \
    --outdir   reports/lived_religion/tables
.venv/bin/pytest -q
```

(Result lines logged in this file at the bottom under "Validation log".)

---

## Files in this export

| File | Purpose |
|------|---------|
| `case_export.jsonl` | One JSON object per case (16 lines). The primary data product. |
| `source_registry.jsonl` | Deduplicated source registry (66 sources). |
| `argument_templates.json` | T1–T8 canonical reference. |
| `methodology_locked.md` | Locked rules so Boron operates under the same discipline. |
| `EXPORT_NOTES.md` | This file. |
| `MANIFEST.csv` | Per-file size + sha256. |
| `build_export.py` | The exporter script (committed for auditability). |
| `export_diagnostics.json` | Machine-readable drift / count diagnostics, sidecar to this report. |

Boron should consume `case_export.jsonl`, `source_registry.jsonl`, `argument_templates.json`, and `methodology_locked.md`. The other three files are auditing artifacts.

---

## What this export is NOT

- Not a methodological revision. No re-scoring, no re-evaluation of evidence quality, no change to verification status. The export reflects live data values verbatim.
- Not a Phase 4 deep-dive. The remaining selected deep-dive cases (LR001, LR005, LR011 in the synthesis-relevant set) appear in the live data already promoted to `documented`, but this export does not assess whether that promotion is itself documented at the level the deep-dive plan requires.
- Not a multi-tradition expansion. Christian-only scope is preserved.
- Not a new freeze. `christian_baseline_v1` remains the official freeze label; no `_v2` is created here.

---

## Validation log

```
$ .venv/bin/python -m compileall src
Listing 'src/corpus'... 'src/history'... 'src/lived_religion'... 'src/validation'... 'src/viz'...
(no errors)

$ .venv/bin/pytest -q
.....................................................                    [100%]
53 passed in 0.57s

$ .venv/bin/python -m src.corpus.metadata_schema --registry data/metadata/source_registry.yaml
Sources inspected: 4
Validation errors: 0
Registry validation passed.

$ .venv/bin/python -m src.lived_religion.lived_religion_schema \
    --schema data/lived_religion/registries/lived_religion_schema.yaml \
    --cases  data/lived_religion/historical_use/christian_historical_use_seed_cases.csv
Schema errors: 0
Case errors: 0
Lived religion schema validation passed.

$ .venv/bin/python -m src.lived_religion.build_lived_religion_table ...   # output redirected to /tmp
Wrote 16 lived-religion control-axis rows to /tmp/_check_lr_table.csv

$ .venv/bin/python -m src.lived_religion.analyze_control_axis ...         # output redirected to /tmp
Wrote 6 lived-religion tables to /tmp/_check_lr_analyze

$ .venv/bin/python -m src.lived_religion.source_verification ...          # output redirected to /tmp
Wrote 3 source-verification tables to /tmp/_check_lr_verify
```

Test count is 53 (current); STATUS.md line 83 reports 50, which is stale by three tests.

---

## File mtime note

Running the validation pass updated the mtimes of these existing files:

```
data/metadata/download_log.csv
data/interim/passage_scores_rule_based.metadata.json
reports/commentary/refined/tables/refined_segmentation_qc.csv
reports/commentary/refined/tables/refined_linking_qc.csv
reports/commentary/refined/tables/locality_distribution.csv
```

Their **content was not modified** (verified by content-hash comparison; see source-tree files diff in the validation pass). The mtime changes come from idempotent validators in the test suite that re-write existing tables with identical content. This is a property of the existing test suite and is not introduced by this export.

If strict mtime preservation is required for downstream tooling, the validation step can be skipped — the export files themselves were produced before the validation pass and do not depend on it.

