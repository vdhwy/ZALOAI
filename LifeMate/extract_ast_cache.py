#!/usr/bin/env python3
"""Pre-extract 768-dimensional AST (Audio Spectrogram Transformer) embeddings
from the pretrained model 'MIT/ast-finetuned-audioset-10-10-0.4593'
specifically designed for Audio Classification.
"""

import os
import sys
import time
import json
from pathlib import Path
import soundfile as sf
import numpy as np
import torch
from transformers import AutoFeatureExtractor, ASTModel

PROJECT_ROOT = Path(".").resolve()
DATA_DIR = PROJECT_ROOT / "train+public_test"
CHECKPOINTS_DIR = PROJECT_ROOT / "checkpoints"
CHECKPOINTS_DIR.mkdir(parents=True, exist_ok=True)
CACHE_FILE = CHECKPOINTS_DIR / "ast_embeddings.pt"

DEVICE = "mps" if hasattr(torch.backends, "mps") and torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")
MODEL_NAME = "MIT/ast-finetuned-audioset-10-10-0.4593"
BATCH_SIZE = 32

def main():
    print(f"========================================================================")
    print(f"AST (Audio Spectrogram Transformer) Audio Classification Cache Extractor")
    print(f"Model: {MODEL_NAME}")
    print(f"Device: {DEVICE} | Batch size: {BATCH_SIZE}")
    print(f"Output: {CACHE_FILE}")
    print(f"========================================================================")

    # 1. Collect all target audio files from train and public_test
    tasks = [] # (rel_path, abs_path)
    for split in ["train", "public_test"]:
        jsonl_path = DATA_DIR / split / f"{split}.jsonl"
        if not jsonl_path.is_file():
            continue
        for line in open(jsonl_path, "r", encoding="utf-8"):
            if not line.strip():
                continue
            item = json.loads(line)
            rel_audio = item.get("audio")
            if rel_audio:
                abs_p = DATA_DIR / split / rel_audio
                if abs_p.is_file():
                    tasks.append((rel_audio, abs_p))

    # Deduplicate while preserving order
    seen = set()
    unique_tasks = []
    for rel_p, abs_p in tasks:
        if rel_p not in seen:
            seen.add(rel_p)
            unique_tasks.append((rel_p, abs_p))

    print(f"Total audio files found: {len(unique_tasks)}")

    # 2. Load existing cache if present
    cache = {}
    if CACHE_FILE.is_file():
        try:
            cache = torch.load(CACHE_FILE, map_location="cpu", weights_only=False)
            print(f"Resuming from existing cache: {len(cache)} files already extracted.")
        except Exception as e:
            print(f"Warning: could not load existing cache ({e}), starting fresh.")
            cache = {}

    remaining_tasks = [(rel_p, abs_p) for rel_p, abs_p in unique_tasks if rel_p not in cache]
    print(f"Files remaining to extract: {len(remaining_tasks)}")

    if not remaining_tasks:
        print("All audio files are already extracted! Cache is complete.")
        return

    # 3. Load AST model & feature extractor
    print(f"\nLoading AST feature extractor and model from {MODEL_NAME}...")
    feature_extractor = AutoFeatureExtractor.from_pretrained(MODEL_NAME)
    model = ASTModel.from_pretrained(MODEL_NAME).to(DEVICE).eval()

    t0 = time.time()
    batch_rel = []
    batch_audio = []

    def flush_batch(b_rel, b_audio):
        if not b_rel:
            return
        with torch.inference_mode():
            inputs = feature_extractor(
                b_audio,
                sampling_rate=16000,
                return_tensors="pt",
                padding="max_length",
                max_length=1024,
                truncation=True
            ).to(DEVICE)
            out = model(**inputs)
            # pooler_output shape: (B, 768)
            embs = out.pooler_output.cpu().numpy().astype(np.float32)
            for r_p, emb in zip(b_rel, embs):
                cache[r_p] = emb

    processed = 0
    total = len(remaining_tasks)

    for i, (rel_p, abs_p) in enumerate(remaining_tasks, 1):
        try:
            audio, sr = sf.read(abs_p)
            # Ensure float32 mono
            if audio.ndim > 1:
                audio = audio.mean(axis=1)
            audio = audio.astype(np.float32)
            batch_rel.append(rel_p)
            batch_audio.append(audio)
        except Exception as e:
            print(f"Error reading {abs_p}: {e}")
            cache[rel_p] = np.zeros(768, dtype=np.float32)

        if len(batch_audio) >= BATCH_SIZE or i == total:
            flush_batch(batch_rel, batch_audio)
            processed += len(batch_rel)
            batch_rel = []
            batch_audio = []

            # Progress update and checkpoint saving every 10 batches
            if processed % (BATCH_SIZE * 5) == 0 or processed == total:
                elapsed = time.time() - t0
                speed = processed / elapsed if elapsed > 0 else 0
                eta = (total - processed) / speed if speed > 0 else 0
                print(f"[{processed}/{total}] {processed/total*100:.1f}% | Speed: {speed:.1f} files/s | ETA: {eta:.0f}s")
                torch.save(cache, CACHE_FILE)

    torch.save(cache, CACHE_FILE)
    print(f"\nExtraction complete! Total cached: {len(cache)} files. Saved to {CACHE_FILE}.")

if __name__ == "__main__":
    main()
