#!/usr/bin/env python3
"""從兔子／貓咪中隨機選一種動物，寫入狀態檔。

Usage:
  python3 pick_animal.py --session-id <ID>

Output (JSON):
  { "animal": "bunny" | "kitty" }

若同一 session 已選過，直接回傳已選的動物，不重選。
"""
import argparse
import json
import os
import random

STATE_FILE = os.path.expanduser("~/.claude/desk-buddy-state.json")
ANIMALS = ["bunny", "kitty"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--session-id", required=True, help="當前 session ID")
    args = parser.parse_args()

    # 讀取狀態檔
    state = {}
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, encoding="utf-8") as f:
                state = json.load(f)
        except (json.JSONDecodeError, IOError):
            state = {}

    # 同一 session 已選過就直接回傳
    if state.get("session_id") == args.session_id and state.get("animal"):
        print(json.dumps({"animal": state["animal"]}, ensure_ascii=False))
        return

    # 隨機選一種
    animal = random.choice(ANIMALS)

    # 寫回狀態檔
    state["animal"] = animal
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False)

    print(json.dumps({"animal": animal}, ensure_ascii=False))


if __name__ == "__main__":
    main()
