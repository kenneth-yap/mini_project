from uagents import Model

# ========== MESSAGE DEFINITIONS ========== 

class RequestRanking(Model):
    vehicle_number: int 
    ranking: int 

class ProvideRanking(Model):
    vehicle_number: int
    ranking: int

class AssignTask(Model):
    vehicle_number: int
    ranking: int

class RejectTask(Model):
    vehicle_number: int

class TaskResponse(Model):
    vehicle_number: int
    can_complete: bool
