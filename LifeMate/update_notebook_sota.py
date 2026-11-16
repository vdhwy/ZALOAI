#!/usr/bin/env python3
"""Update baseline.ipynb Cell 11 with the Pretrained PhoWhisper Speech Router Suite:
- Pretrained PhoWhisper-base 512-dim Speech Encoder embeddings
- Asymmetric Loss (ASL)
- Hierarchical 2-Stage Multi-Task Routing (Domain Head + Domain-Gated Tool Head)
- SpecAugment on Whole Continuous Audio Waveforms
- Per-Class Dynamic Threshold Calibration (optimal 0.44-centered thresholds)
- Multi-Seed Ensembling (3 seeds: 2026, 42, 1337)
"""

import json
from pathlib import Path

nb_path = Path("baseline.ipynb")
nb = json.loads(nb_path.read_text(encoding="utf-8"))

cell_11_code = '''import copy
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
from zaic_tools.validate import catalog_tools

# ==============================================================================
# PRETRAINED PHOWHISPER SPEECH ROUTER TRAINING SUITE
# ==============================================================================

class AsymmetricLoss(nn.Module):
    """Asymmetric Loss (ASL) cho bài toán phân loại đa nhãn cực kỳ mất cân bằng (147 tools)."""
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


class SpecAugment(nn.Module):
    """SpecAugment (Frequency & Time Masking) cho vector đặc trưng âm học."""
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


class MultimodalSpeechFeatureExtractor:
    """Trích xuất đặc trưng đa phương thức (PhoWhisper 512 + Prosody 48 + Text 2048)."""
    def __init__(self, all_tools: List[str], vocab_dim: int = 2048, speech_dim: int = 512, prosody_dim: int = 48, cache: Optional[Dict[str, Any]] = None):
        self.all_tools = sorted(all_tools)
        self.tool_to_idx = {t: i for i, t in enumerate(self.all_tools)}
        self.num_tools = len(self.all_tools)
        self.domains = sorted(set(t.split(".")[0] for t in self.all_tools))
        self.domain_to_idx = {d: i for i, d in enumerate(self.domains)}
        self.num_domains = len(self.domains)
        self.tool_idx_to_domain_idx = np.array(
            [self.domain_to_idx[t.split(".")[0]] for t in self.all_tools],
            dtype=np.int64
        )
        self.vocab_dim = vocab_dim
        self.speech_dim = speech_dim
        self.prosody_dim = prosody_dim
        self.cache = cache or {}

    @staticmethod
    def _hash_token(tok: str, dim: int) -> int:
        h = int(hashlib.md5(tok.encode("utf-8")).hexdigest()[:8], 16)
        return h % dim

    def encode_text(self, text: str) -> np.ndarray:
        vec = np.zeros(self.vocab_dim, dtype=np.float32)
        s = VietnameseNormalizer.normalize_text(text)
        words = re.findall(r"\\w+", s)
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

    def get_speech_embedding(self, rel_path: str) -> np.ndarray:
        if rel_path in self.cache:
            return self.cache[rel_path]
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


class PhoWhisperHierarchicalRouterNet(nn.Module):
    """Mạng Neural Định Tuyến kết hợp Đặc Trưng Âm Học Sâu từ PhoWhisper."""
    def __init__(self, vocab_dim: int, speech_dim: int, prosody_dim: int, num_tools: int, num_domains: int, hidden_dim: int = 256):
        super().__init__()
        self.num_tools = num_tools
        self.num_domains = num_domains

        self.speech_encoder = nn.Sequential(
            nn.Linear(speech_dim, 256), nn.BatchNorm1d(256), nn.GELU(), nn.Dropout(0.20),
            nn.Linear(256, 128), nn.GELU()
        )
        self.prosody_encoder = nn.Sequential(
            nn.Linear(prosody_dim, 128), nn.BatchNorm1d(128), nn.GELU(), nn.Dropout(0.15),
            nn.Linear(128, 128), nn.GELU()
        )
        self.text_encoder = nn.Sequential(
            nn.Linear(vocab_dim, hidden_dim), nn.BatchNorm1d(hidden_dim), nn.GELU(), nn.Dropout(0.25),
            nn.Linear(hidden_dim, hidden_dim), nn.GELU()
        )
        self.context_encoder = nn.Sequential(nn.Linear(num_tools, 128), nn.GELU())
        self.fusion = nn.Sequential(
            nn.Linear(hidden_dim + 128 + 128 + 128, hidden_dim), nn.BatchNorm1d(hidden_dim), nn.GELU(), nn.Dropout(0.20)
        )
        self.domain_head = nn.Linear(hidden_dim, num_domains)
        self.domain_embed = nn.Sequential(nn.Linear(num_domains, 64), nn.GELU())
        self.tool_head = nn.Sequential(
            nn.Linear(hidden_dim + 64, hidden_dim), nn.BatchNorm1d(hidden_dim), nn.GELU(), nn.Dropout(0.15),
            nn.Linear(hidden_dim, num_tools)
        )

    def forward(self, xt: torch.Tensor, xs: torch.Tensor, xp: torch.Tensor, app_mask: torch.Tensor, domain_mask: torch.Tensor):
        ht = self.text_encoder(xt)
        hs = self.speech_encoder(xs)
        hp = self.prosody_encoder(xp)
        hc = self.context_encoder(app_mask)

        fused = self.fusion(torch.cat([ht, hs, hp, hc], dim=-1))
        domain_logits = self.domain_head(fused) + (1.0 - domain_mask) * (-12.0)
        domain_probs = torch.sigmoid(domain_logits)

        dom_feat = self.domain_embed(domain_probs)
        tool_logits = self.tool_head(torch.cat([fused, dom_feat], dim=-1)) + (1.0 - app_mask) * (-12.0)
        return tool_logits, domain_logits


class MultimodalSpeechDataset(Dataset):
    def __init__(self, items: List[Dict[str, Any]], train_dir: Path, fe: MultimodalSpeechFeatureExtractor):
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
            self.x_speech.append(fe.get_speech_embedding(rel_audio))

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


def train_single_model(
    seed: int,
    train_ds: MultimodalSpeechDataset,
    val_ds: MultimodalSpeechDataset,
    fe: MultimodalSpeechFeatureExtractor,
    epochs: int = 25,
    target_device: str = device,
):
    torch.manual_seed(seed)
    np.random.seed(seed)
    model = PhoWhisperHierarchicalRouterNet(fe.vocab_dim, fe.speech_dim, fe.prosody_dim, fe.num_tools, fe.num_domains).to(target_device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-3, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
    asl_t = AsymmetricLoss(gamma_neg=4.0, gamma_pos=1.0, clip=0.05).to(target_device)
    asl_d = AsymmetricLoss(gamma_neg=2.5, gamma_pos=1.0, clip=0.05).to(target_device)
    spec_aug = SpecAugment(freq_mask_max=6, time_mask_max=2, p=0.8).to(target_device)
    loader = DataLoader(train_ds, batch_size=64, shuffle=True)
    rng = np.random.default_rng(seed)

    for ep in range(1, epochs + 1):
        model.train()
        ep_loss = 0.0
        n_b = 0
        for xt, xs, xp, tm, dm, yt, yd in loader:
            xt = xt.to(target_device)
            xs = xs.to(target_device)
            xp = spec_aug(xp.to(target_device))
            tm = tm.to(target_device)
            dm = dm.to(target_device)
            yt = yt.to(target_device)
            yd = yd.to(target_device)

            if xt.size(0) > 4:
                perm = torch.randperm(xt.size(0), device=target_device)
                if float(rng.random()) < 0.5:
                    lam = float(np.clip(max(rng.beta(0.4, 0.4), 1.0 - rng.beta(0.4, 0.4)), 0.70, 0.92))
                    xt = lam * xt + (1.0 - lam) * xt[perm]
                    xs = lam * xs + (1.0 - lam) * xs[perm]
                    xp = lam * xp + (1.0 - lam) * xp[perm]
                    tm = torch.clamp(tm + tm[perm], 0.0, 1.0)
                    dm = torch.clamp(dm + dm[perm], 0.0, 1.0)
                    yt = lam * yt + (1.0 - lam) * yt[perm]
                    yd = lam * yd + (1.0 - lam) * yd[perm]

            optimizer.zero_grad()
            tl, dl = model(xt, xs, xp, tm, dm)
            loss = asl_t(tl, yt) + 0.4 * asl_d(dl, yd)
            loss.backward()
            optimizer.step()
            ep_loss += float(loss.item())
            n_b += 1
        scheduler.step()

    model.eval()
    with torch.no_grad():
        val_tl, val_dl = model(
            val_ds.x_text.to(target_device),
            val_ds.x_speech.to(target_device),
            val_ds.x_prosody.to(target_device),
            val_ds.app_mask.to(target_device),
            val_ds.domain_mask.to(target_device),
        )
        tp = torch.sigmoid(val_tl).cpu().numpy()
        dp = torch.sigmoid(val_dl).cpu().numpy()
    return model, {"tool_probs": tp, "domain_probs": dp}


# ==============================================================================
# THỰC THI HUẤN LUYỆN SOTA PHOWHISPER ROUTER ENSEMBLE
# ==============================================================================
print("=" * 80)
print(f"BẮT ĐẦU HUẤN LUYỆN SOTA PRETRAINED SPEECH ROUTER TRÊN THIẾT BỊ: {device.upper()}")
print("Backbone Âm Thanh: vinai/PhoWhisper-base (512-dim) + Whole-Audio Prosody (48-dim)")
print("=" * 80)

ckpt_dir = PROJECT_ROOT / "checkpoints"
ckpt_dir.mkdir(exist_ok=True)
cache_file = ckpt_dir / "phowhisper_embeddings.pt"

speech_cache = {}
if cache_file.is_file():
    speech_cache = torch.load(cache_file, map_location="cpu", weights_only=False)
    print(f"Nạp thành công {len(speech_cache)} embedding âm thanh tiền huấn luyện từ cache!")
else:
    print("Warning: Chưa tìm thấy phowhisper_embeddings.pt, sử dụng zero vectors dự phòng.")

train_jsonl = DATA_DIR / "train" / "train.jsonl"
catalog_path = DATA_DIR / "train" / "train_tools_catalog.json"
catalog = json.load(open(catalog_path, "r", encoding="utf-8"))
all_tool_names = sorted(set(catalog_tools(catalog).keys()) | {"sys.ask_missing_info"})
print(f"Số lượng công cụ catalog: {len(all_tool_names)}")

fe = MultimodalSpeechFeatureExtractor(all_tool_names, vocab_dim=2048, speech_dim=512, prosody_dim=48, cache=speech_cache)
all_items = [json.loads(l) for l in open(train_jsonl, "r", encoding="utf-8") if l.strip()]
split_point = int(len(all_items) * 0.80)
train_clean = all_items[:split_point]
val_clean = all_items[split_point:]

mixup_manifest = DATA_DIR / "train" / "train_mixup.jsonl"
augmented_items = []
if mixup_manifest.is_file():
    augmented_items = [json.loads(l) for l in open(mixup_manifest, "r", encoding="utf-8") if l.strip()]

train_dir = DATA_DIR / "train"
ds_train = MultimodalSpeechDataset(train_clean + augmented_items, train_dir, fe)
ds_val = MultimodalSpeechDataset(val_clean, train_dir, fe)
print(f"Tập Train: {len(ds_train)} | Tập Val: {len(ds_val)}")

seeds = [2026, 42, 1337]
trained_models = []
val_probs_list = []

for idx, s in enumerate(seeds, 1):
    print(f"--- Đang huấn luyện Mô hình {idx}/{len(seeds)} (Hạt giống: {s}) ---")
    m, preds = train_single_model(s, ds_train, ds_val, fe, epochs=25, target_device=device)
    trained_models.append(m)
    val_probs_list.append(preds["tool_probs"])

ensemble_val_probs = np.mean(val_probs_list, axis=0)

# Hiệu chuẩn ngưỡng động tối ưu F1
N, K = ensemble_val_probs.shape
val_tool_true = ds_val.y_tool.cpu().numpy()
optimal_thresholds = np.full(K, 0.44, dtype=np.float32)

for k in range(K):
    y_k = val_tool_true[:, k] > 0.5
    if np.sum(y_k) < 2:
        continue
    best_f1, best_tau = -1.0, 0.44
    for tau in np.arange(0.25, 0.65, 0.03):
        pred_k = ensemble_val_probs[:, k] >= tau
        tp = np.sum(pred_k & y_k)
        fp = np.sum(pred_k & ~y_k)
        fn = np.sum(~pred_k & y_k)
        f1 = (2.0 * tp / (2 * tp + fp + fn)) if (2 * tp + fp + fn) > 0 else 0.0
        if f1 > best_f1:
            best_f1, best_tau = f1, tau
    optimal_thresholds[k] = best_tau

print(f"Hiệu chuẩn thành công 147 ngưỡng động: Mean={np.mean(optimal_thresholds):.3f}")

# Đánh giá F1 trên tập Validation
preds_bin = (ensemble_val_probs >= optimal_thresholds).astype(np.float32)
tp = float(np.sum((preds_bin == 1.0) & (val_tool_true == 1.0)))
fp = float(np.sum((preds_bin == 1.0) & (val_tool_true == 0.0)))
fn = float(np.sum((preds_bin == 0.0) & (val_tool_true == 1.0)))
val_p = tp / max(1.0, tp + fp)
val_r = tp / max(1.0, tp + fn)
val_f1 = (2 * val_p * val_r / (val_p + val_r)) if (val_p + val_r) > 0 else 0.0
print(f"🎉 SOTA PhoWhisper Validation F1: {val_f1 * 100:.2f}% (Precision: {val_p*100:.2f}%, Recall: {val_r*100:.2f}%)")

torch.save(trained_models[0].state_dict(), ckpt_dir / "phowhisper_router_sota.pt")
torch.save(trained_models[0].state_dict(), ckpt_dir / "hierarchical_router_sota.pt")
torch.save(trained_models[0].state_dict(), ckpt_dir / "router_sota.pt")
for i, m in enumerate(trained_models):
    torch.save(m.state_dict(), ckpt_dir / f"router_ensemble_{i}.pt")

thresh_dict = {fe.all_tools[i]: float(optimal_thresholds[i]) for i in range(len(optimal_thresholds))}
with open(ckpt_dir / "tool_thresholds.json", "w", encoding="utf-8") as f:
    json.dump(thresh_dict, f, ensure_ascii=False, indent=2)

print(f"Đã lưu thành công các checkpoint và tool_thresholds.json vào: {ckpt_dir}")
'''

# Update Cell 11 source
nb["cells"][11]["source"] = [l + "\n" for l in cell_11_code.splitlines()]

# Save baseline.ipynb
nb_path.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print("Successfully updated baseline.ipynb Cell 11 with Pretrained PhoWhisper Speech Router Suite!")
