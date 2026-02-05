import paho.mqtt.client as mqtt
import json
import math
from collections import defaultdict
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, sessionmaker

# Database setup
DATABASE_URL = "postgresql://iot_user:PASSWORD@localhost/iot_project"
Base = declarative_base()
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

class TrainingData(Base):
    __tablename__ = 'training_data'
    id = Column(Integer, primary_key=True)
    location_label = Column(String)
    mac_address = Column(String)
    rssi = Column(Integer)
    ssid = Column(String)
    timestamp = Column(Float)

def load_training_data():
    """Loads and restructures DB rows into fingerprint vectors."""
    session = Session()
    raw_data = session.query(TrainingData).all()
    
    # Group raw rows by timestamp to reconstruct snapshots
    grouped_data = defaultdict(list)
    for row in raw_data:
        grouped_data[row.timestamp].append(row)

    fingerprints = []
    for timestamp, rows in grouped_data.items():
        scan_dict = {row.mac_address: row.rssi for row in rows}
        label = rows[0].location_label
        fingerprints.append({'label': label, 'data': scan_dict})
    
    return fingerprints

def get_distance(live_scan, stored_scan):
    """Calculates Euclidean distance with penalties for missing APs."""
    all_macs = set(live_scan.keys()) | set(stored_scan.keys())
    dist_sq = 0
    
    for mac in all_macs:
        rssi_live = live_scan.get(mac, -100)
        rssi_stored = stored_scan.get(mac, -100)
        dist_sq += (rssi_live - rssi_stored) ** 2
        
    return math.sqrt(dist_sq)

def predict_location(live_scan, k=5):
    """Weighted KNN implementation."""
    distances = []
    
    for fp in training_data:
        d = get_distance(live_scan, fp['data'])
        distances.append((d, fp['label']))
        
    distances.sort(key=lambda x: x[0])
    neighbors = distances[:k]
    
    # Inverse distance weighting
    scores = defaultdict(float)
    for dist, label in neighbors:
        weight = 1 / (dist + 0.1) 
        scores[label] += weight
        
    return max(scores, key=scores.get)

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        live_scan_list = payload.get("scans", [])
        
        # Convert list to dict for O(1) lookups
        live_scan = {item['mac']: item['rssi'] for item in live_scan_list}
        
        if not live_scan:
            return

        estimated_location = predict_location(live_scan)
        print(f"Detected Location: {estimated_location}")
        
        # Write to shared file for frontend
        with open("current_location.txt", "w") as f:
            f.write(estimated_location)
            
    except Exception as e:
        print(f"Error: {e}")

# Initialization
training_data = load_training_data()
print("Training data loaded. Starting inference engine...")

client = mqtt.Client()
client.on_message = on_message
client.connect("broker.hivemq.com", 1883, 60)
client.subscribe("mahdi/iot/scan")
client.loop_forever()
