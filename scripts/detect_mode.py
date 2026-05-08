#!/usr/bin/env python3
"""判斷 bunny-drool 應進入哪個模式。

Usage:
  python3 detect_mode.py --session-id <ID> [--time HH:MM] [--has-emotion] \
                         [--random-chance 50] [--reset]

Output (JSON):
  {
    "mode": "riddle" | "dismissal" | "progress_bar" | "silent",
    "time": "HH:MM",
    "state": { ... },
    "is_test": true/false
  }

模式決策順序：
  1. --reset → 清除狀態檔，回傳 riddle
  2. 新 session 且 (has_emotion 或 random_hit) → riddle（每 session 僅一次）
  3. 下班時段 17:30–17:45 且 (has_emotion 或 random_hit) → dismissal（每 session 僅一次）
  4. has_emotion 或 random_hit → progress_bar（可重複觸發）
  5. 以上皆否 → silent
"""
import argparse
import json
import os
import random
from datetime import datetime, timezone, timedelta

STATE_FILE = os.path.expanduser("~/.claude/bunny-drool-state.json")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--session-id", required=True, help="當前 session ID")
    parser.add_argument("--time", help="覆蓋時間 HH:MM（測試模式）")
    parser.add_argument("--has-emotion", action="store_true",
                        help="使用者訊息含情緒信號")
    parser.add_argument("--random-chance", type=int, default=50,
                        help="隨機觸發機率 0-100（預設 50）")
    parser.add_argument("--reset", action="store_true",
                        help="重置狀態檔（刪除後視為新 session）")
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

    # 計算觸發條件
    random_hit = random.random() < (args.random_chance / 100)
    triggered = args.has_emotion or random_hit
    is_new_session = state.get("session_id") != args.session_id
    in_dismissal_window = 17 * 60 + 30 <= time_minutes <= 17 * 60 + 45

    # 模式決策
    if args.reset:
        mode = "riddle"
    elif is_new_session and triggered and not state.get("riddle_shown"):
        mode = "riddle"
    elif in_dismissal_window and triggered and not state.get("dismissal_shown"):
        mode = "dismissal"
    elif triggered:
        mode = "progress_bar"
    else:
        mode = "silent"

    result = {
        "mode": mode,
        "time": f"{hour:02d}:{minute:02d}",
        "state": state,
        "is_test": is_test,
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
