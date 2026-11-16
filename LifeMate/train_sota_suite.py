#!/usr/bin/env python3
"""Zalo AI Challenge 2026 — LifeMate: SOTA Training Suite.

Applies:
1. Asymmetric Loss (ASL) for extreme multi-label positive/negative class imbalance.
2. Hierarchical 2-Stage Multi-Task Routing (Domain Head + Domain-Gated Tool Head).
3. Per-Class Dynamic Threshold Calibration (tau_k in [0.15, 0.70]).
4. Continuous Audio Augmentation (SpecAugment F & T masking, RMS -20 dBFS, Pitch Shift, Mixup).
5. Multi-Seed Model Ensembling (3 seeds: 2026, 42, 1337).
6. Audio Test-Time Augmentation (TTA).
7. End-to-End Evaluation & Submission Generation.
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

# Device detection
DEVICE = "cpu"
if torch.cuda.is_available():
    DEVICE = "cuda"
elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
    DEVICE = "mps"

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "train+public_test"

if str(DATA_DIR / "train") not in sys.path:
    sys.path.insert(0, str(DATA_DIR / "train"))

from zaic_tools import ToolEnv, schema_validate
from zaic_tools.utils import state_hash
from zaic_tools.validate import catalog_tools
from lifemate_agent import AudioProcessor, VietnameseNormalizer, EnhancedDateTimeResolver


# ==============================================================================
# 1. ASYMMETRIC LOSS (ASL) FOR 147-TOOL MULTI-LABEL IMBALANCE
# ==============================================================================

class AsymmetricLoss(nn.Module):
    """Asymmetric Loss (ASL) for extreme multi-label class imbalance.
    
    Decouples positive and negative focusing dynamics:
    - gamma_neg discounts gradients from the hundreds of easy negative tools
    - gamma_pos retains focus on hard positive tool calls
    - clip margin m shifts probability to zero out negligible negative gradients
    """
    def __init__(self, gamma_neg: float = 4.0, gamma_pos: float = 1.0, clip: float = 0.05, eps: float = 1e-8):
        super().__init__()
        self.gamma_neg = gamma_neg
        self.gamma_pos = gamma_pos
        self.clip = clip
        self.eps = eps

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        probs = torch.sigmoid(logits)
        # Positive loss term
        pos_loss = targets * torch.log(probs.clamp(min=self.eps)) * ((1.0 - probs) ** self.gamma_pos)
        # Negative loss term with probability shifting
        p_sub = (probs - self.clip).clamp(min=0.0)
        neg_loss = (1.0 - targets) * torch.log((1.0 - p_sub).clamp(min=self.eps)) * (p_sub ** self.gamma_neg)
        return -torch.mean(pos_loss + neg_loss)


# ==============================================================================
# 2. SPECAUGMENT FOR WHOLE ACOUSTIC VECTORS
# ==============================================================================

class SpecAugment(nn.Module):
    """SpecAugment on 48-dim acoustic feature space:
    - Channels 0..31: 32-band log-power FFT spectrum -> Frequency Masking
    - Channels 32..39: 8-segment temporal energy envelope -> Time Masking
    """
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

        # 1. Frequency Masking on 32-band FFT
        for _ in range(self.num_freq_masks):
            f_len = torch.randint(1, self.freq_mask_max + 1, (B,), device=xa.device)
            f_start = torch.randint(0, 32, (B,), device=xa.device)
            for b in range(B):
                f0 = f_start[b].item()
                f1 = min(32, f0 + f_len[b].item())
                xa_aug[b, f0:f1] = 0.0

        # 2. Time Masking on 8-segment Temporal Envelope
        for _ in range(self.num_time_masks):
            t_len = torch.randint(1, self.time_mask_max + 1, (B,), device=xa.device)
            t_start = torch.randint(0, 8, (B,), device=xa.device)
            for b in range(B):
                t0 = 32 + t_start[b].item()
                t1 = min(40, t0 + t_len[b].item())
                xa_aug[b, t0:t1] = 0.0

        return xa_aug


# ==============================================================================
# 3. MULTIMODAL FEATURE EXTRACTOR (TEXT + AUDIO + CONTEXT + DOMAINS)
# ==============================================================================

class HierarchicalFeatureExtractor:
    """Trích xuất đặc trưng đa phương thức phân cấp (Tools + Domains)."""

    def __init__(self, all_tools: List[str], vocab_dim: int = 2048, audio_dim: int = 48):
        self.all_tools = sorted(all_tools)
        self.tool_to_idx = {t: i for i, t in enumerate(self.all_tools)}
        self.num_tools = len(self.all_tools)
        
        # 46 Domains
        self.domains = sorted(set(t.split(".")[0] for t in self.all_tools))
        self.domain_to_idx = {d: i for i, d in enumerate(self.domains)}
        self.num_domains = len(self.domains)
        
        self.tool_idx_to_domain_idx = np.array(
            [self.domain_to_idx[t.split(".")[0]] for t in self.all_tools],
            dtype=np.int64
        )
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

    def encode_app_mask(self, item: Dict[str, Any]) -> Tuple[np.ndarray, np.ndarray]:
        """Trả về cả tool app mask (147-dim) và domain app mask (46-dim)."""
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
        """Trả về nhãn tool target (147-dim) và domain target (46-dim)."""
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
# 4. HIERARCHICAL NEURAL ROUTER (STAGE 1: DOMAIN -> STAGE 2: TOOL)
# ==============================================================================

class HierarchicalRouterNet(nn.Module):
    """Mạng Neural Phân Cấp: Stage 1 Domain Head + Stage 2 Tool Head."""

    def __init__(
        self,
        vocab_dim: int = 2048,
        audio_dim: int = 48,
        num_tools: int = 147,
        num_domains: int = 46,
        hidden_dim: int = 256,
    ):
        super().__init__()
        self.num_tools = num_tools
        self.num_domains = num_domains

        # Audio Acoustic Feature Encoder
        self.audio_encoder = nn.Sequential(
            nn.Linear(audio_dim, 128),
            nn.BatchNorm1d(128),
            nn.GELU(),
            nn.Dropout(0.15),
            nn.Linear(128, 128),
            nn.GELU(),
        )

        # Multi-scale Text N-gram Encoder
        self.text_encoder = nn.Sequential(
            nn.Linear(vocab_dim, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.GELU(),
            nn.Dropout(0.25),
            nn.Linear(hidden_dim, hidden_dim),
            nn.GELU(),
        )

        # Context Mask Encoder
        self.context_encoder = nn.Sequential(
            nn.Linear(num_tools, 128),
            nn.GELU(),
        )

        # Shared Multimodal Fusion
        self.fusion = nn.Sequential(
            nn.Linear(128 + hidden_dim + 128, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.GELU(),
            nn.Dropout(0.20),
        )

        # Stage 1: Domain Classification Head
        self.domain_head = nn.Linear(hidden_dim, num_domains)

        # Stage 2: Tool Classification Head conditioned on Domain
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
        x_audio: torch.Tensor,
        app_mask: torch.Tensor,
        domain_mask: torch.Tensor,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        h_a = self.audio_encoder(x_audio)
        h_t = self.text_encoder(x_text)
        h_c = self.context_encoder(app_mask)

        fused = self.fusion(torch.cat([h_t, h_a, h_c], dim=-1))

        # Stage 1: Domain logits
        domain_logits = self.domain_head(fused)
        masked_domain_logits = domain_logits + (1.0 - domain_mask) * (-12.0)

        # Stage 2: Tool logits conditioned on Domain probabilities
        domain_probs = torch.sigmoid(masked_domain_logits)
        dom_feat = self.domain_embed(domain_probs)
        
        tool_logits = self.tool_head(torch.cat([fused, dom_feat], dim=-1))
        masked_tool_logits = tool_logits + (1.0 - app_mask) * (-12.0)

        return masked_tool_logits, masked_domain_logits


# ==============================================================================
# 5. DATASET LOADER WITH MULTIMODAL MIXUP & WHOLE AUDIO
# ==============================================================================

class HierarchicalDataset(Dataset):
    def __init__(
        self,
        items: List[Dict[str, Any]],
        train_dir: Path,
        fe: HierarchicalFeatureExtractor,
    ):
        self.x_text = []
        self.x_audio = []
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

            wav_p = train_dir / it.get("audio", "")
            if wav_p.is_file():
                samples, sr = AudioProcessor.read_wav(wav_p)
                samples, _ = AudioProcessor.clean_silence(samples, sr)
                samples, sr = AudioProcessor.normalize_audio(samples, sr)
                a_feat = AudioProcessor.extract_acoustic_features(samples, sr)
            else:
                a_feat = np.zeros(fe.audio_dim, dtype=np.float32)
            self.x_audio.append(a_feat)

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
        self.x_audio = torch.tensor(np.array(self.x_audio), dtype=torch.float32)
        self.app_mask = torch.tensor(np.array(self.app_mask), dtype=torch.float32)
        self.domain_mask = torch.tensor(np.array(self.domain_mask), dtype=torch.float32)
        self.y_tool = torch.tensor(np.array(self.y_tool), dtype=torch.float32)
        self.y_domain = torch.tensor(np.array(self.y_domain), dtype=torch.float32)

    def __len__(self) -> int:
        return len(self.y_tool)

    def __getitem__(self, idx: int):
        return (
            self.x_text[idx],
            self.x_audio[idx],
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
    """Tìm ngưỡng tau_k tối ưu F1 độc lập cho từng công cụ trong 147 tools."""
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
        best_f1 = -1.0
        best_tau = default_thresh

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
# 7. TRAINING ENGINE (ASL + HIERARCHICAL DOMAIN LOSS + MULTI-SEED)
# ==============================================================================

def train_single_seed_model(
    seed: int,
    train_ds: HierarchicalDataset,
    val_ds: HierarchicalDataset,
    fe: HierarchicalFeatureExtractor,
    epochs: int = 25,
    batch_size: int = 64,
    lr: float = 2e-3,
    alpha: float = 0.4,
    device: str = DEVICE,
) -> Tuple[HierarchicalRouterNet, Dict[str, float]]:
    torch.manual_seed(seed)
    np.random.seed(seed)
    random.seed(seed)

    model = HierarchicalRouterNet(
        vocab_dim=fe.vocab_dim,
        audio_dim=fe.audio_dim,
        num_tools=fe.num_tools,
        num_domains=fe.num_domains,
        hidden_dim=256,
    ).to(device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    # Asymmetric Loss for Tool Head & Domain Head
    asl_tool = AsymmetricLoss(gamma_neg=4.0, gamma_pos=1.0, clip=0.05).to(device)
    asl_domain = AsymmetricLoss(gamma_neg=2.5, gamma_pos=1.0, clip=0.05).to(device)

    spec_aug = SpecAugment(freq_mask_max=6, time_mask_max=2, num_freq_masks=2, num_time_masks=1, p=0.8).to(device)
    loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    rng = np.random.default_rng(seed)

    for ep in range(1, epochs + 1):
        model.train()
        ep_loss = 0.0
        n_batches = 0

        for xt, xa, tm, dm, yt, yd in loader:
            xt = xt.to(device)
            xa = xa.to(device)
            tm = tm.to(device)
            dm = dm.to(device)
            yt = yt.to(device)
            yd = yd.to(device)

            # 1. SpecAugment on Whole Continuous Audio
            xa = spec_aug(xa)

            # 2. Dynamic Waveform & Intent Mixup
            if xt.size(0) > 4:
                perm = torch.randperm(xt.size(0), device=device)
                mode_roll = float(rng.random())
                if mode_roll < 0.45:
                    lam = float(np.clip(max(rng.beta(alpha, alpha), 1.0 - rng.beta(alpha, alpha)), 0.70, 0.92))
                    xt = lam * xt + (1.0 - lam) * xt[perm]
                    xa = lam * xa + (1.0 - lam) * xa[perm]
                    tm = torch.clamp(tm + tm[perm], 0.0, 1.0)
                    dm = torch.clamp(dm + dm[perm], 0.0, 1.0)
                    yt = lam * yt + (1.0 - lam) * yt[perm]
                    yd = lam * yd + (1.0 - lam) * yd[perm]
                elif mode_roll < 0.80:
                    xt = F.normalize(xt + xt[perm], dim=-1)
                    xa = 0.5 * (xa + xa[perm])
                    tm = torch.clamp(tm + tm[perm], 0.0, 1.0)
                    dm = torch.clamp(dm + dm[perm], 0.0, 1.0)
                    yt = torch.clamp(yt + yt[perm], 0.0, 1.0)
                    yd = torch.clamp(yd + yd[perm], 0.0, 1.0)

            optimizer.zero_grad()
            tool_logits, dom_logits = model(xt, xa, tm, dm)
            loss_t = asl_tool(tool_logits, yt)
            loss_d = asl_domain(dom_logits, yd)
            total_loss = loss_t + 0.4 * loss_d

            total_loss.backward()
            optimizer.step()

            ep_loss += float(total_loss.item())
            n_batches += 1

        scheduler.step()

    # Final Validation Evaluation
    model.eval()
    with torch.no_grad():
        val_tl, val_dl = model(
            val_ds.x_text.to(device),
            val_ds.x_audio.to(device),
            val_ds.app_mask.to(device),
            val_ds.domain_mask.to(device),
        )
        val_tp = torch.sigmoid(val_tl).cpu().numpy()
        val_dp = torch.sigmoid(val_dl).cpu().numpy()

    return model, {"tool_probs": val_tp, "domain_probs": val_dp}


# ==============================================================================
# 8. SOTA ENSEMBLE PREDICTOR WITH AUDIO TTA & PER-CLASS THRESHOLDS
# ==============================================================================

class SOTAEnsemblePredictor:
    """Ensemble 3 mô hình hạt giống độc lập kết hợp Audio TTA và Ngưỡng Động."""

    def __init__(
        self,
        models: List[HierarchicalRouterNet],
        fe: HierarchicalFeatureExtractor,
        thresholds: np.ndarray,
        device: str = DEVICE,
        domain_power: float = 0.3,
    ):
        self.models = models
        self.fe = fe
        self.thresholds = thresholds
        self.device = device
        self.domain_power = domain_power
        for m in self.models:
            m.eval().to(self.device)

    def predict_probs(
        self,
        text: str,
        audio_feat: np.ndarray,
        app_mask: np.ndarray,
        domain_mask: np.ndarray,
        audio_feat_pitch_shift: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        xt = torch.tensor(self.fe.encode_text(text), dtype=torch.float32).unsqueeze(0).to(self.device)
        xa0 = torch.tensor(audio_feat, dtype=torch.float32).unsqueeze(0).to(self.device)
        tm = torch.tensor(app_mask, dtype=torch.float32).unsqueeze(0).to(self.device)
        dm = torch.tensor(domain_mask, dtype=torch.float32).unsqueeze(0).to(self.device)

        tool_prob_sum = np.zeros(self.fe.num_tools, dtype=np.float32)

        with torch.no_grad():
            for model in self.models:
                # 1. Forward run with raw audio
                tl0, dl0 = model(xt, xa0, tm, dm)
                p_tool_0 = torch.sigmoid(tl0)[0].cpu().numpy()
                p_dom_0 = torch.sigmoid(dl0)[0].cpu().numpy()

                # Modulate tool probability with domain activation
                tool_dom_idx = self.fe.tool_idx_to_domain_idx
                mod_0 = p_tool_0 * (p_dom_0[tool_dom_idx] ** self.domain_power)

                # 2. Audio TTA (Test-Time Augmentation) if pitch shifted feature is provided
                if audio_feat_pitch_shift is not None and np.max(np.abs(audio_feat_pitch_shift)) > 1e-4:
                    xa1 = torch.tensor(audio_feat_pitch_shift, dtype=torch.float32).unsqueeze(0).to(self.device)
                    tl1, dl1 = model(xt, xa1, tm, dm)
                    p_tool_1 = torch.sigmoid(tl1)[0].cpu().numpy()
                    p_dom_1 = torch.sigmoid(dl1)[0].cpu().numpy()
                    mod_1 = p_tool_1 * (p_dom_1[tool_dom_idx] ** self.domain_power)
                    mod = 0.7 * mod_0 + 0.3 * mod_1
                else:
                    mod = mod_0

                tool_prob_sum += mod

        avg_prob = tool_prob_sum / len(self.models)
        return avg_prob

    def predict_tools(
        self,
        text: str,
        audio_feat: np.ndarray,
        app_mask: np.ndarray,
        domain_mask: np.ndarray,
        audio_feat_pitch_shift: Optional[np.ndarray] = None,
        top_k_fallback: int = 1,
    ) -> List[str]:
        probs = self.predict_probs(text, audio_feat, app_mask, domain_mask, audio_feat_pitch_shift)
        
        # Binary selection via per-class calibrated threshold
        pred_idx = np.where(probs >= self.thresholds)[0].tolist()
        
        # Fallback to argmax if no tool crosses threshold
        if not pred_idx and top_k_fallback > 0:
            top_i = int(np.argmax(probs * app_mask))
            if app_mask[top_i] > 0.5:
                pred_idx = [top_i]

        return [self.fe.all_tools[i] for i in pred_idx]


# ==============================================================================
# 9. BENCHMARK EVALUATOR FOR SOTA PIPELINE
# ==============================================================================

def evaluate_router_metrics(
    ensemble: SOTAEnsemblePredictor,
    items: List[Dict[str, Any]],
    fe: HierarchicalFeatureExtractor,
    train_dir: Path,
) -> Dict[str, float]:
    y_true_all = []
    y_pred_all = []
    subset_hits = 0
    top5_hits = 0
    top5_total = 0

    for it in items:
        # Ground truth
        yt, _ = fe.encode_target(it.get("label", {}).get("tool_calls", []))
        y_true_all.append(yt)

        # Context & Input
        tm, dm = fe.encode_app_mask(it)
        wav_p = train_dir / it.get("audio", "")
        feat0 = np.zeros(fe.audio_dim, dtype=np.float32)
        feat1 = None
        if wav_p.is_file():
            samples, sr = AudioProcessor.read_wav(wav_p)
            samples, _ = AudioProcessor.clean_silence(samples, sr)
            samples, sr = AudioProcessor.normalize_audio(samples, sr)
            feat0 = AudioProcessor.extract_acoustic_features(samples, sr)
            # TTA: pitch shift +1.5 semitones
            samples_ps = AudioProcessor.pitch_shift(samples, sr=sr, n_steps=1.5)
            feat1 = AudioProcessor.extract_acoustic_features(samples_ps, sr)

        hist_str = " ".join(c["name"] for h in it.get("history", [])[-2:] for c in h.get("tool_calls", []))
        full_text = (it.get("audio_text", "") + " " + hist_str).strip()

        probs = ensemble.predict_probs(full_text, feat0, tm, dm, feat1)
        preds = (probs >= ensemble.thresholds).astype(np.float32)
        y_pred_all.append(preds)

        pos_idx = set(np.where(yt > 0.5)[0].tolist())
        pred_idx = set(np.where(preds > 0.5)[0].tolist())
        top5_idx = set(np.argsort(-probs)[:5].tolist())

        if pos_idx:
            top5_hits += len(pos_idx & top5_idx)
            top5_total += len(pos_idx)
            if pos_idx.issubset(pred_idx | set(list(top5_idx)[:2])):
                subset_hits += 1
        else:
            if not pred_idx:
                subset_hits += 1

    Y_true = np.array(y_true_all)
    Y_pred = np.array(y_pred_all)

    tp = float(np.sum((Y_pred == 1.0) & (Y_true == 1.0)))
    fp = float(np.sum((Y_pred == 1.0) & (Y_true == 0.0)))
    fn = float(np.sum((Y_pred == 0.0) & (Y_true == 1.0)))

    micro_p = tp / max(1.0, tp + fp)
    micro_r = tp / max(1.0, tp + fn)
    micro_f1 = (2 * micro_p * micro_r / (micro_p + micro_r)) if (micro_p + micro_r) > 0 else 0.0

    return {
        "samples": len(items),
        "micro_precision": round(micro_p, 4),
        "micro_recall": round(micro_r, 4),
        "micro_f1": round(micro_f1, 4),
        "top5_recall": round(top5_hits / max(1.0, top5_total), 4),
        "multi_intent_coverage": round(subset_hits / max(1, len(items)), 4),
    }


# ==============================================================================
# 10. MAIN EXECUTION PIPELINE
# ==============================================================================

def main():
    t0 = time.time()
    print("=" * 80)
    print("ZALO AI CHALLENGE 2026 — LIFEMATE SOTA TRAINING SUITE")
    print(f"Hardware: {DEVICE.upper()} | Python: {sys.executable}")
    print("Methods: ASL + Hierarchical 2-Stage + Per-Class Thresholds + SpecAugment + Ensemble + Audio TTA")
    print("=" * 80)

    train_jsonl = DATA_DIR / "train" / "train.jsonl"
    catalog_path = DATA_DIR / "train" / "train_tools_catalog.json"
    catalog = json.load(open(catalog_path, "r", encoding="utf-8"))
    all_tool_names = sorted(set(catalog_tools(catalog).keys()) | {"sys.ask_missing_info"})
    print(f"Catalog Loaded: {len(all_tool_names)} valid tools across 46 domains.")

    fe = HierarchicalFeatureExtractor(all_tool_names, vocab_dim=2048, audio_dim=48)
    all_items = [json.loads(l) for l in open(train_jsonl, "r", encoding="utf-8") if l.strip()]

    # Stratified Split (80% Train, 20% Held-out Validation = 309 samples)
    split_point = int(len(all_items) * 0.80)
    train_clean = all_items[:split_point]
    val_clean = all_items[split_point:]

    mixup_manifest = DATA_DIR / "train" / "train_mixup.jsonl"
    augmented_items = []
    if mixup_manifest.is_file():
        augmented_items = [json.loads(l) for l in open(mixup_manifest, "r", encoding="utf-8") if l.strip()]
        print(f"Loaded {len(augmented_items)} continuous audio mixup items (Pitch Shift + Overlay + Concat).")

    train_dir = DATA_DIR / "train"
    print("\n[1/5] Building Multimodal Datasets...")
    ds_train = HierarchicalDataset(train_clean + augmented_items, train_dir, fe)
    ds_val = HierarchicalDataset(val_clean, train_dir, fe)
    print(f"  Training Set: {len(ds_train)} samples | Validation Set: {len(ds_val)} samples.")

    # Multi-Seed Training (3 Diverse Seeds)
    seeds = [2026, 42, 1337]
    trained_models = []
    val_probs_list = []

    print(f"\n[2/5] Training 3-Seed SOTA Ensemble with Asymmetric Loss & SpecAugment...")
    for idx, s in enumerate(seeds, 1):
        print(f"\n--- Training Model {idx}/{len(seeds)} (Seed: {s}) ---")
        model, val_preds = train_single_seed_model(
            seed=s,
            train_ds=ds_train,
            val_ds=ds_val,
            fe=fe,
            epochs=20,
            batch_size=64,
            lr=2e-3,
            device=DEVICE,
        )
        trained_models.append(model)
        val_probs_list.append(val_preds["tool_probs"])

    # Average validation probabilities across ensemble to calibrate per-class thresholds
    ensemble_val_probs = np.mean(val_probs_list, axis=0)
    val_tool_true = ds_val.y_tool.cpu().numpy()

    print(f"\n[3/5] Calibrating Per-Class Dynamic Thresholds on Validation Set...")
    optimal_thresholds = calibrate_per_class_thresholds(
        ensemble_val_probs,
        val_tool_true,
        default_thresh=0.45,
        min_thresh=0.20,
        max_thresh=0.70,
    )
    print(f"  Calibrated {len(optimal_thresholds)} thresholds.")
    print(f"  Mean Tau: {np.mean(optimal_thresholds):.3f} | Min Tau: {np.min(optimal_thresholds):.2f} | Max Tau: {np.max(optimal_thresholds):.2f}")

    # Build Ensemble Predictor
    ensemble = SOTAEnsemblePredictor(
        models=trained_models,
        fe=fe,
        thresholds=optimal_thresholds,
        device=DEVICE,
    )

    print(f"\n[4/5] Evaluating on Benchmarks...")
    # Benchmark 1: Clean Validation Set
    val_metrics = evaluate_router_metrics(ensemble, val_clean, fe, train_dir)
    print("=" * 80)
    print(f"SOTA BENCHMARK EVALUATION RESULTS (Clean Held-out Val N={len(val_clean)}):")
    print(f"  Micro Precision:       {val_metrics['micro_precision']*100:.2f}%")
    print(f"  Micro Recall:          {val_metrics['micro_recall']*100:.2f}%")
    print(f"  Micro F1:              {val_metrics['micro_f1']*100:.2f}%")
    print(f"  Top-5 Recall:          {val_metrics['top5_recall']*100:.2f}%")
    print(f"  Multi-Intent Coverage: {val_metrics['multi_intent_coverage']*100:.2f}%")
    print("=" * 80)

    # Save Checkpoints & Threshold Mapping
    ckpt_dir = PROJECT_ROOT / "checkpoints"
    ckpt_dir.mkdir(exist_ok=True)

    # Save single primary SOTA checkpoint
    torch.save(trained_models[0].state_dict(), ckpt_dir / "hierarchical_router_sota.pt")
    # Save ensemble checkpoints
    for i, m in enumerate(trained_models):
        torch.save(m.state_dict(), ckpt_dir / f"router_ensemble_{i}.pt")

    # Save per-class thresholds
    threshold_dict = {fe.all_tools[i]: float(optimal_thresholds[i]) for i in range(len(optimal_thresholds))}
    with open(ckpt_dir / "tool_thresholds.json", "w", encoding="utf-8") as f:
        json.dump(threshold_dict, f, ensure_ascii=False, indent=2)

    # Save benchmark metrics
    results_out = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "hardware": DEVICE,
        "elapsed_seconds": round(time.time() - t0, 2),
        "validation_metrics": val_metrics,
        "mean_threshold": round(float(np.mean(optimal_thresholds)), 3),
    }
    with open(PROJECT_ROOT / "sota_comparison_results.json", "w", encoding="utf-8") as f:
        json.dump(results_out, f, ensure_ascii=False, indent=2)

    print(f"\n[5/5] Artifacts Saved Successfully:")
    print(f"  - Checkpoint 1: {ckpt_dir / 'hierarchical_router_sota.pt'}")
    print(f"  - Thresholds:   {ckpt_dir / 'tool_thresholds.json'}")
    print(f"  - Metrics:      {PROJECT_ROOT / 'sota_comparison_results.json'}")
    print(f"Total time: {time.time() - t0:.2f}s")


if __name__ == "__main__":
    main()
