#!/usr/bin/env python3
"""Mixed assembler for desk-buddy stickers.

The program handles structure (ear whitelist, format, alignment);
the LLM handles creativity (台詞, optional face creation).

Three modes:

  scaffold (default) — Program picks ear/face/hand/item from data files.
    Outputs a compact JSON "hint" Claude uses to write a short 台詞.
    Minimises tokens: Claude only reads this tiny payload, not the full JSON.

    python3 scripts/generate_sticker.py \\
      --emotion tired --animal bunny [--seed 42]

  assemble — Claude provides 台詞; program assembles and validates
    the final 3-line code block.

    python3 scripts/generate_sticker.py assemble \\
      --emotion coding --animal bunny \\
      --line1 "這個 bug 我幫你看著" \\
      [--face "(・∀・)"] [--hand つ] [--item 💻]

    Progress-bar layout:
    python3 scripts/generate_sticker.py assemble \\
      --emotion tired --animal bunny --progress-bar \\
      --progress "14:30|▓▓▓▓▓▓▓▓▓░░░░░░|3|15|62" \\
      --line1 "你可以的！（不知道你在做什麼但你可以的）"

  deterministic — Fully program-driven with fallback 台詞 (for tests/CI).
    python3 scripts/generate_sticker.py deterministic \\
      --emotion happy --animal kitty [--seed 42]

Keyword-based auto-detection (all modes):
  python3 scripts/generate_sticker.py \\
    --message "好睏，快撐不住了" --animal bunny
"""
import argparse
import json
import os
import random
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
EMOTIONS_FILE = os.path.join(DATA_DIR, "emotions.json")
ROLES_FILE    = os.path.join(DATA_DIR, "roles.json")

VALID_HANDS = ["つ", "づ", "ノ", "っ"]

FALLBACK_EAR_BUNNY = "(\\__/)"
FALLBACK_EAR_KITTY = "/\\_/\\"

# Fallback 台詞 templates used in deterministic mode
FALLBACK_LINES = {
    "neutral":      "在這裡陪你（搓手）",
    "happy":        "耶！一起！（拍桌）",
    "sad":          "沒事的，慢慢來（不知道說什麼）",
    "tired":        "喝水喝水（端著茶）",
    "stressed":     "你可以的！（躲到桌子底下）",
    "annoyed":      "嗯嗯我聽到了（繼續喝茶）",
    "confused_boss":"根據我的分析——（拿出顯微鏡）",
    "eating":       "吃好吃滿！（點頭）",
    "coding":       "這個 bug 我幫你盯著（假裝看得懂）",
}


def load_data():
    with open(EMOTIONS_FILE, encoding="utf-8") as f:
        emotions = json.load(f)
    with open(ROLES_FILE, encoding="utf-8") as f:
        roles = json.load(f)
    return emotions["emotions"], roles


def detect_emotion(message: str, emotions: dict) -> str:
    """Return the best-matching emotion key for a message, or 'neutral'."""
    msg = message.lower()
    # score each emotion by keyword hit count
    scores = {}
    for key, emo in emotions.items():
        hits = sum(1 for kw in emo.get("keywords", []) if kw in msg)
        if hits:
            scores[key] = hits
    if not scores:
        return "neutral"
    return max(scores, key=lambda k: scores[k])


def pick_ear(roles: dict, animal: str, emotion_key: str, rng: random.Random) -> str:
    """Pick ear from the fixed whitelist, prefer one mapped to this emotion."""
    role = roles.get(animal, {})
    ears = role.get("ears", {})
    # Find ears that list this emotion
    matching = [e["ascii"] for e in ears.values() if emotion_key in e.get("emotions", [])]
    if matching:
        return rng.choice(matching)
    # Fall back to first ear in the role
    if ears:
        return next(iter(ears.values()))["ascii"]
    return FALLBACK_EAR_BUNNY if animal == "bunny" else FALLBACK_EAR_KITTY


def build_context(emotion_key: str, animal: str, emotions: dict, roles: dict,
                  rng: random.Random) -> dict:
    emo = emotions.get(emotion_key, emotions.get("neutral"))
    ear = pick_ear(roles, animal, emotion_key, rng)

    face_sample = rng.choice(emo["faces"]) if emo.get("faces") else ""
    hand        = rng.choice(emo["hands"]) if emo.get("hands") else "つ"
    item        = rng.choice(emo["items"]) if emo.get("items") else ""

    role = roles.get(animal, {})
    face_formula = role.get("face_formula", "")
    # Add face_examples from roles.json (kitty only) or show all emotion faces
    face_examples = list(emo.get("faces", []))

    return {
        "ear":          ear,
        "face_sample":  face_sample,
        "hand":         hand,
        "item":         item,
        "face_formula": face_formula,
        "face_examples": face_examples,
        "strategy":     emo.get("strategy", ""),
        "emotion_key":  emotion_key,
        "animal":       animal,
    }


def assemble_lines(animal: str, ear: str, face: str, hand: str, item: str,
                   line1: str = "", line2: str = None,
                   progress_bar: bool = False, progress: str = None) -> list:
    """Return the 3 inner lines of the sticker (without fences)."""
    if animal == "bunny":
        face_str = face if face.startswith("(") else f"({face})"
    else:
        face_str = face if face.startswith("[") else "[=•ω•]"

    item_part = item if item else ""
    hand_part = f"/ {hand}{item_part}"

    if progress_bar and progress:
        parts = progress.split("|")
        if len(parts) >= 5:
            cur_time, bar, hours, minutes, pct = parts[0], parts[1], parts[2], parts[3], parts[4]
        else:
            cur_time, bar, hours, minutes, pct = "??:??", "░" * 15, "?", "?", "?"
        row1 = f"   {ear}  {cur_time} | 距離下班 {hours}h {minutes}m"
        row2 = f"   {face_str}  {bar}  {pct}%"
        row3 = f"   {hand_part}  {line1}" if line1 else f"   {hand_part}"
        return [row1, row2, row3]

    if line2:
        return [f"   {ear}", f"   {face_str}  {line1}", f"   {hand_part}  {line2}"]
    elif line1:
        return [f"   {ear}", f"   {face_str}  {line1}", f"   {hand_part}"]
    else:
        return [f"   {ear}", f"   {face_str}", f"   {hand_part}"]


def validate_lines(lines: list, role_data: dict, ear: str) -> list:
    """Return list of error strings (empty = valid)."""
    errors = []
    if len(lines) != 3:
        errors.append(f"Expected 3 lines, got {len(lines)}")
    elif not lines[2].strip().startswith("/"):
        errors.append(f"Line 3 must start with '/': {lines[2]!r}")
    valid_ears = [e["ascii"] for e in role_data["ears"].values()]
    if ear not in valid_ears:
        errors.append(f"Ear not in whitelist: {ear!r}. Valid: {valid_ears}")
    return errors


def print_sticker(lines: list):
    print("```")
    for l in lines:
        print(l)
    print("```")


def run_assemble(emotion_key: str, animal: str, emotions: dict, roles: dict,
                 rng: random.Random, args) -> None:
    """Assemble mode: program structure + caller-provided 台詞."""
    emo = emotions.get(emotion_key, emotions["neutral"])
    role_data = roles[animal]
    ear = pick_ear(roles, animal, emotion_key, rng)

    # Face: override or sample from pool
    if hasattr(args, "face") and args.face:
        face = args.face
    elif animal == "kitty":
        eyes = ["•", "^", "-", ">", "°", "*", "≧", "＾", "ˇ"]
        eye = rng.choice(eyes)
        face = f"[={eye}ω{eye}]"
    else:
        face = rng.choice(emo["faces"]) if emo.get("faces") else "(・ω・)"

    hand_override = getattr(args, "hand", None)
    hand = hand_override if hand_override in VALID_HANDS else (
        rng.choice([h for h in emo.get("hands", ["つ"]) if h in VALID_HANDS]) or "つ"
    )
    item = getattr(args, "item", None) or (rng.choice(emo["items"]) if emo.get("items") else "")

    line1 = getattr(args, "line1", "") or ""
    line2 = getattr(args, "line2", None)
    use_pb = getattr(args, "progress_bar", False)
    progress = getattr(args, "progress", None)

    lines = assemble_lines(animal, ear, face, hand, item, line1, line2, use_pb, progress)
    errors = validate_lines(lines, role_data, ear)
    if errors:
        for e in errors:
            print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)

    print_sticker(lines)
    print("✅ Valid", file=sys.stderr)


def run_deterministic(emotion_key: str, animal: str, emotions: dict, roles: dict,
                      rng: random.Random) -> None:
    """Deterministic mode: fully program-driven, no LLM needed."""
    emo = emotions.get(emotion_key, emotions["neutral"])
    role_data = roles[animal]
    ear = pick_ear(roles, animal, emotion_key, rng)

    if animal == "kitty":
        eyes = ["•", "^", "-", ">", "°"]
        eye = rng.choice(eyes)
        face = f"[={eye}ω{eye}]"
    else:
        face = rng.choice(emo["faces"]) if emo.get("faces") else "(・ω・)"

    hands = [h for h in emo.get("hands", ["つ"]) if h in VALID_HANDS]
    hand = rng.choice(hands) if hands else "つ"
    item = rng.choice(emo["items"]) if emo.get("items") else ""
    line1 = FALLBACK_LINES.get(emotion_key, "在這裡陪你（點頭）")

    lines = assemble_lines(animal, ear, face, hand, item, line1)
    errors = validate_lines(lines, role_data, ear)
    if errors:
        for e in errors:
            print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)

    print_sticker(lines)
    print("✅ Deterministic valid", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Desk-buddy mixed sticker assembler")
    parser.add_argument("mode", nargs="?", default="scaffold",
                        choices=["scaffold", "assemble", "deterministic"],
                        help="scaffold (default): output JSON hint | "
                             "assemble: build sticker from --line1/--line2 | "
                             "deterministic: fully program-driven (tests)")
    parser.add_argument("--emotion", default=None,
                        help="Emotion key (e.g. tired, coding, happy). Auto-detected from --message if omitted.")
    parser.add_argument("--animal", choices=["bunny", "kitty"], default="bunny")
    parser.add_argument("--message", default="",
                        help="Raw user message — used for auto emotion detection when --emotion is omitted.")
    parser.add_argument("--seed", type=int, default=None,
                        help="Random seed for reproducible output (useful in tests).")
    parser.add_argument("--list-emotions", action="store_true",
                        help="Print all available emotion keys and exit.")
    # assemble-mode extras
    parser.add_argument("--face", default=None, help="Override face (optional)")
    parser.add_argument("--hand", default=None, help="Hand gesture: つ づ ノ っ")
    parser.add_argument("--item", default=None, help="Item emoji")
    parser.add_argument("--line1", default="", help="First 台詞 line")
    parser.add_argument("--line2", default=None, help="Second 台詞 line (optional)")
    parser.add_argument("--progress-bar", action="store_true",
                        help="Use progress-bar layout (assemble mode)")
    parser.add_argument("--progress", default=None,
                        help="Progress data: time|bar|hours|mins|pct")
    args = parser.parse_args()

    emotions, roles = load_data()

    if args.list_emotions:
        for key, emo in emotions.items():
            kws = ", ".join(emo.get("keywords", [])[:4])
            print(f"  {key:<18}  keywords: {kws}")
        sys.exit(0)

    rng = random.Random(args.seed)

    # Resolve emotion key
    emotion_key = args.emotion
    if not emotion_key:
        if args.message:
            emotion_key = detect_emotion(args.message, emotions)
        else:
            emotion_key = "neutral"
    if emotion_key not in emotions:
        print(f"Warning: unknown emotion '{emotion_key}', falling back to 'neutral'", file=sys.stderr)
        emotion_key = "neutral"

    if args.mode == "assemble":
        run_assemble(emotion_key, args.animal, emotions, roles, rng, args)
    elif args.mode == "deterministic":
        run_deterministic(emotion_key, args.animal, emotions, roles, rng)
    else:
        # scaffold (default) — output compact JSON hint
        ctx = build_context(emotion_key, args.animal, emotions, roles, rng)
        print(json.dumps(ctx, ensure_ascii=False))


if __name__ == "__main__":
    main()
