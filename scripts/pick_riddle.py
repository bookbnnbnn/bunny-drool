#!/usr/bin/env python3
"""從內建題庫挑選今日謎語，自動避開歷史重複。

Usage:
  python3 pick_riddle.py

Output (JSON):
  { "question": "...", "answer": "..." }

歷史紀錄存在 ~/.claude/desk-buddy-history.json。
題庫用完時自動重置。
"""
import argparse
import hashlib
import json
import os
import random
from datetime import datetime, timezone, timedelta

HISTORY_FILE = os.path.expanduser("~/.claude/desk-buddy-history.json")

RIDDLES = [
    {"question": "哪兩個英文字母放在一起會爆炸？", "answer": "O和K（OK蹦）"},
    {"question": "越洗越髒是什麼？", "answer": "水"},
    {"question": "老王姓什麼？", "answer": "法，法老王"},
    {"question": "暖暖包為什麼有一堆人在用？", "answer": "因為他有鐵粉"},
    {"question": "為什麼邊緣人不剪頭髮？", "answer": "因為沒人要理他"},
    {"question": "什麼東西有腳卻走不了？", "answer": "桌子"},
    {"question": "什麼門永遠關不上？", "answer": "球門"},
    {"question": "什麼路最窄？", "answer": "冤家路窄"},
    {"question": "什麼東西天氣越熱它爬得越高？", "answer": "溫度計"},
    {"question": "哪種花不能摸？", "answer": "火花"},
    {"question": "什麼蛋打不破、煮不熟、更不能吃？", "answer": "考試考的零蛋"},
    {"question": "太陽和月亮在一起是哪一天？", "answer": "明天"},
    {"question": "什麼東西往上升永遠不會掉下來？", "answer": "年齡"},
    {"question": "小白兔為什麼不嫁給斑馬？", "answer": "因為兔媽媽說紋身的都是壞人"},
    {"question": "什麼動物最容易被貼在牆壁上？", "answer": "海豹（海報）"},
    {"question": "布跟紙怕什麼？", "answer": "布怕一萬，紙怕萬一（不怕一萬，只怕萬一）"},
    {"question": "麒麟飛到北極會變成什麼？", "answer": "冰淇淋（冰麒麟）"},
    {"question": "世界上什麼人一下子變老？", "answer": "新娘（今天是新娘，明天是老婆）"},
    {"question": "有一隻熊走過來，猜一成語？", "answer": "有備而來（有bear而來）"},
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", default=None,
                        help="覆蓋日期 seed（demo 模式：傳入 state.demo_riddle_seed，讓每居体驗不同譜語）")
    args = parser.parse_args()

    # 讀取歷史
    history = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, encoding="utf-8") as f:
                history = json.load(f)
        except (json.JSONDecodeError, IOError):
            history = []

    used_questions = {h["question"] for h in history}

    # 篩選未用過的題目
    available = [r for r in RIDDLES if r["question"] not in used_questions]
    if not available:
        # 題庫用完，重置歷史
        history = []
        available = RIDDLES[:]

    # 以 seed 決定今日譜語，同一天內多次呼叫會得到同一題
    if args.seed:
        # demo 模式：用傳入的 seed，每居會不一様
        seed = int(hashlib.md5(args.seed.encode()).hexdigest(), 16)
        today = args.seed  # 用作历史記錄的 key
    else:
        tz = timezone(timedelta(hours=8))
        today = datetime.now(tz).strftime("%Y-%m-%d")
        seed = int(hashlib.md5(today.encode()).hexdigest(), 16)
    random.seed(seed)
    pick = random.choice(available)

    # 更新歷史
    history.append({"date": today, "question": pick["question"]})
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    print(json.dumps(pick, ensure_ascii=False))


if __name__ == "__main__":
    main()
