# test_manager.py
import asyncio
import random
from uagents import Agent, Context
from handler import CallForProposal, Proposal, AssignMission, MissionResponse

# ------------------------------
# Manager Agent
# ------------------------------
manager = Agent(
    name="manager",
    seed="manager recovery phrase",
    port=8000,
    endpoint=["http://localhost:8000/submit"],
)

# Vehicle agent addresses
VEHICLE_ADDRESSES = {
    1: 'agent1q03ndjvw6z8ke3h80x0f6mezwnhxrxapwzlfmgwrr7kzneucef9lzdqqxp6',
    # "vehicle2_address",
}

# ------------------------------
# Storage to keep received proposals
# ------------------------------
@manager.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info("Manager started. Sending CFP every 15s...")

    while True:
        ctx.storage.set("received_proposals", {})

        # Send CFP to all vehicles
        for vehicle_addr in VEHICLE_ADDRESSES:
            ctx.logger.info(f"📡 Sending CFP to {vehicle_addr}")
            await ctx.send(vehicle_addr, CallForProposal())

        # Wait a short time for vehicles to respond
        await asyncio.sleep(2)

        received_proposals = ctx.storage.get("received_proposals") or {}
        if received_proposals:
            # Choose vehicle with lowest ranking
            best_vehicle_number, best_info = min(
                received_proposals.items(), key=lambda x: x[1]["ranking"]
            )
            best_address = best_info["address"]
            ranking = best_info["ranking"]

            # Assign a random destination Node2–Node6
            destination_node = f"Node{random.randint(2,6)}"
            ctx.logger.info(f"Assigning mission to vehicle {best_vehicle_number} → {destination_node}")
            await ctx.send(best_address, AssignMission(vehicle_number=best_vehicle_number, destination=destination_node))

        # Wait 15s until next CFP
        await asyncio.sleep(15)

# ------------------------------
# Handle proposals from vehicles
# ------------------------------
@manager.on_message(model=Proposal)
async def handle_proposal(ctx: Context, sender: str, msg: Proposal):
    proposals = ctx.storage.get("received_proposals") or {}
    proposals[msg.vehicle_number] = {"address": sender, "ranking": msg.ranking}
    ctx.storage.set("received_proposals", proposals)

# ------------------------------
# Handle mission responses
# ------------------------------
@manager.on_message(model=MissionResponse)
async def handle_mission_response(ctx: Context, sender: str, msg: MissionResponse):
    if msg.can_complete:
        ctx.logger.info(f"✅ Vehicle {msg.vehicle_number} accepted mission")
    else:
        ctx.logger.warning(f"❌ Vehicle {msg.vehicle_number} could not accept mission")

# ------------------------------
# Run manager
# ------------------------------
if __name__ == "__main__":
    manager.run()
