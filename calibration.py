import json
import paho.mqtt.client as mqtt
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
import time

# --- CONFIGURATION ---
# REPLACE 'your_password' with your real DB password!
DATABASE_URL = "postgresql://iot_user:password@localhost/iot_project"
MQTT_BROKER = "broker.hivemq.com"
MQTT_TOPIC = "mahdi/iot/scan"

# --- DATABASE SETUP (New Table for Training) ---
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# We create a specific table for LABELED data
class TrainingData(Base):
    __tablename__ = "training_data"
    id = Column(Integer, primary_key=True, index=True)
    location_label = Column(String, nullable=False) # e.g. "Kitchen"
    mac_address = Column(String, nullable=False)
    rssi = Column(Integer, nullable=False)
    ssid = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

# Create the table immediately
Base.metadata.create_all(bind=engine)

# --- GLOBAL VARIABLES ---
target_location = ""
samples_collected = 0
SAMPLES_NEEDED = 40  # How many ESP32 scans we want to capture per room

def on_connect(client, userdata, flags, rc):
    print(f" -> Connected to Cloud (Pulse: {rc})")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    global samples_collected
    
    try:
        payload = msg.payload.decode()
        data = json.loads(payload)
        
        if "scans" in data:
            db = SessionLocal()
            count = 0
            
            # Save every WiFi network in this scan with the label
            for item in data["scans"]:
                new_entry = TrainingData(
                    location_label=target_location,
                    mac_address=item["mac"],
                    rssi=item["rssi"],
                    ssid=item["ssid"]
                )
                db.add(new_entry)
                count += 1
            
            db.commit()
            db.close()
            
            samples_collected += 1
            print(f" [Sample {samples_collected}/{SAMPLES_NEEDED}] Saved {count} networks for '{target_location}'")
            
            if samples_collected >= SAMPLES_NEEDED:
                print(f"\n✅ CALIBRATION COMPLETE for {target_location}!")
                client.disconnect()

    except Exception as e:
        print(f"Error: {e}")

# --- MAIN INTERACTIVE LOOP ---
if __name__ == "__main__":
    print("\n--- IOT LOCATION CALIBRATION ---")
    
    # 1. Ask the user where they are
    target_location = input("ENTER LOCATION NAME (e.g., Kitchen, Desk): ").strip().upper()
    
    if not target_location:
        print("Error: You must enter a name.")
        exit()

    print(f"\n[INSTRUCTION] Please stand in the {target_location} with your ESP32.")
    print("Collecting data... (Wait ~30 seconds)")

    # 2. Start Listening
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, 1883, 60)
    client.loop_forever()
