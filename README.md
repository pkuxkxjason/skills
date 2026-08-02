# skills

一个集中管理 AI Agent Skills（技能）的仓库。每个子目录即一个独立的 skill，可被 Claude Code、opencode 等支持 Agent Skills 的工具加载使用。

## 目录

- [article-illustrator](./article-illustrator/) — 文章自动配图
- [md2wchtml](./md2wchtml/) — Markdown 转微信公众号风格 HTML

## 技能说明

### article-illustrator

读取 Markdown 文章，通过标题结构自动切分章节，提取每节主题，使用 YouMind CLI 生成手绘简笔画风格配图，下载到文章同目录并插入到 markdown 文件的对应章节末尾。

```bash
node scripts/generate-images.js <markdown-file>            # 为所有章节配图
node scripts/generate-images.js <markdown-file> --replace <section-index>  # 替换某节配图
```

### md2wchtml

将 Markdown 文件转换为微信公众号风格的 HTML。自动生成紫色主题、标题左边框、引用块渐变背景、图片居中、高亮紫色加粗等效果，全部使用内联样式，可直接复制到公众号编辑器。

```bash
python3 md2wchtml.py 文章.md          # 自动生成 [原文件名].html
python3 md2wchtml.py 文章.md 输出.html # 指定输出文件
```

## 使用方法

1. 克隆本仓库：`git clone https://github.com/pkuxkxjason/skills.git`
2. 将需要的 skill 子目录复制到你项目对应位置的 skills 目录（如 `.agents/skills/<skill-name>/`）
3. 在你的对话中触发该 skill，或按各 skill 文档中的说明直接使用其命令行工具

## 工具要求

- 各 skill 的脚本.基于 Python 3 或 Node.js 运行
- 部分技能依赖 YouMind 等外部 API，请参照各 skill 内的说明配置

## 关于作者

资深技术人，外企黄金时代幸存者，金融数字化践行者。分享 40+ 职场人转型之路和企业数字化再增长。

扫码加入《数字化转型干货群》，这里是数字化转型实战者的聚集地，还有免费的 AI 插件和提示词可以领取。

## License

MIT