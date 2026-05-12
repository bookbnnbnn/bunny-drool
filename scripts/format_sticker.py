#!/usr/bin/env python3
"""Test helper: assemble and validate a desk-buddy sticker.

Used only by tests/run_smoke_tests.py — not invoked during normal skill execution.

Usage:
  python3 scripts/format_sticker.py \\
    --role bunny|kitty \\
    --emotion neutral|happy|sad|tired|stressed|annoyed|confused_boss|eating|coding \\
    [--face "(・∀・)"]   # override face (defaults to random from emotion)
    [--hand つ]          # hand gesture: つ づ ノ っ
    [--item "💻"]        # item emoji
    [--line1 "台詞"]
    [--line2 "台詞第二行"]

Output: markdown code block with exactly 3 lines.
Validation errors go to stderr.
"""
import argparse
import json
import os
import random
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
EMOTIONS_FILE = os.path.join(DATA_DIR, "emotions.json")
ROLES_FILE = os.path.join(DATA_DIR, "roles.json")

VALID_HANDS = ["つ", "づ", "ノ", "っ"]


def load_data():
    with open(EMOTIONS_FILE, encoding="utf-8") as f:
        emotions = json.load(f)
    with open(ROLES_FILE, encoding="utf-8") as f:
        roles = json.load(f)
    return emotions, roles


def pick_ear(role_data: dict, emotion_key: str) -> str:
    """Pick the appropriate fixed ear for an emotion. Falls back to first ear."""
    for ear_info in role_data["ears"].values():
        if emotion_key in ear_info.get("emotions", []):
            return ear_info["ascii"]
    return next(iter(role_data["ears"].values()))["ascii"]


def validate_ear(role_data: dict, ear: str) -> bool:
    """Return True if the ear is from the fixed set."""
    valid = [e["ascii"] for e in role_data["ears"].values()]
    return any(v in ear for v in valid)


def main():
    parser = argparse.ArgumentParser(description="Desk-buddy sticker assembler (test helper)")
    parser.add_argument("--role", choices=["bunny", "kitty"], required=True)
    parser.add_argument("--emotion", default="neutral",
                        choices=["neutral", "happy", "sad", "tired", "stressed",
                                 "annoyed", "confused_boss", "eating", "coding"])
    parser.add_argument("--face", default=None, help="Face override (optional)")
    parser.add_argument("--hand", default=None, help="Hand gesture: つ づ ノ っ")
    parser.add_argument("--item", default="", help="Item emoji")
    parser.add_argument("--line1", default="", help="Dialogue line 1")
    parser.add_argument("--line2", default=None, help="Dialogue line 2 (optional)")
    args = parser.parse_args()

    emotions, roles = load_data()
    emotion_data = emotions["emotions"].get(args.emotion, emotions["emotions"]["neutral"])
    role_data = roles[args.role]

    # Ear: always from fixed set
    ear = pick_ear(role_data, args.emotion)

    # Face: override or random from emotion list
    if args.face:
        face_str = args.face
    else:
        face_str = random.choice(emotion_data["faces"])

    # Hand: validate against allowed set
    hand = args.hand if args.hand in VALID_HANDS else random.choice(emotion_data.get("hands", ["つ"]))
    if hand not in VALID_HANDS:
        hand = "つ"

    item_part = args.item if args.item else ""

    # Assemble 3 lines
    if args.role == "bunny":
        line1 = f"   {ear}"
        face_wrapped = face_str if face_str.startswith("(") else f"({face_str})"
        line2 = f"   {face_wrapped}  {args.line1}"
        line3 = f"   / {hand}{item_part}"
    else:  # kitty
        line1 = f"   {ear}"
        face_wrapped = face_str if face_str.startswith("[") else f"[=•ω•]"
        line2 = f"   {face_wrapped}  {args.line1}"
        line3 = f"   / {hand}{item_part}"

    if args.line2:
        line3 += f"  {args.line2}"

    sticker = f"```\n{line1}\n{line2}\n{line3}\n```"
    print(sticker)

    # --- Validation ---
    errors = []
    inner_lines = [line1, line2, line3]

    if len(inner_lines) != 3:
        errors.append(f"Expected 3 lines, got {len(inner_lines)}")

    if not line3.strip().startswith("/"):
        errors.append(f"Third line must start with '/': {line3!r}")

    if not validate_ear(role_data, line1):
        valid_ears = [e["ascii"] for e in role_data["ears"].values()]
        errors.append(f"Ear not in fixed set. Found: {line1!r}. Valid: {valid_ears}")

    if errors:
        for e in errors:
            print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)
    else:
        print("✅ Format validation passed", file=sys.stderr)


if __name__ == "__main__":
    main()
