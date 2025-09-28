import asyncio
import json
import time
import sys
import threading
from paho.mqtt.client import Client as MQTTClient
import pandas as pd

# === Import vehicle number ===
vehicle_number = int(sys.argv[1]) if len(sys.argv) > 1 else 1

# === Config ===
MQTT_BROKER = "localhost"
MQTT_PORT = 4001

# Topics (Simulator ↔ DT) – DO NOT CHANGE
SIM_TOPIC_INSTRUCTION = f"vehicle{vehicle_number}_next_destination"  # DT → simulator
SIM_TOPIC_UPDATE = f"vehicle{vehicle_number}update"                  # simulator → DT

# TCP (Agent ↔ DT)
DT_BASE_PORT = 5000  # vehicle1 → 5000, vehicle2 → 5001, ...

class DigitalTwin:
    def __init__(self, vehicle_id: int):
        self.vehicle_id = vehicle_id
        self.client = MQTTClient()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        # --- Raw simulator data storage ---
        self.raw_simulator_data = {}
        self.state_history = []
        self.last_update_time = None

        # --- Synchronization ---
        self.message_ack = threading.Event()

        # --- TCP connections (agent clients) ---
        self.agent_writers = set()

    # ---------- MQTT (Simulator Communication) ----------
    def start_mqtt(self):
        print(f"[DigitalTwin {self.vehicle_id}] Connecting to MQTT broker {MQTT_BROKER}:{MQTT_PORT}")
        self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
        self.client.loop_start()

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"[DigitalTwin {self.vehicle_id}] ✅ Connected to MQTT broker")
            client.subscribe(SIM_TOPIC_UPDATE)
            print(f"[DigitalTwin {self.vehicle_id}] 📡 Subscribed to {SIM_TOPIC_UPDATE} (simulator)")
        else:
            print(f"[DigitalTwin {self.vehicle_id}] ❌ MQTT connection failed (rc={rc})")

    def on_message(self, client, userdata, msg):
        payload = msg.payload.decode()
        timestamp = time.strftime("%H:%M:%S")

        if msg.topic == SIM_TOPIC_UPDATE:
            try:
                raw_data = json.loads(payload)
                print(f"[DigitalTwin {self.vehicle_id}] 📨 Raw simulator data ({timestamp}): {raw_data}")
            except json.JSONDecodeError:
                print(f"[DigitalTwin {self.vehicle_id}] ⚠️ Non-JSON payload received: {payload}")
                return

            # Store raw data
            self.raw_simulator_data = raw_data
            self.state_history.append({
                "timestamp": time.time(),
                "raw_data": raw_data
            })
            self.last_update_time = time.time()

            # Convert data format for agents
            converted_data = self.convert_simulator_data_to_agent_format(raw_data)
            
            # Forward converted data to connected agents
            print(f"[DigitalTwin {self.vehicle_id}] 🔄 Converting and forwarding to agent(s)")
            self.forward_to_agents({
                "type": "vehicle_data", 
                "data": converted_data
            })

            progress = raw_data.get("progress", 0)
            if progress == 100:
                self.message_ack.set()
            else:
                self.message_ack.clear()

            self.detect_anomalies(progress)

    def convert_simulator_data_to_agent_format(self, raw_data: dict) -> dict:
        """
        Convert raw simulator JSON/MQTT data to agent-readable format
        Simulator format → Agent storage format
        """
        # Raw simulator data keys: progress, next_location, previous_location, x_coordinate, y_coordinate, current_node
        # Agent storage format: mission_progress, current_location, target_location, x_position, y_position, previous_location
        
        progress = raw_data.get("progress", 0)
        next_location = raw_data.get("next_location")
        previous_location = raw_data.get("previous_location") 
        current_node = raw_data.get("current_node")

        # Determine current location based on progress and destinations
        if progress == 100 and next_location:
            current_location = next_location
        elif current_node is not None:
            current_location = f"Node{current_node}"
        elif previous_location:
            # Fallback to previous location if current_node is null
            current_location = previous_location
        else:
            current_location = "Unknown"
            
        converted_data = {
            "mission_progress": progress,  # progress → mission_progress
            "current_location": current_location,  # derived from current_node/next_location
            "target_location": next_location,  # next_location → target_location
            "previous_location": previous_location,  # same key
            "x_position": raw_data.get("x_coordinate", 0),  # x_coordinate → x_position
            "y_position": raw_data.get("y_coordinate", 0),  # y_coordinate → y_position
            "raw_current_node": current_node,  # keep original for reference
            "conversion_timestamp": time.time()
        }
        
        print(f"[DigitalTwin {self.vehicle_id}] 🔄 Data conversion:")
        print(f"    Raw: progress={progress}, next_location={next_location}, current_node={current_node}")
        print(f"    Converted: mission_progress={converted_data['mission_progress']}, "
              f"current_location={converted_data['current_location']}, "
              f"target_location={converted_data['target_location']}")
        
        return converted_data

    # ---------- TCP (Agent Communication) ----------
    async def handle_agent(self, reader, writer):
        addr = writer.get_extra_info("peername")
        print(f"[DigitalTwin {self.vehicle_id}] 🔌 Agent connected: {addr}")
        self.agent_writers.add(writer)

        try:
            while True:
                try:
                    data = await asyncio.wait_for(reader.readline(), timeout=30.0)
                except asyncio.TimeoutError:
                    print(f"[DigitalTwin {self.vehicle_id}] ⏳ Keepalive - Agent {addr}")
                    continue

                if not data:
                    print(f"[DigitalTwin {self.vehicle_id}] 📡 Agent disconnected: {addr}")
                    break

                msg = data.decode().strip()
                if not msg:
                    continue

                print(f"[DigitalTwin {self.vehicle_id}] 📨 Received from Agent: {msg}")

                try:
                    request = json.loads(msg)
                except json.JSONDecodeError:
                    error_resp = {"type": "error", "message": "Invalid JSON"}
                    writer.write((json.dumps(error_resp) + "\n").encode())
                    await writer.drain()
                    continue

                # Handle mission assignment (convert agent format to simulator format)
                if request.get("type") == "assign_mission":
                    destination = request.get("destination")
                    if destination:
                        # Convert agent mission format to simulator instruction format
                        simulator_instruction = self.convert_agent_mission_to_simulator_format(destination)
                        
                        # Send to simulator via MQTT
                        payload = json.dumps(simulator_instruction)
                        self.client.publish(SIM_TOPIC_INSTRUCTION, payload)
                        print(f"[DigitalTwin {self.vehicle_id}] 📤 Converted mission to simulator: {payload}")

                        # Send acknowledgment to agent
                        response = {
                            "type": "task_ack", 
                            "status": "mission_accepted",
                            "destination": destination,
                            "request_id": request.get("request_id")
                        }
                        writer.write((json.dumps(response) + "\n").encode())
                        await writer.drain()
                        print(f"[DigitalTwin {self.vehicle_id}] ✅ Mission ack sent to agent")
                    else:
                        response = {
                            "type": "task_ack", 
                            "status": "mission_rejected", 
                            "error": "No destination specified"
                        }
                        writer.write((json.dumps(response) + "\n").encode())
                        await writer.drain()

                # Handle status requests
                elif request.get("type") == "get_status":
                    # Convert current raw data to agent format and send
                    converted_data = self.convert_simulator_data_to_agent_format(self.raw_simulator_data)
                    response = {
                        "type": "vehicle_data",
                        "data": converted_data
                    }
                    writer.write((json.dumps(response) + "\n").encode())
                    await writer.drain()
                    print(f"[DigitalTwin {self.vehicle_id}] ✅ Status response sent to agent")

                else:
                    error_resp = {"type": "error", "message": f"Unknown request type: {request.get('type')}"}
                    writer.write((json.dumps(error_resp) + "\n").encode())
                    await writer.drain()

        except Exception as e:
            print(f"[DigitalTwin {self.vehicle_id}] ❌ TCP error with {addr}: {e}")
        finally:
            self.agent_writers.discard(writer)
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass
            print(f"[DigitalTwin {self.vehicle_id}] 🔌 Connection closed: {addr}")

    def convert_agent_mission_to_simulator_format(self, destination: str) -> str:
        """
        Convert agent mission format to simulator instruction format
        Agent: "Node2" → Simulator: "Node2" (direct pass-through for now)
        """
        print(f"[DigitalTwin {self.vehicle_id}] 🔄 Mission conversion: Agent '{destination}' → Simulator '{destination}'")
        return destination

    async def start_tcp(self, base_port=DT_BASE_PORT):
        port = base_port + (self.vehicle_id - 1)
        server = await asyncio.start_server(self.handle_agent, "127.0.0.1", port)
        print(f"[DigitalTwin {self.vehicle_id}] 🖥️ Listening for Agent on port {port}")
        async with server:
            await server.serve_forever()

    # ---------- Helper Functions ----------
    def forward_to_agents(self, message: dict):
        """Forward converted data to all connected agents"""
        if not self.agent_writers:
            print(f"[DigitalTwin {self.vehicle_id}] ⚠️ No agents connected, cannot forward message")
            return
        msg = json.dumps(message) + "\n"
        dead_writers = set()
        for w in self.agent_writers:
            try:
                w.write(msg.encode())
            except Exception:
                dead_writers.add(w)
        for w in dead_writers:
            self.agent_writers.discard(w)

    def detect_anomalies(self, progress):
        """Detect anomalies in simulator data"""
        now = time.time()
        if self.last_update_time and now - self.last_update_time > 10:
            print(f"[DigitalTwin {self.vehicle_id}] ⚠️ Anomaly: No updates received in >10s")

    def export_history(self):
        """Export raw simulator data history"""
        filename = f"vehicle{self.vehicle_id}_raw_history.json"
        with open(filename, "w") as f:
            json.dump(self.state_history, f, indent=2)
        print(f"[DigitalTwin {self.vehicle_id}] 💾 Raw history exported to {filename}")
        return pd.DataFrame(self.state_history)


if __name__ == "__main__":
    twin = DigitalTwin(vehicle_number)
    twin.start_mqtt()

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(twin.start_tcp())
    except KeyboardInterrupt:
        print(f"\n[DigitalTwin {vehicle_number}] 👋 Shutting down...")
        twin.export_history()
        twin.client.loop_stop()
        twin.client.disconnect()