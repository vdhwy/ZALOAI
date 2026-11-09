"""Batch transcribe public_test audio using vinai/PhoWhisper-base with MPS acceleration.
Saves progress incrementally to public_test_transcriptions.json.
"""
import json
import os
import time
from pathlib import Path

ROOT = Path(".").resolve()
AUDIO_DIR = ROOT / "train+public_test" / "public_test"
TEST_JSONL = AUDIO_DIR / "public_test.jsonl"
OUT_CACHE = ROOT / "public_test_transcriptions.json"

def main():
    cache = {}
    if OUT_CACHE.is_file():
        try:
            cache = json.load(open(OUT_CACHE, "r", encoding="utf-8"))
            print(f"Loaded existing cache with {len(cache)} transcriptions.")
        except Exception:
            cache = {}

    lines = open(TEST_JSONL, "r", encoding="utf-8").readlines()
    needed = []
    for line in lines:
        if not line.strip():
            continue
        item = json.loads(line)
        if item["id"] not in cache:
            needed.append(item)

    print(f"Total samples: {len(lines)} | Already transcribed: {len(cache)} | Remaining: {len(needed)}")
    if not needed:
        print("All samples are already transcribed!")
        return

    import torch
    from transformers import pipeline

    device = "mps" if hasattr(torch.backends, "mps") and torch.backends.mps.is_available() else "cpu"
    print(f"Loading vinai/PhoWhisper-base on device '{device}'...")
    pipe = pipeline("automatic-speech-recognition", model="vinai/PhoWhisper-base", device=device)
    print("Model loaded successfully. Starting batch transcription...")

    t0 = time.time()
    for idx, item in enumerate(needed, 1):
        sample_id = item["id"]
        audio_file = AUDIO_DIR / item["audio"]
        if audio_file.is_file():
            try:
                res = pipe(str(audio_file))
                cache[sample_id] = res.get("text", "").strip()
            except Exception as e:
                print(f"Error on {sample_id}: {e}")
                cache[sample_id] = ""
        else:
            cache[sample_id] = ""

        if idx % 10 == 0 or idx == len(needed):
            elapsed = time.time() - t0
            rate = idx / elapsed
            rem = (len(needed) - idx) / rate if rate > 0 else 0
            print(f"[{idx}/{len(needed)}] Transcribed {sample_id}: '{cache[sample_id]}' ({rate:.2f} samples/s, ~{rem/60:.1f} mins remaining)")
            with open(OUT_CACHE, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)

    print(f"Transcription complete! Saved {len(cache)} transcriptions to {OUT_CACHE}.")

if __name__ == "__main__":
    main()
