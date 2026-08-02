const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

/**
 * Markdown Article Illustrator
 * 
 * Reads a markdown article, understands its structure by headings,
 * generates illustrations for each section using YouMind CLI with hand-drawn style prompts,
 * downloads images to the article's directory, and inserts them into the markdown file.
 * 
 * Usage:
 *   node generate-images.js <markdown-file> [--regenerate | --replace <index>]
 * 
 * Options:
 *   --regenerate    Regenerate all images
 *   --replace <n>   Replace specific image (0-based index)
 */

// Configuration
const PROMPT_TEMPLATE_PATH = path.join(__dirname, '..', 'prompts', '手绘简笔画.md');
const BOARD_ID = '019aae62-a3d5-7bfb-9d77-8cef58acae0e'; // YouMind board ID for image generation
const MAX_RETRIES = 3;
const RETRY_DELAY = 5000; // 5 seconds

/**
 * Parse markdown file and split into sections by headings
 * Only processes level 2+ headings (##, ###, etc.)
 */
function parseMarkdown(filePath) {
  const content = fs.readFileSync(filePath, 'utf-8');
  const lines = content.split('\n');
  
  const sections = [];
  let currentSection = null;
  let globalIndex = 0;
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const headingMatch = line.match(/^(#{2,6})\s+(.+)$/); // Only match level 2-6 headings
    
    if (headingMatch) {
      // Save previous section
      if (currentSection) {
        sections.push(currentSection);
      }
      
      // Start new section
      currentSection = {
        index: globalIndex++,
        level: headingMatch[1].length,
        title: headingMatch[2].trim(),
        headingLine: i,
        content: [line],
        endLine: i
      };
    } else if (currentSection) {
      currentSection.content.push(line);
      currentSection.endLine = i;
    }
  }
  
  // Don't forget the last section
  if (currentSection) {
    sections.push(currentSection);
  }
  
  return { content, lines, sections };
}

/**
 * Extract the main theme or golden sentence from a section
 */
function extractTheme(section) {
  const text = section.content.join('\n');
  const contentLines = text.split('\n').filter(l => l.trim());
  
  // First, look for quoted text or emphasized text
  for (const line of contentLines) {
    const trimmed = line.trim();
    if (trimmed.match(/["'][^"']{10,}["']/) || trimmed.match(/[「」][^「」]{10,}[「」]/)) {
      return trimmed.replace(/["'「」]/g, '');
    }
  }
  
  // Then look for short impactful lines (potential golden sentences)
  for (const line of contentLines) {
    const trimmed = line.trim();
    if (trimmed.length > 10 && trimmed.length < 100 && 
        !trimmed.startsWith('#') && 
        !trimmed.startsWith('-') && 
        !trimmed.startsWith('*')) {
      return trimmed;
    }
  }
  
  // Fallback: use the heading title
  return section.title;
}

/**
 * Call YouMind API with JSON payload via stdin
 */
function callYouMind(payload) {
  const tempDir = require('os').tmpdir();
  const tempFile = path.join(tempDir, `youmind_${Date.now()}.json`);
  fs.writeFileSync(tempFile, JSON.stringify(payload), 'utf-8');
  
  try {
    const result = execSync(`cat "${tempFile}" | youmind-proxy call createChat`, {
      encoding: 'utf-8',
      timeout: 120000,
      maxBuffer: 50 * 1024 * 1024
    });
    
    return JSON.parse(result);
  } finally {
    try { fs.unlinkSync(tempFile); } catch (e) {}
  }
}

/**
 * Get messages from a chat
 */
function getChatMessages(chatId) {
  const tempDir = require('os').tmpdir();
  const tempFile = path.join(tempDir, `youmind_messages_${Date.now()}.json`);
  fs.writeFileSync(tempFile, JSON.stringify({
    chatId: chatId,
    pageSize: 20
  }), 'utf-8');
  
  try {
    const result = execSync(`cat "${tempFile}" | youmind-proxy call listMessages`, {
      encoding: 'utf-8',
      timeout: 60000,
      maxBuffer: 50 * 1024 * 1024
    });
    
    return JSON.parse(result);
  } finally {
    try { fs.unlinkSync(tempFile); } catch (e) {}
  }
}

/**
 * Extract image URL from messages response
 */
function extractImageUrlFromMessages(messagesResponse) {
  if (!messagesResponse.messages) return null;
  
  // Look through all messages for image URLs
  for (const message of messagesResponse.messages) {
    if (message.blocks) {
      for (const block of message.blocks) {
        // Check for tool blocks with image generation results
        if (block.type === 'tool' && block.toolResult) {
          // Look for image URLs in tool results
          const resultStr = JSON.stringify(block.toolResult);
          const urlMatch = resultStr.match(/https?:\/\/[^\s"']+\.(?:png|jpg|jpeg|webp|gif)/i);
          if (urlMatch) {
            return urlMatch[0];
          }
        }
        
        // Check for content blocks with URLs
        if (block.data) {
          const urlMatch = block.data.match(/https?:\/\/[^\s"']+\.(?:png|jpg|jpeg|webp|gif)/i);
          if (urlMatch) {
            return urlMatch[0];
          }
        }
      }
    }
    
    // Check message content for URLs
    if (message.content) {
      const urlMatch = message.content.match(/https?:\/\/[^\s"']+\.(?:png|jpg|jpeg|webp|gif)/i);
      if (urlMatch) {
        return urlMatch[0];
      }
    }
  }
  
  return null;
}

/**
 * Generate image using YouMind CLI
 */
async function generateImage(theme, outputPath) {
  const promptTemplate = fs.readFileSync(PROMPT_TEMPLATE_PATH, 'utf-8');
  const fullPrompt = `${promptTemplate}\n=========\n${theme}`;
  
  console.log(`\n🎨 Generating image for: "${theme.substring(0, 50)}${theme.length > 50 ? '...' : ''}"`);
  console.log(`   Output: ${outputPath}`);
  
  let lastError = null;
  
  for (let attempt = 1; attempt <= MAX_RETRIES; attempt++) {
    try {
      console.log(`   Attempt ${attempt}/${MAX_RETRIES}...`);
      
      // Step 1: Create chat to generate image
      const createPayload = {
        boardId: BOARD_ID,
        message: fullPrompt,
        tools: {
          imageGenerate: {
            useTool: "required"
          }
        }
      };
      
      console.log(`   Creating chat...`);
      const createResponse = callYouMind(createPayload);
      
      if (!createResponse.id) {
        lastError = new Error('Failed to create chat: no chat ID returned');
        continue;
      }
      
      const chatId = createResponse.id;
      console.log(`   Chat created: ${chatId}`);
      
      // Step 2: Wait for image generation and get messages
      console.log(`   Waiting for image generation...`);
      await new Promise(resolve => setTimeout(resolve, 10000)); // Wait 10 seconds
      
      // Step 3: Get chat messages to find image URL
      console.log(`   Fetching messages...`);
      let imageUrl = null;
      let messageAttempts = 0;
      const maxMessageAttempts = 6;
      
      while (!imageUrl && messageAttempts < maxMessageAttempts) {
        messageAttempts++;
        
        try {
          const messagesResponse = getChatMessages(chatId);
          imageUrl = extractImageUrlFromMessages(messagesResponse);
          
          if (!imageUrl) {
            console.log(`   No image URL yet, retrying... (${messageAttempts}/${maxMessageAttempts})`);
            await new Promise(resolve => setTimeout(resolve, 5000));
          }
        } catch (e) {
          console.log(`   Error fetching messages: ${e.message}`);
          await new Promise(resolve => setTimeout(resolve, 5000));
        }
      }
      
      if (!imageUrl) {
        lastError = new Error('No image URL found after waiting');
        continue;
      }
      
      console.log(`   Found image URL: ${imageUrl.substring(0, 80)}...`);
      
      // Step 4: Download the image
      const downloadResult = await downloadImage(imageUrl, outputPath);
      
      if (downloadResult) {
        console.log(`   ✅ Image saved to ${outputPath}`);
        return outputPath;
      } else {
        lastError = new Error('Failed to download image');
      }
      
    } catch (error) {
      lastError = error;
      console.error(`   Attempt ${attempt} failed: ${error.message}`);
      
      if (attempt < MAX_RETRIES) {
        console.log(`   Retrying in ${RETRY_DELAY}ms...`);
        await new Promise(resolve => setTimeout(resolve, RETRY_DELAY));
      }
    }
  }
  
  // All retries exhausted
  console.error(`   ❌ All ${MAX_RETRIES} attempts failed. Last error: ${lastError?.message}`);
  return null;
}

/**
 * Download image from URL to local path
 */
async function downloadImage(url, outputPath) {
  try {
    // Use curl to download with follow redirects
    execSync(`curl -L -s --max-time 60 -o "${outputPath}" "${url}"`, { 
      encoding: 'utf-8',
      timeout: 60000 
    });
    
    // Verify the file was downloaded and is not empty
    const stats = fs.statSync(outputPath);
    if (stats.size === 0) {
      console.error('   Downloaded file is empty');
      return false;
    }
    
    return true;
  } catch (error) {
    console.error(`   Failed to download image: ${error.message}`);
    return false;
  }
}

/**
 * Generate image filename based on theme
 */
function generateImageFilename(sectionIndex, theme) {
  // Clean the theme for filename
  const cleanTheme = theme
    .replace(/[^\w\u4e00-\u9fa5]/g, '_')
    .substring(0, 20);
  
  return `illustration_${sectionIndex}_${cleanTheme}.png`;
}

/**
 * Check if a section already has an image
 */
function sectionHasImage(section, lines) {
  const sectionText = section.content.join('\n');
  return sectionText.includes('![') || sectionText.includes('<img');
}

/**
 * Insert image markdown into section
 */
function insertImageIntoSection(lines, section, imagePath, imageAlt) {
  const newLines = [...lines];
  
  // Find the insertion point (end of section content)
  // We insert after the section's last line
  const insertLine = section.endLine + 1;
  
  // Generate relative path for image
  const dirName = path.dirname(imagePath);
  const fileName = path.basename(imagePath);
  const relativePath = path.join(dirName, fileName).replace(/\\/g, '/');
  
  // Create image markdown
  const imageMarkdown = `\n![${imageAlt}](${relativePath})\n`;
  
  // Insert after the section's last line
  newLines.splice(insertLine, 0, imageMarkdown);
  
  return newLines;
}

/**
 * Main function
 */
async function main() {
  const args = process.argv.slice(2);
  
  if (args.length < 1) {
    console.error('Usage: node generate-images.js <markdown-file> [--regenerate | --replace <index>]');
    process.exit(1);
  }
  
  const filePath = args[0];
  const regenerate = args.includes('--regenerate');
  const replaceIndex = args.includes('--replace') ? 
    parseInt(args[args.indexOf('--replace') + 1]) : -1;
  
  if (!fs.existsSync(filePath)) {
    console.error(`Error: File not found: ${filePath}`);
    process.exit(1);
  }
  
  console.log(`📖 Reading: ${filePath}`);
  
  const { content, lines, sections } = parseMarkdown(filePath);
  const dir = path.dirname(filePath);
  
  console.log(`Found ${sections.length} sections (level 2+ headings)`);
  
  if (sections.length === 0) {
    console.log('No sections found. Exiting.');
    process.exit(0);
  }
  
  // Determine which sections need images
  const sectionsToProcess = [];
  
  for (const section of sections) {
    // Skip if replace is specified and this is not the target
    if (replaceIndex >= 0 && section.index !== replaceIndex) {
      continue;
    }
    
    // Skip if already has image and not regenerating
    if (!regenerate && replaceIndex < 0 && sectionHasImage(section, lines)) {
      console.log(`⏭️  Section ${section.index}: "${section.title}" - Already has image, skipping`);
      continue;
    }
    
    sectionsToProcess.push(section);
  }
  
  console.log(`\n🎯 Processing ${sectionsToProcess.length} sections...\n`);
  
  // Process each section
  let currentLines = [...lines];
  let totalOffset = 0;
  
  for (const section of sectionsToProcess) {
    console.log(`\n📌 Section ${section.index}: "${section.title}"`);
    
    // Extract theme
    const theme = extractTheme(section);
    console.log(`   Theme: ${theme}`);
    
    // Generate image filename
    const imageFilename = generateImageFilename(section.index, theme);
    const imagePath = path.join(dir, imageFilename);
    
    // Check if image file already exists (from previous run)
    if (fs.existsSync(imagePath) && !regenerate) {
      console.log(`⏭️  Section ${section.index}: "${section.title}" - Image file already exists, skipping`);
      continue;
    }
    
    // Generate image
    const generatedPath = await generateImage(theme, imagePath);
    
    if (generatedPath) {
      // Update section end line to account for added lines
      const originalEndLine = section.endLine + totalOffset;
      
      // Insert image into markdown
      currentLines = insertImageIntoSection(currentLines, {
        ...section,
        endLine: originalEndLine
      }, generatedPath, theme);
      
      // Account for added lines (we add 1 line for the image markdown)
      totalOffset += 1;
    }
    
    // Small delay to avoid rate limiting
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
  
  // Write updated markdown
  const newContent = currentLines.join('\n');
  fs.writeFileSync(filePath, newContent, 'utf-8');
  
  console.log(`\n✅ Done! Updated: ${filePath}`);
  console.log(`   Processed ${sectionsToProcess.length} sections`);
}

// Run main
main().catch(error => {
  console.error('Error:', error);
  process.exit(1);
});
