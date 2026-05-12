#!/usr/bin/env python3
"""計算工作日下班進度條。

Usage:
  python3 progress_bar.py [--time HH:MM]

Output: bar|hours|minutes|percent
  例如: ████████░░|1|30|80
"""
import argparse
from datetime import datetime, timezone, timedelta


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--time", help="覆蓋時間 HH:MM（測試模式）")
    args = parser.parse_args()

    tz = timezone(timedelta(hours=8))
    now = datetime.now(tz)

    if args.time:
        h, m = map(int, args.time.split(":"))
        now = now.replace(hour=h, minute=m, second=0, microsecond=0)

    start = now.replace(hour=9, minute=0, second=0, microsecond=0)
    end = now.replace(hour=17, minute=45, second=0, microsecond=0)

    elapsed = (now - start).total_seconds() / 60
    total = (end - start).total_seconds() / 60
    pct = max(0.0, min(1.0, elapsed / total))

    filled = int(pct * 15)
    bar = "▓" * filled + "░" * (15 - filled)

    remaining = max(0.0, (end - now).total_seconds())
    hours = int(remaining // 3600)
    minutes = int((remaining % 3600) // 60)

    current_time = f"{now.hour:02d}:{now.minute:02d}"
    print(f"{current_time}|{bar}|{hours}|{minutes}|{int(pct * 100)}")


if __name__ == "__main__":
    main()
