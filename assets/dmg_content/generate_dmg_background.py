#!/usr/bin/env python3
"""Generate DMG background image with installation instructions and transparent holes."""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path


def create_dmg_background(output_path: Path, width: int = 480, height: int = 480):
    """Create a DMG background image with transparent holes for icons."""
    
    img = Image.new('RGBA', (width, height), color=(45, 55, 72, 255))
    draw = ImageDraw.Draw(img)
    
    try:
        title_font = ImageFont.truetype('LiberationSans-Bold.ttf', 28)
        body_font = ImageFont.truetype('LiberationSans-Regular.ttf', 17)
        small_font = ImageFont.truetype('LiberationSans-Bold.ttf', 15)
    except Exception:
        title_font = ImageFont.load_default()
        body_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    # Title centered
    title = "Installation guide (MacOS 10.15+)"
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    draw.text(((width - title_width) // 2, 15), title, fill='white', font=title_font)
    
    # Layout: [App Icon] [Instruction Text] [Right Sidebar]
    items = [
        (1, "Put Exe2Iconset.app to\nApplications folder", 135, 80),
        (2, "Copy Exit Quarantine.txt\ncontents to clipboard", 135, 180),
        (3, "Open Terminal, paste\ncommand, press Enter", 135, 280),
    ]
    
    for step_num, step_text, text_x, text_y in items:
        draw.text((text_x, text_y), f"{step_num}.", fill='#48bb78', font=body_font)
        lines = step_text.split('\n')
        for i, line in enumerate(lines):
            draw.text((text_x + 25, text_y + i * 35), line, fill='white', font=body_font)
    
    # Warning box at bottom
    warning_y = 380
    draw.rectangle([(30, warning_y), (width - 30, warning_y + 35)], outline='#ed8936', width=2)
    warning_text = "Only proceed if you trust this bundle"
    warning_bbox = draw.textbbox((0, 0), warning_text, font=small_font)
    warning_width = warning_bbox[2] - warning_bbox[0]
    draw.text(((width - warning_width) // 2, warning_y + 8), warning_text, fill='#ed8936', font=small_font)
    
    # Source info centered
    source_text = "Also available at pypi.org: pip install exe2iconset"
    source_bbox = draw.textbbox((0, 0), source_text, font=small_font)
    source_width = source_bbox[2] - source_bbox[0]
    draw.text(((width - source_width) // 2, height - 60), source_text, fill='#718096', font=small_font)
    
    # Transparent holes (x, y, width, height) for icons and shortcuts
    holes = [
        (25, 150, 100, 19),    # Exe2Iconset.app
        (342, 152, 100, 19),   # /Applications
        (343, 251, 100, 18),   # Exit Quarantine.txt
        (345, 350, 100, 20),   # Terminal.app
    ]
    
    for x, y, w, h in holes:
        for dy in range(h):
            for dx in range(w):
                img.putpixel((x + dx, y + dy), (0, 0, 0, 0))
    
    # White arrow from app bundle to Applications
    arrow_y = 110
    arrow_start = 120
    arrow_end = 350
    
    draw.line([(arrow_start, arrow_y), (arrow_end - 8, arrow_y)], fill='white', width=3)
    
    # Arrow head (triangle pointing right)
    head_tip = arrow_end - 2
    head_base = arrow_end - 12
    
    # Draw triangle using polygon
    draw.polygon([
        (head_tip, arrow_y),
        (head_base, arrow_y - 6),
        (head_base, arrow_y + 6),
    ], fill='white')
    
    # Circle at arrow start
    draw.ellipse([(arrow_start - 4, arrow_y - 4), (arrow_start + 4, arrow_y + 4)], fill='white')
    
    img.save(output_path, 'PNG')
    print(f"Created background image with holes: {output_path}")


if __name__ == '__main__':
    project_root = Path(__file__).parent.parent.parent
    output = project_root / 'build' / 'dmg_content' / 'dmg_background.png'
    output.parent.mkdir(parents=True, exist_ok=True)
    create_dmg_background(output)