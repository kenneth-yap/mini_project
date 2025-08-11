import paho.mqtt.client as mqtt
import random
import time

vehicle_number = 2
topic = f"vehicle/{vehicle_number}/ranking"

client = mqtt.Client()
client.connect("localhost", 1883)
client.loop_start()

try:
    while True:
        ranking = random.randint(1, 100)
        print(f"Publishing ranking {ranking} on topic {topic}")
        client.publish(topic, str(ranking))
        time.sleep(5)
        
except KeyboardInterrupt:
    client.loop_stop()
    client.disconnect()
