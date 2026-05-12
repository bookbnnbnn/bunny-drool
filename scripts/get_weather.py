#!/usr/bin/env python3
"""抓取台北天氣並輸出對應 emoji，同時快取進狀態檔（一天只抓一次）。

Usage:
  python3 get_weather.py [--session-id YYYY-MM-DD]

Output: 單一天氣 emoji（例如 ☀️）
失敗時預設輸出 ☀️（台灣五月合理預設）。
"""
import argparse
import json
import os
import urllib.request

STATE_FILE = os.path.expanduser("~/.claude/desk-buddy-state.json")

WEATHER_MAP = {
    "sunny": "☀️",
    "clear": "☀️",
    "partly cloudy": "⛅",
    "cloudy": "☁️",
    "overcast": "☁️",
    "rain": "🌧️",
    "drizzle": "🌧️",
    "shower": "🌧️",
    "light rain": "🌧️",
    "heavy rain": "🌧️",
    "moderate rain": "🌧️",
    "patchy rain": "🌧️",
    "thunder": "⛈️",
    "thunderstorm": "⛈️",
    "snow": "❄️",
    "fog": "🌫️",
    "mist": "🌫️",
}

DEFAULT_EMOJI = "☀️"


def fetch_emoji():
    try:
        url = "https://wttr.in/%E4%B8%AD%E5%B1%B1%E5%8D%80,%E5%8F%B0%E5%8C%97?format=j1"
        req = urllib.request.Request(url, headers={"User-Agent": "desk-buddy/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read())

        hourly = data.get("weather", [{}])[0].get("hourly", [])
        desc = ""
        for h in hourly:
            if h.get("time", "") in ("900", "0900"):
                desc = h.get("weatherDesc", [{}])[0].get("value", "")
                break

        if not desc and hourly:
            desc = hourly[0].get("weatherDesc", [{}])[0].get("value", "")

        desc_lower = desc.lower()
        for key, emoji in WEATHER_MAP.items():
            if key in desc_lower:
                return emoji

        return DEFAULT_EMOJI
    except Exception:
        return DEFAULT_EMOJI


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--session-id", help="今日 session ID（YYYY-MM-DD），用於快取")
    args = parser.parse_args()

    # 有 session-id 時，先查快取
    if args.session_id:
        state = {}
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, encoding="utf-8") as f:
                    state = json.load(f)
            except Exception:
                state = {}

        cached = state.get("weather", {})
        if cached.get("date") == args.session_id:
            print(cached.get("emoji", DEFAULT_EMOJI))
            return

        emoji = fetch_emoji()

        # 寫回快取
        state["weather"] = {"date": args.session_id, "emoji": emoji}
        try:
            os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False)
        except Exception:
            pass

        print(emoji)
    else:
        print(fetch_emoji())


if __name__ == "__main__":
    main()
