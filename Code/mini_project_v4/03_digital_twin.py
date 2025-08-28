import asyncio
import json
import socket
from paho.mqtt.client import Client as MQTTClient
import sys
import time

# === Import vehicle number ===
vehicle_number = int(sys.argv[1]) if len(sys.argv) > 1 else 1

# === Config ===
MQTT_BROKER = "localhost"
MQTT_PORT = 1883

TCP_HOST = "127.0.0.1"
TCP_PORT = 5000  # port the Digital Twin listens on for vehicle agents


class DigitalTwin:
    def __init__(self, vehicle_number: int, tcp_port: int):
        self.vehicle_number = vehicle_number
        self.tcp_port = tcp_port
        self.loop = asyncio.get_event_loop()

        # MQTT
        self.client = MQTTClient()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        # Storage for awaiting responses
        self.pending_futures = {}
        
        # Debug counters
        self.request_counter = 0

    # ---------- MQTT ----------
    def start_mqtt(self):
        print(f"[DigitalTwin] Starting MQTT connection to {MQTT_BROKER}:{MQTT_PORT}")
        self.client.connect(MQTT_BROKER, MQTT_PORT)
        self.client.loop_start()

    def on_connect(self, client, userdata, flags, rc):
        print(f"[DigitalTwin] Connected to MQTT broker (rc={rc})")
        # Sub to topics from vehicle simulator
        ranking_topic = f"vehicle/{self.vehicle_number}/ranking"
        response_topic = f"vehicle/{self.vehicle_number}/task_response"
        
        client.subscribe(ranking_topic)
        client.subscribe(response_topic)
        print(f"[DigitalTwin] Subscribed to topics:")
        print(f"  - {ranking_topic}")
        print(f"  - {response_topic}")

    def on_message(self, client, userdata, msg):
        payload = msg.payload.decode()
        topic = msg.topic
        timestamp = time.strftime("%H:%M:%S")
        print(f"[DigitalTwin] [{timestamp}] MQTT received on {topic}: {payload}")

        # Match response to waiting future
        if topic.endswith("/ranking"):
            print(f"[DigitalTwin] Processing ranking response: {payload}")
            future = self.pending_futures.pop("ranking", None)
            if future and not future.done():
                try:
                    result = int(payload)
                    future.set_result(result)
                    print(f"[DigitalTwin] Ranking future resolved with: {result}")
                except ValueError as e:
                    print(f"[DigitalTwin] Error parsing ranking: {e}")
                    future.set_result(None)
            else:
                print(f"[DigitalTwin] No pending ranking future found or future already done")

        elif topic.endswith("/task_response"):
            print(f"[DigitalTwin] Processing task response: {payload}")
            future = self.pending_futures.pop("task_response", None)
            if future and not future.done():
                try:
                    result = json.loads(payload)
                    future.set_result(result)
                    print(f"[DigitalTwin] Task response future resolved with: {result}")
                except json.JSONDecodeError as e:
                    print(f"[DigitalTwin] Error parsing task response JSON: {e}")
                    future.set_result(None)
            else:
                print(f"[DigitalTwin] No pending task_response future found or future already done")
                print(f"[DigitalTwin] Current pending futures: {list(self.pending_futures.keys())}")

    async def request_ranking_from_sim(self, timeout=5):
        """Send ranking request via MQTT and wait for response"""
        request_id = self.request_counter
        self.request_counter += 1
        
        request_topic = f"vehicle/{self.vehicle_number}/request_ranking"
        print(f"[DigitalTwin] [{request_id}] Requesting ranking from simulator...")
        print(f"[DigitalTwin] [{request_id}] Publishing to: {request_topic}")
        
        # Create future before publishing
        future = self.loop.create_future()
        self.pending_futures["ranking"] = future
        print(f"[DigitalTwin] [{request_id}] Created future for ranking")
        
        # Publish request
        self.client.publish(request_topic, "get")
        print(f"[DigitalTwin] [{request_id}] Published ranking request")
        
        try:
            result = await asyncio.wait_for(future, timeout)
            print(f"[DigitalTwin] [{request_id}] Received ranking: {result}")
            return result
        except asyncio.TimeoutError:
            print(f"[DigitalTwin] [{request_id}] Ranking request TIMEOUT after {timeout}s")
            # Clean up the future
            self.pending_futures.pop("ranking", None)
            return None

    async def assign_task_to_sim(self, assigned: bool, ranking: int, timeout=10):
        request_id = self.request_counter
        self.request_counter += 1
        
        assignment_topic = f"vehicle/{self.vehicle_number}/task_assignment"
        print(f"[DigitalTwin] [{request_id}] Assigning task - assigned: {assigned}, ranking: {ranking}")
        print(f"[DigitalTwin] [{request_id}] Publishing to: {assignment_topic}")
        
        if assigned:
            # Create future before publishing
            future = self.loop.create_future()
            self.pending_futures["task_response"] = future
            print(f"[DigitalTwin] [{request_id}] Created future for task_response")
            print(f"[DigitalTwin] [{request_id}] Current pending futures: {list(self.pending_futures.keys())}")
            
            payload = json.dumps({"assigned": assigned, "ranking": ranking})
            self.client.publish(assignment_topic, payload)
            print(f"[DigitalTwin] [{request_id}] Published task assignment: {payload}")
            
            try:
                result = await asyncio.wait_for(future, timeout)
                print(f"[DigitalTwin] [{request_id}] Task assignment result: {result}")
                return result
            except asyncio.TimeoutError:
                print(f"[DigitalTwin] [{request_id}] Task assignment TIMEOUT after {timeout}s")
                # Clean up the future
                self.pending_futures.pop("task_response", None)
                return {"can_complete": False, "note": "Timeout"}
        else:
            payload = json.dumps({"assigned": False})
            self.client.publish(assignment_topic, payload)
            print(f"[DigitalTwin] [{request_id}] Published task rejection: {payload}")
            return {"can_complete": False, "note": "Rejected"}

    # ---------- TCP ----------
    async def handle_tcp_client(self, reader, writer):
        addr = writer.get_extra_info("peername")
        print(f"[DigitalTwin] TCP connection established from {addr}")

        try:
            while True:
                # Read data with a timeout to prevent hanging
                try:
                    data = await asyncio.wait_for(reader.readline(), timeout=30.0)
                except asyncio.TimeoutError:
                    print(f"[DigitalTwin] TCP read timeout for {addr}")
                    break
                    
                if not data:
                    print(f"[DigitalTwin] TCP client {addr} disconnected")
                    break

                msg = data.decode().strip()
                timestamp = time.strftime("%H:%M:%S")
                print(f"[DigitalTwin] [{timestamp}] TCP received from {addr}: {msg}")

                try:
                    req = json.loads(msg)
                except json.JSONDecodeError as e:
                    print(f"[DigitalTwin] Invalid JSON from TCP: {e}")
                    error_resp = {"type": "error", "message": "Invalid JSON"}
                    writer.write((json.dumps(error_resp) + "\n").encode())
                    await writer.drain()
                    continue

                # ---------- Handle Ranking Request ----------
                if req.get("type") == "request_ranking":
                    print(f"[DigitalTwin] Processing TCP ranking request...")
                    ranking = await self.request_ranking_from_sim()
                    resp = {"type": "ranking_response", "ranking": ranking or 0}

                    response_json = json.dumps(resp) + "\n"
                    writer.write(response_json.encode())
                    await writer.drain()
                    print(f"[DigitalTwin] Sent TCP ranking response: {resp}")

                # ---------- Handle Task Assignment ----------
                elif req.get("type") == "assign_task":
                    print(f"[DigitalTwin] Processing TCP task assignment...")
                    print(f"[DigitalTwin] Request details: {req}")
                    
                    result = await self.assign_task_to_sim(
                        req.get("assigned", False), 
                        req.get("ranking", 0)
                    )
                    
                    if result is None:
                        result = {"can_complete": False, "note": "No response"}
                        print(f"[DigitalTwin] No result from simulator, using default")
                    
                    resp = {"type": "task_result", **result}
                    response_json = json.dumps(resp) + "\n"
                    writer.write(response_json.encode())
                    await writer.drain()
                    print(f"[DigitalTwin] Sent TCP task result: {resp}")

                else:
                    print(f"[DigitalTwin] Unknown TCP request type: {req.get('type')}")
                    error_resp = {"type": "error", "message": f"Unknown request type: {req.get('type')}"}
                    writer.write((json.dumps(error_resp) + "\n").encode())
                    await writer.drain()

        except Exception as e:
            print(f"[DigitalTwin] TCP Error with {addr}: {e}")
            import traceback
            traceback.print_exc()
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception as e:
                print(f"[DigitalTwin] Error closing connection: {e}")
            print(f"[DigitalTwin] TCP connection closed: {addr}")

    async def start_tcp_server(self):
        """Start the TCP server"""
        server = await asyncio.start_server(
            self.handle_tcp_client, TCP_HOST, self.tcp_port
        )
        print(f"[DigitalTwin] TCP server listening on {TCP_HOST}:{self.tcp_port}")
        print(f"[DigitalTwin] Vehicle {self.vehicle_number} Digital Twin ready")
        
        async with server:
            await server.serve_forever()


async def main_async(vehicle_number: int):
    tcp_port = TCP_PORT + (vehicle_number - 1)
    print(f"[DigitalTwin] Starting Digital Twin for vehicle {vehicle_number}")
    print(f"[DigitalTwin] TCP port: {tcp_port}")
    
    twin = DigitalTwin(vehicle_number, tcp_port)
    twin.start_mqtt()

    # Wait a moment for MQTT to connect
    print(f"[DigitalTwin] Waiting for MQTT connection...")
    await asyncio.sleep(2)

    # Start the TCP server
    await twin.start_tcp_server()


def main(vehicle_number: int):
    tcp_port = TCP_PORT + (vehicle_number - 1)
    twin = DigitalTwin(vehicle_number, tcp_port)
    twin.start_mqtt()

    loop = asyncio.get_event_loop()
    
    async def run_server():
        server = await asyncio.start_server(
            twin.handle_tcp_client,
            TCP_HOST,
            tcp_port
        )
        print(f"[DigitalTwin] TCP server for vehicle {vehicle_number} listening on {TCP_HOST}:{tcp_port}")
        
        async with server:
            await server.serve_forever()  # This was missing!

    try:
        loop.run_until_complete(run_server())
    except KeyboardInterrupt:
        print(f"\n[DigitalTwin] Shutting down vehicle {vehicle_number}...")
    finally:
        twin.client.loop_stop()
        twin.client.disconnect()

if __name__ == "__main__":
    main(vehicle_number)