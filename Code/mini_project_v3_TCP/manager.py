from uagents import Agent, Context
from protocol import protocol
from handler import *
from ranking import get_lowest_ranked_vehicle

vehicle_addresses = {
    1: 'agent1q03ndjvw6z8ke3h80x0f6mezwnhxrxapwzlfmgwrr7kzneucef9lzdqqxp6',
    2: 'agent1qtazd65qr6ss3g2l4h0m04q5g7kj8y4fwf4f989tyxntd2mgnyr7wrgzy6d'
}

manager = Agent(
    name="manager",
    seed="manager recovery phrase",
    port=8000,
    endpoint=["http://localhost:8000/submit"]
)

manager.include(protocol)

@manager.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info("Manager started.")
    ctx.storage.set("state", "idle")
    ctx.storage.set("TOTAL_VEHICLES", len(vehicle_addresses))
    ctx.storage.set("ranking_all", {})
    ctx.storage.set("responses_received", [])
    ctx.storage.set("task_assigned_vehicle", None)
    ctx.storage.set("vehicle_addresses", vehicle_addresses)

    ctx.logger.info(f"Protocol digest: {protocol.digest}")

@manager.on_interval(5)
async def initiate_ranking_request(ctx: Context):
    if ctx.storage.get("state") != "idle":
        return

    ctx.logger.info("Initiating ranking request...")
    ctx.storage.set("state", "waiting_for_responses")
    ctx.storage.set("ranking_all", {})
    ctx.storage.set("responses_received", [])

    vehicle_addresses = ctx.storage.get("vehicle_addresses")

    for vehicle_number, address in vehicle_addresses.items():
        await ctx.send(address, RequestRanking(
            vehicle_number=vehicle_number,
            ranking=0  # Manager doesn't have a real rank
        ))

if __name__ == "__main__":
    manager.run()

# To do
'''
- Create one class instantiate with unique parameters [DONE]
- Implementation of client (cancellation) 
- Embedded in the DT lifecycle/maintenance
- TCP protocol impelemntation 
'''