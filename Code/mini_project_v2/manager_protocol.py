from uagents import Context, Model, Protocol
from ranking import get_lowest_ranked_vehicle

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

# ========== STATE CONSTANTS ==========

'''
MANAGER_STATES = [
    "idle",
    "waiting_for_responses",
    "task_assigned",
    "waiting_for_task_completion"
]
'''

# ======= PROTOCOL INSTANCE =======

protocol = Protocol()

@protocol.on_message(model=ProvideRanking)
async def handle_ranking_response(ctx: Context, sender: str, msg: ProvideRanking):
    state = ctx.storage.get("state")
    if state != "waiting_for_responses":
        ctx.logger.warning(f"Unexpected ranking in state {state}. Ignoring.")
        return

    ranking_all = ctx.storage.get("ranking_all")
    responses_received = ctx.storage.get("responses_received")
    vehicle_addresses = ctx.storage.get("vehicle_addresses")
    TOTAL_VEHICLES = ctx.storage.get("TOTAL_VEHICLES")

    ranking_all[msg.vehicle_number] = msg.ranking
    responses_received.append(msg.vehicle_number)

    ctx.storage.set("ranking_all", ranking_all)
    ctx.storage.set("responses_received", responses_received)

    if len(responses_received) == TOTAL_VEHICLES:
        task_assigned_vehicle = get_lowest_ranked_vehicle(ranking_all)
        ctx.logger.info(f"Assigning task to Vehicle {task_assigned_vehicle}")
        ctx.storage.set("task_assigned_vehicle", task_assigned_vehicle)

        for vehicle_number, address in vehicle_addresses.items():
            # ctx.logger.info(f"Checking vehicle {type(vehicle_number)} against assigned {type(task_assigned_vehicle)}")
            if vehicle_number == task_assigned_vehicle:
                await ctx.send(address, AssignTask(
                    vehicle_number=vehicle_number,
                    ranking=ranking_all[vehicle_number]
                ))
            else:
                await ctx.send(address, RejectTask(vehicle_number=vehicle_number))

        ctx.storage.set("state", "waiting_for_task_completion")

@protocol.on_message(model=TaskResponse)
async def handle_task_response(ctx: Context, sender: str, msg: TaskResponse):
    state = ctx.storage.get("state")
    if state != "waiting_for_task_completion":
        ctx.logger.warning(f"Ignoring task response in state {state}")
        return

    if msg.can_complete:
        ctx.logger.info(f"Vehicle {msg.vehicle_number} completed the task successfully.")
    else:
        ctx.logger.info(f"Vehicle {msg.vehicle_number} could not complete the task.")

    ctx.storage.set("state", "idle")
