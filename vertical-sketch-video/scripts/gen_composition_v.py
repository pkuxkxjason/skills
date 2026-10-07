#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
竖屏 9:16 组合生成器（改编自 article-to-video/scripts/gen_composition.py，去掉封面特例、改为竖屏满屏配图布局）。

用法:
  python gen_composition_v.py --config video.config.json --manifest assets/audio/manifest.json --out index.html

约定:
  配图(透明): assets/img/<img>.png   配图(白底): assets/img/raw/<img>.png
  音频: assets/audio/<NN>_<img>.wav   字体: assets/fonts/*.woff2

竖屏布局: 配图等比缩放到画幅宽(留边距)居中于上半区；底部三层文字 kw/cap/sub + 纸色蒙层。
"""
import argparse
import json


def build(cfg, manifest):
    W = cfg.get("width", 1080)
    H = cfg.get("height", 1920)
    th = cfg.get("theme", {})

    HERO_W = int(W * 0.94)          # 配图宽（左右留 3%）
    HERO_TOP = int(H * 0.185)       # 配图顶
    CSS = """<!doctype html><html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width={W}, height={H}">
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>
@font-face{{font-family:"Noto Serif SC";src:url("{SERIF}") format("woff2");font-weight:400 900;font-display:swap;}}
@font-face{{font-family:"Noto Sans SC";src:url("{SANS}") format("woff2");font-weight:400 900;font-display:swap;}}
:root{{--paper:{PAPER};--ink:{INK};--ink-soft:{INK_SOFT};--blue:{BLUE};--coral:{CORAL};--green:{GREEN};}}
*{{margin:0;padding:0;box-sizing:border-box;}}
html,body{{margin:0;width:{W}px;height:{H}px;overflow:hidden;background:var(--paper);font-family:"Noto Sans SC",sans-serif;}}
.bg-layer{{position:absolute;top:0;left:0;width:{W}px;height:{H}px;background:var(--paper);z-index:0;}}
.bg-glow{{position:absolute;border-radius:50%;}}
.bg-glow1{{width:1500px;height:1500px;left:-420px;top:-360px;background:radial-gradient(circle,rgba(11,99,197,.09) 0%,rgba(246,241,230,0) 64%);}}
.bg-glow2{{width:1400px;height:1400px;right:-360px;bottom:-420px;background:radial-gradient(circle,rgba(198,64,44,.06) 0%,rgba(246,241,230,0) 64%);opacity:.7;}}
.scene{{position:absolute;top:0;left:0;width:{W}px;height:{H}px;overflow:hidden;background:var(--paper);opacity:0;visibility:hidden;}}
#s1{{opacity:1;visibility:visible;}}
.bg-blur{{position:absolute;inset:0;width:{W}px;height:{H}px;object-fit:cover;filter:blur(48px) brightness(1.04) saturate(1.03);opacity:.5;}}
.hero{{position:absolute;left:50%;top:{HERO_TOP}px;width:{HERO_W}px;height:auto;object-fit:contain;transform:translateX(-50%);}}
.scrim{{position:absolute;left:0;bottom:0;width:{W}px;height:1000px;z-index:3;background:linear-gradient(180deg,rgba(246,241,230,0) 0%,rgba(246,241,230,.55) 30%,rgba(246,241,230,.9) 62%,rgba(246,241,230,.99) 100%);}}
.kw{{position:absolute;left:110px;right:110px;bottom:466px;z-index:4;text-align:center;font-family:"Noto Serif SC",serif;font-weight:900;font-size:92px;line-height:1.2;color:var(--ink);}}
.kw-blue{{color:var(--blue);}} .kw-coral{{color:var(--coral);}} .kw-green{{color:var(--green);}}
.cap{{position:absolute;left:110px;right:110px;bottom:350px;z-index:4;text-align:center;}}
.cap span{{font-family:"Noto Sans SC",sans-serif;font-weight:600;font-size:44px;line-height:1.42;color:var(--ink-soft);}}
.sub{{position:absolute;left:110px;right:110px;bottom:198px;z-index:5;height:56px;}}
.sub span{{position:absolute;left:0;right:0;bottom:0;text-align:center;font-family:"Noto Sans SC",sans-serif;font-weight:400;font-size:31px;line-height:1.35;color:var(--ink-soft);visibility:hidden;}}
.card-wrap{{position:absolute;left:90px;right:90px;top:566px;z-index:4;text-align:center;}}
.card-kw{{font-family:"Noto Serif SC",serif;font-weight:900;font-size:104px;line-height:1.22;color:var(--coral);}}
.card-rule{{width:200px;height:6px;background:var(--coral);margin:64px auto;border-radius:3px;}}
.card-sign{{font-family:"Noto Sans SC",sans-serif;font-weight:800;font-size:64px;line-height:1.4;color:var(--ink);}}
.card-sign .soft{{display:block;margin-top:26px;font-weight:500;font-size:40px;color:var(--ink-soft);}}
</style></head><body>
<div id="main" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="{W}" data-height="{H}">
  <div class="bg-layer"><div class="bg-glow bg-glow1"></div><div class="bg-glow bg-glow2"></div></div>
""".format(
        W=W, H=H, HERO_W=HERO_W, HERO_TOP=HERO_TOP, TOTAL=round(manifest[-1]["start"] + manifest[-1]["dur"], 2),
        PAPER=th.get("paper", "#F6F1E6"), INK=th.get("ink", "#23272E"), INK_SOFT=th.get("ink_soft", "#5A5F68"),
        BLUE=th.get("blue", "#0B63C5"), CORAL=th.get("coral", "#C6402C"), GREEN=th.get("green", "#2E8B57"),
        SERIF=cfg.get("fonts", {}).get("serif", "assets/fonts/NotoSerifSC.woff2"),
        SANS=cfg.get("fonts", {}).get("sans", "assets/fonts/NotoSansSC.woff2"),
    )
    out = [CSS]

    cfg_scenes = {s["id"]: s for s in cfg.get("scenes", [])}
    for r in manifest:
        src = cfg_scenes.get(r["id"], {})
        color = src.get("color", "ink")
        cls = "" if color == "ink" else " kw-" + color
        segs = r.get("segs") or []
        spans = "".join('<span id="sub{}-{}">{}</span>'.format(r["id"], i, sg["text"]) for i, sg in enumerate(segs))
        sub_html = '<div class="sub">{}</div>\n'.format(spans) if segs else ""
        if src.get("kind") == "card":
            sign_name = src.get("sign_name", "")
            sign_line = src.get("sign_line", "")
            sign_html = ('<div class="card-sign">{}<span class="soft">{}</span></div>'
                         .format(sign_name, sign_line)) if (sign_name or sign_line) else ""
            out.append(
                '  <div id="s{r}" class="scene" data-layout-allow-overflow>\n'
                '    <div class="card-wrap">\n'
                '      <div class="card-kw">{kw}</div>\n'
                '      <div class="card-rule"></div>\n'
                '      {sign}\n'
                '    </div>\n'
                '{sub}  </div>\n'.format(r=r["id"], kw=r["kw"], sign=sign_html, sub=sub_html))
        else:
            out.append(
                '  <div id="s{r}" class="scene" data-layout-allow-overflow>\n'
                '    <img class="bg-blur" data-layout-ignore src="assets/img/raw/{img}.png" alt="">\n'
                '    <img class="hero" src="assets/img/{img}.png" alt="">\n'
                '    <div class="scrim"></div>\n'
                '    <div class="kw{cls}">{kw}</div>\n'
                '    <div class="cap"><span>{cap}</span></div>\n'
                '{sub}  </div>\n'.format(r=r["id"], img=r["img"], cls=cls, kw=r["kw"], cap=r.get("sub", ""), sub=sub_html))

    # audio
    out.append('  <!-- narration -->\n')
    for r in manifest:
        out.append('  <audio id="a{id}" data-start="{st}" data-duration="{dur}" '
                   'data-track-index="10" src="assets/audio/{id:02d}_{img}.wav"></audio>\n'.format(
                       id=r["id"], st=r["start"], dur=r["audio"], img=r["img"]))
    out.append('</div>\n')

    # timeline
    js = ['<script>\n  window.__timelines = window.__timelines || {};\n  var tl = gsap.timeline({ paused: true });\n']
    js.append('''  function entrance(id,t,isCard){
    if(isCard){
      tl.from("#"+id+" .card-kw",{opacity:0,y:26,duration:0.7,ease:"power3.out"},t+0.14);
      tl.from("#"+id+" .card-rule",{opacity:0,scaleX:0.35,duration:0.6,ease:"power2.out"},t+0.52);
      tl.from("#"+id+" .card-sign",{opacity:0,y:16,duration:0.6,ease:"power2.out"},t+0.64);
    } else {
      tl.from("#"+id+" .hero",{opacity:0,scale:0.97,duration:0.6,ease:"power3.out"},t+0.12);
      tl.from("#"+id+" .kw",{opacity:0,y:18,duration:0.5,ease:"power2.out"},t+0.26);
      tl.from("#"+id+" .cap",{opacity:0,duration:0.5,ease:"power2.out"},t+0.48);
    }
  }
  function swap(prev,next,t,isCardNext){
    tl.to("#"+prev,{opacity:0,duration:0.35,ease:"power2.inOut"},t);
    tl.set("#"+prev,{visibility:"hidden"},t+0.36);
    tl.set("#"+next,{visibility:"visible"},t+0.02);
    tl.to("#"+next,{opacity:1,duration:0.4,ease:"power2.inOut"},t);
    entrance(next,t,isCardNext);
  }
''')
    # s1 入场（自身即为第一场景）
    js.append('  tl.from("#s1 .hero",{opacity:0,scale:0.97,duration:0.8,ease:"power3.out"},0.2);\n')
    js.append('  tl.from("#s1 .kw",{opacity:0,y:18,duration:0.6,ease:"power2.out"},0.5);\n')
    js.append('  tl.from("#s1 .cap",{opacity:0,duration:0.6,ease:"power2.out"},0.8);\n')
    for i in range(2, len(manifest) + 1):
        is_card = cfg_scenes.get(manifest[i - 1]["id"], {}).get("kind") == "card"
        js.append(f'  swap("s{i - 1}","s{i}",{manifest[i - 1]["start"]},{"true" if is_card else "false"});\n')
    for r in manifest:
        for i, sg in enumerate(r.get("segs") or []):
            t = round(r["start"] + sg["s"], 2)
            e = round(t + sg["d"], 2)
            js.append('  tl.set("#sub{id}-{i}",{{visibility:"visible"}},{t});\n'.format(id=r["id"], i=i, t=t))
            js.append('  tl.fromTo("#sub{id}-{i}",{{opacity:0}},{{opacity:1,duration:0.14,ease:"none"}},{t});\n'.format(id=r["id"], i=i, t=t))
            js.append('  tl.set("#sub{id}-{i}",{{visibility:"hidden"}},{e});\n'.format(id=r["id"], i=i, e=e))
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