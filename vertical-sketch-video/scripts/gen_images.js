#!/usr/bin/env node
/**
 * 为「千篇一律的，只是入场券」视频生成 4 张同风格简笔画配图。
 * 引擎：YouMind（youmind-image-generator/scripts/youmind-agent.sh，走 127.0.0.1:7890 代理）。
 * 产出：
 *   assets/img/raw/<key>.png  原图（白底，全尺寸）
 *   assets/img/<key>.png      透明化线稿（供合成 hero）
 *   assets/img/<key>.jpg      白底压缩版（长边 1080 / q82）
 *
 * 用法: node gen_images.js [--only <key>]
 */
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const WRAPPER = '/Users/jasonzhang/Documents/consultant/self-media/内容/.opencode/skills/youmind-image-generator/scripts/youmind-agent.sh';
const TEMPLATE = fs.readFileSync('/Users/jasonzhang/.agents/skills/youmind-image-generator/prompts/手绘简笔画.md', 'utf8');
// 目标文章目录：优先 --dir <path> / 环境变量 VIDEO_DIR，否则用下面默认值
const DIR = process.env.VIDEO_DIR
  || (process.argv.includes('--dir') ? process.argv[process.argv.indexOf('--dir') + 1] : null)
  || '/Users/jasonzhang/Documents/consultant/self-media/内容/手工精品/2026-10-06_Agent为什么千篇一律';

function call(api, params) {
  const out = execSync(`${JSON.stringify(WRAPPER)} call ${api} ${JSON.stringify(JSON.stringify(params || {}))}`,
    { encoding: 'utf8', maxBuffer: 20 * 1024 * 1024 });
  return JSON.parse(out);
}
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const JOBS = {
  's1-sameness': `请生成一张极简手绘简笔画，风格必须与一张已有的黑白线条插画完全一致：纯白背景、极细的黑色手绘线条、火柴人（圆形头、简单线条身体，无五官）。
主题：千篇一律 / 大家都在造同一个东西。
画面内容：画面中一排（5-6 个）一模一样的火柴人并肩站立，每个人面前都立着一个完全相同的小方块或小窗口；相邻方块之间用极细的虚线相连，强调它们一模一样、像复制粘贴。画面的角落，一个火柴人停下脚步，侧头看着这一长排"复制品"，露出若有所思的姿态。
要点：不要任何大标题和大段文字，最多一个极小的中文词"一样"或干脆不要文字；黑白线条，可用一处红色轻点；线条克制、留白充足、画面干净，视觉焦点在那排"一模一样"。
尺寸：4:3 比例。`,

  's2-stack': `请生成一张极简手绘简笔画，风格必须与一张已有的黑白线条插画完全一致：纯白背景、极细的黑色手绘线条。
主题：一个 agent 的循环（agent loop）。
画面内容：画面中央画一个清晰、完整、首尾相接的大圆环箭头（循环）；圆环上均匀分布五个简单小图标，每个图标旁配一个极小的中文标签：一个小铃铛（标签"通知"）、一个电源插头（标签"连接器"）、一块方形芯片（标签"记忆"）、一个方形盒子（标签"沙箱"）、一个放大镜（标签"联网"）。图标用短线连到圆环上，像把标准件装配成一个循环。
要点：画面中不要任何大标题；除上述五个极小标签外不要出现其他文字；圆环的循环方向要清晰一致；黑白线条为主，可用一处蓝色轻轻点缀；留白充足、画面干净、视觉焦点在中央的循环。
尺寸：4:3 比例。`,

  's3-2005': `请生成一张极简手绘简笔画，风格必须与一张已有的黑白线条插画完全一致：纯白背景、极细的黑色手绘线条、火柴人（圆形头、简单线条身体，无五官）。
主题：2005 年，互联网的标配清单。
画面内容：画面左侧一台老式台式电脑（CRT 显示器 + 主机）；从电脑牵出几条细线，连着几个简单图标：一个三层圆柱（数据库）、一张带行列的表格（用户表）、四扇一模一样的小门或小页面；四扇门上分别用极小的中文写上"登录""注册""个人""登出"。整体像一张"必备清单"，一目了然。
要点：画面中不要任何大标题；除上述四个极小中文标签以及数据库/用户表可不标注外，绝对不要出现任何英文、字母、品牌名或版本号（不要出现 MySQL / Nginx / PHP / Apache 之类）；黑白线条为主，可用一处蓝色点缀；留白充足、画面干净、带一点复古感。
尺寸：4:3 比例。`,

's4-ticket': `请生成一张极简手绘简笔画，风格必须与一张已有的黑白线条插画完全一致：纯白背景、极细的黑色手绘线条、火柴人（圆形头、简单线条身体，无五官）。
主题：标配之上，才是差异。
画面内容：画面左半，一台巨大的复印机正在不停复印出一模一样的老网页——一叠完全相同、每页只写极小中文"复制"的方块纸，一个火柴人机械地往机器里送纸。画面右半，同一根主干上长出四个明显不同的小图标：一个地图指针/导航箭头、一个音符、一个外卖餐盒、一个购物袋，四个图标形状各异、用四种不同颜色轻轻点亮。
要点：画面中绝对不要出现任何大标题或成句文字（尤其不要写"标配之上，才是差异"这类标题文字）；只在复印出的纸页上写极小的中文"复制"；黑白线条为主；留白充足、左右对比有力、画面干净。
尺寸：4:3 比例。`,
};

function compress(src, dst) {
  const py = [
    'import sys',
    'from PIL import Image, ImageOps',
    'src,dst,mx,q=sys.argv[1],sys.argv[2],int(sys.argv[3]),int(sys.argv[4])',
    'im=ImageOps.exif_transpose(Image.open(src))',
    "if im.mode in ('RGBA','LA') or (im.mode=='P' and 'transparency' in im.info):",
    "    im=im.convert('RGBA');bg=Image.new('RGB',im.size,(255,255,255));bg.paste(im,mask=im.split()[-1]);im=bg",
    "elif im.mode!='RGB': im=im.convert('RGB')",
    'w,h=im.size',
    'if max(w,h)>mx:',
    '    s=mx/float(max(w,h));im=im.resize((max(1,round(w*s)),max(1,round(h*s))),Image.LANCZOS)',
    "im.save(dst,'JPEG',quality=q,optimize=True,progressive=True)",
  ].join('\n');
  const p = '/tmp/_gen_img_compress.py';
  fs.writeFileSync(p, py);
  execSync(`python3 ${JSON.stringify(p)} ${JSON.stringify(src)} ${JSON.stringify(dst)} 1080 82`, { stdio: 'pipe' });
}

function transparent(src, dst) {
  const py = [
    'import sys',
    'import numpy as np',
    'from PIL import Image',
    'src,dst,lo,hi=sys.argv[1],sys.argv[2],float(sys.argv[3]),float(sys.argv[4])',
    "im=Image.open(src).convert('RGB')",
    'a=np.asarray(im).astype(np.float32)',
    'w=a.min(axis=2)',
    'alpha=np.clip((hi-w)/(hi-lo)*255.0,0,255)',
    "out=np.dstack([a,alpha]).astype(np.uint8)",
    "Image.fromarray(out,'RGBA').save(dst)",
  ].join('\n');
  const p = '/tmp/_gen_img_transparent.py';
  fs.writeFileSync(p, py);
  execSync(`python3 ${JSON.stringify(p)} ${JSON.stringify(src)} ${JSON.stringify(dst)} 236 247`, { stdio: 'pipe' });
}

function extractUrls(msgs) {
  const items = Array.isArray(msgs) ? msgs : (msgs.items || msgs.messages || []);
  const urls = [];
  for (const m of items) for (const b of (m.blocks || [])) {
    if (b.toolName === 'generate_image' && b.status === 'success') {
      const tr = b.toolResult || {};
      const ur = tr.original_image_urls || tr.image_urls;
      if (Array.isArray(ur)) urls.push(...ur);
    }
  }
  return [...new Set(urls)];
}

async function gen(boardId, key) {
  const msg = TEMPLATE + '\n=========\n' + JOBS[key];
  const chat = call('createChat', { boardId, message: msg, tools: { imageGenerate: { useTool: 'required' } } });
  const chatId = chat.id;
  console.log(`  [${key}] chatId=${chatId} 生图中...`);
  let status = 'answering';
  for (let i = 0; i < 60; i++) {
    await sleep(5000);
    try { status = call('getChat', { chatId }).status; } catch (e) { /* ignore */ }
    if (status === 'completed' || status === 'errored') break;
  }
  if (status !== 'completed') { console.error(`  ${key} 未完成 status=${status}`); return false; }
  const urls = extractUrls(call('listMessages', { chatId, pageSize: 20 }));
  if (!urls.length) { console.error(`  ${key} 未提取到图片`); return false; }
  const tmp = path.join(DIR, `.tmp-${key}.png`);
  execSync(`curl -sS -m 600 -x http://127.0.0.1:7890 -o ${JSON.stringify(tmp)} ${JSON.stringify(urls[0])}`);
  const raw = path.join(DIR, 'video/assets/img/raw', `${key}.png`);
  const hero = path.join(DIR, 'video/assets/img', `${key}.png`);
  const jpg = path.join(DIR, 'video/assets/img', `${key}.jpg`);
  fs.renameSync(tmp, raw);
  transparent(raw, hero);
  compress(raw, jpg);
  console.log(`  ✅ ${key} 已保存 (raw/hero/jpg)`);
  return true;
}

(async () => {
  const only = process.argv.includes('--only') ? process.argv[process.argv.indexOf('--only') + 1] : null;
  const board = call('getDefaultBoard', {});
  console.log('boardId:', board.id);
  const keys = Object.keys(JOBS).filter((k) => !only || k === only);
  for (const k of keys) await gen(board.id, k);
  console.log('done');
})();