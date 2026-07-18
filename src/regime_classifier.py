"""Canonical regime classifier for the code-geometry ABM.

Single source of truth for outcome classification. Supersedes the inline
classifiers previously scattered across scripts/run_v2_7_endogenous_delta_sweep.py,
scripts/reclassify_regimes.py, and scripts/run_dose_response.py, which used three
inconsistent rules. All downstream analysis should import from here.

Two schemas:
  hierarchical (canonical): capture defined by enforcement lock-in, no prevalence gate.
  legacy (discriminant only): capture additionally requires high fundamentalist prevalence.

Thresholds are module-level constants; change them here and nowhere else.
"""
from __future__ import annotations

# Canonical thresholds (edit here only).
EXIT_CAPTURE_MAX = 0.20      # captured systems retain members: low exit
PUNISH_ACTIVE_MIN = 0.10     # enforcement is active
ENFORCER_SHARE_MIN = 0.70    # punishment concentrated in the cadre
EXIT_COLLAPSE_MIN = 0.90     # depopulation
PREVALENCE_LEGACY_MIN = 0.90 # legacy-only: belief reaches majority
ACQUIESCENCE_CAPTURE_MIN = 0.50  # majority self-polices -> functional capture even
                                 # when overt punishment is low (deterrence working)

# Open question flagged for the reconstruction: whether COLLAPSE should
# additionally require that enforcement occurred (active punishment > 0),
# to justify the phrase "enforcement-induced depopulation". Default False
# preserves the current exit-only definition; set True to require enforcement.
COLLAPSE_REQUIRES_ENFORCEMENT = False


def classify(exit_rate, active_punish, enforcer_share, fund_prevalence=None,
             schema="hierarchical", acquiescence=None):
    """Return one of QUIET, MIXED, CAPTURE, COLLAPSE.

    schema="hierarchical" (canonical) ignores fund_prevalence.
    schema="legacy" additionally requires fund_prevalence >= PREVALENCE_LEGACY_MIN
    for CAPTURE; used only as a discriminant, never as the headline classifier.

    acquiescence (optional): fraction of the population that self-polices (q above
    the acquiescence threshold). When provided, a retained population that has
    crossed ACQUIESCENCE_CAPTURE_MIN counts as CAPTURE even if overt punishment is
    low -- this is functional capture by internalized fear, which the overt-only
    rule (acquiescence=None, the historical behavior) misses. Pass None to
    reproduce the published classification exactly.
    """
    collapse = exit_rate >= EXIT_COLLAPSE_MIN
    if COLLAPSE_REQUIRES_ENFORCEMENT:
        collapse = collapse and (active_punish is not None and active_punish > 0)
    if collapse:
        return "COLLAPSE"

    active = active_punish is not None and active_punish >= PUNISH_ACTIVE_MIN
    concentrated = enforcer_share is not None and enforcer_share >= ENFORCER_SHARE_MIN
    retained = exit_rate <= EXIT_CAPTURE_MAX
    self_policing = acquiescence is not None and acquiescence >= ACQUIESCENCE_CAPTURE_MIN

    # capture via overt enforcement OR via retained self-policing (functional capture).
    capture = retained and (active and concentrated or self_policing)
    if schema == "legacy":
        if fund_prevalence is None:
            raise ValueError("legacy schema requires fund_prevalence")
        capture = capture and (fund_prevalence >= PREVALENCE_LEGACY_MIN)

    if capture:
        return "CAPTURE"
    if active:
        return "MIXED"
    return "QUIET"


def classify_dataframe(df, schema="hierarchical",
                       exit_col="final_exit_rate",
                       punish_col="max_punish",
                       enforcer_col="enforcer_punish_share",
                       prevalence_col="final_fund_prevalence",
                       out_col=None):
    """Add a regime column to a copy of df using the given schema. Returns the copy."""
    out = df.copy()
    if out_col is None:
        out_col = f"regime_{schema}"
    prev = df[prevalence_col] if (schema == "legacy" and prevalence_col in df.columns) else None
    out[out_col] = [
        classify(
            df[exit_col].iloc[i],
            df[punish_col].iloc[i] if punish_col in df.columns else None,
            df[enforcer_col].iloc[i] if enforcer_col in df.columns else None,
            fund_prevalence=(prev.iloc[i] if prev is not None else None),
            schema=schema,
        )
        for i in range(len(df))
    ]
    return out


if __name__ == "__main__":
    # Self-check.
    assert classify(0.006, 0.18, 0.98) == "CAPTURE"
    assert classify(0.006, 0.18, 0.98, fund_prevalence=0.10, schema="legacy") == "MIXED"
    assert classify(0.006, 0.18, 0.98, fund_prevalence=0.95, schema="legacy") == "CAPTURE"
    assert classify(0.05, 0.05, 0.30) == "QUIET"
    assert classify(0.05, 0.20, 0.50) == "MIXED"
    assert classify(0.95, 0.20, 0.98) == "COLLAPSE"
    # acquiescence-aware: low overt punish + low exit + high self-policing -> functional CAPTURE
    assert classify(0.02, 0.03, 0.40, acquiescence=0.85) == "CAPTURE"
    # the SAME run under the overt-only view is only QUIET (this is the confound we fix)
    assert classify(0.02, 0.03, 0.40) == "QUIET"
    # self-policing but people are still leaving (not retained) -> not capture
    assert classify(0.50, 0.03, 0.40, acquiescence=0.85) == "QUIET"
    print("regime_classifier self-check OK")
