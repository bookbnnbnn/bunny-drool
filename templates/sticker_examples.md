# desk-buddy sticker examples

這份文件是**參考範例庫**，不是輸出模板。LLM 看這些例子感受語感與格式，但台詞必須即興生成，禁止照抄。

> **排版重要提醒**
> - 三行 code block，每行前置 3 個空格，中間無空行
> - 耳朵必須來自 `data/roles.json` 的固定清單
> - 第三行永遠以 `/ ` 開頭，後接手勢（つ づ ノ っ）再接持物

---

## 型態零：純貼圖（companion — encouragement / analysis）

**兔子 × 疲憊**
```
   /)_/)
   (－_－)  喝水喝水，先把杯子填滿（端著茶）
   / っ🍵
```

**兔子 × 壓力**
```
   (\__/)
   (°Д°；)  你可以的！（已經躲到桌子底下）
   / ノ🚨
```

**貓咪 × coding**
```
   /\_/\
   [=°ω°]  根據我的分析，這個 bug 很潮（拿出顯微鏡）
   / つ🔬
```

**貓咪 × 煩躁**
```
   /|_|\
   [=>ω<]  嗯嗯我聽到了（繼續喝茶）你說你說
   / っ☕
```

---

## 型態〇.五：riddle_teaser

> 台詞必須暗示「等等有東西」，禁止直接提到謎語

**兔子**
```
   (\__/)
   (✦ω✦)  等一下有個東西要給你看（搓手）
   / つ✨
```

**貓咪**
```
   /\_/\
   [=^ω^]  剛發現一件事，你等一下（搖尾巴）
   / つ🌟
```

---

## 型態一：謎語貼圖（riddle）

> 第三行格式：`/ 手持物  謎語emoji 謎語題目`

**兔子**
```
   (\__/)
   (・∀・)  這題很簡單，我覺得啦
   / つ📬  ❓ 什麼東西往上升永遠不會掉下來？
```

**貓咪**
```
   /|_|\
   [=°ω°]  我出一題，你來試試（假裝很嚴肅）
   / つ🎯  📤 布跟紙怕什麼？
```

---

## 型態二：謎語揭曉（dismissal）

> 週五語氣更誇張；答案來自 state.riddle.answer

**兔子**
```
   (\__/)
   (≧▽≦)  好了好了，答案揭曉！年齡！（拍桌）
   / ノ🎉  你猜到了嗎？！
```

**貓咪**
```
   /)_(\
   [=-ω-]  嗯，差不多下班了，順便說一下答案是暖暖包（因為他有鐵粉）
   / っ🍵
```

---

## 型態三A：進度條（progress_bar）

> 第一行（耳朵行）接時間資訊，第二行接進度條，第三行接台詞
> 時間資訊**不可單獨成行**

**兔子**
```
   (\__/)  12:05 | 距離下班 5h 40m
   (°Д°；)  ▓▓▓▓▓░░░░░░░░░  35%
   / つ💦  你可以的！（不知道你在做什麼但你可以的）
```

**貓咪**
```
   /)_(\  17:40 | 距離下班 0h 4m
   [=-ω-]  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓░  99%
   / っ🍵  再撐 4 分鐘就自由了（端著茶陪你）
```

---

## 猜謎互動：猜對 / 猜錯

**猜對（兔子）**
```
   (\__/)
   (≧▽≦)  對了！答案就是年齡！（彈跳）
   / ノ🎊  你果然很厲害（或許）
```

**猜錯提示（貓咪）**
```
   /\_/\
   [=°ω°]  還差一點點喔（拿出線索）
   / づ🔍  再想想，方向對了
```

---

## generate_sticker.py 快速使用

```bash
# scaffold 模式（輸出 JSON 給 LLM 當提示，最省 token）
python3 scripts/generate_sticker.py scaffold --emotion coding --animal bunny --seed 42

# assemble 模式（LLM 提供台詞，程式組裝驗證）
python3 scripts/generate_sticker.py assemble \
  --emotion stressed --animal bunny \
  --line1 "你可以的！（已經躲到桌子底下）" --item 🚨

# progress_bar assemble
python3 scripts/generate_sticker.py assemble \
  --emotion tired --animal kitty --progress-bar \
  --progress "14:30|▓▓▓▓▓▓▓▓▓░░░░░░|3|15|62" \
  --line1 "再撐一下，快了"

# deterministic 模式（測試用，不呼叫 LLM）
python3 scripts/generate_sticker.py deterministic --emotion happy --animal kitty --seed 7
```
