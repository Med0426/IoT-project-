import streamlit as st
import time
import base64
import datetime
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

# Room layout configuration (x, y coordinates in %)
ROOM_COORDS = {
    "KITCHEN":  {"x": 25, "y": 25},
    "DESK":     {"x": 75, "y": 25},
    "BEDROOM":  {"x": 25, "y": 75},
    "BATHROOM": {"x": 75, "y": 75},
    "UNKNOWN":  {"x": 50, "y": 50}
}

def render_blueprint(active_room):
    """Generates the floor plan image using PIL."""
    W, H = 800, 600
    bg_color = "#1e293b"
    grid_color = "#334155"
    wall_color = "#94a3b8"
    
    img = Image.new('RGB', (W, H), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # Draw grid
    step = 40
    for x in range(0, W, step):
        draw.line([(x, 0), (x, H)], fill=grid_color, width=1)
    for y in range(0, H, step):
        draw.line([(0, y), (W, y)], fill=grid_color, width=1)

    # Highlight active zone
    if active_room in ROOM_COORDS and active_room != "UNKNOWN":
        rc = ROOM_COORDS[active_room]
        cx, cy = rc['x'] * (W/100), rc['y'] * (H/100)
        draw.rectangle([cx-150, cy-120, cx+150, cy+120], fill="#1e3a8a", outline=None)

    # Draw walls
    draw.rectangle([50, 50, 750, 550], outline=wall_color, width=3)
    draw.line([400, 50, 400, 550], fill=wall_color, width=3)
    draw.line([50, 300, 750, 300], fill=wall_color, width=3)
    
    # Draw doors
    draw.line([370, 300, 430, 300], fill=bg_color, width=5)
    draw.line([400, 270, 400, 330], fill=bg_color, width=5)
    
    # Labels
    try:
        font = ImageFont.truetype("arial.ttf", 30)
    except:
        font = ImageFont.load_default()
    
    text_color = "#64748b"
    draw.text((100, 80), "KITCHEN", fill=text_color, font=font)
    draw.text((550, 80), "DESK",    fill=text_color, font=font)
    draw.text((100, 480), "BEDROOM", fill=text_color, font=font)
    draw.text((550, 480), "BATHROOM", fill=text_color, font=font)
    
    return img

def render_marker():
    """Draws the tracking marker."""
    size = 120
    img = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # Marker styling
    draw.ellipse([30, 30, 90, 90], fill=(59, 130, 246, 100))
    draw.ellipse([40, 40, 80, 80], fill="white", outline=None)
    draw.ellipse([50, 55, 55, 60], fill="#333")
    draw.ellipse([65, 55, 70, 60], fill="#333")
    
    return img

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

# Page setup
st.set_page_config(page_title="IoT Localizer", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0f172a; }
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
    .map-container {
        position: relative;
        width: 100%;
        max-width: 900px;
        margin: auto;
        border: 1px solid #334155;
        border-radius: 8px;
        overflow: hidden;
    }
    .base-map { width: 100%; display: block; }
    .marker {
        position: absolute;
        width: 80px;
        height: auto;
        transform: translate(-50%, -50%);
        transition: all 1.0s cubic-bezier(0.34, 1.56, 0.64, 1);
        z-index: 50;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("System Status")
    loc = get_current_location()
    
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Location</div>
        <div class="metric-value">{loc}</div>
    </div>
    <div class="metric-card" style="border-left-color: #10b981;">
        <div class="metric-label">Status</div>
        <div class="metric-value">ONLINE</div>
    </div>
    <div class="metric-card" style="border-left-color: #f59e0b;">
        <div class="metric-label">Last Update</div>
        <div class="metric-value">{datetime.datetime.now().strftime("%H:%M:%S")}</div>
    </div>
    """, unsafe_allow_html=True)

# Main layout
st.title("IoT Real-Time Localizer")

# Generate assets
floor_plan = render_blueprint(loc) 
marker = render_marker()

map_b64 = img_to_b64(floor_plan)
marker_b64 = img_to_b64(marker)

pos = ROOM_COORDS.get(loc, ROOM_COORDS["UNKNOWN"])

# Render map
html_map = f"""
<div class="map-container">
    <img src="data:image/png;base64,{map_b64}" class="base-map">
    <img src="data:image/png;base64,{marker_b64}" 
         class="marker" 
         style="left: {pos['x']}%; top: {pos['y']}%;">
</div>
"""

st.markdown(html_map, unsafe_allow_html=True)

time.sleep(1)
st.rerun()
