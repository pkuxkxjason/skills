# 封面生成

## 1. 尺寸

| 平台 | 比例 | 建议尺寸 |
|---|---|---|
| B 站 / 公众号视频 | 16:9 | 1920×1080 |
| 视频号 | 约 3.35:1（横版） / 1:1 | 按平台要求另出 |
| 抖音 | 9:16 | 1080×1920 |

默认出 **1920×1080**，如需其它比例再补。

## 2. 两种做法（优先复用作者已有封面）

**做法 A（推荐）：复用文章已有封面**
作者通常已设计好文章封面（自带标题与角色）。把它**完整不裁**地放进 16:9，两侧/上下用**同一张图虚化**补底，再压一个系列角标。既保留品牌视觉，又不裁角色。

```html
<style>
body{width:1920px;height:1080px;margin:0;background:#0d121a;}
.blur{position:absolute;inset:0;width:1920px;height:1080px;object-fit:cover;filter:blur(60px) brightness(.5) saturate(1.1);}
.main{position:absolute;left:0;top:50%;transform:translateY(-50%);width:1920px;height:817px;object-fit:contain;}
.tag{position:absolute;left:0;right:0;top:52px;text-align:center;font-weight:700;font-size:34px;letter-spacing:.3em;color:#BFE0FF;}
</style>
<img class="blur" src="assets/cover.jpg"><img class="main" src="assets/cover.jpg">
<div class="tag">系统化思维 · 系列第一篇</div>
```

**做法 B：与视频同风格的纸张版**
纸张底 + 宋体大标题（`警惕别人塞给你的 / Aha Moment！`）+ 左侧文案、右侧手绘配图 + 短钩子句。适合没有现成封面、或想要统一视觉时。

## 3. 截图（headless Chrome）

```bash
CHROME=~/.cache/puppeteer/chrome-headless-shell/*/chrome-headless-shell-mac-arm64/chrome-headless-shell
"$CHROME" --headless --disable-gpu --hide-scrollbars \
  --force-device-scale-factor=1 --virtual-time-budget=5000 \
  --window-size=1920,1080 \
  --screenshot="视频封面/封面.png" "file:///abs/path/cover.html"
```

- `--virtual-time-budget=5000` 等**字体加载完**再截，否则可能截到无字/回退字体。
- HTML 里的 `@font-face`、图片用**相对路径**（把素材拷到 HTML 同目录）。
- 转 jpg 上传：`sips -s format jpeg -s formatOptions 90 in.png --out out.jpg`（macOS）。

## 4. 自检

把封面发 `qwen-vl-max`：标题在缩略图尺寸是否看得清、有无重叠/裁剪、吸引力打分。通常做 2~3 版让用户挑，不要只出一版。