---
name: vertical-sketch-video
description: 本风格的竖屏知识科普短视频（≤60s）——满屏手绘简笔画配图 + AI 配音 + 三层字幕（关键词 kw / 关键句 cap / 当下所念句 sub）+ 品牌结束卡；可选「口播真人画中画」（把真人出镜做成右下圆小窗，带口型）。当用户说「做一条这种风格的视频」「竖屏手绘简笔画视频」「用手工精品那套做视频」「把这段观点做成短视频」「加个我的小窗/口播画中画」等时使用。核心纪律：先出剧本时间线、确认后再做画面；时长由旁白字数决定。
triggers:
  - "这种风格的视频"
  - "竖屏手绘简笔画视频"
  - "手绘简笔画视频"
  - "手工精品视频"
  - "把这段观点做成视频"
  - "短观点视频"
  - "口播画中画"
  - "真人小窗"
  - "vertical sketch video"
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

# 竖屏手绘简笔画视频（本风格）

## 这个 skill 是什么

这是 `article-to-video`（通用文章转视频引擎）的一个**风格预设 + 一套已验证的工程资产**。输入一段核心观点/短文，产出 ≤60s 的竖屏（9:16）知识科普短片：

**满屏白底黑线手绘简笔画（配图是主角）+ AI 配音 + 底部三层字幕（关键词 kw / 关键句 cap / 当下所念句 sub）+ 品牌结束卡。**

已产出样片（可直接抄工程）：
- `手工精品/2026-10-05_AI时代的教育何去何从/`（别让孩子只会算抛物线）
- `手工精品/2026-10-06_Agent为什么千篇一律/`（千篇一律的，只是入场券）
- `手工精品/2026-10-07_开发新App-or-找到一个新客户/`（别用忙碌逃避思考）

## 与 article-to-video 的关系

- **直接复用其脚本**：`say.py`（音色清单/试听）、`gen_tts.py`（逐场景配音 + 响度归一化 + 真实时长 `manifest.json`，含字幕分段 `segs`）、`prep_images.py`（白底透明化）、`make_cover.sh`（headless Chrome 截图）、`_voice.py`（密钥/端点分流）、`voices.json`。
- **本 skill 额外提供**：竖屏 + 品牌卡合成器 `scripts/gen_composition_v.py`、YouMind 生图模板 `scripts/gen_images.js`、**可选口播画中画 `scripts/talking_head.py`**、`templates/` 配置与封面骨架、`references/playbook.md`、`references/talking-head.md`。
- 更细的方法论（音色/停顿模型/响度/代听、布局/转场/常见报错、封面）见 `article-to-video/references/tts.md`、`composition.md`、`cover.md`。

## 风格规格（硬参数）

| 项 | 值 |
|---|---|
| 画幅 | 竖屏 1080×1920（9:16），fps 30 |
| 配图 | 纯白底 + 极细黑色手绘线条 + 火柴人（圆头、无五官），4:3，长边 1080 JPEG；**视频用透明化 PNG** |
| 背景/配色 | 纸张色 `#F6F1E6`，墨色 `#23272E`，点睛 `blue #0B63C5` / `coral #C6402C` |
| 字幕 | 三层：kw 大字（92px 衬线）/ cap 中字（44px）/ sub 当下句（31px），叠在画面下部 + 纸色渐变蒙层；层级 kw>cap>sub |
| 结束卡 | `kind:"card"`：大字 kw + 红色分隔线 + 署名（`sign_name`/`sign_line`，**只上屏、不念**） |
| 配音 | 默认 `male-deep`（龙安路风，包月 token plan；见 `article-to-video/voices.json`） |
| 语速 | 默认 `speed 1.25`（atempo；默认配音偏慢） |
| 场景间隔 | `gap 0.8` |
| 时长 | ≤60s：`字数 ÷ 语速(中文约 5 字/秒) + 标点停顿 + 场景静默` |

## 工作流

### 0. 确认参数（用 question 工具，别拍板）
画幅（默认竖屏 9:16）、音色（`say.py --list` 后让用户选，默认 `male-deep`）、内容范围与目标时长、语速、要不要品牌结束卡。

### 1. 剧本 + 时间线（先做，必须确认）
通读观点，按"配图"切场景。每场景四要素：**配图 + 旁白 + 画面关键词 kw + 字幕关键句 cap**。估算时长，产出 `视频剧本.md`（分镜表 + 汇总）交用户确认。**确认前不动画面。**

### 2. 素材准备
- 配图：**优先复用同系列已有图**（风格统一、省时）；缺的用 `scripts/gen_images.js` 生成（改 `JOBS` 的 key 与 prompt）。
- 字体：`assets/fonts/NotoSerifSC.woff2`、`NotoSansSC.woff2`（从任一样片工程拷，中文不能依赖内置字体）。

### 3. 配音（真实音频定时间线）
`python <article-to-video>/scripts/gen_tts.py --config video/video.config.json --voice male-deep`
产 `assets/audio/NN_<img>.wav` + `manifest.json`。**不要用估的时长拍画面。**

### 4. 组合
`python scripts/gen_composition_v.py --config video.config.json --manifest assets/audio/manifest.json --out index.html`（**必须用本 skill 的带 card 版**）。

### 5. 质检 → 渲染
`npx --yes hyperframes@0.8.97 lint && ... validate && ... inspect` 全绿 → `render --quality draft` 核对 → `render --quality standard`。

### 6. （可选）口播画中画
开启后，把真人出镜做成**圆形/圆角小窗**叠到成片角落（默认**右下角圆形**，带白描边 + 投影）。两步、可只用其一：`scripts/talking_head.py gen`（VideoRetalk 生成口型，¥0.08/秒、1800 秒免费）→ `overlay`（**纯本地 ffmpeg**，不花钱）。**默认关闭**；老板样本固定用 skill 自带 `assets/avatars/boss_sample.mov`（不入库），细节与坑见 `references/talking-head.md`。

### 7. 封面
改 `templates/cover.html` 文案 → `bash <article-to-video>/scripts/make_cover.sh cover.html <out.png> 1080 1920`。**做 2 版让用户挑**。

### 8. 自检（没有视觉/听觉时）
抽帧发 `qwen-vl-max`（dashscope **兼容**端点）代看排版/压主体；逐段发 `qwen3-omni-flash`（dashscope **原生**端点）代听。方法见 `references/playbook.md`。

## 铁律（本风格专有，全是踩过的坑）

1. **先剧本后画面**；时长由旁白决定。
2. **配图是主角**：先透明化，别套白卡片/边框/阴影/圆角药丸（会和手绘风格割裂）。
3. **图里禁止放大标题或成句文字**，否则与 kw/cap 字幕重复打架；只允许极小中文标签（且要代看是否乱码）。
4. **生图必须代看**：YouMind 可能写出乱码/错字、多/少元素、甚至擅自画大标题——用 `qwen-vl-max` 逐张核，不合格就改提示词重画（可只重画单张）。
5. **合成器要用带 `kind:card` 的竖屏版**（本 skill 的 `gen_composition_v.py`）。用错版本会把品牌卡当普通场景，`lint` 报 `missing_local_asset: assets/img/s7-card.png`。
6. **复用他片配图要拷两份**：`assets/img/<key>.png`（透明 hero）与 `assets/img/raw/<key>.png`（白底、给虚化补底）都要拷，缺一不可。
7. **`gen_tts` 每幕都要有 `img` 字段**（含品牌卡，给个 `s7-card` 之类占位名即可），否则生成音频文件名报错。
8. 音频必须**响度归一化**（`gen_tts` 已内置 loudnorm+压缩）；**两个账号别混**：龙系列 `qwen-audio-3.0-tts-*` 走包月 `bailian-token-plan`，克隆/cosyvoice/`qwen3-tts-*` 走按量 `dashscope-payg`。
9. 字幕 sub 的逐句时间由 `gen_tts` 写进 `manifest.segs`，合成器按 `visibility` 显隐——**不要手写**。
10. **口播画中画（可选）**：`overlay` 是纯本地 ffmpeg，**不调模型、不花钱**；只有 `gen`（生成口型）走 VideoRetalk。投影用的 `color` 源是无限流，必须 `d=<成片时长>` + `-shortest`，否则成片时长跑飞；`geq` 里逗号要转义成 `\,`（脚本已处理）。VideoRetalk 需**华北2（北京）地域 key**，且**别走系统代理**。详见 `references/talking-head.md`。

## 目录约定

```
<文章目录>/
├── 核心观点.md / content.md     # 旁白来源
├── 视频剧本.md                  # 步骤1 产出，需用户确认
├── gen_images.js                # 生图（可选）
├── 原始音视频/口播样本.mov       # 口播画中画：样本视频（可选）
├── video/
│   ├── index.html
│   ├── video.config.json
│   ├── gen_composition_v.py     # 本 skill 拷入
│   ├── head.mp4                 # 口播画中画：生成的口型片（可选）
│   ├── assets/{img, img/raw, fonts, audio}/
│   └── renders/
├── 视频封面/封面_A.png · 封面_B.png
└── 成片_<标题>.mp4
```

## scripts / templates

- `scripts/gen_composition_v.py` —— 竖屏满屏配图 + 品牌卡合成器（权威版）。
- `scripts/gen_images.js` —— YouMind 生图（含透明化 + JPEG 压缩）；改写 `JOBS` 即可复用。
- `scripts/talking_head.py` —— **可选口播画中画**：`gen`（VideoRetalk 生成口型）+ `overlay`（本地裁圆/圆角 + 描边 + 投影 + 叠角）。
- `templates/video.config.example.json` —— 配置骨架（含 card 场景 + `talking_head` 开关）。
- `templates/cover.html` —— 竖屏封面模板。
- `references/playbook.md` —— 三期实战踩坑与自检脚本片段。
- `references/talking-head.md` —— 口播画中画：VideoRetalk 事实/成本/坑、本地合成的 geq 公式与踩坑。