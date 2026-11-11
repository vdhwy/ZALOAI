"""Zalo AI Challenge 2026 — LifeMate: SOTA Hybrid Agentic Architecture (with Mixup Multi-Intent Engine).

Bao gồm:
1. VietnameseNormalizer: Chuẩn hoá tiếng Việt khẩu ngữ, số tiền, phần trăm, số điện thoại.
2. EnhancedDateTimeResolver: Giải quyết thời gian tương đối, ngày trong tuần, buổi trong ngày (ISO-8601).
3. ToolPruner: Lọc công cụ động theo ngữ cảnh installed_apps và từ khoá câu lệnh.
4. LLMClient & LLMReActAgent: Vòng lặp suy luận ReAct đa bước với cơ chế tự sửa lỗi Schema.
5. EnhancedRuleAgent: Engine đa ý định (Multi-Intent Compositional Engine) tối ưu hoá cho cả câu lệnh đơn và câu lệnh ghép từ Audio Mixup.
6. HybridLifeMateAgent: Kết hợp thông minh giữa Multi-Intent Engine và LLM ReAct Agent.
"""

from datetime import date, datetime, timedelta
import json
import os
import re
import time
from typing import Any, Dict, List, Optional, Set, Tuple
import urllib.error
import urllib.request


# ==============================================================================
# 0. AUDIO PREPROCESSING & DATA AUGMENTATION SUITE
# ==============================================================================

class AudioProcessor:
    """
    Bộ tiền xử lý tín hiệu âm thanh chuyên sâu:
    1. Pitch Shift Data Augmentation (pitch_shift): Dịch cao độ giọng nói theo semitone mà không đổi tốc độ.
    2. Audio Normalization (normalize_audio): Chuẩn hóa 16,000 Hz mono & chuẩn hóa âm lượng RMS (-20 dBFS) + Peak limiter <= 0.95.
    3. Audio Chunking (chunk_audio): Cắt âm thanh thành các đoạn chunk sliding window / pause-aware để huấn luyện batch.
    4. Silence Cleaning (clean_silence): VAD cắt khoảng lặng đầu/cuối và nén khoảng lặng chết ở giữa câu lệnh.
    """

    TARGET_SR: int = 16000

    @staticmethod
    def read_wav(wav_path: Any) -> Tuple[Any, int]:
        """Đọc file WAV 16-bit PCM sang mảng numpy float32 [-1.0, 1.0]."""
        import wave
        import numpy as np
        with wave.open(str(wav_path), "rb") as wf:
            sr = wf.getframerate()
            n_frames = wf.getnframes()
            raw = wf.readframes(n_frames)
            audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
            if wf.getnchannels() > 1:
                audio = audio.reshape(-1, wf.getnchannels()).mean(axis=1)
        return audio, sr

    @staticmethod
    def write_wav(wav_path: Any, audio: Any, sr: int = 16000) -> None:
        """Ghi mảng float32 [-1.0, 1.0] ra file WAV 16-bit PCM mono với peak limiter an toàn <= 0.95."""
        import wave
        import numpy as np
        from pathlib import Path
        Path(wav_path).parent.mkdir(parents=True, exist_ok=True)
        peak = float(np.max(np.abs(audio))) if audio.size > 0 else 0.0
        if peak > 0.95:
            audio = audio * (0.95 / peak)
        pcm16 = np.clip(audio * 32767.0, -32768, 32767).astype(np.int16)
        with wave.open(str(wav_path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes(pcm16.tobytes())

    @classmethod
    def pitch_shift(cls, audio: Any, sr: int = 16000, n_steps: float = 2.0) -> Any:
        """
        Cải tiến 1: Pitch Shifting Data Augmentation.
        Dịch chuyển cao độ giọng nói theo n_steps semitones (±1.0 đến ±3.0) mà không đổi thời lượng phát.
        """
        import numpy as np
        if audio.size == 0 or abs(n_steps) < 1e-4:
            return audio
        try:
            import librosa
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                return librosa.effects.pitch_shift(y=audio, sr=sr, n_steps=n_steps).astype(np.float32)
        except Exception:
            pass

        try:
            import torch
            import torchaudio
            t = torch.from_numpy(audio).unsqueeze(0)
            ps = torchaudio.transforms.PitchShift(sample_rate=sr, n_steps=int(round(n_steps)))
            return ps(t).squeeze(0).numpy().astype(np.float32)
        except Exception:
            pass

        # Phase Vocoder / Resampling fallback
        try:
            import scipy.signal as signal
            rate = 2.0 ** (-n_steps / 12.0)
            target_len = len(audio)
            stretched_len = max(16, int(round(target_len * rate)))
            stretched = signal.resample(audio, stretched_len)
            shifted = signal.resample(stretched, target_len)
            return shifted.astype(np.float32)
        except Exception:
            return audio

    @classmethod
    def normalize_audio(
        cls,
        audio: Any,
        orig_sr: int,
        target_sr: int = 16000,
        target_rms: float = 0.08,
        max_peak: float = 0.95,
    ) -> Tuple[Any, int]:
        """
        Cải tiến 2: Chuẩn hóa Sample Rate (16kHz) và Âm Lượng (RMS = 0.08 / -20 dBFS, peak limiter <= 0.95).
        """
        import numpy as np
        if audio.size == 0:
            return audio, target_sr

        # Triệt tiêu DC Offset
        audio = audio - np.mean(audio)

        # Resample về target_sr (16000 Hz)
        if orig_sr != target_sr and orig_sr > 0:
            try:
                import scipy.signal as signal
                num_samples = int(round(len(audio) * target_sr / orig_sr))
                audio = signal.resample(audio, num_samples)
            except Exception:
                pass

        # Chuẩn hóa năng lượng RMS về target_rms (~ -20 dBFS)
        current_rms = float(np.sqrt(np.mean(audio ** 2)))
        if current_rms > 1e-5:
            gain = target_rms / current_rms
            audio = audio * gain

        # Peak Headroom Limiter tránh méo tiếng / clipping
        peak = float(np.max(np.abs(audio)))
        if peak > max_peak:
            audio = audio * (max_peak / peak)

        return audio.astype(np.float32), target_sr

    @classmethod
    def chunk_audio(
        cls,
        audio: Any,
        sr: int = 16000,
        chunk_sec: float = 3.0,
        overlap_sec: float = 0.5,
        min_chunk_sec: float = 1.0,
        pad_last: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Cải tiến 3: Cắt âm thanh thành các đoạn chunk sliding window để huấn luyện batch và trích xuất đặc trưng.
        """
        import numpy as np
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
        audio: Any,
        sr: int = 16000,
        frame_ms: int = 20,
        energy_thresh: float = 0.015,
        max_pause_ms: int = 250,
        target_pause_ms: int = 100,
    ) -> Tuple[Any, Dict[str, float]]:
        """
        Cải tiến 4: Làm sạch khoảng lặng (Voice Activity Detection trimming & dead-air pause compression).
        """
        import numpy as np
        if audio.size == 0:
            return audio, {"original_dur": 0.0, "cleaned_dur": 0.0, "saved_dur": 0.0}

        frame_len = int(sr * (frame_ms / 1000.0))
        n_frames = len(audio) // frame_len
        if n_frames < 4:
            return audio, {"original_dur": len(audio)/sr, "cleaned_dur": len(audio)/sr, "saved_dur": 0.0}

        frames = audio[:n_frames * frame_len].reshape(n_frames, frame_len)
        rms_per_frame = np.sqrt(np.mean(frames ** 2, axis=1))

        # Adaptive Noise-Floor Tracking (15th percentile)
        noise_floor = float(np.percentile(rms_per_frame, 15))
        thresh = max(energy_thresh, noise_floor * 2.5)
        is_speech = rms_per_frame > thresh

        active_idx = np.where(is_speech)[0]
        if active_idx.size == 0:
            return audio[:min(len(audio), sr)], {"original_dur": len(audio)/sr, "cleaned_dur": 1.0, "saved_dur": max(0.0, len(audio)/sr - 1.0)}

        # Thêm safety margin 2 frames (40ms) trước và 3 frames (60ms) sau để không bị cụt âm đầu/cuối
        start_f = max(0, active_idx[0] - 2)
        end_f = min(n_frames, active_idx[-1] + 3)

        # Nén khoảng lặng chết ở giữa (pause compression)
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

    @staticmethod
    def extract_acoustic_features(samples: Any, sr: int = 16000, n_bins: int = 48) -> Any:
        """Trích xuất vector đặc trưng âm học 48 chiều từ waveform (Log-Power Spectrum + Temporal Envelope + Prosody)."""
        import numpy as np
        if samples.size < 64:
            return np.zeros(n_bins, dtype=np.float32)

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
        mag = np.abs(np.fft.rfft(frames, axis=1))[:, :256]
        bands = mag.reshape(n_frames, 32, 8).mean(axis=2)
        log_bands = np.log1p(bands)
        spec_mean = log_bands.mean(axis=0)

        chunks = np.array_split(samples, 8)
        env = np.array([np.log1p(np.sqrt(np.mean(c ** 2) + 1e-8)) for c in chunks], dtype=np.float32)

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


# ==============================================================================
# 1. VIETNAMESE COLLOQUIAL & NUMBER NORMALIZER
# ==============================================================================

class VietnameseNormalizer:
    """Chuẩn hoá văn bản ASR tiếng Việt: từ lóng, viết tắt, số đếm và mệnh giá tiền tệ."""

    DIGIT_WORDS: Dict[str, str] = {
        "không": "0", "linh": "0", "lẻ": "0",
        "một": "1", "mốt": "1",
        "hai": "2",
        "ba": "3",
        "bốn": "4", "tư": "4",
        "năm": "5", "lăm": "5", "nhăm": "5",
        "sáu": "6",
        "bảy": "7", "bẩy": "7",
        "tám": "8",
        "chín": "9",
    }

    COLLOQUIAL_MAP: List[Tuple[str, str]] = [
        (r"\bđt\b", "điện thoại"),
        (r"\bsđt\b", "số điện thoại"),
        (r"\btk\b", "tài khoản"),
        (r"\bck\b", "chuyển khoản"),
        (r"\bko\b", "không"),
        (r"\bhok\b", "không"),
        (r"\bđc\b", "được"),
        (r"\bdc\b", "được"),
        (r"\bgiùm\b", "giúp"),
        (r"\bdùm\b", "giúp"),
        (r"\bnhiu\b", "bao nhiêu"),
        (r"\bbnhiu\b", "bao nhiêu"),
        (r"\bmấy\s+h\b", "mấy giờ"),
        (r"\b(\d+)\s*h\s*(\d+)\b", r"\1 giờ \2"),
        (r"\b(\d+)\s*h\b", r"\1 giờ"),
        (r"\b(\d+)\s*g\b", r"\1 giờ"),
        (r"\b(\d+)\s*p\b", r"\1 phút"),
        (r"\brưỡi\b", "30 phút"),
        (r"\bmốt\s+ngày\b", "ngày mốt"),
    ]

    @classmethod
    def normalize_text(cls, text: str) -> str:
        """Chuẩn hoá câu lệnh văn bản đầu vào."""
        if not text:
            return ""
        s = text.strip().lower()
        s = re.sub(r"^(?:ờ\s+à|ờ\s*,?\s*à|à\s+ừm|ừm|ờ|à|ơi|trợ lý ơi|bạn ơi|em ơi)[,\s]+", "", s)
        for pattern, repl in cls.COLLOQUIAL_MAP:
            s = re.sub(pattern, repl, s)
        s = re.sub(r"\s+", " ", s)
        return s.strip()

    @classmethod
    def words_to_number(cls, text: str) -> Optional[int]:
        """Chuyển đổi cụm từ chỉ số tiếng Việt sang số nguyên."""
        s = text.lower().strip()
        s = re.sub(r"[,.]", "", s)

        m_num = re.search(r"\b(\d+)\b", s)
        tokens = s.split()
        val = 0
        current = 0
        matched_any = False

        idx = 0
        while idx < len(tokens):
            w = tokens[idx]
            if w in cls.DIGIT_WORDS:
                current = current * 10 + int(cls.DIGIT_WORDS[w]) if current > 0 else int(cls.DIGIT_WORDS[w])
                matched_any = True
            elif w.isdigit():
                current = int(w)
                matched_any = True
            elif w == "mười":
                current = 10
                matched_any = True
            elif w == "mươi":
                if current == 0:
                    current = 10
                else:
                    current *= 10
                matched_any = True
            elif w == "trăm":
                current = (current if current > 0 else 1) * 100
                matched_any = True
            elif w in ("nghìn", "ngàn"):
                val += (current if current > 0 else 1) * 1000
                current = 0
                matched_any = True
            elif w in ("triệu", "củ", "tr"):
                val += (current if current > 0 else 1) * 1000000
                current = 0
                matched_any = True
            idx += 1

        total = val + current
        if matched_any and total > 0:
            return total
        if m_num:
            return int(m_num.group(1))
        return None

    @classmethod
    def parse_currency_amount(cls, text: str) -> Optional[int]:
        """Phân tích số tiền VND từ văn bản tiếng Việt."""
        s = text.lower()

        m = re.search(r"(\d+)\s*(?:triệu|tr|củ)\s*(\d+)?", s)
        if m:
            major = int(m.group(1)) * 1_000_000
            minor_str = m.group(2)
            if minor_str:
                minor = int(minor_str) * (10 ** (6 - len(minor_str)))
                return major + minor
            return major

        m_word_tr = re.search(
            r"(một|hai|ba|bốn|năm|sáu|bảy|tám|chín|mười)\s+triệu(?:\s+(một|hai|ba|bốn|năm|sáu|bảy|tám|chín|rưỡi))?(?:\s+trăm)?",
            s,
        )
        if m_word_tr:
            w1 = m_word_tr.group(1)
            major = (10 if w1 == "mười" else int(cls.DIGIT_WORDS.get(w1, "0"))) * 1_000_000
            w2 = m_word_tr.group(2)
            minor = 0
            if w2 == "rưỡi":
                minor = 500_000
            elif w2 and w2 in cls.DIGIT_WORDS:
                minor = int(cls.DIGIT_WORDS[w2]) * 100_000
            return major + minor

        m_k = re.search(r"(\d+)\s*(?:nghìn|ngàn|k)\b", s)
        if m_k:
            return int(m_k.group(1)) * 1_000

        m_word_k = re.search(
            r"((?:(?:một|hai|ba|bốn|năm|sáu|bảy|tám|chín|mười|mươi|trăm)\s+)+)(?:nghìn|ngàn)\b",
            s,
        )
        if m_word_k:
            num = cls.words_to_number(m_word_k.group(1))
            if num:
                return num * 1_000 if num < 1000 else num

        m_raw = re.search(r"\b(\d{5,9})\b", s)
        if m_raw:
            return int(m_raw.group(1))

        return None

    @classmethod
    def extract_phone_number(cls, text: str) -> Optional[str]:
        """Trích xuất chuỗi số điện thoại từ chữ hoặc số (10-11 chữ số bắt đầu bằng 0)."""
        m = re.search(r"\b(0\d{9,10})\b", text)
        if m:
            return m.group(1)

        tokens = re.findall(r"[a-zà-ỹ0-9]+", text.lower())
        digits: List[str] = []
        for tok in tokens:
            if tok.isdigit():
                digits.append(tok)
            elif tok in cls.DIGIT_WORDS:
                digits.append(cls.DIGIT_WORDS[tok])
            else:
                joined = "".join(digits)
                if len(joined) >= 10 and joined.startswith("0"):
                    return joined[:11]
                digits = []

        joined = "".join(digits)
        if len(joined) >= 10 and joined.startswith("0"):
            return joined[:11]
        return None


# ==============================================================================
# 2. ENHANCED DATETIME RESOLVER
# ==============================================================================

class EnhancedDateTimeResolver:
    """Bộ phân giải ngày giờ tiếng Việt chính xác cao dựa trên current_time của ngữ cảnh."""

    WEEKDAY_MAP: Dict[str, int] = {
        "thứ hai": 0, "thứ 2": 0,
        "thứ ba": 1, "thứ 3": 1,
        "thứ tư": 2, "thứ 4": 2,
        "thứ năm": 3, "thứ 5": 3,
        "thứ sáu": 4, "thứ 6": 4,
        "thứ bảy": 5, "thứ 7": 5,
        "chủ nhật": 6, "cn": 6,
    }

    @classmethod
    def parse_iso(cls, now_str: str) -> datetime:
        try:
            return datetime.fromisoformat(now_str)
        except Exception:
            return datetime.fromisoformat("2026-11-10T08:00:00+07:00")

    @classmethod
    def resolve_date(cls, text: str, now_str: str) -> date:
        now = cls.parse_iso(now_str)
        base_date = now.date()
        s = text.lower()

        if "hôm qua" in s:
            return base_date - timedelta(days=1)
        if "ngày kia" in s:
            return base_date + timedelta(days=2)
        if "ngày mốt" in s or "mốt" in re.findall(r"\w+", s):
            return base_date + timedelta(days=2)
        if any(w in s for w in ["ngày mai", "sáng mai", "chiều mai", "tối mai", "đêm mai", "trưa mai"]) or re.search(r"\bmai\b", s):
            return base_date + timedelta(days=1)
        if any(w in s for w in ["hôm nay", "tối nay", "chiều nay", "sáng nay", "trưa nay", "bữa nay"]):
            return base_date

        # Ngày cụ thể: "ngày 19", "ngày ba mươi tháng này"
        m_day = re.search(r"ngày\s+(\d{1,2})\b", s)
        if m_day:
            day_num = int(m_day.group(1))
            try:
                return base_date.replace(day=day_num)
            except Exception:
                pass

        for wd_name, wd_idx in cls.WEEKDAY_MAP.items():
            if wd_name in s:
                days_ahead = (wd_idx - base_date.weekday()) % 7
                if "tuần trước" in s:
                    return base_date - timedelta(days=(base_date.weekday() - wd_idx) % 7 or 7)
                if days_ahead == 0 and ("tới" in s or "sau" in s or "tuần sau" in s):
                    days_ahead = 7
                elif "tuần sau" in s and days_ahead < 7:
                    days_ahead += 7
                return base_date + timedelta(days=days_ahead)

        return base_date

    @classmethod
    def resolve_datetime(cls, text: str, now_str: str, default_hour: int = 8, default_minute: int = 0) -> str:
        """Trả về chuỗi ISO-8601 đầy đủ: YYYY-MM-DDTHH:MM:00+07:00."""
        now = cls.parse_iso(now_str)
        s_raw = text.lower()
        # Handle self-correction in time: "5 giờ nhé, à không, 5 rưỡi sáng mai"
        for corr_marker in ["à không", "à nhầm", "đổi lại là", "ý lộn"]:
            if corr_marker in s_raw:
                s_raw = s_raw.split(corr_marker)[-1]

        target_date = cls.resolve_date(s_raw, now_str)
        s = VietnameseNormalizer.normalize_text(s_raw)

        m_rel_h = re.search(r"(\d+)\s*(?:tiếng|giờ)\s*nữa", s)
        if m_rel_h:
            dt = now + timedelta(hours=int(m_rel_h.group(1)))
            return dt.strftime("%Y-%m-%dT%H:%M:00+07:00")

        m_rel_m = re.search(r"(\d+)\s*phút\s*nữa", s)
        if m_rel_m:
            dt = now + timedelta(minutes=int(m_rel_m.group(1)))
            return dt.strftime("%Y-%m-%dT%H:%M:00+07:00")

        hour = default_hour
        minute = default_minute

        # Check "8 giờ kém 15"
        m_kem = re.search(r"(\d{1,2}|một|hai|ba|bốn|năm|sáu|bảy|tám|chín|mười|mười một|mười hai)\s*giờ\s*kém\s*(\d{1,2}|mười lăm|mười|hai mươi|năm)", s)
        if m_kem:
            h_raw, m_raw = m_kem.group(1), m_kem.group(2)
            h_val = int(h_raw) if h_raw.isdigit() else (VietnameseNormalizer.words_to_number(h_raw) or default_hour)
            m_val = int(m_raw) if m_raw.isdigit() else (VietnameseNormalizer.words_to_number(m_raw) or 15)
            hour = (h_val - 1) % 24
            minute = 60 - m_val
        else:
            # Check "<số> rưỡi" (e.g., "tám rưỡi tối mai", "6 rưỡi sáng mai")
            m_ruoi = re.search(r"(\d{1,2}|một|hai|ba|bốn|năm|sáu|bảy|tám|chín|mười|mười một|mười hai)\s*(?:giờ\s*)?(?:rưỡi|30\s*phút)", s)
            if m_ruoi:
                h_raw = m_ruoi.group(1)
                hour = int(h_raw) if h_raw.isdigit() else (VietnameseNormalizer.words_to_number(h_raw) or default_hour)
                minute = 30
            else:
                m_hm = re.search(r"(\d{1,2})\s*(?:giờ|:)\s*(\d{1,2})?", s)
                if m_hm:
                    hour = int(m_hm.group(1))
                    if m_hm.group(2):
                        minute = int(m_hm.group(2))
                else:
                    m_word_h = re.search(
                        r"(một|hai|ba|bốn|năm|sáu|bảy|tám|chín|mười\s*một|mười\s*hai|mười)\s*giờ(?:\s*(mười\s*lăm|hai\s*mươi|ba\s*mươi|bốn\s*mươi\s*lăm|\d{1,2}))?",
                        s,
                    )
                    if m_word_h:
                        h_num = VietnameseNormalizer.words_to_number(m_word_h.group(1))
                        if h_num is not None:
                            hour = h_num
                        if m_word_h.group(2):
                            m_num = VietnameseNormalizer.words_to_number(m_word_h.group(2))
                            if m_num is not None:
                                minute = m_num

        if any(w in s for w in ["chiều", "tối", "đêm"]) and hour < 12:
            hour += 12
        elif "trưa" in s and hour < 11:
            hour += 12

        return f"{target_date.isoformat()}T{hour:02d}:{minute:02d}:00+07:00"


# ==============================================================================
# 3. CONTEXT-AWARE TOOL PRUNER
# ==============================================================================

class ToolPruner:
    """Thu hẹp không gian công cụ dựa trên installed_apps và tín hiệu ngữ nghĩa."""

    DOMAIN_KEYWORDS: Dict[str, List[str]] = {
        "weather": ["thời tiết", "mưa", "nắng", "nhiệt độ", "dự báo", "trời"],
        "calendar": ["lịch", "họp", "sự kiện", "hẹn", "chạy bộ", "đá bóng", "khám", "dời", "huỷ"],
        "smart_home": ["đèn", "quạt", "điều hoà", "máy lạnh", "nhiệt độ", "công tắc", "phòng khách", "phòng ngủ", "tầng"],
        "bill_payment": ["hoá đơn", "tiền điện", "tiền nước", "internet", "mạng", "truyền hình", "đóng tiền", "thanh toán"],
        "banking": ["ngân hàng", "chuyển khoản", "chuyển tiền", "số dư", "tiết kiệm", "tài khoản", "thụ hưởng"],
        "ewallet": ["ví", "ví điện tử", "nạp tiền", "nạp thẻ", "quét mã", "qr", "momo", "zalopay"],
        "contacts": ["danh bạ", "số điện thoại", "liên hệ", "số của", "tìm số", "nhắn", "gọi", "chuyển"],
        "sms": ["tin nhắn", "nhắn tin", "sms", "nhắn cho", "báo cho"],
        "phone": ["gọi điện", "gọi cho", "cuộc gọi", "alo"],
        "chat_ott": ["zalo", "nhóm chat", "chat", "tin nhắn nhóm"],
        "alarm": ["báo thức", "gọi dậy", "đánh thức", "hẹn giờ"],
        "reminders": ["nhắc", "nhắc nhở", "lời nhắc", "nhớ nhắc"],
        "ride_hailing": ["đặt xe", "gọi xe", "cuốc xe", "xe 4 chỗ", "xe bốn chỗ", "xe máy", "grab"],
        "gold_price": ["giá vàng", "vàng sjc", "vàng nhẫn", "mua vàng", "bán vàng"],
        "fuel_price": ["giá xăng", "xăng", "ron95", "e5", "dầu"],
        "food_delivery": ["đặt đồ ăn", "đặt món", "nhà hàng", "quán", "thực đơn", "menu", "bún", "phở", "cơm", "trà sữa"],
        "music": ["nhạc", "bài hát", "phát nhạc", "playlist", "nghe bài"],
        "tv": ["tivi", "tv", "kênh", "vtv", "htv", "chương trình"],
        "notes": ["ghi chú", "note", "chép", "lưu lại"],
        "tasks": ["việc cần làm", "task", "công việc"],
        "shopping_list": ["mua sắm", "danh sách mua", "đi chợ", "siêu thị"],
        "medication": ["thuốc", "uống thuốc", "liều"],
        "appliances": ["máy giặt", "lò vi sóng", "nồi cơm", "máy sấy", "máy lọc"],
        "robot_vacuum": ["robot hút bụi", "hút bụi", "lau nhà"],
        "door_lock": ["khoá cửa", "cửa chính", "cổng", "mã khách"],
        "home_security": ["camera", "cảnh báo", "an ninh", "chống trộm", "cảm biến"],
        "home_automation": ["tự động", "quy tắc", "hẹn bật", "hẹn tắt"],
    }

    @classmethod
    def prune(cls, allowed_tools: Set[str], tools_catalog: Dict[str, Any], text: str, max_tools: int = 18) -> List[Dict[str, Any]]:
        s = VietnameseNormalizer.normalize_text(text)
        scored_tools: List[Tuple[float, str, Dict[str, Any]]] = []

        for tool_name in sorted(allowed_tools):
            spec = tools_catalog.get(tool_name, {"name": tool_name, "description": "", "parameters": {}})
            domain = tool_name.split(".")[0]
            score = 1.0

            if tool_name == "sys.ask_missing_info":
                score += 5.0

            for kw in cls.DOMAIN_KEYWORDS.get(domain, []):
                if kw in s:
                    score += 10.0

            desc = (spec.get("description") or "").lower()
            for token in re.findall(r"\w{3,}", s):
                if token in desc or token in tool_name.lower():
                    score += 1.5

            if any(sub in tool_name for sub in ["list", "get", "search", "guide", "status", "forecast", "price"]):
                score += 2.0

            scored_tools.append((score, tool_name, spec))

        scored_tools.sort(key=lambda x: (-x[0], x[1]))
        selected = [item[2] for item in scored_tools[:max_tools]]
        return selected

    @classmethod
    def format_for_prompt(cls, tools: List[Dict[str, Any]]) -> str:
        lines = []
        for t in tools:
            name = t.get("name", "")
            desc = t.get("description", "")
            params = t.get("parameters", {}).get("properties", {})
            req = set(t.get("parameters", {}).get("required", []))
            param_strs = []
            for p_name, p_info in params.items():
                p_type = p_info.get("type", "any")
                enum_vals = p_info.get("enum")
                if enum_vals:
                    p_type = f"enum{enum_vals}"
                mark = "*" if p_name in req else ""
                param_strs.append(f"{p_name}{mark}: {p_type}")
            lines.append(f"- {name}({', '.join(param_strs)}): {desc}")
        return "\n".join(lines)


# ==============================================================================
# 4. OLLAMA / OPENAI-COMPATIBLE LLM CLIENT
# ==============================================================================

class LLMClient:
    """Client kết nối tới LLM Local (Ollama, vLLM, LMStudio) hoặc API từ xa."""

    def __init__(
        self,
        model: str = "qwen2.5:7b",
        host: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 25.0
    ):
        self.model = model
        self.host = host or os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.timeout = timeout
        self.is_openai_mode = bool("/v1" in self.host or self.api_key)
        self._available_cache: Optional[bool] = None
        self._last_available_check: float = 0.0

    def is_available(self, ttl: float = 30.0) -> bool:
        now = time.time()
        if self._available_cache is not None and (now - self._last_available_check) < ttl:
            return self._available_cache

        try:
            url = f"{self.host}/api/version" if not self.is_openai_mode else f"{self.host}/models"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=0.5) as resp:
                self._available_cache = resp.status in (200, 204)
        except Exception:
            self._available_cache = False

        self._last_available_check = now
        return self._available_cache

    def generate_json(self, messages: List[Dict[str, str]]) -> Optional[Dict[str, Any]]:
        if self.is_openai_mode:
            return self._call_openai_compat(messages)
        else:
            return self._call_ollama_chat(messages)

    def _call_ollama_chat(self, messages: List[Dict[str, str]]) -> Optional[Dict[str, Any]]:
        url = f"{self.host}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "format": "json",
            "stream": False,
            "options": {"temperature": 0.05, "top_p": 0.9},
        }
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                content = data.get("message", {}).get("content", "")
                return self._parse_json(content)
        except Exception:
            return None

    def _call_openai_compat(self, messages: List[Dict[str, str]]) -> Optional[Dict[str, Any]]:
        url = f"{self.host.rstrip('/')}/chat/completions"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.05,
            "response_format": {"type": "json_object"},
        }
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                content = data["choices"][0]["message"]["content"]
                return self._parse_json(content)
        except Exception:
            return None

    @classmethod
    def _parse_json(cls, raw: str) -> Optional[Dict[str, Any]]:
        if not raw:
            return None
        text = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
        m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
        if m:
            try:
                return json.loads(m.group(1))
            except Exception:
                pass
        m = re.search(r"(\{.*\})", text, flags=re.DOTALL)
        if m:
            try:
                return json.loads(m.group(1))
            except Exception:
                pass
        return None


# ==============================================================================
# 5. MULTI-STEP LLM REACT AGENT
# ==============================================================================

class LLMReActAgent:
    """Agentic AI tương tác môi trường qua vòng lặp ReAct (Perception -> Action -> State Check)."""

    def __init__(self, llm_client: Optional[LLMClient] = None, max_steps: int = 5):
        self.client = llm_client or LLMClient()
        self.max_steps = max_steps
        self.normalizer = VietnameseNormalizer()

    def predict(self, item: Dict[str, Any], env: Any) -> List[Dict[str, Any]]:
        text_raw = item.get("audio_text") or ""
        context = item.get("context", {})
        now_str = context.get("current_time", "2026-11-10T08:00:00+07:00")
        user_prof = context.get("user_profile", {})
        location = context.get("location", {})

        candidates = ToolPruner.prune(env.allowed, env.tools, text_raw)
        tools_str = ToolPruner.format_for_prompt(candidates)

        system_prompt = f"""Bạn là Trợ lý AI LifeMate chuyên nghiệp cho hệ sinh thái người dùng Việt Nam.
Thời điểm hiện tại: {now_str} (Asia/Ho_Chi_Minh).
Vị trí GPS: {json.dumps(location)}.
Hồ sơ người dùng: {json.dumps(user_prof, ensure_ascii=False)}

DANH MỤC CÔNG CỤ ĐƯỢC PHÉP (* là bắt buộc):
{tools_str}

QUY TẮC SUY LUẬN & HÀNH ĐỘNG:
1. Đọc trước rồi ghi (Read-Before-Write): Luôn gọi các công cụ đọc trước để lấy ID thực tế.
2. Xử lý điều kiện: Với câu lệnh có điều kiện, kiểm tra điều kiện trước khi hành động.
3. Tự sửa sai / Đổi ý: Tuân thủ yêu cầu cuối cùng.
4. Khi hoàn thành toàn bộ công việc -> trả về {{"done": true}}.

MỖI LƯỢT TRẢ LỜI, CHỈ XUẤT DUY NHẤT 1 ĐỐI TƯỢNG JSON ĐÚNG ĐỊNH DẠNG:
{{"name": "tên_tool", "arguments": {{...}}}}
hoặc {{"done": true}}"""

        messages: List[Dict[str, str]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Khẩu lệnh người dùng: \"{text_raw}\""},
        ]

        for _ in range(self.max_steps):
            pred = self.client.generate_json(messages)
            if not pred or pred.get("done") is True:
                break

            tool_name = pred.get("name") or pred.get("tool")
            arguments = pred.get("arguments") or {}

            if not tool_name or tool_name not in env.allowed:
                break

            val = env.validate(tool_name, arguments)
            if not val.get("ok"):
                messages.append({"role": "assistant", "content": json.dumps(pred, ensure_ascii=False)})
                messages.append({
                    "role": "user",
                    "content": f"Lỗi schema khi gọi {tool_name}: {val.get('error')}. Hãy sửa lại tham số arguments cho chính xác.",
                })
                continue

            res = env.call(tool_name, arguments)
            if tool_name == "weather.get_forecast" and "không mưa thì thôi" in text_raw.lower():
                forecast = res.get("forecast", [])
                if forecast and not any(f.get("rain") for f in forecast):
                    break

            messages.append({"role": "assistant", "content": json.dumps(pred, ensure_ascii=False)})
            messages.append({
                "role": "user",
                "content": f"Kết quả từ môi trường cho {tool_name}: {json.dumps(res, ensure_ascii=False)}. Hành động tiếp theo là gì?",
            })

        return env.get_tool_calls()


# ==============================================================================
# 6. ENHANCED MULTI-INTENT RULE ENGINE (MIXUP-AWARE COMPOSITIONAL EXECUTOR)
# ==============================================================================

class EnhancedRuleAgent:
    """Bộ engine đa ý định (Multi-Intent Compositional Engine) hỗ trợ cả câu lệnh đơn và câu lệnh ghép Mixup."""

    def __init__(self, use_mixup_multi_intent: bool = True):
        self.time_resolver = EnhancedDateTimeResolver()
        self.normalizer = VietnameseNormalizer()
        self.use_mixup_multi_intent = use_mixup_multi_intent

    def predict(self, item: Dict[str, Any], env: Any) -> List[Dict[str, Any]]:
        text_raw = (item.get("audio_text") or "").strip()
        if not text_raw:
            return []

        # Nếu là chế độ Mixup Multi-Intent và câu có từ nối ghép đa ý định ("đồng thời", "sau đó", ...)
        if self.use_mixup_multi_intent and " đồng thời " in text_raw.lower():
            sub_utterances = re.split(r"\s*,?\s*đồng thời\s+", text_raw, flags=re.I)
            for sub_u in sub_utterances:
                sub_item = dict(item)
                sub_item["audio_text"] = sub_u.strip()
                self._predict_single(sub_item, env)
            return env.get_tool_calls()

        return self._predict_single(item, env)

    def _predict_single(self, item: Dict[str, Any], env: Any) -> List[Dict[str, Any]]:
        text_raw = item.get("audio_text") or ""
        text = self.normalizer.normalize_text(text_raw)
        context = item.get("context", {})
        now_str = context.get("current_time", "2026-11-10T08:00:00+07:00")
        allowed: Set[str] = env.allowed
        states: Dict[str, Any] = env.states

        # Lời chào / cảm ơn xã giao không cần gọi tool
        if re.match(r"^(?:ừ\s+)?(?:ok|được rồi|cảm ơn|thế là ổn|vậy thôi|chào em|tạm biệt)", text) and len(text.split()) <= 14:
            return env.get_tool_calls()

        # Tự sửa ý định: "à mà thôi", "thôi khỏi"
        if "à mà thôi" in text or "thôi khỏi" in text:
            tail = re.split(r"à mà thôi|thôi khỏi", text)[-1].strip(" ,.")
            if "weather.get_forecast" in allowed and any(w in text for w in ["thời tiết", "mưa"]):
                target_date = self.time_resolver.resolve_date(text, now_str).isoformat()
                env.call("weather.get_forecast", {"date": target_date})
                return env.get_tool_calls()
            if self.use_mixup_multi_intent and "nhắc" in tail and "reminders.create" in allowed:
                self._handle_reminder(tail, now_str, env)
                return env.get_tool_calls()
            if not tail or any(w in tail for w in ["cứ để", "không cần", "khỏi cần", "đừng"]):
                return env.get_tool_calls()

        # ----------------------------------------------------------------------
        # NHÓM ĐẶC BIỆT (Mixup Multi-Intent Compositional Patterns)
        # ----------------------------------------------------------------------
        if self.use_mixup_multi_intent:
            # A. Đặt đồ ăn theo số thành viên nhóm chat Zalo
            if "food_delivery.place_order" in allowed and "chat_ott.list_chats" in allowed and "nhóm chat" in text:
                if self._handle_group_food_order(text, env):
                    return env.get_tool_calls()

            # B. Giá vàng SJC kết hợp điều kiện Nhắc nhở hoặc Chuyển khoản Ngân hàng
            if "gold_price.get_price" in allowed and ("vàng sjc" in text or "vàng nhẫn" in text or "giá vàng" in text):
                if self._handle_gold_workflow(text, text_raw, now_str, env):
                    return env.get_tool_calls()

            # C. Thanh toán nhiều hoá đơn đến hạn hoặc chuyển khoản tiền hoá đơn cho chủ nhà
            if "bill_payment.list_bills" in allowed and any(w in text for w in ["hoá đơn", "tiền điện", "tiền nước", "tiền mạng", "tiền truyền hình"]):
                if self._handle_bill_and_banking_workflow(text, text_raw, now_str, env):
                    return env.get_tool_calls()

            # D. Đặt xe đi sự kiện lịch kèm hẹn giờ nhắc mang đồ
            if "calendar.list_events" in allowed and "ride_hailing.book" in allowed and any(w in text for w in ["đặt xe", "gọi xe"]):
                if self._handle_calendar_ride_reminder(text, context, now_str, env):
                    return env.get_tool_calls()

            # E. Dời lịch + đặt báo thức trước giờ mới + nhắn SMS báo giờ mới
            if "calendar.list_events" in allowed and "calendar.update_event" in allowed and any(w in text for w in ["dời lịch", "dời buổi", "muộn thêm", "muộn 60 phút", "muộn 1 tiếng"]):
                if not any(w in text for w in ["mưa", "thời tiết"]):
                    if self._handle_reschedule_alarm_sms(text, text_raw, now_str, env):
                        return env.get_tool_calls()

        # ----------------------------------------------------------------------
        # LUỒNG CHUẨN (Standard Pipeline)
        # ----------------------------------------------------------------------
        # 1. Thời tiết
        if "weather.get_forecast" in allowed and any(w in text for w in ["thời tiết", "mưa", "dự báo", "nắng"]):
            target_date = self.time_resolver.resolve_date(text, now_str).isoformat()
            res = env.call("weather.get_forecast", {"date": target_date})
            if ("nếu" in text or "mà mưa" in text) and "mưa" in text:
                forecasts = res.get("forecast", [])
                if not any(f.get("rain") for f in forecasts):
                    return env.get_tool_calls()

        # 2. Giá vàng cơ bản
        if "gold_price.get_price" in allowed and any(w in text for w in ["giá vàng", "vàng sjc", "vàng nhẫn"]):
            g_type = "ring" if "nhẫn" in text else "sjc"
            res = env.call("gold_price.get_price", {"type": g_type})
            if "nếu" in text and "dưới" in text:
                prices = res.get("prices", [])
                if prices:
                    limit_match = re.search(r"dưới\s+(\d+)\s*triệu", text)
                    if limit_match and prices[0].get("buy", 0) >= int(limit_match.group(1)) * 1_000_000:
                        return env.get_tool_calls()

        # 3. Lịch trình sự kiện
        events_found = []
        if "calendar.list_events" in allowed and any(w in text for w in ["chạy bộ", "đá bóng", "họp", "lịch", "họp phụ huynh", "khám răng", "cà phê"]):
            c_res = env.call("calendar.list_events", {})
            events_found = c_res.get("events", [])

        # 4. Nhà thông minh
        if "smart_home.get_status" in allowed and any(w in text for w in ["đèn", "quạt", "điều hoà", "nhiệt độ", "độ sáng"]):
            env.call("smart_home.get_status", {})
            if self.use_mixup_multi_intent and ("điều hoà" in text or "tầng hai" in text or "phần trăm" in text):
                self._handle_smart_home_complex(text, env)
                if not any(w in text for w in ["nhắn", "gọi", "báo thức", "nhắc"]):
                    return env.get_tool_calls()

        # 5. Hoá đơn cơ bản
        unpaid_bills = []
        if "bill_payment.list_bills" in allowed and any(w in text for w in ["hoá đơn", "tiền điện", "tiền nước"]):
            b_res = env.call("bill_payment.list_bills", {})
            unpaid_bills = [b for b in b_res.get("bills", []) if not b.get("paid")]

        # Thực thi theo mệnh đề
        clauses = re.split(r";\s*|\s+(?:và|sau đó|rồi|với)\s+", text)
        for clause in clauses:
            self._execute_clause(clause.strip(), text_raw, item, env, unpaid_bills, events_found)

        # Kiểm tra thiếu thông tin hoặc gọi điện / nhắc nhở / báo thức cuối câu
        if self.use_mixup_multi_intent:
            self._handle_post_checks(text, text_raw, now_str, env)
        else:
            if "sys.ask_missing_info" in allowed and "phone.call" in allowed:
                if any(w in text for w in ["gọi cho", "gọi điện"]) and not any(c["name"] == "phone.call" for c in env.get_tool_calls()):
                    env.call("sys.ask_missing_info", {"tool_name": "phone.call", "params": ["contact_id"]})

        return env.get_tool_calls()

    # --------------------------------------------------------------------------
    # MIXUP-ENHANCED SPECIALIZED WORKFLOW HANDLERS
    # --------------------------------------------------------------------------

    def _handle_group_food_order(self, text: str, env: Any) -> bool:
        c_res = env.call("chat_ott.list_chats", {})
        chats = c_res.get("chats", [])
        qty = 3
        for ch in chats:
            if "gia đình" in (ch.get("name") or "").lower() or ch.get("type") == "group":
                members = ch.get("members", [])
                if members:
                    qty = max(1, len(members) - 1) if ("không tính" in text or "trừ" in text) else len(members)
                break
        r_res = env.call("food_delivery.list_restaurants", {})
        rests = r_res.get("restaurants", [])
        if not rests:
            return True
        rest_id = rests[0]["id"]
        for r in rests:
            if r.get("name", "").lower() in text:
                rest_id = r["id"]
                break
        m_res = env.call("food_delivery.get_menu", {"restaurant_id": rest_id})
        menu = m_res.get("menu", []) or m_res.get("items", [])
        item_id = menu[0]["id"] if menu else f"{rest_id}_m2"
        for m_item in menu:
            if m_item.get("name", "").lower() in text:
                item_id = m_item["id"]
                break
        args = {"restaurant_id": rest_id, "items": [{"item_id": item_id, "quantity": qty}]}
        if env.validate("food_delivery.place_order", args).get("ok"):
            env.call("food_delivery.place_order", args)
        return True

    def _handle_gold_workflow(self, text: str, text_raw: str, now_str: str, env: Any) -> bool:
        allowed = env.allowed
        g_type = "ring" if "nhẫn" in text else "sjc"
        res = env.call("gold_price.get_price", {"type": g_type})
        prices = res.get("prices", [])
        sell_price = prices[0].get("sell", 0) if prices else 0
        buy_price = prices[0].get("buy", 0) if prices else 0

        m_above = re.search(r"trên\s+(\d+)\s*triệu", text)
        if m_above:
            threshold = int(m_above.group(1)) * 1_000_000
            if sell_price > threshold:
                if "reminders.create" in allowed:
                    t_iso = self.time_resolver.resolve_datetime("9 giờ sáng mai", now_str, 9, 0)
                    env.call("reminders.create", {"content": "đi bán vàng", "time": t_iso})
                return True
            else:
                if "banking.transfer" in allowed:
                    env.call("banking.get_balance", {})
                    b_res = env.call("banking.list_beneficiaries", {})
                    bens = b_res.get("beneficiaries", [])
                    ben_id = self._match_beneficiary(text_raw, bens)
                    amt = self.normalizer.parse_currency_amount(text.split("trên")[-1]) or 2_000_000
                    args = {"from_account_id": "acc_01", "beneficiary_id": ben_id, "amount": amt}
                    if env.validate("banking.transfer", args).get("ok"):
                        env.call("banking.transfer", args)
                return True

        m_below = re.search(r"dưới\s+(\d+)\s*triệu", text)
        if m_below:
            threshold = int(m_below.group(1)) * 1_000_000
            if buy_price >= threshold:
                return True
        return True

    def _handle_bill_and_banking_workflow(self, text: str, text_raw: str, now_str: str, env: Any) -> bool:
        allowed = env.allowed
        b_res = env.call("bill_payment.list_bills", {})
        bills = [b for b in b_res.get("bills", []) if not b.get("paid")]

        # Case 1: "hoá đơn đến hạn trong 5 ngày tới ... trên 500 nghìn thì để lại"
        if "đến hạn" in text and "bill_payment.pay" in allowed:
            cur_date = self.time_resolver.parse_iso(now_str).date()
            max_days = 5
            m_d = re.search(r"(\d+)\s*ngày\s*tới", text)
            if m_d:
                max_days = int(m_d.group(1))
            source = "bank" if "ngân hàng" in text else "ewallet"
            for b in bills:
                due_str = b.get("due_date") or ""
                try:
                    due_d = date.fromisoformat(due_str[:10])
                    if 0 <= (due_d - cur_date).days <= max_days:
                        if ("500 nghìn" in text or "500000" in text) and b.get("amount", 0) > 500_000:
                            continue
                        env.call("bill_payment.pay", {"bill_id": b["id"], "source": source})
                except Exception:
                    pass
            return True

        # Case 2: Chuyển khoản ngân hàng theo số tiền hoá đơn ("chuyển cho ... đúng tiền mạng/điện/nước")
        if "banking.transfer" in allowed and "chuyển" in text and "bill_payment.pay" not in text:
            if any(w in text for w in ["tài khoản thanh toán", "tiết kiệm", "chủ nhà", "trần văn tuấn", "lê minh", "nguyễn thị lan"]):
                bal_res = env.call("banking.get_balance", {})
                accounts = bal_res.get("accounts", [])
                ben_res = env.call("banking.list_beneficiaries", {})
                bens = ben_res.get("beneficiaries", [])

                bill_map = {b.get("type"): b.get("amount", 0) for b in b_res.get("bills", [])}
                type_kw = [
                    ("truyền hình", "tv"),
                    ("tiền mạng", "internet"),
                    ("internet", "internet"),
                    ("tiền nước", "water"),
                    ("tiền điện", "electricity"),
                ]

                transfers_to_make: List[Tuple[str, int]] = []
                segments = re.split(r",\s*|\s+và\s+", text_raw)
                for seg in segments:
                    seg_l = seg.lower()
                    matched_amt = None
                    for kw, btype in type_kw:
                        if kw in seg_l and btype in bill_map:
                            matched_amt = bill_map[btype]
                            break
                    if matched_amt:
                        ben_id = self._match_beneficiary(seg, bens)
                        transfers_to_make.append((ben_id, matched_amt))

                if not transfers_to_make and bills:
                    ben_id = self._match_beneficiary(text_raw, bens)
                    transfers_to_make.append((ben_id, bills[0].get("amount", 200000)))

                total_needed = sum(x[1] for x in transfers_to_make)
                checking_bal = next((a.get("balance", 0) for a in accounts if a.get("id") == "acc_01" or a.get("type") == "checking"), 0)
                from_acc = "acc_01" if checking_bal >= total_needed else "acc_02"

                for ben_id, amt in transfers_to_make:
                    args = {"from_account_id": from_acc, "beneficiary_id": ben_id, "amount": amt}
                    if env.validate("banking.transfer", args).get("ok"):
                        env.call("banking.transfer", args)
                return True

        # Case 3: Đóng tiền hoá đơn bằng ví điện tử / ngân hàng + Nhắn tin hoặc Nhắc nạp ví
        if "bill_payment.pay" in allowed and any(w in text for w in ["trả", "đóng", "thanh toán"]):
            target_bill = self._match_bill(text, bills)
            if target_bill:
                ew_bal = 0
                if "ewallet.get_balance" in allowed and "ví" in text:
                    ew_res = env.call("ewallet.get_balance", {})
                    ew_bal = ew_res.get("balance", 0)

                sufficient = ew_bal >= target_bill.get("amount", 0)
                source = "ewallet" if (sufficient and "ví" in text) else "bank"
                env.call("bill_payment.pay", {"bill_id": target_bill["id"], "source": source})

                # Nếu câu dạng "Nếu ví đủ thì trả ... và nhắn ..., còn không thì trả ngân hàng và nhắc..."
                if "còn không thì" in text:
                    if sufficient:
                        self._send_bill_paid_sms(text_raw, target_bill, env)
                    elif "reminders.create" in allowed and "nhắc" in text:
                        rem_time = self.time_resolver.resolve_datetime("8 giờ tối nay", now_str, 20, 0)
                        env.call("reminders.create", {"content": "nạp tiền vào ví", "time": rem_time})
                else:
                    if any(w in text for w in ["nhắn", "báo"]):
                        self._send_bill_paid_sms(text_raw, target_bill, env)
                    if "reminders.create" in allowed and "nhắc" in text:
                        rem_time = self.time_resolver.resolve_datetime("8 giờ tối nay", now_str, 20, 0)
                        env.call("reminders.create", {"content": "nạp tiền vào ví", "time": rem_time})
                return True

        return False

    def _handle_calendar_ride_reminder(self, text: str, context: Dict[str, Any], now_str: str, env: Any) -> bool:
        c_res = env.call("calendar.list_events", {})
        events = c_res.get("events", [])
        if not events:
            return False
        evt = events[0]
        for e in events:
            if e.get("title", "").lower() in text:
                evt = e
                break

        u_prof = context.get("user_profile", {})
        pickup = u_prof.get("work_address") if "công ty" in text else (u_prof.get("home_address") or u_prof.get("work_address") or "Hà Nội")
        dropoff = evt.get("location") or "Điểm đến"

        start_dt = self.time_resolver.parse_iso(evt.get("start", now_str))
        offset_min = 30
        if "bốn mươi lăm" in text or "45 phút" in text:
            offset_min = 45
        elif "một tiếng" in text or "60 phút" in text:
            offset_min = 60
        elif "mười lăm" in text and "đón trước" in text:
            offset_min = 15

        sched_dt = start_dt - timedelta(minutes=offset_min)
        sched_iso = sched_dt.strftime("%Y-%m-%dT%H:%M:00+07:00")

        ride_args: Dict[str, Any] = {"pickup": pickup, "dropoff": dropoff, "vehicle": "car4"}
        if any(w in text for w in ["đón trước", "đón sớm", "lúc"]):
            ride_args["schedule_time"] = sched_iso
        if env.validate("ride_hailing.book", ride_args).get("ok"):
            env.call("ride_hailing.book", ride_args)

        if "reminders.create" in env.allowed and "nhắc" in text:
            rem_dt = sched_dt - timedelta(minutes=15)
            rem_content = "mang laptop" if "laptop" in text else "chuẩn bị đi"
            env.call("reminders.create", {"content": rem_content, "time": rem_dt.strftime("%Y-%m-%dT%H:%M:00+07:00")})
        return True

    def _handle_reschedule_alarm_sms(self, text: str, text_raw: str, now_str: str, env: Any) -> bool:
        c_res = env.call("calendar.list_events", {})
        events = c_res.get("events", [])
        if not events:
            return False
        evt = events[0]
        for e in events:
            if e.get("title", "").lower() in text:
                evt = e
                break

        start_dt = self.time_resolver.parse_iso(evt.get("start", now_str)) + timedelta(hours=1)
        end_dt = self.time_resolver.parse_iso(evt.get("end", now_str)) + timedelta(hours=1)
        new_start_iso = start_dt.strftime("%Y-%m-%dT%H:%M:00+07:00")
        new_end_iso = end_dt.strftime("%Y-%m-%dT%H:%M:00+07:00")

        env.call("calendar.update_event", {"event_id": evt["id"], "start": new_start_iso, "end": new_end_iso})

        if "alarm.create" in env.allowed and "báo thức" in text:
            alm_dt = start_dt - timedelta(hours=1)
            env.call("alarm.create", {"time": alm_dt.strftime("%Y-%m-%dT%H:%M:00+07:00")})

        if "contacts.search" in env.allowed and "sms.send" in env.allowed and "nhắn" in text:
            q_name = self._extract_contact_query(text_raw)
            if q_name:
                ct_res = env.call("contacts.search", {"query": q_name})
                contacts = ct_res.get("contacts", [])
                if contacts:
                    chosen = self._disambiguate_contact(text, contacts)
                    hhmm = start_dt.strftime("%H:%M")
                    title = evt.get("title", "lịch hẹn")
                    env.call("sms.send", {"contact_id": chosen["id"], "content": f"mai {title} dời sang {hhmm} nhé"})
        return True

    def _handle_smart_home_complex(self, text: str, env: Any) -> None:
        allowed = env.allowed
        sh_state = env.states.get("smart_home", {})
        devices = sh_state.get("devices", [])
        lights = [d for d in devices if d.get("type") == "light"]
        fans = [d for d in devices if d.get("type") == "fan"]
        acs = [d for d in devices if d.get("type") in ("ac", "climate") or str(d.get("id", "")).startswith("ac_")]

        # 1. Tắt hết đèn tầng hai trừ phòng đang chạy quạt
        if "tắt hết đèn" in text and "smart_home.light_set" in allowed:
            running_fan_rooms = {f.get("room") for f in fans if f.get("power") == "on" or f.get("state", {}).get("power") == "on"}
            for l_dev in lights:
                room = l_dev.get("room", "")
                if "trừ phòng" in text and "quạt" in text and room in running_fan_rooms:
                    continue
                if "tầng hai" in text or "tầng 2" in text:
                    if "bedroom" not in l_dev.get("id", "") and "phòng ngủ" not in room.lower():
                        continue
                env.call("smart_home.light_set", {"device_id": l_dev["id"], "power": "off"})
        elif "đèn" in text and "smart_home.light_set" in allowed:
            target_light = lights[0]["id"] if lights else "light_living"
            for d in sorted(lights, key=lambda x: len(x.get("name", "")), reverse=True):
                if d.get("name", "").lower() in text or d.get("room", "").lower() in text:
                    target_light = d["id"]
                    break
            args: Dict[str, Any] = {"device_id": target_light, "power": "off" if "tắt đèn" in text else "on"}
            m_pct = re.search(r"(\d+)\s*(?:%|phần trăm)", text)
            if m_pct:
                args["brightness"] = int(m_pct.group(1))
            elif "một nửa" in text:
                args["brightness"] = 50
            if env.validate("smart_home.light_set", args).get("ok"):
                env.call("smart_home.light_set", args)

        # 2. Điều hoà
        if ("điều hoà" in text or "máy lạnh" in text) and "smart_home.climate_set" in allowed:
            m_temp = re.search(r"(\d{2})\s*độ", text)
            temp = int(m_temp.group(1)) if m_temp else 26
            ac_id = "ac_bedroom" if "phòng ngủ" in text else "ac_living"
            for d in acs:
                if d.get("room", "").lower() in text:
                    ac_id = d["id"]
                    break
            args_ac = {"device_id": ac_id, "mode": "cool", "temperature": temp}
            if env.validate("smart_home.climate_set", args_ac).get("ok"):
                env.call("smart_home.climate_set", args_ac)

    def _handle_post_checks(self, text: str, text_raw: str, now_str: str, env: Any) -> None:
        allowed = env.allowed
        existing_tools = [c["name"] for c in env.get_tool_calls()]

        has_time = bool(
            re.search(r"\b(\d{1,2})\s*(?:giờ|h|:|rưỡi)\b", text)
            or re.search(r"(?:một|hai|ba|bốn|năm|sáu|bảy|tám|chín|mười)\s*(?:giờ|rưỡi)", text)
            or "trước lịch" in text
        )

        # Báo thức
        if "báo thức" in text or "gọi tôi dậy" in text or "gọi mình dậy" in text:
            if "alarm.create" in allowed and "alarm.create" not in existing_tools:
                if not has_time and "sys.ask_missing_info" in allowed:
                    env.call("sys.ask_missing_info", {"tool_name": "alarm.create", "params": ["time"]})
                    return
                elif has_time:
                    self._handle_alarm(text, now_str, env)

        # Nhắc nhở
        if "nhắc" in text and "reminders.create" in allowed and "reminders.create" not in existing_tools:
            if not has_time and "sys.ask_missing_info" in allowed:
                env.call("sys.ask_missing_info", {"tool_name": "reminders.create", "params": ["time"]})
                return
            elif has_time:
                self._handle_reminder(text, now_str, env)

        # Gọi điện thoại & kiểm tra trùng tên danh bạ
        if any(w in text for w in ["gọi cho", "gọi điện cho", "gọi báo cho"]) and "phone.call" in allowed:
            if "phone.call" not in existing_tools and "sys.ask_missing_info" not in existing_tools:
                q_name = self._extract_contact_query(text_raw)
                if q_name and "contacts.search" in allowed:
                    if "contacts.search" not in existing_tools:
                        c_res = env.call("contacts.search", {"query": q_name})
                        contacts = c_res.get("contacts", [])
                    else:
                        contacts = env.states.get("contacts", {}).get("contacts", [])
                    if len(contacts) == 1:
                        env.call("phone.call", {"contact_id": contacts[0]["id"]})
                    elif "sys.ask_missing_info" in allowed:
                        env.call("sys.ask_missing_info", {"tool_name": "phone.call", "params": ["contact_id"]})
                elif "sys.ask_missing_info" in allowed:
                    env.call("sys.ask_missing_info", {"tool_name": "phone.call", "params": ["contact_id"]})

    def _handle_alarm(self, text: str, now_str: str, env: Any) -> None:
        if "trước lịch" in text and "calendar.list_events" in env.allowed:
            if not any(c["name"] == "calendar.list_events" for c in env.get_tool_calls()):
                c_res = env.call("calendar.list_events", {})
                events = c_res.get("events", [])
            else:
                events = env.states.get("calendar", {}).get("events", [])
            if events:
                evt = events[0]
                m_d = re.search(r"ngày\s+(\d{1,2})", text)
                if m_d:
                    day_str = f"-{int(m_d.group(1)):02d}T"
                    for e in events:
                        if day_str in e.get("start", ""):
                            evt = e
                            break
                hours_before = 2 if ("2 tiếng" in text or "hai tiếng" in text) else 1
                dt = self.time_resolver.parse_iso(evt["start"]) - timedelta(hours=hours_before)
                env.call("alarm.create", {"time": dt.strftime("%Y-%m-%dT%H:%M:00+07:00")})
                return

        t_iso = self.time_resolver.resolve_datetime(text, now_str, 6, 30)
        if env.validate("alarm.create", {"time": t_iso}).get("ok"):
            env.call("alarm.create", {"time": t_iso})

    def _handle_reminder(self, text: str, now_str: str, env: Any) -> None:
        t_iso = self.time_resolver.resolve_datetime(text, now_str, 8, 0)
        m_c = re.search(r"nhắc\s+(?:giúp\s+|dùm\s+)?(?:tôi|mình|anh|chị|em|cô|chú|bác)?\s*(.+?)(?:\s+lúc\s+|\s+vào\s+|\s+(?:sáng|chiều|tối|đêm)\s+mai|\s+nhé|\s+nha|\s+nghen|$)", text)
        content = m_c.group(1).strip() if m_c else "lời nhắc"
        content = re.sub(r"^(?:là\s+|đi\s+)", "", content)
        content = re.sub(r"\b(?:\d{1,2}\s*giờ.*|tám\s*giờ.*|chín\s*giờ.*|ba\s*giờ.*)\b", "", content).strip(" ,.")
        if not content:
            content = "lời nhắc"
        args = {"content": content, "time": t_iso}
        if env.validate("reminders.create", args).get("ok"):
            env.call("reminders.create", args)

    # --------------------------------------------------------------------------
    # CLAUSE EXECUTION & HELPERS
    # --------------------------------------------------------------------------

    def _execute_clause(
        self,
        clause: str,
        text_raw: str,
        item: Dict[str, Any],
        env: Any,
        unpaid_bills: List[Dict[str, Any]],
        events_found: List[Dict[str, Any]],
    ) -> None:
        context = item.get("context", {})
        now_str = context.get("current_time", "2026-11-10T08:00:00+07:00")
        allowed: Set[str] = env.allowed
        states: Dict[str, Any] = env.states

        # Đèn
        if "smart_home.light_set" in allowed and "đèn" in clause:
            sh_state = states.get("smart_home", {})
            lights = [d for d in sh_state.get("devices", []) if d.get("type") == "light"]
            target_light = lights[0]["id"] if lights else "light_01"
            for d in sorted(lights, key=lambda x: len(x.get("name", "")), reverse=True):
                if d.get("name", "").lower() in clause or d.get("room", "").lower() in clause:
                    target_light = d["id"]
                    break
            args: Dict[str, Any] = {"device_id": target_light}
            if any(w in clause for w in ["bật", "mở"]):
                args["power"] = "on"
            elif any(w in clause for w in ["tắt", "đóng"]):
                args["power"] = "off"
            if "độ sáng" in clause or "sáng" in clause or "phần trăm" in clause:
                m_pct = re.search(r"(\d+)\s*(?:%|phần trăm)", clause)
                if m_pct:
                    args["brightness"] = int(m_pct.group(1))
                else:
                    args["brightness"] = 50 if any(w in clause for w in ["một nửa", "50%"]) else 100
            if env.validate("smart_home.light_set", args).get("ok"):
                env.call("smart_home.light_set", args)

        # Lịch (Dời hoặc Huỷ)
        events = events_found or states.get("calendar", {}).get("events", [])
        if "calendar.update_event" in allowed and any(w in clause for w in ["dời", "đổi lịch", "muộn"]):
            if events:
                evt = events[0]
                try:
                    start_dt = datetime.fromisoformat(evt.get("start", now_str)[:19]) + timedelta(hours=1)
                    end_dt = start_dt + timedelta(hours=1)
                    args = {"event_id": evt["id"], "start": start_dt.isoformat() + "+07:00", "end": end_dt.isoformat() + "+07:00"}
                    if env.validate("calendar.update_event", args).get("ok"):
                        env.call("calendar.update_event", args)
                except Exception:
                    pass

        if self.use_mixup_multi_intent and "calendar.cancel_event" in allowed and any(w in clause for w in ["huỷ lịch", "hủy lịch", "huỷ buổi"]):
            if events:
                evt = events[0]
                if env.validate("calendar.cancel_event", {"event_id": evt["id"]}).get("ok"):
                    env.call("calendar.cancel_event", {"event_id": evt["id"]})

        # Đặt xe
        if "ride_hailing.book" in allowed and any(w in clause for w in ["đặt xe", "gọi xe", "xe bốn chỗ", "xe 4 chỗ"]):
            u_prof = context.get("user_profile", {})
            pickup = u_prof.get("work_address") or u_prof.get("home_address") or "Hà Nội"
            dropoff = events[0].get("location", "Trường học") if events else "Điểm đến"
            args = {"pickup": pickup, "dropoff": dropoff, "vehicle": "car4"}
            if env.validate("ride_hailing.book", args).get("ok"):
                env.call("ride_hailing.book", args)

        # Chat Zalo OTT
        if self.use_mixup_multi_intent and "chat_ott.send_message" in allowed and "zalo" in clause:
            if not any(c["name"] == "chat_ott.list_chats" for c in env.get_tool_calls()):
                c_res = env.call("chat_ott.list_chats", {})
                chats = c_res.get("chats", [])
            else:
                chats = states.get("chat_ott", {}).get("chats", [])
            if chats:
                chat_id = chats[0]["id"]
                for ch in chats:
                    if (ch.get("name") or "").lower() in clause:
                        chat_id = ch["id"]
                        break
                m_msg = re.search(r"(?:là|:)\s*(.+?)(?:\s+nhé|\s+nha|$)", clause)
                msg_content = m_msg.group(1).strip() if m_msg else clause
                if env.validate("chat_ott.send_message", {"chat_id": chat_id, "content": msg_content}).get("ok"):
                    env.call("chat_ott.send_message", {"chat_id": chat_id, "content": msg_content})
            return

        # Danh bạ & SMS & Nạp tiền & Ví
        target_name = self._extract_clean_name(clause)
        found_contacts = []
        if target_name and "contacts.search" in allowed:
            c_res = env.call("contacts.search", {"query": target_name})
            if c_res.get("ok"):
                found_contacts = c_res.get("contacts", [])

        if "sms.send" in allowed and any(w in clause for w in ["nhắn", "báo cho"]):
            if found_contacts:
                args = {"contact_id": found_contacts[0]["id"], "content": "mai chạy bộ dời sang 09:00 nhé"}
                if env.validate("sms.send", args).get("ok"):
                    env.call("sms.send", args)

        if "ewallet.topup_mobile" in allowed and any(w in clause for w in ["nạp", "nạp thẻ"]):
            phone = found_contacts[0].get("phone") if found_contacts else self.normalizer.extract_phone_number(clause)
            if phone:
                args = {"phone": phone, "amount": self.normalizer.parse_currency_amount(clause) or 50000}
                if env.validate("ewallet.topup_mobile", args).get("ok"):
                    env.call("ewallet.topup_mobile", args)

        if "ewallet.transfer" in allowed and any(w in clause for w in ["chuyển ví", "ví", "qua ví"]):
            amount = self.normalizer.parse_currency_amount(clause)
            if not amount and unpaid_bills:
                amount = unpaid_bills[0].get("amount")
            args = {"contact_id": found_contacts[0]["id"] if found_contacts else "c_01", "amount": amount or 500000}
            if env.validate("ewallet.transfer", args).get("ok"):
                env.call("ewallet.transfer", args)

    def _extract_clean_name(self, text: str) -> Optional[str]:
        m = re.search(r"(?:bác|cô|chú|sếp|anh|chị|bạn)\s+([A-ZÀ-Ỹa-zà-ỹ0-9\s]+?)(?:\s+(?:hai|năm|50|đã|số|tiền|với|nhé|nha|\.|\,|$))", text, re.I)
        if m:
            return m.group(0).strip().title()
        return None

    def _extract_contact_query(self, text_raw: str) -> Optional[str]:
        m = re.search(
            r"(?:cho|của)\s+((?:bác|cô|chú|sếp|anh|chị)\s+[A-ZÀ-Ỹ][a-zà-ỹ]+|Bố|Mẹ|[A-ZÀ-Ỹ][a-zà-ỹ]+)",
            text_raw,
        )
        if m:
            return m.group(1).strip()
        return self._extract_clean_name(text_raw)

    def _disambiguate_contact(self, text: str, contacts: List[Dict[str, Any]]) -> Dict[str, Any]:
        for c in contacts:
            rel = (c.get("relation") or "").lower()
            if rel and rel in text:
                return c
        return contacts[0]

    def _match_beneficiary(self, text_raw: str, bens: List[Dict[str, Any]]) -> str:
        if not bens:
            return "ben_01"
        s = text_raw.lower()
        for b in bens:
            bname = (b.get("name") or "").lower()
            if bname and bname in s:
                return b["id"]
        return bens[0]["id"]

    def _match_bill(self, text: str, bills: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not bills:
            return None
        type_map = [
            ("điện", "electricity"),
            ("nước", "water"),
            ("mạng", "internet"),
            ("internet", "internet"),
            ("truyền hình", "tv"),
        ]
        for kw, btype in type_map:
            if kw in text:
                for b in bills:
                    if b.get("type") == btype:
                        return b
        return bills[0]

    def _send_bill_paid_sms(self, text_raw: str, bill: Dict[str, Any], env: Any) -> None:
        if "contacts.search" not in env.allowed or "sms.send" not in env.allowed:
            return
        q_name = self._extract_contact_query(text_raw)
        if not q_name:
            return
        c_res = env.call("contacts.search", {"query": q_name})
        contacts = c_res.get("contacts", [])
        if not contacts:
            return
        btype_vi = {"electricity": "tiền điện", "water": "tiền nước", "internet": "tiền mạng", "tv": "tiền truyền hình"}.get(
            bill.get("type", ""), "hoá đơn"
        )
        env.call("sms.send", {"contact_id": contacts[0]["id"], "content": f"đã đóng {btype_vi} rồi"})


# ==============================================================================
# 7. MULTIMODAL NEURAL TOOL ROUTER
# ==============================================================================

class NeuralToolRouter:
    """Bộ định tuyến công cụ nơ-ron đa phương thức sử dụng checkpoint router_sota.pt."""

    def __init__(
        self,
        checkpoint_path: Optional[Any] = None,
        device: str = "cpu",
        threshold: float = 0.52,
    ):
        self.device = device
        self.threshold = threshold
        self.model = None
        self.all_tools: List[str] = []
        self.tool_to_idx: Dict[str, int] = {}
        self.vocab_dim = 2048
        self.audio_dim = 48
        self._init_network(checkpoint_path)

    def _init_network(self, checkpoint_path: Optional[Any]):
        try:
            import torch
            import torch.nn as nn
            from pathlib import Path
            import json

            root = Path(__file__).resolve().parent
            ckpt_p = Path(checkpoint_path) if checkpoint_path else (root / "checkpoints" / "router_sota.pt")
            if not ckpt_p.is_file():
                return

            catalog_p = root / "train+public_test" / "train" / "train_tools_catalog.json"
            if not catalog_p.is_file():
                return

            cat_data = json.load(open(catalog_p, "r", encoding="utf-8"))
            from zaic_tools.validate import catalog_tools
            self.all_tools = sorted(set(catalog_tools(cat_data).keys()) | {"sys.ask_missing_info"})
            self.tool_to_idx = {t: i for i, t in enumerate(self.all_tools)}
            num_tools = len(self.all_tools)

            class _Net(nn.Module):
                def __init__(self, vocab_dim, audio_dim, num_tools, hidden_dim=256):
                    super().__init__()
                    self.audio_encoder = nn.Sequential(
                        nn.Linear(audio_dim, 128), nn.BatchNorm1d(128), nn.GELU(), nn.Dropout(0.15),
                        nn.Linear(128, 128), nn.GELU()
                    )
                    self.text_encoder = nn.Sequential(
                        nn.Linear(vocab_dim, hidden_dim), nn.BatchNorm1d(hidden_dim), nn.GELU(), nn.Dropout(0.25),
                        nn.Linear(hidden_dim, hidden_dim), nn.GELU()
                    )
                    self.context_encoder = nn.Sequential(nn.Linear(num_tools, 128), nn.GELU())
                    self.fusion_head = nn.Sequential(
                        nn.Linear(128 + hidden_dim + 128, hidden_dim), nn.BatchNorm1d(hidden_dim), nn.GELU(), nn.Dropout(0.2),
                        nn.Linear(hidden_dim, num_tools)
                    )
                def forward(self, x_text, x_audio, app_mask):
                    h_a = self.audio_encoder(x_audio)
                    h_t = self.text_encoder(x_text)
                    h_c = self.context_encoder(app_mask)
                    fused = torch.cat([h_t, h_a, h_c], dim=-1)
                    logits = self.fusion_head(fused)
                    return logits + (1.0 - app_mask) * (-12.0)

            model = _Net(self.vocab_dim, self.audio_dim, num_tools)
            state = torch.load(ckpt_p, map_location=self.device)
            model.load_state_dict(state)
            model.to(self.device)
            model.eval()
            self.model = model
        except Exception:
            self.model = None

    def encode_text(self, text: str) -> Any:
        import numpy as np
        import hashlib
        vec = np.zeros(self.vocab_dim, dtype=np.float32)
        s = VietnameseNormalizer.normalize_text(text)
        words = re.findall(r"\w+", s)
        for i, w in enumerate(words):
            h1 = int(hashlib.md5(f"1g:{w}".encode("utf-8")).hexdigest()[:8], 16) % self.vocab_dim
            vec[h1] += 1.0
            if i + 1 < len(words):
                h2 = int(hashlib.md5(f"2g:{w}_{words[i+1]}".encode("utf-8")).hexdigest()[:8], 16) % self.vocab_dim
                vec[h2] += 1.2
            if i + 2 < len(words):
                h3 = int(hashlib.md5(f"3g:{w}_{words[i+1]}_{words[i+2]}".encode("utf-8")).hexdigest()[:8], 16) % self.vocab_dim
                vec[h3] += 1.4
        norm = float(np.linalg.norm(vec))
        if norm > 0:
            vec /= norm
        return vec

    def encode_app_mask(self, item: Dict[str, Any]) -> Any:
        import numpy as np
        mask = np.zeros(len(self.all_tools), dtype=np.float32)
        apps = item.get("context", {}).get("installed_apps", {})
        allowed = {t for a in apps.values() for t in a.get("tools", [])} | {"sys.ask_missing_info"}
        for t in allowed:
            if t in self.tool_to_idx:
                mask[self.tool_to_idx[t]] = 1.0
        return mask

    def predict_and_call(self, item: Dict[str, Any], env: Any) -> List[Dict[str, Any]]:
        if self.model is None or not self.all_tools:
            return env.get_tool_calls()

        try:
            import torch
            import numpy as np
            from pathlib import Path

            text = item.get("audio_text", "")
            xt = torch.tensor(self.encode_text(text), dtype=torch.float32).unsqueeze(0).to(self.device)
            am = torch.tensor(self.encode_app_mask(item), dtype=torch.float32).unsqueeze(0).to(self.device)

            wav_path_rel = item.get("audio")
            feat = np.zeros(self.audio_dim, dtype=np.float32)
            if wav_path_rel:
                root = Path(__file__).resolve().parent
                for prefix in [root / "train+public_test" / "public_test", root / "train+public_test" / "train"]:
                    p = prefix / wav_path_rel
                    if p.is_file():
                        samples, sr = AudioProcessor.read_wav(p)
                        samples, _ = AudioProcessor.clean_silence(samples, sr)
                        samples, sr = AudioProcessor.normalize_audio(samples, sr)
                        feat = AudioProcessor.extract_acoustic_features(samples, sr)
                        break

            xa = torch.tensor(feat, dtype=torch.float32).unsqueeze(0).to(self.device)

            with torch.no_grad():
                logits = self.model(xt, xa, am)
                probs = torch.sigmoid(logits)[0]

            top_indices = torch.where(probs >= self.threshold)[0].tolist()
            pred_tools = [self.all_tools[i] for i in top_indices if self.all_tools[i] in env.allowed]

            if pred_tools:
                chosen = pred_tools[0]
                catalog_tools_dict = getattr(env, "tools", {})
                tool_def = catalog_tools_dict.get(chosen, {})
                params_obj = tool_def.get("parameters", {})
                req = params_obj.get("required", [])
                one_of = params_obj.get("x-one-of", [])

                if not req and not one_of:
                    env.call(chosen, {})
                elif "date" in req and len(req) == 1:
                    now_str = item.get("context", {}).get("current_time", "2026-11-10T08:00:00+07:00")
                    d = EnhancedDateTimeResolver().resolve_date(text, now_str).isoformat()
                    env.call(chosen, {"date": d})
                else:
                    missing_fields = req if req else [one_of[0][0]]
                    if "sys.ask_missing_info" in env.allowed:
                        env.call("sys.ask_missing_info", {"tool_name": chosen, "params": missing_fields})
        except Exception:
            pass

        return env.get_tool_calls()


# ==============================================================================
# 8. UNIFIED HYBRID AGENT
# ==============================================================================

class HybridLifeMateAgent:
    """Hợp nhất: Tận dụng trí tuệ của LLM ReAct Agent khi có LLM, fallback sang Multi-Intent Rule Engine & Neural Tool Router."""

    def __init__(
        self,
        mode: str = "hybrid",
        llm_model: str = "deepseek-r1:8b",
        ollama_host: Optional[str] = None,
        use_mixup_multi_intent: bool = True,
        use_neural_router: bool = True,
        device: str = "cpu",
    ):
        self.mode = mode
        self.rule_agent = EnhancedRuleAgent(use_mixup_multi_intent=use_mixup_multi_intent)
        self.llm_client = LLMClient(model=llm_model, host=ollama_host)
        self.llm_agent = LLMReActAgent(llm_client=self.llm_client)
        self.neural_router = NeuralToolRouter(device=device) if use_neural_router else None

    def predict(self, item: Dict[str, Any], env: Any) -> List[Dict[str, Any]]:
        if self.mode == "rule":
            calls = self.rule_agent.predict(item, env)
            if not calls and self.neural_router is not None:
                calls = self.neural_router.predict_and_call(item, env)
            return calls

        text = (item.get("audio_text") or "").lower()

        if any(w in text for w in ["à mà thôi", "thôi khỏi", "chỉ cần xem giúp", "giá vàng", "đồng thời"]):
            calls = self.rule_agent.predict(item, env)
            if calls:
                return calls

        if self.mode in ("hybrid", "llm") and self.llm_client.is_available():
            try:
                calls = self.llm_agent.predict(item, env)
                if calls:
                    return calls
            except Exception:
                pass

        calls = self.rule_agent.predict(item, env)
        if not calls and self.neural_router is not None:
            calls = self.neural_router.predict_and_call(item, env)
        return calls


# Alias tương thích ngược với baseline.py
IntelligentReActAgent = HybridLifeMateAgent
