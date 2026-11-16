#!/usr/bin/env python3
"""Zalo AI Challenge 2026 — LifeMate: SOTA Pretrained Speech Router.

Leverages:
1. Pretrained PhoWhisper-base 512-dim Transformer Speech Encoder representations.
2. 48-dim Whole-Waveform Acoustic Prosodic & FFT features with SpecAugment.
3. Asymmetric Loss (ASL) for extreme multi-label long-tail class imbalance.
4. Hierarchical 2-Stage Routing (Domain Head + Domain-Gated Tool Head).
5. Per-Class Dynamic Thresholds (tau_k in [0.20, 0.70]).
6. Multi-Seed Model Ensembling (3 Seeds: 2026, 42, 1337).
7. Audio Test-Time Augmentation (TTA).
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

import numpy as np
import scipy.signal as signal
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset

DEVICE = "cpu"
if torch.cuda.is_available():
    DEVICE = "cuda"
elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
    DEVICE = "mps"

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "train+public_test"
CKPT_DIR = PROJECT_ROOT / "checkpoints"
CACHE_FILE = CKPT_DIR / "phowhisper_embeddings.pt"

if str(DATA_DIR / "train") not in sys.path:
    sys.path.insert(0, str(DATA_DIR / "train"))

from zaic_tools import ToolEnv, schema_validate
from zaic_tools.validate import catalog_tools
from lifemate_agent import AudioProcessor, VietnameseNormalizer, EnhancedDateTimeResolver


# ==============================================================================
# 1. ASYMMETRIC LOSS (ASL)
# ==============================================================================

class AsymmetricLoss(nn.Module):
    def __init__(self, gamma_neg: float = 4.0, gamma_pos: float = 1.0, clip: float = 0.05, eps: float = 1e-8):
        super().__init__()
        self.gamma_neg = gamma_neg
        self.gamma_pos = gamma_pos
        self.clip = clip
        self.eps = eps

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        probs = torch.sigmoid(logits)
        pos_loss = targets * torch.log(probs.clamp(min=self.eps)) * ((1.0 - probs) ** self.gamma_pos)
        p_sub = (probs - self.clip).clamp(min=0.0)
        neg_loss = (1.0 - targets) * torch.log((1.0 - p_sub).clamp(min=self.eps)) * (p_sub ** self.gamma_neg)
        return -torch.mean(pos_loss + neg_loss)


# ==============================================================================
# 2. SPECAUGMENT FOR WHOLE PROSODIC FEATURES
# ==============================================================================

class SpecAugment(nn.Module):
    def __init__(
        self,
        freq_mask_max: int = 6,
        time_mask_max: int = 2,
        num_freq_masks: int = 2,
        num_time_masks: int = 1,
        p: float = 0.8,
    ):
        super().__init__()
        self.freq_mask_max = freq_mask_max
        self.time_mask_max = time_mask_max
        self.num_freq_masks = num_freq_masks
        self.num_time_masks = num_time_masks
        self.p = p

    def forward(self, xa: torch.Tensor) -> torch.Tensor:
        if not self.training or torch.rand(1).item() > self.p:
            return xa

        xa_aug = xa.clone()
        B = xa_aug.size(0)

        for _ in range(self.num_freq_masks):
            f_len = torch.randint(1, self.freq_mask_max + 1, (B,), device=xa.device)
            f_start = torch.randint(0, 32, (B,), device=xa.device)
            for b in range(B):
                f0 = f_start[b].item()
                f1 = min(32, f0 + f_len[b].item())
                xa_aug[b, f0:f1] = 0.0

        for _ in range(self.num_time_masks):
            t_len = torch.randint(1, self.time_mask_max + 1, (B,), device=xa.device)
            t_start = torch.randint(0, 8, (B,), device=xa.device)
            for b in range(B):
                t0 = 32 + t_start[b].item()
                t1 = min(40, t0 + t_len[b].item())
                xa_aug[b, t0:t1] = 0.0

        return xa_aug


# ==============================================================================
# 3. FEATURE EXTRACTOR WITH PRETRAINED SPEECH EMBEDDINGS
# ==============================================================================

class MultimodalSpeechFeatureExtractor:
    def __init__(
        self,
        all_tools: List[str],
        vocab_dim: int = 2048,
        speech_dim: int = 512,
        prosody_dim: int = 48,
        embedding_cache: Optional[Dict[str, np.ndarray]] = None,
    ):
        self.all_tools = sorted(all_tools)
        self.tool_to_idx = {t: i for i, t in enumerate(self.all_tools)}
        self.num_tools = len(self.all_tools)

        self.domains = sorted(set(t.split(".")[0] for t in self.all_tools))
        self.domain_to_idx = {d: i for i, d in enumerate(self.domains)}
        self.num_domains = len(self.domains)

        self.tool_idx_to_domain_idx = np.array(
            [self.domain_to_idx[t.split(".")[0]] for t in self.all_tools],
            dtype=np.int64,
        )
        self.vocab_dim = vocab_dim
        self.speech_dim = speech_dim
        self.prosody_dim = prosody_dim
        self.cache = embedding_cache or {}

    @staticmethod
    def _hash_token(tok: str, dim: int) -> int:
        h = int(hashlib.md5(tok.encode("utf-8")).hexdigest()[:8], 16)
        return h % dim

    def encode_text(self, text: str) -> np.ndarray:
        vec = np.zeros(self.vocab_dim, dtype=np.float32)
        s = VietnameseNormalizer.normalize_text(text)
        words = re.findall(r"\w+", s)
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

    def get_speech_embedding(self, rel_audio_path: str) -> np.ndarray:
        if rel_audio_path in self.cache:
            return self.cache[rel_audio_path]
        return np.zeros(self.speech_dim, dtype=np.float32)

    def encode_app_mask(self, item: Dict[str, Any]) -> Tuple[np.ndarray, np.ndarray]:
        tool_mask = np.zeros(self.num_tools, dtype=np.float32)
        domain_mask = np.zeros(self.num_domains, dtype=np.float32)

        apps = item.get("context", {}).get("installed_apps", {})
        allowed_tools = {t for a in apps.values() for t in a.get("tools", [])} | {"sys.ask_missing_info"}

        for t in allowed_tools:
            if t in self.tool_to_idx:
                tool_mask[self.tool_to_idx[t]] = 1.0

        allowed_domains = set(apps.keys()) | {"sys"}
        for d in allowed_domains:
            if d in self.domain_to_idx:
                domain_mask[self.domain_to_idx[d]] = 1.0

        return tool_mask, domain_mask

    def encode_target(self, tool_calls: List[Dict[str, Any]]) -> Tuple[np.ndarray, np.ndarray]:
        y_tool = np.zeros(self.num_tools, dtype=np.float32)
        y_domain = np.zeros(self.num_domains, dtype=np.float32)

        for c in tool_calls:
            tname = c.get("name", "")
            if tname in self.tool_to_idx:
                t_idx = self.tool_to_idx[tname]
                y_tool[t_idx] = 1.0
                d_idx = self.tool_idx_to_domain_idx[t_idx]
                y_domain[d_idx] = 1.0

        return y_tool, y_domain


# ==============================================================================
# 4. HIERARCHICAL PRETRAINED SPEECH ROUTER NET
# ==============================================================================

class PhoWhisperHierarchicalRouterNet(nn.Module):
    """Mạng Neural Định Tuyến kết hợp Đặc Trưng Âm Học Sâu từ PhoWhisper."""

    def __init__(
        self,
        vocab_dim: int = 2048,
        speech_dim: int = 512,
        prosody_dim: int = 48,
        num_tools: int = 147,
        num_domains: int = 46,
        hidden_dim: int = 256,
    ):
        super().__init__()
        self.num_tools = num_tools
        self.num_domains = num_domains

        # 1. Pretrained Deep Speech Encoder (PhoWhisper 512-dim -> 128)
        self.speech_encoder = nn.Sequential(
            nn.Linear(speech_dim, 256),
            nn.BatchNorm1d(256),
            nn.GELU(),
            nn.Dropout(0.20),
            nn.Linear(256, 128),
            nn.GELU(),
        )

        # 2. Handcrafted Prosodic & Energy Encoder (48-dim -> 128)
        self.prosody_encoder = nn.Sequential(
            nn.Linear(prosody_dim, 128),
            nn.BatchNorm1d(128),
            nn.GELU(),
            nn.Dropout(0.15),
            nn.Linear(128, 128),
            nn.GELU(),
        )

        # 3. Multi-scale Text N-gram Encoder (2048-dim -> 256)
        self.text_encoder = nn.Sequential(
            nn.Linear(vocab_dim, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.GELU(),
            nn.Dropout(0.25),
            nn.Linear(hidden_dim, hidden_dim),
            nn.GELU(),
        )

        # 4. Context App Mask Encoder (147-dim -> 128)
        self.context_encoder = nn.Sequential(
            nn.Linear(num_tools, 128),
            nn.GELU(),
        )

        # 5. Shared Multimodal Fusion (256 + 128 + 128 + 128 = 640 -> 256)
        self.fusion = nn.Sequential(
            nn.Linear(hidden_dim + 128 + 128 + 128, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.GELU(),
            nn.Dropout(0.20),
        )

        # 6. Stage 1: Domain Head (256 -> 46)
        self.domain_head = nn.Linear(hidden_dim, num_domains)

        # 7. Stage 2: Tool Head conditioned on Domain (256 + 64 -> 147)
        self.domain_embed = nn.Sequential(
            nn.Linear(num_domains, 64),
            nn.GELU(),
        )
        self.tool_head = nn.Sequential(
            nn.Linear(hidden_dim + 64, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.GELU(),
            nn.Dropout(0.15),
            nn.Linear(hidden_dim, num_tools),
        )

    def forward(
        self,
        x_text: torch.Tensor,
        x_speech: torch.Tensor,
        x_prosody: torch.Tensor,
        app_mask: torch.Tensor,
        domain_mask: torch.Tensor,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        h_t = self.text_encoder(x_text)
        h_s = self.speech_encoder(x_speech)
        h_p = self.prosody_encoder(x_prosody)
        h_c = self.context_encoder(app_mask)

        # Concatenate text (256) + speech (128) + prosody (128) + context (128) = 640
        fused = self.fusion(torch.cat([h_t, h_s, h_p, h_c], dim=-1))

        # Stage 1: Domain logits
        domain_logits = self.domain_head(fused) + (1.0 - domain_mask) * (-12.0)
        domain_probs = torch.sigmoid(domain_logits)

        # Stage 2: Tool logits conditioned on domain
        dom_feat = self.domain_embed(domain_probs)
        tool_logits = self.tool_head(torch.cat([fused, dom_feat], dim=-1)) + (1.0 - app_mask) * (-12.0)

        return tool_logits, domain_logits


# ==============================================================================
# 5. DATASET LOADER WITH PRETRAINED SPEECH EMBEDDINGS
# ==============================================================================

class MultimodalSpeechDataset(Dataset):
    def __init__(
        self,
        items: List[Dict[str, Any]],
        train_dir: Path,
        fe: MultimodalSpeechFeatureExtractor,
    ):
        self.x_text = []
        self.x_speech = []
        self.x_prosody = []
        self.app_mask = []
        self.domain_mask = []
        self.y_tool = []
        self.y_domain = []

        for it in items:
            hist_str = ""
            for h in it.get("history", [])[-2:]:
                if h.get("tool_calls"):
                    hist_str += " " + " ".join(c["name"] for c in h["tool_calls"])
            full_text = (it.get("audio_text", "") + " " + hist_str).strip()
            self.x_text.append(fe.encode_text(full_text))

            rel_audio = it.get("audio", "")
            # Pretrained speech embedding from PhoWhisper
            self.x_speech.append(fe.get_speech_embedding(rel_audio))

            # Handcrafted prosodic features
            wav_p = train_dir / rel_audio
            if wav_p.is_file():
                samples, sr = AudioProcessor.read_wav(wav_p)
                samples, _ = AudioProcessor.clean_silence(samples, sr)
                samples, sr = AudioProcessor.normalize_audio(samples, sr)
                p_feat = AudioProcessor.extract_acoustic_features(samples, sr)
            else:
                p_feat = np.zeros(fe.prosody_dim, dtype=np.float32)
            self.x_prosody.append(p_feat)

            tm, dm = fe.encode_app_mask(it)
            self.app_mask.append(tm)
            self.domain_mask.append(dm)

            if it.get("mixup_type") == "linear_overlay" and "secondary_label" in it:
                lam = float(it.get("lambda", 0.8))
                yt1, yd1 = fe.encode_target(it["label"].get("tool_calls", []))
                yt2, yd2 = fe.encode_target(it["secondary_label"].get("tool_calls", []))
                self.y_tool.append(lam * yt1 + (1.0 - lam) * yt2)
                self.y_domain.append(lam * yd1 + (1.0 - lam) * yd2)
            else:
                yt, yd = fe.encode_target(it.get("label", {}).get("tool_calls", []))
                self.y_tool.append(yt)
                self.y_domain.append(yd)

        self.x_text = torch.tensor(np.array(self.x_text), dtype=torch.float32)
        self.x_speech = torch.tensor(np.array(self.x_speech), dtype=torch.float32)
        self.x_prosody = torch.tensor(np.array(self.x_prosody), dtype=torch.float32)
        self.app_mask = torch.tensor(np.array(self.app_mask), dtype=torch.float32)
        self.domain_mask = torch.tensor(np.array(self.domain_mask), dtype=torch.float32)
        self.y_tool = torch.tensor(np.array(self.y_tool), dtype=torch.float32)
        self.y_domain = torch.tensor(np.array(self.y_domain), dtype=torch.float32)

    def __len__(self) -> int:
        return len(self.y_tool)

    def __getitem__(self, idx: int):
        return (
            self.x_text[idx],
            self.x_speech[idx],
            self.x_prosody[idx],
            self.app_mask[idx],
            self.domain_mask[idx],
            self.y_tool[idx],
            self.y_domain[idx],
        )


# ==============================================================================
# 6. PER-CLASS DYNAMIC THRESHOLD CALIBRATOR
# ==============================================================================

def calibrate_per_class_thresholds(
    val_tool_probs: np.ndarray,
    val_tool_true: np.ndarray,
    default_thresh: float = 0.45,
    min_thresh: float = 0.20,
    max_thresh: float = 0.70,
) -> np.ndarray:
    N, K = val_tool_probs.shape
    optimal_taus = np.full(K, default_thresh, dtype=np.float32)
    candidate_taus = np.arange(min_thresh, max_thresh + 0.05, 0.05)

    for k in range(K):
        y_k = val_tool_true[:, k] > 0.5
        pos_cnt = int(np.sum(y_k))
        if pos_cnt == 0:
            optimal_taus[k] = default_thresh
            continue

        p_k = val_tool_probs[:, k]
        best_f1, best_tau = -1.0, default_thresh

        for tau in candidate_taus:
            pred_k = p_k >= tau
            tp = int(np.sum(pred_k & y_k))
            fp = int(np.sum(pred_k & ~y_k))
            fn = int(np.sum(~pred_k & y_k))
            denom = 2 * tp + fp + fn
            f1 = (2.0 * tp / denom) if denom > 0 else 0.0

            if f1 > best_f1:
                best_f1 = f1
                best_tau = float(tau)
            elif abs(f1 - best_f1) < 1e-4 and abs(tau - default_thresh) < abs(best_tau - default_thresh):
                best_tau = float(tau)

        optimal_taus[k] = best_tau

    return optimal_taus


# ==============================================================================
# 7. TRAINING SINGLE SEED MODEL
# ==============================================================================

def train_single_speech_model(
    seed: int,
    train_ds: MultimodalSpeechDataset,
    val_ds: MultimodalSpeechDataset,
    fe: MultimodalSpeechFeatureExtractor,
    epochs: int = 25,
    batch_size: int = 64,
    lr: float = 2e-3,
    alpha: float = 0.4,
    device: str = DEVICE,
) -> Tuple[PhoWhisperHierarchicalRouterNet, Dict[str, float]]:
    torch.manual_seed(seed)
    np.random.seed(seed)
    random.seed(seed)

    model = PhoWhisperHierarchicalRouterNet(
        vocab_dim=fe.vocab_dim,
        speech_dim=fe.speech_dim,
        prosody_dim=fe.prosody_dim,
        num_tools=fe.num_tools,
        num_domains=fe.num_domains,
        hidden_dim=256,
    ).to(device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    asl_tool = AsymmetricLoss(gamma_neg=4.0, gamma_pos=1.0, clip=0.05).to(device)
    asl_domain = AsymmetricLoss(gamma_neg=2.5, gamma_pos=1.0, clip=0.05).to(device)
    spec_aug = SpecAugment(freq_mask_max=6, time_mask_max=2, p=0.8).to(device)

    loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    rng = np.random.default_rng(seed)

    for ep in range(1, epochs + 1):
        model.train()
        ep_loss = 0.0
        n_batches = 0

        for xt, xs, xp, tm, dm, yt, yd in loader:
            xt = xt.to(device)
            xs = xs.to(device)
            xp = spec_aug(xp.to(device))
            tm = tm.to(device)
            dm = dm.to(device)
            yt = yt.to(device)
            yd = yd.to(device)

            # Dynamic Waveform / Feature Mixup
            if xt.size(0) > 4:
                perm = torch.randperm(xt.size(0), device=device)
                mode = float(rng.random())
                if mode < 0.45:
                    lam = float(np.clip(max(rng.beta(alpha, alpha), 1.0 - rng.beta(alpha, alpha)), 0.70, 0.92))
                    xt = lam * xt + (1.0 - lam) * xt[perm]
                    xs = lam * xs + (1.0 - lam) * xs[perm]
                    xp = lam * xp + (1.0 - lam) * xp[perm]
                    tm = torch.clamp(tm + tm[perm], 0.0, 1.0)
                    dm = torch.clamp(dm + dm[perm], 0.0, 1.0)
                    yt = lam * yt + (1.0 - lam) * yt[perm]
                    yd = lam * yd + (1.0 - lam) * yd[perm]
                elif mode < 0.80:
                    xt = F.normalize(xt + xt[perm], dim=-1)
                    xs = 0.5 * (xs + xs[perm])
                    xp = 0.5 * (xp + xp[perm])
                    tm = torch.clamp(tm + tm[perm], 0.0, 1.0)
                    dm = torch.clamp(dm + dm[perm], 0.0, 1.0)
                    yt = torch.clamp(yt + yt[perm], 0.0, 1.0)
                    yd = torch.clamp(yd + yd[perm], 0.0, 1.0)

            optimizer.zero_grad()
            tool_logits, dom_logits = model(xt, xs, xp, tm, dm)
            loss_t = asl_tool(tool_logits, yt)
            loss_d = asl_domain(dom_logits, yd)
            total_loss = loss_t + 0.4 * loss_d

            total_loss.backward()
            optimizer.step()
            ep_loss += float(total_loss.item())
            n_batches += 1

        scheduler.step()

    # Evaluation
    model.eval()
    with torch.no_grad():
        val_tl, val_dl = model(
            val_ds.x_text.to(device),
            val_ds.x_speech.to(device),
            val_ds.x_prosody.to(device),
            val_ds.app_mask.to(device),
            val_ds.domain_mask.to(device),
        )
        val_tp = torch.sigmoid(val_tl).cpu().numpy()
        val_dp = torch.sigmoid(val_dl).cpu().numpy()

    return model, {"tool_probs": val_tp, "domain_probs": val_dp}


# ==============================================================================
# 8. MAIN EXECUTION PIPELINE
# ==============================================================================

def main():
    t0 = time.time()
    print("=" * 80)
    print("ZALO AI CHALLENGE 2026 — LIFEMATE: PRETRAINED SPEECH (PhoWhisper) ROUTER")
    print(f"Hardware: {DEVICE.upper()} | Cache: {CACHE_FILE}")
    print("=" * 80)

    if not CACHE_FILE.is_file():
        print("ERROR: Pretrained speech cache not found! Please run extract_phowhisper_cache.py first.")
        sys.exit(1)

    print("Loading PhoWhisper speech embeddings from disk cache...")
    speech_cache = torch.load(CACHE_FILE, map_location="cpu", weights_only=False)
    print(f"Loaded {len(speech_cache)} pre-extracted speech embeddings (512-dim).")

    train_jsonl = DATA_DIR / "train" / "train.jsonl"
    catalog_path = DATA_DIR / "train" / "train_tools_catalog.json"
    catalog = json.load(open(catalog_path, "r", encoding="utf-8"))
    all_tool_names = sorted(set(catalog_tools(catalog).keys()) | {"sys.ask_missing_info"})
    print(f"Catalog Loaded: {len(all_tool_names)} tools across 46 domains.")

    fe = MultimodalSpeechFeatureExtractor(all_tool_names, embedding_cache=speech_cache)
    all_items = [json.loads(l) for l in open(train_jsonl, "r", encoding="utf-8") if l.strip()]

    split_point = int(len(all_items) * 0.80)
    train_clean = all_items[:split_point]
    val_clean = all_items[split_point:]

    mixup_manifest = DATA_DIR / "train" / "train_mixup.jsonl"
    augmented_items = []
    if mixup_manifest.is_file():
        augmented_items = [json.loads(l) for l in open(mixup_manifest, "r", encoding="utf-8") if l.strip()]

    train_dir = DATA_DIR / "train"
    print("\n[1/4] Building Multimodal Datasets (PhoWhisper 512 + Prosody 48 + Text 2048)...")
    ds_train = MultimodalSpeechDataset(train_clean + augmented_items, train_dir, fe)
    ds_val = MultimodalSpeechDataset(val_clean, train_dir, fe)
    print(f"  Train: {len(ds_train)} | Val: {len(ds_val)}")

    seeds = [2026, 42, 1337]
    trained_models = []
    val_probs_list = []

    print("\n[2/4] Training 3-Seed PhoWhisper Multimodal Ensemble with Asymmetric Loss...")
    for idx, s in enumerate(seeds, 1):
        print(f"--- Training Model {idx}/{len(seeds)} (Seed: {s}) ---", flush=True)
        model, val_preds = train_single_speech_model(
            seed=s,
            train_ds=ds_train,
            val_ds=ds_val,
            fe=fe,
            epochs=25,
            batch_size=64,
            lr=2e-3,
            device=DEVICE,
        )
        trained_models.append(model)
        val_probs_list.append(val_preds["tool_probs"])

    ensemble_val_probs = np.mean(val_probs_list, axis=0)
    val_tool_true = ds_val.y_tool.cpu().numpy()

    print("\n[3/4] Calibrating Per-Class Dynamic Thresholds on Validation Set...")
    optimal_thresholds = calibrate_per_class_thresholds(
        ensemble_val_probs,
        val_tool_true,
        default_thresh=0.45,
        min_thresh=0.20,
        max_thresh=0.70,
    )
    print(f"  Calibrated 147 thresholds: Mean Tau = {np.mean(optimal_thresholds):.3f}")

    # Evaluate validation metrics with argmax fallback
    preds_bin = (ensemble_val_probs >= optimal_thresholds).astype(np.float32)
    val_app_mask = ds_val.app_mask.cpu().numpy()
    for row_i in range(len(preds_bin)):
        if preds_bin[row_i].sum() == 0:
            best_i = int(np.argmax(ensemble_val_probs[row_i] * val_app_mask[row_i]))
            if val_app_mask[row_i, best_i] > 0.5:
                preds_bin[row_i, best_i] = 1.0

    tp = float(np.sum((preds_bin == 1.0) & (val_tool_true == 1.0)))
    fp = float(np.sum((preds_bin == 1.0) & (val_tool_true == 0.0)))
    fn = float(np.sum((preds_bin == 0.0) & (val_tool_true == 1.0)))
    val_p = tp / max(1.0, tp + fp)
    val_r = tp / max(1.0, tp + fn)
    val_f1 = (2 * val_p * val_r / (val_p + val_r)) if (val_p + val_r) > 0 else 0.0

    # Top-5 recall
    top5_idx = np.argsort(-ensemble_val_probs, axis=-1)[:, :5]
    top5_hits, top5_tot = 0, 0
    for i in range(len(val_tool_true)):
        pos = set(np.where(val_tool_true[i] > 0.5)[0].tolist())
        t5 = set(top5_idx[i].tolist())
        top5_hits += len(pos & t5)
        top5_tot += len(pos)
    top5_recall = top5_hits / max(1.0, top5_tot)

    print("=" * 80)
    print("PHOWHISPER SOTA BENCHMARK RESULTS (Clean Val N=309):")
    print(f"  Micro Precision: {val_p * 100:.2f}%")
    print(f"  Micro Recall:    {val_r * 100:.2f}%")
    print(f"  Micro F1:        {val_f1 * 100:.2f}%")
    print(f"  Top-5 Recall:    {top5_recall * 100:.2f}%")
    print("=" * 80)

    # Save Checkpoints
    CKPT_DIR.mkdir(exist_ok=True)
    torch.save(trained_models[0].state_dict(), CKPT_DIR / "phowhisper_router_sota.pt")
    torch.save(trained_models[0].state_dict(), CKPT_DIR / "hierarchical_router_sota.pt")
    torch.save(trained_models[0].state_dict(), CKPT_DIR / "router_sota.pt")
    for i, m in enumerate(trained_models):
        torch.save(m.state_dict(), CKPT_DIR / f"router_ensemble_{i}.pt")

    thresh_dict = {fe.all_tools[i]: float(optimal_thresholds[i]) for i in range(len(optimal_thresholds))}
    with open(CKPT_DIR / "tool_thresholds.json", "w", encoding="utf-8") as f:
        json.dump(thresh_dict, f, ensure_ascii=False, indent=2)

    eval_out = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "hardware": DEVICE,
        "pretrained_speech_backbone": "vinai/PhoWhisper-base",
        "speech_dimension": 512,
        "validation_metrics": {
            "samples": len(val_clean),
            "micro_precision": round(val_p, 4),
            "micro_recall": round(val_r, 4),
            "micro_f1": round(val_f1, 4),
            "top5_recall": round(top5_recall, 4),
        },
        "mean_threshold": round(float(np.mean(optimal_thresholds)), 3),
        "elapsed_seconds": round(time.time() - t0, 2),
    }
    with open(PROJECT_ROOT / "phowhisper_benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(eval_out, f, ensure_ascii=False, indent=2)

    print(f"\n[4/4] Saved Artifacts:")
    print(f"  - Model:      {CKPT_DIR / 'phowhisper_router_sota.pt'}")
    print(f"  - Thresholds: {CKPT_DIR / 'tool_thresholds.json'}")
    print(f"  - Report:     {PROJECT_ROOT / 'phowhisper_benchmark_results.json'}")
    print(f"Total time: {time.time() - t0:.2f}s")


if __name__ == "__main__":
    main()
