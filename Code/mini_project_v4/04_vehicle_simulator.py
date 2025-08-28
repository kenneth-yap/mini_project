import paho.mqtt.client as mqtt
import random
import json
import sys
import time

# Import vehicle number
vehicle_number = int(sys.argv[1]) if len(sys.argv) > 1 else 1

# === Config ===
BROKER = "localhost"
PORT = 1883

# Topics
request_topic = f"vehicle/{vehicle_number}/request_ranking"
ranking_topic = f"vehicle/{vehicle_number}/ranking"
assignment_topic = f"vehicle/{vehicle_number}/task_assignment"
response_topic = f"vehicle/{vehicle_number}/task_response"

print(f"[Simulator {vehicle_number}] Starting Vehicle Simulator")
print(f"[Simulator {vehicle_number}] Topics:")
print(f"  Listen: {request_topic}")
print(f"  Listen: {assignment_topic}")
print(f"  Publish: {ranking_topic}")
print(f"  Publish: {response_topic}")

# MQTT setup
client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    timestamp = time.strftime("%H:%M:%S")
    print(f"[Simulator {vehicle_number}] [{timestamp}] Connected to MQTT broker (rc={rc})")

    # Subscribe to requests from Digital Twin
    client.subscribe(request_topic)
    client.subscribe(assignment_topic)
    print(f"[Simulator {vehicle_number}] Subscribed to:")
    print(f"  - {request_topic}")
    print(f"  - {assignment_topic}")


def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()
    timestamp = time.strftime("%H:%M:%S")
    print(f"[Simulator {vehicle_number}] [{timestamp}] Received on {topic}: {payload}")

    if topic == request_topic:
        # DT requests a ranking
        ranking = random.randint(1, 100)
        print(f"[Simulator {vehicle_number}] Generated ranking: {ranking}")
        print(f"[Simulator {vehicle_number}] Publishing ranking to: {ranking_topic}")
        
        result = client.publish(ranking_topic, str(ranking))
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"[Simulator {vehicle_number}] Ranking published successfully")
        else:
            print(f"[Simulator {vehicle_number}] ERROR: Failed to publish ranking (rc={result.rc})")

    elif topic == assignment_topic:
        print(f"[Simulator {vehicle_number}] Processing task assignment...")
        
        try:
            data = json.loads(payload)
        except json.JSONDecodeError as e:
            print(f"[Simulator {vehicle_number}] ERROR: Invalid JSON in task assignment: {e}")
            return

        assigned = data.get("assigned", False)
        print(f"[Simulator {vehicle_number}] Task assigned: {assigned}")
        
        if assigned:
            # Generate random number to determine success/failure
            task_number = random.randint(1, 100)
            can_complete = (task_number % 2 == 0)
            result_data = {"can_complete": can_complete}
            
            print(f"[Simulator {vehicle_number}] Task evaluation:")
            print(f"  Random number: {task_number}")
            print(f"  Can complete: {can_complete}")
            print(f"  Result: {'SUCCESS' if can_complete else 'FAILURE'}")
            print(f"[Simulator {vehicle_number}] Publishing result to: {response_topic}")
            
            result_json = json.dumps(result_data)
            pub_result = client.publish(response_topic, result_json)
            
            if pub_result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"[Simulator {vehicle_number}] Task result published successfully: {result_json}")
            else:
                print(f"[Simulator {vehicle_number}] ERROR: Failed to publish task result (rc={pub_result.rc})")
                
        else:
            print(f"[Simulator {vehicle_number}] Task REJECTED")
            result_data = {"can_complete": False}
            result_json = json.dumps(result_data)
            
            pub_result = client.publish(response_topic, result_json)
            if pub_result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"[Simulator {vehicle_number}] Rejection response published: {result_json}")
            else:
                print(f"[Simulator {vehicle_number}] ERROR: Failed to publish rejection (rc={pub_result.rc})")

    else:
        print(f"[Simulator {vehicle_number}] WARNING: Received message on unexpected topic: {topic}")


def on_publish(client, userdata, mid):
    print(f"[Simulator {vehicle_number}] Message {mid} published successfully")


def on_log(client, userdata, level, buf):
    print(f"[Simulator {vehicle_number}] MQTT Log: {buf}")


# Attach callbacks
client.on_connect = on_connect
client.on_message = on_message
client.on_publish = on_publish
# Uncomment for detailed MQTT logs:
# client.on_log = on_log

def main():
    print(f"[Simulator {vehicle_number}] Connecting to MQTT broker at {BROKER}:{PORT}")
    try:
        client.connect(BROKER, PORT)
        print(f"[Simulator {vehicle_number}] Starting MQTT loop...")
        client.loop_forever()
    except KeyboardInterrupt:
        print(f"\n[Simulator {vehicle_number}] Shutting down...")
        client.disconnect()
    except Exception as e:
        print(f"[Simulator {vehicle_number}] ERROR: {e}")


if __name__ == "__main__":
    main()