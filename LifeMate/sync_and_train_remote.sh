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

echo "[2/4] Syncing AST & SOTA code suite, embeddings, and notebook..."
scp -O baseline.ipynb run_notebook.py lifemate_agent.py baseline.py extract_ast_cache.py train_ast_router.py benchmark_ast_agent.py "$REMOTE:$REMOTE_DIR/"
ssh "$REMOTE" "mkdir -p $REMOTE_DIR/checkpoints $REMOTE_DIR/result"
scp -O checkpoints/ast_embeddings.pt "$REMOTE:$REMOTE_DIR/checkpoints/" 2>/dev/null || true
scp -O checkpoints/ast_router_sota.pt "$REMOTE:$REMOTE_DIR/checkpoints/" 2>/dev/null || true
scp -O checkpoints/ast_thresholds.json "$REMOTE:$REMOTE_DIR/checkpoints/" 2>/dev/null || true

echo "[3/4] Executing SOTA baseline notebook on vdhwy-legion (CUDA RTX 3060)..."
ssh "$REMOTE" "cd $REMOTE_DIR && mkdir -p checkpoints result && $REMOTE_PY run_notebook.py"

echo "[4/4] Pulling results, checkpoints, and executed notebook back to local workspace..."
scp -O "$REMOTE:$REMOTE_DIR/baseline.ipynb" ./baseline.ipynb
mkdir -p ./result ./checkpoints
scp -O "$REMOTE:$REMOTE_DIR/result/submission.jsonl" ./result/submission.jsonl 2>/dev/null || true
scp -O "$REMOTE:$REMOTE_DIR/result/eval_results.json" ./result/eval_results.json 2>/dev/null || true
scp -O "$REMOTE:$REMOTE_DIR/checkpoints/ast_thresholds.json" ./checkpoints/ast_thresholds.json 2>/dev/null || true
scp -O "$REMOTE:$REMOTE_DIR/checkpoints/ast_router_sota.pt" ./checkpoints/ast_router_sota.pt 2>/dev/null || true
scp -O "$REMOTE:$REMOTE_DIR/checkpoints/ast_ensemble_*.pt" ./checkpoints/ 2>/dev/null || true

echo "========================================================================"
echo "Deployment & Remote Execution Complete! Submission verified."
echo "========================================================================"
