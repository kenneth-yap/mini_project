import asyncio
import json
import time
import sys
import threading
from paho.mqtt.client import Client as MQTTClient
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional

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

# === Performance Metrics Configuration ===
CARBON_PER_UNIT_DISTANCE = 0.12  # kg CO2 per distance unit
COST_PER_UNIT_DISTANCE = 0.50    # currency per distance unit
COST_PER_UNIT_TIME = 0.10        # currency per time unit (operating cost)

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

        # --- Journey tracking ---
        self.current_journey = None
        self.completed_journeys = []
        
        # --- Task tracking (from manager) ---
        self.tasks_completed = 0
        self.tasks_accepted = 0
        self.tasks_rejected = 0
        
        # --- Comprehensive metrics ---
        self.total_distance_traveled = 0.0
        self.total_carbon_emitted = 0.0
        self.total_cost_incurred = 0.0
        self.total_active_time = 0.0
        self.total_idle_time = 0.0
        self.node_visit_count = {}
        self.edge_usage_count = {}  # Track which edges are used most
        
        # --- Performance analytics ---
        self.velocity_history = []
        self.last_position = None
        self.last_velocity = 0.0
        self.last_timestamp = None
        self.peak_velocity = 0.0
        
        # --- Mission tracking ---
        self.current_mission = None
        self.mission_start_time = None

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
        timestamp = time.time()
        timestamp_str = time.strftime("%H:%M:%S")

        if msg.topic == SIM_TOPIC_UPDATE:
            try:
                raw_data = json.loads(payload)
                print(f"[DigitalTwin {self.vehicle_id}] 📨 Raw simulator data ({timestamp_str}): {raw_data}")
            except json.JSONDecodeError:
                print(f"[DigitalTwin {self.vehicle_id}] ⚠️ Non-JSON payload received: {payload}")
                return

            # Calculate metrics before storing
            self._calculate_journey_metrics(raw_data, timestamp)
            
            # Store raw data with enhanced metadata
            state_entry = {
                "timestamp": timestamp,
                "datetime": datetime.fromtimestamp(timestamp).isoformat(),
                "raw_data": raw_data,
                "metrics": self._get_current_metrics(),
                "mission_context": {
                    "current_task_id": self.current_mission.get("task_id") if self.current_mission else None,
                    "mission_destination": self.current_mission.get("destination") if self.current_mission else None,
                    "mission_elapsed_time": time.time() - self.mission_start_time if self.mission_start_time else 0
                }
            }
            
            self.raw_simulator_data = raw_data
            self.state_history.append(state_entry)
            self.last_update_time = timestamp

            # Convert data format for agents
            converted_data = self.convert_simulator_data_to_agent_format(raw_data)
            
            # Forward converted data to connected agents
            print(f"[DigitalTwin {self.vehicle_id}] 🔄 Converting and forwarding to agent(s)")
            self.forward_to_agents({
                "type": "vehicle_data", 
                "data": converted_data,
                "metrics": self._get_current_metrics()
            })

            progress = raw_data.get("progress", 0)
            next_location = raw_data.get("next_location")
            
            # Track journey segments
            self._track_journey_segment(raw_data, timestamp)
            
            # Check for journey completion
            if progress == 100:
                if next_location:
                    self._complete_journey_segment(raw_data, timestamp)
                    self.message_ack.set()
                else:
                    self.message_ack.clear()
            else:
                self.message_ack.clear()

    def _calculate_journey_metrics(self, raw_data: dict, timestamp: float):
        """Calculate distance, carbon, cost, and velocity metrics"""
        current_x = raw_data.get("x_coordinate", 0)
        current_y = raw_data.get("y_coordinate", 0)
        current_position = (current_x, current_y)
        
        # Calculate distance traveled since last update
        if self.last_position is not None:
            distance = ((current_x - self.last_position[0])**2 + 
                       (current_y - self.last_position[1])**2)**0.5
            
            self.total_distance_traveled += distance
            
            # Calculate carbon emissions
            carbon_emitted = distance * CARBON_PER_UNIT_DISTANCE
            self.total_carbon_emitted += carbon_emitted
            
            # Calculate costs
            distance_cost = distance * COST_PER_UNIT_DISTANCE
            
            if self.last_timestamp is not None:
                time_elapsed = timestamp - self.last_timestamp
                time_cost = time_elapsed * COST_PER_UNIT_TIME
                
                # Calculate velocity
                if time_elapsed > 0:
                    velocity = distance / time_elapsed
                    self.velocity_history.append({
                        "timestamp": timestamp,
                        "velocity": velocity,
                        "distance": distance,
                        "time_elapsed": time_elapsed
                    })
                    
                    self.last_velocity = velocity
                    
                    # Update peak velocity
                    if velocity > self.peak_velocity:
                        self.peak_velocity = velocity
                    
                    # Track idle vs active time
                    if velocity < 0.01:  # Essentially stationary
                        self.total_idle_time += time_elapsed
                    else:
                        self.total_active_time += time_elapsed
                else:
                    time_cost = 0
                
                self.total_cost_incurred += distance_cost + time_cost
        
        self.last_position = current_position
        self.last_timestamp = timestamp
    
    def _track_journey_segment(self, raw_data: dict, timestamp: float):
        """Track journey segment from one node to another"""
        progress = raw_data.get("progress", 0)
        next_location = raw_data.get("next_location")
        previous_location = raw_data.get("previous_location")
        current_node = raw_data.get("current_node")
        
        # Start new journey segment when we have a clear start->end path
        if progress < 100 and self.current_journey is None and next_location and previous_location:
            self.current_journey = {
                "journey_id": f"J_{self.vehicle_id}_{len(self.completed_journeys)+1}",
                "start_node": previous_location,
                "end_node": next_location,
                "start_time": timestamp,
                "start_position": (raw_data.get("x_coordinate"), raw_data.get("y_coordinate")),
                "start_distance": self.total_distance_traveled,
                "start_carbon": self.total_carbon_emitted,
                "start_cost": self.total_cost_incurred,
                "waypoints": [],
                "task_id": self.current_mission.get("task_id") if self.current_mission else None
            }
            print(f"[DigitalTwin {self.vehicle_id}] 🚀 Started journey: {previous_location} → {next_location}")
        
        # Record waypoints during journey
        if self.current_journey is not None:
            self.current_journey["waypoints"].append({
                "timestamp": timestamp,
                "progress": progress,
                "position": (raw_data.get("x_coordinate"), raw_data.get("y_coordinate")),
                "current_node": current_node
            })
    
    def _complete_journey_segment(self, raw_data: dict, timestamp: float):
        """Complete and record journey segment metrics"""
        if self.current_journey is None:
            return
        
        # Calculate journey-specific metrics
        journey_duration = timestamp - self.current_journey["start_time"]
        journey_distance = self.total_distance_traveled - self.current_journey["start_distance"]
        journey_carbon = self.total_carbon_emitted - self.current_journey["start_carbon"]
        journey_cost = self.total_cost_incurred - self.current_journey["start_cost"]
        
        # Calculate efficiency metrics
        start_pos = self.current_journey["start_position"]
        end_pos = (raw_data.get("x_coordinate"), raw_data.get("y_coordinate"))
        straight_line_distance = ((end_pos[0] - start_pos[0])**2 + 
                                 (end_pos[1] - start_pos[1])**2)**0.5
        
        path_efficiency = (straight_line_distance / journey_distance * 100) if journey_distance > 0 else 0
        average_velocity = journey_distance / journey_duration if journey_duration > 0 else 0
        
        # Complete journey record
        self.current_journey.update({
            "end_time": timestamp,
            "end_position": end_pos,
            "duration": journey_duration,
            "distance_traveled": journey_distance,
            "straight_line_distance": straight_line_distance,
            "path_efficiency": path_efficiency,
            "carbon_emitted": journey_carbon,
            "cost_incurred": journey_cost,
            "average_velocity": average_velocity,
            "waypoint_count": len(self.current_journey["waypoints"]),
            "completed": True
        })
        
        self.completed_journeys.append(self.current_journey)
        

        # Update node visit count
        end_node = self.current_journey["end_node"]
        self.node_visit_count[end_node] = self.node_visit_count.get(end_node, 0) + 1
        
        # Update edge usage
        edge = f"{self.current_journey['start_node']}->{end_node}"
        self.edge_usage_count[edge] = self.edge_usage_count.get(edge, 0) + 1
        
        print(f"[DigitalTwin {self.vehicle_id}] ✅ Journey completed:")
        print(f"    Route: {self.current_journey['start_node']} → {end_node}")
        print(f"    Duration: {journey_duration:.2f}s")
        print(f"    Distance: {journey_distance:.2f} units")
        print(f"    Efficiency: {path_efficiency:.1f}%")
        print(f"    Carbon: {journey_carbon:.3f} kg CO2")
        print(f"    Cost: ${journey_cost:.2f}")
        print(f"    Avg Velocity: {average_velocity:.2f} units/s")
        
        self.current_journey = None

    def _get_current_metrics(self) -> dict:
        """Get current comprehensive metrics snapshot"""
        # Calculate average velocity using only active time
        avg_velocity = self.total_distance_traveled / self.total_active_time if self.total_active_time > 0 else 0
        
        return {
            "total_distance": self.total_distance_traveled,
            "total_carbon": self.total_carbon_emitted,
            "total_cost": self.total_cost_incurred,
            "total_active_time": self.total_active_time,
            "current_velocity": self.last_velocity,
            "average_velocity": avg_velocity,
            "completed_journeys": len(self.completed_journeys),
            "nodes_visited": len(self.node_visit_count),
            "unique_edges_used": len(self.edge_usage_count),
            "utilization_rate": 100.0  # Always 100% since we only track active time
        }

    def convert_simulator_data_to_agent_format(self, raw_data: dict) -> dict:
        """
        Convert raw simulator JSON/MQTT data to agent-readable format
        Simulator format → Agent storage format
        """
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
            current_location = previous_location
        else:
            current_location = "Unknown"
            
        converted_data = {
            "mission_progress": progress,
            "current_location": current_location,
            "target_location": next_location,
            "previous_location": previous_location,
            "x_position": raw_data.get("x_coordinate", 0),
            "y_position": raw_data.get("y_coordinate", 0),
            "raw_current_node": current_node,
            "conversion_timestamp": time.time(),
            "performance_metrics": self._get_current_metrics()
        }
        
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
                    print(f"[DigitalTwin {self.vehicle_id}] 🔌 Agent disconnected: {addr}")
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

                # Handle mission assignment
                if request.get("type") == "assign_mission":
                    destination = request.get("destination")
                    task_id = request.get("task_id")
                    
                    if destination:
                        # Record task acceptance
                        self.tasks_accepted += 1
                        
                        # Record mission
                        self.current_mission = {
                            "task_id": task_id,
                            "destination": destination,
                            "acceptance_time": time.time(),
                            "request_data": request
                        }
                        
                        # Convert agent mission format to simulator instruction format
                        simulator_instruction = self.convert_agent_mission_to_simulator_format(destination)
                        
                        # Send to simulator via MQTT
                        payload = json.dumps(simulator_instruction)
                        self.client.publish(SIM_TOPIC_INSTRUCTION, payload)
                        print(f"[DigitalTwin {self.vehicle_id}] 📤 Converted mission to simulator: {payload}")
                        
                        # Mark mission start time
                        self.mission_start_time = time.time()

                        # Send acknowledgment to agent
                        response = {
                            "type": "task_ack", 
                            "status": "mission_accepted",
                            "destination": destination,
                            "request_id": request.get("request_id"),
                            "acceptance_time": time.time()
                        }
                        writer.write((json.dumps(response) + "\n").encode())
                        await writer.drain()
                        print(f"[DigitalTwin {self.vehicle_id}] ✅ Mission ack sent to agent")
                    else:
                        self.tasks_rejected += 1
                        response = {
                            "type": "task_ack", 
                            "status": "mission_rejected", 
                            "error": "No destination specified"
                        }
                        writer.write((json.dumps(response) + "\n").encode())
                        await writer.drain()

                # Handle mission completion
                elif request.get("type") == "mission_complete":
                    if self.current_mission:
                        self.tasks_completed += 1
                        mission_duration = time.time() - self.mission_start_time if self.mission_start_time else 0
                        
                        print(f"[DigitalTwin {self.vehicle_id}] 🎯 Task completed: {self.current_mission['task_id']}")
                        print(f"    Duration: {mission_duration:.2f}s")
                        
                        self.current_mission = None
                        self.mission_start_time = None

                # Handle status requests
                elif request.get("type") == "get_status":
                    converted_data = self.convert_simulator_data_to_agent_format(self.raw_simulator_data)
                    response = {
                        "type": "vehicle_data",
                        "data": converted_data,
                        "metrics": self._get_current_metrics()
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
        """Convert agent mission format to simulator instruction format"""
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

    def export_history(self):
        """Export comprehensive data history with CLEAN metrics"""
        
        # Export raw state history
        filename_raw = f"vehicle{self.vehicle_id}_raw_history.json"
        with open(filename_raw, "w") as f:
            json.dump(self.state_history, f, indent=2)
        print(f"[DigitalTwin {self.vehicle_id}] 💾 Raw history exported to {filename_raw}")
        
        # Export journey summaries
        filename_journeys = f"vehicle{self.vehicle_id}_journeys.json"
        with open(filename_journeys, "w") as f:
            json.dump(self.completed_journeys, f, indent=2)
        print(f"[DigitalTwin {self.vehicle_id}] 💾 Journey data exported to {filename_journeys}")
        
        # Get unique nodes visited (actual list)
        unique_nodes_visited = list(self.node_visit_count.keys())
        
        # Get most visited node
        most_visited = max(self.node_visit_count.items(), key=lambda x: x[1]) if self.node_visit_count else (None, 0)
        
        # Get most used edge
        most_used_edge = max(self.edge_usage_count.items(), key=lambda x: x[1]) if self.edge_usage_count else (None, 0)
        
        # Calculate average journey metrics
        avg_journey_distance = self.total_distance_traveled / len(self.completed_journeys) if self.completed_journeys else 0
        avg_journey_efficiency = sum(j["path_efficiency"] for j in self.completed_journeys) / len(self.completed_journeys) if self.completed_journeys else 0
        
        # Calculate average velocity using active time only
        avg_velocity = self.total_distance_traveled / self.total_active_time if self.total_active_time > 0 else 0
        
        # Export CLEAN comprehensive metrics summary
        summary = {
            "vehicle_id": self.vehicle_id,
            "export_timestamp": time.time(),
            "export_datetime": datetime.now().isoformat(),
            
            "task_metrics": {
                "total_tasks_completed": self.tasks_completed,
                "total_tasks_accepted": self.tasks_accepted,
                "total_tasks_rejected": self.tasks_rejected
            },
            
            "travel_metrics": {
                "total_distance": round(self.total_distance_traveled, 2),
                "total_carbon_emissions": round(self.total_carbon_emitted, 2),
                "total_cost": round(self.total_cost_incurred, 2),
                "total_travel_time": round(self.total_active_time, 2),
                "average_velocity": round(avg_velocity, 2)
            },
            
            "journey_metrics": {
                "total_journeys": len(self.completed_journeys),
                "average_journey_distance": round(avg_journey_distance, 2),
                "average_journey_efficiency": round(avg_journey_efficiency, 2),
                "nodes_visited": unique_nodes_visited,
                "unique_nodes_count": len(unique_nodes_visited),
                "edges_used": list(self.edge_usage_count.keys()),
                "unique_edges_count": len(self.edge_usage_count)
            },
            
            "node_statistics": {
                "visit_counts": self.node_visit_count,
                "most_visited_node": most_visited[0],
                "most_visited_count": most_visited[1]
            },
            
            "edge_statistics": {
                "usage_counts": self.edge_usage_count,
                "most_used_edge": most_used_edge[0],
                "most_used_count": most_used_edge[1]
            },
            
            "efficiency_metrics": {
                "average_speed": round(avg_velocity, 2),
                "distance_per_task": round(self.total_distance_traveled / self.tasks_completed, 2) if self.tasks_completed > 0 else 0
            }
        }
        
        filename_summary = f"vehicle{self.vehicle_id}_summary.json"
        with open(filename_summary, "w") as f:
            json.dump(summary, f, indent=2)
        print(f"[DigitalTwin {self.vehicle_id}] 💾 Summary exported to {filename_summary}")
        
        # Also export as DataFrames for easy analysis
        df_state = pd.DataFrame(self.state_history)
        df_journeys = pd.DataFrame(self.completed_journeys)
        df_velocity = pd.DataFrame(self.velocity_history)
        
        return {
            "state_df": df_state,
            "journeys_df": df_journeys,
            "velocity_df": df_velocity,
            "summary": summary
        }


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