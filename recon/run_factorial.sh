#!/usr/bin/env bash
set -u
cd /storage/kiran-stuff/code-geometry-abm
echo "FACTORIAL START $(date -Is)"
python scripts/run_v2_7_endogenous_delta_sweep.py --out recon/factorial_shock_off --seeds 30 --workers 30 --shock-schedule "" > recon/factorial_off.log 2>&1 &
OFF=$!
python scripts/run_v2_7_endogenous_delta_sweep.py --out recon/factorial_shock_on --seeds 30 --workers 30 --shock-schedule "100,220,320" > recon/factorial_on.log 2>&1 &
ON=$!
echo "OFF_PID=$OFF ON_PID=$ON"
wait $OFF; echo "SHOCK_OFF_DONE $(date -Is) rc=$?"
wait $ON; echo "SHOCK_ON_DONE $(date -Is) rc=$?"
echo "FACTORIAL COMPLETE $(date -Is)"
