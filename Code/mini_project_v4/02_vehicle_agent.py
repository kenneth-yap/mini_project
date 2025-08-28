
from uagents import Agent, Context
from protocol import *
import sys

# Pass vehicle number as command-line argument: python agent.py 1
vehicle_number = int(sys.argv[1]) if len(sys.argv) > 1 else 1

vehicle = Agent(
    name=f"vehicle{vehicle_number}",
    seed=f"vehicle {vehicle_number} recovery phrase",
    port=8000 + vehicle_number,  # 8001, 8002, ...
    endpoint=[f"http://localhost:{8000 + vehicle_number}/submit"]
)

vehicle.include(protocol)

@vehicle.on_event("startup")
async def init(ctx: Context):

    # Vehicle startup
    # dt_client = DigitalTwinClient(vehicle_number)
    # ctx.storage.set("dt_client", dt_client)

    ctx.storage.set("state", "idle")
    ctx.storage.set("vehicle_number", vehicle_number)
    ctx.storage.set("ranking", None)
    ctx.logger.info(f"Starting in state: idle")
    ctx.logger.info(f"Protocol digest: {protocol.digest}")
    ctx.logger.info(f"Agent address: {vehicle.address}")

if __name__ == "__main__":
    vehicle.run()


