#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
md2wchtml - Markdown 转微信公众号风格 HTML (内联样式版)
生成与手工归档文章.html一致的内联样式
"""

import re
import sys
import os
from pathlib import Path


def extract_title_from_md(md_content: str) -> str:
    """从 Markdown 内容中提取标题"""
    # 跳过 YAML frontmatter (如果存在)
    content = md_content.strip()
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            content = parts[2].strip()
    
    # 尝试从第一行 # 标题提取
    match = re.search(r'^# (.+)$', content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    
    # 尝试从文件名或前20个字符提取
    first_line = content.split('\n')[0]
    if len(first_line) > 30:
        return first_line[:30] + '...'
    return first_line or '文章标题'


def md_to_wechat_html(md_content: str, title: str = "文章标题") -> str:
    """
    将 Markdown 内容转换为微信公众号风格的 HTML (内联样式)
    """
    html_content = md_content
    
    # 跳过 YAML frontmatter (如果存在)
    if html_content.strip().startswith('---'):
        parts = html_content.split('---', 2)
        if len(parts) >= 3:
            html_content = parts[2].strip()
    
    # 处理代码块 (需要在处理其他内容之前，避免被其他处理器干扰)
    code_blocks = []
    
    def extract_code_block(match):
        code_content = match.group(1)
        idx = len(code_blocks)
        code_blocks.append(code_content)
        return f"<!--CODE_BLOCK_{idx}-->"
    
    # 匹配 ```...``` 格式的代码块
    code_pattern = r'```(?:\w+)?\n(.*?)\n```'
    html_content = re.sub(code_pattern, extract_code_block, html_content, flags=re.DOTALL)
    
    # 先处理粗体和斜体（图片 alt 中可能包含）
    html_content = process_emphasis(html_content)
    
    # 处理图片
    html_content = process_images(html_content)
    
    # 处理引用块
    html_content = process_blockquotes(html_content)
    
    # 处理标题
    html_content = process_headings(html_content)
    
    # 处理列表
    html_content = process_lists(html_content)
    
    # 处理段落
    html_content = process_paragraphs(html_content)
    
    # 恢复代码块
    for i, code_content in enumerate(code_blocks):
        placeholder = f"<!--CODE_BLOCK_{i}-->"
        code_html = f'''<pre style="margin: 0; padding: 16px; background-color: #f5f5f5; border-radius: 4px; font-family: 'SF Mono', Monaco, 'Courier New', 'PingFang SC', 'Microsoft YaHei', monospace; font-size: 14px; line-height: 1.6; color: #333; white-space: pre-wrap; word-break: break-all; overflow-x: auto;">{code_content}</pre>'''
        html_content = html_content.replace(placeholder, code_html)
    
    # 清理多余的空行
    html_content = re.sub(r'\n\n+', '\n', html_content)
    
    return html_content


def process_images(content: str) -> str:
    """处理图片 ![alt](url)"""
    import html
    pattern = r'!\[(.*?)\]\((.*?)\)'
    
    def replace_image(match):
        alt_text = match.group(1)
        img_url = match.group(2)
        # 移除 alt 文本中的 HTML 标签
        alt_text = re.sub(r'<[^>]+>', '', alt_text)
        return f'''<p style="margin: 16px 0; line-height: 1.8; color: #1f2937;"><img src="{img_url}" alt="{alt_text}" style="max-width: 100%; height: auto; display: block; margin: 0 auto;" /></p>'''
    
    content = re.sub(pattern, replace_image, content)
    return content


def process_blockquotes(content: str) -> str:
    """处理引用块 > 文本 - 使用内联样式"""
    # 匹配多行引用块
    pattern = r'(^> .+$\n?)+'
    
    def replace_quote(match):
        quote_text = match.group(0)
        # 移除 > 符号并合并
        lines = quote_text.strip().split('\n')
        text = ' '.join([line[2:].strip() for line in lines])
        # 处理内部的高亮和斜体
        text = process_inline_emphasis(text)
        
        return f'''<blockquote style="padding: 8px 12px; background: linear-gradient(135deg, #fafafa 0%, #fff 100%); border-left: 3px solid #5965af; border-radius: 0 8px 8px 0; box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08); margin: 28px 4px 0; position: relative">
<p style="margin: 16px 0; line-height: 1.8; color: #1f2937; font-family: 'Noto Sans SC', sans-serif; font-weight: normal; font-size: 17px; font-style: normal">{text}</p>
</blockquote>'''
    
    content = re.sub(pattern, replace_quote, content, flags=re.MULTILINE)
    return content


def process_headings(content: str) -> str:
    """处理标题 # ## ### - 使用内联样式"""
    lines = content.split('\n')
    result = []
    
    for line in lines:
        # 一级标题 # 标题
        if re.match(r'^# .+$', line):
            title = re.sub(r'^# ', '', line).strip()
            result.append(f'''<h2 style="font-weight: 700; line-height: 1; margin-top: 48px; margin-bottom: 32px; color: #1f2937; font-size: 22px; padding-left: 16px; border-left: 5px solid #474f9f; padding-top: 0; padding-bottom: 0">{title}</h2>''')
        # 二级标题 ## 标题
        elif re.match(r'^## .+$', line):
            title = re.sub(r'^## ', '', line).strip()
            result.append(f'''<h2 style="font-weight: 700; line-height: 1; margin-top: 48px; margin-bottom: 32px; color: #1f2937; font-size: 22px; padding-left: 16px; border-left: 5px solid #474f9f; padding-top: 0; padding-bottom: 0">{title}</h2>''')
        # 三级标题 ### 标题
        elif re.match(r'^### .+$', line):
            title = re.sub(r'^### ', '', line).strip()
            result.append(f'''<h2 style="font-weight: 700; line-height: 1; margin-top: 48px; margin-bottom: 32px; color: #1f2937; font-size: 22px; padding-left: 16px; border-left: 5px solid #474f9f; padding-top: 0; padding-bottom: 0">{title}</h2>''')
        else:
            result.append(line)
    
    return '\n'.join(result)


def process_lists(content: str) -> str:
    """处理列表 - 使用内联样式"""
    lines = content.split('\n')
    result = []
    in_ul = False
    in_ol = False
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # 无序列表
        if re.match(r'^- .+$', line):
            if not in_ul:
                if in_ol:
                    result.append('</ol>')
                    in_ol = False
                result.append('<ul style="margin: 16px 0; padding-left: 24px">')
                in_ul = True
            item_text = re.sub(r'^- ', '', line).strip()
            item_text = process_inline_emphasis(item_text)
            result.append(f'<li style="margin: 8px 0; line-height: 1.8; position: relative">{item_text}</li>')
        
        # 有序列表
        elif re.match(r'^\d+\. .+$', line):
            if not in_ol:
                if in_ul:
                    result.append('</ul>')
                    in_ul = False
                result.append('<ol style="margin: 16px 0; padding-left: 24px; counter-reset: item">')
                in_ol = True
            item_text = re.sub(r'^\d+\. ', '', line).strip()
            item_text = process_inline_emphasis(item_text)
            result.append(f'<li style="margin: 8px 0; line-height: 1.8; position: relative">{item_text}</li>')
        
        else:
            if in_ul:
                result.append('</ul>')
                in_ul = False
            if in_ol:
                result.append('</ol>')
                in_ol = False
            result.append(line)
        
        i += 1
    
    # 关闭未闭合的列表
    if in_ul:
        result.append('</ul>')
    if in_ol:
        result.append('</ol>')
    
    return '\n'.join(result)


def process_emphasis(content: str) -> str:
    """处理粗体和斜体 - 使用内联样式"""
    # 处理粗体 **文本**
    content = re.sub(r'\*\*(.+?)\*\*', r'<strong style="font-weight: 600; color: #474f9f">\1</strong>', content)
    # 处理斜体 *文本*
    content = re.sub(r'\*(.+?)\*', r'<em style="font-style: italic; color: #4b5563">\1</em>', content)
    # 处理删除线 ~~文本~~
    content = re.sub(r'~~(.+?)~~', r'<del>\1</del>', content)
    return content


def process_inline_emphasis(text: str) -> str:
    """处理行内强调"""
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong style="font-weight: 600; color: #474f9f">\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em style="font-style: italic; color: #4b5563">\1</em>', text)
    return text


def process_paragraphs(content: str) -> str:
    """处理普通段落 - 使用内联样式"""
    lines = content.split('\n')
    result = []
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # 跳过空行和已经是块级 HTML 的行（内联标签如 <strong> 仍需包裹段落）
        if not line or re.match(r'^<(h\d|ul|ol|li|blockquote|pre|table|div|section|p|hr|tr|td|th)', line) or line.startswith('    '):
            result.append(lines[i])
            i += 1
            continue
        
        # 收集段落文本
        paragraph_lines = []
        while i < len(lines):
            current = lines[i].strip()
            if not current or re.match(r'^<(h\d|ul|ol|li|blockquote|pre|table|div|section|p|hr|tr|td|th)', current) or current.startswith('- ') or re.match(r'^\d+\.', current):
                break
            paragraph_lines.append(lines[i])
            i += 1
        
        if paragraph_lines:
            paragraph_text = ' '.join(paragraph_lines)
            paragraph_text = process_inline_emphasis(paragraph_text)
            
            result.append(f'<p style="margin: 16px 0; line-height: 1.8; color: #1f2937">{paragraph_text}</p>')
        else:
            i += 1
    
    return '\n'.join(result)


def generate_full_html(content: str, title: str) -> str:
    """生成完整的 HTML 文件 - 只保留基本结构，全部内联样式"""
    
    html_template = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
</head>
<body>
{content}
</body>
</html>'''
    
    return html_template


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python md2wchtml.py <markdown文件路径> [输出文件路径]")
        print("示例: python md2wchtml.py 文章.md")
        print("      python md2wchtml.py 文章.md 输出.html")
        sys.exit(1)
    
    md_file = sys.argv[1]
    
    # 检查文件是否存在
    if not os.path.exists(md_file):
        print(f"错误: 文件不存在 - {md_file}")
        sys.exit(1)
    
    # 读取 Markdown 文件
    try:
        with open(md_file, 'r', encoding='utf-8') as f:
            md_content = f.read()
    except Exception as e:
        print(f"错误: 读取文件失败 - {e}")
        sys.exit(1)
    
    # 提取标题
    title = extract_title_from_md(md_content)
    
    # 转换为 HTML
    html_body = md_to_wechat_html(md_content, title)
    html_content = generate_full_html(html_body, title)
    
    # 确定输出文件路径
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
    else:
        # 默认输出到同目录，文件名加 .html 后缀
        md_path = Path(md_file)
        output_file = md_path.parent / f"{md_path.stem}.html"
    
    # 写入 HTML 文件
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"✅ 转换成功!")
        print(f"📄 Markdown文件: {md_file}")
        print(f"🌐 HTML文件: {output_file}")
        print(f"\n提示: 可以直接用浏览器打开 HTML 文件预览效果")
        print(f"      复制到公众号时，建议只复制 body 标签内的内容")
    except Exception as e:
        print(f"错误: 写入文件失败 - {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
