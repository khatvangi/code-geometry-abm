# Phase S2 Envelope Sweep — Manifest

**Phase:** Synthesis Phase S2 — ABM Extension 1 (argument-template envelope as input)
**Output dirs:** `synthesis/envelope_sweep_v1/` and `results/v3_0_envelope_sweep/`
**Produced:** 2026-04-28
**Read first:** `synthesis_findings_s2.md`

---

## Files in synthesis/envelope_sweep_v1/

| File | Size | Role | Read order |
|---|---|---|---|
| `synthesis_findings_s2.md` | ~14 KB | The substantive report. Phase S3 readiness depends on Kiran's resolution of Q-S2-1 through Q-S2-4 | **1st — read this** |
| `_dry_run.md` | ~4 KB | Pre-launch grid coordinate inspection per §6.1.4 | For audit |
| `MANIFEST.md` | this file | File inventory + pipeline diagram + hard-rule checklist | For navigation |

## Files in results/v3_0_envelope_sweep/

| File | Size | Role |
|---|---|---|
| `sweep_seed_results.csv` | 290 KB | 1,200 rows, one per seed. Canonical analysis input |
| `sweep_summary.csv` | 5.3 KB | 40 rows, one per (template, grid) cell. Includes regime majority + per-regime counts |
| `template_regime_counts.csv` | 0.6 KB | Per-template per-grid regime distribution pivot |
| `phase_map_v3_0.png` | 276 KB | 8-panel σ×π regime map across templates |
| `<T>/grid_<i>/seed_<s>/metrics.csv` | ~265 KB each, ×1200 | Per-step metrics including `active_punish_rate` |
| `<T>/grid_<i>/seed_<s>/agent_summary.csv` | ~25 KB each, ×1200 | Per-agent terminal state |
| `run.log` | gitignored (`*.log`) | Sweep progress log |
| `run.pid` | gitignored (`*.pid`) | Orchestrator PID (2149011) |

Plus the canonical scripts/model:

| File | Size | Role |
|---|---|---|
| `src/religion_fundamentalism_abm_v3_0.py` | 970 lines, +83 over v2.5 | New ABM model with envelope-as-input |
| `scripts/run_v3_0_envelope_sweep.py` | 245 lines | Sweep orchestrator with --dry_run mode |
| `scripts/aggregate_v3_0_envelope_sweep.py` | 220 lines | Aggregation + phase-map figure |

---

## Pipeline

```
src/religion_fundamentalism_abm_v3_0.py        (canonical model w/ envelope validation)
      │                                         (sourced from §3.3 of INSTRUCTION_BORON_S2.md)
      │
scripts/run_v3_0_envelope_sweep.py              (1200-run sweep orchestrator)
      │
      └→ results/v3_0_envelope_sweep/<T>/grid_<i>/seed_<s>/
             ├── metrics.csv                   (per-step, includes active_punish_rate)
             └── agent_summary.csv             (per-agent terminal state)
                  │
scripts/aggregate_v3_0_envelope_sweep.py        (collect → CSV summaries → phase map)
      │
      └→ results/v3_0_envelope_sweep/
             ├── sweep_seed_results.csv         (1200 rows)
             ├── sweep_summary.csv              (40 rows)
             ├── template_regime_counts.csv    
             └── phase_map_v3_0.png             (8-panel σ×π regime map)
                  │
synthesis_findings_s2.md                        (this report)
```

The model is the canonical source for `ENVELOPE_TABLE`. The sweep script imports that table directly — no value duplication.

---

## Headline numbers

- **1,200 runs** complete; 0 failed; 0 skipped.
- **Wall-clock:** ~15 minutes from launch to last metrics.csv. Throughput ≈ 1.3 runs/sec across 64 workers.
- **Predicted regime distribution:** 598 quiet / 541 mixed / 61 collapse / **0 capture**.
- **Cell-level majority:** 26 quiet / 12 mixed / 2 collapse / 0 capture across the 40 cells.
- **Phase S3 recommendation:** PAUSED pending Kiran's resolution of Q-S2-1 through Q-S2-4 (in `synthesis_findings_s2.md` §6).

---

## Decisions affecting downstream phases

Surfaced in `synthesis_findings_s2.md`:

1. **Q-S2-1: §3.1 base_opp_floor directionality.** E "raises base_opp_floor" — but in v2.5 raising base_opp raises exit pressure (working against capture). Either §3.1 is inverted, or the term means something other than v2.5's exit_opportunity_base. Recommended fix: lower base_opp_floor for templates with E (Reading C in §4 of findings).
2. **Q-S2-2: Phase S2 claim revision.** Strong claim "templates can reach CAPTURE in isolation" is empirically false in this sweep. Weak claim "templates set the QUIET-vs-active threshold; non-textual forces close the CAPTURE gap" is consistent with both Phase S1 (LR005/LR015/LR016 formal_only_mechanism_mismatch) and Phase S2 evidence.
3. **Q-S2-3: Re-sweep decision.** If Q-S2-1 corrected: re-run (~15 min) or proceed to Phase S3 with directionality fix as a Phase S3 input.
4. **Q-S2-4: T6/T7 prediction-violation framing.** P caps intensity, not activation. §1 prediction (>80% quiet) was inconsistent with §3.1 spec.

---

## Hard-rule compliance

- ✓ No file outside `src/`, `scripts/`, `synthesis/`, `results/v3_0_envelope_sweep/`, `.gitignore`, `HISTORY.md` modified.
- ✓ v2.5–v2.9 model files unchanged.
- ✓ Phase S1 deliverables in `synthesis/unified_christian_baseline_v1/` untouched (immutable per frozen-baseline rule).
- ✓ PLOS submission package in `synthesis/inputs/manuscript_plosone_v3/` untouched.
- ✓ `manuscript/` untouched.
- ✓ `scripts/reclassify_regimes.py` not used — active-rate computed at sweep time per §4.1.
- ✓ No synthetic data — all 1,200 runs from real ABM with fixed seeds 1..30.
- ✓ Existing `results/` directories not overwritten; new sweep in new whitelisted dir.
- ✓ Hard Rule 10 followed: zero-CAPTURE finding raised in `synthesis_findings_s2.md` §6 for Kiran review; envelope NOT silently retuned.

---

## Reproducibility

To regenerate from scratch (assuming src/ + scripts/ committed):

```bash
# 1. dry-run for grid coordinate inspection
.venv/bin/python scripts/run_v3_0_envelope_sweep.py --dry_run

# 2. run the sweep (~15 min on 64 cores)
nohup .venv/bin/python scripts/run_v3_0_envelope_sweep.py --workers 64 \
    > results/v3_0_envelope_sweep/run.log 2>&1 &

# 3. aggregate when sweep completes
.venv/bin/python scripts/aggregate_v3_0_envelope_sweep.py
```

`ENVELOPE_TABLE` in `src/religion_fundamentalism_abm_v3_0.py` is the canonical source. Re-running with the same seeds produces bit-for-bit identical CSVs (per the v2.5.1 reproducibility guarantee, inherited by v3.0).

---

*End of Phase S2 envelope sweep manifest. Update upon Kiran's Q-S2 resolutions.*
