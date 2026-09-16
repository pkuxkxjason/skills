#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
逐场景 TTS 配音：按 video.config.json 的 scenes 生成音频，做响度归一化，写真实时长 manifest。

用法:
  export DASHSCOPE_API_KEY=sk-xxx          # 不要写进任何文件
  python gen_tts.py --config video/video.config.json [--out-dir video/assets/audio]

产出:
  <out-dir>/NN_<img>.wav     每场景（已响度归一化）
  <out-dir>/manifest.json    [{id,img,kw,sub,narration,audio,start,dur}, ...]（真实时长）
"""
import argparse, json, os, subprocess, sys, time

# 各系列的端点。{ws}=业务空间ID（token-plan 等套餐即套餐名）
DASHSCOPE = "https://dashscope.aliyuncs.com"
MG_PATH = "/api/v1/services/aigc/multimodal-generation/generation"
SS_PATH = "/api/v1/services/audio/tts/SpeechSynthesizer"


def curl_json(url, key, body, timeout=150):
    with open("/tmp/_tts_req.json", "w") as f:
        json.dump(body, f, ensure_ascii=False)
    p = subprocess.run(
        ["curl", "-s", "--max-time", str(timeout), "-X", "POST", url,
         "-H", f"Authorization: Bearer {key}", "-H", "Content-Type: application/json",
         "--data-binary", "@/tmp/_tts_req.json"],
        capture_output=True, text=True)
    try:
        return json.loads(p.stdout)
    except Exception:
        return {"_raw": p.stdout[:300]}


def synth(cfg, key, text):
    """返回音频 URL（失败返回 None）"""
    t = cfg["tts"]
    model = t["model"]
    if t.get("provider") == "qwen-audio":
        url = t["workspace_url"].rstrip("/") + SS_PATH
        text = (t.get("emotion_tag", "") or "") + text
        body = {"model": model, "input": {
            "text": text, "voice": t["voice"], "format": "wav",
            "sample_rate": t.get("sample_rate", 24000)}}
        if t.get("instruction"):
            body["input"]["instruction"] = t["instruction"]
    else:  # qwen-tts / qwen3-tts-flash / qwen3-tts-instruct-flash
        url = t.get("base_url", DASHSCOPE).rstrip("/") + MG_PATH
        inp = {"text": text, "voice": t["voice"], "language_type": t.get("language_type", "Chinese")}
        if t.get("instructions"):
            inp["instructions"] = t["instructions"]
            inp["optimize_instructions"] = True
        body = {"model": model, "input": inp}
    d = curl_json(url, key, body)
    return d.get("output", {}).get("audio", {}).get("url")


def normalize(src, dst):
    subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-af",
                    "loudnorm=I=-16:TP=-1.5:LRA=9,acompressor=threshold=-20dB:ratio=2.5:attack=5:release=150",
                    "-ar", "24000", "-ac", "1", "-y", dst])


def dur_of(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=noprint_wrappers=1:nokey=1", path],
                         capture_output=True, text=True).stdout.strip()
    return float(out or 0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--out-dir", default=None)
    args = ap.parse_args()

    cfg = json.load(open(args.config, encoding="utf-8"))
    key = os.environ.get(cfg["tts"].get("api_key_env", "DASHSCOPE_API_KEY"))
    if not key:
        sys.exit("缺少 API Key：请设置环境变量 " + cfg["tts"].get("api_key_env", "DASHSCOPE_API_KEY"))
    outdir = args.out_dir or cfg.get("audio_dir", "audio")
    os.makedirs(outdir, exist_ok=True)
    gap = cfg.get("gap", 0.8)

    rows, cum = [], 0.0
    for sc in cfg["scenes"]:
        text = sc["narration"]
        ok = False
        for attempt in range(4):
            u = synth(cfg, key, text)
            if u:
                raw = f"/tmp/_tts_raw_{sc['id']}.wav"
                subprocess.run(["curl", "-s", "--max-time", "120", u, "-o", raw])
                out = os.path.join(outdir, f"{sc['id']:02d}_{sc['img']}.wav")
                normalize(raw, out)
                a = round(dur_of(out), 2)
                rows.append(dict(id=sc["id"], img=sc["img"], kw=sc.get("kw", ""), sub=sc.get("sub", ""),
                                 kind=sc.get("kind", "content"), narration=text,
                                 audio=a, start=round(cum, 2), dur=round(a + gap, 2)))
                cum += a + gap
                print(f"{sc['id']:>2} {sc['img']:16s} {a:5.2f}s")
                ok = True
                break
            print(f"  retry {sc['id']} #{attempt}")
            time.sleep(3)
        if not ok:
            print(f"FAIL {sc['id']} {sc['img']}")

    json.dump(rows, open(os.path.join(outdir, "manifest.json"), "w"), ensure_ascii=False, indent=1)
    print(f"\n纯语音 {sum(r['audio'] for r in rows):.1f}s | 含静默 {cum:.1f}s = {cum/60:.2f} 分钟")


if __name__ == "__main__":
    main()