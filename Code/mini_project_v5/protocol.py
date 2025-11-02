# protocol.py
from uagents import Model
from typing import Optional, List

class CallForProposal(Model):
    """Manager sends this to all vehicles with the destination node"""
    destination_node: str  # e.g., "Node12"
    task_id: str  # Unique identifier for this task

class ProposalResponse(Model):
    """Vehicle's response to call for proposal with estimated time"""
    task_id: str
    vehicle_id: int
    estimated_time: Optional[float]  # None if vehicle is busy
    is_busy: bool
    current_node: Optional[str]  # Current location of the vehicle
    planned_path: Optional[List[str]]  # The path the vehicle would take
    distance: Optional[float]
    carbon: Optional[float]
    cost: Optional[float]

class TaskAssignment(Model):
    """Manager assigns task to selected vehicle"""
    task_id: str
    destination_node: str
    vehicle_id: int

class TaskAcceptance(Model):
    """Vehicle confirms task acceptance"""
    task_id: str
    vehicle_id: int
    accepted: bool
    planned_path: Optional[List[str]]

class TaskCompletion(Model):
    """Vehicle reports task completion"""
    task_id: str
    vehicle_id: int
    final_node: str
    success: bool

class NodeUpdate(Model):
    """Vehicle sends current position updates"""
    vehicle_id: int
    current_node: str
    next_node: str
    progress: float