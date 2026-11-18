#!/usr/bin/env python3
"""Comprehensive Benchmark and Submission Generator for LifeMate with AST Audio Classifier Router."""

import sys
import os
import json
import time
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path("train+public_test/train").resolve()))
from zaic_tools import ToolEnv, schema_validate
from lifemate_agent import HybridLifeMateAgent

PROJECT_ROOT = Path(".").resolve()
DATA_DIR = PROJECT_ROOT / "train+public_test"

def evaluate_train():
    print("========================================================================")
    print("Evaluating LifeMate Agent on Full Train Set (1,545 samples)...")
    print("========================================================================")
    train_lines = [json.loads(l) for l in open(DATA_DIR / "train" / "train.jsonl", "r", encoding="utf-8") if l.strip()]
    agent = HybridLifeMateAgent(mode="rule", use_neural_router=True)

    t0 = time.time()
    correct_hash = 0
    exact_seq = 0
    N = len(train_lines)

    for item in train_lines:
        sample_id = item["id"]
        o_env = ToolEnv("train", sample_id, root=DATA_DIR)
        for c in item["label"]["tool_calls"]:
            o_env.call(c["name"], c.get("arguments", {}))
        t_hash = o_env.get_state_hash()
        t_tools = [c["name"] for c in item["label"]["tool_calls"]]

        p_env = ToolEnv("train", sample_id, root=DATA_DIR)
        agent.predict(item, p_env)
        p_hash = p_env.get_state_hash()
        p_tools = [c["name"] for c in p_env.get_tool_calls()]

        if p_hash == t_hash:
            correct_hash += 1
        if p_tools == t_tools:
            exact_seq += 1

    elapsed = time.time() - t0
    print(f"Train Evaluation Complete in {elapsed:.2f}s ({elapsed/N*1000:.1f} ms/sample)")
    print(f"State Hash Accuracy: {correct_hash/N*100:.2f}% ({correct_hash}/{N})")
    print(f"Exact Tool Sequence: {exact_seq/N*100:.2f}% ({exact_seq}/{N})")
    return correct_hash, exact_seq, N

def generate_public_test_submission():
    print("\n========================================================================")
    print("Generating Public Test Submission (634 samples)...")
    print("========================================================================")
    test_lines = [json.loads(l) for l in open(DATA_DIR / "public_test" / "public_test.jsonl", "r", encoding="utf-8") if l.strip()]
    cache = json.load(open(PROJECT_ROOT / "public_test_transcriptions.json", "r", encoding="utf-8"))
    catalog = json.load(open(DATA_DIR / "public_test" / "public_test_tools_catalog.json", "r", encoding="utf-8"))

    agent = HybridLifeMateAgent(mode="rule", use_neural_router=True)

    all_calls = []
    records = []
    tool_counts = Counter()
    empty_count = 0

    t0 = time.time()
    for item in test_lines:
        sample_id = item["id"]
        item["audio_text"] = cache.get(sample_id, "")
        env = ToolEnv("public_test", sample_id, root=DATA_DIR)
        agent.predict(item, env)
        calls = env.get_tool_calls()
        all_calls.extend(calls)
        if not calls:
            empty_count += 1
        for c in calls:
            tool_counts[c["name"]] += 1

        records.append({
            "id": sample_id,
            "tool_calls": calls,
            "state_hash": env.get_state_hash(),
        })

    # Validate Schema
    val_res = schema_validate(all_calls, catalog)
    errors = [v for v in val_res if not v.get("ok")]
    assert len(errors) == 0, f"Schema validation errors found: {errors}"

    # Write files
    for fname in ["submission.jsonl", "submission2.jsonl", "result/submission.jsonl"]:
        out_p = PROJECT_ROOT / fname
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"Saved {len(records)} verified records to {fname}")

    print(f"\nSubmission Generation Complete in {time.time() - t0:.2f}s!")
    print(f"Total Tool Calls: {len(all_calls)} | Schema Errors: {len(errors)}")
    print(f"Conservative Rejections (Empty): {empty_count}/{len(records)} ({empty_count/len(records)*100:.1f}%)")
    print("Top 10 Predicted Tools:")
    for t, c in tool_counts.most_common(10):
        print(f"  {t:30s}: {c}")

if __name__ == "__main__":
    evaluate_train()
    generate_public_test_submission()
