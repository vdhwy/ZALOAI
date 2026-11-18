#!/usr/bin/env python3
"""Zalo AI Challenge 2026 — LifeMate: SOTA Audio Spectrogram Transformer (AST) Router.

Leverages:
1. Pretrained AST (Audio Spectrogram Transformer) 768-dim representations
   specifically designed for Audio Classification ('MIT/ast-finetuned-audioset-10-10-0.4593').
2. 48-dim Whole-Waveform Acoustic Prosodic & FFT features with SpecAugment.
3. Asymmetric Loss (ASL) for extreme multi-label long-tail class imbalance.
4. Hierarchical 2-Stage Routing (Domain Head + Domain-Gated Tool Head).
5. Precision-Gated Calibrated Thresholds (tau_k >= 0.85) to eliminate false positives.
6. Multi-Seed Model Ensembling (3 Seeds: 2026, 42, 1337).
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
CACHE_FILE = CKPT_DIR / "ast_embeddings.pt"

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
# 3. FEATURE EXTRACTOR WITH PRETRAINED AST EMBEDDINGS
# ==============================================================================

class MultimodalASTFeatureExtractor:
    def __init__(
        self,
        all_tools: List[str],
        vocab_dim: int = 2048,
        speech_dim: int = 768,
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
# 4. HIERARCHICAL PRETRAINED AST AUDIO CLASSIFIER ROUTER NET
# ==============================================================================

class ASTAudioClassifierRouterNet(nn.Module):
    """Mạng Neural Định Tuyến kết hợp Đặc Trưng Âm Học Sâu từ AST (Audio Spectrogram Transformer)."""

    def __init__(
        self,
        vocab_dim: int = 2048,
        speech_dim: int = 768,
        prosody_dim: int = 48,
        num_tools: int = 147,
        num_domains: int = 46,
        hidden_dim: int = 256,
    ):
        super().__init__()
        self.num_tools = num_tools
        self.num_domains = num_domains

        # 1. Pretrained Deep AST Audio Classifier Encoder (AST 768-dim -> 192)
        self.speech_encoder = nn.Sequential(
            nn.Linear(speech_dim, 384),
            nn.BatchNorm1d(384),
            nn.GELU(),
            nn.Dropout(0.20),
            nn.Linear(384, 192),
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

        # 5. Shared Multimodal Fusion (256 + 192 + 128 + 128 = 704 -> 256)
        self.fusion = nn.Sequential(
            nn.Linear(hidden_dim + 192 + 128 + 128, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.GELU(),
            nn.Dropout(0.20),
        )

        # 6. Stage 1: Domain Head (256 -> num_domains)
        self.domain_head = nn.Linear(hidden_dim, num_domains)

        # 7. Stage 2: Tool Head conditioned on Domain (256 + 64 -> num_tools)
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

        # Concatenate text (256) + AST audio (192) + prosody (128) + context (128) = 704
        fused = self.fusion(torch.cat([h_t, h_s, h_p, h_c], dim=-1))

        # Stage 1: Domain logits
        domain_logits = self.domain_head(fused) + (1.0 - domain_mask) * (-12.0)
        domain_probs = torch.sigmoid(domain_logits)

        # Stage 2: Tool logits conditioned on domain
        dom_feat = self.domain_embed(domain_probs)
        tool_logits = self.tool_head(torch.cat([fused, dom_feat], dim=-1)) + (1.0 - app_mask) * (-12.0)

        return tool_logits, domain_logits


# ==============================================================================
# 5. DATASET LOADER
# ==============================================================================

class MultimodalASTDataset(Dataset):
    def __init__(
        self,
        items: List[Dict[str, Any]],
        extractor: MultimodalASTFeatureExtractor,
        root_dir: Path,
        split: str = "train",
        cache_features: bool = True,
    ):
        self.items = items
        self.extractor = extractor
        self.root_dir = root_dir
        self.split = split
        self.cache_features = cache_features
        self._cached: Dict[int, Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]] = {}

        if cache_features:
            print(f"Pre-caching multimodal AST features for {len(items)} samples...")
            t0 = time.time()
            for idx in range(len(items)):
                self._cached[idx] = self._extract(idx)
            print(f"Caching complete in {time.time() - t0:.2f}s.")

    def _extract(self, idx: int):
        item = self.items[idx]
        hist_str = " ".join(c["name"] for h in item.get("history", [])[-2:] for c in h.get("tool_calls", []))
        text = (item.get("audio_text", "") + " " + hist_str).strip()
        x_text = self.extractor.encode_text(text)

        rel_audio = item.get("audio", "")
        x_speech = self.extractor.get_speech_embedding(rel_audio)

        x_prosody = np.zeros(self.extractor.prosody_dim, dtype=np.float32)
        if rel_audio:
            wav_path = self.root_dir / self.split / rel_audio
            if wav_path.is_file():
                try:
                    samples, sr = AudioProcessor.read_wav(wav_path)
                    samples, _ = AudioProcessor.clean_silence(samples, sr)
                    samples, sr = AudioProcessor.normalize_audio(samples, sr)
                    x_prosody = AudioProcessor.extract_acoustic_features(samples, sr)
                except Exception:
                    pass

        tool_mask, domain_mask = self.extractor.encode_app_mask(item)
        tool_calls = item.get("label", {}).get("tool_calls", [])
        y_tool, y_domain = self.extractor.encode_target(tool_calls)

        return x_text, x_speech, x_prosody, tool_mask, domain_mask, y_tool, y_domain

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, idx: int):
        if self.cache_features and idx in self._cached:
            t = self._cached[idx]
        else:
            t = self._extract(idx)

        return (
            torch.tensor(t[0], dtype=torch.float32),
            torch.tensor(t[1], dtype=torch.float32),
            torch.tensor(t[2], dtype=torch.float32),
            torch.tensor(t[3], dtype=torch.float32),
            torch.tensor(t[4], dtype=torch.float32),
            torch.tensor(t[5], dtype=torch.float32),
            torch.tensor(t[6], dtype=torch.float32),
        )


# ==============================================================================
# 6. TRAINING SUITE WITH MULTI-SEED ENSEMBLE & DYNAMIC THRESHOLD CALIBRATION
# ==============================================================================

def train_single_seed(
    seed: int,
    train_loader: DataLoader,
    val_loader: DataLoader,
    extractor: MultimodalASTFeatureExtractor,
    epochs: int = 35,
    lr: float = 8e-4,
    device: str = DEVICE,
) -> Tuple[ASTAudioClassifierRouterNet, float]:
    torch.manual_seed(seed)
    np.random.seed(seed)
    random.seed(seed)

    model = ASTAudioClassifierRouterNet(
        vocab_dim=extractor.vocab_dim,
        speech_dim=extractor.speech_dim,
        prosody_dim=extractor.prosody_dim,
        num_tools=extractor.num_tools,
        num_domains=extractor.num_domains,
        hidden_dim=256,
    ).to(device)

    spec_aug = SpecAugment(p=0.8).to(device)
    asl_tool = AsymmetricLoss(gamma_neg=4.0, gamma_pos=1.0, clip=0.05)
    asl_dom = AsymmetricLoss(gamma_neg=2.0, gamma_pos=1.0, clip=0.05)

    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-5)

    best_val_f1 = 0.0
    best_state = None

    for epoch in range(1, epochs + 1):
        model.train()
        train_loss = 0.0

        for xt, xs, xp, app_m, dom_m, yt, yd in train_loader:
            xt, xs, xp = xt.to(device), xs.to(device), xp.to(device)
            app_m, dom_m = app_m.to(device), dom_m.to(device)
            yt, yd = yt.to(device), yd.to(device)

            xp_aug = spec_aug(xp)
            logits_t, logits_d = model(xt, xs, xp_aug, app_m, dom_m)

            loss_t = asl_tool(logits_t, yt)
            loss_d = asl_dom(logits_d, yd)
            loss = loss_t + 0.5 * loss_d

            optimizer.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 2.0)
            optimizer.step()

            train_loss += loss.item() * len(xt)

        scheduler.step()
        train_loss /= len(train_loader.dataset)

        # Validation evaluation
        model.eval()
        all_pred = []
        all_true = []
        with torch.no_grad():
            for xt, xs, xp, app_m, dom_m, yt, yd in val_loader:
                xt, xs, xp = xt.to(device), xs.to(device), xp.to(device)
                app_m, dom_m = app_m.to(device), dom_m.to(device)

                tl, dl = model(xt, xs, xp, app_m, dom_m)
                p_t = torch.sigmoid(tl).cpu().numpy()
                p_d = torch.sigmoid(dl).cpu().numpy()

                mod = p_t * (p_d[:, extractor.tool_idx_to_domain_idx] ** 0.3)
                all_pred.append(mod)
                all_true.append(yt.numpy())

        preds = np.vstack(all_pred)
        trues = np.vstack(all_true)

        p_bin = (preds >= 0.85).astype(np.float32)
        tp = (p_bin * trues).sum()
        fp = (p_bin * (1.0 - trues)).sum()
        fn = ((1.0 - p_bin) * trues).sum()
        precision = tp / (tp + fp + 1e-8)
        recall = tp / (tp + fn + 1e-8)
        val_f1 = 2 * precision * recall / (precision + recall + 1e-8)

        if val_f1 > best_val_f1 or best_state is None:
            best_val_f1 = val_f1
            best_state = copy.deepcopy(model.state_dict())

        if epoch % 5 == 0 or epoch == epochs:
            print(f"Seed {seed} | Epoch {epoch:02d}/{epochs:02d} | Train Loss: {train_loss:.4f} | Val F1: {val_f1:.4f} (P: {precision:.4f}, R: {recall:.4f})")

    model.load_state_dict(best_state)
    return model, best_val_f1


def calibrate_thresholds(
    models: List[ASTAudioClassifierRouterNet],
    val_loader: DataLoader,
    extractor: MultimodalASTFeatureExtractor,
    device: str = DEVICE,
) -> Dict[str, float]:
    for m in models:
        m.eval()

    all_prob_sums = []
    all_true = []

    with torch.no_grad():
        for xt, xs, xp, app_m, dom_m, yt, yd in val_loader:
            xt, xs, xp = xt.to(device), xs.to(device), xp.to(device)
            app_m, dom_m = app_m.to(device), dom_m.to(device)

            batch_probs = np.zeros((len(xt), extractor.num_tools), dtype=np.float32)
            for m in models:
                tl, dl = model_forward = m(xt, xs, xp, app_m, dom_m)
                p_t = torch.sigmoid(tl).cpu().numpy()
                p_d = torch.sigmoid(dl).cpu().numpy()
                batch_probs += p_t * (p_d[:, extractor.tool_idx_to_domain_idx] ** 0.3)

            batch_probs /= len(models)
            all_prob_sums.append(batch_probs)
            all_true.append(yt.numpy())

    probs = np.vstack(all_prob_sums)
    trues = np.vstack(all_true)

    # Precision Gate: calibrate optimal threshold per tool, strictly >= 0.85
    thresholds = {}
    candidate_taus = np.linspace(0.85, 0.95, 11)

    for i, tname in enumerate(extractor.all_tools):
        p_col = probs[:, i]
        y_col = trues[:, i]

        if y_col.sum() == 0:
            thresholds[tname] = 0.85
            continue

        best_tau = 0.85
        best_f1 = -1.0

        for tau in candidate_taus:
            pred_b = (p_col >= tau).astype(np.float32)
            tp = (pred_b * y_col).sum()
            fp = (pred_b * (1.0 - y_col)).sum()
            fn = ((1.0 - pred_b) * y_col).sum()
            prec = tp / (tp + fp + 1e-8)
            rec = tp / (tp + fn + 1e-8)
            f1 = 2 * prec * rec / (prec + rec + 1e-8)
            if f1 > best_f1:
                best_f1 = f1
                best_tau = float(tau)

        thresholds[tname] = best_tau

    return thresholds


# ==============================================================================
# 7. MAIN ORCHESTRATOR
# ==============================================================================

def main():
    print(f"========================================================================")
    print(f"ZAC 2026 LifeMate — AST Audio Classifier Router Training Suite")
    print(f"Pretrained Model: MIT/ast-finetuned-audioset-10-10-0.4593")
    print(f"AST Embedding Dimension: 768 | Device: {DEVICE}")
    print(f"========================================================================")

    # 1. Load tools catalog
    catalog_path = DATA_DIR / "train" / "train_tools_catalog.json"
    catalog = json.load(open(catalog_path, "r", encoding="utf-8"))
    all_tools = sorted(set(catalog_tools(catalog).keys()) | {"sys.ask_missing_info"})
    print(f"Loaded {len(all_tools)} tools across {len(set(t.split('.')[0] for t in all_tools))} domains.")

    # 2. Load AST embeddings cache
    if not CACHE_FILE.is_file():
        print(f"ERROR: AST cache file {CACHE_FILE} not found! Please run extract_ast_cache.py first.")
        sys.exit(1)

    ast_cache = torch.load(CACHE_FILE, map_location="cpu", weights_only=False)
    print(f"Loaded AST cache: {len(ast_cache)} audio representations (dim=768).")

    # 3. Load dataset
    train_source = DATA_DIR / "train" / "train.jsonl"
    all_lines = [json.loads(l) for l in open(train_source, "r", encoding="utf-8") if l.strip()]

    # Stratified train/val split (85% train, 15% val)
    random.seed(2026)
    indices = list(range(len(all_lines)))
    random.shuffle(indices)
    split_pt = int(0.85 * len(indices))
    train_items = [all_lines[i] for i in indices[:split_pt]]
    val_items = [all_lines[i] for i in indices[split_pt:]]

    # Include mixup data in train set if available
    mixup_path = DATA_DIR / "train" / "train_mixup.jsonl"
    if mixup_path.is_file():
        mixup_lines = [json.loads(l) for l in open(mixup_path, "r", encoding="utf-8") if l.strip()]
        train_items.extend(mixup_lines)
        print(f"Added {len(mixup_lines)} mixup samples to training set.")

    print(f"Dataset Split: {len(train_items)} train samples, {len(val_items)} validation samples.")

    # 4. Feature Extractor & Datasets
    extractor = MultimodalASTFeatureExtractor(
        all_tools=all_tools,
        vocab_dim=2048,
        speech_dim=768,
        prosody_dim=48,
        embedding_cache=ast_cache,
    )

    train_ds = MultimodalASTDataset(train_items, extractor, DATA_DIR, split="train", cache_features=True)
    val_ds = MultimodalASTDataset(val_items, extractor, DATA_DIR, split="train", cache_features=True)

    train_loader = DataLoader(train_ds, batch_size=32, shuffle=True, drop_last=True)
    val_loader = DataLoader(val_ds, batch_size=32, shuffle=False)

    # 5. Multi-seed training (3 seeds)
    seeds = [2026, 42, 1337]
    trained_models = []

    for s_idx, seed in enumerate(seeds):
        print(f"\n--- Training AST Audio Classifier Model {s_idx + 1}/3 (Seed: {seed}) ---")
        m, f1 = train_single_seed(seed, train_loader, val_loader, extractor, epochs=30, lr=8e-4, device=DEVICE)
        trained_models.append(m)

        ckpt_file = CKPT_DIR / f"ast_ensemble_{s_idx}.pt"
        torch.save(m.state_dict(), ckpt_file)
        print(f"Model saved to {ckpt_file} (Val F1: {f1:.4f})")

    # Save primary model
    torch.save(trained_models[0].state_dict(), CKPT_DIR / "ast_router_sota.pt")

    # 6. Calibrate per-class thresholds with Precision Gate
    print("\n--- Calibrating Precision Gate Thresholds (tau >= 0.85) ---")
    thresholds = calibrate_thresholds(trained_models, val_loader, extractor, device=DEVICE)
    thresh_file = CKPT_DIR / "ast_thresholds.json"
    with open(thresh_file, "w", encoding="utf-8") as f:
        json.dump(thresholds, f, indent=2, ensure_ascii=False)
    print(f"Calibrated thresholds saved to {thresh_file}.")

    print("\n========================================================================")
    print("AST Audio Classifier Router Training & Calibration Complete!")
    print("========================================================================")


if __name__ == "__main__":
    main()
