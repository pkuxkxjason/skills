#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配图白底透明化：把手绘线稿的白/近白背景抠成透明，让墨线直接落在纸张/场景背景上。
原图自动备份到 <dir>/raw/。

用法:
  python prep_images.py --dir video/assets/img [--glob "s*.png"] [--lo 236 --hi 247]

原理: 以每像素三通道最小值 min(r,g,b) 作为"白度"；白度 >= hi 全透明，<= lo 全不透明，
中间线性羽化（保留抗锯齿边缘，不出硬边）。彩色/深色像素（min 小）自然保持不透明。
"""
import argparse, glob, os, shutil
import numpy as np
from PIL import Image


def cut_white(path, lo, hi):
    im = Image.open(path).convert("RGB")
    a = np.asarray(im).astype(np.float32)
    w = a.min(axis=2)                                  # whiteness
    alpha = np.clip((hi - w) / (hi - lo) * 255.0, 0, 255)
    out = np.dstack([a, alpha]).astype(np.uint8)
    Image.fromarray(out, "RGBA").save(path)
    return round(float((alpha < 8).mean()) * 100, 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, help="配图目录")
    ap.add_argument("--glob", default="*.png", help="匹配模式（默认全部 png；封面等请排除）")
    ap.add_argument("--lo", type=float, default=236.0, help="<=lo 视为不透明")
    ap.add_argument("--hi", type=float, default=247.0, help=">=hi 视为透明")
    ap.add_argument("--no-backup", action="store_true")
    args = ap.parse_args()

    files = sorted(glob.glob(os.path.join(args.dir, args.glob)))
    if not files:
        print("没有匹配的图片:", os.path.join(args.dir, args.glob)); return
    raw = os.path.join(args.dir, "raw")
    if not args.no_backup:
        os.makedirs(raw, exist_ok=True)
    for f in files:
        if os.path.basename(f).lower().startswith(("cover", "封面")):
            print("跳过封面:", os.path.basename(f)); continue
        if not args.no_backup:
            shutil.copy(f, os.path.join(raw, os.path.basename(f)))
        pct = cut_white(f, args.lo, args.hi)
        print(f"{os.path.basename(f):32s} transparent≈{pct:2d}%")


if __name__ == "__main__":
    main()