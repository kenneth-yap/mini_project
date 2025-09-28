import asyncio
import json
import random
import time
import sys
import math
import heapq
from typing import Optional, Dict, List, Tuple
from collections import defaultdict

# === Import vehicle number ===
vehicle_number = int(sys.argv[1]) if len(sys.argv) > 1 else 1

# === Config ===
DT_BASE_PORT = 5000  # Digital Twin base port (vehicle1 → 5000, vehicle2 → 5001, etc.)

# === ROUTING PRIORITY SETTING ===
# Change this value to set routing priority:
# 1 = Shortest Distance
# 2 = Lowest Carbon Emissions  
# 3 = Lowest Cost
# 4 = Fastest Travel Time
ROUTING_PRIORITY = 1

class VehicleRoutingSystem:
    """Integrated routing system for path optimization"""
    
    def __init__(self, map_file_path=None, vehicles_file_path=None):
        self.nodes = {}
        self.connections = defaultdict(list)
        self.edge_weights = {}
        self.vehicles = {}
        self.map_file_path = map_file_path
        self.vehicles_file_path = vehicles_file_path
        self._load_network_from_file()
        self._load_vehicles_from_file()
        
    def _load_network_from_file(self):
        """Load network data from map.txt file"""
        if not self.map_file_path:
            print("No map file path provided, using default network")
            self._initialize_default_network()
            return
            
        try:
            with open(self.map_file_path, 'r') as file:
                print(f"Loading network from: {self.map_file_path}")
                for line in file:
                    line = line.strip()
                    if line:
                        # Parse the format: {{"Node1", {250,50}},["Node2","Node3","Node4","Node5","Node6"]}.
                        print(f"Parsing line: {line}")
                        
                        # Remove outer braces and period
                        line = line.strip('{}.}')
                        
                        # Find the node name (between first two quotes)
                        node_start = line.find('"') + 1
                        node_end = line.find('"', node_start)
                        node_name = line[node_start:node_end]
                        
                        # Find coordinates (between { and })
                        coord_start = line.find('{', node_end) + 1
                        coord_end = line.find('}', coord_start)
                        coords_str = line[coord_start:coord_end]
                        
                        # Parse coordinates
                        coords = coords_str.split(',')
                        x = int(coords[0].strip())
                        y = int(coords[1].strip())
                        
                        self.nodes[node_name] = (x, y)
                        
                        # Find connections (between [ and ])
                        bracket_start = line.find('[')
                        if bracket_start != -1:
                            bracket_end = line.find(']', bracket_start)
                            if bracket_end != -1:
                                connections_str = line[bracket_start+1:bracket_end]
                                if connections_str.strip():
                                    # Split by comma and clean up quotes
                                    connections = [conn.strip().strip('"') for conn in connections_str.split('","')]
                                    # Handle first and last items that might have extra quotes
                                    connections = [conn.strip('"') for conn in connections]
                                    for conn in connections:
                                        if conn:  # Make sure connection is not empty
                                            self.connections[node_name].append(conn)
                        
                        print(f"  Added node: {node_name} at {(x, y)} with connections: {self.connections[node_name]}")
                                        
            print(f"Loaded {len(self.nodes)} nodes from map file")
            self._build_edge_weights()
            
        except FileNotFoundError:
            print(f"Map file not found at {self.map_file_path}")
            print("Using default network data for demonstration...")
            self._initialize_default_network()
        except Exception as e:
            print(f"Error parsing map file: {e}")
            print("Using default network data for demonstration...")
            self._initialize_default_network()
            
    def _initialize_default_network(self):
        """Initialize default 15-node network if file loading fails"""
        # Node coordinates (x, y)
        network_data = [
            ("Node1", (200, 250), ["Node2", "Node3", "Node4", "Node5", "Node6", "Node7"]),
            ("Node2", (200, 150), ["Node8", "Node9"]),
            ("Node3", (200, 350), ["Node10", "Node11"]),
            ("Node4", (300, 250), ["Node6", "Node12"]),
            ("Node5", (100, 250), ["Node7", "Node13"]),
            ("Node6", (350, 300), ["Node12"]),
            ("Node7", (50, 300), ["Node13"]),
            ("Node8", (150, 100), ["Node9", "Node13"]),
            ("Node9", (250, 100), ["Node12"]),
            ("Node10", (150, 400), ["Node11", "Node13"]),
            ("Node11", (250, 400), ["Node12"]),
            ("Node12", (350, 200), []),
            ("Node13", (50, 200), []),
            ("Node14", (100, 50), []),
            ("Node15", (300, 50), [])
        ]
        
        # Build nodes and connections
        for node_name, coords, connections in network_data:
            self.nodes[node_name] = coords
            for conn in connections:
                self.connections[node_name].append(conn)
                
        # Build edge weights
        self._build_edge_weights()
        
    def _build_edge_weights(self):
        """Calculate distances and assign random weights for all edges"""
        for node, connected_nodes in self.connections.items():
            for connected_node in connected_nodes:
                if connected_node in self.nodes:
                    # Calculate distance
                    x1, y1 = self.nodes[node]
                    x2, y2 = self.nodes[connected_node]
                    distance = math.sqrt((x2-x1)**2 + (y2-y1)**2)
                    
                    # Assign weights based on distance
                    carbon_emission = random.uniform(0.1, 2.0) * distance
                    cost = random.uniform(0.5, 3.0) * distance
                    
                    # Store edge weights (use sorted tuple as key for bidirectional edges)
                    edge_key = tuple(sorted([node, connected_node]))
                    if edge_key not in self.edge_weights:
                        self.edge_weights[edge_key] = {
                            'distance': distance,
                            'carbon': carbon_emission,
                            'cost': cost
                        }
    
    def _load_vehicles_from_file(self):
        """Load vehicle data from vehicles.txt file"""
        if not self.vehicles_file_path:
            print("No vehicles file path provided, using default vehicles")
            self._initialize_default_vehicles()
            return
            
        try:
            with open(self.vehicles_file_path, 'r') as file:
                print(f"Loading vehicles from: {self.vehicles_file_path}")
                for line in file:
                    line = line.strip()
                    if line:
                        # Parse format: {1, 30, "Node1"}.
                        print(f"Parsing vehicle line: {line}")
                        
                        # Remove outer braces and period
                        line = line.strip('{}.')
                        
                        # Split by comma
                        parts = [p.strip() for p in line.split(',')]
                        
                        vehicle_id = int(parts[0])
                        speed = int(parts[1])
                        start_node = parts[2].strip('"')  # Remove quotes
                        
                        self.vehicles[vehicle_id] = {
                            'speed': speed,
                            'start_node': start_node
                        }
                        
                        print(f"  Added vehicle: {vehicle_id}, speed: {speed}, start: {start_node}")
                        
            print(f"Loaded {len(self.vehicles)} vehicles from file")
            
        except FileNotFoundError:
            print(f"Vehicles file not found at {self.vehicles_file_path}")
            print("Using default vehicle data for demonstration...")
            self._initialize_default_vehicles()
        except Exception as e:
            print(f"Error parsing vehicles file: {e}")
            print("Using default vehicle data for demonstration...")
            self._initialize_default_vehicles()
    
    def _initialize_default_vehicles(self):
        """Initialize default vehicle data if file loading fails"""
        vehicle_data = [
            (1, 25, "Node1"), (2, 35, "Node1"), (3, 40, "Node1"), (4, 30, "Node1"), (5, 45, "Node1"),
            (6, 20, "Node1"), (7, 50, "Node1"), (8, 35, "Node1"), (9, 40, "Node1"), (10, 30, "Node1")
        ]
        
        for vehicle_id, speed, start_node in vehicle_data:
            self.vehicles[vehicle_id] = {
                'speed': speed,
                'start_node': start_node
            }
    
    def get_edge_weight(self, node1: str, node2: str, weight_type: str) -> float:
        """Get edge weight between two nodes"""
        edge_key = tuple(sorted([node1, node2]))
        if edge_key in self.edge_weights:
            return self.edge_weights[edge_key][weight_type]
        return float('inf')
    
    def dijkstra_shortest_path(self, start_node: str, end_node: str, weight_type: str = 'distance') -> Tuple[List[str], float]:
        """Find shortest path using Dijkstra's algorithm"""
        if start_node not in self.nodes or end_node not in self.nodes:
            return [], float('inf')
        
        # Initialize distances and previous nodes
        distances = {node: float('inf') for node in self.nodes.keys()}
        previous = {node: None for node in self.nodes.keys()}
        distances[start_node] = 0
        
        # Priority queue: (distance, node)
        pq = [(0, start_node)]
        visited = set()
        
        while pq:
            current_distance, current_node = heapq.heappop(pq)
            
            if current_node in visited:
                continue
                
            visited.add(current_node)
            
            if current_node == end_node:
                break
            
            # Check neighbors
            neighbors = self.connections[current_node] + [n for n, conns in self.connections.items() if current_node in conns]
            for neighbor in set(neighbors):  # Remove duplicates
                if neighbor not in visited and neighbor in self.nodes:
                    weight = self.get_edge_weight(current_node, neighbor, weight_type)
                    distance = current_distance + weight
                    
                    if distance < distances[neighbor]:
                        distances[neighbor] = distance
                        previous[neighbor] = current_node
                        heapq.heappush(pq, (distance, neighbor))
        
        # Reconstruct path
        if distances[end_node] == float('inf'):
            return [], float('inf')
        
        path = []
        current = end_node
        while current is not None:
            path.append(current)
            current = previous[current]
        path.reverse()
        
        return path, distances[end_node]
    
    def calculate_travel_time(self, path: List[str], vehicle_id: int) -> float:
        """Calculate travel time for a path using specific vehicle"""
        if len(path) < 2 or vehicle_id not in self.vehicles:
            return 0
        
        vehicle_speed = self.vehicles[vehicle_id]['speed']
        total_distance = 0
        
        for i in range(len(path) - 1):
            total_distance += self.get_edge_weight(path[i], path[i+1], 'distance')
        
        return total_distance / vehicle_speed
    
    def find_optimal_path(self, start_node: str, end_node: str, vehicle_id: int, priority: int = 1) -> Tuple[List[str], Dict]:
        """Find optimal path based on priority setting"""
        if priority == 1:  # Shortest Distance
            path, total_weight = self.dijkstra_shortest_path(start_node, end_node, 'distance')
            weight_type = 'distance'
        elif priority == 2:  # Lowest Carbon Emissions
            path, total_weight = self.dijkstra_shortest_path(start_node, end_node, 'carbon')
            weight_type = 'carbon'
        elif priority == 3:  # Lowest Cost
            path, total_weight = self.dijkstra_shortest_path(start_node, end_node, 'cost')
            weight_type = 'cost'
        elif priority == 4:  # Fastest Travel Time
            # For travel time optimization, we need to consider vehicle speed
            best_path = []
            best_time = float('inf')
            
            # Try all three weight types and calculate actual travel time
            for wt in ['distance', 'carbon', 'cost']:
                temp_path, _ = self.dijkstra_shortest_path(start_node, end_node, wt)
                if temp_path:
                    travel_time = self.calculate_travel_time(temp_path, vehicle_id)
                    if travel_time < best_time:
                        best_time = travel_time
                        best_path = temp_path
            
            path = best_path
            total_weight = best_time
            weight_type = 'time'
        else:
            # Default to shortest distance
            path, total_weight = self.dijkstra_shortest_path(start_node, end_node, 'distance')
            weight_type = 'distance'
        
        # Calculate all metrics for the chosen path
        if path and len(path) > 1:
            total_distance = sum(self.get_edge_weight(path[i], path[i+1], 'distance') for i in range(len(path)-1))
            total_carbon = sum(self.get_edge_weight(path[i], path[i+1], 'carbon') for i in range(len(path)-1))
            total_cost = sum(self.get_edge_weight(path[i], path[i+1], 'cost') for i in range(len(path)-1))
            travel_time = self.calculate_travel_time(path, vehicle_id)
            
            metrics = {
                'distance': total_distance,
                'carbon': total_carbon,
                'cost': total_cost,
                'time': travel_time,
                'optimized_for': weight_type,
                'priority': priority
            }
        else:
            metrics = {'distance': 0, 'carbon': 0, 'cost': 0, 'time': 0, 'optimized_for': weight_type, 'priority': priority}
        
        return path, metrics

# === Agent Storage Simulation ===
class AgentContext:
    """Simulates the agent context with storage and logger"""
    def __init__(self):
        self.storage = {}
        self.logger = Logger()
    
    def set_storage(self, key: str, value):
        """Simulate ctx.storage.set()"""
        self.storage[key] = value
    
    def get_storage(self, key: str, default=None):
        """Simulate ctx.storage.get()"""
        return self.storage.get(key, default)

class Logger:
    """Simple logger simulation"""
    def info(self, message: str):
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] INFO: {message}")
    
    def warning(self, message: str):
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] WARNING: {message}")
    
    def error(self, message: str):
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] ERROR: {message}")

class VehicleAgent:
    """Handles TCP communication with Digital Twin and intelligent routing decisions"""
    
    def __init__(self, vehicle_id: int, map_file_path: str = None, vehicles_file_path: str = None):
        self.vehicle_id = vehicle_id
        self.port = DT_BASE_PORT + (vehicle_id - 1)
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.connected = False
        
        # Initialize routing system with file paths
        self.routing_system = VehicleRoutingSystem(map_file_path, vehicles_file_path)
        
        # Agent context simulation
        self.ctx = AgentContext()
        
        # Initialize agent storage
        # Get vehicle's starting node from loaded data, default to Node1 if not found
        vehicle_start = "Node1"
        if vehicle_id in self.routing_system.vehicles:
            vehicle_start = self.routing_system.vehicles[vehicle_id].get('start_node', 'Node1')
        
        self.ctx.set_storage("state", "idle")
        self.ctx.set_storage("vehicle_number", vehicle_id)
        self.ctx.set_storage("progress", 0)
        self.ctx.set_storage("current_location", vehicle_start)
        self.ctx.set_storage("target_location", None)
        self.ctx.set_storage("final_destination", None)
        self.ctx.set_storage("planned_path", [])
        self.ctx.set_storage("current_path_index", 0)
        self.ctx.set_storage("x_position", 0)
        self.ctx.set_storage("y_position", 0)
        self.ctx.set_storage("mission_active", False)
        
        self.ctx.logger.info(f"Agent {vehicle_id} initialized with routing priority: {ROUTING_PRIORITY}")
        self.ctx.logger.info(f"Vehicle starting location: {vehicle_start}")
        if vehicle_id in self.routing_system.vehicles:
            speed = self.routing_system.vehicles[vehicle_id]['speed']
            self.ctx.logger.info(f"Vehicle speed: {speed} units/time")
        
        priority_names = {1: "Shortest Distance", 2: "Lowest Carbon", 3: "Lowest Cost", 4: "Fastest Time"}
        self.ctx.logger.info(f"Routing Priority: {priority_names.get(ROUTING_PRIORITY, 'Unknown')}")
        
        # Message handling
        self.pending_acks = {}
        self.ack_counter = 0
        
    async def connect(self):
        """Connect to the Digital Twin via TCP"""
        try:
            self.reader, self.writer = await asyncio.open_connection('127.0.0.1', self.port)
            self.connected = True
            self.ctx.logger.info(f"Connected to Digital Twin on port {self.port}")
            
            # Start listening for updates from Digital Twin
            asyncio.create_task(self.listen_for_updates())
            
        except Exception as e:
            self.ctx.logger.error(f"Failed to connect to Digital Twin: {e}")
            self.connected = False
            
    async def listen_for_updates(self):
        """Listen for processed data from Digital Twin"""
        try:
            while self.connected and self.reader:
                try:
                    data = await asyncio.wait_for(self.reader.readline(), timeout=30.0)
                except asyncio.TimeoutError:
                    continue
                    
                if not data:
                    self.ctx.logger.warning("Digital Twin disconnected")
                    self.connected = False
                    break
                    
                message = data.decode().strip()
                if not message:
                    continue
                    
                try:
                    response = json.loads(message)
                    
                    # Handle acknowledgments
                    if response.get("type") == "task_ack":
                        if self.pending_acks:
                            for event in self.pending_acks.values():
                                event.set()
                        self.ctx.logger.info(f"Task acknowledgment received: {response.get('status')}")
                        
                    # Handle processed vehicle data from Digital Twin    
                    elif response.get("type") == "vehicle_data":
                        await self.process_vehicle_data(response.get("data", {}))
                        
                except json.JSONDecodeError:
                    self.ctx.logger.warning(f"Received invalid JSON: {message}")
                    
        except Exception as e:
            self.ctx.logger.error(f"Listening error: {e}")
        finally:
            self.connected = False
            
    async def process_vehicle_data(self, data: dict):
        """Process vehicle data from Digital Twin and update agent storage"""
        # Update agent storage with processed data
        old_progress = self.ctx.get_storage("progress")
        new_progress = data.get("mission_progress", 0)
        old_location = self.ctx.get_storage("current_location")
        new_location = data.get("current_location", "Unknown")
        
        self.ctx.set_storage("progress", new_progress)
        self.ctx.set_storage("current_location", new_location)
        self.ctx.set_storage("target_location", data.get("target_location"))
        self.ctx.set_storage("x_position", data.get("x_position", 0))
        self.ctx.set_storage("y_position", data.get("y_position", 0))
        self.ctx.set_storage("last_location", data.get("previous_location"))
        
        # Check if we've reached a new waypoint
        if old_location != new_location:
            self.ctx.logger.info(f"Reached waypoint: {new_location}")
            await self.handle_waypoint_reached(new_location)
        
        # Log the data update
        self.ctx.logger.info(f"Vehicle data updated - Progress: {new_progress}%, "
                           f"Location: {new_location}, Target: {data.get('target_location')}")
        
        # Trigger decision making based on new data
        await self.make_decisions()
    
    async def handle_waypoint_reached(self, current_location: str):
        """Handle reaching a waypoint in the planned path"""
        planned_path = self.ctx.get_storage("planned_path")
        current_index = self.ctx.get_storage("current_path_index")
        
        if planned_path and current_index < len(planned_path):
            # Update path index
            if current_location == planned_path[current_index]:
                self.ctx.set_storage("current_path_index", current_index + 1)
                self.ctx.logger.info(f"Waypoint {current_index + 1}/{len(planned_path)} reached: {current_location}")
                
                # Check if we need to continue to the next waypoint
                next_index = current_index + 1
                if next_index < len(planned_path):
                    next_waypoint = planned_path[next_index]
                    self.ctx.logger.info(f"Proceeding to next waypoint: {next_waypoint}")
                    await self.send_mission(next_waypoint)
                else:
                    self.ctx.logger.info("Final destination reached!")
                    self.ctx.set_storage("mission_active", False)
                    self.ctx.set_storage("state", "mission_completed")
            
    async def send_mission(self, destination: str) -> bool:
        """Send mission assignment to Digital Twin"""
        if not self.connected or not self.writer:
            self.ctx.logger.error("Not connected to Digital Twin")
            return False
            
        try:
            # Create unique request ID and event for acknowledgment
            self.ack_counter += 1
            request_id = f"mission_{self.ack_counter}"
            ack_event = asyncio.Event()
            self.pending_acks[request_id] = ack_event
            
            request = {
                "type": "assign_mission",
                "destination": destination,
                "request_id": request_id
            }
            message = json.dumps(request) + "\n"
            self.writer.write(message.encode())
            await self.writer.drain()
            
            # Wait for acknowledgment
            try:
                await asyncio.wait_for(ack_event.wait(), timeout=5.0)
                self.ctx.logger.info(f"Mission to {destination} assigned successfully")
                return True
                    
            except asyncio.TimeoutError:
                self.ctx.logger.error("Mission assignment timeout")
                return False
            finally:
                self.pending_acks.pop(request_id, None)
                
        except Exception as e:
            self.ctx.logger.error(f"Mission assignment error: {e}")
            return False
    
    async def plan_and_execute_route(self, final_destination: str):
        """Plan optimal route and execute it step by step"""
        current_location = self.ctx.get_storage("current_location")
        
        self.ctx.logger.info(f"Planning route from {current_location} to {final_destination}")
        
        # Find optimal path using routing system
        path, metrics = self.routing_system.find_optimal_path(
            current_location, 
            final_destination, 
            self.vehicle_id, 
            ROUTING_PRIORITY
        )
        
        if not path or len(path) < 2:
            self.ctx.logger.error(f"No path found from {current_location} to {final_destination}")
            return False
        
        # Log route details
        self.ctx.logger.info(f"Optimal path found: {' → '.join(path)}")
        self.ctx.logger.info(f"Route metrics - Distance: {metrics['distance']:.1f}, "
                           f"Carbon: {metrics['carbon']:.1f}, Cost: {metrics['cost']:.1f}, "
                           f"Time: {metrics['time']:.2f}")
        self.ctx.logger.info(f"Optimized for: {metrics['optimized_for']}")
        
        # Store planned path
        self.ctx.set_storage("planned_path", path)
        self.ctx.set_storage("final_destination", final_destination)
        self.ctx.set_storage("current_path_index", 0)
        self.ctx.set_storage("mission_active", True)
        
        # Start with first waypoint (skip current location)
        if len(path) > 1:
            next_waypoint = path[1]
            self.ctx.logger.info(f"Starting route execution - first waypoint: {next_waypoint}")
            success = await self.send_mission(next_waypoint)
            if success:
                self.ctx.set_storage("state", "executing_route")
                self.ctx.set_storage("current_path_index", 1)
            return success
        
        return False
            
    async def make_decisions(self):
        """Enhanced decision making logic with dynamic routing"""
        current_state = self.ctx.get_storage("state")
        progress = self.ctx.get_storage("progress")
        current_location = self.ctx.get_storage("current_location")
        target_location = self.ctx.get_storage("target_location")
        mission_active = self.ctx.get_storage("mission_active")
        planned_path = self.ctx.get_storage("planned_path")
        final_destination = self.ctx.get_storage("final_destination")
        
        self.ctx.logger.info(f"Decision making - State: {current_state}, Progress: {progress}%, "
                           f"Location: {current_location}, Mission Active: {mission_active}")
        
        # Rule 1: Vehicle is idle and ready for new mission
        if current_state == "idle" and progress == 0:
            await self.assign_intelligent_mission()
            
        # Rule 2: Mission completed, ready for new mission
        elif current_state == "mission_completed" or (progress == 100 and not mission_active):
            self.ctx.set_storage("state", "idle")
            self.ctx.set_storage("progress", 0)
            await asyncio.sleep(2)  # Brief pause before next mission
            await self.assign_intelligent_mission()
            
        # Rule 3: Vehicle reached final destination
        elif (progress == 100 and current_location == final_destination and 
              planned_path and current_location == planned_path[-1]):
            self.ctx.logger.info(f"Successfully reached final destination: {final_destination}")
            self.ctx.set_storage("mission_active", False)
            self.ctx.set_storage("state", "mission_completed")
            
        # Rule 4: Vehicle is executing route
        elif current_state == "executing_route" and 0 < progress <= 100:
            self.ctx.logger.info(f"Executing route to {final_destination} ({progress}% to next waypoint)")
            
    async def assign_intelligent_mission(self):
        """Assign a new mission with intelligent routing"""
        # Select random destination from available nodes (avoid current location)
        available_destinations = list(self.routing_system.nodes.keys())
        current_location = self.ctx.get_storage("current_location")
        
        if current_location in available_destinations:
            available_destinations.remove(current_location)
        
        if not available_destinations:
            self.ctx.logger.error("No available destinations found")
            return
        
        destination = random.choice(available_destinations)
        
        self.ctx.logger.info(f"DECISION: Planning intelligent route to {destination}")
        
        success = await self.plan_and_execute_route(destination)
        if not success:
            self.ctx.logger.error("Failed to plan and execute route")
            
    async def disconnect(self):
        """Disconnect from Digital Twin"""
        self.connected = False
        if self.writer:
            try:
                self.writer.close()
                await self.writer.wait_closed()
            except:
                pass
        self.ctx.logger.info("Disconnected from Digital Twin")

# --- Main execution ---
async def main():
    priority_names = {1: "Shortest Distance", 2: "Lowest Carbon", 3: "Lowest Cost", 4: "Fastest Time"}
    print(f"🤖 Starting Intelligent Agent for Vehicle {vehicle_number}")
    print(f"🗺️  Routing Priority: {priority_names.get(ROUTING_PRIORITY, 'Unknown')} (Priority {ROUTING_PRIORITY})")
    
    # File paths - modify these paths as needed
    base_path = r"C:\Users\hhy26\OneDrive - University of Cambridge\Desktop\01_PhD\04_First_Year_Report\04_vehicle_simulator_0.1.2\vehicle_simulator"
    map_file = f"{base_path}\\map.txt"
    vehicles_file = f"{base_path}\\vehicles.txt"
    
    print(f"📁 Map file: {map_file}")
    print(f"🚗 Vehicles file: {vehicles_file}")
    
    # Create and connect vehicle agent with file paths
    agent = VehicleAgent(vehicle_number, map_file, vehicles_file)
    await agent.connect()
    
    if not agent.connected:
        print(f"❌ Failed to connect to Digital Twin for Vehicle {vehicle_number}")
        return
        
    # Wait for connection to stabilize
    await asyncio.sleep(2)
    
    agent.ctx.logger.info("Intelligent Agent operational - using dynamic routing from files")
    
    # Print network summary
    print(f"📊 Network loaded: {len(agent.routing_system.nodes)} nodes, {len(agent.routing_system.vehicles)} vehicles")
    
    # Make initial decision to get the vehicle started
    await agent.make_decisions()
    
    try:
        while True:
            if not agent.connected:
                agent.ctx.logger.warning("Digital Twin connection lost, exiting...")
                break
                
            # Main loop - the agent is reactive, decisions are made when data is received
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        agent.ctx.logger.info("Shutdown requested")
    finally:
        await agent.disconnect()
        agent.ctx.logger.info("Intelligent Agent shutdown complete")

if __name__ == "__main__":
    print(f"Vehicle number: {vehicle_number}")
    print(f"Routing priority: {ROUTING_PRIORITY}")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n👋 Intelligent Agent {vehicle_number} terminated")