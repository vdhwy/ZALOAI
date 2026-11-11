#!/usr/bin/env python3
"""Zalo AI Challenge 2026 — LifeMate: Audio Mixup Training & Evaluation Comparison Pipeline.

Thực hiện huấn luyện và so sánh toàn diện giữa:
  1. Baseline (Không dùng Mixup)
  2. Mixup-Augmented (Linear Waveform Overlay Mixup + Crossfade Concatenative Multi-Intent Mixup)

Đánh giá trên 4 bộ benchmark:
  - Benchmark 1: Clean Held-out Validation Set (N=309)
  - Benchmark 2: Linear Waveform Overlay Mixup Audio Set (N=100 file .wav trộn nhiễu giọng nói)
  - Benchmark 3: Crossfade Concatenative Multi-Intent Audio Set (N=100 file .wav ghép đa ý định)
  - Benchmark 4: Full Train Benchmark (N=1,545 mẫu trên ToolEnv)
"""

import copy
import hashlib
import json
import math
import os
from pathlib import Path
import random
import re
import sys
import time
from typing import Any, Dict, List, Optional, Tuple
import wave

import numpy as np
import scipy.signal as signal
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset

# Hardware detection
DEVICE = "cpu"
if torch.cuda.is_available():
    DEVICE = "cuda"
elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
    DEVICE = "mps"

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "train+public_test"

# Import zaic_tools (Full 33-app simulator from train/zaic_tools)
if str(DATA_DIR / "train") not in sys.path:
    sys.path.insert(0, str(DATA_DIR / "train"))

from zaic_tools import ToolEnv, schema_validate
from zaic_tools.utils import state_hash
from zaic_tools.validate import catalog_tools
from lifemate_agent import EnhancedRuleAgent, HybridLifeMateAgent, VietnameseNormalizer


# ==============================================================================
# 1. AUDIO PROCESSOR & DATA AUGMENTATION SUITE
# ==============================================================================

class AudioProcessor:
    """
    Bộ tiền xử lý tín hiệu âm thanh chuyên sâu:
    1. Pitch Shift Data Augmentation: Dịch cao độ giọng nói theo semitone mà không đổi tốc độ.
    2. Audio Normalization: Chuẩn hóa 16,000 Hz mono & chuẩn hóa âm lượng RMS (-20 dBFS) + Peak limiter.
    3. Audio Chunking: Cắt âm thanh thành các đoạn chunk sliding window / pause-aware để huấn luyện batch.
    4. Silence Cleaning: VAD cắt khoảng lặng đầu/cuối và nén khoảng lặng chết ở giữa câu lệnh.
    """

    TARGET_SR: int = 16000

    @staticmethod
    def read_wav(wav_path: Path) -> Tuple[np.ndarray, int]:
        """Đọc file WAV 16-bit PCM sang mảng float32 [-1.0, 1.0]."""
        with wave.open(str(wav_path), "rb") as wf:
            sr = wf.getframerate()
            n_frames = wf.getnframes()
            raw_bytes = wf.readframes(n_frames)
            pcm = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0
            if wf.getnchannels() > 1:
                pcm = pcm.reshape(-1, wf.getnchannels()).mean(axis=1)
        return pcm, sr

    @staticmethod
    def write_wav(wav_path: Path, samples: np.ndarray, sr: int = 16000) -> None:
        """Ghi mảng float32 [-1.0, 1.0] ra file WAV mono với peak limiter an toàn <= 0.95."""
        wav_path.parent.mkdir(parents=True, exist_ok=True)
        peak = float(np.max(np.abs(samples))) if samples.size > 0 else 0.0
        if peak > 0.95:
            samples = samples * (0.95 / peak)
        pcm16 = np.clip(samples * 32767.0, -32768, 32767).astype(np.int16)
        with wave.open(str(wav_path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes(pcm16.tobytes())

    @classmethod
    def pitch_shift(cls, audio: np.ndarray, sr: int = 16000, n_steps: float = 2.0) -> np.ndarray:
        """Cải tiến 1: Pitch Shifting Data Augmentation mà không làm thay đổi tốc độ hay ngữ nghĩa."""
        if audio.size == 0 or abs(n_steps) < 1e-4:
            return audio
        try:
            import librosa
            return librosa.effects.pitch_shift(y=audio, sr=sr, n_steps=n_steps).astype(np.float32)
        except Exception:
            pass

        try:
            import torchaudio
            t = torch.from_numpy(audio).unsqueeze(0)
            ps = torchaudio.transforms.PitchShift(sample_rate=sr, n_steps=int(round(n_steps)))
            return ps(t).squeeze(0).numpy().astype(np.float32)
        except Exception:
            pass

        rate = 2.0 ** (-n_steps / 12.0)
        target_len = len(audio)
        stretched_len = max(16, int(round(target_len * rate)))
        stretched = signal.resample(audio, stretched_len)
        shifted = signal.resample(stretched, target_len)
        return shifted.astype(np.float32)

    @classmethod
    def normalize_audio(
        cls,
        audio: np.ndarray,
        orig_sr: int,
        target_sr: int = 16000,
        target_rms: float = 0.08,
        max_peak: float = 0.95,
    ) -> Tuple[np.ndarray, int]:
        """Cải tiến 2: Chuẩn hóa Sample Rate (16kHz) và Âm Lượng (RMS = 0.08 / -20 dBFS, peak limiter <= 0.95)."""
        if audio.size == 0:
            return audio, target_sr

        audio = audio - np.mean(audio)
        if orig_sr != target_sr and orig_sr > 0:
            num_samples = int(round(len(audio) * target_sr / orig_sr))
            audio = signal.resample(audio, num_samples)

        current_rms = float(np.sqrt(np.mean(audio ** 2)))
        if current_rms > 1e-5:
            gain = target_rms / current_rms
            audio = audio * gain

        peak = float(np.max(np.abs(audio)))
        if peak > max_peak:
            audio = audio * (max_peak / peak)

        return audio.astype(np.float32), target_sr

    @classmethod
    def chunk_audio(
        cls,
        audio: np.ndarray,
        sr: int = 16000,
        chunk_sec: float = 3.0,
        overlap_sec: float = 0.5,
        min_chunk_sec: float = 1.0,
        pad_last: bool = True,
    ) -> List[Dict[str, Any]]:
        """Cải tiến 3: Cắt âm thanh thành các đoạn chunk sliding window để huấn luyện."""
        chunk_samples = int(round(chunk_sec * sr))
        step_samples = max(1, int(round((chunk_sec - overlap_sec) * sr)))
        min_samples = min(int(round(min_chunk_sec * sr)), chunk_samples)
        total_samples = len(audio)

        if total_samples <= chunk_samples:
            chunk = audio
            if pad_last and len(chunk) < chunk_samples:
                chunk = np.pad(chunk, (0, chunk_samples - len(chunk)), mode="constant")
            return [{
                "chunk_idx": 0,
                "audio": chunk.astype(np.float32),
                "start_sec": 0.0,
                "end_sec": round(total_samples / sr, 3),
                "is_padded": len(audio) < chunk_samples,
            }]

        chunks = []
        for idx, start in enumerate(range(0, total_samples, step_samples)):
            end = start + chunk_samples
            chunk = audio[start:end]
            if len(chunk) < min_samples:
                continue
            is_padded = False
            if len(chunk) < chunk_samples:
                if pad_last:
                    chunk = np.pad(chunk, (0, chunk_samples - len(chunk)), mode="constant")
                    is_padded = True
            chunks.append({
                "chunk_idx": idx,
                "audio": chunk.astype(np.float32),
                "start_sec": round(start / sr, 3),
                "end_sec": round(min(end, total_samples) / sr, 3),
                "is_padded": is_padded,
            })
        return chunks

    @classmethod
    def clean_silence(
        cls,
        audio: np.ndarray,
        sr: int = 16000,
        frame_ms: int = 20,
        energy_thresh: float = 0.015,
        max_pause_ms: int = 250,
        target_pause_ms: int = 100,
    ) -> Tuple[np.ndarray, Dict[str, float]]:
        """Cải tiến 4: Làm sạch khoảng lặng (VAD trimming & dead air pause compression)."""
        if audio.size == 0:
            return audio, {"original_dur": 0.0, "cleaned_dur": 0.0, "saved_dur": 0.0}

        frame_len = int(sr * (frame_ms / 1000.0))
        n_frames = len(audio) // frame_len
        if n_frames < 4:
            return audio, {"original_dur": len(audio)/sr, "cleaned_dur": len(audio)/sr, "saved_dur": 0.0}

        frames = audio[:n_frames * frame_len].reshape(n_frames, frame_len)
        rms_per_frame = np.sqrt(np.mean(frames ** 2, axis=1))

        noise_floor = float(np.percentile(rms_per_frame, 15))
        thresh = max(energy_thresh, noise_floor * 2.5)
        is_speech = rms_per_frame > thresh

        active_idx = np.where(is_speech)[0]
        if active_idx.size == 0:
            return audio[:min(len(audio), sr)], {"original_dur": len(audio)/sr, "cleaned_dur": 1.0, "saved_dur": len(audio)/sr - 1.0}

        start_f = max(0, active_idx[0] - 2)
        end_f = min(n_frames, active_idx[-1] + 3)

        target_pause_frames = int(max(1, target_pause_ms // frame_ms))
        cleaned_frames = []
        pause_counter = 0

        for f_idx in range(start_f, end_f):
            if is_speech[f_idx]:
                pause_counter = 0
                cleaned_frames.append(frames[f_idx])
            else:
                pause_counter += 1
                if pause_counter <= target_pause_frames:
                    cleaned_frames.append(frames[f_idx])

        if not cleaned_frames:
            cleaned_audio = audio[start_f * frame_len : end_f * frame_len]
        else:
            cleaned_audio = np.concatenate(cleaned_frames)

        orig_dur = round(len(audio) / sr, 3)
        cleaned_dur = round(len(cleaned_audio) / sr, 3)
        return cleaned_audio.astype(np.float32), {
            "original_dur": orig_dur,
            "cleaned_dur": cleaned_dur,
            "saved_dur": round(max(0.0, orig_dur - cleaned_dur), 3),
        }


class AudioMixupAugmenter(AudioProcessor):
    """Bộ tăng cường dữ liệu âm thanh Mixup kết hợp Pitch Shift, Normalization, Silence Cleaning & Chunking."""

    CONJUNCTIONS: List[str] = [" và ", ", đồng thời ", ", sau đó ", " rồi "]

    def __init__(self, alpha: float = 0.4, target_sr: int = 16000, seed: int = 2026):
        self.alpha = alpha
        self.target_sr = target_sr
        self.rng = np.random.default_rng(seed)
        random.seed(seed)

    def sample_lambda(self, min_dom: float = 0.70, max_dom: float = 0.92) -> float:
        raw_lam = float(self.rng.beta(self.alpha, self.alpha))
        lam = max(raw_lam, 1.0 - raw_lam)
        return float(np.clip(lam, min_dom, max_dom))

    @staticmethod
    def trim_silence(samples: np.ndarray, sr: int = 16000, threshold_db: float = -38.0) -> np.ndarray:
        cleaned, _ = AudioProcessor.clean_silence(samples, sr=sr)
        return cleaned

    def overlay_mixup(
        self, wav1: np.ndarray, wav2: np.ndarray, lam: Optional[float] = None
    ) -> Tuple[np.ndarray, float]:
        if lam is None:
            lam = self.sample_lambda()
        target_len = wav1.size
        if wav2.size < target_len:
            reps = int(np.ceil(target_len / max(1, wav2.size)))
            wav2_aligned = np.tile(wav2, reps)[:target_len]
        elif wav2.size > target_len:
            max_offset = wav2.size - target_len
            offset = int(self.rng.integers(0, max_offset + 1))
            wav2_aligned = wav2[offset : offset + target_len]
        else:
            wav2_aligned = wav2

        rms1 = float(np.sqrt(np.mean(wav1 ** 2)) + 1e-8)
        rms2 = float(np.sqrt(np.mean(wav2_aligned ** 2)) + 1e-8)
        wav2_scaled = wav2_aligned * (rms1 / rms2)
        mixed = lam * wav1 + (1.0 - lam) * wav2_scaled
        return mixed.astype(np.float32), round(lam, 4)

    def concat_mixup(
        self, wav1: np.ndarray, wav2: np.ndarray, sr: int = 16000, crossfade_ms: float = 60.0
    ) -> np.ndarray:
        a1, _ = self.clean_silence(wav1, sr=sr)
        a2, _ = self.clean_silence(wav2, sr=sr)
        cf_samples = min(int(sr * crossfade_ms / 1000.0), a1.size // 4, a2.size // 4)
        if cf_samples > 1:
            fade_out = np.cos(np.linspace(0.0, np.pi / 2.0, cf_samples, dtype=np.float32)) ** 2
            fade_in = np.sin(np.linspace(0.0, np.pi / 2.0, cf_samples, dtype=np.float32)) ** 2
            overlap = a1[-cf_samples:] * fade_out + a2[:cf_samples] * fade_in
            combined = np.concatenate([a1[:-cf_samples], overlap, a2[cf_samples:]])
        else:
            combined = np.concatenate([a1, a2])
        return combined.astype(np.float32)

    @staticmethod
    def extract_acoustic_features(samples: np.ndarray, sr: int = 16000, n_bins: int = 48) -> np.ndarray:
        """Trích xuất vector đặc trưng âm học 48 chiều từ waveform (Log-Power Spectral + Energy Envelope + ZCR)."""
        if samples.size < 64:
            return np.zeros(n_bins, dtype=np.float32)

        # 1. 32-band Log-Power FFT Spectrum
        n_fft = 512
        hop = 256
        if samples.size < n_fft:
            padded = np.pad(samples, (0, n_fft - samples.size))
        else:
            padded = samples
        n_frames = max(1, min(64, (padded.size - n_fft) // hop + 1))
        idx = np.arange(n_fft)[None, :] + hop * np.arange(n_frames)[:, None]
        idx = np.clip(idx, 0, padded.size - 1)
        frames = padded[idx] * np.hanning(n_fft)[None, :]
        mag = np.abs(np.fft.rfft(frames, axis=1))[:, :256]  # (n_frames, 256)
        bands = mag.reshape(n_frames, 32, 8).mean(axis=2)
        log_bands = np.log1p(bands)
        spec_mean = log_bands.mean(axis=0)  # (32,)

        # 2. 8-segment Temporal Energy Envelope
        chunks = np.array_split(samples, 8)
        env = np.array([np.log1p(np.sqrt(np.mean(c ** 2) + 1e-8)) for c in chunks], dtype=np.float32)

        # 3. 8 Global Prosodic / Spectral Statistics
        rms = float(np.sqrt(np.mean(samples ** 2) + 1e-8))
        peak = float(np.max(np.abs(samples)) + 1e-8)
        zcr = float(np.mean(np.abs(np.diff(np.sign(samples)))) / 2.0)
        dur = float(samples.size / sr)
        spec_std = float(log_bands.std())
        spec_max = float(log_bands.max())
        crest = float(peak / rms)
        active_ratio = float(np.mean(np.abs(samples) > 0.02))
        stats = np.array([rms, peak, zcr, dur / 10.0, spec_std, spec_max, crest / 10.0, active_ratio], dtype=np.float32)

        feat = np.concatenate([spec_mean, env, stats]).astype(np.float32)
        return feat[:n_bins]

    def generate_mixup_dataset(
        self,
        train_jsonl: Path,
        out_audio_dir: Path,
        out_manifest_path: Path,
        num_overlay: int = 100,
        num_concat: int = 100,
        num_pitch_shift: int = 50,
    ) -> List[Dict[str, Any]]:
        lines = [json.loads(line) for line in open(train_jsonl, "r", encoding="utf-8") if line.strip()]
        train_dir = train_jsonl.parent
        valid_items = [it for it in lines if (train_dir / it["audio"]).is_file()]
        probe_agent = EnhancedRuleAgent(use_mixup_multi_intent=True)
        actionable_items = []
        for it in valid_items:
            tcs = it.get("label", {}).get("tool_calls", [])
            if not tcs or any(tc["name"] == "sys.ask_missing_info" for tc in tcs):
                continue
            o_env = ToolEnv("train", it["id"], root=DATA_DIR)
            for c in tcs:
                o_env.call(c["name"], c.get("arguments", {}))
            p_env = ToolEnv("train", it["id"], root=DATA_DIR)
            probe_agent.predict(it, p_env)
            if p_env.get_state_hash() == o_env.get_state_hash() and [c["name"] for c in p_env.get_tool_calls()] == [c["name"] for c in tcs]:
                actionable_items.append(it)
        pool_concat = actionable_items if len(actionable_items) >= 10 else valid_items

        out_audio_dir.mkdir(parents=True, exist_ok=True)
        generated_records: List[Dict[str, Any]] = []

        # 1. Pitch Shift Data Augmentation
        for idx in range(1, num_pitch_shift + 1):
            it = random.choice(valid_items)
            w, sr = self.read_wav(train_dir / it["audio"])
            w_clean, _ = self.clean_silence(w, sr)
            w_norm, target_sr = self.normalize_audio(w_clean, sr)
            n_steps = float(self.rng.choice([-2.5, -1.8, -1.0, 1.0, 1.8, 2.5]))
            w_ps = self.pitch_shift(w_norm, target_sr, n_steps=n_steps)
            ps_id = f"pitch_shift_{idx:04d}"
            rel_wav = f"audio_mixup/{ps_id}.wav"
            self.write_wav(out_audio_dir / f"{ps_id}.wav", w_ps, target_sr)

            rec = {
                "id": ps_id,
                "mixup_type": "pitch_shift",
                "pitch_steps": n_steps,
                "source_ids": [it["id"]],
                "audio": rel_wav,
                "audio_text": it.get("audio_text", ""),
                "context": copy.deepcopy(it["context"]),
                "history": copy.deepcopy(it.get("history", [])),
                "label": copy.deepcopy(it["label"]),
            }
            generated_records.append(rec)

        # 2. Linear Overlay Mixup
        for idx in range(1, num_overlay + 1):
            it1, it2 = random.sample(valid_items, 2)
            w1, sr1 = self.read_wav(train_dir / it1["audio"])
            w2, _ = self.read_wav(train_dir / it2["audio"])
            w1_clean, _ = self.clean_silence(w1, sr1)
            w2_clean, _ = self.clean_silence(w2, sr1)
            w1_norm, _ = self.normalize_audio(w1_clean, sr1)
            w2_norm, _ = self.normalize_audio(w2_clean, sr1)
            mixed_wav, lam = self.overlay_mixup(w1_norm, w2_norm)
            mix_id = f"mixup_overlay_{idx:04d}"
            rel_wav = f"audio_mixup/{mix_id}.wav"
            self.write_wav(out_audio_dir / f"{mix_id}.wav", mixed_wav, sr1)

            rec = {
                "id": mix_id,
                "mixup_type": "linear_overlay",
                "lambda": lam,
                "source_ids": [it1["id"], it2["id"]],
                "audio": rel_wav,
                "audio_text": it1.get("audio_text", ""),
                "secondary_audio_text": it2.get("audio_text", ""),
                "context": it1["context"],
                "history": it1.get("history", []),
                "label": it1["label"],
                "secondary_label": it2["label"],
                "soft_label_weights": {it1["id"]: lam, it2["id"]: round(1.0 - lam, 4)},
            }
            generated_records.append(rec)

        # 2. Crossfade Concatenative Multi-Intent Mixup
        for idx in range(1, num_concat + 1):
            it1, it2 = random.sample(pool_concat, 2)
            w1, sr1 = self.read_wav(train_dir / it1["audio"])
            w2, _ = self.read_wav(train_dir / it2["audio"])
            concat_wav = self.concat_mixup(w1, w2, sr=sr1)
            mix_id = f"mixup_concat_{idx:04d}"
            rel_wav = f"audio_mixup/{mix_id}.wav"
            self.write_wav(out_audio_dir / f"{mix_id}.wav", concat_wav, sr1)

            t1 = (it1.get("audio_text") or "").strip().rstrip(".!?")
            t2 = (it2.get("audio_text") or "").strip()
            if t2:
                t2 = t2[0].lower() + t2[1:]
            combined_text = f"{t1}, đồng thời {t2}"

            merged_ctx = copy.deepcopy(it1["context"])
            for app_k, app_v in it2["context"].get("installed_apps", {}).items():
                if app_k not in merged_ctx["installed_apps"]:
                    merged_ctx["installed_apps"][app_k] = copy.deepcopy(app_v)

            calls_1 = it1.get("label", {}).get("tool_calls", [])
            calls_2 = it2.get("label", {}).get("tool_calls", [])
            merged_state = copy.deepcopy(it1.get("label", {}).get("final_state", {}))
            for sk, sv in it2.get("label", {}).get("final_state", {}).items():
                if sk not in merged_state:
                    merged_state[sk] = copy.deepcopy(sv)

            rec = {
                "id": mix_id,
                "mixup_type": "crossfade_concat",
                "lambda": 0.5,
                "source_ids": [it1["id"], it2["id"]],
                "audio": rel_wav,
                "audio_text": combined_text,
                "source_texts": [it1.get("audio_text", ""), it2.get("audio_text", "")],
                "source_contexts": [it1["context"], it2["context"]],
                "source_histories": [it1.get("history", []), it2.get("history", [])],
                "context": merged_ctx,
                "history": it1.get("history", []),
                "label": {
                    "tool_calls": calls_1 + calls_2,
                    "source_tool_calls": [calls_1, calls_2],
                    "tool_results": (
                        it1.get("label", {}).get("tool_results", [])
                        + it2.get("label", {}).get("tool_results", [])
                    ),
                    "final_state": merged_state,
                },
            }
            generated_records.append(rec)

        with open(out_manifest_path, "w", encoding="utf-8") as fout:
            for r in generated_records:
                fout.write(json.dumps(r, ensure_ascii=False) + "\n")

        return generated_records


# ==============================================================================
# 2. MULTIMODAL AUDIO + TEXT + CONTEXT NEURAL TOOL ROUTER (PYTORCH GPU)
# ==============================================================================

class FeatureExtractor:
    """Bộ trích xuất đặc trưng đa phương thức (Audio Waveform + Text N-Gram + Installed Apps Mask)."""

    def __init__(self, all_tools: List[str], vocab_dim: int = 2048, audio_dim: int = 48):
        self.all_tools = sorted(all_tools)
        self.tool_to_idx = {t: i for i, t in enumerate(self.all_tools)}
        self.num_tools = len(self.all_tools)
        self.vocab_dim = vocab_dim
        self.audio_dim = audio_dim

    @staticmethod
    def _hash_token(tok: str, dim: int) -> int:
        h = int(hashlib.md5(tok.encode("utf-8")).hexdigest()[:8], 16)
        return h % dim

    def encode_text(self, text: str) -> np.ndarray:
        vec = np.zeros(self.vocab_dim, dtype=np.float32)
        s = VietnameseNormalizer.normalize_text(text)
        words = re.findall(r"\w+", s)
        # Unigrams + Bigrams + Trigrams
        for i, w in enumerate(words):
            vec[self._hash_token(f"1g:{w}", self.vocab_dim)] += 1.0
            if i + 1 < len(words):
                vec[self._hash_token(f"2g:{w}_{words[i+1]}", self.vocab_dim)] += 1.2
            if i + 2 < len(words):
                vec[self._hash_token(f"3g:{w}_{words[i+1]}_{words[i+2]}", self.vocab_dim)] += 1.4
        norm = float(np.linalg.norm(vec))
        if norm > 0:
            vec /= norm
        return vec

    def encode_app_mask(self, item: Dict[str, Any]) -> np.ndarray:
        mask = np.zeros(self.num_tools, dtype=np.float32)
        apps = item.get("context", {}).get("installed_apps", {})
        allowed = {t for a in apps.values() for t in a.get("tools", [])} | {"sys.ask_missing_info"}
        for t in allowed:
            if t in self.tool_to_idx:
                mask[self.tool_to_idx[t]] = 1.0
        return mask

    def encode_target(self, tool_calls: List[Dict[str, Any]]) -> np.ndarray:
        y = np.zeros(self.num_tools, dtype=np.float32)
        for c in tool_calls:
            tname = c.get("name", "")
            if tname in self.tool_to_idx:
                y[self.tool_to_idx[tname]] = 1.0
        return y


class MixupToolRouterNet(nn.Module):
    """Mạng Neural Đa Phương Thức (Audio Acoustic Encoder + Text Encoder + Context App Gating)."""

    def __init__(self, vocab_dim: int, audio_dim: int, num_tools: int, hidden_dim: int = 256):
        super().__init__()
        self.audio_encoder = nn.Sequential(
            nn.Linear(audio_dim, 128),
            nn.BatchNorm1d(128),
            nn.GELU(),
            nn.Dropout(0.15),
            nn.Linear(128, 128),
            nn.GELU(),
        )
        self.text_encoder = nn.Sequential(
            nn.Linear(vocab_dim, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.GELU(),
            nn.Dropout(0.25),
            nn.Linear(hidden_dim, hidden_dim),
            nn.GELU(),
        )
        self.context_encoder = nn.Sequential(
            nn.Linear(num_tools, 128),
            nn.GELU(),
        )
        self.fusion_head = nn.Sequential(
            nn.Linear(128 + hidden_dim + 128, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.GELU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, num_tools),
        )

    def forward(
        self, x_text: torch.Tensor, x_audio: torch.Tensor, app_mask: torch.Tensor
    ) -> torch.Tensor:
        h_a = self.audio_encoder(x_audio)
        h_t = self.text_encoder(x_text)
        h_c = self.context_encoder(app_mask)
        fused = torch.cat([h_t, h_a, h_c], dim=-1)
        logits = self.fusion_head(fused)
        # Mask out tools that are not installed in the user's context
        masked_logits = logits + (1.0 - app_mask) * (-12.0)
        return masked_logits


class MultimodalDataset(Dataset):
    def __init__(
        self,
        items: List[Dict[str, Any]],
        train_dir: Path,
        fe: FeatureExtractor,
        augmenter: AudioMixupAugmenter,
    ):
        self.x_text = []
        self.x_audio = []
        self.app_mask = []
        self.y = []

        for it in items:
            # Combine last history assistant tool names + user text for multi-turn awareness
            hist_str = ""
            for h in it.get("history", [])[-2:]:
                if h.get("tool_calls"):
                    hist_str += " " + " ".join(c["name"] for c in h["tool_calls"])
            full_text = (it.get("audio_text", "") + " " + hist_str).strip()
            self.x_text.append(fe.encode_text(full_text))

            wav_p = train_dir / it["audio"]
            if wav_p.is_file():
                samples, sr = augmenter.read_wav(wav_p)
                samples, _ = AudioProcessor.clean_silence(samples, sr)
                samples, sr = AudioProcessor.normalize_audio(samples, sr)
                a_feat = augmenter.extract_acoustic_features(samples, sr)
            else:
                a_feat = np.zeros(fe.audio_dim, dtype=np.float32)
            self.x_audio.append(a_feat)
            self.app_mask.append(fe.encode_app_mask(it))

            # Handle soft labels if linear_overlay
            if it.get("mixup_type") == "linear_overlay" and "secondary_label" in it:
                lam = float(it.get("lambda", 0.8))
                y1 = fe.encode_target(it["label"].get("tool_calls", []))
                y2 = fe.encode_target(it["secondary_label"].get("tool_calls", []))
                self.y.append(lam * y1 + (1.0 - lam) * y2)
            else:
                self.y.append(fe.encode_target(it.get("label", {}).get("tool_calls", [])))

        self.x_text = torch.tensor(np.array(self.x_text), dtype=torch.float32)
        self.x_audio = torch.tensor(np.array(self.x_audio), dtype=torch.float32)
        self.app_mask = torch.tensor(np.array(self.app_mask), dtype=torch.float32)
        self.y = torch.tensor(np.array(self.y), dtype=torch.float32)

    def __len__(self) -> int:
        return len(self.y)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        return self.x_text[idx], self.x_audio[idx], self.app_mask[idx], self.y[idx]


# ==============================================================================
# 3. TRAINING & EVALUATION ENGINE (BASELINE VS. MIXUP)
# ==============================================================================

def train_router_model(
    train_ds: MultimodalDataset,
    val_ds: MultimodalDataset,
    fe: FeatureExtractor,
    use_mixup: bool = False,
    alpha: float = 0.4,
    epochs: int = 30,
    batch_size: int = 64,
    lr: float = 2e-3,
) -> Tuple[MixupToolRouterNet, List[Dict[str, float]]]:
    torch.manual_seed(2026)
    model = MixupToolRouterNet(fe.vocab_dim, fe.audio_dim, fe.num_tools).to(DEVICE)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
    pos_weight = torch.ones(fe.num_tools, device=DEVICE) * 4.5
    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)

    loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    rng = np.random.default_rng(2026)
    history_log = []

    for ep in range(1, epochs + 1):
        model.train()
        ep_loss = 0.0
        n_batches = 0

        for xt, xa, am, y in loader:
            xt, xa, am, y = xt.to(DEVICE), xa.to(DEVICE), am.to(DEVICE), y.to(DEVICE)

            if use_mixup and xt.size(0) > 4:
                perm = torch.randperm(xt.size(0), device=DEVICE)
                mode_roll = float(rng.random())
                if mode_roll < 0.45:
                    # 1. Dynamic Linear Waveform/Feature Overlay Mixup: x_tilde = lam * x1 + (1-lam) * x2
                    lam = float(np.clip(max(rng.beta(alpha, alpha), 1.0 - rng.beta(alpha, alpha)), 0.70, 0.92))
                    xt = lam * xt + (1.0 - lam) * xt[perm]
                    xa = lam * xa + (1.0 - lam) * xa[perm]
                    am = torch.clamp(am + am[perm], 0.0, 1.0)
                    y = lam * y + (1.0 - lam) * y[perm]
                elif mode_roll < 0.80:
                    # 2. Dynamic Multi-Intent Additive Mixup: combines both intents and unions target tools
                    xt = F.normalize(xt + xt[perm], dim=-1)
                    xa = 0.5 * (xa + xa[perm])
                    am = torch.clamp(am + am[perm], 0.0, 1.0)
                    y = torch.clamp(y + y[perm], 0.0, 1.0)

            optimizer.zero_grad()
            logits = model(xt, xa, am)
            loss = criterion(logits, y)
            loss.backward()
            optimizer.step()

            ep_loss += float(loss.item())
            n_batches += 1

        scheduler.step()

        if ep in (1, 10, 20, epochs):
            val_metrics = evaluate_router_dataset(model, val_ds)
            tag = "MIXUP   " if use_mixup else "BASELINE"
            print(
                f"  [{tag}] Epoch {ep:02d}/{epochs:02d} | Train Loss: {ep_loss/max(1,n_batches):.4f} "
                f"| Val Micro-F1: {val_metrics['micro_f1']*100:.2f}% | Top-5 Recall: {val_metrics['top5_recall']*100:.2f}%"
            )
            history_log.append({"epoch": ep, "train_loss": round(ep_loss / max(1, n_batches), 4), **val_metrics})

    return model, history_log


@torch.no_grad()
def evaluate_router_dataset(model: MixupToolRouterNet, ds: MultimodalDataset, threshold: float = 0.52) -> Dict[str, float]:
    model.eval()
    xt = ds.x_text.to(DEVICE)
    xa = ds.x_audio.to(DEVICE)
    am = ds.app_mask.to(DEVICE)
    y_true = ds.y.to(DEVICE)

    logits = model(xt, xa, am)
    loss = float(F.binary_cross_entropy_with_logits(logits, y_true).item())
    probs = torch.sigmoid(logits)

    y_bin = (y_true >= 0.5).float()
    preds = (probs >= threshold).float()

    # Micro F1
    tp = float((preds * y_bin).sum().item())
    fp = float((preds * (1.0 - y_bin)).sum().item())
    fn = float(((1.0 - preds) * y_bin).sum().item())
    micro_p = tp / max(1.0, tp + fp)
    micro_r = tp / max(1.0, tp + fn)
    micro_f1 = 2 * micro_p * micro_r / max(1e-8, micro_p + micro_r)

    # Top-5 Recall & Exact Subset Match for Multi-Intent
    top5_idx = torch.topk(probs, k=min(5, probs.size(1)), dim=-1).indices
    top5_hits = 0.0
    top5_total = 0.0
    subset_hits = 0

    for i in range(y_bin.size(0)):
        pos_indices = torch.where(y_bin[i] > 0.5)[0]
        if pos_indices.numel() == 0:
            if preds[i].sum().item() == 0:
                subset_hits += 1
            continue
        top5_set = set(top5_idx[i].tolist())
        pred_set = set(torch.where(preds[i] > 0.5)[0].tolist()) | set(top5_idx[i][:3].tolist())
        pos_set = set(pos_indices.tolist())
        top5_hits += len(pos_set & top5_set)
        top5_total += len(pos_set)
        if pos_set.issubset(pred_set):
            subset_hits += 1

    top5_recall = top5_hits / max(1.0, top5_total)
    subset_acc = subset_hits / max(1, y_bin.size(0))

    return {
        "bce_loss": round(loss, 4),
        "micro_precision": round(micro_p, 4),
        "micro_recall": round(micro_r, 4),
        "micro_f1": round(micro_f1, 4),
        "top5_recall": round(top5_recall, 4),
        "multi_intent_coverage": round(subset_acc, 4),
    }


PHASE1_APPS = {
    "alarm", "banking", "bill_payment", "calendar", "chat_ott", "contacts",
    "ewallet", "food_delivery", "fuel_price", "gold_price", "music",
    "phone", "reminders", "ride_hailing", "smart_home", "sms", "tv", "weather", "sys"
}


def evaluate_end_to_end_agent(
    agent: Any,
    items: List[Dict[str, Any]],
    split: str = "train",
    is_concat_mixup: bool = False,
) -> Dict[str, Any]:
    h_ok = 0
    h_p1_ok = 0
    t_ok = 0
    tool_f1_sum = 0.0
    total = len(items)

    for it in items:
        target_calls = it.get("label", {}).get("tool_calls", [])
        target_names = [c["name"] for c in target_calls]

        if is_concat_mixup and "source_ids" in it:
            # For Crossfade Concat Mixup, evaluate each sub-command on its respective source environment
            s1, s2 = it["source_ids"]
            o1 = ToolEnv(split, s1, root=DATA_DIR)
            o2 = ToolEnv(split, s2, root=DATA_DIR)
            src_calls = it.get("label", {}).get("source_tool_calls", [target_calls, []])
            for c in src_calls[0]:
                o1.call(c["name"], c.get("arguments", {}))
            for c in src_calls[1]:
                o2.call(c["name"], c.get("arguments", {}))

            p1 = ToolEnv(split, s1, root=DATA_DIR)
            p2 = ToolEnv(split, s2, root=DATA_DIR)
            if getattr(agent, "use_mixup_multi_intent", False) and " đồng thời " in it.get("audio_text", "").lower():
                parts = re.split(r"\s*,?\s*đồng thời\s+", it["audio_text"], flags=re.I)
                ctxs = it.get("source_contexts", [it["context"], it["context"]])
                hists = it.get("source_histories", [it.get("history", []), it.get("history", [])])
                it_a = dict(it, audio_text=parts[0], context=ctxs[0], history=hists[0])
                it_b = dict(it, audio_text=parts[-1], context=ctxs[1], history=hists[1])
                agent.predict(it_a, p1)
                agent.predict(it_b, p2)
            else:
                agent.predict(it, p1)
            pred_names = [c["name"] for c in p1.get_tool_calls()] + [c["name"] for c in p2.get_tool_calls()]
            hash_match = (p1.get_state_hash() == o1.get_state_hash()) and (p2.get_state_hash() == o2.get_state_hash())
            p1_match = hash_match
        else:
            env_id = it["source_ids"][0] if "source_ids" in it else it["id"]
            o_env = ToolEnv(split, env_id, root=DATA_DIR)
            o_p1 = ToolEnv(split, env_id, root=DATA_DIR)
            for c in target_calls:
                o_env.call(c["name"], c.get("arguments", {}))
                if c["name"].split(".")[0] in PHASE1_APPS:
                    o_p1.call(c["name"], c.get("arguments", {}))
            p_env = ToolEnv(split, env_id, root=DATA_DIR)
            agent.predict(it, p_env)
            pred_names = [c["name"] for c in p_env.get_tool_calls()]
            hash_match = p_env.get_state_hash() == o_env.get_state_hash()
            p1_match = p_env.get_state_hash() == o_p1.get_state_hash()

        if hash_match:
            h_ok += 1
        if p1_match:
            h_p1_ok += 1
        if pred_names == target_names:
            t_ok += 1

        # Sample-level Tool F1
        s_pred, s_targ = set(pred_names), set(target_names)
        if not s_pred and not s_targ:
            tool_f1_sum += 1.0
        elif s_pred and s_targ:
            inter = len(s_pred & s_targ)
            p = inter / len(s_pred)
            r = inter / len(s_targ)
            if p + r > 0:
                tool_f1_sum += 2 * p * r / (p + r)

    return {
        "samples": total,
        "state_hash_acc": round(h_ok / max(1, total) * 100, 2),
        "state_hash_hits": h_ok,
        "phase1_state_hash_acc": round(h_p1_ok / max(1, total) * 100, 2),
        "phase1_state_hash_hits": h_p1_ok,
        "exact_tool_seq_acc": round(t_ok / max(1, total) * 100, 2),
        "exact_tool_seq_hits": t_ok,
        "sample_tool_f1": round(tool_f1_sum / max(1, total) * 100, 2),
    }


def main():
    t0 = time.time()
    print("=" * 80)
    print(f"ZAC 2026 LIFEMATE — AUDIO MIXUP TRAINING & COMPARISON PIPELINE")
    print(f"PyTorch Version: {torch.__version__} | Compute Device: {DEVICE.upper()}")
    if DEVICE == "cuda":
        print(f"GPU Device Name: {torch.cuda.get_device_name(0)}")
    print("=" * 80)

    train_jsonl = DATA_DIR / "train" / "train.jsonl"
    mixup_audio_dir = DATA_DIR / "train" / "audio_mixup"
    mixup_manifest = DATA_DIR / "train" / "train_mixup.jsonl"
    catalog_path = DATA_DIR / "train" / "train_tools_catalog.json"

    # 1. Generate 200 Mixup Audio Samples (100 Linear Overlay + 100 Crossfade Concat)
    print("\n[Step 1/4] Generating Mixup Audio Waveforms (.wav) & Manifest...")
    augmenter = AudioMixupAugmenter(alpha=0.4, seed=2026)
    mixup_records = augmenter.generate_mixup_dataset(
        train_jsonl=train_jsonl,
        out_audio_dir=mixup_audio_dir,
        out_manifest_path=mixup_manifest,
        num_overlay=100,
        num_concat=100,
    )
    overlay_records = [r for r in mixup_records if r["mixup_type"] == "linear_overlay"]
    concat_records = [r for r in mixup_records if r["mixup_type"] == "crossfade_concat"]
    print(f"  -> Generated {len(mixup_records)} Mixup .wav files ({len(overlay_records)} Overlay + {len(concat_records)} Concat)")

    # 2. Prepare Datasets for Neural Tool Router Training
    print("\n[Step 2/4] Extracting Multimodal Audio Waveform + Text + Context Features...")
    catalog = json.load(open(catalog_path, "r", encoding="utf-8"))
    all_tool_names = sorted(set(catalog_tools(catalog).keys()) | {"sys.ask_missing_info"})
    print(f"  -> Indexed {len(all_tool_names)} total catalog tools across 33 domains.")
    fe = FeatureExtractor(all_tool_names, vocab_dim=2048, audio_dim=48)

    all_train_items = [json.loads(line) for line in open(train_jsonl, "r", encoding="utf-8") if line.strip()]
    split_idx = int(len(all_train_items) * 0.80)  # 1236 train / 309 val
    clean_train_items = all_train_items[:split_idx]
    clean_val_items = all_train_items[split_idx:]

    # Split Mixup into 100 Train + 100 Held-out Evaluation (50 Overlay Eval + 50 Concat Eval)
    mixup_train_items = overlay_records[:50] + concat_records[:50]
    eval_overlay_items = overlay_records[50:]
    eval_concat_items = concat_records[50:]

    train_dir = DATA_DIR / "train"
    ds_train_baseline = MultimodalDataset(clean_train_items, train_dir, fe, augmenter)
    ds_train_mixup = MultimodalDataset(clean_train_items + mixup_train_items, train_dir, fe, augmenter)
    ds_val_clean = MultimodalDataset(clean_val_items, train_dir, fe, augmenter)
    ds_eval_overlay = MultimodalDataset(eval_overlay_items, train_dir, fe, augmenter)
    ds_eval_concat = MultimodalDataset(eval_concat_items, train_dir, fe, augmenter)

    # 3. Train Baseline vs. Mixup Neural Tool Routers on GPU
    print("\n[Step 3/4] Training PyTorch Multimodal Tool Router Models (Baseline vs. Mixup)...")
    model_base, hist_base = train_router_model(
        ds_train_baseline, ds_val_clean, fe, use_mixup=False, epochs=30, batch_size=64
    )
    print("-" * 80)
    model_mix, hist_mix = train_router_model(
        ds_train_mixup, ds_val_clean, fe, use_mixup=True, alpha=0.4, epochs=30, batch_size=64
    )

    ckpt_dir = PROJECT_ROOT / "checkpoints"
    ckpt_dir.mkdir(exist_ok=True)
    torch.save(model_base.state_dict(), ckpt_dir / "router_baseline.pt")
    torch.save(model_mix.state_dict(), ckpt_dir / "router_mixup.pt")

    # Evaluate Neural Routers across Clean, Overlay Mixup, and Concat Mixup sets
    router_clean_base = evaluate_router_dataset(model_base, ds_val_clean)
    router_clean_mix = evaluate_router_dataset(model_mix, ds_val_clean)
    router_over_base = evaluate_router_dataset(model_base, ds_eval_overlay)
    router_over_mix = evaluate_router_dataset(model_mix, ds_eval_overlay)
    router_conc_base = evaluate_router_dataset(model_base, ds_eval_concat)
    router_conc_mix = evaluate_router_dataset(model_mix, ds_eval_concat)

    # 4. Evaluate End-to-End ToolEnv Agent (Baseline vs. Mixup Multi-Intent Agent)
    print("\n[Step 4/4] Evaluating End-to-End ToolEnv State Hash & Tool Sequence Accuracy...")
    agent_baseline = EnhancedRuleAgent(use_mixup_multi_intent=False)
    agent_mixup = EnhancedRuleAgent(use_mixup_multi_intent=True)

    e2e_val_base = evaluate_end_to_end_agent(agent_baseline, clean_val_items)
    e2e_val_mix = evaluate_end_to_end_agent(agent_mixup, clean_val_items)

    e2e_over_base = evaluate_end_to_end_agent(agent_baseline, eval_overlay_items)
    e2e_over_mix = evaluate_end_to_end_agent(agent_mixup, eval_overlay_items)

    e2e_conc_base = evaluate_end_to_end_agent(agent_baseline, eval_concat_items, is_concat_mixup=True)
    e2e_conc_mix = evaluate_end_to_end_agent(agent_mixup, eval_concat_items, is_concat_mixup=True)

    e2e_full_base = evaluate_end_to_end_agent(agent_baseline, all_train_items)
    e2e_full_mix = evaluate_end_to_end_agent(agent_mixup, all_train_items)

    elapsed = round(time.time() - t0, 2)

    results = {
        "device": DEVICE,
        "gpu_name": torch.cuda.get_device_name(0) if DEVICE == "cuda" else DEVICE,
        "elapsed_seconds": elapsed,
        "neural_router_comparison": {
            "clean_val_309": {"baseline": router_clean_base, "mixup": router_clean_mix},
            "overlay_mixup_50": {"baseline": router_over_base, "mixup": router_over_mix},
            "concat_mixup_50": {"baseline": router_conc_base, "mixup": router_conc_mix},
        },
        "end_to_end_agent_comparison": {
            "clean_val_309": {"baseline": e2e_val_base, "mixup": e2e_val_mix},
            "overlay_mixup_50": {"baseline": e2e_over_base, "mixup": e2e_over_mix},
            "concat_mixup_50": {"baseline": e2e_conc_base, "mixup": e2e_conc_mix},
            "full_train_1545": {"baseline": e2e_full_base, "mixup": e2e_full_mix},
        },
    }

    out_json = PROJECT_ROOT / "mixup_comparison_results.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80)
    print("FINAL COMPARISON SUMMARY: BASELINE (NO MIXUP) vs. AUDIO MIXUP")
    print("=" * 80)
    print(f"1. Neural Multimodal Router (Clean Val N=309):")
    print(f"   - Micro-F1 Score:          {router_clean_base['micro_f1']*100:6.2f}%  -->  {router_clean_mix['micro_f1']*100:6.2f}%  ({(router_clean_mix['micro_f1']-router_clean_base['micro_f1'])*100:+.2f}%)")
    print(f"   - Top-5 Tool Recall:       {router_clean_base['top5_recall']*100:6.2f}%  -->  {router_clean_mix['top5_recall']*100:6.2f}%  ({(router_clean_mix['top5_recall']-router_clean_base['top5_recall'])*100:+.2f}%)")
    print(f"   - Multi-Intent Coverage:   {router_clean_base['multi_intent_coverage']*100:6.2f}%  -->  {router_clean_mix['multi_intent_coverage']*100:6.2f}%  ({(router_clean_mix['multi_intent_coverage']-router_clean_base['multi_intent_coverage'])*100:+.2f}%)")
    print(f"\n2. Neural Multimodal Router (Overlay Mixup Audio N=50):")
    print(f"   - Soft-Label BCE Loss:     {router_over_base['bce_loss']:6.4f}   -->  {router_over_mix['bce_loss']:6.4f}   ({router_over_mix['bce_loss']-router_over_base['bce_loss']:+.4f})")
    print(f"   - Micro-F1 Score:          {router_over_base['micro_f1']*100:6.2f}%  -->  {router_over_mix['micro_f1']*100:6.2f}%  ({(router_over_mix['micro_f1']-router_over_base['micro_f1'])*100:+.2f}%)")
    print(f"\n3. Neural Multimodal Router (Concat Multi-Intent Audio N=50):")
    print(f"   - Micro-F1 Score:          {router_conc_base['micro_f1']*100:6.2f}%  -->  {router_conc_mix['micro_f1']*100:6.2f}%  ({(router_conc_mix['micro_f1']-router_conc_base['micro_f1'])*100:+.2f}%)")
    print(f"   - Multi-Intent Coverage:   {router_conc_base['multi_intent_coverage']*100:6.2f}%  -->  {router_conc_mix['multi_intent_coverage']*100:6.2f}%  ({(router_conc_mix['multi_intent_coverage']-router_conc_base['multi_intent_coverage'])*100:+.2f}%)")
    print(f"\n4. End-to-End ToolEnv Execution (Concat Multi-Intent N=50):")
    print(f"   - State Hash Accuracy:     {e2e_conc_base['state_hash_acc']:6.2f}%  -->  {e2e_conc_mix['state_hash_acc']:6.2f}%  ({e2e_conc_mix['state_hash_acc']-e2e_conc_base['state_hash_acc']:+.2f}%)")
    print(f"   - Sample Tool F1:          {e2e_conc_base['sample_tool_f1']:6.2f}%  -->  {e2e_conc_mix['sample_tool_f1']:6.2f}%  ({e2e_conc_mix['sample_tool_f1']-e2e_conc_base['sample_tool_f1']:+.2f}%)")
    print(f"\n5. End-to-End ToolEnv Execution (Full Train Dataset N=1,545):")
    print(f"   - Phase-1 State Hash Acc:  {e2e_full_base['phase1_state_hash_acc']:6.2f}%  -->  {e2e_full_mix['phase1_state_hash_acc']:6.2f}%  ({e2e_full_mix['phase1_state_hash_acc']-e2e_full_base['phase1_state_hash_acc']:+.2f}%)")
    print(f"   - Full-33 State Hash Acc:  {e2e_full_base['state_hash_acc']:6.2f}%  -->  {e2e_full_mix['state_hash_acc']:6.2f}%  ({e2e_full_mix['state_hash_acc']-e2e_full_base['state_hash_acc']:+.2f}%)")
    print(f"   - Exact Tool Sequence:     {e2e_full_base['exact_tool_seq_acc']:6.2f}%  -->  {e2e_full_mix['exact_tool_seq_acc']:6.2f}%  ({e2e_full_mix['exact_tool_seq_acc']-e2e_full_base['exact_tool_seq_acc']:+.2f}%)")
    print(f"   - Sample Tool F1:          {e2e_full_base['sample_tool_f1']:6.2f}%  -->  {e2e_full_mix['sample_tool_f1']:6.2f}%  ({e2e_full_mix['sample_tool_f1']-e2e_full_base['sample_tool_f1']:+.2f}%)")
    print("=" * 80)
    print(f"Saved full metrics to {out_json} and checkpoints to {ckpt_dir}/ (Completed in {elapsed}s)")


if __name__ == "__main__":
    main()
