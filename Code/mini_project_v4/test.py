import paho.mqtt.client as mqtt
import json
import threading
import time

# === Config ===
MQTT_BROKER = "localhost"
MQTT_PORT = 4001

VEHICLE_ID = 3
MQTT_TOPIC_INSTRUCTION = f"vehicle{VEHICLE_ID}_next_destination"
MQTT_TOPIC_UPDATE = f"vehicle{VEHICLE_ID}update"

# --- Synchronization ---
message_ack = threading.Event()
vehicle_progress = None  # None means no update received yet

# --- MQTT callbacks ---
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"✅ Connected to broker at {MQTT_BROKER}:{MQTT_PORT}")
        client.subscribe(MQTT_TOPIC_UPDATE)
        print(f"📡 Subscribed to {MQTT_TOPIC_UPDATE}")
    else:
        print(f"❌ Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    global vehicle_progress
    payload = msg.payload.decode()
    try:
        data = json.loads(payload)
        # Returns 0 if no value is found in progress
        vehicle_progress = data.get('progress', 0)
        print(f"\n📨 Update from {msg.topic}: progress={vehicle_progress}, "
              f"next_location={data.get('next_location')}, "
              f"previous_location={data.get('previous_location')}, "
              f"x={data.get('x_coordinate')}, y={data.get('y_coordinate')}")

        # Set the event if vehicle is idle
        if vehicle_progress == 100:
            message_ack.set()
        else:
            message_ack.clear()

    except json.JSONDecodeError:
        print(f"⚠️ Received non-JSON message: {payload}")

# --- MQTT setup ---
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_start()

# --- Main loop: send instructions ---
try:
    first_instruction_sent = False
    while True:
        next_node = "Node4"  # can be randomized or dynamically generated
        json_message = json.dumps(next_node)

        # Send the first instruction immediately
        if not first_instruction_sent:
            client.publish(MQTT_TOPIC_INSTRUCTION, json_message)
            print(f"📤 First instruction sent to {MQTT_TOPIC_INSTRUCTION}: {json_message}")
            first_instruction_sent = True
            message_ack.clear()  # wait for vehicle to move and become idle again
        else:
            # Wait until vehicle is idle
            print("⏳ Waiting for vehicle to become idle...")
            while not message_ack.wait(timeout=0.5):
                pass

            # Vehicle is idle, send next instruction
            client.publish(MQTT_TOPIC_INSTRUCTION, json_message)
            print(f"📤 Published instruction to {MQTT_TOPIC_INSTRUCTION}: {json_message}")
            message_ack.clear()

except KeyboardInterrupt:
    print("\n👋 Disconnecting...")
    client.loop_stop()
    client.disconnect()
