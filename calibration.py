import paho.mqtt.client as mqtt
import json
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, sessionmaker

# Database configuration
DATABASE_URL = "postgresql://iot_user:PASSWORD@localhost/iot_project"
Base = declarative_base()
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
db = Session()

# Define table structure
class TrainingData(Base):
    __tablename__ = 'training_data'
    id = Column(Integer, primary_key=True)
    location_label = Column(String)
    mac_address = Column(String)
    rssi = Column(Integer)
    ssid = Column(String)
    timestamp = Column(Float)

# Initialize database
Base.metadata.create_all(engine)

# User settings
TARGET_LOCATION = input("Enter location label (e.g., KITCHEN): ").upper()
SAMPLES_NEEDED = 40
samples_collected = 0

def on_message(client, userdata, msg):
    global samples_collected
    
    if samples_collected >= SAMPLES_NEEDED:
        print(f"Collection complete for {TARGET_LOCATION}.")
        client.disconnect()
        return

    try:
        payload = json.loads(msg.payload.decode())
        scans = payload.get("scans", [])

        if not scans:
            return

        # Use a single timestamp for the batch
        current_time = 12345.67 
        
        print(f"Saving sample {samples_collected + 1}/{SAMPLES_NEEDED}...")

        # Batch insert
        for network in scans:
            new_data = TrainingData(
                location_label=TARGET_LOCATION,
                mac_address=network['mac'],
                rssi=network['rssi'],
                ssid=network.get('ssid', 'HIDDEN'),
                timestamp=current_time
            )
            db.add(new_data)
        
        db.commit()
        samples_collected += 1

    except Exception as e:
        print(f"Error processing message: {e}")

# MQTT setup
client = mqtt.Client()
client.on_message = on_message
client.connect("broker.hivemq.com", 1883, 60)
client.subscribe("mahdi/iot/scan")

print(f"Listening for data. Target: {TARGET_LOCATION}...")
client.loop_forever()
