# 01_manager.py
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
import random
import time
import uuid
import os
import glob
from typing import Dict, List, Optional

# Clean up any corrupted storage files before starting
def cleanup_old_storage():
    """Remove any corrupted storage files from previous runs"""
    try:
        # Look for agent storage files
        for file in glob.glob("agent1q*.json"):
            try:
                os.remove(file)
                print(f"Cleaned up old storage: {file}")
            except:
                pass
        for file in glob.glob(".agent_storage*"):
            try:
                os.remove(file)
                print(f"Cleaned up old storage: {file}")
            except:
                pass
    except Exception as e:
        print(f"Storage cleanup warning: {e}")

# Clean storage before creating agent
cleanup_old_storage()

# File path for map
MAP_FILE = r"C:\Users\hhy26\OneDrive - University of Cambridge\Desktop\01_PhD\04_First_Year_Report\04_vehicle_simulator_0.1.2\vehicle_simulator\map.txt"

def load_nodes_from_map(map_file_path: str) -> List[str]:
    """Load all node names from the map.txt file"""
    nodes = []
    try:
        with open(map_file_path, 'r') as file:
            print(f"Loading nodes from: {map_file_path}")
            for line in file:
                line = line.strip()
                if line:
                    # Parse the format: {{"Node1", {250,50}},["Node2","Node3","Node4","Node5","Node6"]}.
                    # Find the node name (between first two quotes)
                    node_start = line.find('"') + 1
                    if node_start > 0:
                        node_end = line.find('"', node_start)
                        if node_end > node_start:
                            node_name = line[node_start:node_end]
                            nodes.append(node_name)
                            print(f"  Found node: {node_name}")
        
        print(f"Loaded {len(nodes)} nodes from map file")
        return nodes
    
    except FileNotFoundError:
        print(f"WARNING: Map file not found at {map_file_path}")
        print("Using default node list instead")
        # Return default nodes if file not found
        return ["Node2", "Node3", "Node4", "Node5", "Node6", "Node7", "Node8"]

    except Exception as e:
        print(f"Error reading map file: {e}")
        print("Using default node list instead")
        return ["Node2", "Node3", "Node4", "Node5", "Node6", "Node7", "Node8"]

# Load nodes from map file
ALL_NODES = load_nodes_from_map(MAP_FILE)

# Remove Node1 from destinations (assuming vehicles start there)
DESTINATION_NODES = [node for node in ALL_NODES if node != "Node1"]
print(f"Available destination nodes: {DESTINATION_NODES}")
print(f"Total destination nodes: {len(DESTINATION_NODES)}")

# Manager configuration
MANAGER_PORT = 8000
MANAGER_SEED = "manager recovery phrase"

# Vehicle agent addresses - these will be shown when you run the vehicle agents
VEHICLE_ADDRESSES = {
    1: 'agent1q03ndjvw6z8ke3h80x0f6mezwnhxrxapwzlfmgwrr7kzneucef9lzdqqxp6',
    2: 'agent1qtazd65qr6ss3g2l4h0m04q5g7kj8y4fwf4f989tyxntd2mgnyr7wrgzy6d',
    3: 'agent1q0lw72pj974rt4z5ea29zxqm32mpcjwqyexj6mwx8mady6l8ueafkxzvzr2',
}

try:
    # Create manager agent
    manager = Agent(
        name="manager",
        seed=MANAGER_SEED,
        port=MANAGER_PORT,
        endpoint=[f"http://localhost:{MANAGER_PORT}/submit"]
    )
    print(f"Manager agent created successfully")
    print(f"Manager address: {manager.address}")
    print("="*60)
    print("IMPORTANT: Copy this address to your vehicle agents!")
    print("="*60)
except Exception as e:
    print(f"Error creating manager agent: {e}")
    print("Try deleting any .json files in the current directory and run again")
    exit(1)

# Create protocol
protocol = Protocol()

# Manager state
class ManagerState:
    def __init__(self):
        self.current_task_id: Optional[str] = None
        self.current_destination: Optional[str] = None
        self.proposals: Dict[int, ProposalResponse] = {}
        self.active_assignments: Dict[str, Dict] = {}
        self.completed_tasks: List[str] = []
        self.last_cfp_time: float = 0
        self.awaiting_responses: bool = False
        self.response_timeout: float = 5.0
        self.vehicle_addresses = VEHICLE_ADDRESSES

state = ManagerState()

@manager.on_event("startup")
async def startup(ctx: Context):
    """Initialize manager on startup"""
    ctx.logger.info("="*60)
    ctx.logger.info("MANAGER AGENT STARTED")
    ctx.logger.info("="*60)
    ctx.logger.info(f"Manager address: {manager.address}")
    ctx.logger.info(f"Protocol digest: {protocol.digest}")
    ctx.logger.info(f"Map file: {MAP_FILE}")
    ctx.logger.info(f"Loaded {len(ALL_NODES)} nodes from map")
    ctx.logger.info(f"Available destinations: {len(DESTINATION_NODES)} nodes")
    ctx.logger.info(f"Monitoring {len(VEHICLE_ADDRESSES)} vehicles")
    
    # Initialize storage
    ctx.storage.set("state", "idle")
    ctx.storage.set("current_task_id", None)
    ctx.storage.set("proposals", {})
    ctx.storage.set("active_assignments", {})
    ctx.storage.set("completed_tasks", [])
    ctx.storage.set("awaiting_responses", False)

@manager.on_interval(period=15.0)
async def send_call_for_proposal(ctx: Context):
    """Send out call for proposal every 20 seconds"""
    
    # Check if we're still waiting for responses
    awaiting = ctx.storage.get("awaiting_responses")
    if awaiting:
        ctx.logger.info("Still awaiting responses from previous CFP")
        return
    
    # Check if we have destination nodes
    if not DESTINATION_NODES:
        ctx.logger.error("No destination nodes available!")
        return
    
    # Generate new task
    task_id = str(uuid.uuid4())[:8]
    destination = random.choice(DESTINATION_NODES)
    
    ctx.storage.set("current_task_id", task_id)
    ctx.storage.set("current_destination", destination)
    ctx.storage.set("proposals", {})
    ctx.storage.set("awaiting_responses", True)
    ctx.storage.set("last_cfp_time", time.time())
    
    cfp = CallForProposal(
        destination_node=destination,
        task_id=task_id
    )
    
    ctx.logger.info("="*60)
    ctx.logger.info(f"SENDING CFP - Task ID: {task_id}")
    ctx.logger.info(f"Destination: {destination}")
    ctx.logger.info("="*60)
    
    # Send to all vehicles
    for vehicle_id, address in VEHICLE_ADDRESSES.items():
        ctx.logger.info(f"Sending CFP to Vehicle {vehicle_id}")
        await ctx.send(address, cfp)

@protocol.on_message(model=ProposalResponse)
async def handle_proposal(ctx: Context, sender: str, msg: ProposalResponse):
    """Handle proposal responses from vehicles"""
    
    current_task_id = ctx.storage.get("current_task_id")
    
    # Ignore proposals for old tasks
    if msg.task_id != current_task_id:
        ctx.logger.info(f"Ignoring proposal for old task {msg.task_id}")
        return
    
    # Store the proposal (convert to dict for JSON storage)
    proposals = ctx.storage.get("proposals") or {}
    proposals[msg.vehicle_id] = msg.dict()   # ✅ use dict instead of raw object
    ctx.storage.set("proposals", proposals)
    
    ctx.logger.info(f"Received proposal from Vehicle {msg.vehicle_id}:")
    ctx.logger.info(f"  Busy: {msg.is_busy}")
    ctx.logger.info(f"  Current location: {msg.current_node}")
    if not msg.is_busy and msg.estimated_time:
        ctx.logger.info(f"  Estimated time: {msg.estimated_time:.2f} time units")
        if msg.planned_path:
            ctx.logger.info(f"  Path: {' → '.join(msg.planned_path)}")
    
    # Check if we've received all proposals or if timeout reached
    last_cfp_time = ctx.storage.get("last_cfp_time")
    response_timeout = 5.0
    
    if len(proposals) >= len(VEHICLE_ADDRESSES) or \
       (time.time() - last_cfp_time) > response_timeout:
        await evaluate_proposals(ctx)


async def evaluate_proposals(ctx: Context):
    """Evaluate all proposals and assign task to best vehicle"""
    
    awaiting = ctx.storage.get("awaiting_responses")
    if not awaiting:
        return
    
    ctx.storage.set("awaiting_responses", False)
    raw_proposals = ctx.storage.get("proposals") or {}
    
    # Rehydrate dicts into ProposalResponse objects
    proposals = {
        vid: ProposalResponse(**data) for vid, data in raw_proposals.items()
    }
    
    # Filter out busy vehicles and find the one with shortest time
    available_proposals = [
        (vid, prop) for vid, prop in proposals.items() 
        if not prop.is_busy and prop.estimated_time is not None
    ]
    
    if not available_proposals:
        ctx.logger.info("No vehicles available for task")
        return
    
    # Select vehicle with shortest estimated time
    best_vehicle_id, best_proposal = min(
        available_proposals, 
        key=lambda x: x[1].estimated_time
    )
    
    ctx.logger.info("="*60)
    ctx.logger.info(f"TASK ASSIGNMENT")
    ctx.logger.info(f"Task {ctx.storage.get('current_task_id')} assigned to Vehicle {best_vehicle_id}")
    ctx.logger.info(f"Destination: {ctx.storage.get('current_destination')}")
    ctx.logger.info(f"Estimated time: {best_proposal.estimated_time:.2f} time units")
    ctx.logger.info("="*60)
    
    # Create and send assignment
    assignment = TaskAssignment(
        task_id=ctx.storage.get("current_task_id"),
        destination_node=ctx.storage.get("current_destination"),
        vehicle_id=best_vehicle_id
    )
    
    active_assignments = ctx.storage.get("active_assignments") or {}
    active_assignments[ctx.storage.get("current_task_id")] = {
        "vehicle_id": best_vehicle_id,
        "destination": ctx.storage.get("current_destination"),
        "start_time": time.time()
    }
    ctx.storage.set("active_assignments", active_assignments)
    
    # Send assignment to the selected vehicle
    for vehicle_id, address in VEHICLE_ADDRESSES.items():
        if vehicle_id == best_vehicle_id:
            await ctx.send(address, assignment)
            break


@protocol.on_message(model=TaskAcceptance)
async def handle_task_acceptance(ctx: Context, sender: str, msg: TaskAcceptance):
    """Handle task acceptance confirmation from vehicle"""
    
    if msg.accepted:
        ctx.logger.info(f"Task {msg.task_id} accepted by Vehicle {msg.vehicle_id}")
        if msg.planned_path:
            ctx.logger.info(f"Execution path: {' → '.join(msg.planned_path)}")
    else:
        ctx.logger.warning(f"Task {msg.task_id} rejected by Vehicle {msg.vehicle_id}")

@protocol.on_message(model=TaskCompletion)
async def handle_task_completion(ctx: Context, sender: str, msg: TaskCompletion):
    """Handle task completion notification from vehicle"""
    
    ctx.logger.info("="*60)
    ctx.logger.info(f"TASK COMPLETION")
    ctx.logger.info(f"Task {msg.task_id} completed by Vehicle {msg.vehicle_id}")
    ctx.logger.info(f"Success: {msg.success}")
    ctx.logger.info(f"Final node: {msg.final_node}")
    ctx.logger.info("="*60)
    
    # Remove from active assignments
    active_assignments = ctx.storage.get("active_assignments") or {}
    if msg.task_id in active_assignments:
        del active_assignments[msg.task_id]
        ctx.storage.set("active_assignments", active_assignments)
    
    # Add to completed tasks
    completed_tasks = ctx.storage.get("completed_tasks") or []
    completed_tasks.append(msg.task_id)
    ctx.storage.set("completed_tasks", completed_tasks)
    
    ctx.logger.info(f"Total completed tasks: {len(completed_tasks)}")

@protocol.on_message(model=NodeUpdate)
async def handle_node_update(ctx: Context, sender: str, msg: NodeUpdate):
    """Handle position updates from vehicles"""
    ctx.logger.info(f"Vehicle {msg.vehicle_id} position update: {msg.current_node} (Progress: {msg.progress:.0f}%)")

# Include protocol in agent
manager.include(protocol)

if __name__ == "__main__":
    print("Starting Manager Agent...")
    print(f"Manager will send Call for Proposals every 20 seconds")
    print(f"Destination nodes loaded from: {MAP_FILE}")
    print(f"Available destinations: {DESTINATION_NODES[:5]}..." if len(DESTINATION_NODES) > 5 else DESTINATION_NODES)
    print(f"Monitoring vehicles: {list(VEHICLE_ADDRESSES.keys())}")
    manager.run()