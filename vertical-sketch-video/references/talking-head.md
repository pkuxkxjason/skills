# 可选开关：口播画中画（真人出镜小窗）

> 把真人出镜做成**圆形/圆角小窗**，叠在成片的某个角（默认**右下角圆形**）。
> 脚本：`scripts/talking_head.py`。**默认关闭**，剧本确认后在 `video.config.json` 里开启。

## 默认样本（老板）

老板口播样本固定放在 skill 自带目录：`assets/avatars/boss_sample.mov`（正脸近景，约 34s；说明见同目录 `README.md`）。
`*.mov` 已被项目根 `.gitignore` 排除，**不入库**；分享 skill 时需自备样本。
每期 config 的 `talking_head.src` 直接写这个 skill 内路径即可，无需每期另带样本。

## 分两步，可只用其一

| 步骤 | 命令 | 是否调模型 | 计费 |
|---|---|---|---|
| ① 生成口型 | `talking_head.py gen`（VideoRetalk） | 是 | ¥0.08/秒（**1800 秒免费额度**） |
| ② 本地合成 | `talking_head.py overlay` | **否**（纯 ffmpeg） | ¥0 |

> 若只是想叠一段"老板本来就在说话"的原片，**跳过 ①**，直接 `overlay --head 样本.mov` 即可，全程本地免费。
> 若要口型对上本片配音，就做 ①：用**成片原声**驱动，天然 1:1 同步。

## 推荐流程（接在成片之后）

```bash
SK=.opencode/skills/vertical-sketch-video/scripts/talking_head.py

# ① 生成口型：样本视频 + 从成片抽出的原声（1:1 同步）
python3 $SK gen --video .opencode/skills/vertical-sketch-video/assets/avatars/boss_sample.mov --base <成片>.mp4 --out video/head.mp4

# ② 本地合成：右下圆、白描边、投影（参数读 config 的 talking_head 段）
python3 $SK overlay --base <成片>.mp4 --head video/head.mp4 --out 成片_<标题>_口播.mp4 \
    --config video/video.config.json
```

## 配置段（`video.config.json`，可选）

```json
"talking_head": {
  "enabled": false,
  "src": "assets/avatars/boss_sample.mov",   // skill 自带默认样本；也可写每期目录内的样本
  "shape": "circle",           // circle | rrect
  "position": "bottom-right",  // bottom-right|bottom-left|top-right|top-left
  "size": 320, "margin": 40,
  "ring": 6, "ring_color": "#FFFFFF",   // 描边环（仅 circle）
  "shadow": true
}
```

## ① VideoRetalk 事实（已核实）

- 模型 `videoretalk`，端点 `POST https://dashscope.aliyuncs.com/api/v1/services/aigc/image2video/video-synthesis`（异步，另 `GET /api/v1/tasks/{id}` 轮询）。
- **仅华北2（北京）地域的 API Key**；走现有 `dashscope-payg` key（`cn-beijing`）即可。
- 视频：mp4/avi/mov，2–120s，15–60fps，H.264/H.265，边长 640–2048，≤300MB；**正脸近景**。
- 音频：wav/mp3/aac，2–120s，≤30MB；人声清晰、无 BGM。
- `video_extension=true`：音频比视频长时用"倒放-正放"循环补足画面；否则按较短者截断。
- **多张人脸才需要** `ref_image_url`；单人不用。
- 上传本地文件：先 `GET /api/v1/uploads?action=getPolicy&model=videoretalk` 拿凭证 → POST 表单上传 → 得 `oss://…`；调用时**必须**带 Header `X-DashScope-OssResourceResolve: enable`。

**坑**
1. `oss://` 少带 `X-DashScope-OssResourceResolve: enable` → `No connection adapters …`。
2. **别走代理**：dashscope 是国内端点，`requests` 走系统代理会偶发 `ProxyError`。脚本已内置 `NO_PROXY=aliyuncs.com`。
3. 上传的文件与**模型名、主账号**绑定：`model` 必须写 `videoretalk`，key 必须与调用同一主账号。
4. 输出 `video_url` 仅存 **24 小时**，及时下载。

## ② 本地合成（纯 ffmpeg）

- 人脸定位：`cv2` Haar 级联（`haarcascade_frontalface_default.xml`）→ 取最大脸 → 正方形裁剪框（`side = min(3×脸宽, 帧高)`）；失败则居中。可用 `--crop x:y:w:h` 覆盖。
- 圆形 alpha（`geq`，S=size，c=S/2）：
  `a='if(lte(hypot(X-c,Y-c),R),255,0)'`
- 白色描边环（圆）：`r/g/b` 在 `between(R-ring, R)` 的环带里置白，`a` 用外径。
- 圆角矩形 alpha：`dist=hypot(X-clip(X,R,S-R),Y-clip(Y,R,S-R))`，`a='if(lte(dist,R),255,0)'`（R≈0.15×size）。**描边环目前只支持圆。**
- 投影：一层模糊黑圆（`color` 源 + `geq` alpha + `gblur`），偏移 +6/+8 垫在人像下。
- 位置：`POS[位置]` 计算 (x,y)，留 `margin` 边距。

**坑**
1. 投影用的 `color` 源是**无限流**，必须 `d=<成片时长>` 且 `overlay … -shortest`，否则成片时长会跑飞到几百秒。
2. `geq` 表达式里的逗号要转义 `\,`（脚本已用 `esc()` 统一处理）。

## 自检

- 抽帧发 `qwen-vl-max` 代看：小窗是否干净、有描边/投影、人脸居中、**不遮字幕主体**。
- 需要时对成片逐段代听，确认音轨 = 成片配音。

## 成本与规模

- 口型：¥0.08/秒 × 片长；**前 1800 秒免费**（≈36 条 50s 短片）。
- 合成：本地 ¥0，任意调位置/大小/描边都不花钱。

## 已知待优化（老板后续会更新）

- 圆角矩形暂不支持描边环。
- 小窗目前 720p 源放大到 1080 宽，正式可让窗口更小或提高源清晰度。
- 右下角小窗与底部字幕可能接近，长字幕会靠近；必要时让图文区上移或字幕避让。