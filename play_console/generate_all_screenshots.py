from PIL import Image, ImageDraw, ImageFont
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
    1: ("DroidOS - A Queue-Based Window Tiling Manager", "Turn your phone into a desktop-class multitasking productivity workstation."),
    2: ("Launcher Drawer & App Queue", "Manage app layout from app drawer. Automatically organized & tiled - no wasted time draging & resizing."),
    3: ("Precision Display Control", "Pro-grade tools to adjust resolution, DPI, and refresh rate for any screen."),
    4: ("Complete Compatibilty", "Built for native device screen, external monitors and AR display glasses. Made for any Android phone device/manufacturer."),
    5: ("Transform Your Workflow or Adapt Existing", "DroidOS can enhance other launchers, themes and desktop modes or be a standalone replacement."),
    6: ("The Ultimate Keyboard Companion", "DroidOS Keyboard & Trackpad enables keybind control window management with a persistent togglable keybooard while system keyboards cannot remain open (Available separately)."),
    7: ("External Keyboard, Keybind and Automation Capabilities", "Enhances keyboard only workflow and custom keybinds to control app window and display management. Fully broadcast-ready for Tasker and MacroDroid. Automation built for pros."),
    8: ("Custom Window Focus System", "Switch between active app windows with a keypress to input text or manage windows - avoid slow clicks and touches.")
}

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
    # If text contains manual newlines, split them first
    for segment in text.split('\n'):
        words = segment.split()
        if not words:
            lines.append("")
            continue
        
        current_line = words[0]
        for word in words[1:]:
            # Check width if we add the next word
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

    # 1. Background
    canvas = Image.new('RGB', (CANVAS_WIDTH, CANVAS_HEIGHT), color=BG_COLOR)
    draw = ImageDraw.Draw(canvas)

    # 2. Load & Prepare Phone Template
    template = Image.open(template_path).convert('RGBA')
    template = template.crop((0, 980, 1080, 2520))
    
    # 3. Load & Prepare App Screenshot
    ss = Image.open(raw_path).convert('RGBA')
    
    if index == 5:
        # 1. Prepare Symmetrical Phone Frame from Original Template
        # Original template is 1080x1540. We mirror it to make a whole phone.
        half = template.crop((0, 0, 1080, 770))
        full = Image.new('RGBA', (1080, 1540), (0,0,0,0))
        full.paste(half, (0, 0))
        full.paste(half.transpose(Image.FLIP_TOP_BOTTOM), (0, 770))
        template_landscape = full.rotate(90, expand=True) # 1540x1080
        
        # 2. Create Blurred Background
        from PIL import ImageFilter
        bg_ss = ss.resize((CANVAS_WIDTH, CANVAS_HEIGHT), Image.Resampling.LANCZOS)
        bg_blur = bg_ss.filter(ImageFilter.GaussianBlur(radius=60))
        bg_overlay = Image.new('RGB', (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0))
        canvas = Image.blend(bg_blur.convert('RGB'), bg_overlay, alpha=0.5)
        draw = ImageDraw.Draw(canvas)

        # 3. Scale and Position (Close-up look)
        # Scale 1.0 means phone height (1080) matches canvas width (1080).
        scale = 1.0
        
        # Inner screen area in unscaled landscape frame:
        # Height = 1080 - 115 - 134 = 831
        # Width = 1540 - 33 - 33 = 1474
        target_ss_h = 831
        target_ss_w = int((ss.size[0] / ss.size[1]) * target_ss_h)
        if target_ss_w > 1474: target_ss_w = 1474
        
        ss_resized = ss.resize((target_ss_w, target_ss_h), Image.Resampling.LANCZOS)
        ss_resized = add_rounded_corners(ss_resized, rad=40, top_only=False)
        
        # 4. Composite
        template_x = (CANVAS_WIDTH - 1540) // 2 
        template_y = 600
        
        # Rich drop shadow for depth
        shadow_margin = 40
        shadow = Image.new('RGBA', (template_landscape.size[0] + shadow_margin*2, template_landscape.size[1] + shadow_margin*2), (0,0,0,0))
        shadow_mask = Image.new('L', template_landscape.size, 140)
        shadow.paste((0,0,0,180), (shadow_margin, shadow_margin), shadow_mask)
        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=30))
        
        canvas.paste(shadow, (template_x - shadow_margin, template_y - shadow_margin + 20), shadow)
        canvas.paste(template_landscape, (template_x, template_y), template_landscape)
        
        ss_x = (CANVAS_WIDTH - target_ss_w) // 2
        ss_y = template_y + 115 
        canvas.paste(ss_resized, (ss_x, ss_y), ss_resized)
    else:
        # CROP STATUS BAR for portrait
        ss_w, ss_h = ss.size
        ss = ss.crop((0, 100, ss_w, ss_h)) 
        
        # Resize screenshot to fit into the inner frame (831 width)
        target_ss_w = 831 
        target_ss_h = int((ss.size[1] / ss.size[0]) * target_ss_w)
        ss = ss.resize((target_ss_w, target_ss_h), Image.Resampling.LANCZOS)
        
        # Add rounded corners to top of screenshot (radius ~ 60px)
        ss = add_rounded_corners(ss, rad=60)

        # 4. Composite
        template_x = 0
        template_y = 480 
        
        canvas.paste(template, (template_x, template_y), template)
        
        ss_x = 134
        ss_y = template_y + 33
        
        canvas.paste(ss, (ss_x, ss_y), ss)

    # 5. Text
    try:
        # Use Bold font for Header, larger size
        hook_font = ImageFont.truetype(font_path_bold, 48)
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

    # Layout params
    MAX_TEXT_WIDTH = CANVAS_WIDTH - 160  # 80px padding on each side
    TOP_MARGIN = 80
    LINE_SPACING_SUB = 50
    HOOK_SUB_GAP = 30

    # Wrap texts
    hook_lines = wrap_text(hook, hook_font, MAX_TEXT_WIDTH)
    sub_lines = wrap_text(sub, sub_font, MAX_TEXT_WIDTH)

    # Calculate starting Y to be somewhat centered in the top area (0 to 480)
    # Total text height
    LINE_HEIGHT_HOOK = 60
    hook_h = len(hook_lines) * LINE_HEIGHT_HOOK
    sub_h = len(sub_lines) * LINE_SPACING_SUB
    total_text_h = hook_h + HOOK_SUB_GAP + sub_h
    
    # Start Y such that the text block is centered in the upper 480px region
    current_y = (480 - total_text_h) // 2
    if current_y < 40: current_y = 40 # Minimum top margin

    # Draw Hook
    for line in hook_lines:
        draw_text_centered(line, hook_font, current_y, (255, 255, 255))
        current_y += 60

    current_y += HOOK_SUB_GAP

    # Draw Sub
    for line in sub_lines:
        draw_text_centered(line, sub_font, current_y, (180, 180, 180))
        current_y += LINE_SPACING_SUB

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
