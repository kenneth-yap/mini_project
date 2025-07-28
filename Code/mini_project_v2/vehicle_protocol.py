from uagents import Context, Model, Protocol
from random_number_generator import generate_random_number, generate_unique_random_number

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

# ======= PROTOCOL INSTANCE =======

protocol = Protocol()

# FIX DIGEST FOR ALL MODELS
fixed_digest = "contract_net_fixed_digest_v1"

for model in [RequestRanking, ProvideRanking, AssignTask, RejectTask, TaskResponse]:
    model.__digest__ = fixed_digest

# ========== STATE CONSTANTS ==========

'''
VEHICLE_STATES = [
    "idle",
    "assigned",
    "busy"
]
'''

# ========== MESSAGE HANDLERS ==========

@protocol.on_message(model=RequestRanking, replies={ProvideRanking})
async def handle_ranking_request(ctx: Context, sender: str, _: RequestRanking):
    state = ctx.storage.get("state")
    if state != "idle":
        ctx.logger.warning(f"Busy state ({state}), ignoring ranking request.")
        return

    vehicle_number = ctx.storage.get("vehicle_number")
    ranking = generate_unique_random_number()

    await ctx.send(sender, ProvideRanking(
        vehicle_number=vehicle_number,
        ranking=ranking
    ))

@protocol.on_message(model=RejectTask)
async def handle_rejection(ctx: Context, sender: str, msg: RejectTask):
    ctx.logger.info(f"Vehicle {msg.vehicle_number} was rejected.")
    ctx.storage.set("state", "idle")

@protocol.on_message(model=AssignTask, replies={TaskResponse})
async def handle_assignment(ctx: Context, sender: str, msg: AssignTask):
    state = ctx.storage.get("state")
    if state != "idle":
        ctx.logger.warning(f"Already assigned or busy. Current state: {state}")
        return

    ctx.logger.info(f"Assigned task. Moving to assigned state.")
    ctx.storage.set("state", "assigned")

    task_number = generate_random_number()
    can_complete = task_number % 2 == 0
    ctx.logger.info(f"Generated task number {task_number}, success: {can_complete}")

    vehicle_number = ctx.storage.get("vehicle_number")

    ctx.storage.set("state", "busy")
    await ctx.send(sender, TaskResponse(
        vehicle_number=vehicle_number,
        can_complete=can_complete
    ))
    ctx.storage.set("state", "idle")
