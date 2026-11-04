"""ZAC 2026 - LifeMate Baseline Agent

Architecture & Execution Pipeline:
1. Input Audio / Text: Voice input (.wav 16kHz) transcribed via ASR or direct text.
2. Context & Environment: Sample-specific context (current_time, timezone, user_profile, installed_apps).
3. Tool Intent & Argument Resolution:
   - Heuristic / Rule-based Pattern Matching (fast, offline, zero-dependency).
   - Extensible LLM Agent Interface (OpenAI / vLLM / Ollama / Transformers compatible).
4. Tool Execution & State Transition: Calls executed sequentially on zaic_tools.ToolEnv.
5. Submission Generation: Produces submission.jsonl with (id, tool_calls, state_hash).
"""

from __future__ import annotations

import argparse
import copy
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

# Add zaic_tools paths
PROJECT_ROOT = Path(__file__).resolve().parent
TRAIN_ROOT = PROJECT_ROOT / "train+public_test" / "train"
TEST_ROOT = PROJECT_ROOT / "train+public_test" / "public_test"

if str(TRAIN_ROOT) not in sys.path:
    sys.path.insert(0, str(TRAIN_ROOT))

from zaic_tools import ToolEnv, schema_validate  # noqa: E402
from zaic_tools.utils import state_hash  # noqa: E402


# ==============================================================================
# 1. ASR Component (Speech-to-Text)
# ==============================================================================
class SimpleASR:
    """ASR handler with fallback support for pre-extracted transcriptions."""

    def __init__(self, model_name: Optional[str] = None, device: str = "cpu"):
        self.model_name = model_name
        self.device = device
        self._pipe = None

    def load_model(self):
        """Lazy load HuggingFace Whisper pipeline if needed."""
        if self._pipe is None and self.model_name:
            try:
                from transformers import pipeline

                print(f"Loading ASR model {self.model_name} on {self.device}...")
                self._pipe = pipeline(
                    "automatic-speech-recognition",
                    model=self.model_name,
                    device=self.device,
                )
            except Exception as e:
                print(f"Warning: Failed to load ASR pipeline ({e}). Fallback to text.")

    def transcribe(self, audio_path: Path, fallback_text: str = "") -> str:
        """Transcribe audio file or return fallback_text if available."""
        if fallback_text:
            return fallback_text
        if self._pipe is not None and audio_path.is_file():
            try:
                res = self._pipe(str(audio_path))
                return res.get("text", "").strip()
            except Exception as e:
                print(f"ASR error on {audio_path}: {e}")
        return ""


# ==============================================================================
# 2. Vietnamese DateTime Resolver
# ==============================================================================
class DateTimeResolver:
    """Helper to resolve relative Vietnamese date and time expressions against current_time."""

    @staticmethod
    def parse_current_time(current_time_str: str) -> datetime:
        # e.g. "2026-11-10T08:15:00+07:00"
        time_part = current_time_str[:19]
        return datetime.fromisoformat(time_part)

    @classmethod
    def resolve_datetime(
        cls, text: str, current_time_str: str, tz_offset: str = "+07:00"
    ) -> Optional[str]:
        now = cls.parse_current_time(current_time_str)
        target_date = now.date()

        text_lower = text.lower()

        # Date offsets
        if "ngày mai" in text_lower or "sáng mai" in text_lower or "tối mai" in text_lower or "chiều mai" in text_lower or "mai" in text_lower:
            target_date = target_date + timedelta(days=1)
        elif "ngày kia" in text_lower:
            target_date = target_date + timedelta(days=2)
        elif "hôm nay" in text_lower or "tối nay" in text_lower or "chiều nay" in text_lower:
            target_date = target_date

        # Explicit day number (e.g. "ngày 19")
        day_match = re.search(r"ngày\s+(\d{1,2})", text_lower)
        if day_match:
            try:
                d = int(day_match.group(1))
                target_date = target_date.replace(day=d)
            except Exception:
                pass

        # Time resolution
        hour = 7
        minute = 0

        # Pattern: 5 rưỡi / 5h30 / 5:30
        rưỡi_match = re.search(r"(\d{1,2})\s*(?:giờ|h)?\s*rưỡi", text_lower)
        colon_match = re.search(r"(\d{1,2})[:h](\d{2})", text_lower)
        hour_match = re.search(r"(\d{1,2})\s*(?:giờ|h)", text_lower)

        if rưỡi_match:
            hour = int(rưỡi_match.group(1))
            minute = 30
        elif colon_match:
            hour = int(colon_match.group(1))
            minute = int(colon_match.group(2))
        elif hour_match:
            hour = int(hour_match.group(1))
            minute = 0
        elif "tám rưỡi" in text_lower:
            hour = 8
            minute = 30
        elif "tám giờ" in text_lower:
            hour = 8
            minute = 0
        elif "sáu rưỡi" in text_lower:
            hour = 6
            minute = 30
        elif "sáu giờ" in text_lower:
            hour = 6
            minute = 0
        elif "năm rưỡi" in text_lower:
            hour = 5
            minute = 30
        elif "năm giờ" in text_lower:
            hour = 5
            minute = 0
        elif "bảy giờ" in text_lower:
            hour = 7
            minute = 0

        # PM / Evening adjustment
        if ("tối" in text_lower or "chiều" in text_lower) and hour < 12:
            hour += 12

        dt = datetime(target_date.year, target_date.month, target_date.day, hour, minute, 0)
        return dt.isoformat() + tz_offset


# ==============================================================================
# 3. Baseline Agents
# ==============================================================================
class BaseAgent:
    """Abstract base class for LifeMate agents."""

    def predict(self, item: Dict[str, Any], env: Any) -> List[Dict[str, Any]]:
        raise NotImplementedError


class HeuristicBaselineAgent(BaseAgent):
    """Rule-based baseline agent mapping Vietnamese voice requests to tool calls."""

    def __init__(self):
        self.time_resolver = DateTimeResolver()

    def predict(self, item: Dict[str, Any], env: Any) -> List[Dict[str, Any]]:
        text = item.get("audio_text", "").lower()
        context = item.get("context", {})
        now_str = context.get("current_time", "2026-11-10T08:00:00+07:00")
        allowed = env.allowed
        states = env.states

        calls = []

        # ------------------------------------------------------------------
        # 1. Weather Intent
        # ------------------------------------------------------------------
        if "weather.get_forecast" in allowed:
            if any(w in text for w in ["thời tiết", "mưa", "nhiệt độ", "dự báo"]):
                target_date = self.time_resolver.parse_current_time(now_str).date()
                if "mai" in text:
                    target_date = target_date + timedelta(days=1)
                date_str = target_date.isoformat()
                # Execute read call immediately to inform downstream actions
                res = env.call("weather.get_forecast", {"date": date_str})
                calls.append({"name": "weather.get_forecast", "arguments": {"date": date_str}})

        # ------------------------------------------------------------------
        # 2. Smart Home Intent (Lights, Fans, Status)
        # ------------------------------------------------------------------
        if "smart_home.light_set" in allowed:
            sh_state = states.get("smart_home", {})
            lights = [d for d in sh_state.get("devices", []) if d.get("type") == "light"]
            if lights:
                target_device = lights[0]["id"]
                # Match room / device name in text
                for d in lights:
                    name = d.get("name", "").lower()
                    room = d.get("room", "").lower()
                    if (name and name in text) or (room and room in text):
                        target_device = d["id"]
                        break

                if any(w in text for w in ["bật đèn", "mở đèn", "bật ánh sáng"]):
                    env.call("smart_home.light_set", {"device_id": target_device, "power": "on"})
                    calls.append({"name": "smart_home.light_set", "arguments": {"device_id": target_device, "power": "on"}})
                elif any(w in text for w in ["tắt đèn", "đóng đèn"]):
                    env.call("smart_home.light_set", {"device_id": target_device, "power": "off"})
                    calls.append({"name": "smart_home.light_set", "arguments": {"device_id": target_device, "power": "off"}})

        if "smart_home.fan_set" in allowed:
            sh_state = states.get("smart_home", {})
            fans = [d for d in sh_state.get("devices", []) if d.get("type") == "fan"]
            if fans:
                dev_id = fans[0]["id"]
                if any(w in text for w in ["bật quạt", "mở quạt"]):
                    env.call("smart_home.fan_set", {"device_id": dev_id, "power": "on"})
                    calls.append({"name": "smart_home.fan_set", "arguments": {"device_id": dev_id, "power": "on"}})
                elif any(w in text for w in ["tắt quạt"]):
                    env.call("smart_home.fan_set", {"device_id": dev_id, "power": "off"})
                    calls.append({"name": "smart_home.fan_set", "arguments": {"device_id": dev_id, "power": "off"}})

        if "smart_home.get_status" in allowed and not calls:
            if any(w in text for w in ["trạng thái nhà", "kiểm tra nhà", "các thiết bị"]):
                env.call("smart_home.get_status", {})
                calls.append({"name": "smart_home.get_status", "arguments": {}})

        # ------------------------------------------------------------------
        # 3. Alarm Intent
        # ------------------------------------------------------------------
        if "alarm.create" in allowed:
            if any(w in text for w in ["báo thức", "đặt báo thức", "hẹn giờ"]):
                resolved_time = self.time_resolver.resolve_datetime(text, now_str)
                if resolved_time:
                    args = {"time": resolved_time}
                    v = env.validate("alarm.create", args)
                    if v.get("ok"):
                        env.call("alarm.create", args)
                        calls.append({"name": "alarm.create", "arguments": args})

        if "alarm.list" in allowed and "danh sách báo thức" in text:
            env.call("alarm.list", {})
            calls.append({"name": "alarm.list", "arguments": {}})

        # ------------------------------------------------------------------
        # 4. Reminders Intent
        # ------------------------------------------------------------------
        if "reminders.create" in allowed:
            if any(w in text for w in ["nhắc tôi", "nhắc nhở", "nhớ nhắc"]):
                resolved_time = self.time_resolver.resolve_datetime(text, now_str)
                content = "lịch nhắc"
                m = re.search(r"nhắc\s+(?:tôi|mình|dùm chị|giúp)?\s*(.*?)(?:\s+lúc|\s+vào|\s+nhé|\.|$)", text)
                if m and m.group(1).strip():
                    content = m.group(1).strip()
                args = {"content": content, "time": resolved_time or now_str}
                v = env.validate("reminders.create", args)
                if v.get("ok"):
                    env.call("reminders.create", args)
                    calls.append({"name": "reminders.create", "arguments": args})

        # ------------------------------------------------------------------
        # 5. Contacts Search Intent
        # ------------------------------------------------------------------
        if "contacts.search" in allowed:
            contact_match = re.search(r"(?:nhắn|gọi|hỏi|báo cho)\s+(?:sếp|anh|chị|bạn|bố|mẹ)?\s*([A-ZÀ-Ỹa-zà-ỹ0-9\s]+)", text)
            if contact_match and not any(c["name"] == "contacts.search" for c in calls):
                query = contact_match.group(1).strip().split()[0] if contact_match.group(1) else ""
                if query and query not in ["tôi", "mình", "ai"]:
                    env.call("contacts.search", {"query": query})
                    calls.append({"name": "contacts.search", "arguments": {"query": query}})

        # ------------------------------------------------------------------
        # 6. Missing Info / Meta Fallback (sys.ask_missing_info)
        # ------------------------------------------------------------------
        if "phone.call" in allowed and "sys.ask_missing_info" in allowed:
            if any(w in text for w in ["gọi cho", "gọi điện"]) and not any(c["name"] == "phone.call" for c in calls):
                args = {"tool_name": "phone.call", "params": ["contact_id"]}
                env.call("sys.ask_missing_info", args)
                calls.append({"name": "sys.ask_missing_info", "arguments": args})

        return calls


class LLMBaselineAgent(BaseAgent):
    """Prompt-based LLM Agent template for tool-calling models (Qwen, Llama, PhoGPT, Ollama)."""

    def __init__(self, api_url: Optional[str] = None, model_name: str = "qwen2.5-coder"):
        self.api_url = api_url
        self.model_name = model_name

    def format_prompt(self, item: Dict[str, Any], allowed_tools: List[Dict[str, Any]]) -> str:
        text = item.get("audio_text", "")
        context = item.get("context", {})
        return (
            f"Bối cảnh người dùng:\n"
            f"- Thời gian hiện tại: {context.get('current_time')}\n"
            f"- Địa điểm: {context.get('location')}\n"
            f"- Danh sách tool được phép gọi: {[t['name'] for t in allowed_tools]}\n\n"
            f"Lịch sử hội thoại: {json.dumps(item.get('history', []), ensure_ascii=False)}\n\n"
            f"Yêu cầu người dùng: {text}\n\n"
            f"Hãy đưa ra chuỗi tool_calls định dạng JSON list: [{{\"name\": \"...\", \"arguments\": {{...}}}}, ...]"
        )

    def predict(self, item: Dict[str, Any], env: Any) -> List[Dict[str, Any]]:
        # In this template, fallback to heuristic or call external API
        heuristic = HeuristicBaselineAgent()
        return heuristic.predict(item, env)


# ==============================================================================
# 4. Evaluation & Submission Generation
# ==============================================================================
def evaluate_agent(
    agent: BaseAgent,
    data_path: Path,
    split: str = "train",
    max_samples: Optional[int] = None,
) -> Dict[str, float]:
    """Evaluate agent against ground truth labels in train.jsonl."""
    print(f"\n--- Evaluating Agent on {split} ({data_path}) ---")
    correct_hash = 0
    total = 0
    total_calls_pred = 0
    total_calls_target = 0
    exact_tool_names = 0

    with open(data_path, encoding="utf-8") as f:
        for idx, line in enumerate(f):
            if not line.strip():
                continue
            if max_samples and idx >= max_samples:
                break

            item = json.loads(line)
            sample_id = item["id"]

            # 1. Oracle environment: compute target state hash
            oracle_env = ToolEnv(split, sample_id, root=PROJECT_ROOT / "train+public_test")
            for call in item["label"]["tool_calls"]:
                oracle_env.call(call["name"], call.get("arguments", {}))
            target_hash = oracle_env.get_state_hash()
            target_tools = [c["name"] for c in item["label"]["tool_calls"]]

            # 2. Prediction environment: run agent
            pred_env = ToolEnv(split, sample_id, root=PROJECT_ROOT / "train+public_test")
            agent.predict(item, pred_env)
            pred_hash = pred_env.get_state_hash()
            pred_calls = pred_env.get_tool_calls()
            pred_tools = [c["name"] for c in pred_calls]

            # 3. Metrics
            if pred_hash == target_hash:
                correct_hash += 1
            if pred_tools == target_tools:
                exact_tool_names += 1

            total_calls_pred += len(pred_calls)
            total_calls_target += len(target_tools)
            total += 1

            if total % 100 == 0:
                print(f"Evaluated {total} samples | Current State Hash Accuracy: {correct_hash/total*100:.2f}%")

    acc = correct_hash / total if total > 0 else 0.0
    tool_acc = exact_tool_names / total if total > 0 else 0.0

    print("\n--- Evaluation Results ---")
    print(f"Total samples evaluated: {total}")
    print(f"State Hash Accuracy: {acc*100:.2f}% ({correct_hash}/{total})")
    print(f"Exact Tool Match:    {tool_acc*100:.2f}% ({exact_tool_names}/{total})")
    print(f"Total Calls (Pred / Target): {total_calls_pred} / {total_calls_target}")

    return {"accuracy": acc, "tool_accuracy": tool_acc, "total": total}


def generate_submission(
    agent: BaseAgent,
    test_jsonl: Path,
    output_path: Path,
    split: str = "public_test",
) -> None:
    """Run agent on test split and generate valid submission.jsonl."""
    print(f"\n--- Generating Submission for {split} -> {output_path} ---")
    data_root = PROJECT_ROOT / "train+public_test"
    count = 0

    with open(test_jsonl, encoding="utf-8") as fin, open(output_path, "w", encoding="utf-8") as fout:
        for line in fin:
            if not line.strip():
                continue
            item = json.loads(line)
            sample_id = item["id"]

            env = ToolEnv(split, sample_id, root=data_root)
            agent.predict(item, env)

            record = {
                "id": sample_id,
                "tool_calls": env.get_tool_calls(),
                "state_hash": env.get_state_hash(),
            }
            fout.write(json.dumps(record, ensure_ascii=False) + "\n")
            count += 1

    print(f"Wrote {count} lines to {output_path}.")

    # Validate output schema using zaic_tools validator
    print("Running schema validation on submission...")
    from zaic_tools.executor import Executor

    executor = Executor(
        str(data_root / split / f"{split}_environment"),
        str(data_root / split / f"{split}_tools_catalog.json"),
    )
    all_calls = []
    with open(output_path, encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            all_calls.extend(rec.get("tool_calls", []))

    val_res = schema_validate(all_calls, executor.catalog)
    errors = [v for v in val_res if not v.get("ok")]
    print(f"Validation finished: {len(all_calls)} tool calls checked, {len(errors)} schema errors.")
    if errors:
        print("First 3 errors:", errors[:3])
    else:
        print("Submission is 100% valid and ready for leaderboard!")


# ==============================================================================
# 5. Main CLI Entry Point
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(description="ZAC 2026 LifeMate Baseline")
    parser.add_argument("--evaluate", action="store_true", help="Evaluate baseline on train split")
    parser.add_argument("--predict", action="store_true", help="Generate submission for public_test")
    parser.add_argument("--max-samples", type=int, default=200, help="Max samples for evaluation (default: 200)")
    parser.add_argument("--output", type=str, default="submission.jsonl", help="Output submission path")
    args = parser.parse_args()

    agent = HeuristicBaselineAgent()

    if args.evaluate or (not args.evaluate and not args.predict):
        train_file = PROJECT_ROOT / "train+public_test" / "train" / "train.jsonl"
        evaluate_agent(agent, train_file, split="train", max_samples=args.max_samples)

    if args.predict:
        test_file = PROJECT_ROOT / "train+public_test" / "public_test" / "public_test.jsonl"
        out_file = PROJECT_ROOT / args.output
        generate_submission(agent, test_file, out_file, split="public_test")


if __name__ == "__main__":
    main()
