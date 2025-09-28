import paho.mqtt.client as mqtt
import json
import threading
import time
import random

# === Config ===
MQTT_BROKER = "localhost"
MQTT_PORT = 4001
NUM_VEHICLES = 5

# MQTT topics per vehicle
MQTT_TOPIC_INSTRUCTION = {i: f"vehicle{i}_next_destination" for i in range(1, NUM_VEHICLES+1)}
MQTT_TOPIC_UPDATE = {i: f"vehicle{i}update" for i in range(1, NUM_VEHICLES+1)}

# --- Vehicle state ---
vehicle_status = {
    i: {
        "progress": 0,
        "current_node": 1,
        "target_node": None,   # The node vehicle is currently assigned to
        "busy": False          # True when vehicle has a target and is en route
    }
    for i in range(1, NUM_VEHICLES+1)
}
vehicle_lock = threading.Lock()

# --- MQTT callbacks ---
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"✅ Connected to broker at {MQTT_BROKER}:{MQTT_PORT}")
        for i in range(1, NUM_VEHICLES+1):
            client.subscribe(MQTT_TOPIC_UPDATE[i])
            print(f"📡 Subscribed to {MQTT_TOPIC_UPDATE[i]}")
    else:
        print(f"❌ Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    try:
        data = json.loads(payload)
        vehicle_id = int(msg.topic.replace("vehicle", "").replace("update", ""))

        with vehicle_lock:
            vehicle_status[vehicle_id]["progress"] = data.get("progress", 0)
            vehicle_status[vehicle_id]["current_node"] = data.get(
                "current_node", vehicle_status[vehicle_id]["current_node"]
            )
            vehicle_status[vehicle_id]["next_location"] = data.get("next_location", None)

        # Print vehicle updates
        print(f"\n📨 Vehicle {vehicle_id} update: "
              f"progress={vehicle_status[vehicle_id]['progress']}, "
              f"current_node={vehicle_status[vehicle_id]['current_node']}, "
              f"next_location={vehicle_status[vehicle_id]['next_location']}, "
              f"previous_location={data.get('previous_location')}, "
              f"x={data.get('x_coordinate')}, y={data.get('y_coordinate')}")

    except json.JSONDecodeError:
        print(f"⚠️ Received non-JSON message: {payload}")

# --- MQTT setup ---
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_start()

# --- Function to assign vehicle ---
def assign_vehicle(vehicle_id):
    next_node = f"Node{random.randint(2,6)}"
    client.publish(MQTT_TOPIC_INSTRUCTION[vehicle_id], json.dumps(next_node))
    print(f"📤 Assigned Vehicle {vehicle_id} to {next_node}")
    with vehicle_lock:
        vehicle_status[vehicle_id]["target_node"] = next_node
        vehicle_status[vehicle_id]["busy"] = True

# --- Main loop ---
try:
    while True:
        for vehicle_id in range(1, NUM_VEHICLES+1):
            with vehicle_lock:
                status = vehicle_status[vehicle_id]
                progress = status["progress"]
                current_node = status["current_node"]
                next_location = status.get("next_location")
                busy = status["busy"]
                target_node = status["target_node"]

            # 1) Vehicle has no target or just started → assign initial delivery
            if not busy and progress == 0:
                assign_vehicle(vehicle_id)

            # 2) Delivery completed, not Node1 → send back to Node1
            elif busy and progress == 100 and next_location not in ("Node1", None):
                client.publish(MQTT_TOPIC_INSTRUCTION[vehicle_id], json.dumps("Node1"))
                print(f"📤 Vehicle {vehicle_id} completed delivery to {next_location}, returning to Node 1")
                with vehicle_lock:
                    status["target_node"] = "Node1"

            # 3) Vehicle arrived at Node1 → assign new delivery
            elif busy and progress == 100 and current_node == 1:
                assign_vehicle(vehicle_id)

            # 4) Else: just monitor updates
            else:
                pass

        time.sleep(1)

except KeyboardInterrupt:
    print("\n👋 Disconnecting...")
    client.loop_stop()
    client.disconnect()
