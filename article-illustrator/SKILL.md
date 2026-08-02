---
name: article-illustrator
description: Reads a markdown article, understands its structure by headings, generates illustrations for each section using YouMind CLI with hand-drawn style prompts, downloads images to the article's directory, and inserts them into the markdown file. Supports full regeneration or replacing specific images.
triggers:
  - "generate article images"
  - "illustrate markdown"
  - "article images"
  - "generate illustrations"
  - "配图"
  - "文章配图"
  - "markdown配图"
  - "生成配图"
platform:
  - openclaw
  - claude-code
  - cursor
  - codex
  - gemini-cli
  - windsurf
  - kilo
  - opencode
  - goose
  - roo
allowed-tools:
  - Bash(node *)
  - Read(*.md)
  - Write(*.md)
---

# Article Illustrator

Reads a markdown article, understands its structure by headings (#, ##, etc.), generates illustrations for each section using YouMind CLI with hand-drawn style prompts, downloads images to the article's directory, and inserts them into the markdown file.

## Features

- **Heading-based segmentation**: Automatically splits article by markdown headings (#, ##, ###, etc.)
- **Theme extraction**: Extracts the main theme or golden sentence from each section
- **Hand-drawn style**: Uses "手绘简笔画" (hand-drawn sketch) prompt template
- **Automatic insertion**: Inserts images at the end of each section (as explanation of above text)
- **Regeneration support**: Supports regenerating all images or replacing specific ones

## Usage

### Generate images for all sections

```bash
node scripts/generate-images.js <markdown-file>
```

### Regenerate all images

```bash
node scripts/generate-images.js <markdown-file> --regenerate
```

### Replace a specific image

```bash
node scripts/generate-images.js <markdown-file> --replace <section-index>
```

Where `<section-index>` is the 0-based index of the section to replace.

## Workflow

1. **Parse**: Read the markdown file and split into sections by headings
2. **Extract**: For each section, extract the main theme or golden sentence
3. **Generate**: Call YouMind API with the hand-drawn prompt template + theme
4. **Download**: Save the generated image to the article's directory
5. **Insert**: Add the image markdown at the end of each section
6. **Write**: Update the original markdown file

## Image Insertion Rules

- Images are inserted at the **end of each section** (after the section's content, before the next heading)
- This ensures the image serves as a visual summary/explanation of the above text
- The image markdown format: `![alt-text](image-path)`

## Prompt Template

The skill uses `prompts/手绘简笔画.md` as the prompt template. This template defines:
- Role: Professional hand-drawn note artist and information designer
- Style: Hand-drawn sketch style with clean, minimalist lines
- Layout: Clear, simple, logical with 4:3 aspect ratio
- Colors: Black lines on white background, no gradients or shadows

## Output

- Images are saved in the same directory as the markdown file
- Filenames are auto-generated based on section theme
- The original markdown file is updated in-place with image references

## Dependencies

- Node.js
- youmind-proxy CLI (installed globally via `npm install -g @youmind-ai/cli`)
- YouMind API key (configured in `~/.agents/skills/youmind/.env`)
