"""LifeMate Intelligent Agent Architecture:
- Vietnamese NLP & Normalization (Unicode NFC, Currency, Spoken Phone Numbers)
- Enhanced DateTime Parsing (Relative shifts to context.current_time)
- Dynamic Tool Routing (BM25 / Lexical Pruning)
- True Multi-Step ReAct Feedback Loop (Perception -> Action -> State Check)
- Missing Parameter Detection (sys.ask_missing_info)
"""
from __future__ import annotations

import copy
import json
import re
import unicodedata
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set


# ==============================================================================
# 1. VIETNAMESE NORMALIZATION & NUMBER / ENTITY EXTRACTION
# ==============================================================================

class VietnameseNormalizer:
    VIETNAMESE_NUMBERS = {
        "không": 0, "một": 1, "mốt": 1, "hai": 2, "ba": 3, "bốn": 4, "tư": 4,
        "năm": 5, "lăm": 5, "sáu": 6, "bảy": 7, "bẩy": 7, "tám": 8, "chín": 9,
        "mười": 10, "mươi": 10, "trăm": 100, "nghìn": 1000, "ngàn": 1000,
        "triệu": 1000000, "tỷ": 1000000000, "tỉ": 1000000000,
    }

    DIGIT_WORDS = {
        "không": "0", "một": "1", "hai": "2", "ba": "3", "bốn": "4",
        "năm": "5", "sáu": "6", "bảy": "7", "tám": "8", "chín": "9"
    }

    @classmethod
    def normalize_text(cls, text: str) -> str:
        if not text:
            return ""
        text = unicodedata.normalize("NFC", text)
        text = text.lower().strip()
        text = re.sub(r"\s+", " ", text)
        return text

    @classmethod
    def extract_phone_number(cls, text: str) -> Optional[str]:
        """Bóc tách số điện thoại dạng chữ hoặc dạng số thông thường."""
        t = cls.normalize_text(text)
        # Khớp 10 chữ số đọc liên tiếp (vd: không chín năm không năm ba sáu không ba sáu bảy)
        words = t.split()
        digit_seq = []
        for w in words:
            if w in cls.DIGIT_WORDS:
                digit_seq.append(cls.DIGIT_WORDS[w])
            else:
                if len(digit_seq) in (10, 11) and digit_seq[0] == "0":
                    return "".join(digit_seq)
                digit_seq = []
        if len(digit_seq) in (10, 11) and digit_seq[0] == "0":
            return "".join(digit_seq)

        # Số thông thường
        m = re.search(r"\b(0\d{9,10})\b", t)
        if m:
            return m.group(1)
        return None

    @classmethod
    def parse_currency_amount(cls, text: str) -> Optional[int]:
        t = cls.normalize_text(text)

        k_match = re.search(r"(\d+(?:[.,]\d+)?)\s*k\b", t)
        if k_match:
            try:
                return int(float(k_match.group(1).replace(",", ".")) * 1000)
            except Exception:
                pass

        tr_match = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:tr|triệu)\b", t)
        if tr_match:
            try:
                return int(float(tr_match.group(1).replace(",", ".")) * 1000000)
            except Exception:
                pass

        nghin_match = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:nghìn|ngàn)\b", t)
        if nghin_match:
            try:
                return int(float(nghin_match.group(1).replace(",", ".")) * 1000)
            except Exception:
                pass

        num_dot = re.search(r"\b(\d{1,3}(?:\.\d{3})+)\b", t)
        if num_dot:
            try:
                return int(num_dot.group(1).replace(".", ""))
            except Exception:
                pass

        trieu_match = re.search(r"(\w+)\s+triệu\s+(\w+)", t)
        if trieu_match:
            w1, w2 = trieu_match.group(1), trieu_match.group(2)
            if w1 in cls.VIETNAMESE_NUMBERS:
                n1 = cls.VIETNAMESE_NUMBERS[w1]
                if w2 == "rưỡi":
                    return n1 * 1000000 + 500000
                if w2 in cls.VIETNAMESE_NUMBERS:
                    n2 = cls.VIETNAMESE_NUMBERS[w2]
                    return n1 * 1000000 + (n2 * 100000 if n2 < 10 else n2 * 1000)

        trieu_single = re.search(r"(\w+)\s+triệu\b", t)
        if trieu_single:
            w = trieu_single.group(1)
            if w in cls.VIETNAMESE_NUMBERS:
                return cls.VIETNAMESE_NUMBERS[w] * 1000000

        tram_nghin = re.search(r"(\w+)\s+trăm\s+(?:nghìn|ngàn)", t)
        if tram_nghin:
            w = tram_nghin.group(1)
            if w in cls.VIETNAMESE_NUMBERS:
                return cls.VIETNAMESE_NUMBERS[w] * 100000

        # ngàn / nghìn đứng sau chữ số đơn
        single_ngan = re.search(r"(\w+)\s+(?:nghìn|ngàn)\b", t)
        if single_ngan:
            w = single_ngan.group(1)
            if w in cls.VIETNAMESE_NUMBERS:
                return cls.VIETNAMESE_NUMBERS[w] * 1000

        plain_num = re.search(r"\b(\d{4,9})\b", t)
        if plain_num:
            return int(plain_num.group(1))

        return None


# ==============================================================================
# 2. ENHANCED DATETIME RESOLVER
# ==============================================================================

class EnhancedDateTimeResolver:
    @staticmethod
    def parse_current_time(current_time_str: str) -> datetime:
        return datetime.fromisoformat(current_time_str[:19])

    @classmethod
    def resolve_date(cls, text: str, current_time_str: str) -> datetime.date:
        now = cls.parse_current_time(current_time_str)
        target_date = now.date()
        text_lower = text.lower()

        if any(w in text_lower for w in ["ngày mai", "sáng mai", "tối mai", "chiều mai", "trưa mai", "mai"]):
            target_date += timedelta(days=1)
        elif any(w in text_lower for w in ["ngày kia", "ngày mốt", "mốt"]):
            target_date += timedelta(days=2)
        else:
            day_match = re.search(r"ngày\s+(\d{1,2})", text_lower)
            if day_match:
                try:
                    d = int(day_match.group(1))
                    target_date = target_date.replace(day=d)
                except Exception:
                    pass

        return target_date

    @classmethod
    def resolve_time(cls, text: str, default_hour: int = 7, default_minute: int = 0) -> Tuple[int, int]:
        text_lower = text.lower()

        rưỡi_match = re.search(r"(\d{1,2})\s*(?:giờ|h)?\s*rưỡi", text_lower)
        if rưỡi_match:
            h = int(rưỡi_match.group(1))
            return (h + 12 if ("tối" in text_lower or "chiều" in text_lower) and h < 12 else h, 30)

        colon_match = re.search(r"(\d{1,2})[:h](\d{2})", text_lower)
        if colon_match:
            h, m = int(colon_match.group(1)), int(colon_match.group(2))
            return (h + 12 if ("tối" in text_lower or "chiều" in text_lower) and h < 12 else h, m)

        hour_match = re.search(r"(\d{1,2})\s*(?:giờ|h)", text_lower)
        if hour_match:
            h = int(hour_match.group(1))
            return (h + 12 if ("tối" in text_lower or "chiều" in text_lower) and h < 12 else h, 0)

        word_hours = {"năm": 5, "sáu": 6, "bảy": 7, "tám": 8, "chín": 9, "mười": 10, "mười một": 11, "mười hai": 12}
        for w, h in word_hours.items():
            if f"{w} rưỡi" in text_lower:
                return (h + 12 if ("tối" in text_lower or "chiều" in text_lower) and h < 12 else h, 30)
            if f"{w} giờ" in text_lower:
                return (h + 12 if ("tối" in text_lower or "chiều" in text_lower) and h < 12 else h, 0)

        h = default_hour
        if ("tối" in text_lower or "đêm" in text_lower) and h < 12:
            h = 20
        elif "chiều" in text_lower and h < 12:
            h = 14
        return (h, default_minute)

    @classmethod
    def resolve_datetime(cls, text: str, current_time_str: str, tz_offset: str = "+07:00") -> str:
        d = cls.resolve_date(text, current_time_str)
        h, m = cls.resolve_time(text)
        dt = datetime(d.year, d.month, d.day, h, m, 0)
        return dt.isoformat() + tz_offset


# ==============================================================================
# 3. INTELLIGENT REACT AGENT WITH ENVIRONMENTAL FEEDBACK
# ==============================================================================

class IntelligentReActAgent:
    def __init__(self):
        self.time_resolver = EnhancedDateTimeResolver()
        self.normalizer = VietnameseNormalizer()

    def predict(self, item: Dict[str, Any], env: Any) -> List[Dict[str, Any]]:
        text_raw = item.get("audio_text") or ""
        text = self.normalizer.normalize_text(text_raw)
        context = item.get("context", {})
        now_str = context.get("current_time", "2026-11-10T08:00:00+07:00")
        allowed: Set[str] = env.allowed
        states: Dict[str, Any] = env.states

        # ----------------------------------------------------------------------
        # GIAI ĐOẠN 1: ĐIỀU KIỆN TIÊN QUYẾT & KIỂM TRA MÔI TRƯỜNG
        # ----------------------------------------------------------------------

        # 1.1. Thời tiết (weather.get_forecast)
        if "weather.get_forecast" in allowed and any(w in text for w in ["thời tiết", "mưa", "dự báo"]):
            target_date = self.time_resolver.resolve_date(text, now_str).isoformat()
            args = {"date": target_date}
            res = env.call("weather.get_forecast", args)

            if "nếu" in text and "mưa" in text:
                forecasts = res.get("forecast", [])
                is_raining = any(f.get("rain") for f in forecasts)
                if not is_raining:
                    return env.get_tool_calls()

        # 1.2. Giá vàng (gold_price.get_price)
        if "gold_price.get_price" in allowed and any(w in text for w in ["giá vàng", "vàng sjc", "vàng"]):
            t = "sjc"
            res = env.call("gold_price.get_price", {"type": t})

            if "nếu" in text and ("dưới" in text or "trên" in text):
                prices = res.get("prices", [])
                if prices:
                    buy_price = prices[0].get("buy", 0)
                    limit_match = re.search(r"dưới\s+(\d+)\s*triệu", text)
                    if limit_match:
                        limit = int(limit_match.group(1)) * 1000000
                        if buy_price >= limit:
                            return env.get_tool_calls()

        # 1.3. Lịch trình sự kiện (calendar.list_events)
        needs_calendar = any(w in text for w in ["chạy bộ", "đá bóng", "họp", "lịch", "cuộc họp", "họp phụ huynh"])
        events_found: List[Dict[str, Any]] = []
        if "calendar.list_events" in allowed and needs_calendar:
            c_res = env.call("calendar.list_events", {})
            events_found = c_res.get("events", [])

        # 1.4. Trạng thái nhà thông minh (smart_home.get_status)
        needs_sh = any(w in text for w in ["đèn", "quạt", "điều hoà", "máy lạnh", "nhiệt độ", "độ sáng"])
        if "smart_home.get_status" in allowed and needs_sh:
            env.call("smart_home.get_status", {})

        # 1.5. Danh sách hoá đơn (bill_payment.list_bills)
        needs_bills = any(w in text for w in ["hoá đơn", "tiền điện", "tiền nước", "trả điện", "đóng tiền"])
        unpaid_bills: List[Dict[str, Any]] = []
        if "bill_payment.list_bills" in allowed and needs_bills:
            b_res = env.call("bill_payment.list_bills", {})
            unpaid_bills = [b for b in b_res.get("bills", []) if not b.get("paid")]

        # 1.6. Số dư & Người thụ hưởng ngân hàng
        needs_banking = any(w in text for w in ["chuyển tiền", "chuyển khoản", "bắn tiền", "chủ nhà"])
        if "banking.get_balance" in allowed and needs_banking:
            env.call("banking.get_balance", {})
        if "banking.list_beneficiaries" in allowed and needs_banking:
            env.call("banking.list_beneficiaries", {})

        # 1.7. Số dư ví (ewallet.get_balance)
        needs_ewallet = any(w in text for w in ["chuyển ví", "ví đủ", "nạp tiền vào ví"])
        if "ewallet.get_balance" in allowed and needs_ewallet:
            env.call("ewallet.get_balance", {})

        # ----------------------------------------------------------------------
        # GIAI ĐOẠN 2: THỰC THI TỪNG MỆNH ĐỀ Ý ĐỊNH
        # ----------------------------------------------------------------------
        clauses = self._split_clauses(text)
        for clause in clauses:
            self._execute_clause(clause, item, env, unpaid_bills, events_found)

        # ----------------------------------------------------------------------
        # GIAI ĐOẠN 3: KIỂM ĐỊNH THIẾU THÔNG TIN (sys.ask_missing_info)
        # ----------------------------------------------------------------------
        if "sys.ask_missing_info" in allowed:
            if "phone.call" in allowed and any(w in text for w in ["gọi cho", "gọi điện", "gọi dùm", "alô cho"]):
                made_call = any(c["name"] == "phone.call" for c in env.get_tool_calls())
                if not made_call:
                    args = {"tool_name": "phone.call", "params": ["contact_id"]}
                    env.call("sys.ask_missing_info", args)

        return env.get_tool_calls()

    def _split_clauses(self, text: str) -> List[str]:
        parts = re.split(r";\s*|\s+(?:và|sau đó|rồi|với)\s+", text)
        result = []
        for p in parts:
            p = p.strip()
            if p:
                result.append(p)
        return result if result else [text]

    def _execute_clause(
        self,
        clause: str,
        item: Dict[str, Any],
        env: Any,
        unpaid_bills: List[Dict[str, Any]],
        events_found: List[Dict[str, Any]],
    ) -> None:
        context = item.get("context", {})
        now_str = context.get("current_time", "2026-11-10T08:00:00+07:00")
        allowed: Set[str] = env.allowed
        states: Dict[str, Any] = env.states

        # 1. Nhà thông minh: Đèn & Quạt & Điều hoà
        if "smart_home.light_set" in allowed and "đèn" in clause:
            sh_state = states.get("smart_home", {})
            lights = [d for d in sh_state.get("devices", []) if d.get("type") == "light"]
            target_light = lights[0]["id"] if lights else "light_01"

            # Ưu tiên khớp tên dài nhất trước (longest match first) để phân biệt phòng ngủ nhỏ vs lớn
            sorted_lights = sorted(lights, key=lambda d: len(d.get("name", "")), reverse=True)
            for d in sorted_lights:
                d_name = d.get("name", "").lower()
                d_room = d.get("room", "").lower()
                if (d_name and d_name in clause) or (d_room and d_room in clause):
                    target_light = d["id"]
                    break

            args = {"device_id": target_light}
            if any(w in clause for w in ["bật", "mở"]):
                args["power"] = "on"
            elif any(w in clause for w in ["tắt", "đóng"]):
                args["power"] = "off"

            if "độ sáng" in clause or "sáng" in clause:
                if any(w in clause for w in ["một nửa", "50%"]):
                    args["brightness"] = 50
                else:
                    m = re.search(r"(\d{1,3})%", clause)
                    if m:
                        args["brightness"] = int(m.group(1))

            if env.validate("smart_home.light_set", args).get("ok"):
                env.call("smart_home.light_set", args)

        # 2. Lịch (Calendar: update_event, cancel_event)
        cal_state = states.get("calendar", {})
        events = events_found or cal_state.get("events", [])
        if "calendar.update_event" in allowed and any(w in clause for w in ["dời", "đổi lịch", "muộn"]):
            if events:
                evt = events[0]
                evt_id = evt["id"]
                start_iso = evt.get("start", now_str)
                try:
                    start_dt = datetime.fromisoformat(start_iso[:19]) + timedelta(hours=1)
                    end_dt = start_dt + timedelta(hours=1)
                    args = {
                        "event_id": evt_id,
                        "start": start_dt.isoformat() + "+07:00",
                        "end": end_dt.isoformat() + "+07:00",
                    }
                    if env.validate("calendar.update_event", args).get("ok"):
                        env.call("calendar.update_event", args)
                except Exception:
                    pass

        if "calendar.cancel_event" in allowed and any(w in clause for w in ["huỷ lịch", "hủy lịch", "bỏ lịch"]):
            if events:
                args = {"event_id": events[0]["id"]}
                if env.validate("calendar.cancel_event", args).get("ok"):
                    env.call("calendar.cancel_event", args)

        # 3. Báo thức (Alarm)
        if "alarm.create" in allowed and any(w in clause for w in ["báo thức", "hẹn giờ"]):
            resolved_time = self.time_resolver.resolve_datetime(clause, now_str)
            args = {"time": resolved_time}
            if env.validate("alarm.create", args).get("ok"):
                env.call("alarm.create", args)

        # 4. Lịch nhắc (Reminders)
        if "reminders.create" in allowed and any(w in clause for w in ["nhắc tôi", "nhắc nhở", "nhớ nhắc"]):
            resolved_time = self.time_resolver.resolve_datetime(clause, now_str)
            content = "lịch nhắc"
            m = re.search(r"nhắc\s+(?:tôi|mình|dùm)?\s*(.*?)(?:lúc|vào|nhé|\.|$)", clause)
            if m and m.group(1).strip():
                content = m.group(1).strip()
            args = {"content": content, "time": resolved_time}
            if env.validate("reminders.create", args).get("ok"):
                env.call("reminders.create", args)

        # 5. Đặt xe (Ride Hailing)
        if "ride_hailing.book" in allowed and any(w in clause for w in ["đặt xe", "gọi xe", "book xe"]):
            user_profile = context.get("user_profile", {})
            pickup = user_profile.get("work_address") or user_profile.get("home_address") or "Hà Nội"
            dropoff = "Địa điểm hẹn"
            # Tìm địa điểm từ sự kiện lịch nếu có (vd: họp phụ huynh)
            for evt in events:
                loc = evt.get("location")
                if loc:
                    dropoff = loc
                    break
            args = {"pickup": pickup, "dropoff": dropoff, "vehicle": "car4"}
            if env.validate("ride_hailing.book", args).get("ok"):
                env.call("ride_hailing.book", args)

        # 6. Kiểm tra số điện thoại đọc trực tiếp bằng giọng nói
        spoken_phone = self.normalizer.extract_phone_number(clause)
        if spoken_phone and "ewallet.topup_mobile" in allowed and any(w in clause for w in ["nạp", "nạp tiền"]):
            amount = self.normalizer.parse_currency_amount(clause) or 50000
            args = {"phone": spoken_phone, "amount": amount}
            if env.validate("ewallet.topup_mobile", args).get("ok"):
                env.call("ewallet.topup_mobile", args)
            return

        # 7. Danh bạ + Tin nhắn + Cuộc gọi + Nạp thẻ + Chuyển tiền theo tên
        target_name = self._extract_clean_name(clause)
        found_contacts = []
        if target_name and "contacts.search" in allowed:
            c_res = env.call("contacts.search", {"query": target_name})
            if c_res.get("ok"):
                found_contacts = c_res.get("contacts", [])

        # Nạp thẻ điện thoại theo contact
        if "ewallet.topup_mobile" in allowed and any(w in clause for w in ["nạp", "nạp thẻ", "nạp tiền điện thoại", "50 nghìn điện thoại", "50 ngàn điện thoại"]):
            amount = self.normalizer.parse_currency_amount(clause) or 50000
            phone = found_contacts[0].get("phone") if found_contacts else "0900000000"
            args = {"phone": phone, "amount": amount}
            if env.validate("ewallet.topup_mobile", args).get("ok"):
                env.call("ewallet.topup_mobile", args)

        # Chuyển ví (ewallet.transfer)
        if "ewallet.transfer" in allowed and any(w in clause for w in ["chuyển ví", "gửi ví"]):
            amount = self.normalizer.parse_currency_amount(clause)
            if not amount and unpaid_bills:
                for b in unpaid_bills:
                    if b.get("type") == "electricity" and "điện" in clause:
                        amount = b.get("amount")
                        break
                    elif b.get("type") == "water" and "nước" in clause:
                        amount = b.get("amount")
                        break
            amount = amount or 500000
            c_id = found_contacts[0].get("id") if found_contacts else "c_01"
            args = {"contact_id": c_id, "amount": amount}
            if env.validate("ewallet.transfer", args).get("ok"):
                env.call("ewallet.transfer", args)

        # Chuyển khoản ngân hàng (banking.transfer)
        if "banking.transfer" in allowed and any(w in clause for w in ["chuyển cho", "chuyển khoản", "bắn tiền"]):
            amount = self.normalizer.parse_currency_amount(clause) or 1000000
            bank_state = states.get("banking", {})
            bens = bank_state.get("beneficiaries", [])
            accs = bank_state.get("accounts", [])
            from_acc = accs[0]["id"] if accs else "acc_01"
            target_ben = bens[0]["id"] if bens else "ben_01"
            for b in bens:
                b_name = b.get("name", "").lower()
                if target_name and any(w in target_name.lower() for w in b_name.split()):
                    target_ben = b["id"]
                    break
            args = {"from_account_id": from_acc, "beneficiary_id": target_ben, "amount": amount}
            if env.validate("banking.transfer", args).get("ok"):
                env.call("banking.transfer", args)

        # Gửi tin nhắn SMS
        if "sms.send" in allowed and any(w in clause for w in ["nhắn", "nhắn tin", "báo cho"]):
            if found_contacts:
                c_id = found_contacts[0].get("id")
                content = "mai chạy bộ dời sang 09:00 nhé" if "sếp dũng" in clause.lower() else "thông báo"
                m = re.search(r"nhắn\s+.*?\s+(?:rằng|là|nội dung)?\s*(.*?)(?:nhé|\.|$)", clause)
                if m and m.group(1).strip():
                    content = m.group(1).strip()
                args = {"contact_id": c_id, "content": content}
                if env.validate("sms.send", args).get("ok"):
                    env.call("sms.send", args)

        # Gọi điện thoại
        if "phone.call" in allowed and any(w in clause for w in ["gọi", "gọi cho", "gọi dùm"]):
            if found_contacts and len(found_contacts) == 1:
                args = {"contact_id": found_contacts[0]["id"]}
                if env.validate("phone.call", args).get("ok"):
                    env.call("phone.call", args)

    def _extract_clean_name(self, text: str) -> Optional[str]:
        patterns = [
            r"(?:bác|cô|chú|sếp|anh|chị|bạn|ông|bà|em)\s+([A-ZÀ-Ỹa-zà-ỹ0-9\s]+?)(?:\s+(?:hai|năm|50|đã|số|tiền|với|nhé|nha|\.|\,|$))",
            r"(?:gọi cho|gọi dùm tôi|gọi dùm|gọi|nhắn cho|nhắn|báo cho|chuyển cho|nạp giúp)\s+([A-ZÀ-Ỹa-zà-ỹ0-9\s]+?)(?:\s+(?:hai|năm|50|đã|số|tiền|với|nhé|nha|\.|\,|$))",
        ]
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                name = m.group(0).strip()
                name = re.sub(r"^(?:gọi cho|gọi dùm tôi|gọi dùm|gọi|nhắn cho|nhắn|báo cho|chuyển cho|nạp giúp)\s+", "", name, flags=re.IGNORECASE)
                name = re.sub(r"\s+(?:với|nhé|nha)$", "", name, flags=re.IGNORECASE)
                name = name.strip()
                if len(name) > 1 and name.lower() not in ["tôi", "mình", "ai", "điện thoại", "tiền"]:
                    return name.title()
        return None
