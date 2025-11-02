# 01_manager_FIXED.py - Fixed version with corrected export timing and better messaging
# FIXES:
# 1. Export only after ALL tasks complete (including active ones), not just after max_tasks sent
# 2. Better messaging when vehicle is already at destination (not "rejected")

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
import random
import time
import uuid
import os
import glob
import json
from typing import Dict, List, Optional
from datetime import datetime
from collections import defaultdict

# Clean up any corrupted storage files before starting
def cleanup_old_storage():
    """Remove any corrupted storage files from previous runs"""
    try:
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

cleanup_old_storage()

# File path for map
MAP_FILE = r"C:\Users\hhy26\OneDrive - University of Cambridge\Desktop\01_PhD\04_First_Year_Report\00_vehicle_simulator_0.1.2\vehicle_simulator\map.txt"

def load_nodes_from_map(map_file_path: str) -> List[str]:
    """Load all node names from the map.txt file"""
    nodes = []
    try:
        with open(map_file_path, 'r') as file:
            print(f"Loading nodes from: {map_file_path}")
            for line in file:
                line = line.strip()
                if line:
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
        return ["Node2", "Node3", "Node4", "Node5", "Node6", "Node7", "Node8"]
    except Exception as e:
        print(f"Error reading map file: {e}")
        return ["Node2", "Node3", "Node4", "Node5", "Node6", "Node7", "Node8"]

ALL_NODES = load_nodes_from_map(MAP_FILE)
DESTINATION_NODES = [node for node in ALL_NODES if node != "Node1"]

print(f"Available destination nodes: {DESTINATION_NODES}")
print(f"Total destination nodes: {len(DESTINATION_NODES)}")

# Manager configuration
MANAGER_PORT = 8000
MANAGER_SEED = "manager recovery phrase"

# Vehicle agent addresses
VEHICLE_ADDRESSES = {
    1: 'agent1q03ndjvw6z8ke3h80x0f6mezwnhxrxapwzlfmgwrr7kzneucef9lzdqqxp6',
    2: 'agent1qtazd65qr6ss3g2l4h0m04q5g7kj8y4fwf4f989tyxntd2mgnyr7wrgzy6d',
    3: 'agent1q0lw72pj974rt4z5ea29zxqm32mpcjwqyexj6mwx8mady6l8ueafkxzvzr2',
}

try:
    manager = Agent(
        name="manager",
        seed=MANAGER_SEED,
        port=MANAGER_PORT,
        endpoint=[f"http://localhost:{MANAGER_PORT}/submit"]
    )
    print(f"Manager agent created successfully")
    print(f"Manager address: {manager.address}")
    print("="*60)
except Exception as e:
    print(f"Error creating manager agent: {e}")
    exit(1)

protocol = Protocol()

# Enhanced Manager State with Comprehensive Metrics
class ManagerState:
    def __init__(self):
        # Current task state
        self.current_task_id: Optional[str] = None
        self.current_destination: Optional[str] = None
        self.proposals: Dict[int, ProposalResponse] = {}
        self.active_assignments: Dict[str, Dict] = {}
        self.completed_tasks: List[str] = []
        self.last_cfp_time: float = 0
        self.awaiting_responses: bool = False
        self.response_timeout: float = 10.0
        self.vehicle_addresses = VEHICLE_ADDRESSES
        
        # Task limiting
        self.tasks_sent_count: int = 0
        self.max_tasks: int = 30
        self.simulation_stopped: bool = False
        self.export_triggered: bool = False
        
        # === Comprehensive Metrics Tracking ===
        
        # Task allocation metrics
        self.task_history: List[Dict] = []
        self.allocation_decisions: List[Dict] = []
        self.rejected_tasks: List[Dict] = []
        
        # Response time metrics
        self.cfp_response_times: List[Dict] = []
        self.task_execution_times: List[Dict] = []
        self.end_to_end_times: List[Dict] = []
        
        # Vehicle performance tracking
        self.vehicle_metrics: Dict[int, Dict] = {
            vid: {
                "tasks_assigned": 0,
                "tasks_completed": 0,
                "tasks_rejected": 0,
                "total_estimated_time": 0.0,
                "total_distance": 0.0,
                "busy_time": 0.0,
                "idle_time": 0.0,
                "proposals_submitted": 0,
                "avg_response_time": 0.0,
                "response_times": []
            } for vid in VEHICLE_ADDRESSES.keys()
        }
        
        # System-level metrics
        self.system_utilization: List[Dict] = []
        self.load_balance_metrics: List[Dict] = []
        self.coordination_efficiency: List[Dict] = []
        
        # Destination/Node metrics
        self.destination_metrics: Dict[str, Dict] = defaultdict(lambda: {
            "times_requested": 0,
            "times_completed": 0,
            "avg_completion_time": 0.0,
            "completion_times": [],
            "vehicles_used": set()
        })
        
        # Fairness metrics
        self.task_distribution_fairness: List[float] = []
        
        # Communication metrics
        self.message_count: Dict[str, int] = {
            "cfp_sent": 0,
            "proposals_received": 0,
            "assignments_sent": 0,
            "acceptances_received": 0,
            "completions_received": 0,
            "updates_received": 0
        }
        
        # Optimization metrics
        self.optimal_vs_actual: List[Dict] = []
        
        # Time windows
        self.simulation_start_time: float = time.time()
        self.last_metrics_snapshot: float = time.time()

state = ManagerState()

@manager.on_event("startup")
async def startup(ctx: Context):
    """Initialize manager on startup with comprehensive logging"""
    ctx.logger.info("="*60)
    ctx.logger.info("FIXED MANAGER AGENT STARTED")
    ctx.logger.info("="*60)
    ctx.logger.info(f"Manager address: {manager.address}")
    ctx.logger.info(f"Protocol digest: {protocol.digest}")
    ctx.logger.info(f"Map file: {MAP_FILE}")
    ctx.logger.info(f"Loaded {len(ALL_NODES)} nodes from map")
    ctx.logger.info(f"Available destinations: {len(DESTINATION_NODES)} nodes")
    ctx.logger.info(f"Monitoring {len(VEHICLE_ADDRESSES)} vehicles")
    ctx.logger.info("Comprehensive metrics tracking: ENABLED")
    ctx.logger.info(f"Task limit: 30 tasks")
    ctx.logger.info("="*60)
    ctx.logger.info("FIXES APPLIED:")
    ctx.logger.info("  1. Export only after ALL tasks complete (not just sent)")
    ctx.logger.info("  2. Better messaging for already-at-destination cases")
    ctx.logger.info("="*60)
    
    # Initialize storage with enhanced state
    ctx.storage.set("state", "idle")
    ctx.storage.set("current_task_id", None)
    ctx.storage.set("proposals", {})
    ctx.storage.set("active_assignments", {})
    ctx.storage.set("completed_tasks", [])
    ctx.storage.set("awaiting_responses", False)
    ctx.storage.set("task_history", [])
    ctx.storage.set("vehicle_metrics", state.vehicle_metrics)
    ctx.storage.set("message_count", state.message_count)
    ctx.storage.set("simulation_start_time", state.simulation_start_time)
    ctx.storage.set("tasks_sent_count", 0)
    ctx.storage.set("max_tasks", 30)
    ctx.storage.set("simulation_stopped", False)
    ctx.storage.set("export_triggered", False)  # NEW: Track if we've exported

@manager.on_interval(period=10.0)
async def send_call_for_proposal(ctx: Context):
    """Send out call for proposal with metrics tracking"""
    
    # Check if simulation has been stopped
    simulation_stopped = ctx.storage.get("simulation_stopped")
    if simulation_stopped:
        # FIX #1: Check if we should export now
        active_assignments = ctx.storage.get("active_assignments") or {}
        export_triggered = ctx.storage.get("export_triggered") or False
        
        if not active_assignments and not export_triggered:
            ctx.logger.info("="*60)
            ctx.logger.info("✅ ALL TASKS COMPLETED - EXPORTING FINAL METRICS")
            ctx.logger.info("="*60)
            completed_count = len(ctx.storage.get("completed_tasks") or [])
            ctx.logger.info(f"Total tasks completed: {completed_count}")
            ctx.storage.set("export_triggered", True)
            export_all_metrics(ctx)
        elif active_assignments:
            ctx.logger.info(f"⏳ Waiting for {len(active_assignments)} active tasks to complete...")
        
        return
    
    # Check task limit
    tasks_sent_count = ctx.storage.get("tasks_sent_count")
    max_tasks = ctx.storage.get("max_tasks")
    
    if tasks_sent_count >= max_tasks:
        if not simulation_stopped:
            ctx.logger.info("="*60)
            ctx.logger.info(f"📊 TASK LIMIT REACHED: {tasks_sent_count}/{max_tasks} tasks sent")
            ctx.logger.info("⏸️  Stopping task generation...")
            active_count = len(ctx.storage.get("active_assignments") or {})
            ctx.logger.info(f"⏳ {active_count} tasks still active - waiting for completion")
            ctx.logger.info("="*60)
            ctx.storage.set("simulation_stopped", True)
            
        return
    
    # Check if we're still waiting for responses
    awaiting = ctx.storage.get("awaiting_responses")
    if awaiting:
        ctx.logger.info("Still awaiting responses from previous CFP")
        return
    
    if not DESTINATION_NODES:
        ctx.logger.error("No destination nodes available!")
        return
    
    # Generate new task
    task_id = str(uuid.uuid4())[:8]
    destination = random.choice(DESTINATION_NODES)
    cfp_timestamp = time.time()
    
    # Update destination metrics
    dest_metrics = state.destination_metrics[destination]
    dest_metrics["times_requested"] += 1
    
    # Record task creation
    task_record = {
        "task_id": task_id,
        "destination": destination,
        "cfp_timestamp": cfp_timestamp,
        "cfp_datetime": datetime.fromtimestamp(cfp_timestamp).isoformat(),
        "vehicles_contacted": list(VEHICLE_ADDRESSES.keys()),
        "status": "cfp_sent"
    }
    
    task_history = ctx.storage.get("task_history") or []
    task_history.append(task_record)
    ctx.storage.set("task_history", task_history)
    
    ctx.storage.set("current_task_id", task_id)
    ctx.storage.set("current_destination", destination)
    ctx.storage.set("proposals", {})
    ctx.storage.set("awaiting_responses", True)
    ctx.storage.set("last_cfp_time", cfp_timestamp)
    ctx.storage.set("current_cfp_timestamp", cfp_timestamp)
    
    # Update message count
    message_count = ctx.storage.get("message_count") or state.message_count
    message_count["cfp_sent"] += 1
    ctx.storage.set("message_count", message_count)
    
    # Increment tasks sent
    tasks_sent_count += 1
    ctx.storage.set("tasks_sent_count", tasks_sent_count)
    
    ctx.logger.info("="*60)
    ctx.logger.info(f"📣 CALL FOR PROPOSAL #{tasks_sent_count}/{max_tasks}")
    ctx.logger.info(f"Task ID: {task_id}")
    ctx.logger.info(f"Destination: {destination}")
    ctx.logger.info(f"Vehicles contacted: {len(VEHICLE_ADDRESSES)}")
    ctx.logger.info("="*60)
    
    # Send CFP to all vehicles
    cfp = CallForProposal(
        task_id=task_id,
        destination_node=destination,
        timestamp=cfp_timestamp
    )

    '''
    for vehicle_id, address in VEHICLE_ADDRESSES.items():
    await ctx.send(address, cfp)  # Send → wait → log → repeat
    ctx.logger.info(f"  → Sent to Vehicle {vehicle_id}")
    '''
    
    send_tasks = []
    for vehicle_id, address in VEHICLE_ADDRESSES.items():
        send_tasks.append(ctx.send(address, cfp))  # Queue all sends
        ctx.logger.info(f"  → Sent to Vehicle {vehicle_id}")  # Log immediately

    await asyncio.gather(*send_tasks)  # Send all at once

@protocol.on_message(model=ProposalResponse)
async def handle_proposal(ctx: Context, sender: str, msg: ProposalResponse):
    """Handle proposals from vehicles with enhanced tracking"""
    
    current_task_id = ctx.storage.get("current_task_id")
    
    if msg.task_id != current_task_id:
        ctx.logger.info(f"Ignoring proposal for old task {msg.task_id}")
        return
    
    proposal_timestamp = time.time()
    cfp_timestamp = ctx.storage.get("current_cfp_timestamp")
    
    # Calculate response time
    response_time = proposal_timestamp - cfp_timestamp if cfp_timestamp else 0
    
    # Update vehicle metrics
    vehicle_metrics = ctx.storage.get("vehicle_metrics") or state.vehicle_metrics
    vehicle_metrics[msg.vehicle_id]["proposals_submitted"] += 1
    vehicle_metrics[msg.vehicle_id]["response_times"].append(response_time)
    vehicle_metrics[msg.vehicle_id]["avg_response_time"] = sum(
        vehicle_metrics[msg.vehicle_id]["response_times"]
    ) / len(vehicle_metrics[msg.vehicle_id]["response_times"])
    
 
    
    # Record response time
    state.cfp_response_times.append({
        "task_id": msg.task_id,
        "vehicle_id": msg.vehicle_id,
        "response_time": response_time,
        "timestamp": proposal_timestamp,
        "is_busy": msg.is_busy
    })
    
    # Update message count
    message_count = ctx.storage.get("message_count") or state.message_count
    message_count["proposals_received"] += 1
    ctx.storage.set("message_count", message_count)
    
    # Store the proposal
    proposals = ctx.storage.get("proposals") or {}
    proposals[msg.vehicle_id] = msg.dict()
    ctx.storage.set("proposals", proposals)
    
    # FIX #2: Better messaging for already-at-destination case
    destination = ctx.storage.get("current_destination")
    if not msg.is_busy and msg.current_node == destination:
        ctx.logger.info(f"✅ Vehicle {msg.vehicle_id} is already at {destination}!")
        ctx.logger.info(f"   Response time: {response_time:.3f}s")
        ctx.logger.info(f"   Task can be completed immediately")
    elif msg.is_busy:
        ctx.logger.info(f"📌 Vehicle {msg.vehicle_id} is busy")
        ctx.logger.info(f"   Current location: {msg.current_node}")
        ctx.logger.info(f"   Response time: {response_time:.3f}s")
    else:
        ctx.logger.info(f"📩 Received proposal from Vehicle {msg.vehicle_id}:")
        ctx.logger.info(f"   Busy: {msg.is_busy}")
        ctx.logger.info(f"   Current location: {msg.current_node}")
        ctx.logger.info(f"   Response time: {response_time:.3f}s")
        
        if msg.estimated_time:
            ctx.logger.info(f"   Estimated time: {msg.estimated_time:.2f} time units")
            if msg.planned_path:
                ctx.logger.info(f"   Path: {' → '.join(msg.planned_path)}")
    
    # Check if all responses received or timeout
    last_cfp_time = ctx.storage.get("last_cfp_time")
    response_timeout = 10.0
    
    if len(proposals) >= len(VEHICLE_ADDRESSES) or \
       (time.time() - last_cfp_time) > response_timeout:
        await evaluate_proposals(ctx)

async def evaluate_proposals(ctx: Context):
    """Evaluate proposals with comprehensive decision metrics"""
    
    awaiting = ctx.storage.get("awaiting_responses")
    if not awaiting:
        return
    
    evaluation_start = time.time()
    ctx.storage.set("awaiting_responses", False)
    
    raw_proposals = ctx.storage.get("proposals") or {}
    proposals = {
        vid: ProposalResponse(**data) for vid, data in raw_proposals.items()
    }
    
    # Filter available vehicles
    available_proposals = [
        (vid, prop) for vid, prop in proposals.items() 
        if not prop.is_busy and prop.estimated_time is not None
    ]
    
    # Record allocation decision context
    allocation_decision = {
        "task_id": ctx.storage.get("current_task_id"),
        "destination": ctx.storage.get("current_destination"),
        "evaluation_timestamp": evaluation_start,
        "total_proposals": len(proposals),
        "available_proposals": len(available_proposals),
        "busy_vehicles": [vid for vid, prop in proposals.items() if prop.is_busy],
        "proposal_details": [
            {
                "vehicle_id": vid,
                "is_busy": prop.is_busy,
                "estimated_time": prop.estimated_time,
                "current_node": prop.current_node
            } for vid, prop in proposals.items()
        ]
    }
    
    if not available_proposals:
        ctx.logger.info("❌ No vehicles available for task")
        allocation_decision["outcome"] = "no_vehicles_available"
        allocation_decision["selected_vehicle"] = None
        state.rejected_tasks.append(allocation_decision)
        return
    
    # Select best vehicle (shortest time)
    best_vehicle_id, best_proposal = min(
        available_proposals,
        key=lambda x: x[1].estimated_time
    )
    
    # FIX #2: Check if vehicle is already at destination
    destination = ctx.storage.get("current_destination")
    if best_proposal.current_node == destination:
        ctx.logger.info("="*60)
        ctx.logger.info(f"🎯 INSTANT COMPLETION - Vehicle {best_vehicle_id} already at destination!")
        ctx.logger.info(f"Task ID: {ctx.storage.get('current_task_id')}")
        ctx.logger.info(f"Location: {destination}")
        ctx.logger.info(f"No travel required - vehicle is free and ready")
        ctx.logger.info("="*60)
    else:
        ctx.logger.info("="*60)
        ctx.logger.info(f"🎯 TASK ASSIGNED to Vehicle {best_vehicle_id}")
        ctx.logger.info(f"Task ID: {ctx.storage.get('current_task_id')}")
        ctx.logger.info(f"Destination: {destination}")
        ctx.logger.info(f"Estimated time: {best_proposal.estimated_time:.2f}")
        if best_proposal.planned_path:
            ctx.logger.info(f"Planned path: {' → '.join(best_proposal.planned_path)}")
        ctx.logger.info("="*60)
    
    # Record allocation decision
    allocation_decision["outcome"] = "assigned"
    allocation_decision["selected_vehicle"] = best_vehicle_id
    allocation_decision["selected_estimated_time"] = best_proposal.estimated_time
    allocation_decision["winner_already_at_destination"] = (best_proposal.current_node == destination)
    state.allocation_decisions.append(allocation_decision)
    
    # Update vehicle metrics
    vehicle_metrics = ctx.storage.get("vehicle_metrics") or state.vehicle_metrics
    vehicle_metrics[best_vehicle_id]["tasks_assigned"] += 1
    vehicle_metrics[best_vehicle_id]["total_estimated_time"] += best_proposal.estimated_time
    ctx.storage.set("vehicle_metrics", vehicle_metrics)
    
    # Update message count
    message_count = ctx.storage.get("message_count") or state.message_count
    message_count["assignments_sent"] += 1
    ctx.storage.set("message_count", message_count)
    
    # Send assignment
    assignment = TaskAssignment(
        task_id=ctx.storage.get("current_task_id"),
        destination_node=destination,
        vehicle_id=best_vehicle_id
    )
    
    vehicle_address = VEHICLE_ADDRESSES[best_vehicle_id]
    await ctx.send(vehicle_address, assignment)
    
    # Track active assignment
    active_assignments = ctx.storage.get("active_assignments") or {}
    active_assignments[assignment.task_id] = {
        "vehicle_id": best_vehicle_id,
        "destination": destination,
        "estimated_time": best_proposal.estimated_time,
        "start_time": time.time(),
        "already_at_destination": (best_proposal.current_node == destination)
    }
    ctx.storage.set("active_assignments", active_assignments)

@protocol.on_message(model=TaskAcceptance)
async def handle_task_acceptance(ctx: Context, sender: str, msg: TaskAcceptance):
    """Handle task acceptance confirmation"""
    
    # Update message count
    message_count = ctx.storage.get("message_count") or state.message_count
    message_count["acceptances_received"] += 1
    ctx.storage.set("message_count", message_count)
    
    if msg.accepted:
        ctx.logger.info("="*60)
        ctx.logger.info(f"✅ TASK ACCEPTED by Vehicle {msg.vehicle_id}")
        ctx.logger.info(f"Task ID: {msg.task_id}")
        if msg.planned_path:
            ctx.logger.info(f"Planned path: {' → '.join(msg.planned_path)}")
        ctx.logger.info("="*60)
        
        # Update active assignment with acceptance time
        active_assignments = ctx.storage.get("active_assignments") or {}
        if msg.task_id in active_assignments:
            active_assignments[msg.task_id]["acceptance_timestamp"] = time.time()
            active_assignments[msg.task_id]["planned_path"] = msg.planned_path
            ctx.storage.set("active_assignments", active_assignments)
    else:
        ctx.logger.warning("="*60)
        ctx.logger.warning(f"❌ TASK REJECTED by Vehicle {msg.vehicle_id}")
        ctx.logger.warning(f"Task ID: {msg.task_id}")
        ctx.logger.warning("="*60)
        
        # Update vehicle metrics
        vehicle_metrics = ctx.storage.get("vehicle_metrics") or state.vehicle_metrics
        vehicle_metrics[msg.vehicle_id]["tasks_rejected"] += 1
        ctx.storage.set("vehicle_metrics", vehicle_metrics)

@protocol.on_message(model=TaskCompletion)
async def handle_task_completion(ctx: Context, sender: str, msg: TaskCompletion):
    """Handle task completion with comprehensive metrics"""
    
    completion_timestamp = time.time()
    
    ctx.logger.info("="*60)
    ctx.logger.info(f"✅ TASK COMPLETED by Vehicle {msg.vehicle_id}")
    ctx.logger.info(f"Task ID: {msg.task_id}")
    ctx.logger.info(f"Success: {msg.success}")
    ctx.logger.info(f"Final node: {msg.final_node}")
    ctx.logger.info("="*60)
    
    # Update message count
    message_count = ctx.storage.get("message_count") or state.message_count
    message_count["completions_received"] += 1
    ctx.storage.set("message_count", message_count)
    
    # Calculate execution metrics
    active_assignments = ctx.storage.get("active_assignments") or {}
    if msg.task_id in active_assignments:
        assignment = active_assignments[msg.task_id]
        
        actual_time = completion_timestamp - assignment["start_time"]
        estimated_time = assignment.get("estimated_time", 0)
        
        
        completion_record = {
            "task_id": msg.task_id,
            "vehicle_id": msg.vehicle_id,
            "final_node": msg.final_node,
            "success": msg.success,
            "estimated_time": estimated_time,
            "actual_time": actual_time,
            "completion_timestamp": completion_timestamp,
            "completion_datetime": datetime.fromtimestamp(completion_timestamp).isoformat(),
            "was_already_at_destination": assignment.get("already_at_destination", False)
        }
        
        state.task_execution_times.append(completion_record)
        
        # Update vehicle metrics
        vehicle_metrics = ctx.storage.get("vehicle_metrics") or state.vehicle_metrics
        vehicle_metrics[msg.vehicle_id]["tasks_completed"] += 1
        ctx.storage.set("vehicle_metrics", vehicle_metrics)
        
        # Update destination metrics
        dest = assignment["destination"]
        state.destination_metrics[dest]["times_completed"] += 1
        state.destination_metrics[dest]["completion_times"].append(actual_time)
        state.destination_metrics[dest]["avg_completion_time"] = sum(
            state.destination_metrics[dest]["completion_times"]
        ) / len(state.destination_metrics[dest]["completion_times"])
        state.destination_metrics[dest]["vehicles_used"].add(msg.vehicle_id)
        
        ctx.logger.info(f"📊 Execution metrics:")
        ctx.logger.info(f"   Estimated: {estimated_time:.2f}s")
        if assignment.get("already_at_destination"):
            ctx.logger.info(f"   Note: Vehicle was already at destination")
        
        del active_assignments[msg.task_id]
        ctx.storage.set("active_assignments", active_assignments)
    
    # Add to completed tasks
    completed_tasks = ctx.storage.get("completed_tasks") or []
    completed_tasks.append(msg.task_id)
    ctx.storage.set("completed_tasks", completed_tasks)
    
    # Calculate fairness metrics
    calculate_fairness_metrics(ctx)
    
    # FIX #1: Check if we should export now
    simulation_stopped = ctx.storage.get("simulation_stopped")
    active_assignments = ctx.storage.get("active_assignments") or {}
    export_triggered = ctx.storage.get("export_triggered") or False
    
    if simulation_stopped and not active_assignments and not export_triggered:
        ctx.logger.info("="*60)
        ctx.logger.info("✅ ALL TASKS COMPLETED - EXPORTING FINAL METRICS")
        ctx.logger.info("="*60)
        ctx.logger.info(f"Total tasks completed: {len(completed_tasks)}")
        ctx.storage.set("export_triggered", True)
        export_all_metrics(ctx)

@protocol.on_message(model=NodeUpdate)
async def handle_node_update(ctx: Context, sender: str, msg: NodeUpdate):
    """Handle position updates with tracking"""
    
    # Update message count
    message_count = ctx.storage.get("message_count") or state.message_count
    message_count["updates_received"] += 1
    ctx.storage.set("message_count", message_count)
    
    # destination = ctx.storage.get("current_destination")
    ctx.logger.info(f"📍 Vehicle {msg.vehicle_id} position: {msg.current_node} to {msg.next_node} (Progress: {msg.progress:.0f}%)")

def calculate_fairness_metrics(ctx: Context):
    """Calculate task distribution fairness using Gini coefficient"""
    vehicle_metrics = ctx.storage.get("vehicle_metrics") or state.vehicle_metrics
    
    tasks_assigned = [vm["tasks_completed"] for vm in vehicle_metrics.values()]
    
    if sum(tasks_assigned) == 0:
        return
    
    # Calculate Gini coefficient
    n = len(tasks_assigned)
    tasks_sorted = sorted(tasks_assigned)
    cumsum = sum((i+1) * tasks for i, tasks in enumerate(tasks_sorted))
    gini = (2 * cumsum) / (n * sum(tasks_assigned)) - (n + 1) / n
    
    state.task_distribution_fairness.append(gini)
    
    ctx.logger.info(f"⚖️  Task distribution fairness (Gini): {gini:.3f} (0=perfect, 1=unfair)")

@manager.on_interval(period=30.0)
async def periodic_status_check(ctx: Context):
    """Periodically check status and log active tasks"""
    
    simulation_stopped = ctx.storage.get("simulation_stopped")
    if not simulation_stopped:
        return
    
    active_assignments = ctx.storage.get("active_assignments") or {}
    if active_assignments:
        ctx.logger.info("="*60)
        ctx.logger.info(f"⏳ STATUS CHECK: {len(active_assignments)} tasks still active")
        for task_id, assignment in active_assignments.items():
            elapsed = time.time() - assignment["start_time"]
            ctx.logger.info(f"   Task {task_id[:8]}: Vehicle {assignment['vehicle_id']} → {assignment['destination']} ({elapsed:.1f}s)")
        ctx.logger.info("="*60)

manager.include(protocol)

# Export comprehensive metrics on shutdown
def export_all_metrics(ctx: Context = None):
    """Export all tracked metrics to files (overwrite instead of new timestamped files)."""
    
    # Sync latest values
    if ctx:
        tasks_sent = ctx.storage.get("tasks_sent_count")
        if tasks_sent is not None:
            state.tasks_sent_count = tasks_sent
        max_tasks = ctx.storage.get("max_tasks")
        if max_tasks is not None:
            state.max_tasks = max_tasks
    
    # Always overwrite — fixed filenames
    export_files = {
        "allocations": "manager_allocations.json",
        "response_times": "manager_response_times.json",
        "execution_times": "manager_execution_times.json",
        "destination_metrics": "manager_destination_metrics.json",
        "system_snapshots": "manager_system_snapshots.json",
        "summary": "manager_summary.json"
    }
    
    # Export allocation decisions
    with open(export_files["allocations"], "w") as f:
        json.dump(state.allocation_decisions, f, indent=2)
    
    # Export response times
    with open(export_files["response_times"], "w") as f:
        json.dump(state.cfp_response_times, f, indent=2)
    
    # Export execution times
    with open(export_files["execution_times"], "w") as f:
        json.dump(state.task_execution_times, f, indent=2)
    
    # Export destination metrics (convert sets)
    dest_metrics_serializable = {
        k: {**v, "vehicles_used": list(v["vehicles_used"])} 
        for k, v in state.destination_metrics.items()
    }
    with open(export_files["destination_metrics"], "w") as f:
        json.dump(dest_metrics_serializable, f, indent=2)
    
    # Export system snapshots
    with open(export_files["system_snapshots"], "w") as f:
        json.dump(state.system_utilization, f, indent=2)
    
    # Export summary
    summary = {
        "export_timestamp": time.time(),
        "export_datetime": datetime.now().isoformat(),
        "completed_tasks": len(state.task_execution_times),
        "rejected_tasks": len(state.rejected_tasks),
        "allocation_decisions": len(state.allocation_decisions),
        "vehicle_count": len(VEHICLE_ADDRESSES),
        "destination_count": len(DESTINATION_NODES),
        "message_statistics": state.message_count,
        "fairness_metrics": {
            "gini_coefficients": state.task_distribution_fairness,
            "average_gini": (
                sum(state.task_distribution_fairness) / len(state.task_distribution_fairness)
                if state.task_distribution_fairness else 0
            )
        },
        "performance_summary": {
            "avg_response_time": (
                sum(rt["response_time"] for rt in state.cfp_response_times) / len(state.cfp_response_times)
                if state.cfp_response_times else 0
            ),
            "avg_execution_time": (
                sum(et["actual_time"] for et in state.task_execution_times) / len(state.task_execution_times)
                if state.task_execution_times else 0
            )
        }
    }
    with open(export_files["summary"], "w") as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n{'='*60}")
    print("✅ METRICS EXPORTED (OVERWRITTEN EXISTING FILES)")
    print(f"{'='*60}")
    print(f"Tasks completed: {len(state.task_execution_times)}")
    for key, path in export_files.items():
        print(f"{key.capitalize()}: {path}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    print("Starting FIXED Manager Agent...")
    print(f"Task limit: 30 tasks")
    print(f"FIXES APPLIED:")
    print(f"  1. ✅ Export only after ALL tasks complete (not just sent)")
    print(f"  2. ✅ Better messaging when vehicle already at destination")
    print(f"Tracking: allocations, response times, execution times, fairness, system utilization")
    print(f"Destination nodes: {DESTINATION_NODES[:5]}..." if len(DESTINATION_NODES) > 5 else DESTINATION_NODES)
    print(f"Monitoring vehicles: {list(VEHICLE_ADDRESSES.keys())}")
    print("="*60)
    
    try:
        manager.run()
    except KeyboardInterrupt:
        print("\nShutting down manager...")
        export_all_metrics()
    finally:
        # Only export if not already done
        if not getattr(state, 'export_triggered', False):
            export_all_metrics()