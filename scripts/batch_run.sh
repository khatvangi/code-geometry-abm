#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source .venv/bin/activate

if command -v ffmpeg >/dev/null 2>&1; then
  export IMAGEIO_FFMPEG_EXE="$(command -v ffmpeg)"
fi

ABM=""
if [[ -f src/religion_fundamentalism_abm.py ]]; then
  ABM="src/religion_fundamentalism_abm.py"
elif [[ -f religion_fundamentalism_abm.py ]]; then
  ABM="religion_fundamentalism_abm.py"
else
  CANDIDATE="$(rg -l 'argparse' src --glob '*.py' | head -n 1 || true)"
  if [[ -n "$CANDIDATE" ]] && rg -q -- '--sigma' "$CANDIDATE"; then
    ABM="$CANDIDATE"
  fi
fi

if [[ -z "$ABM" ]]; then
  echo "Could not locate ABM script." >&2
  exit 1
fi

HELP_TEXT="$(python "$ABM" --help 2>/dev/null || true)"
HAS_KAPPA=0
HAS_FPS=0
HAS_NO_MOVIE=0
[[ "$HELP_TEXT" == *"--kappa_cost"* ]] && HAS_KAPPA=1
[[ "$HELP_TEXT" == *"--fps"* ]] && HAS_FPS=1
[[ "$HELP_TEXT" == *"--no_movie"* ]] && HAS_NO_MOVIE=1

TS="$(date +%Y%m%d_%H%M%S)"
RUN_ROOT="runs/batch_${TS}"
mkdir -p "$RUN_ROOT"
mkdir -p runs/_meta
printf '%s\n' "$RUN_ROOT" > runs/_meta/last_batch_root.txt

{
  echo "timestamp=$(date -Iseconds)"
  echo "abm=$ABM"
  echo "run_root=$RUN_ROOT"
  echo "has_kappa_cost=$HAS_KAPPA"
  echo "has_fps=$HAS_FPS"
  echo "has_no_movie=$HAS_NO_MOVIE"
  echo "imageio_ffmpeg_exe=${IMAGEIO_FFMPEG_EXE:-}"
} > "$RUN_ROOT/run_meta.txt"

run_case() {
  local outdir="$1"
  local render="$2"
  local sigma="$3"
  local v_obs="$4"
  local a_obs="$5"
  local pi_reward="$6"
  local lam_punish="$7"
  local graph="$8"
  local seed="$9"

  mkdir -p "$outdir"

  local cmd=(python "$ABM"
    --outdir "$outdir"
    --steps 450
    --n 350
    --graph "$graph"
    --seed "$seed"
    --sigma "$sigma"
    --v_obs "$v_obs"
    --a_obs "$a_obs"
    --pi_reward "$pi_reward"
    --lam_punish "$lam_punish"
  )

  if [[ "$HAS_KAPPA" -eq 1 ]]; then
    cmd+=(--kappa_cost 0.08)
  fi

  if [[ "$HAS_FPS" -eq 1 ]]; then
    cmd+=(--fps 20)
  fi

  if [[ "$render" -eq 0 && "$HAS_NO_MOVIE" -eq 1 ]]; then
    cmd+=(--no_movie)
  fi

  echo "[$(date -Iseconds)] RUN ${cmd[*]}" | tee -a "$RUN_ROOT/run.log"
  "${cmd[@]}" >> "$RUN_ROOT/run.log" 2>&1
}

echo "Running batch into: $RUN_ROOT" | tee -a "$RUN_ROOT/run.log"

# Suite A: seed robustness
for condition in high_sigma low_sigma; do
  for seed in $(seq 1 30); do
    seed_id="$(printf '%02d' "$seed")"
    outdir="$RUN_ROOT/seed_sweep/$condition/seed_${seed_id}"
    render=0
    if [[ "$seed" -eq 1 ]]; then
      render=1
    fi

    if [[ "$condition" == "high_sigma" ]]; then
      run_case "$outdir" "$render" 0.80 0.95 0.03 0.24 0.28 scale_free "$seed"
    else
      run_case "$outdir" "$render" 0.15 0.95 0.03 0.05 0.10 scale_free "$seed"
    fi
  done
done

# Suite B: sigma sweep
for i in $(seq 0 20); do
  sigma="$(awk -v x="$i" 'BEGIN { printf "%.2f", x * 0.05 }')"
  outdir="$RUN_ROOT/sigma_sweep/sigma_${sigma}"
  render=0
  if [[ "$sigma" == "0.15" || "$sigma" == "0.80" ]]; then
    render=1
  fi
  run_case "$outdir" "$render" "$sigma" 0.95 0.03 0.24 0.28 scale_free 1
done

# Suite C: pi sweep
for i in $(seq 0 15); do
  pi_reward="$(awk -v x="$i" 'BEGIN { printf "%.2f", x * 0.02 }')"
  outdir="$RUN_ROOT/pi_sweep/pi_${pi_reward}"
  render=0
  if [[ "$pi_reward" == "0.00" || "$pi_reward" == "0.24" ]]; then
    render=1
  fi
  run_case "$outdir" "$render" 0.80 0.95 0.03 "$pi_reward" 0.28 scale_free 1
done

# Suite D: topology sensitivity
for graph in scale_free small_world erdos_renyi; do
  outdir="$RUN_ROOT/topology/${graph}"
  run_case "$outdir" 1 0.80 0.95 0.03 0.24 0.28 "$graph" 1
done

echo "Batch complete: $RUN_ROOT" | tee -a "$RUN_ROOT/run.log"
printf '%s\n' "$RUN_ROOT"
