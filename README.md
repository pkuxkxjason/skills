# skills

一个集中管理 AI Agent Skills（技能）的仓库。每个子目录即一个独立的 skill，可被 Claude Code、opencode 等支持 Agent Skills 的工具加载使用。

## 目录

- [article-illustrator](./article-illustrator/) — 文章自动配图
- [article-to-video](./article-to-video/) — 带配图的公众号文章转视频（配音 / 字幕 / 封面）
- [md2wchtml](./md2wchtml/) — Markdown 转微信公众号风格 HTML
- [vertical-sketch-video](./vertical-sketch-video/) — 竖屏手绘简笔画知识短视频（≤60s，竖屏 9:16，可选口播画中画）

## 技能说明

### article-illustrator

读取 Markdown 文章，通过标题结构自动切分章节，提取每节主题，使用 YouMind CLI 生成手绘简笔画风格配图，下载到文章同目录并插入到 markdown 文件的对应章节末尾。

```bash
node scripts/generate-images.js <markdown-file>            # 为所有章节配图
node scripts/generate-images.js <markdown-file> --replace <section-index>  # 替换某节配图
```

### article-to-video

把一篇带配图的公众号 / Markdown 文章，做成横屏视频——满屏配图 + AI 配音 + 关键词与字幕 + 上传封面。用文章自己的手绘配图当主角，配沉稳旁白，产出 B 站 / 视频号可发的成片。

核心纪律（也是踩过的坑）：**先出带时间线的剧本、确认后再做画面**；时长由旁白字数决定（中文约 300 字/分）；4:3 配图放进 16:9 用「虚化补底 + 不裁切」；白底配图先做透明化、别套卡片；文字放画面下部避免压主体；音频必须做响度归一化；没有视觉 / 听觉时用 `qwen-vl-max` 代看、`qwen3-omni-flash` 代听。

```bash
python3 scripts/prep_images.py --dir video/assets/img          # 配图白底透明化
python3 scripts/gen_tts.py --config video/video.config.json    # 逐场景配音 + 响度归一化
python3 scripts/gen_composition.py --config video/video.config.json \
        --manifest video/assets/audio/manifest.json --out video/index.html
bash scripts/make_cover.sh 封面.html 视频封面/封面.png          # 封面截图
```

依赖：Node ≥ 22、FFmpeg、HyperFrames CLI、Puppeteer Chrome、Python(numpy/Pillow)。需在环境变量里提供 TTS 的 API Key（如 `DASHSCOPE_API_KEY`）。

### md2wchtml

将 Markdown 文件转换为微信公众号风格的 HTML。自动生成紫色主题、标题左边框、引用块渐变背景、图片居中、高亮紫色加粗等效果，全部使用内联样式，可直接复制到公众号编辑器。

```bash
python3 md2wchtml.py 文章.md          # 自动生成 [原文件名].html
python3 md2wchtml.py 文章.md 输出.html # 指定输出文件
```

### vertical-sketch-video

竖屏（9:16）知识科普短视频（≤60s）——满屏白底黑线手绘简笔画配图 + AI 配音 + 三层字幕（关键词 kw / 关键句 cap / 当下所念句 sub）+ 品牌结束卡。它是 `article-to-video` 的**风格预设 + 已验证工程资产**，直接复用其配音/透明化/封面脚本，额外提供竖屏带品牌卡合成器、生图模板与**可选「口播真人画中画」**（右下圆小窗 + 口型）。

核心纪律：**先出剧本时间线、确认后再做画面**；配图是主角（禁套卡片/边框）；图里禁放大标题或成句文字；生图必须用 `qwen-vl-max` 代看；字幕时间由 `gen_tts` 的 `manifest.segs` 驱动。

```bash
python3 scripts/gen_tts.py --config video/video.config.json --voice male-deep   # 配音（复用 article-to-video）
python3 scripts/gen_composition_v.py --config video.config.json \
        --manifest assets/audio/manifest.json --out index.html                  # 竖屏 + 品牌卡合成
python3 scripts/talking_head.py gen     # 可选：VideoRetalk 生成口型
python3 scripts/talking_head.py overlay # 可选：本地 ffmpeg 裁圆/圆角叠角（不花钱）
```

依赖同 `article-to-video`；口播画中画需阿里云百炼 VideoRetalk（华北2 北京地域）。

## 使用方法

1. 克隆本仓库：`git clone https://github.com/pkuxkxjason/skills.git`
2. 将需要的 skill 子目录复制到你项目对应位置的 skills 目录（如 `.agents/skills/<skill-name>/`）
3. 在你的对话中触发该 skill，或按各 skill 文档中的说明直接使用其命令行工具

## 工具要求

- 各 skill 的脚本.基于 Python 3 或 Node.js 运行
- 部分技能依赖 YouMind 等外部 API，请参照各 skill 内的说明配置

## 关于作者

资深技术人，外企黄金时代幸存者，金融数字化践行者。分享 40+ 职场人转型之路和企业数字化再增长。

## License

MIT