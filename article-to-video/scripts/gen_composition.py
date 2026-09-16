#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
依据 video.config.json（配色/字体/封面）+ manifest.json（真实时长）生成 HyperFrames index.html。

用法:
  python gen_composition.py --config video/video.config.json --manifest video/assets/audio/manifest.json \
      --out video/index.html

约定:
  配图: assets/img/<img>.png（透明） 与 assets/img/raw/<img>.png（白底）
  音频: assets/audio/<NN>_<img>.wav
  字体: assets/fonts/*.woff2
"""
import argparse, json, os

CSS = """<!doctype html><html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width={W}, height={H}">
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>
@font-face{{font-family:"Noto Serif SC";src:url("{SERIF}") format("woff2");font-weight:400 900;font-display:swap;}}
@font-face{{font-family:"Noto Sans SC";src:url("{SANS}") format("woff2");font-weight:400 900;font-display:swap;}}
:root{{--paper:{PAPER};--ink:{INK};--ink-soft:{INK_SOFT};--blue:{BLUE};--coral:{CORAL};}}
*{{margin:0;padding:0;box-sizing:border-box;}}
html,body{{margin:0;width:{W}px;height:{H}px;overflow:hidden;background:var(--paper);font-family:"Noto Sans SC",sans-serif;}}
.bg-layer{{position:absolute;top:0;left:0;width:{W}px;height:{H}px;background:var(--paper);z-index:0;}}
.bg-glow{{position:absolute;border-radius:50%;}}
.bg-glow1{{width:1500px;height:1500px;left:-360px;top:-320px;background:radial-gradient(circle,rgba(11,99,197,.09) 0%,rgba(246,241,230,0) 64%);}}
.bg-glow2{{width:1400px;height:1400px;right:-300px;bottom:-380px;background:radial-gradient(circle,rgba(198,64,44,.06) 0%,rgba(246,241,230,0) 64%);opacity:.7;}}
.scene{{position:absolute;top:0;left:0;width:{W}px;height:{H}px;overflow:hidden;background:var(--paper);opacity:0;visibility:hidden;}}
#s1{{opacity:1;visibility:visible;background:var(--ink);}}
.bg-blur{{position:absolute;inset:0;width:{W}px;height:{H}px;object-fit:cover;filter:blur(52px) brightness(1.06) saturate(1.05);opacity:.72;}}
.hero{{position:absolute;left:50%;top:0;width:{HERO_W}px;height:{H}px;object-fit:contain;transform:translateX(-50%);}}
.scrim{{position:absolute;left:0;bottom:0;width:{W}px;height:500px;z-index:3;background:linear-gradient(180deg,rgba(246,241,230,0) 0%,rgba(246,241,230,.6) 38%,rgba(246,241,230,.92) 72%,rgba(246,241,230,.99) 100%);}}
.kw{{position:absolute;left:150px;right:150px;bottom:196px;z-index:4;font-family:"Noto Serif SC",serif;font-weight:900;font-size:76px;line-height:1.22;color:var(--ink);}}
.kw-blue{{color:var(--blue);}} .kw-coral{{color:var(--coral);}}
.cap{{position:absolute;left:150px;right:150px;bottom:96px;z-index:4;}}
.cap span{{font-family:"Noto Sans SC",sans-serif;font-weight:600;font-size:36px;line-height:1.4;color:var(--ink-soft);}}
.cover{{position:absolute;inset:0;width:{W}px;height:{H}px;object-fit:cover;z-index:0;}}
.cover-shade{{position:absolute;inset:0;width:{W}px;height:{H}px;z-index:1;background:linear-gradient(180deg,rgba(13,18,26,.58) 0%,rgba(13,18,26,.28) 45%,rgba(13,18,26,.74) 100%);}}
.cover-content{{position:absolute;inset:0;z-index:2;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;gap:30px;}}
.series-tag{{font-family:"Noto Sans SC",sans-serif;font-weight:700;font-size:28px;letter-spacing:.3em;color:#BFE0FF;}}
.title-t1{{font-family:"Noto Serif SC",serif;font-weight:900;font-size:118px;line-height:1.24;color:#FFFFFF;text-shadow:0 6px 40px rgba(0,0,0,.45);}}
.title-en{{font-family:"Noto Serif SC",serif;font-weight:900;font-size:96px;line-height:1.2;color:#6CC4FF;text-shadow:0 6px 40px rgba(0,0,0,.45);}}
</style></head><body>
<div id="main" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="{W}" data-height="{H}">
  <div class="bg-layer"><div class="bg-glow bg-glow1"></div><div class="bg-glow bg-glow2"></div></div>
"""


def build(cfg, manifest):
    th = cfg.get("theme", {})
    subs = dict(
        W=cfg.get("width", 1920), H=cfg.get("height", 1080),
        HERO_W=int(cfg.get("height", 1080) * 4 / 3),
        PAPER=th.get("paper", "#F6F1E6"), INK=th.get("ink", "#23272E"),
        INK_SOFT=th.get("ink_soft", "#5A5F68"), BLUE=th.get("blue", "#0B63C5"),
        CORAL=th.get("coral", "#C6402C"),
        SERIF=cfg.get("fonts", {}).get("serif", "assets/fonts/NotoSerifSC.woff2"),
        SANS=cfg.get("fonts", {}).get("sans", "assets/fonts/NotoSansSC.woff2"),
    )
    total = round(manifest[-1]["start"] + manifest[-1]["dur"], 2)
    subs["TOTAL"] = total
    out = [CSS.format(**subs)]

    # cover scene
    cov = cfg.get("cover", {})
    lines = cov.get("lines", [])
    tag = cov.get("tag", "")
    out.append(f'  <div id="s1" class="scene" data-layout-allow-overflow>\n'
               f'    <img class="cover" src="{cov.get("img","assets/img/cover.jpg")}" alt="">\n'
               f'    <div class="cover-shade"></div>\n    <div class="cover-content">\n')
    if tag:
        out.append(f'      <div class="series-tag">{tag}</div>\n')
    for ln in lines:
        cls = "title-en" if ln.get("cls") == "accent" else "title-t1"
        out.append(f'      <div class="{cls}">{ln["text"]}</div>\n')
    out.append('    </div>\n  </div>\n')

    # content scenes
    for r in manifest[1:]:
        color = r.get("color", "ink")
        cls = "" if color == "ink" else f' kw-{color}'
        out.append(
            f'  <div id="s{r["id"]}" class="scene" data-layout-allow-overflow>\n'
            f'    <img class="bg-blur" data-layout-ignore src="assets/img/raw/{r["img"]}.png" alt="">\n'
            f'    <img class="hero" src="assets/img/{r["img"]}.png" alt="">\n'
            f'    <div class="scrim"></div>\n'
            f'    <div class="kw{cls}">{r["kw"]}</div>\n'
            f'    <div class="cap"><span>{r["sub"]}</span></div>\n  </div>\n')

    # audio
    out.append('  <!-- narration -->\n')
    for r in manifest:
        out.append(f'  <audio id="a{r["id"]}" data-start="{r["start"]}" data-duration="{r["audio"]}" '
                   f'data-track-index="10" src="assets/audio/{r["id"]:02d}_{r["img"]}.wav"></audio>\n')
    out.append('</div>\n')

    # timeline
    js = ['<script>\n  window.__timelines = window.__timelines || {};\n  var tl = gsap.timeline({ paused: true });\n',
          '  tl.from("#s1 .cover",{opacity:0,duration:1.2,ease:"power2.out"},0);\n',
          '  tl.from("#s1 .series-tag",{y:-18,opacity:0,duration:0.6,ease:"power2.out"},0.15);\n']
    n_lines = len(lines)
    for i, ln in enumerate(lines):
        sel = "title-en" if ln.get("cls") == "accent" else "title-t1"
        js.append(f'  tl.from("#s1 .{sel}",{{y:40,opacity:0,duration:0.7,ease:"power3.out"}},{0.35+i*0.25});\n')
    js.append('''  function entrance(id,t){
    tl.from("#"+id+" .hero",{opacity:0,scale:0.96,duration:0.6,ease:"power3.out"},t+0.15);
    tl.from("#"+id+" .kw",{opacity:0,y:16,duration:0.5,ease:"power2.out"},t+0.28);
    tl.from("#"+id+" .cap",{opacity:0,duration:0.5,ease:"power2.out"},t+0.5);
  }
  function swap(prev,next,t){
    tl.to("#"+prev,{opacity:0,duration:0.35,ease:"power2.inOut"},t);
    tl.set("#"+prev,{visibility:"hidden"},t+0.36);
    tl.set("#"+next,{visibility:"visible"},t+0.02);
    tl.to("#"+next,{opacity:1,duration:0.4,ease:"power2.inOut"},t);
    entrance(next,t);
  }
''')
    for i in range(2, len(manifest) + 1):
        js.append(f'  swap("s{i-1}","s{i}",{manifest[i-1]["start"]});\n')
    js.append('  tl.from(".bg-glow1",{scale:0.92,opacity:0.6,duration:9,repeat:27,yoyo:true,ease:"sine.inOut"},0);\n')
    js.append('  tl.from(".bg-glow2",{scale:1.1,opacity:0.5,duration:9,repeat:27,yoyo:true,ease:"sine.inOut"},0);\n')
    js.append('  window.__timelines["main"] = tl;\n</script>\n</body></html>\n')
    out.append("".join(js))
    return "".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    cfg = json.load(open(args.config, encoding="utf-8"))
    manifest = json.load(open(args.manifest, encoding="utf-8"))
    html = build(cfg, manifest)
    open(args.out, "w", encoding="utf-8").write(html)
    print("wrote", args.out, "total", round(manifest[-1]["start"] + manifest[-1]["dur"], 2), "s")


if __name__ == "__main__":
    main()