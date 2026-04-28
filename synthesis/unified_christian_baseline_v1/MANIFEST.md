# Phase S1 Deliverables — Manifest

**Phase:** Synthesis Phase S1 — Christian baseline rescoring on ABM vocabulary
**Output dir:** `synthesis/unified_christian_baseline_v1/`
**Produced:** 2026-04-27
**Read first:** `synthesis_findings.md`

---

## Files in this directory

| File | Size | Role | Read order |
|---|---|---|---|
| `synthesis_findings.md` | ~24 KB | The substantive report. Phase S2 recommendation, the 7 instruction-required findings, and 4 additional Phase S1 findings. | **1st — read this** |
| `mismatches_report.md` | ~14 KB | Diagnoses of all matches that warrant separate explanation (boring-null, formal-only-mechanism-mismatch, the LR014 rubric-vs-observation tension, the LR007 decline). | 2nd |
| `unified_cases.jsonl` | 78 KB | **Canonical data.** 16 lines, one JSON object per case. All scoring, rationale, confidence, exit-cost-mechanism decomposition, non-textual-forces vector, scoring decisions, open questions, Nitrogen provenance. | 3rd if querying specific cases |
| `regime_predictions_summary.csv` | 2.3 KB | At-a-glance regime table sorted with mismatches first. 16 rows × 12 columns. | For audit |
| `unified_christian_baseline_v1.csv` | 66 KB | Flat CSV view of the JSONL. Generated mechanically from JSONL by the build script — do not hand-edit. | For spreadsheet inspection |
| `_build_deliverables.py` | ~70 KB | Build script. Holds the canonical case dict; generates JSONL + both CSVs. Re-runnable. | For reproducibility |
| `_dry_run.md` | ~9 KB | Pre-scoring inventory and Q1–Q7 questions to Kiran. Approved 2026-04-27 with the answer document folded into deliverables. | For context, not active reference |

Total: 7 files.

---

## Pipeline

```
_build_deliverables.py         (canonical case dict in Python)
        │
        ├─→ unified_cases.jsonl                  (canonical data, JSONL)
        │       │
        │       └─→ unified_christian_baseline_v1.csv  (flat view, derived)
        │
        └─→ regime_predictions_summary.csv       (at-a-glance, derived)
```

The Python script `_build_deliverables.py` is the canonical source. JSONL and CSVs are derived deterministically. Re-running the script regenerates the data files exactly. This satisfies the instruction's requirement: "The CSV regenerates from the JSONL without hand-edits (the JSONL is canonical)."

To regenerate:

```bash
cd synthesis/unified_christian_baseline_v1
python _build_deliverables.py
```

The script prints diagnostics (regime distribution, match-type distribution, match counts) on each run.

---

## Headline numbers

- **16 cases total**: 15 scored, 1 declined (LR007 per Q1).
- **Predicted regime distribution**: 3 quiet, 8 mixed, 0 collapse, 4 capture, 1 declined.
- **Match decomposition (Q5 schema)**: 9 substantive, 3 boring_null, 3 formal_only_mechanism_mismatch, 1 declined.
- **Substantive match rate**: 9/12 = 75% (excluding boring-null and declined).
- **Phase S2 recommendation**: PROCEED.

---

## Schema notes

`unified_cases.jsonl` follows the schema specified in `INSTRUCTION_BORON_S1.md` §"unified_cases.jsonl" plus the additions from the answer document:

- `match_type` field added (per Q5): one of `substantive`, `boring_null`, `formal_only_mechanism_mismatch`, or `null`.
- LR007 has `predicted_regime`, `observed_regime`, `regime_match`, `match_type` all `null` per Q1.

Each non-declined case has at least one entry in `scoring_decisions` documenting non-trivial scoring choices and a confirmation-bias audit. Each case has at least one entry in `open_questions` (most have 1–2; LR007 has 3).

---

## Decisions affecting downstream phases

Surfaced in `synthesis_findings.md`:

1. **Extension 5 (target-population modeling)** — new, unspecified in current `SYNTHESIS_WORKING_DOC.md §5`. Required for substantive evaluation of LR005/LR015/LR016 and for Paper 3.
2. **Q1 resolved**: Phase S2 envelope derivation should use theoretical path (structural variables in `argument_templates.json`), not empirical calibration. Saves 1–2 weeks.
3. **Q4 resolved**: restraint cases (LR011–LR014) included as low-σ × low-π cases per option (b). Transition to (c) once Extension 2 is built.
4. **COLLAPSE-narrow-definition issue (Q4)** — Phase S5 manuscript-revision item. ABM's COLLAPSE label requires enforcement-induced depopulation, which excludes mainline-style attrition.
5. **Regime-vs-event-axis** — Phase S5 §5 clarification item. ABM steady-state assumption is strained by short-mobilization cases (Crusades).
6. **Active-rate gotcha figure rebuild** — Phase S5 manuscript-revision item per `INSTRUCTION_BORON_S1.md` §"Active-rate gotcha". 18 of 72 v2.5 cells flip QUIET→MIXED under reclassification; manuscript figures and §8 numbers must be regenerated from `reclassified_seed_results.csv` and placed in a new whitelisted result directory.

---

## Hard-rule compliance

- ✓ No file outside `synthesis/` was modified during Phase S1.
- ✓ No model file (`src/`) was edited.
- ✓ No manuscript file (`manuscript/`) was edited.
- ✓ `HISTORY.md` (repo root) appended with Phase S1 Q&A entry per CLAUDE.md convention.
- ✓ Nitrogen-provenance fields preserved verbatim (argument_templates_active, text_role_assessment, non_textual_forces qualitative source, verification_status, evidence_quality from Nitrogen export).
- ✓ ABM five dimensions scored independently from Nitrogen's T/L/I/C/MCI/R per Hard Rule 5.
- ✓ Confirmation-bias audit documented per case (in `scoring_decisions`) per the answer document's auditing requirement.
- ✓ Methodology terminology cautions respected (residential schools: "unmarked graves" not "mass graves"; Pratt phrase preserved as U.S. Carlisle attribution).

---

## Gitignore status

`synthesis/` is currently untracked and not whitelisted in `.gitignore`. Per CLAUDE.md's gitignore-whitelist convention: if `synthesis/` should be committed, add `!synthesis/**` to `.gitignore`. **This decision is deferred to Kiran.**

Recommendation: commit `synthesis/` to git so future Claude sessions and any external auditor can find Phase S1 outputs alongside the manuscript and code. The deliverables are reproducibility artifacts (the build script + canonical JSONL allow regeneration). The Nitrogen export bundle (8 files in `synthesis/inputs/from_nitrogen/`) should also be committed so the synthesis is self-contained on Boron.

If `synthesis/` is committed, the suggested .gitignore additions are:

```
!synthesis/
!synthesis/**
```

---

*End of manifest.*
