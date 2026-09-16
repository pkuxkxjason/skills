# HyperFrames 组合规范（满屏配图 · 关键词 · 字幕 · 转场）

HTML 即视频源码：一个 `index.html` + GSAP 时间轴，`data-*` 决定时序与轨道。

## 1. 工程与目录

```
video/
├── index.html
├── hyperframes.json          # 由 hyperframes init 生成
├── assets/
│   ├── img/                  # 透明化后的配图（主角）
│   ├── img/raw/              # 白底原图（虚化补底用）
│   ├── fonts/                # NotoSerifSC.woff2 / NotoSansSC.woff2
│   └── audio/                # 逐场景配音 wav
└── renders/                  # 渲染产物
```

初始化：`npx hyperframes init video --non-interactive`。

## 2. 中文字体（必须本地声明）

编译器内置字体不含中文。用本地 woff2：

```css
@font-face{font-family:"Noto Serif SC";src:url("assets/fonts/NotoSerifSC.woff2") format("woff2");font-weight:400 900;font-display:swap;}
@font-face{font-family:"Noto Sans SC";src:url("assets/fonts/NotoSansSC.woff2") format("woff2");font-weight:400 900;font-display:swap;}
```

> 下载 `.ttf` 后转 woff2：`pip install fonttools brotli`，`TTFont(x).save(y, flavor="woff2")`。

## 3. 满屏配图布局（4:3 图 → 16:9，不裁切）

思路：底层放**虚化放大的原图铺满**，上层放**透明化后、全高等比的原图**居中，底部加纸色渐变蒙层给文字。

```css
.bg-blur{position:absolute;inset:0;width:1920px;height:1080px;object-fit:cover;
         filter:blur(52px) brightness(1.06) saturate(1.05);opacity:.72;}
.hero{position:absolute;left:50%;top:0;width:1440px;height:1080px;object-fit:contain;transform:translateX(-50%);}
.scrim{position:absolute;left:0;bottom:0;width:1920px;height:500px;z-index:3;
       background:linear-gradient(180deg,rgba(246,241,230,0) 0%,rgba(246,241,230,.6) 38%,rgba(246,241,230,.92) 72%,rgba(246,241,230,.99) 100%);}
.kw{position:absolute;left:150px;right:150px;bottom:196px;z-index:4;
    font-family:"Noto Serif SC";font-weight:900;font-size:76px;line-height:1.22;color:#23272E;}
.cap{position:absolute;left:150px;right:150px;bottom:96px;z-index:4;}
.cap span{font-family:"Noto Sans SC";font-weight:600;font-size:36px;color:#5A5F68;}
```

```html
<div id="s2" class="scene" data-layout-allow-overflow>
  <img class="bg-blur" data-layout-ignore src="assets/img/raw/s1-hook.png">
  <img class="hero" src="assets/img/s1-hook.png">
  <div class="scrim"></div>
  <div class="kw kw-coral">越爽的顿悟，越要警惕</div>
  <div class="cap"><span>它被精心设计，只为让你转发</span></div>
</div>
```

**为什么文字放下方**：插画主体多在中上部，关键词放顶部会压住画面；下方纸色蒙层既保证可读，又不动主体。

## 4. 音频

每个场景一段音频，按**真实时长**放：

```html
<audio id="a2" data-start="8.96" data-duration="10.48" data-track-index="10"
       src="assets/audio/v3/02_s1-hook.wav"></audio>
```

`场景时长 = 音频时长 + 场景静默`（默认 0.8s）。`起点 = 上一场景起点 + 上一场景时长`。

## 5. 场景与时间轴（单时间线交替换场）

场景用 `.scene{opacity:0;visibility:hidden}` 默认隐藏，首场景可见；用一条 GSAP 时间线控制淡入淡出与元素入场：

```js
function swap(prev,next,t){
  tl.to("#"+prev,{opacity:0,duration:0.35,ease:"power2.inOut"},t);
  tl.set("#"+prev,{visibility:"hidden"},t+0.36);          // 让对比度/布局审计忽略已离场元素
  tl.set("#"+next,{visibility:"visible"},t+0.02);
  tl.to("#"+next,{opacity:1,duration:0.4,ease:"power2.inOut"},t);
  entrance(next,t);
}
function entrance(id,t){
  tl.from("#"+id+" .hero",{opacity:0,scale:0.96,duration:0.6,ease:"power3.out"},t+0.15);  // scale<1，别越界
  tl.from("#"+id+" .kw",{opacity:0,y:16,duration:0.5,ease:"power2.out"},t+0.28);
  tl.from("#"+id+" .cap",{opacity:0,duration:0.5,ease:"power2.out"},t+0.5);
}
```

## 6. 必踩的坑

- **`mix-blend-mode` 会被层叠上下文隔离**：若插画的祖先有 `z-index`/`transform`/`opacity<1`，multiply 就不生效（白底还在）。**直接用透明化 PNG**，别指望混合模式。
- **`inspect` 报 overflow**：入场动画不要越界（别用 `scale>1`、别把 `y` 顶出画布）。必须大的装饰（如虚化底图）加 `data-layout-ignore`，动画容器加 `data-layout-allow-overflow`。`clipped_text` 不接受 allow-overflow，只能改动画。
- **单入口**：工程里只能有一个带 `data-composition-id` 的 `index.html`。备份旧组合要改名去掉 `.html`，否则报 `multiple_root_compositions`。
- **中文渲染**：像素级自检——字幕区应有 7%~13% 暗像素（文字墨迹），否则可能字体没生效。
- **对比度**：`validate` 的 WCAG 审计会把隐藏场景里的元素也算进去，用第 5 节的 `visibility` 切换让它只测可见场景。

## 7. 质检与渲染

```bash
npx hyperframes lint        # 0 error
npx hyperframes validate    # 对比度 + 无 console error
npx hyperframes inspect     # 0 layout issues
npx hyperframes render --quality draft --output renders/draft.mp4     # 先小样
npx hyperframes render --quality standard --output renders/final.mp4  # 正式
```

## 8. 代看自检（没有视觉时的眼睛）

渲染帧发 `qwen-vl-max`（兼容端点），问：插画是否满屏/是否主角、叠加文字是否压主体、排版有无重叠、美感打分。base64 过长要用 `--data-binary @file`。

> 注意：手绘信息图**内部自带文字**，VL 说的"顶部标题拥挤"多半是画里的字，不是你的叠加——先确认再改。