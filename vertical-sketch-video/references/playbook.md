# 实战 playbook · 竖屏手绘简笔画视频

> 来自三期样片（10-05 教育 / 10-06 千篇一律 / 10-07 新App）的复盘。配套 `article-to-video` 的 `references/`。

## 1. 流程顺序（别跳步）

```
确认参数 → 剧本+时间线(确认) → 生图/复用图+透明化 → 字体 → 配音(真实时长)
→ 合成(gen_composition_v) → lint/validate/inspect → draft → standard → 封面 → 自检
```

**最容易返工的地方**：①没确认剧本就做画面；②生图后没代看，等到渲染才发现图里乱码/大标题。

## 2. 生图（YouMind）要点

- 模板：`YouMind` 的手绘简笔画 prompt（纯白底、极细黑线、火柴人、4:3）。
- `scripts/gen_images.js` 从样片拷来，改 `JOBS` 的 key/prompt 即可；每条 prompt 结尾都要重申："不要任何大标题/成句文字，最多极小的中文词；线条克制、留白充足"。
- 输出三件套：`assets/img/raw/<key>.png`（白底原图）、`assets/img/<key>.png`（透明化 hero）、`assets/img/<key>.jpg`（白底压缩，长边 1080 / q82）。
- **生成后必做代看**（见 §5）。不合格只重跑那一条：`node gen_images.js --only <key>`。
- 复用他片配图时，`assets/img/<key>.png` 和 `assets/img/raw/<key>.png` **两份都要拷**。

## 3. 合成器的两个坑

1. **必须用带 `kind:card` 的竖屏版**（本 skill `scripts/gen_composition_v.py`）。用了不含 card 的版本，品牌卡会被当普通场景渲染：
   `lint` 报 `missing_local_asset: assets/img/s7-card.png / assets/img/raw/s7-card.png`。
2. **`gen_tts` 每幕都要 `img`**（含 card 幕），否则 `f"{id:02d}_{img}.wav"` 报错；card 幕给个占位名如 `s7-card`。

## 4. 音频

- 龙系列 `qwen-audio-3.0-tts-*` 走 **包月** `bailian-token-plan`（`DASHSCOPE_TOKEN_PLAN_KEY`）；克隆/cosyvoice/`qwen3-tts-*` 走 **按量** `dashscope-payg`。混了会 `InvalidApiKey` 或 `Model not exist`。
- 多音字：只改配音、不改字幕时，用可选字段 `scene.tts_text`（字幕仍显示 `narration` 原字）。
- 每段已做 loudnorm + 轻压缩，段间音量才齐。

## 5. 自检脚本（无视觉/听觉时的眼睛和耳朵）

### 5.1 代看画面/封面（`qwen-vl-max`，dashscope **兼容**端点）

```python
import json,os,base64,urllib.request
key=json.load(open(os.path.expanduser("~/.config/opencode/opencode.json")))["provider"]["dashscope-payg"]["options"]["apiKey"]
url="https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
b=base64.b64encode(open("frame.jpg","rb").read()).decode()
body={"model":"qwen-vl-max","messages":[{"role":"user","content":[
  {"type":"image_url","image_url":{"url":"data:image/jpeg;base64,"+b}},
  {"type":"text","text":"这是竖屏视频抽帧。检查：1)底部kw/cap/sub是否互相或与主体重叠、是否越界；2)插画是否完整为主角（有无裁切）；3)中文有无乱码/错字；4)排版美观度。简短分点+结论。"}]}]}
req=urllib.request.Request(url,data=json.dumps(body).encode(),
  headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"})
print(json.load(urllib.request.urlopen(req,timeout=180))["choices"][0]["message"]["content"])
```

多条/多帧时把多个 `image_url` 塞进同一条 message（前面加 `{"type":"text","text":"[帧1]"}` 标记），一次评完更省事。

### 5.2 代听配音（`qwen3-omni-flash`，dashscope **原生**端点）

```python
import json,os,base64,urllib.request
key=json.load(open(os.path.expanduser("~/.config/opencode/opencode.json")))["provider"]["dashscope-payg"]["options"]["apiKey"]
url="https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
b=base64.b64encode(open("assets/audio/02_xxx.wav","rb").read()).decode()
body={"model":"qwen3-omni-flash","input":{"messages":[{"role":"user","content":[
  {"text":"转录这段中文配音，评估：男/女声、语速、音量是否平稳、有无机械感/念错字，自然度1-10。"},
  {"audio":"data:audio/wav;base64,"+b}]}]},"parameters":{"result_format":"message"}}
req=urllib.request.Request(url,data=json.dumps(body).encode(),
  headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"})
r=json.load(urllib.request.urlopen(req,timeout=180))
c=r["output"]["choices"][0]["message"]["content"]
print(" ".join(x.get("text","") for x in c if isinstance(x,dict)))
```

**坑**：兼容端点的音频只收 URL、不收 base64 → 必须用原生端点 + `data:audio/wav;base64,`；body 大时用 `curl --data-binary @file`。

### 5.3 抽帧

```bash
for t in 3 9 18 27 35 43 50; do
  ffmpeg -y -loglevel error -ss $t -i renders/<成片>.mp4 -frames:v 1 -q:v 3 "renders/frames/f${t}.jpg"
done
```

## 6. 汇总检查表（交付前）

- [ ] `ffprobe` 时长 ≤60s
- [ ] `lint` / `validate` / `inspect` 全绿
- [ ] 抽帧代看：排版不压主体、字幕不越界、末帧品牌卡正常
- [ ] 逐段代听：音色/语速/音量正常、无错字
- [ ] 封面 2 版已出、发用户挑
- [ ] 成片归档 `<文章目录>/成片_<标题>.mp4`