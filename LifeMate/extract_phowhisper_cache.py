#!/usr/bin/env python3
"""Pre-extract 512-dim deep speech embeddings from pretrained PhoWhisper-base.

Caches embeddings into checkpoints/phowhisper_embeddings.pt for:
1. train.jsonl audio files
2. train_mixup.jsonl audio files
3. public_test.jsonl audio files
"""

import json
import os
from pathlib import Path
import sys
import time
import numpy as np
import torch

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"

from transformers import AutoFeatureExtractor, WhisperModel
from lifemate_agent import AudioProcessor

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "train+public_test"
CKPT_DIR = PROJECT_ROOT / "checkpoints"
CKPT_DIR.mkdir(exist_ok=True)
CACHE_FILE = CKPT_DIR / "phowhisper_embeddings.pt"

DEVICE = "cpu"
if torch.cuda.is_available():
    DEVICE = "cuda"
elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
    DEVICE = "mps"

print("=" * 80)
print(f"PRETRAINED SPEECH EMBEDDING EXTRACTOR (PhoWhisper-base on {DEVICE.upper()})")
print("=" * 80)

# Locate PhoWhisper snapshot
snapshots = list(Path.home().glob(".cache/huggingface/hub/models--vinai--PhoWhisper-base/snapshots/*"))
if not snapshots:
    print("ERROR: PhoWhisper-base snapshot not found in ~/.cache/huggingface/hub")
    sys.exit(1)

model_dir = str(snapshots[0])
print(f"Loading pretrained model from: {model_dir}")

feature_extractor = AutoFeatureExtractor.from_pretrained(model_dir, local_files_only=True)
whisper = WhisperModel.from_pretrained(model_dir, local_files_only=True)
encoder = whisper.encoder.to(DEVICE)
encoder.eval()

# Collect all audio references
existing_cache = {}
if CACHE_FILE.is_file():
    try:
        existing_cache = torch.load(CACHE_FILE, map_location="cpu")
        print(f"Loaded existing cache with {len(existing_cache)} pre-extracted embeddings.")
    except Exception:
        existing_cache = {}

audio_tasks = []

# 1. Train items
train_jsonl = DATA_DIR / "train" / "train.jsonl"
if train_jsonl.is_file():
    for l in open(train_jsonl, "r", encoding="utf-8"):
        it = json.loads(l)
        rel = it.get("audio")
        if rel and rel not in existing_cache:
            full_p = DATA_DIR / "train" / rel
            if full_p.is_file():
                audio_tasks.append((rel, full_p))

# 2. Mixup items
mixup_jsonl = DATA_DIR / "train" / "train_mixup.jsonl"
if mixup_jsonl.is_file():
    for l in open(mixup_jsonl, "r", encoding="utf-8"):
        it = json.loads(l)
        rel = it.get("audio")
        if rel and rel not in existing_cache:
            full_p = DATA_DIR / "train" / rel
            if full_p.is_file():
                audio_tasks.append((rel, full_p))

# 3. Public test items
test_jsonl = DATA_DIR / "public_test" / "public_test.jsonl"
if test_jsonl.is_file():
    for l in open(test_jsonl, "r", encoding="utf-8"):
        it = json.loads(l)
        rel = it.get("audio")
        if rel and rel not in existing_cache:
            full_p = DATA_DIR / "public_test" / rel
            if full_p.is_file():
                audio_tasks.append((rel, full_p))

# Deduplicate
unique_tasks = {}
for rel, p in audio_tasks:
    if rel not in unique_tasks:
        unique_tasks[rel] = p

print(f"Pending audio files to extract: {len(unique_tasks)}")

batch_size = 16
task_items = list(unique_tasks.items())
total = len(task_items)
t0 = time.time()
saved_count = 0

for i in range(0, total, batch_size):
    batch = task_items[i : i + batch_size]
    batch_audios = []
    batch_keys = []

    for rel, p in batch:
        try:
            samples, sr = AudioProcessor.read_wav(p)
            samples, sr = AudioProcessor.normalize_audio(samples, sr)
            batch_audios.append(samples)
            batch_keys.append(rel)
        except Exception as e:
            print(f"  Warning: failed reading {p}: {e}")

    if not batch_audios:
        continue

    inputs = feature_extractor(batch_audios, sampling_rate=16000, return_tensors="pt")
    with torch.no_grad():
        feat = inputs.input_features.to(DEVICE)
        hidden = encoder(feat).last_hidden_state
        # Mean pooling across the time dimension
        pooled = torch.mean(hidden, dim=1).cpu().numpy()

    for idx, k in enumerate(batch_keys):
        existing_cache[k] = pooled[idx].astype(np.float32)
        saved_count += 1

    if (i + batch_size) % 160 == 0 or (i + batch_size) >= total:
        elapsed = time.time() - t0
        rate = saved_count / max(1e-4, elapsed)
        print(f"  Processed {min(i + batch_size, total)}/{total} ({rate:.1f} files/sec, {elapsed:.1f}s elapsed)...", flush=True)
        # Checkpoint to disk
        torch.save(existing_cache, CACHE_FILE)

torch.save(existing_cache, CACHE_FILE)
print("=" * 80)
print(f"Extraction complete! Total cached embeddings: {len(existing_cache)} -> {CACHE_FILE}")
print(f"Total elapsed time: {time.time() - t0:.2f}s")
print("=" * 80)
