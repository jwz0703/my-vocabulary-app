# 第 25 題：猴子吊繩子 — 動畫講解

`monkey-rope.mp4`：1920×1080、60 fps、82 秒，含配樂與音效。所有畫面與聲音都是程式產生的。

> 一隻 14.6 kg 的猴子懸吊在一條輕質繩子的中間，兩邊的繩子與水平線的夾角皆為 11.0°，求繩子的張力並與猴子的重量相比較。

**答案**：2T sin θ = mg → T = mg / (2 sin θ) = (14.6)(9.8) / (2 sin 11.0°) ≈ **375 N**，約為猴子重量（143 N）的 **2.6 倍**。

| 時間 | 段落 | 內容 |
|------|------|------|
| 0–6s | 開場 | 「第 25 題」重擊登場、故障特效提問、猴子探頭 |
| 6–16s | 題目 | 打字機逐字出題、關鍵數字螢光筆標示、已知量膠囊 |
| 16–26s | 情境 | 柱子升起、繩子拉開、猴子掉落彈跳、標出 11.0° |
| 26–36s | 自由體圖 | W 與兩條 T 箭頭射出（箭頭長度按真實比例 T : W = 2.62 : 1） |
| 36–46s | 分解 | T cos θ 左右抵消；兩個 T sin θ 滑到中間疊起來，剛好等於 mg |
| 46–58s | 計算 | 公式推導、代入數字、數字滾動到 374.9 N → 蓋章「T ≈ 375 N」 |
| 58–66s | 比較 | 長條圖：143 N vs 375 N，疊出 2.62 個 W，彩帶爆發 |
| 66–76s | 延伸 | θ 從 45° 掃到 5°，T/W 曲線上的點即時移動，音高跟著張力上升 |
| 76–82s | 解答卡 | 總結與「下一題見！」 |

## 製作

```sh
node render.mjs video.mp4 cues.json   # 無頭 Chromium 逐格繪製 canvas → x264，並輸出音效時間表
python3 audio.py cues.json audio.wav  # numpy/scipy 合成配樂 + 音效，依 cues.json 精準對齊畫面
ffmpeg -i video.mp4 -i audio.wav -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart monkey-rope.mp4
node preview.mjs outdir 12.5 40 55.5  # 輸出指定秒數的畫面（PNG）供檢查
```

字型：Noto Sans TC（SIL Open Font License，見 `fonts/OFL.txt`）。
