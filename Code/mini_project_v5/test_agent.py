from uagents import Agent, Context
from protocol import protocol
from handler import *

vehicle_addresses = {
    1: 'agent1q03ndjvw6z8ke3h80x0f6mezwnhxrxapwzlfmgwrr7kzneucef9lzdqqxp6',
    # Add more vehicles as needed
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
    ctx.logger.info("Manager started")
    ctx.storage.set("state", "idle")
    ctx.storage.set("TOTAL_VEHICLES", len(vehicle_addresses))
    ctx.storage.set("ranking_all", {})
    ctx.storage.set("responses_received", [])
    ctx.storage.set("task_assigned_vehicle", None)
    ctx.storage.set("vehicle_addresses", vehicle_addresses)
    
    ctx.logger.info(f"Managing {len(vehicle_addresses)} vehicle(s)")
    ctx.logger.info(f"Protocol digest: {protocol.digest}")

if __name__ == "__main__":
    manager.run()