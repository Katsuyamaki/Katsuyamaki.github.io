from PIL import Image, ImageDraw, ImageFilter, ImageFont
import os

os.makedirs("final_screenshots", exist_ok=True)

# Config
font_path_regular = "/system/fonts/Roboto-Regular.ttf"
font_path_bold = "/system/fonts/DroidSans-Bold.ttf"
template_path = "temp_images/view.jpg"
CANVAS_WIDTH = 1080
CANVAS_HEIGHT = 1920
BG_COLOR = (0, 0, 0) # True Black

# Define Captions
CAPTIONS = {
    1: ("Queue-Based Window Tiling", 
        "Transform your device into a desktop-class multitasking productivity workstation."),
    
    2: ("Intelligent App Queue", 
        "Organize and tile apps automatically from the drawer. Professional layout without manual dragging."),
    
    3: ("Pro Display Controls", 
        "Precision tools to adjust windows, resolution, DPI, and refresh rate for optimized screen viewing."),
    
    4: ("Universal Display Support", 
        "Optimized for mobile screens, external monitors, and AR glasses across various devices."),
    
    5: ("Flexible Workflow Modes", 
        "Enhance your current desktop mode or use DroidOS as a standalone launcher replacement."),
    
    6: ("Persistent Keyboard Support", 
        "Enable keybind window management with the DroidOS Keyboard & Trackpad (Available separately)."),
    
    7: ("Automation & Keybinds", 
        "Custom hotkeys for window management. Fully compatible with Tasker and MacroDroid broadcasts."),
    
    8: ("Rapid Window Switching", 
        "Switch active window focus instantly via keyboard to manage text input.")
}

def key_out_black(img, threshold=15):
    img = img.convert('RGBA')
    gray = img.convert('L')
    mask = gray.point(lambda x: 255 if x > threshold else 0, 'L')
    img.putalpha(mask)
    return img

def add_rounded_corners(im, rad, top_only=True):
    mask = Image.new('L', im.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, im.size[0], im.size[1]), radius=rad, fill=255)
    if top_only:
        draw.rectangle((0, rad, im.size[0], im.size[1]), fill=255)
    result = im.copy()
    result.putalpha(mask)
    return result

def wrap_text(text, font, max_width):
    lines = []
    for segment in text.split('\n'):
        words = segment.split()
        if not words:
            lines.append("")
            continue
        
        current_line = words[0]
        for word in words[1:]:
            test_line = current_line + " " + word
            bbox = font.getbbox(test_line)
            w = bbox[2] - bbox[0]
            if w <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        lines.append(current_line)
    return lines

def generate_screenshot(index, hook, sub, raw_dir):
    files = [f for f in os.listdir(raw_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    if not files:
        print(f"Skipping folder {index}: No image found.")
        return
    
    raw_path = os.path.join(raw_dir, files[0])
    print(f"Processing #{index}: {raw_path}")

    # 1. Background (Blurred Screenshot)
    ss_original = Image.open(raw_path).convert('RGBA')
    bg_ss = ss_original.resize((CANVAS_WIDTH, CANVAS_HEIGHT), Image.Resampling.LANCZOS)
    bg_blur = bg_ss.filter(ImageFilter.GaussianBlur(radius=60))
    bg_overlay = Image.new('RGB', (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0))
    canvas = Image.blend(bg_blur.convert('RGB'), bg_overlay, alpha=0.7)
    draw = ImageDraw.Draw(canvas)

    # 2. Load & Prepare Phone Template
    template = Image.open(template_path).convert('RGBA')
    template = template.crop((0, 980, 1080, 2520))
    template = key_out_black(template)
    
    # 3. Process Screenshot
    ss = ss_original.copy()
    
    # Standard Portrait Frame
    # Crop status bar
    ss_w, ss_h = ss.size
    ss = ss.crop((0, 100, ss_w, ss_h)) 
    
    target_ss_w = 831 
    target_ss_h = int((ss.size[1] / ss.size[0]) * target_ss_w)
    ss = ss.resize((target_ss_w, target_ss_h), Image.Resampling.LANCZOS)
    ss = add_rounded_corners(ss, rad=60)

    template_x = 0
    template_y = 480 
    
    # Shadow for Portrait
    shadow_margin = 40
    shadow = Image.new('RGBA', (template.size[0] + shadow_margin*2, template.size[1] + shadow_margin*2), (0,0,0,0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle((shadow_margin, shadow_margin, shadow_margin + template.size[0], shadow_margin + template.size[1]), radius=60, fill=(0,0,0,160))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=30))
    
    canvas.paste(shadow, (template_x - shadow_margin, template_y - shadow_margin + 20), shadow)
    canvas.paste(template, (template_x, template_y), template)
    
    ss_x = 134
    ss_y = template_y + 33
    canvas.paste(ss, (ss_x, ss_y), ss)

    # 5. Text
    try:
        hook_font = ImageFont.truetype(font_path_bold, 72)
        sub_font = ImageFont.truetype(font_path_regular, 38)
    except Exception as e:
        print("Font error:", e)
        hook_font = ImageFont.load_default()
        sub_font = ImageFont.load_default()

    def draw_text_centered(text, font, y_pos, color):
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        x = (CANVAS_WIDTH - tw) // 2
        draw.text((x, y_pos), text, font=font, fill=color, align="center")

    MAX_TEXT_WIDTH = CANVAS_WIDTH - 160 
    HOOK_SUB_GAP = 30
    hook_lines = wrap_text(hook, hook_font, MAX_TEXT_WIDTH)
    sub_lines = wrap_text(sub, sub_font, MAX_TEXT_WIDTH)

    hook_h = len(hook_lines) * 85
    sub_h = len(sub_lines) * 50
    total_text_h = hook_h + HOOK_SUB_GAP + sub_h
    
    current_y = (480 - total_text_h) // 2
    if current_y < 40: current_y = 40 

    for line in hook_lines:
        draw_text_centered(line, hook_font, current_y, (255, 255, 255))
        current_y += 85
    current_y += HOOK_SUB_GAP
    for line in sub_lines:
        draw_text_centered(line, sub_font, current_y, (180, 180, 180))
        current_y += 50

    # 6. Save
    output_name = f"final_screenshots/{index}_processed.jpg"
    canvas = canvas.convert('RGB')
    canvas.save(output_name, "JPEG", quality=95)
    print(f"Generated: {output_name}")

# Run for all folders
for i in range(1, 9):
    raw_dir = f"raw_screenshots/{i}"
    if os.path.exists(raw_dir):
        hook, sub = CAPTIONS[i]
        generate_screenshot(i, hook, sub, raw_dir)
