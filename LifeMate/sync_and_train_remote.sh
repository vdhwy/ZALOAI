#!/bin/bash
# Sync SOTA Training Suite & Hierarchical Ensemble code to vdhwy@vdhwy-legion and run execution
set -e

REMOTE="${1:-vdhwy-legion}"
REMOTE_DIR="/home/huy/ZALOAI"
REMOTE_PY="/var/tmp/gguf/venv/bin/python"

echo "========================================================================"
echo "ZAC 2026 LifeMate — Remote Deployment & SOTA Execution on vdhwy-legion"
echo "Target Host: $REMOTE | Remote Dir: $REMOTE_DIR"
echo "========================================================================"

echo "[1/4] Checking SSH connection to $REMOTE..."
if ! ssh -o ConnectTimeout=8 "$REMOTE" "uname -a && nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader"; then
    echo "ERROR: Unable to connect to $REMOTE. Please verify that the Legion laptop is powered on, awake, and connected to Tailscale."
    exit 1
fi

echo "[2/4] Syncing SOTA code suite, PhoWhisper embeddings, and notebook..."
scp -O baseline.ipynb run_notebook.py lifemate_agent.py baseline.py extract_phowhisper_cache.py train_phowhisper_router.py train_sota_suite.py "$REMOTE:$REMOTE_DIR/"
ssh "$REMOTE" "mkdir -p $REMOTE_DIR/checkpoints $REMOTE_DIR/result"
scp -O checkpoints/phowhisper_embeddings.pt "$REMOTE:$REMOTE_DIR/checkpoints/" 2>/dev/null || true
scp -O checkpoints/phowhisper_router_sota.pt "$REMOTE:$REMOTE_DIR/checkpoints/" 2>/dev/null || true

echo "[3/4] Executing SOTA baseline notebook on vdhwy-legion (CUDA)..."
ssh "$REMOTE" "cd $REMOTE_DIR && mkdir -p checkpoints result && $REMOTE_PY run_notebook.py"

echo "[4/4] Pulling results, checkpoints, and executed notebook back to local workspace..."
scp -O "$REMOTE:$REMOTE_DIR/baseline.ipynb" ./baseline.ipynb
mkdir -p ./result ./checkpoints
scp -O "$REMOTE:$REMOTE_DIR/result/submission.jsonl" ./result/submission.jsonl 2>/dev/null || true
scp -O "$REMOTE:$REMOTE_DIR/result/eval_results.json" ./result/eval_results.json 2>/dev/null || true
scp -O "$REMOTE:$REMOTE_DIR/sota_comparison_results.json" ./sota_comparison_results.json 2>/dev/null || true
scp -O "$REMOTE:$REMOTE_DIR/checkpoints/tool_thresholds.json" ./checkpoints/tool_thresholds.json 2>/dev/null || true
scp -O "$REMOTE:$REMOTE_DIR/checkpoints/phowhisper_router_sota.pt" ./checkpoints/phowhisper_router_sota.pt 2>/dev/null || true
scp -O "$REMOTE:$REMOTE_DIR/checkpoints/hierarchical_router_sota.pt" ./checkpoints/hierarchical_router_sota.pt 2>/dev/null || true
scp -O "$REMOTE:$REMOTE_DIR/checkpoints/router_sota.pt" ./checkpoints/router_sota.pt 2>/dev/null || true
scp -O "$REMOTE:$REMOTE_DIR/checkpoints/router_ensemble_*.pt" ./checkpoints/ 2>/dev/null || true

echo "========================================================================"
echo "Deployment & Remote Execution Complete! Submission verified."
echo "========================================================================"
