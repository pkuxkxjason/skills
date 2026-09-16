# TTS 配音（选型 · 指令 · 停顿 · 归一化 · 代听）

## 1. 模型与端点（DashScope / 阿里云百炼）

各系列的**端点不同，不能混用**：

| 系列 | 模型 | 端点 |
|---|---|---|
| Qwen-TTS | `qwen-tts`、`qwen3-tts-flash`、`qwen3-tts-instruct-flash` | `https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation` |
| Qwen-Audio-TTS | `qwen-audio-3.0-tts-plus`、`qwen-audio-3.0-tts-flash` | `https://{WorkspaceId}.cn-beijing.maas.aliyuncs.com/api/v1/services/audio/tts/SpeechSynthesizer` |
| 声音复刻 | `qwen3-tts-vc` | 同 Qwen-TTS |
| 声音设计 | `qwen3-tts-vd` | 同 Qwen-TTS |

> `{WorkspaceId}` 是业务空间 ID；某些套餐（如 token-plan）里就是套餐名，例如 `token-plan.cn-beijing.maas.aliyuncs.com`。
> **踩坑**：把 Qwen-Audio-TTS 打到 `.../multimodal-generation/generation`，或把兼容端点 `/compatible-mode/v1/audio/speech` 当 TTS 用，都会报 `url error, please check url`。

### 请求示例

Qwen-TTS（自然语言定制音色）：
```json
POST <dashscope>/api/v1/services/aigc/multimodal-generation/generation
{ "model": "qwen3-tts-instruct-flash",
  "input": { "text": "……", "voice": "Ethan", "language_type": "Chinese",
             "instructions": "沉稳的中年男性播音员，中气十足，吐字清晰有力，节奏干脆，适合知识讲解。",
             "optimize_instructions": true } }
```

Qwen-Audio-TTS（富音色 + 指令 + 情感标签）：
```json
POST https://{WorkspaceId}.cn-beijing.maas.aliyuncs.com/api/v1/services/audio/tts/SpeechSynthesizer
{ "model": "qwen-audio-3.0-tts-plus",
  "input": { "text": "[serious]今天讲一个反常识的结论。", "voice": "longanlufeng",
             "format": "wav", "sample_rate": 24000,
             "instruction": "沉稳的中年男性，中气十足，吐字清晰有力，节奏干脆" } }
```

响应都返回 `output.audio.url`（有效期 24h），下载即可。

## 2. 音色

- **Qwen-TTS** 预置：`Cherry`、`Ethan`、`Serena`、`Chelsie`（不同音色语速差很多：实测这段 41 字 Ethan 7.5s、Cherry 9.0s、Chelsie 11.4s）。
- **Qwen-Audio-TTS** 龙系列：`longanhuan_v3.6`(25岁女)、`longanlufeng`(25岁男/明亮)、`longchuanshu_v3.6`(40岁男/川普)、`longanfengyue`(30岁女)、`longanxiaoxin`(22岁女)、`longanlingxi`(女/知心)、`longpaopao_v3.6`(5岁女)、`longhuohuo_v3.6`(8岁男)…… 具体见官方「音色列表」。
- 想要固定音色/特定人声：**声音复刻**（`qwen3-tts-vc`，给一段录音）或**声音设计**（`qwen3-tts-vd`）。

## 3. 指令写法（voice design）

用自然语言描述声音，四原则：**具体、多维、客观、不模仿名人**。
维度：性别/年龄/音调/语速/情感/特点/用途。
> 例：「沉稳的中年男性，四十岁左右，音色低沉有磁性，吐字清晰有力，节奏明快不拖沓，适合知识科普讲解。」

**两大常见病与解药**：
- **慵懒、散漫** → 别在指令里写"舒缓 / 平缓 / 柔和"（会把模型带瘫）。改成正向词：「中气足、吐字清晰有力、节奏干脆、字正腔圆」，Qwen-Audio 再加 `[serious]` 情感标签。
- **忽大忽小** → 不是指令能修的，必须做**响度归一化**（见第 5 节）。

**情感 / 富语言标签**（仅 `qwen-audio-3.0-tts-plus/flash`）：写在 `text` 里，
控制类 `[serious] [excited] [sad] [curious] [angry] [whisper] …`，
拟声类 `[laughing] [sighing] [gasp] [clears throat] …`。

## 4. 停顿模型（估算时长用）

语音时长按 `中文字数 / 5`（≈300 字/分）。停顿：

| 标点 | 停顿 |
|---|---|
| 。！？ | 0.55s |
| ； | 0.35s |
| ： | 0.32s |
| ， | 0.22s |
| 、 | 0.18s |
| —— | 0.32s |
| 场景之间静默 | 0.8~1.0s |

> 估算只用于**剧本阶段**。进入制作后一律用 TTS **真实音频时长**。多数 TTS 不解析 SSML `<break>`；要精确停顿就把句子分行、用标点控制。

## 5. 响度归一化（必做）

每段生成后统一响度，否则拼接后忽大忽小：

```bash
ffmpeg -i raw.wav \
  -af "loudnorm=I=-16:TP=-1.5:LRA=9,acompressor=threshold=-20dB:ratio=2.5:attack=5:release=150" \
  -ar 24000 -ac 1 -y norm.wav
```

（`loudnorm` 定响度，`acompressor` 压掉句内忽大忽小的动态。实测可把段间波动从 8.6dB 压到 0.6dB。）

## 6. 代听自检（没有听觉时的耳朵）

用 `qwen3-omni-flash`（dashscope **原生**端点）把音频"听"一遍：

```python
body={"model":"qwen3-omni-flash",
 "input":{"messages":[{"role":"user","content":[
   {"text":"转录这段中文配音，评估：男/女声、是否慵懒、音量是否平稳、自然度1-10。"},
   {"audio":"data:audio/wav;base64,"+b64}]}]},
 "parameters":{"result_format":"message"}}
# POST https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation
```

**坑**：兼容端点的 `input_audio` 只收 URL，不收 base64；要用原生端点 + `data:audio/wav;base64,`。base64 很长时 `curl` 命令行会超长，必须把 body 写文件、用 `curl --data-binary @file`。

## 7. 密钥

**不要写进 skill / 脚本**。从环境变量读取，例如 `DASHSCOPE_API_KEY`；或复用用户的 opencode `provider` 配置。脚本参数化（`--api-key-env DASHSCOPE_API_KEY`）。