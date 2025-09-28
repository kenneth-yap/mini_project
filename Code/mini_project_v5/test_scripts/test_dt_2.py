import asyncio
import json
import random
import time
import sys
from typing import Optional, Dict, List
from route import VehicleRoutingSystem

# === Import vehicle number ===
vehicle_number = int(sys.argv[1]) if len(sys.argv) > 1 else 1

# === Config ===
DT_BASE_PORT = 5000  # Digital Twin base port (vehicle1 → 5000, vehicle2 → 5001, etc.)

# === ROUTING PRIORITY SETTING ===
# Change this value to set routing priority:
# 1 = Shortest Distance
# 2 = Lowest Carbon Emissions  
# 3 = Lowest Cost

ROUTING_PRIORITY = vehicle_number

# File paths - modify these paths as needed
MAP_FILE = r"C:\Users\hhy26\OneDrive - University of Cambridge\Desktop\01_PhD\04_First_Year_Report\04_vehicle_simulator_0.1.2\vehicle_simulator\map.txt"
VEHICLES_FILE = r"C:\Users\hhy26\OneDrive - University of Cambridge\Desktop\01_PhD\04_First_Year_Report\04_vehicle_simulator_0.1.2\vehicle_simulator\vehicles.txt"

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
    
    def __init__(self, vehicle_id: int):
        self.vehicle_id = vehicle_id
        self.port = DT_BASE_PORT + (vehicle_id - 1)
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.connected = False
        
        # Initialize routing system
        try:
            self.routing_system = VehicleRoutingSystem(MAP_FILE, VEHICLES_FILE)
            self.ctx = AgentContext()
            self._initialize_agent()
        except Exception as e:
            print(f"❌ Failed to initialize routing system: {e}")
            raise
        
    def _initialize_agent(self):
        """Initialize agent storage and settings - uses start node from vehicles.txt ONLY at startup"""
        # Get vehicle's starting node from loaded data
        if self.vehicle_id not in self.routing_system.vehicles:
            error_msg = f"CRITICAL ERROR: Vehicle {self.vehicle_id} not found in vehicles file!"
            self.ctx.logger.error(error_msg)
            self.ctx.logger.error(f"Available vehicles: {list(self.routing_system.vehicles.keys())}")
            raise ValueError(error_msg)
        
        # Read starting position from vehicles.txt (ONLY used at initialization)
        vehicle_start = self.routing_system.vehicles[self.vehicle_id].get('start_node')
        vehicle_speed = self.routing_system.vehicles[self.vehicle_id].get('speed')
        
        if not vehicle_start or vehicle_start not in self.routing_system.nodes:
            error_msg = f"CRITICAL ERROR: Invalid start node '{vehicle_start}' for Vehicle {self.vehicle_id}"
            self.ctx.logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Initialize vehicle location in routing system with start node from file
        self.routing_system.update_vehicle_location(self.vehicle_id, vehicle_start)
        
        self.ctx.logger.info(f"Vehicle {self.vehicle_id} initialized from vehicles.txt")
        self.ctx.logger.info(f"  Starting location: {vehicle_start}")
        self.ctx.logger.info(f"  Speed: {vehicle_speed} units/time")
        self.ctx.logger.info(f"  NOTE: After first movement, location will be tracked from Digital Twin")
        
        self.ctx.set_storage("state", "idle")
        self.ctx.set_storage("vehicle_number", self.vehicle_id)
        self.ctx.set_storage("progress", 0)
        self.ctx.set_storage("current_location", vehicle_start)
        self.ctx.set_storage("target_location", None)
        self.ctx.set_storage("final_destination", None)
        self.ctx.set_storage("planned_path", [])
        self.ctx.set_storage("current_path_index", 0)
        self.ctx.set_storage("x_position", 0)
        self.ctx.set_storage("y_position", 0)
        self.ctx.set_storage("mission_active", False)
        self.ctx.set_storage("executing_full_path", False)
        self.ctx.set_storage("waiting_for_completion", False)
        self.ctx.set_storage("initialized_from_file", True)  # Flag to track initialization
        
        # Message handling
        self.pending_acks = {}
        self.ack_counter = 0
        
        # Log initialization with vehicle verification
        self.ctx.logger.info(f"Agent {self.vehicle_id} initialized with routing priority: {ROUTING_PRIORITY}")
        
        priority_names = {1: "Shortest Distance", 2: "Lowest Carbon", 3: "Lowest Cost", 4: "Fastest Time"}
        self.ctx.logger.info(f"Routing Priority: {priority_names.get(ROUTING_PRIORITY, 'Unknown')}")
        
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
        # Log raw data from Digital Twin for debugging
        self.ctx.logger.info(f"RAW DATA FROM DIGITAL TWIN: {json.dumps(data, indent=2)}")
        
        # Update agent storage with processed data
        old_progress = self.ctx.get_storage("progress")
        new_progress = data.get("mission_progress", 0)
        old_location = self.ctx.get_storage("current_location")
        new_location = data.get("current_location", "Unknown")
        target = data.get("target_location")
        
        # WORKAROUND: Detect and ignore spurious intermediate locations from buggy Digital Twin
        planned_path = self.ctx.get_storage("planned_path")
        if planned_path and len(planned_path) >= 2:
            # If we get a location that's not in our planned path, and progress is advancing
            if new_location not in planned_path and new_progress > old_progress:
                self.ctx.logger.warning(f"Digital Twin reported location '{new_location}' not in planned path {planned_path}")
                self.ctx.logger.warning(f"This appears to be incorrect data from Digital Twin - IGNORING this update")
                
                # Check if target is in the path - if so, assume we're still heading there
                if target and target in planned_path:
                    self.ctx.logger.info(f"Target {target} is in planned path - continuing with existing path")
                    return  # Skip this update entirely
        
        # Detect impossible backward movement
        if old_location != new_location and old_location in self.routing_system.nodes and new_location in self.routing_system.nodes:
            if planned_path and old_location in planned_path and new_location in planned_path:
                old_index = planned_path.index(old_location)
                new_index = planned_path.index(new_location)
                if new_index < old_index:
                    self.ctx.logger.error(f"BACKWARD MOVEMENT DETECTED: {old_location} → {new_location}")
                    self.ctx.logger.error(f"This suggests Digital Twin sent stale/incorrect data")
                    self.ctx.logger.warning(f"Planned path was: {' → '.join(planned_path)}")
                    self.ctx.logger.warning(f"IGNORING this backward movement")
                    return  # Skip this update
        
        self.ctx.set_storage("progress", new_progress)
        self.ctx.set_storage("current_location", new_location)
        self.ctx.set_storage("target_location", target)
        self.ctx.set_storage("x_position", data.get("x_position", 0))
        self.ctx.set_storage("y_position", data.get("y_position", 0))
        self.ctx.set_storage("last_location", data.get("previous_location"))
        
        # IMPORTANT: Update the routing system with current vehicle location
        if new_location != "Unknown" and new_location in self.routing_system.nodes:
            self.routing_system.update_vehicle_location(self.vehicle_id, new_location)
        
        # Recovery: If vehicle is moving but we have no planned path, reconstruct it
        if target and not planned_path and old_location != new_location:
            self.ctx.logger.warning(f"Vehicle moving to {target} but no planned path exists (late acknowledgment?)")
            self.ctx.logger.info(f"Reconstructing path state for mission to {target}")
            
            # Reconstruct minimal path state
            self.ctx.set_storage("planned_path", [old_location, target])
            self.ctx.set_storage("final_destination", target)
            self.ctx.set_storage("executing_full_path", True)
            self.ctx.set_storage("mission_active", True)
            self.ctx.set_storage("state", "executing_route")
        
        # Check if we've reached a new waypoint
        if old_location != new_location:
            self.ctx.logger.info(f"Reached waypoint: {new_location}")
            await self.handle_waypoint_reached(new_location)
        
        # Log the data update
        self.ctx.logger.info(f"Vehicle data updated - Progress: {new_progress}%, "
                           f"Location: {new_location}, Target: {target}")
        
        # Trigger decision making based on new data
        await self.make_decisions()
    
    async def handle_waypoint_reached(self, current_location: str):
        """Handle reaching a waypoint in the planned path - ENSURE COMPLETE PATH EXECUTION"""
        planned_path = self.ctx.get_storage("planned_path")
        current_index = self.ctx.get_storage("current_path_index")
        executing_full_path = self.ctx.get_storage("executing_full_path")
        final_destination = self.ctx.get_storage("final_destination")
        
        # Check if this is the final destination (even without active execution)
        if current_location == final_destination and planned_path and current_location == planned_path[-1]:
            self.ctx.logger.info(f"FINAL DESTINATION REACHED: {current_location} (even after timeout)")
            self.ctx.set_storage("mission_active", False)
            self.ctx.set_storage("executing_full_path", False)
            self.ctx.set_storage("waiting_for_completion", False)
            self.ctx.set_storage("state", "mission_completed")
            self.ctx.set_storage("progress", 100)
            return
        
        if not executing_full_path or not planned_path:
            self.ctx.logger.warning("Waypoint reached but no active path execution")
            return
            
        # Find current location in the path
        try:
            actual_index = planned_path.index(current_location)
            
            # Update path index if we've progressed
            if actual_index >= current_index:
                self.ctx.set_storage("current_path_index", actual_index)
                current_index = actual_index
                
            self.ctx.logger.info(f"=== WAYPOINT {actual_index + 1}/{len(planned_path)} REACHED: {current_location} ===")
            
            # Check if this is the final destination
            if actual_index == len(planned_path) - 1:
                self.ctx.logger.info("FINAL DESTINATION REACHED! Path execution complete.")
                self.ctx.set_storage("mission_active", False)
                self.ctx.set_storage("executing_full_path", False)
                self.ctx.set_storage("waiting_for_completion", False)
                self.ctx.set_storage("state", "mission_completed")
                self.ctx.set_storage("progress", 100)
                return
            
            # Continue to next waypoint
            next_index = actual_index + 1
            if next_index < len(planned_path):
                next_waypoint = planned_path[next_index]
                self.ctx.logger.info(f">>> CONTINUING PATH: Next waypoint {next_index + 1}/{len(planned_path)}: {next_waypoint}")
                
                # Mark that we're waiting for this waypoint to complete
                self.ctx.set_storage("waiting_for_completion", True)
                
                success = await self.send_mission(next_waypoint)
                if success:
                    self.ctx.set_storage("current_path_index", next_index)
                else:
                    self.ctx.logger.error(f"CRITICAL: Failed to send mission to waypoint {next_waypoint}")
                    # Keep execution flags - Digital Twin might still accept
                    self.ctx.logger.warning("Keeping execution state - Digital Twin may accept mission")
                
        except ValueError:
            # Current location not in planned path - this shouldn't happen
            self.ctx.logger.error(f"CRITICAL ERROR: Current location {current_location} not found in planned path {planned_path}")
            self.ctx.set_storage("executing_full_path", False)
            self.ctx.set_storage("waiting_for_completion", False)
            
    async def send_mission(self, destination: str) -> bool:
        """Send mission assignment to Digital Twin"""
        if not self.connected or not self.writer:
            self.ctx.logger.error("Not connected to Digital Twin")
            return False
            
        # IMPORTANT: Update routing system with target location
        self.routing_system.set_vehicle_target(self.vehicle_id, destination)
            
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
            
            # Wait for acknowledgment with longer timeout
            try:
                await asyncio.wait_for(ack_event.wait(), timeout=10.0)  # Increased from 5 to 10 seconds
                self.ctx.logger.info(f"Mission to {destination} assigned successfully")
                return True
                    
            except asyncio.TimeoutError:
                self.ctx.logger.error(f"Mission assignment timeout after 10 seconds")
                # Check if Digital Twin might still process it
                self.ctx.logger.warning("Mission may still be accepted by Digital Twin - monitoring state")
                return False
            finally:
                self.pending_acks.pop(request_id, None)
                
        except Exception as e:
            self.ctx.logger.error(f"Mission assignment error: {e}")
            return False
    
    async def show_vehicle_comparison_for_route(self, final_destination: str):
        """Show how all vehicles would perform on this route"""
        current_location = self.ctx.get_storage("current_location")
        
        self.ctx.logger.info(f"Comparing all vehicles for route: {current_location} → {final_destination}")
        
        # Get comprehensive vehicle analysis
        try:
            all_vehicle_routes = self.routing_system.get_all_vehicle_times_for_route(current_location, final_destination)
            
            if not all_vehicle_routes:
                self.ctx.logger.warning("No route data available for comparison")
                return
            
            # Show comparison for each path type
            for criterion, route_data in all_vehicle_routes.items():
                if not route_data or 'path' not in route_data:
                    continue
                    
                self.ctx.logger.info(f"\n{criterion.upper()} PATH: {' → '.join(route_data['path'])}")
                self.ctx.logger.info(f"   Distance: {route_data.get('distance', 0):.1f}, "
                                   f"Carbon: {route_data.get('carbon', 0):.1f}, Cost: {route_data.get('cost', 0):.1f}")
                
                # Find fastest and slowest vehicles for this path
                vehicle_times = route_data.get('vehicle_times', {})
                if vehicle_times:
                    fastest = min(vehicle_times.items(), key=lambda x: x[1]['travel_time'])
                    slowest = max(vehicle_times.items(), key=lambda x: x[1]['travel_time'])
                    
                    self.ctx.logger.info(f"   Fastest: Vehicle {fastest[0]} ({fastest[1]['travel_time']:.1f}s, speed: {fastest[1]['speed']})")
                    self.ctx.logger.info(f"   Slowest: Vehicle {slowest[0]} ({slowest[1]['travel_time']:.1f}s, speed: {slowest[1]['speed']})")
                    
                    # Show current vehicle performance
                    if self.vehicle_id in vehicle_times:
                        current_vehicle = vehicle_times[self.vehicle_id]
                        rank = sorted(vehicle_times.keys(), key=lambda v: vehicle_times[v]['travel_time']).index(self.vehicle_id) + 1
                        self.ctx.logger.info(f"   Vehicle {self.vehicle_id}: {current_vehicle['travel_time']:.1f}s "
                                           f"(rank: {rank}/{len(vehicle_times)})")
                                           
        except Exception as e:
            self.ctx.logger.error(f"Error in vehicle comparison: {e}")
            import traceback
            self.ctx.logger.error(f"Traceback: {traceback.format_exc()}")

    async def plan_and_execute_full_route(self, final_destination: str):
        """Plan optimal route based on priority and execute it node by node using vehicle-specific routing"""
        
        # Show vehicle comparison first
        await self.show_vehicle_comparison_for_route(final_destination)
        
        # Use the new vehicle-specific routing method
        optimal_path_data = self.routing_system.find_optimal_path_for_vehicle(
            self.vehicle_id,
            final_destination, 
            ROUTING_PRIORITY
        )
        
        if not optimal_path_data:
            self.ctx.logger.error(f"No optimal path found for Vehicle {self.vehicle_id} to {final_destination}")
            return False
        
        path = optimal_path_data['path']
        current_location = self.ctx.get_storage("current_location")
        
        # Verify path starts with current location
        if path[0] != current_location:
            self.ctx.logger.warning(f"Path starts with {path[0]} but vehicle is at {current_location}")
            self.ctx.logger.info(f"This may be due to location tracking - proceeding with planned path")
        
        # Log route details with vehicle-specific information
        vehicle_status = self.routing_system.get_vehicle_status(self.vehicle_id)
        self.ctx.logger.info(f"Optimal path selected for Vehicle {self.vehicle_id}: {' → '.join(path)}")
        self.ctx.logger.info(f"Vehicle {self.vehicle_id} route metrics:")
        self.ctx.logger.info(f"   Distance: {optimal_path_data['distance']:.2f} units")
        self.ctx.logger.info(f"   Carbon: {optimal_path_data['carbon']:.2f} kg CO2")
        self.ctx.logger.info(f"   Cost: ${optimal_path_data['cost']:.2f}")
        self.ctx.logger.info(f"   Travel Time: {optimal_path_data['travel_time']:.2f} time units")
        self.ctx.logger.info(f"   Optimized for: {optimal_path_data['criterion']}")
        self.ctx.logger.info(f"   Vehicle Speed: {vehicle_status['speed']} units/time")
        self.ctx.logger.info(f"   Location tracked: {vehicle_status['location_tracked']}")
        
        # Store planned path BEFORE sending mission (important for recovery)
        self.ctx.set_storage("planned_path", path)
        self.ctx.set_storage("final_destination", final_destination)
        self.ctx.set_storage("current_path_index", 0)
        self.ctx.set_storage("mission_active", True)
        self.ctx.set_storage("executing_full_path", True)
        
        # Start with first waypoint (skip current location since we're already there)
        if len(path) > 1:
            next_waypoint = path[1]
            self.ctx.logger.info(f"Starting route execution - first waypoint: {next_waypoint}")
            success = await self.send_mission(next_waypoint)
            
            if not success:
                self.ctx.logger.warning("Mission send returned False (timeout or error)")
                self.ctx.logger.info("Keeping planned path in case Digital Twin accepted mission anyway")
                # Don't clear the path - let process_vehicle_data handle recovery
                self.ctx.set_storage("waiting_for_completion", True)  # Still wait for completion
                return True  # Consider it potentially successful
            else:
                self.ctx.set_storage("state", "executing_route")
                self.ctx.set_storage("current_path_index", 1)
                self.ctx.set_storage("waiting_for_completion", True)
                return True
        
        return False

    async def assign_intelligent_mission(self):
        """Assign a new mission with intelligent routing using current location and vehicle ID"""
        # Get available destinations from routing system
        available_destinations = list(self.routing_system.nodes.keys())
        current_location = self.ctx.get_storage("current_location")
        
        # Remove current location from destinations
        if current_location in available_destinations:
            available_destinations.remove(current_location)
        
        if not available_destinations:
            self.ctx.logger.error("No available destinations found")
            return
        
        destination = random.choice(available_destinations)
        
        # Get and log vehicle status from routing system
        vehicle_status = self.routing_system.get_vehicle_status(self.vehicle_id)
        
        self.ctx.logger.info(f"Vehicle {self.vehicle_id} status:")
        self.ctx.logger.info(f"   Current location: {vehicle_status['current_location']}")
        self.ctx.logger.info(f"   Target destination: {destination}")
        self.ctx.logger.info(f"   Vehicle speed: {vehicle_status['speed']}")
        self.ctx.logger.info(f"   Location tracking: {vehicle_status['location_tracked']}")
        self.ctx.logger.info(f"   Start node from file: {vehicle_status['start_node_from_file']}")
        
        self.ctx.logger.info(f"DECISION: Planning intelligent route for Vehicle {self.vehicle_id} to {destination}")
        
        success = await self.plan_and_execute_full_route(destination)
        if not success:
            self.ctx.logger.error("Failed to plan and execute route")
            
    async def make_decisions(self):
        """Enhanced decision making logic - PREVENTS PREMATURE MISSION ASSIGNMENT"""
        current_state = self.ctx.get_storage("state")
        progress = self.ctx.get_storage("progress")
        current_location = self.ctx.get_storage("current_location")
        target_location = self.ctx.get_storage("target_location")
        mission_active = self.ctx.get_storage("mission_active")
        executing_full_path = self.ctx.get_storage("executing_full_path")
        waiting_for_completion = self.ctx.get_storage("waiting_for_completion")
        planned_path = self.ctx.get_storage("planned_path")
        final_destination = self.ctx.get_storage("final_destination")
        
        self.ctx.logger.info(f"Decision Check - State: {current_state}, Progress: {progress}%, "
                           f"Executing: {executing_full_path}, Waiting: {waiting_for_completion}")
        
        # CRITICAL: Do NOT assign new missions if path is being executed
        if executing_full_path or waiting_for_completion:
            self.ctx.logger.info("Path execution in progress - blocking new mission assignment")
            return
        
        # Rule 1: Vehicle is idle and ready for new mission (progress must be 0 or 100 with no active mission)
        if current_state == "idle" and (progress == 0 or (progress == 100 and not mission_active)):
            self.ctx.logger.info("Vehicle idle - assigning new mission")
            await self.assign_intelligent_mission()
            
        # Rule 2: Mission completed, ready for new mission
        elif current_state == "mission_completed":
            self.ctx.logger.info("Mission completed - preparing for new mission")
            self.ctx.set_storage("state", "idle")
            self.ctx.set_storage("progress", 0)
            self.ctx.set_storage("planned_path", [])
            self.ctx.set_storage("current_path_index", 0)
            self.ctx.set_storage("mission_active", False)
            self.ctx.set_storage("executing_full_path", False)
            self.ctx.set_storage("waiting_for_completion", False)
            await asyncio.sleep(3)  # Longer pause to ensure clean state
            await self.assign_intelligent_mission()
            
        # Rule 3: Check if we've truly completed the full path
        elif progress == 100 and not mission_active and not executing_full_path:
            if planned_path and current_location == planned_path[-1]:
                self.ctx.logger.info(f"Confirmed completion at final destination: {current_location}")
                self.ctx.set_storage("state", "mission_completed")
            elif not planned_path:
                # No planned path but progress is 100% - likely just finished, assign new mission
                self.ctx.logger.info("Progress 100% with no planned path - ready for new mission")
                self.ctx.set_storage("state", "idle")
                self.ctx.set_storage("progress", 0)
                await self.assign_intelligent_mission()
            else:
                self.ctx.logger.warning(f"Progress 100% but location mismatch. Current: {current_location}, Expected: {planned_path[-1] if planned_path else 'None'}")
        
        # Rule 4: Vehicle is executing planned route
        elif current_state == "executing_route" and executing_full_path:
            if planned_path:
                current_index = self.ctx.get_storage("current_path_index")
                total_waypoints = len(planned_path)
                self.ctx.logger.info(f"Route execution: Waypoint {current_index}/{total_waypoints-1}, Progress: {progress}%")
            else:
                self.ctx.logger.error("CRITICAL: Executing route but no planned path!")
                self.ctx.set_storage("executing_full_path", False)
                self.ctx.set_storage("state", "idle")
            
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
    print(f"Starting Intelligent Agent for Vehicle {vehicle_number}")
    print(f"Routing Priority: {priority_names.get(ROUTING_PRIORITY, 'Unknown')} (Priority {ROUTING_PRIORITY})")
    
    print(f"Map file: {MAP_FILE}")
    print(f"Vehicles file: {VEHICLES_FILE}")
    
    try:
        # Create and connect vehicle agent
        # NOTE: Vehicle starts at location specified in vehicles.txt
        # After first movement, location is tracked from Digital Twin updates
        agent = VehicleAgent(vehicle_number)
        
        # Verify agent initialization
        print(f"Network loaded: {len(agent.routing_system.nodes)} nodes")
        print(f"Vehicles loaded: {len(agent.routing_system.vehicles)} vehicles")
        
        # Verify vehicle data and show status
        vehicle_status = agent.routing_system.get_vehicle_status(vehicle_number)
        if "error" not in vehicle_status:
            print(f"Vehicle {vehicle_number} initialization:")
            print(f"   Initial location (from vehicles.txt): {vehicle_status['start_node_from_file']}")
            print(f"   Speed: {vehicle_status['speed']} units/time")
            print(f"   Location tracking active: {vehicle_status['location_tracked']}")
        else:
            print(f"{vehicle_status['error']}")
            print(f"Available vehicles: {list(agent.routing_system.vehicles.keys())}")
            return
        
        await agent.connect()
        
        if not agent.connected:
            print(f"Failed to connect to Digital Twin for Vehicle {vehicle_number}")
            return
            
        # Wait for connection to stabilize
        await asyncio.sleep(2)
        
        agent.ctx.logger.info("Intelligent Agent operational - using vehicle-specific dynamic routing")
        agent.ctx.logger.info(f"Agent will track real-time location from Digital Twin")
        agent.ctx.logger.info(f"Vehicle {vehicle_number}-specific speed will be used for time calculations")
        agent.ctx.logger.info(f"Routing system will use current location for all path planning")
        
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
            
    except Exception as e:
        print(f"Failed to initialize agent: {e}")
        print("Please check that map.txt and vehicles.txt files exist and are properly formatted")

if __name__ == "__main__":
    print(f"Vehicle number: {vehicle_number}")
    print(f"Routing priority: {ROUTING_PRIORITY}")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\nIntelligent Agent {vehicle_number} terminated")