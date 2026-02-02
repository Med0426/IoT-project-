import json
import math
import paho.mqtt.client as mqtt
from sqlalchemy import create_engine, text
from collections import Counter, defaultdict  # <--- FIXED: Added defaultdict here

# --- CONFIGURATION ---
DATABASE_URL = "postgresql://iot_user:password@localhost/iot_project" # UPDATE PASSWORD
MQTT_BROKER = "broker.hivemq.com"
MQTT_TOPIC = "mahdi/iot/scan"

# --- KNN SETTINGS ---
K_NEIGHBORS = 5           # Look at the 5 closest matches
RSSI_THRESHOLD = -85      # Ignore very weak signals
PENALTY = 1000            # Penalty for missing MAC addresses

# --- 1. LOAD ALL TRAINING DATA ---
print("Loading raw training data...")
engine = create_engine(DATABASE_URL)
connection = engine.connect()

result = connection.execute(text("SELECT location_label, mac_address, rssi, created_at FROM training_data"))
rows = result.fetchall()

# Reconstruct individual scans
training_points = []
temp_scans = {}

for label, mac, rssi, timestamp in rows:
    key = str(timestamp)
    if key not in temp_scans:
        temp_scans[key] = {'label': label, 'data': {}}
    temp_scans[key]['data'][mac] = rssi

training_points = list(temp_scans.values())
print(f"✅ Brain Loaded! Stored {len(training_points)} distinct reference points.")

# --- 2. MATH: EUCLIDEAN DISTANCE ---
def get_distance(live_scan, stored_scan):
    error = 0
    matches = 0
    
    for mac, stored_rssi in stored_scan.items():
        if mac in live_scan:
            live_rssi = live_scan[mac]
            if live_rssi < RSSI_THRESHOLD: continue 
            
            diff = (live_rssi - stored_rssi) ** 2
            error += diff
            matches += 1
        else:
            error += PENALTY 
            
    if matches == 0: return float('inf')
    return math.sqrt(error)

# --- 3. WEIGHTED KNN ALGORITHM ---
def predict_location(live_scan_data):
    # Calculate distance to EVERY point
    distances = []
    for point in training_points:
        dist = get_distance(live_scan_data, point['data'])
        if dist == 0: dist = 0.001 # Prevent division by zero
        distances.append( (dist, point['label']) )
    
    # Sort and pick Top K
    distances.sort(key=lambda x: x[0])
    neighbors = distances[:K_NEIGHBORS]
    
    # WEIGHTED VOTING (Inverse Distance)
    vote_scores = defaultdict(float) # <--- This caused your error before
    
    for dist, label in neighbors:
        weight = 1.0 / dist
        vote_scores[label] += weight
    
    # Find winner
    winner = max(vote_scores, key=vote_scores.get)
    
    # Calculate confidence
    raw_votes = [n[1] for n in neighbors]
    vote_count = raw_votes.count(winner)
    confidence = int((vote_count / K_NEIGHBORS) * 100)
    
    return winner, confidence, neighbors

# --- 4. MQTT LISTENER ---
def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        data = json.loads(payload)
        if "scans" not in data: return

        live_scan = {item["mac"]: item["rssi"] for item in data["scans"]}
        
        winner, confidence, top_k = predict_location(live_scan)
        
        # Check for uncertainty
        best_dist = top_k[0][0]
        if best_dist > 20.0:
            print(f"❓ UNCERTAIN (Distance: {best_dist:.1f}) - Neighbors: {[n[1] for n in top_k]}")
        else:
            print("-" * 40)
            print(f"📍 LOCATION: >> {winner} << ({confidence}% Confidence)")
            print(f"   (Neighbors: { [n[1] for n in top_k] })")
            print("-" * 40)

    except Exception as e:
        print(f"Error: {e}")

# --- START ---
print("Waiting for ESP32 data...")
# Fix for DeprecationWarning: explicitly use version 2
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = lambda c, u, f, rc, props: c.subscribe(MQTT_TOPIC)
client.on_message = on_message
client.connect(MQTT_BROKER, 1883, 60)
client.loop_forever()
