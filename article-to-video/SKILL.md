---
name: article-to-video
description: 把一篇带配图的公众号/Markdown 文章，做成横屏视频——满屏配图 + AI 配音 + 关键词与字幕 + 上传封面。当用户说「把这篇公众号/文章做成视频」「文章转视频」「给文章配音」「生成视频封面」「文章生成视频」等时使用。核心纪律：先出剧本时间线、确认后再做画面；时长由旁白字数决定。
triggers:
  - "文章做成视频"
  - "公众号转视频"
  - "文章转视频"
  - "文章生成视频"
  - "给文章配音"
  - "文章配视频"
  - "生成视频封面"
  - "article to video"
  - "article video"
platform:
  - opencode
allowed-tools:
  - Bash(*)
  - Read(*)
  - Write(*)
  - Edit(*)
  - Glob(*)
  - Grep(*)
---

# 文章转视频

## 这个 skill 做什么

**输入**：一篇带配图的公众号/Markdown 文章（`content.md` 正文 + `img-*.png`/`封面.jpg` 配图）。
**输出**：横屏视频（满屏配图 + AI 配音 + 关键词与字幕）+ 一版上传封面。

适合知识科普类长文：用文章自己的手绘配图当主角，配上沉稳的旁白，做成 B 站/视频号能发的成片。

---

## 铁律（先读，全是踩过的坑）

1. **先出带时间线的剧本，确认后再做画面。** 不要一上来就写组合、渲染——画面是剧本的投影，剧本错了画面全废。

2. **时长由旁白决定，不是拍脑袋。** 旁白取自正文，`时长 = 字数 ÷ 语速`。中文配音约 **300 字/分钟（5 字/秒）**，另加句间停顿与场景静默。拿到数量级离谱的参数（如"每秒 200 字"）先质疑、核对单位。

3. **配图比例 ≠ 画幅时，不裁切。** 4:3 配图放进 16:9，用「虚化放大补底 + 原图全高居中」。裁切会切掉画面内容。

4. **配图是主角，别给它套卡片。** 白卡片边框/阴影/圆角药丸会和手绘风格"割裂"。先给白底配图做**透明化**预处理，让墨线直接落在纸张背景上。

5. **文字放画面下方（下部信息区）。** 大关键词 + 一句小字幕叠加在底部，用纸色渐变蒙层保证可读。放顶部会压住插画主体（主体多在中上部）。

6. **没有视觉/听觉时，用别的模型代看/代听。** 见「自检」一节——这是保证质量的关键，不要盲交付。

7. **音频必须做响度归一化。** TTS 各段音量天然不齐（实测能差 8dB+），不归一化会"忽大忽小"非常难听。

---

## 工作流

### 0. 确认参数（用 question 工具，别自己拍板）

- **目标平台/画幅**：横屏 16:9（B 站/公众号）/ 竖屏 9:16（抖音/视频号）/ 4:3
- **配音音色**：男/女、气质。**先给几版试听样本让用户选**（不同模型/音色差异很大）
- **内容范围**：全文 vs 节选精华；目标时长
- **字幕形态**：字幕=旁白全文，还是只留「点到为止」的关键句
- **工程与输出目录**：默认 `<文章目录>/video/`

### 1. 剧本 + 时间线（先做，必须确认）

1. 通读正文，按配图切分为场景。每场景四要素：**配图 + 旁白（取自正文，可精简）+ 画面关键词 + 字幕关键句**。
2. 估算时长：`语音秒数 = 中文字数/5 + 标点停顿`（停顿模型见 `references/tts.md`），加场景静默（默认 0.8s）。
3. 产出 `视频剧本.md`（分镜表 + 汇总），交用户确认。**确认前不动画面。**

### 2. 素材准备

- **配图透明化**：`python scripts/prep_images.py --dir <素材目录>`（原图备份到 `raw/`）。
- **中文字体**：下载 Noto Serif SC / Noto Sans SC 并转 woff2 放 `video/assets/fonts/`。中文不能依赖编译器内置字体，必须本地 `@font-face`。

### 3. 配音（真实音频定时间线）

- 选模型与音色（见 `references/tts.md`），用 `scripts/gen_tts.py` 按 `video.config.json` 逐场景生成。
- 每段**响度归一化 + 轻压缩**，再测**真实时长**，写 `manifest.json`。
- **不要用估的时长拍画面**——用真实音频时长。

### 4. 构建组合（HyperFrames）

- `python scripts/gen_composition.py` 依据 `video.config.json` + `manifest.json` 生成 `index.html`。
- 布局与坑见 `references/composition.md`。
- 质检：`lint` → `validate`（对比度）→ `inspect`（布局），**全绿再渲染**。

### 5. 渲染

- 先 `--quality draft` 出小样核对，满意再 `--quality standard`。

### 6. 封面

- `bash scripts/make_cover.sh`（headless Chrome 截图 HTML）。见 `references/cover.md`。
- **优先复用文章已有封面**（作者自己的视觉），可做与视频同风格的纸张版作为备选。

### 7. 自检（没有视觉/听觉能力时）

- **代看画面**：渲染帧发 `qwen-vl-max`（dashscope 兼容端点），评估排版/美感/是否压主体。
- **代听配音**：音频发 `qwen3-omni-flash`（dashscope 原生端点），转录并评估自然度/音量/机械感。
- 方法与踩坑（如 base64 过长要用 `--data-binary @file`）见 `references/tts.md` 与 `references/composition.md`。

---

## 依赖与密钥

- Node ≥ 22、FFmpeg、HyperFrames CLI（`npx hyperframes`）、Puppeteer Chrome、Python（numpy/Pillow）。
- **绝不在任何文件里写死 API Key。** 从环境变量读取（如 `DASHSCOPE_API_KEY`），或复用用户的 opencode provider 配置。生成脚本只接受 `--api-key-env` 之类参数。

---

## 目录约定

```
<文章目录>/
├── content.md                # 正文（旁白来源）
├── 封面.jpg / img-*.png       # 配图
├── 视频剧本.md                # 步骤1 产出，需用户确认
├── 配音/                      # 逐场景 wav + 完整旁白 + manifest.json
├── 视频封面/                  # 上传封面 png/jpg
└── video/                     # HyperFrames 工程
    ├── index.html             # 组合
    ├── video.config.json      # 场景/配色/字体配置
    ├── assets/{img,fonts,audio,img/raw}/
    ── renders/*.mp4
```

---

## references

- `references/tts.md` —— TTS 选型、端点、指令写法、情感标签、停顿模型、响度归一化、代听自检。
- `references/composition.md` —— HyperFrames 组合规范、满屏配图布局、转场、质检、常见报错。
- `references/cover.md` —— 封面生成（尺寸、复用原封面、headless 截图）。

## scripts

- `scripts/prep_images.py` —— 配图白底透明化（亮度羽化）。
- `scripts/gen_tts.py` —— 逐场景 TTS + 响度归一化 + 真实时长 manifest。
- `scripts/gen_composition.py` —— 依据配置与 manifest 生成 `index.html`。
- `scripts/make_cover.sh` —— headless Chrome 把封面 HTML 截成 png。