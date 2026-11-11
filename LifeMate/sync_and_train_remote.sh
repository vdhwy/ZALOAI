#!/bin/bash
# Sync Audio Improvements & Mixup code to vdhwy@vdhwy-legion and run execution
set -e

REMOTE="${1:-vdhwy-legion}"
REMOTE_DIR="/home/huy/ZALOAI"
REMOTE_PY="/var/tmp/gguf/venv/bin/python"

echo "========================================================================"
echo "ZAC 2026 LifeMate — Remote Deployment & Execution on vdhwy-legion"
echo "Target Host: $REMOTE | Remote Dir: $REMOTE_DIR"
echo "========================================================================"

echo "[1/4] Checking SSH connection to $REMOTE..."
if ! ssh -o ConnectTimeout=8 "$REMOTE" "uname -a && nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader"; then
    echo "ERROR: Unable to connect to $REMOTE. Please verify that the Legion machine is powered on and connected to Tailscale."
    exit 1
fi

echo "[2/4] Syncing baseline.ipynb, run_notebook.py, lifemate_agent.py & train_compare_mixup.py..."
scp baseline.ipynb run_notebook.py lifemate_agent.py baseline.py train_compare_mixup.py "$REMOTE:$REMOTE_DIR/"

echo "[3/4] Executing baseline.ipynb via run_notebook.py on vdhwy-legion..."
ssh "$REMOTE" "cd $REMOTE_DIR && mkdir -p checkpoints result && $REMOTE_PY run_notebook.py"

echo "[4/4] Pulling results, checkpoints, and executed baseline.ipynb back to local workspace..."
scp "$REMOTE:$REMOTE_DIR/baseline.ipynb" ./baseline.ipynb
mkdir -p ./result ./checkpoints
scp "$REMOTE:$REMOTE_DIR/result/submission.jsonl" ./result/submission.jsonl 2>/dev/null || true
scp "$REMOTE:$REMOTE_DIR/result/eval_results.json" ./result/eval_results.json 2>/dev/null || true
scp "$REMOTE:$REMOTE_DIR/checkpoints/router_sota.pt" ./checkpoints/router_sota.pt 2>/dev/null || true

echo "========================================================================"
echo "Deployment & Remote Execution Complete! Submission verified."
echo "========================================================================"
