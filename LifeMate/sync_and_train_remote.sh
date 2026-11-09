#!/bin/bash
# Sync Mixup code & audio dataset to vdhwy@vdhwy-legion and run GPU training & comparison
set -e
REMOTE="huy@100.64.0.83"
REMOTE_DIR="/home/huy/ZALOAI"
REMOTE_PY="/var/tmp/gguf/venv/bin/python"

echo "[1/3] Checking SSH connection to vdhwy@vdhwy-legion ($REMOTE)..."
ssh -o ConnectTimeout=8 "$REMOTE" "nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv"

echo "[2/3] Syncing updated Mixup scripts and baseline.ipynb to $REMOTE:$REMOTE_DIR..."
scp lifemate_agent.py baseline.py baseline.ipynb train_compare_mixup.py "$REMOTE:$REMOTE_DIR/"

echo "[3/3] Running Mixup GPU Training & Comparison on vdhwy-legion (RTX 3060)..."
ssh "$REMOTE" "cd $REMOTE_DIR && $REMOTE_PY -u train_compare_mixup.py | tee mixup_remote_job.log"

echo "[Done] Pulling remote comparison results back to local workspace..."
scp "$REMOTE:$REMOTE_DIR/mixup_comparison_results.json" ./mixup_comparison_results_rtx3060.json
scp "$REMOTE:$REMOTE_DIR/mixup_remote_job.log" ./mixup_remote_job.log
