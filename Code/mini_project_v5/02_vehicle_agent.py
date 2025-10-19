# 02_vehicle_agent.py
from uagents import Agent, Context, Protocol
from uagents.setup import fund_agent_if_low
from protocol import (
    CallForProposal,
    ProposalResponse,
    TaskAssignment,
    TaskAcceptance,
    TaskCompletion,
    NodeUpdate
)
import asyncio
import json
import sys
import time
from typing import Optional, List, Dict
from route import VehicleRoutingSystem

# === Import vehicle number ===
vehicle_number = int(sys.argv[1]) if len(sys.argv) > 1 else 1

# === Config (same as test_dt_2.py) ===
DT_BASE_PORT = 5000  # Digital Twin base port (vehicle1 → 5000, vehicle2 → 5001, etc.)
DT_HOST = "127.0.0.1"

# === ROUTING PRIORITY SETTING ===
# Change this value to set routing priority:
# 1 = Shortest Distance
# 2 = Lowest Carbon Emissions  
# 3 = Lowest Cost

ROUTING_PRIORITY = vehicle_number

# File paths - same as test_dt_2.py
MAP_FILE = r"C:\Users\hhy26\OneDrive - University of Cambridge\Desktop\01_PhD\04_First_Year_Report\00_vehicle_simulator_0.1.2\vehicle_simulator\map.txt"
VEHICLES_FILE = r"C:\Users\hhy26\OneDrive - University of Cambridge\Desktop\01_PhD\04_First_Year_Report\00_vehicle_simulator_0.1.2\vehicle_simulator\vehicles.txt"

# Manager address
MANAGER_ADDRESS = "agent1qfjcg2h5c2d2qkzksc8wntkpcyflntz0w8lsh2q6nwqpe6a2dn5ps88aqq3"

# Create vehicle agent
vehicle = Agent(
    name=f"vehicle{vehicle_number}",
    seed=f"vehicle {vehicle_number} recovery phrase",
    port=8000 + vehicle_number,  # 8001, 8002, ...
    endpoint=[f"http://localhost:{8000 + vehicle_number}/submit"]
)

# Create protocol
protocol = Protocol()

class VehicleState:
    def __init__(self, vehicle_id: int):
        self.vehicle_id = vehicle_id
        self.port = DT_BASE_PORT + (vehicle_id - 1)
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.connected = False
        
        # Initialize routing system
        self.routing_system = VehicleRoutingSystem(MAP_FILE, VEHICLES_FILE)
        
        # State variables
        self.current_node: str = None
        self.is_busy: bool = False
        self.current_task_id: Optional[str] = None
        self.planned_path: List[str] = []
        self.current_path_index: int = 0
        self.final_destination: Optional[str] = None
        self.progress: float = 0
        self.executing_full_path: bool = False
        self.waiting_for_completion: bool = False
        
        # Message handling
        self.pending_acks = {}
        self.ack_counter = 0
        
        # Initialize vehicle location from vehicles.txt
        self._initialize_location()
        
    def _initialize_location(self):
        """Initialize vehicle location from vehicles.txt"""
        if self.vehicle_id not in self.routing_system.vehicles:
            raise ValueError(f"Vehicle {self.vehicle_id} not found in vehicles file!")
            
        # Read starting position from vehicles.txt
        vehicle_start = self.routing_system.vehicles[self.vehicle_id].get('start_node')
        vehicle_speed = self.routing_system.vehicles[self.vehicle_id].get('speed')
        
        if not vehicle_start or vehicle_start not in self.routing_system.nodes:
            raise ValueError(f"Invalid start node '{vehicle_start}' for Vehicle {self.vehicle_id}")
        
        # Initialize vehicle location in routing system with start node from file
        self.routing_system.update_vehicle_location(self.vehicle_id, vehicle_start)
        self.current_node = vehicle_start
        
        print(f"[Vehicle {self.vehicle_id}] Initialized from vehicles.txt")
        print(f"  Starting location: {vehicle_start}")
        print(f"  Speed: {vehicle_speed} units/time")
        print(f"  Routing Priority: {ROUTING_PRIORITY}")

state = VehicleState(vehicle_number)

async def connect_to_dt():
    """Connect to the Digital Twin via TCP"""
    try:
        state.reader, state.writer = await asyncio.open_connection(DT_HOST, state.port)
        state.connected = True
        print(f"[Vehicle {vehicle_number}] Connected to Digital Twin on port {state.port}")
        
        # Start listening for updates from Digital Twin
        asyncio.create_task(listen_for_dt_updates())
        
    except Exception as e:
        print(f"[Vehicle {vehicle_number}] Failed to connect to Digital Twin: {e}")
        state.connected = False

async def listen_for_dt_updates():
    """Listen for processed data from Digital Twin"""
    try:
        while state.connected and state.reader:
            try:
                data = await asyncio.wait_for(state.reader.readline(), timeout=30.0)
            except asyncio.TimeoutError:
                continue
                
            if not data:
                print(f"[Vehicle {vehicle_number}] Digital Twin disconnected")
                state.connected = False
                break
                
            message = data.decode().strip()
            if not message:
                continue
                
            try:
                response = json.loads(message)
                
                # Handle acknowledgments
                if response.get("type") == "task_ack":
                    if state.pending_acks:
                        for event in state.pending_acks.values():
                            event.set()
                    print(f"[Vehicle {vehicle_number}] Task acknowledgment received")
                    
                # Handle processed vehicle data from Digital Twin    
                elif response.get("type") == "vehicle_data":
                    await process_vehicle_data(response.get("data", {}))
                    
            except json.JSONDecodeError:
                print(f"[Vehicle {vehicle_number}] Received invalid JSON: {message}")
                
    except Exception as e:
        print(f"[Vehicle {vehicle_number}] Listening error: {e}")
    finally:
        state.connected = False

async def process_vehicle_data(data: dict):
    """Process vehicle data from Digital Twin and update state"""
    print(f"[Vehicle {vehicle_number}] Data from Digital Twin: {json.dumps(data, indent=2)}")
    
    # Update state with processed data
    old_progress = state.progress
    new_progress = data.get("mission_progress", 0)
    old_location = state.current_node
    new_location = data.get("current_location", "Unknown")
    target = data.get("target_location")
    
    # Check for valid location updates
    if new_location != "Unknown" and new_location != old_location:
        # Update location in routing system
        if new_location in state.routing_system.nodes:
            state.routing_system.update_vehicle_location(state.vehicle_id, new_location)
            state.current_node = new_location
            print(f"[Vehicle {vehicle_number}] Reached waypoint: {new_location}")
            await handle_waypoint_reached(new_location)
    
    state.progress = new_progress
    
    # Check if we've completed the mission
    if new_progress == 100 and state.executing_full_path:
        if state.current_node == state.final_destination:
            print(f"[Vehicle {vehicle_number}] MISSION COMPLETED at {state.current_node}")
            await complete_current_task(success=True)

async def handle_waypoint_reached(current_location: str):
    """Handle reaching a waypoint in the planned path"""
    if not state.executing_full_path or not state.planned_path:
        return
        
    # Check if this is the final destination
    if current_location == state.final_destination:
        print(f"[Vehicle {vehicle_number}] FINAL DESTINATION REACHED: {current_location}")
        return
    
    # Find current location in the path
    try:
        actual_index = state.planned_path.index(current_location)
        
        # Update path index if we've progressed
        if actual_index >= state.current_path_index:
            state.current_path_index = actual_index
            
        print(f"[Vehicle {vehicle_number}] Waypoint {actual_index + 1}/{len(state.planned_path)} reached: {current_location}")
        
        # Continue to next waypoint
        next_index = actual_index + 1
        if next_index < len(state.planned_path):
            next_waypoint = state.planned_path[next_index]
            print(f"[Vehicle {vehicle_number}] Next waypoint: {next_waypoint}")
            
            success = await send_mission_to_dt(next_waypoint)
            if success:
                state.current_path_index = next_index
                state.waiting_for_completion = True
                
    except ValueError:
        print(f"[Vehicle {vehicle_number}] ERROR: Location {current_location} not in planned path")

async def send_mission_to_dt(destination: str) -> bool:
    """Send mission assignment to Digital Twin"""
    if not state.connected or not state.writer:
        print(f"[Vehicle {vehicle_number}] Not connected to Digital Twin")
        return False
        
    # Update routing system with target location
    state.routing_system.set_vehicle_target(state.vehicle_id, destination)
        
    try:
        # Create unique request ID and event for acknowledgment
        state.ack_counter += 1
        request_id = f"mission_{state.ack_counter}"
        ack_event = asyncio.Event()
        state.pending_acks[request_id] = ack_event
        
        request = {
            "type": "assign_mission",
            "destination": destination,
            "request_id": request_id
        }
        message = json.dumps(request) + "\n"
        state.writer.write(message.encode())
        await state.writer.drain()
        
        print(f"[Vehicle {vehicle_number}] Sending mission to DT: {destination}")
        
        # Wait for acknowledgment
        try:
            await asyncio.wait_for(ack_event.wait(), timeout=10.0)
            print(f"[Vehicle {vehicle_number}] Mission to {destination} assigned successfully")
            return True
                
        except asyncio.TimeoutError:
            print(f"[Vehicle {vehicle_number}] Mission assignment timeout")
            return False
        finally:
            state.pending_acks.pop(request_id, None)
            
    except Exception as e:
        print(f"[Vehicle {vehicle_number}] Mission assignment error: {e}")
        return False

async def plan_and_execute_route(destination: str) -> bool:
    """Plan optimal route and start execution"""
    
    # Use vehicle-specific routing
    optimal_path_data = state.routing_system.find_optimal_path_for_vehicle(
        state.vehicle_id,
        destination, 
        ROUTING_PRIORITY
    )
    
    if not optimal_path_data:
        print(f"[Vehicle {vehicle_number}] No optimal path found to {destination}")
        return False
    
    path = optimal_path_data['path']
    
    # Log route details
    print(f"[Vehicle {vehicle_number}] Optimal path: {' → '.join(path)}")
    print(f"  Distance: {optimal_path_data['distance']:.2f} units")
    print(f"  Carbon: {optimal_path_data['carbon']:.2f} kg CO2")
    print(f"  Cost: ${optimal_path_data['cost']:.2f}")
    print(f"  Travel Time: {optimal_path_data['travel_time']:.2f} time units")
    
    # Store planned path
    state.planned_path = path
    state.final_destination = destination
    state.current_path_index = 0
    state.executing_full_path = True
    
    # Start with first waypoint (skip current location)
    if len(path) > 1:
        next_waypoint = path[1]
        print(f"[Vehicle {vehicle_number}] Starting route execution - first waypoint: {next_waypoint}")
        success = await send_mission_to_dt(next_waypoint)
        
        if success:
            state.current_path_index = 1
            state.waiting_for_completion = True
            return True
    
    return False

async def complete_current_task(success: bool):
    """Complete the current task and notify manager"""
    if state.current_task_id:
        # Send completion to manager
        completion = TaskCompletion(
            task_id=state.current_task_id,
            vehicle_id=state.vehicle_id,
            final_node=state.current_node,
            success=success
        )
        
        # Get context to send message
        ctx = vehicle._ctx  # Access the agent's context
        if ctx:
            await ctx.send(MANAGER_ADDRESS, completion)
        
        # Reset state
        state.is_busy = False
        state.current_task_id = None
        state.planned_path = []
        state.current_path_index = 0
        state.final_destination = None
        state.executing_full_path = False
        state.waiting_for_completion = False
        state.progress = 0

@vehicle.on_event("startup")
async def startup(ctx: Context):
    """Initialize vehicle agent on startup"""
    # Store context for later use
    vehicle._ctx = ctx
    
    ctx.logger.info("="*60)
    ctx.logger.info(f"VEHICLE {vehicle_number} AGENT STARTED")
    ctx.logger.info("="*60)
    ctx.logger.info(f"Vehicle address: {vehicle.address}")
    ctx.logger.info(f"Protocol digest: {protocol.digest}")
    ctx.logger.info(f"Current location: {state.current_node}")
    ctx.logger.info(f"Speed: {state.routing_system.vehicles[vehicle_number]['speed']} units/time")
    
    priority_names = {1: "Shortest Distance", 2: "Lowest Carbon", 3: "Lowest Cost"}
    ctx.logger.info(f"Routing Priority: {priority_names.get(ROUTING_PRIORITY, 'Unknown')}")
    
    # Connect to Digital Twin
    await connect_to_dt()

@protocol.on_message(model=CallForProposal)
async def handle_cfp(ctx: Context, sender: str, msg: CallForProposal):
    """Handle call for proposal from manager"""
    
    ctx.logger.info(f"Received CFP for task {msg.task_id} to {msg.destination_node}")
    
    # Prepare response
    response = ProposalResponse(
        task_id=msg.task_id,
        vehicle_id=state.vehicle_id,
        is_busy=state.is_busy,
        current_node=state.current_node,
        estimated_time=None,
        planned_path=None,
        distance=None,
        carbon=None,
        cost=None
    )
    
    # If not busy, calculate estimated time
    if not state.is_busy:
        # Get optimal path
        optimal_path_data = state.routing_system.find_optimal_path_for_vehicle(
            state.vehicle_id,
            msg.destination_node,
            ROUTING_PRIORITY
        )
        
        if optimal_path_data:
            response.estimated_time = optimal_path_data['travel_time']
            response.planned_path = optimal_path_data['path']
            response.distance = optimal_path_data['distance']
            response.carbon = optimal_path_data['carbon']
            response.cost = optimal_path_data['cost']
            
            ctx.logger.info(f"Calculated path: {' → '.join(optimal_path_data['path'])}")
            ctx.logger.info(f"Estimated time: {optimal_path_data['travel_time']:.2f} time units")
    else:
        ctx.logger.info(f"Vehicle is busy with task {state.current_task_id}")
    
    # Send response to manager
    await ctx.send(MANAGER_ADDRESS, response)

@protocol.on_message(model=TaskAssignment)
async def handle_assignment(ctx: Context, sender: str, msg: TaskAssignment):
    """Handle task assignment from manager"""
    
    # Only accept if this assignment is for this vehicle and we're not busy
    if msg.vehicle_id != state.vehicle_id:
        return
    
    if state.is_busy:
        # Send rejection
        acceptance = TaskAcceptance(
            task_id=msg.task_id,
            vehicle_id=state.vehicle_id,
            accepted=False,
            planned_path=None
        )
        await ctx.send(MANAGER_ADDRESS, acceptance)
        return
    
    ctx.logger.info(f"Accepted task {msg.task_id} to go to {msg.destination_node}")
    
    # Accept the task
    state.is_busy = True
    state.current_task_id = msg.task_id
    
    # Start route execution
    success = await plan_and_execute_route(msg.destination_node)
    
    # Send acceptance
    acceptance = TaskAcceptance(
        task_id=msg.task_id,
        vehicle_id=state.vehicle_id,
        accepted=success,
        planned_path=state.planned_path if success else None
    )
    await ctx.send(MANAGER_ADDRESS, acceptance)
    
    if not success:
        # Reset if failed to start
        state.is_busy = False
        state.current_task_id = None

@vehicle.on_interval(period=5.0)
async def send_status_update(ctx: Context):
    """Send periodic status updates to manager"""
    if state.is_busy and state.current_task_id:
        # Send position update
        update = NodeUpdate(
            vehicle_id=state.vehicle_id,
            current_node=state.current_node,
            progress=state.progress
        )
        await ctx.send(MANAGER_ADDRESS, update)

# Include protocol in agent
vehicle.include(protocol)

if __name__ == "__main__":
    print(f"Starting Vehicle {vehicle_number} Agent...")
    print(f"Digital Twin TCP port: {DT_BASE_PORT + (vehicle_number - 1)}")
    print(f"Agent port: {8000 + vehicle_number}")
    print(f"Map file: {MAP_FILE}")
    print(f"Vehicles file: {VEHICLES_FILE}")
    priority_names = {1: "Shortest Distance", 2: "Lowest Carbon", 3: "Lowest Cost"}
    print(f"Routing Priority: {priority_names.get(ROUTING_PRIORITY, 'Unknown')}")
    vehicle.run()