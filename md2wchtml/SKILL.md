---
name: md2wchtml
description: 将 Markdown 文章转换为微信公众号风格的 HTML 代码。当用户需要将 .md 文件转为公众号 HTML、想把 Markdown 转成微信图文格式、或者需要生成带内联样式的 HTML 时触发。
---

# md2wchtml - Markdown 转微信公众号风格 HTML

## 功能特性

- 支持标准 Markdown 语法（标题、段落、列表、引用、加粗、斜体、图片等）
- 自动生成微信公众号风格的视觉效果
  - 紫色主题配色 (#5965af)
  - 标题带左边框装饰
  - 引用块带渐变背景和圆角
  - 高亮文字自动转为紫色加粗
  - 图片自动转为居中显示
- 生成可直接复制到公众号编辑器的 HTML 代码（全部使用内联样式）

## 快速使用（命令行工具）

本 skill 提供了一个 Python 脚本，可直接在命令行使用：

```bash
# 基础用法 - 自动生成输出文件名
python3 md2wchtml.py 文章.md

# 指定输出文件
python3 md2wchtml.py 文章.md 输出.html
```

输出文件默认保存为 `[原文件名].html`，位于原文件同目录下。

## 工作流程

当用户要求将 Markdown 文章转换为微信公众号风格时：

### 第一步：读取 Markdown 源文件

使用 Read 工具读取用户提供的 Markdown 文件路径。

### 第二步：解析并转换内容

将 Markdown 语法映射到微信公众号 HTML 结构：

| Markdown 元素 | HTML 结构 | 样式特点 |
|--------------|----------|---------|
| `# 标题` | `<section>` + `<span>` | 左边5px紫色竖条，22px粗体 |
| `## 小标题` | `<section>` + `<span>` | 同主标题，字号略小 |
| `> 引用` | `<section>` 嵌套 | 浅紫背景#f1ecf4，渐变左边框，圆角10px，斜体 |
| `**粗体**` | `<strong>` | 紫色#5965af，font-weight:bold |
| `![alt](url)` | `<img>` | 居中显示，最大宽度100% |
| 普通段落 | `<section>` | 17px字号，240%行高，#333颜色，margin-top:28px |
| `- 列表项` | `<ul>` + `<li>` | 圆点列表，左缩进20px |
| `1. 有序列表` | `<ol>` + `<li>` | 数字列表，左缩进20px |
| `\`\`\`代码\`\`\`` | `<section>` + `<pre>` | 浅灰背景#f5f5f5，左边框，等宽字体，圆角 |

### 第三步：生成完整 HTML

生成包含以下结构的完整 HTML 文件：

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>文章标题</title>
  <style>
    /* 基础重置 */
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans SC', sans-serif;
      background: #f5f5f5;
      padding: 20px;
    }
    
    /* 文章容器 - 模拟手机宽度 */
    .article-container {
      max-width: 375px;
      margin: 0 auto;
      background: #fff;
      padding: 24px 20px;
      border-radius: 8px;
    }
    
    /* 主标题样式 */
    .article-title {
      font-size: 22px;
      font-weight: 700;
      color: #252525;
      line-height: 1.4;
      margin-bottom: 20px;
    }
    
    /* 标题区块 - 带左边框 */
    .section-title {
      margin-top: 48px;
      display: flex;
      align-items: flex-start;
    }
    .section-title::before {
      content: '';
      width: 5px;
      height: 21px;
      background: #5965af;
      flex-shrink: 0;
      margin-top: 6px;
      margin-right: 10px;
      border-radius: 2px;
    }
    .section-title-text {
      font-size: 20px;
      font-weight: 700;
      color: #252525;
      line-height: 1.5;
    }
    
    /* 二级标题 */
    .section-subtitle {
      margin-top: 36px;
      display: flex;
      align-items: flex-start;
    }
    .section-subtitle::before {
      content: '';
      width: 4px;
      height: 18px;
      background: #5965af;
      flex-shrink: 0;
      margin-top: 5px;
      margin-right: 10px;
      border-radius: 2px;
    }
    .section-subtitle-text {
      font-size: 17px;
      font-weight: 700;
      color: #252525;
      line-height: 1.5;
      flex: 1;
    }
    
    /* 普通段落 */
    .paragraph {
      margin-top: 28px;
      font-size: 17px;
      line-height: 2.4;
      color: #333;
      text-align: justify;
    }
    
    /* 高亮文字 */
    .highlight {
      color: #5965af;
      font-weight: bold;
    }
    
    /* 引用块样式 */
    .quote-block {
      margin-top: 28px;
      padding: 15px;
      background-color: #f1ecf4;
      border-radius: 10px;
    }
    .quote-inner {
      padding: 16px 20px;
      background: linear-gradient(180deg, #5965af 0%, rgba(89, 101, 175, 0.5) 100%) left / 3px 100% no-repeat,
                  linear-gradient(135deg, #fafafa 0%, #ffffff 100%);
      box-shadow: 0 2px 6px rgba(0,0,0,0.08);
      color: #5965af;
      font-size: 16px;
      font-style: italic;
      line-height: 1.8;
      border-radius: 4px;
    }
    
    /* 列表样式 */
    .list-container {
      margin-top: 20px;
      padding-left: 20px;
    }
    .list-container li {
      margin: 10px 0;
      font-size: 17px;
      line-height: 2;
      color: #333;
    }
    
    /* 分隔线 */
    .divider {
      margin: 32px 0;
      border: none;
      height: 1px;
      background: linear-gradient(90deg, transparent, #e0e0e0, transparent);
    }
  </style>
</head>
<body>
  <div class="article-container">
    <!-- 文章标题 -->
    <h1 class="article-title">文章标题</h1>
    
    <!-- 转换后的内容 -->
    ...
  </div>
</body>
</html>
```

### 第四步：保存并交付

1. 生成的 HTML 文件保存到原 Markdown 文件同目录下，命名为 `[原文件名].html`
2. 向用户提供：
   - 生成的 HTML 文件路径
   - 使用说明：复制 HTML 中的内容到公众号编辑器

## 转换规则详解

### 1. 标题处理

- `# 一级标题` → 带紫色左边框的标题区块
- `## 二级标题` → 带紫色左边框的二级标题区块（竖条稍细）
- `### 三级标题` → 使用普通段落加粗样式

### 2. 引用块处理

- `> 引用内容` → 外层浅紫背景容器 + 内层渐变左边框容器
- 引用内容中的 `**粗体**` 保持紫色高亮

### 3. 列表处理

- 无序列表 `- 项目` → `<ul class="list-container">` + `<li>`
- 有序列表 `1. 项目` → `<ol class="list-container">` + `<li>`
- 列表项间距 10px，行高 2

### 4. 强调处理

- `**粗体**` → `<strong class="highlight">`（紫色加粗）
- `*斜体*` → `<em>`（斜体，灰色）
- `~~删除线~~` → `<del>`（删除线效果）

### 5. 图片处理

- `![alt](url)` → `<img src="url" alt="alt" style="display:block; margin:20px auto; max-width:100%; border-radius:8px;">`
- 图片居中显示，最大宽度100%，带圆角

### 6. 代码块处理

- `\`\`\`代码\`\`\`` → 浅灰色背景容器 (#f5f5f5)
- 等宽字体显示 (Monaco, Courier New)
- 左边框装饰，圆角8px
- 支持多行代码，自动换行

### 7. 段落处理

- 普通段落首行不缩进
- 段落间距通过 margin-top 控制
- 行高 240%，两端对齐

## 示例

### 输入 Markdown

```markdown
# 欢迎使用 Agent

Agent 是**数字化的高智商员工**，能够胜任一切用电脑能干的活。

> Agent 好不好用，要看你会不会管人。

你需要掌握三个技能：

- 把任务说清楚
- 发放合适的工具
- 检查工作结果

行动起来，**改变世界**！
```

### 输出 HTML 预览

生成的 HTML 将包含：
- 紫色主题的标题「欢迎使用 Agent」
- 正文中「数字化的高智商员工」显示为紫色加粗
- 引用块带浅紫背景和渐变左边框
- 列表项使用标准圆点列表
- 结尾「改变世界」为紫色加粗

## 注意事项

1. 生成的 HTML 为完整独立文件，包含所有必要的 CSS 样式
2. 用户可以直接用浏览器打开预览效果
3. 复制到公众号编辑器时，建议只复制 `<div class="article-container">` 内部的内容
4. 图片链接会被保留，但需要确保图片可访问

## 使用示例

用户请求：
> 请帮我将 @文章.md 转换成公众号风格的 HTML

执行步骤：
1. 读取 `/path/to/文章.md`
2. 解析 Markdown 内容
3. 应用转换规则
4. 生成 `/path/to/文章.html`
5. 告知用户转换完成
