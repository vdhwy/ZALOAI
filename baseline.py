#!/usr/bin/env python3
"""Zalo AI Challenge 2026 — LifeMate: Complete Command-Line Baseline.
Supports:
  --evaluate: Evaluate agent on train dataset
  --predict:  Run prediction on public_test and output submission.jsonl
  --max-samples N: Run on N samples
"""
import argparse
import json
import os
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional

# Hardware device detection
device = "cpu"
try:
    import torch
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        device = "mps"
    elif torch.cuda.is_available():
        device = "cuda"
except Exception:
    pass

PROJECT_ROOT = Path(".").resolve()
DATA_DIR = PROJECT_ROOT / "train+public_test"

# Setup sys.path for zaic_tools
for p in [DATA_DIR / "train", DATA_DIR / "public_test"]:
    if p.is_dir() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

from zaic_tools import ToolEnv, schema_validate
from zaic_tools.utils import state_hash
from lifemate_agent import IntelligentReActAgent, VietnameseNormalizer, EnhancedDateTimeResolver


class PhoWhisperASR:
    def __init__(self, model_name: str = "vinai/PhoWhisper-base", device: str = device):
        self.model_name = model_name
        self.device = device
        self.cache_path = PROJECT_ROOT / "public_test_transcriptions.json"
        self.cache: Dict[str, str] = {}
        self._pipe = None
        self._load_cache()

    def _load_cache(self):
        if self.cache_path.is_file():
            try:
                self.cache = json.load(open(self.cache_path, "r", encoding="utf-8"))
            except Exception:
                pass

    def load_model(self):
        if self._pipe is None:
            try:
                from transformers import pipeline
                print(f"[ASR] Loading model {self.model_name} on {self.device}...")
                self._pipe = pipeline("automatic-speech-recognition", model=self.model_name, device=self.device)
            except Exception as e:
                print(f"[ASR Warning] Could not load ASR model ({e}). Fallback to text.")

    def transcribe(self, sample_id: str, audio_path: Path, fallback_text: str = "") -> str:
        if fallback_text:
            return fallback_text
        if sample_id in self.cache:
            return self.cache[sample_id]
        if self._pipe is None:
            self.load_model()
        if self._pipe is not None and audio_path.is_file():
            try:
                res = self._pipe(str(audio_path))
                text = res.get("text", "").strip()
                self.cache[sample_id] = text
                return text
            except Exception:
                pass
        return ""


def evaluate_agent(agent: IntelligentReActAgent, split: str = "train", max_samples: Optional[int] = 100):
    train_source = DATA_DIR / split / f"{split}.jsonl"
    print(f"\n--- Evaluating Agent on {split} (max: {max_samples} samples) ---")
    lines = open(train_source, "r", encoding="utf-8").readlines()
    correct_hash = 0
    exact_tools = 0
    total = 0

    for idx, line in enumerate(lines):
        if max_samples and idx >= max_samples:
            break
        item = json.loads(line)
        sample_id = item["id"]

        # Oracle
        o_env = ToolEnv(split, sample_id, root=DATA_DIR)
        for c in item["label"]["tool_calls"]:
            o_env.call(c["name"], c.get("arguments", {}))
        target_hash = o_env.get_state_hash()
        target_tools = [c["name"] for c in item["label"]["tool_calls"]]

        # Prediction
        p_env = ToolEnv(split, sample_id, root=DATA_DIR)
        agent.predict(item, p_env)
        pred_hash = p_env.get_state_hash()
        pred_tools = [c["name"] for c in p_env.get_tool_calls()]

        if pred_hash == target_hash:
            correct_hash += 1
        if pred_tools == target_tools:
            exact_tools += 1
        total += 1

        if total % 25 == 0:
            print(f"[{total}/{max_samples or len(lines)}] State Hash Accuracy: {correct_hash/total*100:.2f}%")

    print(f"\n=== EVALUATION RESULTS (N={total}) ===")
    print(f"State Hash Accuracy:   {correct_hash/total*100:.2f}% ({correct_hash}/{total})")
    print(f"Exact Tool Sequence:   {exact_tools/total*100:.2f}% ({exact_tools}/{total})")


def generate_submission(agent: IntelligentReActAgent, asr: PhoWhisperASR, split: str = "public_test", out_path: Optional[Path] = None):
    test_source = DATA_DIR / split / f"{split}.jsonl"
    out_file = out_path or (PROJECT_ROOT / "submission.jsonl")
    print(f"\n--- Generating Submission for {split} -> {out_file} ---")
    lines = open(test_source, "r", encoding="utf-8").readlines()
    count = 0
    all_calls = []

    with open(out_file, "w", encoding="utf-8") as fout:
        for idx, line in enumerate(lines, 1):
            if not line.strip():
                continue
            item = json.loads(line)
            sample_id = item["id"]

            audio_file = DATA_DIR / split / item["audio"]
            item["audio_text"] = asr.transcribe(sample_id, audio_file)

            env = ToolEnv(split, sample_id, root=DATA_DIR)
            agent.predict(item, env)

            calls = env.get_tool_calls()
            all_calls.extend(calls)
            record = {
                "id": sample_id,
                "tool_calls": calls,
                "state_hash": env.get_state_hash(),
            }
            fout.write(json.dumps(record, ensure_ascii=False) + "\n")
            count += 1
            if count % 100 == 0:
                print(f"Processed {count}/{len(lines)} samples...")

    print(f"Generated {count} records into {out_file}.")

    # Validate Schema
    catalog_path = DATA_DIR / split / f"{split}_tools_catalog.json"
    if catalog_path.is_file():
        catalog = json.load(open(catalog_path, "r", encoding="utf-8"))
        val_res = schema_validate(all_calls, catalog)
        errors = [v for v in val_res if not v.get("ok")]
        print(f"Schema validation: {len(all_calls)} tool calls checked, {len(errors)} errors found.")
        if not errors:
            print("100% SCHEMA COMPLIANT! Ready for leaderboard submission.")


def main():
    parser = argparse.ArgumentParser(description="ZAC 2026 LifeMate Baseline Runner")
    parser.add_argument("--evaluate", action="store_true", help="Run evaluation on train dataset")
    parser.add_argument("--predict", action="store_true", help="Run prediction on public_test dataset")
    parser.add_argument("--max-samples", type=int, default=None, help="Max samples to evaluate")
    args = parser.parse_args()

    agent = IntelligentReActAgent()
    asr = PhoWhisperASR()

    if args.evaluate or (not args.evaluate and not args.predict):
        evaluate_agent(agent, split="train", max_samples=args.max_samples or 100)

    if args.predict:
        generate_submission(agent, asr, split="public_test")


if __name__ == "__main__":
    main()
