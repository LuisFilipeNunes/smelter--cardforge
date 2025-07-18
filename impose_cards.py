import os
from PIL import Image, ImageDraw
import math
import xml.etree.ElementTree as ET
from xml.dom import minidom

def mm_to_pixels(mm, dpi=300):
    """Convert millimeters to pixels"""
    return int(mm * dpi / 25.4)

def setup_dimensions():
    """Set up paper and card dimensions"""
    # Using A3+ paper (329x483mm) - good for card printing
    paper_w_mm = 329
    paper_h_mm = 483
    
    # Standard card game size
    card_w_mm = 63
    card_h_mm = 88
    bleed_mm = 4  # Extra space around cards for cutting
    
    # Card size including bleed
    card_bleed_w_mm = card_w_mm + (2 * bleed_mm)
    card_bleed_h_mm = card_h_mm + (2 * bleed_mm)
    
    # Convert everything to pixels (300 DPI)
    dpi = 300
    paper_w = mm_to_pixels(paper_w_mm, dpi)
    paper_h = mm_to_pixels(paper_h_mm, dpi)
    card_w = mm_to_pixels(card_w_mm, dpi)
    card_h = mm_to_pixels(card_h_mm, dpi)
    card_bleed_w = mm_to_pixels(card_bleed_w_mm, dpi)
    card_bleed_h = mm_to_pixels(card_bleed_h_mm, dpi)
    bleed_px = mm_to_pixels(bleed_mm, dpi)
    
    # Layout: 4 across, 5 down (fits nicely on A3+)
    cols = 4
    rows = 5
    cards_per_sheet = cols * rows
    
    # Check if everything fits
    needed_w = cols * card_bleed_w_mm
    needed_h = rows * card_bleed_h_mm
    
    print(f"Paper: A3+ ({paper_w_mm}x{paper_h_mm}mm)")
    print(f"Cards: {card_w_mm}x{card_h_mm}mm + {bleed_mm}mm bleed")
    print(f"Layout: {cols}x{rows} = {cards_per_sheet} cards")
    print(f"Space used: {needed_w}x{needed_h}mm")
    
    if needed_w > paper_w_mm or needed_h > paper_h_mm:
        print("WARNING: Cards might not fit!")
    
    return {
        'paper_w': paper_w, 'paper_h': paper_h,
        'card_w': card_w, 'card_h': card_h,
        'card_bleed_w': card_bleed_w, 'card_bleed_h': card_bleed_h,
        'bleed_px': bleed_px, 'cols': cols, 'rows': rows,
        'cards_per_sheet': cards_per_sheet, 'dpi': dpi,
        'paper_w_mm': paper_w_mm, 'paper_h_mm': paper_h_mm,
        'card_w_mm': card_w_mm, 'card_h_mm': card_h_mm,
        'card_bleed_w_mm': card_bleed_w_mm, 'card_bleed_h_mm': card_bleed_h_mm,
        'bleed_mm': bleed_mm
    }

def find_normal_cards():
    """Find cards that use the standard backface"""
    backface = "backface.jpg"
    
    if not os.path.exists(backface):
        print(f"Can't find {backface}!")
        return []
    
    cards = []
    normal_folder = "normal"
    
    if os.path.exists(normal_folder):
        for file in os.listdir(normal_folder):
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                front = os.path.join(normal_folder, file)
                cards.append((front, backface))
    
    return cards

def find_double_cards():
    """Find double-faced cards (different front/back)"""
    cards = []
    double_folder = "double"
    
    if not os.path.exists(double_folder):
        return cards
    
    for subfolder in os.listdir(double_folder):
        subfolder_path = os.path.join(double_folder, subfolder)
        if not os.path.isdir(subfolder_path):
            continue
            
        images = []
        for file in os.listdir(subfolder_path):
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                images.append(os.path.join(subfolder_path, file))
        
        # Pair up images (front/back)
        for i in range(0, len(images) - 1, 2):
            cards.append((images[i], images[i + 1]))
    
    return cards

def prepare_card_image(image_path, card_w, card_h, bleed_px):
    """Load and prepare a card image with bleed"""
    try:
        img = Image.open(image_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Resize to fit card exactly
        scale_w = card_w / img.width
        scale_h = card_h / img.height
        scale = max(scale_w, scale_h)  # Scale to fill completely
        
        new_w = int(img.width * scale)
        new_h = int(img.height * scale)
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        # Crop to exact card size
        left = (new_w - card_w) // 2
        top = (new_h - card_h) // 2
        card_img = img.crop((left, top, left + card_w, top + card_h))
        
        # Add black bleed border
        final_w = card_w + (2 * bleed_px)
        final_h = card_h + (2 * bleed_px)
        final_img = Image.new('RGB', (final_w, final_h), 'black')
        final_img.paste(card_img, (bleed_px, bleed_px))
        
        return final_img
        
    except Exception as e:
        print(f"Problem with {image_path}: {e}")
        # Make a blank card if something goes wrong
        final_w = card_w + (2 * bleed_px)
        final_h = card_h + (2 * bleed_px)
        blank = Image.new('RGB', (final_w, final_h), 'black')
        white_card = Image.new('RGB', (card_w, card_h), 'white')
        blank.paste(white_card, (bleed_px, bleed_px))
        return blank

def make_cutting_file(output_dir, sheet_num, dims):
    """Create JDF file for cutting machine"""
    d = dims  # shorthand
    
    # Calculate card positions
    total_w = d['cols'] * d['card_bleed_w_mm']
    total_h = d['rows'] * d['card_bleed_h_mm']
    
    # Center everything on the page
    offset_x = (d['paper_w_mm'] - total_w) / 2
    offset_y = (d['paper_h_mm'] - total_h) / 2
    
    # Build JDF structure
    jdf = ET.Element("JDF", {
        "Type": "ProcessGroup",
        "Types": "Cutting", 
        "ID": f"Sheet_{sheet_num + 1:02d}_Cutting",
        "Status": "Waiting",
        "Version": "1.3"
    })
    
    resource_pool = ET.SubElement(jdf, "ResourcePool")
    
    # Paper info
    media = ET.SubElement(resource_pool, "Media", {
        "ID": "Media_001",
        "Class": "Consumable", 
        "Status": "Available",
        "MediaType": "Paper",
        "Dimension": f"{d['paper_w_mm']} {d['paper_h_mm']}",
        "Unit": "mm"
    })
    
    # Cutting settings
    cutting_params = ET.SubElement(resource_pool, "CuttingParams", {
        "ID": "CuttingParams_001",
        "Class": "Parameter",
        "Status": "Available"
    })
    
    cut_block = ET.SubElement(cutting_params, "CutBlock", {
        "BlockName": "CardSheet",
        "TrimSize": f"{d['paper_w_mm']} {d['paper_h_mm']}",
        "Unit": "mm"
    })
    
    # Add cut marks for each card
    for row in range(d['rows']):
        for col in range(d['cols']):
            card_x = offset_x + (col * d['card_bleed_w_mm']) + d['bleed_mm']
            card_y = offset_y + (row * d['card_bleed_h_mm']) + d['bleed_mm']
            
            cut_mark = ET.SubElement(cut_block, "CutMark", {
                "MarkType": "CutContour",
                "Center": f"{card_x + d['card_w_mm']/2} {card_y + d['card_h_mm']/2}",
                "Size": f"{d['card_w_mm']} {d['card_h_mm']}",
                "Unit": "mm"
            })
            
            cut_path = ET.SubElement(cut_mark, "CutPath")
            rect_path = ET.SubElement(cut_path, "Rectangle", {
                "LLx": str(card_x),
                "LLy": str(card_y), 
                "URx": str(card_x + d['card_w_mm']),
                "URy": str(card_y + d['card_h_mm']),
                "Unit": "mm"
            })
    
    # Add metadata
    node_info = ET.SubElement(jdf, "NodeInfo", {
        "NodeStatus": "Waiting",
        "Start": "2025-07-17T12:00:00",
        "End": "2025-07-17T12:30:00"
    })
    
    resource_link_pool = ET.SubElement(jdf, "ResourceLinkPool")
    
    media_link = ET.SubElement(resource_link_pool, "MediaLink", {
        "Usage": "Input",
        "rRef": "Media_001"
    })
    
    cutting_link = ET.SubElement(resource_link_pool, "CuttingParamsLink", {
        "Usage": "Input", 
        "rRef": "CuttingParams_001"
    })
    
    # Save the file
    rough_string = ET.tostring(jdf, 'unicode')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")
    pretty_xml = '\n'.join([line for line in pretty_xml.split('\n') if line.strip()])
    
    jdf_file = os.path.join(output_dir, f"sheet_{sheet_num + 1:02d}_cutting.jdf")
    with open(jdf_file, 'w', encoding='utf-8') as f:
        f.write(pretty_xml)
    
    return jdf_file

def build_sheet(card_pairs, sheet_num, dims, is_back=False):
    """Build one sheet of cards"""
    d = dims  # shorthand
    
    # White background
    sheet = Image.new('RGB', (d['paper_w'], d['paper_h']), 'white')
    
    # Figure out which cards go on this sheet
    start_idx = sheet_num * d['cards_per_sheet']
    end_idx = min(start_idx + d['cards_per_sheet'], len(card_pairs))
    
    # Center the card grid
    total_w = d['cols'] * d['card_bleed_w']
    total_h = d['rows'] * d['card_bleed_h']
    offset_x = (d['paper_w'] - total_w) // 2
    offset_y = (d['paper_h'] - total_h) // 2
    
    for i in range(start_idx, end_idx):
        card_pos = i - start_idx
        row = card_pos // d['cols']
        col = card_pos % d['cols']
        
        # For back sheets, flip horizontally for double-sided printing
        if is_back:
            col = d['cols'] - 1 - col
        
        # Position on sheet
        x = offset_x + (col * d['card_bleed_w'])
        y = offset_y + (row * d['card_bleed_h'])
        
        # Get the right image (front or back)
        image_path = card_pairs[i][1 if is_back else 0]
        card_img = prepare_card_image(image_path, d['card_w'], d['card_h'], d['bleed_px'])
        
        # Place card on sheet
        sheet.paste(card_img, (x, y))
        
        # Add a blue border for reference
        draw = ImageDraw.Draw(sheet)
        draw.rectangle([x, y, x + d['card_bleed_w'] - 1, y + d['card_bleed_h'] - 1], 
                      outline='blue', width=1)
    
    return sheet

def main():
    dims = setup_dimensions()
    
    print("Looking for cards...")
    normal_cards = find_normal_cards()
    double_cards = find_double_cards()
    
    print(f"Found {len(normal_cards)} normal cards")
    print(f"Found {len(double_cards)} double-faced cards")
    
    all_cards = normal_cards + double_cards
    total = len(all_cards)
    
    if total == 0:
        print("No cards found! Check your folders.")
        return
    
    print(f"Total: {total} cards")
    
    num_sheets = math.ceil(total / dims['cards_per_sheet'])
    print(f"Will need {num_sheets} sheets")
    
    # Make output folder
    output_dir = "output_sheets"
    os.makedirs(output_dir, exist_ok=True)
    
    # Create each sheet
    for sheet_num in range(num_sheets):
        print(f"Making sheet {sheet_num + 1}...")
        
        # Front and back
        front = build_sheet(all_cards, sheet_num, dims, is_back=False)
        back = build_sheet(all_cards, sheet_num, dims, is_back=True)
        
        # Save as PDF
        pdf_file = os.path.join(output_dir, f"sheet_{sheet_num + 1:02d}.pdf")
        
        front = front.convert('RGB')
        back = back.convert('RGB')
        
        front.save(pdf_file, format='PDF', save_all=True, 
                  append_images=[back], resolution=dims['dpi'])
        
        # Make cutting file
        jdf_file = make_cutting_file(output_dir, sheet_num, dims)
        
        print(f"  Saved: {os.path.basename(pdf_file)}")
        print(f"  Saved: {os.path.basename(jdf_file)}")
    
    print(f"\nAll done! Check the '{output_dir}' folder.")
    print("\nTo print: Print page 1, flip the paper, print page 2")
    print("Blue lines show division between cards!")

if __name__ == "__main__":
    main()