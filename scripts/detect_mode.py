#!/usr/bin/env python3
"""判斷 desk-buddy 應進入哪個模式。

Usage:
  python3 detect_mode.py --session-id <ID> [--time HH:MM] [--has-emotion] \
                         [--random-chance 50] [--reset] [--demo] \
                         [--riddle-hour 10]

Output (JSON):
  {
  "mode": "riddle_teaser" | "riddle" | "dismissal" | "companion",
  "companion_variant": "progress_bar" | "encouragement" | "analysis" | "silent",
              # --force-sticker 時 silent 改為隙機選其餘三種
    "time": "HH:MM",
    "state": { ... },
    "is_test": true/false,
    "is_demo": true/false
  }

模式決策順序：
  1. --demo-reset     → 清除 demo 欄位（demo_active / demo_message_count / demo_shown_types），回傳 silent
  2. --reset          → 清除狀態檔，回傳 riddle_teaser
  3. --demo           → 開發者初始化 demo session，寫入 demo_active，回傳 silent（不出貼圖）
  3. state.demo_active → 使用者訊息自動觸發 demo 邏輯：
       - 第 1 則強制出 riddle_teaser
       - 其後隨機（50%），確保 10 則內展完全部 6 種型態
       - 選型態順序：riddle_teaser → riddle → 其餘（謎題比進度條早）
  4. riddle_hour 前 且 riddle 未出過 且 riddle_incoming 未設定 → riddle_teaser
  5. riddle_incoming 為 true → riddle
  6. 中午時段 11:30–12:00 且 (has_emotion 或 random_hit) → dismissal（每 session 僅一次）
  7. 以上皆否 → companion（silent 機率=random_chance%；其餘三種各佔(1-random_chance/100)/3）
"""
import argparse
import json
import os
import random
from datetime import datetime, timezone, timedelta

STATE_FILE = os.path.expanduser("~/.claude/desk-buddy-state.json")

DEMO_RIDDLE_TYPES = ["riddle_teaser", "riddle"]
DEMO_OTHER_TYPES = ["progress_bar", "encouragement", "analysis", "dismissal"]
DEMO_ALL_TYPES = DEMO_RIDDLE_TYPES + DEMO_OTHER_TYPES
DEMO_MAX_MESSAGES = 10


def demo_candidate_pool(shown_types: set) -> list:
    """謎題系列用完才開放其他型態。"""
    if "riddle_teaser" not in shown_types:
        return ["riddle_teaser"]
    if "riddle" not in shown_types:
        return ["riddle"]
    return [t for t in DEMO_OTHER_TYPES if t not in shown_types]


def save_state(state: dict) -> None:
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--time", help="覆蓋時間 HH:MM（測試模式）")
    parser.add_argument("--has-emotion", action="store_true")
    parser.add_argument("--random-chance", type=int, default=50)
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--demo", action="store_true",
                        help="開發者初始化 demo session（靜默，不出貼圖）")
    parser.add_argument("--demo-reset", action="store_true",
                        help="清除 demo 狀態，回到一般模式（不影響其他 session 資料）")
    parser.add_argument("--riddle-hour", type=int, default=10)
    parser.add_argument("--force-sticker", action="store_true",
                        help="謎語互動模式：強制 companion_variant 不為 silent")
    parser.add_argument("--detected-emotion", default=None,
                        help="由 Claude 傳入已偵測的情緒 key（直接寫入輸出 JSON，供 generate_sticker.py 使用）")
    args = parser.parse_args()

    # --reset：清除狀態檔
    if args.reset and os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)

    # 讀取狀態檔
    state = {}
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, encoding="utf-8") as f:
            try:
                state = json.load(f)
            except json.JSONDecodeError:
                state = {}

    # 決定時間
    is_test = args.time is not None
    if args.time:
        hour, minute = map(int, args.time.split(":"))
    else:
        tz = timezone(timedelta(hours=8))
        now = datetime.now(tz)
        hour, minute = now.hour, now.minute

    time_minutes = hour * 60 + minute

    random_hit = random.random() < (args.random_chance / 100)
    triggered = args.has_emotion or random_hit
    is_new_session = state.get("session_id") != args.session_id
    in_dismissal_window = 11 * 60 + 30 <= time_minutes <= 12 * 60
    before_riddle_hour = time_minutes < args.riddle_hour * 60

    COMPANION_VARIANTS = ["progress_bar", "encouragement", "analysis", "silent"]

    mode = "companion"
    companion_variant = None
    is_demo = False

    # 模式決策
    if args.demo_reset:
        # demo reset：保留 demo_active，計數歸零，準備迎接下一位使用者
        state["session_id"] = args.session_id   # 確保同天 session 符對即自動進入 demo
        state.pop("animal", None)               # 清除動物，下一位使用者起就重新選動物
        state["demo_active"] = True
        state["demo_message_count"] = 0
        state["demo_shown_types"] = []
        state["demo_riddle_seed"] = str(random.random())  # 新 seed，譜語與上一居不同
        # 清除譜語相關狀態，讓下一居從頭開始
        for key in ("riddle_shown", "riddle_incoming", "riddle", "riddle_answered",
                    "wrong_guesses", "dismissal_shown", "weather"):
            state.pop(key, None)
        save_state(state)
        mode = "companion"
        companion_variant = "silent"

    elif args.reset:
        mode = "riddle_teaser"

    elif args.demo:
        # 開發者指令：初始化（或重新初始化）demo session，永遠靜默
        is_demo = True
        state["session_id"] = args.session_id
        state["demo_active"] = True
        state["demo_message_count"] = 0
        state["demo_shown_types"] = []
        state["demo_riddle_seed"] = str(random.random())  # 每次 demo 初始化產生不同 seed
        save_state(state)
        mode = "companion"
        companion_variant = "silent"

    elif state.get("demo_active") and state.get("session_id") == args.session_id:
        # Demo 模式：使用者訊息自動觸發
        is_demo = True

        if is_new_session:
            # session 換了，結束 demo
            state["demo_active"] = False
            save_state(state)
            mode = "silent"
        else:
            demo_count = state.get("demo_message_count", 0) + 1
            shown_types = set(state.get("demo_shown_types", []))
            pending = [t for t in DEMO_ALL_TYPES if t not in shown_types]
            remaining_after = DEMO_MAX_MESSAGES - demo_count
            candidate_pool = demo_candidate_pool(shown_types)

            chosen_type = None

            if demo_count == 1:
                chosen_type = candidate_pool[0] if candidate_pool else (pending[0] if pending else None)
            elif pending and remaining_after < len(pending):
                chosen_type = random.choice(candidate_pool) if candidate_pool else random.choice(pending)
            elif candidate_pool and random.random() < 0.5:
                chosen_type = random.choice(candidate_pool)

            if state.get("riddle_incoming") and "riddle" not in shown_types:
                chosen_type = "riddle"                          # 修 bug 1
            elif args.has_emotion and "dismissal" not in shown_types:
                chosen_type = "dismissal"                       # 修 bug 2（情緒優先出 dismissal）
            elif args.force_sticker and chosen_type is None:
                chosen_type = random.choice(candidate_pool) if candidate_pool else random.choice(pending)  # 修 bug 3

            if chosen_type:
                shown_types.add(chosen_type)

            state["demo_message_count"] = demo_count
            state["demo_shown_types"] = list(shown_types)

            # 展完或達上限後自動關閉 demo
            if demo_count >= DEMO_MAX_MESSAGES or not pending:
                state["demo_active"] = False

            save_state(state)

            if chosen_type is None:
                mode = "silent"
            elif chosen_type in COMPANION_VARIANTS:
                mode = "companion"
                companion_variant = chosen_type
            else:
                mode = chosen_type

    elif before_riddle_hour and not state.get("riddle_shown") and not state.get("riddle_incoming"):
        mode = "riddle_teaser"
    elif state.get("riddle_incoming"):
        mode = "riddle"
    elif in_dismissal_window and triggered and not state.get("dismissal_shown"):
        mode = "dismissal"
    # else: mode 保持 companion（預設值）

    # 非 demo 的 companion 模式：silent 佔 random_chance%，其餘三種均分剩餘機率
    if mode == "companion" and companion_variant is None:
        if args.force_sticker:
            # 謎語互動模式：一定要出貼圖，不選 silent
            companion_variant = random.choice(["progress_bar", "encouragement", "analysis"])
        else:
            silent_prob = args.random_chance / 100
            other_prob = (1 - silent_prob) / 3
            roll = random.random()
            if roll < silent_prob:
                companion_variant = "silent"
            elif roll < silent_prob + other_prob:
                companion_variant = "progress_bar"
            elif roll < silent_prob + 2 * other_prob:
                companion_variant = "encouragement"
            else:
                companion_variant = "analysis"

    result = {
        "mode": mode,
        "time": f"{hour:02d}:{minute:02d}",
        "state": state,
        "is_test": is_test,
        "is_demo": is_demo,
    }
    if companion_variant:
        result["companion_variant"] = companion_variant
    if args.detected_emotion:
        result["detected_emotion"] = args.detected_emotion
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
