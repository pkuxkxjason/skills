#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
口播画中画（可选开关）—— 把真人出镜做成圆形/圆角小窗，叠在成片某个角。

两步（互不依赖，可只用其一）:
  1) gen     生成口型：样本视频 + 配音 → 阿里云百炼 VideoRetalk（需模型；走现有 dashscope-payg key）
  2) overlay 本地合成：裁圆/圆角 + 白色描边环 + 投影 → 叠到指定角（纯 ffmpeg，不调模型、不花钱）

用法:
  # 只用本地合成（已有口型片或直接用样本原片）
  python3 talking_head.py overlay --base 成片.mp4 --head 口型片.mp4 --out final.mp4 \
      --shape circle --pos bottom-right --size 320 --margin 40 --ring 6

  # 从 video.config.json 的 talking_head 段读参数（推荐）
  python3 talking_head.py overlay --base 成片.mp4 --head 口型片.mp4 --out final.mp4 --config video/video.config.json

  # 用样本视频+配音生成口型片（音频缺省则从 --base 抽）
  python3 talking_head.py gen --video 样本.mov --audio 配音.wav --out head.mp4

video.config.json 可选段（默认 enabled=false）:
  "talking_head": {
    "enabled": false,
    "src": "原始音视频/口播样本.mov",   // 样本视频（gen 用）
    "shape": "circle",                  // circle | rrect
    "position": "bottom-right",         // bottom-right|bottom-left|top-right|top-left
    "size": 320, "margin": 40,
    "ring": 6, "ring_color": "#FFFFFF", // 描边环（仅 circle）
    "shadow": true
  }
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

BASE_URL = "https://dashscope.aliyuncs.com"
MODEL = "videoretalk"

POS = {
    "bottom-right": lambda W, H, s, m: (W - s - m, H - s - m),
    "bottom-left":  lambda W, H, s, m: (m, H - s - m),
    "top-right":    lambda W, H, s, m: (W - s - m, m),
    "top-left":     lambda W, H, s, m: (m, m),
}


# ---------- 公共 ----------
def api_key():
    env = os.getenv("DASHSCOPE_API_KEY")
    if env:
        return env
    cfg = json.load(open(os.path.expanduser("~/.config/opencode/opencode.json")))
    return cfg["provider"]["dashscope-payg"]["options"]["apiKey"]


def esc(expr):
    return expr.replace(",", "\\,")


def dur_of(path):
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)], text=True).strip()
    return float(out)


def dims_of(path):
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-of", "csv=s=x:p=0", str(path)], text=True).strip()
    w, h = out.split("x")
    return int(w), int(h)


def hex_rgb(s):
    s = s.lstrip("#")
    return int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)


# ---------- 人脸裁剪框 ----------
def detect_crop(video):
    """返回 (x,y,w,h) 正方形裁剪框（含头肩），失败则居中。"""
    import tempfile
    try:
        import cv2
    except Exception:
        cv2 = None
    W, H = dims_of(video)
    if cv2 is not None:
        with tempfile.TemporaryDirectory() as d:
            jpg = os.path.join(d, "f.jpg")
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "5",
                            "-i", str(video), "-frames:v", "1", jpg], check=True)
            img = cv2.imread(jpg)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            cas = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
            faces = cas.detectMultiScale(gray, 1.1, 5, minSize=(80, 80))
            if len(faces):
                x, y, fw, fh = max(faces, key=lambda f: f[2] * f[3])
                cx, cy = int(x + fw / 2), int(y + fh / 2)
                side = min(int(fw * 3.0), H)
                x0 = max(0, min(W - side, cx - side // 2))
                y0 = max(0, min(H - side, cy - side // 2))
                return x0, y0, side, side
    side = min(W, H)
    return (W - side) // 2, (H - side) // 2, side, side


# ---------- gen：VideoRetalk ----------
def _policy(key, model):
    import requests
    r = requests.get(f"{BASE_URL}/api/v1/uploads",
                     headers={"Authorization": f"Bearer {key}"},
                     params={"action": "getPolicy", "model": model}, timeout=60)
    r.raise_for_status()
    return r.json()["data"]


def _upload(key, model, path):
    import requests
    pol = _policy(key, model)
    fn = Path(path).name
    k = f"{pol['upload_dir']}/{fn}"
    with open(path, "rb") as f:
        files = {"OSSAccessKeyId": (None, pol["oss_access_key_id"]),
                 "Signature": (None, pol["signature"]),
                 "policy": (None, pol["policy"]),
                 "x-oss-object-acl": (None, pol["x_oss_object_acl"]),
                 "x-oss-forbid-overwrite": (None, pol["x_oss_forbid_overwrite"]),
                 "key": (None, k), "success_action_status": (None, "200"),
                 "file": (fn, f)}
        r = requests.post(pol["upload_host"], files=files, timeout=600)
    if r.status_code != 200:
        raise SystemExit(f"上传失败 {path}: {r.status_code} {r.text[:200]}")
    return f"oss://{k}"


def cmd_gen(a):
    os.environ["NO_PROXY"] = "aliyuncs.com,.aliyuncs.com"
    os.environ["no_proxy"] = "aliyuncs.com,.aliyuncs.com"
    import requests
    key = api_key()
    audio = a.audio
    if not audio and a.base:
        audio = str(Path(a.out).with_suffix(".audio.wav"))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", a.base,
                        "-vn", "-ac", "1", "-ar", "24000", "-c:a", "pcm_s16le", audio], check=True)
    if not audio:
        raise SystemExit("gen 需要 --audio，或用 --base 指定成片以便抽取音轨")
    print("[upload] 样本视频 …"); vurl = _upload(key, MODEL, a.video); print("  ", vurl)
    print("[upload] 配音音频 …"); aurl = _upload(key, MODEL, audio); print("  ", aurl)
    body = {"model": MODEL, "input": {"video_url": vurl, "audio_url": aurl},
            "parameters": {"video_extension": bool(a.extend)}}
    hdr = {"Authorization": f"Bearer {key}", "Content-Type": "application/json",
           "X-DashScope-Async": "enable", "X-DashScope-OssResourceResolve": "enable"}
    r = requests.post(f"{BASE_URL}/api/v1/services/aigc/image2video/video-synthesis",
                      headers=hdr, json=body, timeout=60)
    if r.status_code != 200:
        raise SystemExit(f"提交失败 {r.status_code}: {r.text[:600]}")
    task = r.json()["output"]["task_id"]
    print("[task]", task)
    while True:
        time.sleep(15)
        j = requests.get(f"{BASE_URL}/api/v1/tasks/{task}",
                         headers={"Authorization": f"Bearer {key}"}, timeout=60).json()["output"]
        print("  status:", j.get("task_status"))
        if j.get("task_status") == "SUCCEEDED":
            with requests.get(j["video_url"], stream=True, timeout=600) as d:
                d.raise_for_status()
                with open(a.out, "wb") as f:
                    for c in d.iter_content(1 << 16):
                        f.write(c)
            print("[saved]", a.out); return
        if j.get("task_status") in ("FAILED", "UNKNOWN", "CANCELED"):
            raise SystemExit("口型生成失败: " + json.dumps(j, ensure_ascii=False))


# ---------- overlay：本地合成 ----------
def cmd_overlay(a):
    cfg = {}
    if a.config:
        cfg = json.load(open(a.config, encoding="utf-8")).get("talking_head", {}) or {}
    shape = a.shape or cfg.get("shape", "circle")
    pos = a.pos or cfg.get("position", "bottom-right")
    size = int(a.size or cfg.get("size", 320))
    margin = int(a.margin if a.margin is not None else cfg.get("margin", 40))
    ring = int(a.ring if a.ring is not None else cfg.get("ring", 6))
    ring_color = a.ring_color or cfg.get("ring_color", "#FFFFFF")
    shadow = cfg.get("shadow", True) if a.shadow is None else a.shadow

    W, H = dims_of(a.base)
    crop = a.crop
    if crop:
        cx, cy, cw, ch = [int(v) for v in crop.split(":")]
    else:
        cx, cy, cw, ch = detect_crop(a.head)
    print(f"[crop] {cx}:{cy}:{cw}:{ch}  -> {shape} @ {pos} size={size} margin={margin}")

    c = size / 2.0
    rr, gg, bb = hex_rgb(ring_color)
    if shape == "rrect":
        R = int(size * 0.15)
        dist = f"hypot(X-clip(X,{R},{size - R}),Y-clip(Y,{R},{size - R}))"
        alpha = esc(f"if(lte({dist},{R}),255,0)")
        geq = (f"geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='{alpha}'")
    else:  # circle
        outer = c - 8
        inner = outer - ring
        between = f"between(hypot(X-{c},Y-{c}),{inner},{outer})"
        geq = ("geq=r='%s':g='%s':b='%s':a='%s'" % (
            esc(f"if({between},{rr},r(X,Y))"), esc(f"if({between},{gg},g(X,Y))"),
            esc(f"if({between},{bb},b(X,Y))"), esc(f"if(lte(hypot(X-{c},Y-{c}),{outer}),255,0)")))

    x, y = POS[pos](W, H, size, margin)
    dur = dur_of(a.base)

    fc = []
    inputs = ["-i", str(a.base), "-i", str(a.head)]
    if shadow:
        fc.append(f"color=c=black@0.001:s={size}x{size}:r=30:d={dur:.3f},format=rgba,"
                  f"geq=r='0':g='0':b='0':a='if(lte(hypot(X-{c},Y-{c}),{c - 12}),120,0)',gblur=sigma=9[sh]")
        fc.append(f"[1:v]crop={cw}:{ch}:{cx}:{cy},scale={size}:{size},{geq}[head]")
        fc.append(f"[0:v][sh]overlay={x + 6}:{y + 8}:format=auto[t]")
        fc.append(f"[t][head]overlay={x}:{y}:format=auto[o]")
    else:
        fc.append(f"[1:v]crop={cw}:{ch}:{cx}:{cy},scale={size}:{size},{geq}[head]")
        fc.append(f"[0:v][head]overlay={x}:{y}:format=auto[o]")
    graph = ";".join(fc)

    subprocess.run(["ffmpeg", "-y", *inputs, "-filter_complex", graph,
                    "-map", "[o]", "-map", "0:a", "-c:v", "libx264", "-crf", "18",
                    "-pix_fmt", "yuv420p", "-c:a", "copy", "-shortest", str(a.out)],
                   check=True)
    print("[saved]", a.out)


def main():
    ap = argparse.ArgumentParser(description="口播画中画（可选开关）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("gen", help="样本视频+配音 → 口型片（VideoRetalk）")
    g.add_argument("--video", required=True, help="样本视频（正脸近景）")
    g.add_argument("--audio", help="配音音频；缺省则从 --base 抽")
    g.add_argument("--base", help="成片（用于抽取音轨，与口型 1:1 同步）")
    g.add_argument("--out", required=True)
    g.add_argument("--extend", type=int, default=1, help="音频比视频长时延展画面(1/0)")
    g.set_defaults(func=cmd_gen)

    o = sub.add_parser("overlay", help="本地合成：裁圆/圆角+描边+投影+叠角")
    o.add_argument("--base", required=True, help="底片（成片）")
    o.add_argument("--head", required=True, help="口型片（或样本原片）")
    o.add_argument("--out", required=True)
    o.add_argument("--config", help="video.config.json（读 talking_head 段）")
    o.add_argument("--crop", help="人脸裁剪框 x:y:w:h（缺省自动检测）")
    o.add_argument("--shape", choices=["circle", "rrect"])
    o.add_argument("--pos", choices=list(POS))
    o.add_argument("--size", type=int)
    o.add_argument("--margin", type=int)
    o.add_argument("--ring", type=int)
    o.add_argument("--ring-color")
    o.add_argument("--shadow", type=lambda v: v not in ("0", "false", "no"), nargs="?")
    o.set_defaults(func=cmd_overlay)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()