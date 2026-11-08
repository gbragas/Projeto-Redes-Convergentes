#!/usr/bin/env bash
# Run every combination of load scenario x QoS configuration and save the
# raw output of each simulation in results/logs/. Then build the CSV
# summaries with parse_results.py.
#
# Usage (from anywhere):
#   scratch/network-qos/run_experiments.sh
#
# Requires the ns-3 Python bindings (cppyy). If a .venv exists in the ns-3
# root, it is activated automatically.

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NS3_ROOT="$(cd "$PROJECT_DIR/../.." && pwd)"
LOG_DIR="$PROJECT_DIR/results/logs"

SCENARIOS=(low medium high)
# Each configuration: <name>:<QOS_MECHANISM>:<QOS_PRIORITY_QUEUING>
CONFIGS=(
    "baseline:baseline:0"
    "fq_codel:fq_codel:0"
    "pq_baseline:baseline:1"
    "pq_fq_codel:fq_codel:1"
)

if [[ -f "$NS3_ROOT/.venv/bin/activate" ]]; then
    # shellcheck disable=SC1091
    source "$NS3_ROOT/.venv/bin/activate"
fi

mkdir -p "$LOG_DIR"
cd "$NS3_ROOT"

for scenario in "${SCENARIOS[@]}"; do
    for entry in "${CONFIGS[@]}"; do
        IFS=: read -r name mechanism pq <<< "$entry"
        log="$LOG_DIR/${scenario}_${name}.txt"

        echo "==> scenario=$scenario config=$name"
        start=$(date +%s)

        QOS_SCENARIO="$scenario" \
        QOS_MECHANISM="$mechanism" \
        QOS_PRIORITY_QUEUING="$pq" \
            ./ns3 run --no-build scratch/network-qos/main.py > "$log" 2>&1

        echo "    done in $(( $(date +%s) - start ))s -> ${log#"$NS3_ROOT"/}"
    done
done

python3 "$PROJECT_DIR/parse_results.py" "$LOG_DIR" "$PROJECT_DIR/results"
