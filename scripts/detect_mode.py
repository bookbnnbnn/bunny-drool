#!/usr/bin/env python3
"""判斷 morning-avatar 應進入哪個模式。

Usage:
  python3 detect_mode.py --session-id <ID> [--time HH:MM] [--has-emotion]

Output (JSON):
  {
    "mode": "morning" | "dismissal" | "progress_bar" | "silent",
    "time": "HH:MM",
    "state": { ... },       # 現有狀態檔內容
    "is_test": true/false
  }
"""
import argparse
import json
import os
import random
import sys
from datetime import datetime, timezone, timedelta

STATE_FILE = os.path.expanduser("~/.claude/morning-avatar-state.json")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--session-id", required=True, help="當前 session ID")
    parser.add_argument("--time", help="覆蓋時間 HH:MM（測試模式）")
    parser.add_argument("--has-emotion", action="store_true",
                        help="使用者訊息含情緒信號")
    args = parser.parse_args()

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

    # 模式判斷（優先級由高到低）
    if state.get("session_id") != args.session_id:
        mode = "morning"
    elif 17 * 60 + 30 <= time_minutes <= 17 * 60 + 45:
        mode = "dismissal"
    elif args.has_emotion or random.randint(0, 9) <= 2:
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
