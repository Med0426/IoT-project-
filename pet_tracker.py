import streamlit as st
import time
import base64
import datetime
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

# --- 1. CONFIGURATION ---
ROOM_COORDS = {
    "KITCHEN":  {"x": 25, "y": 25, "w": 350, "h": 250}, # x,y center & width/height for room
    "DESK":     {"x": 75, "y": 25, "w": 350, "h": 250},
    "BEDROOM":  {"x": 25, "y": 75, "w": 350, "h": 250},
    "BATHROOM": {"x": 75, "y": 75, "w": 350, "h": 250},
    "UNKNOWN":  {"x": 50, "y": 50, "w": 0,   "h": 0}
}

# --- 2. THE ARCHITECT (Professional Blueprint) ---
def draw_professional_blueprint(active_room):
    """Draws a CAD-style architectural blueprint."""
    # 1. Background: Dark Blueprint Blue
    W, H = 800, 600
    bg_color = "#1e293b" # Dark Slate Blue
    grid_color = "#334155" # Lighter Blue for grid
    wall_color = "#94a3b8" # Light Grey for walls
    active_fill = "#3b82f6" # Bright Blue highlight
    
    img = Image.new('RGB', (W, H), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # 2. Draw Grid (Engineering Paper Look)
    step = 40
    for x in range(0, W, step):
        draw.line([(x, 0), (x, H)], fill=grid_color, width=1)
    for y in range(0, H, step):
        draw.line([(0, y), (W, y)], fill=grid_color, width=1)

    # 3. Draw Room Highlights (If active)
    # If the user is in a room, we draw a subtle transparent rectangle there
    # (Since PIL doesn't do transparency on RGB easily, we just draw a solid faint rect)
    if active_room in ROOM_COORDS and active_room != "UNKNOWN":
        rc = ROOM_COORDS[active_room]
        # Calculate top-left and bottom-right based on % coordinates
        # Map 0-100% to pixels
        cx, cy = rc['x'] * (W/100), rc['y'] * (H/100)
        # Draw a "Zone" highlight
        draw.rectangle([cx-150, cy-120, cx+150, cy+120], fill="#1e3a8a", outline=None)

    # 4. Draw Architectural Walls (Double Lines)
    # Outer Box
    draw.rectangle([50, 50, 750, 550], outline=wall_color, width=3)
    draw.rectangle([60, 60, 740, 540], outline=wall_color, width=1) # Inner detail
    
    # Inner Walls
    draw.line([400, 50, 400, 550], fill=wall_color, width=3) # Vertical Split
    draw.line([50, 300, 750, 300], fill=wall_color, width=3) # Horizontal Split
    
    # Doors (Gaps)
    door_color = bg_color # "Erase" wall by drawing background color
    draw.line([370, 300, 430, 300], fill=door_color, width=5) # Top Door
    draw.line([400, 270, 400, 330], fill=door_color, width=5) # Bottom Door
    
    # 5. Room Labels
    try:
        font = ImageFont.truetype("arial.ttf", 30)
    except:
        font = ImageFont.load_default()
    
    text_color = "#64748b"
    draw.text((100, 80), "KITCHEN [Z1]", fill=text_color, font=font)
    draw.text((550, 80), "DESK [Z2]",    fill=text_color, font=font)
    draw.text((100, 480), "BEDROOM [Z3]", fill=text_color, font=font)
    draw.text((550, 480), "BATHROOM [Z4]", fill=text_color, font=font)
    
    return img

def draw_pet_avatar():
    """Draws a stylized 'Bot' or 'Pet' marker."""
    size = 120
    img = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # Glow Effect (Soft Circles)
    draw.ellipse([10, 10, 110, 110], fill=(59, 130, 246, 50)) # Outer Glow
    draw.ellipse([30, 30, 90, 90], fill=(59, 130, 246, 100))  # Inner Glow
    
    # The "Body" (White Circle)
    draw.ellipse([40, 40, 80, 80], fill="white", outline=None)
    
    # The "Face" (Cute Dog Details)
    # Ears
    draw.polygon([(40, 45), (30, 30), (50, 40)], fill="#333")
    draw.polygon([(80, 45), (90, 30), (70, 40)], fill="#333")
    # Eyes
    draw.ellipse([50, 55, 55, 60], fill="#333")
    draw.ellipse([65, 55, 70, 60], fill="#333")
    # Nose
    draw.ellipse([57, 63, 63, 66], fill="#e11d48")
    
    return img

# --- 3. HELPER FUNCTIONS ---
def img_to_b64(img):
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def get_current_location():
    try:
        with open("current_location.txt", "r") as f:
            return f.read().strip()
    except:
        return "UNKNOWN"

# --- 4. STREAMLIT APP CONFIG ---
st.set_page_config(page_title="IoT Smart Dashboard", page_icon="📡", layout="wide")

# Custom CSS for "Professional" Look
st.markdown("""
<style>
    /* Dark Theme Background */
    .stApp {
        background-color: #0f172a;
    }
    
    /* Metrics Cards in Sidebar */
    .metric-card {
        background-color: #1e293b;
        border-left: 5px solid #3b82f6;
        padding: 15px;
        margin-bottom: 10px;
        border-radius: 5px;
        color: white;
    }
    .metric-label { font-size: 12px; color: #94a3b8; text-transform: uppercase; }
    .metric-value { font-size: 24px; font-weight: bold; color: white; }
    
    /* Map Container */
    .blueprint-container {
        position: relative;
        width: 100%;
        max-width: 900px;
        margin: auto;
        border: 1px solid #334155;
        border-radius: 8px;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
        overflow: hidden;
    }
    
    /* The Map Image */
    .base-map { width: 100%; display: block; }
    
    /* The Pet/Marker */
    .pet-marker {
        position: absolute;
        width: 80px;
        height: auto;
        transform: translate(-50%, -50%);
        transition: all 1.2s cubic-bezier(0.34, 1.56, 0.64, 1); /* Elastic Bounce */
        z-index: 50;
    }
</style>
""", unsafe_allow_html=True)

# --- 5. MAIN LAYOUT ---

# Sidebar: System Stats
with st.sidebar:
    st.title("📡 System Status")
    
    loc = get_current_location()
    
    # Custom HTML Metrics
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Detected Zone</div>
        <div class="metric-value">{loc}</div>
    </div>
    <div class="metric-card" style="border-left-color: #10b981;">
        <div class="metric-label">System State</div>
        <div class="metric-value">ONLINE ●</div>
    </div>
    <div class="metric-card" style="border-left-color: #f59e0b;">
        <div class="metric-label">Last Update</div>
        <div class="metric-value">{datetime.datetime.now().strftime("%H:%M:%S")}</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.info("System uses KNN Algorithm with Inverse Distance Weighting.")

# Main Area: The Map
st.title("📍 IoT Real-Time Localizer")

# 1. Generate Assets
# We pass 'loc' to the blueprint drawer so it can highlight the active room!
floor_plan = draw_professional_blueprint(loc) 
pet_avatar = draw_pet_avatar()

# 2. Convert to B64
map_b64 = img_to_b64(floor_plan)
pet_b64 = img_to_b64(pet_avatar)

# 3. Get Coords
pos = ROOM_COORDS.get(loc, ROOM_COORDS["UNKNOWN"])

# 4. Render HTML Map
html_map = f"""
<div class="blueprint-container">
    <img src="data:image/png;base64,{map_b64}" class="base-map">
    <img src="data:image/png;base64,{pet_b64}" 
         class="pet-marker" 
         style="left: {pos['x']}%; top: {pos['y']}%;">
</div>
"""

st.markdown(html_map, unsafe_allow_html=True)

# Auto-refresh
time.sleep(1)
st.rerun()
