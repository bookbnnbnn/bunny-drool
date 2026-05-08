#!/usr/bin/env python3
"""抓取台北天氣並輸出對應 emoji。

Usage:
  python3 get_weather.py

Output: 單一天氣 emoji（例如 ☀️）
失敗時預設輸出 ☀️（台灣五月合理預設）。
"""
import json
import sys
import urllib.request

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


def main():
    try:
        url = "https://wttr.in/%E4%B8%AD%E5%B1%B1%E5%8D%80,%E5%8F%B0%E5%8C%97?format=j1"
        req = urllib.request.Request(url, headers={"User-Agent": "morning-avatar/1.0"})
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
                print(emoji)
                return

        print(DEFAULT_EMOJI)
    except Exception:
        print(DEFAULT_EMOJI)


if __name__ == "__main__":
    main()
