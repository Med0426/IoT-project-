import json
import paho.mqtt.client as mqtt
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# --- CONFIGURATION ---
# REMEMBER: Replace 'your_password' with the real password!
DATABASE_URL = "postgresql://iot_user:password@localhost/iot_project"
MQTT_BROKER = "broker.hivemq.com"
MQTT_TOPIC = "mahdi/iot/scan"

# --- DATABASE SETUP ---
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class WiFiScanDB(Base):
    __tablename__ = "wifi_scans"
    id = Column(Integer, primary_key=True, index=True)
    mac_address = Column(String)
    rssi = Column(Integer)
    ssid = Column(String)
    created_at = Column(DateTime, default=datetime.now)

# Create tables
Base.metadata.create_all(bind=engine)

# --- MQTT CALLBACKS ---
def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT Broker! (Code: {rc})")
    client.subscribe(MQTT_TOPIC)
    print(f"Listening for data on: {MQTT_TOPIC}")

def on_message(client, userdata, msg):
    try:
        print("\n[!] New Message Received!")
        payload = msg.payload.decode()
        data = json.loads(payload)
        
        db = SessionLocal()
        count = 0
        
        # Check if valid format
        if "scans" in data:
            for item in data["scans"]:
                new_entry = WiFiScanDB(
                    mac_address=item["mac"],
                    rssi=item["rssi"],
                    ssid=item["ssid"]
                )
                db.add(new_entry)
                count += 1
            
            db.commit()
            print(f" -> SUCCESS: Saved {count} WiFi networks to Database.")
        else:
            print(" -> Error: JSON format incorrect.")
            
        db.close()
        
    except Exception as e:
        print(f" -> ERROR processing data: {e}")

# --- START LISTENER ---
if __name__ == "__main__":
    print("--- IoT Listener Starting ---")
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, 1883, 60)
    
    # Run forever
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("\nStopping...")
