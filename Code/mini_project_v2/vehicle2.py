from uagents import Agent, Context
from vehicle_protocol import protocol
from random_number_generator import generate_unique_random_number

vehicle_number = 2

vehicle = Agent(
    name=f"vehicle{vehicle_number}",
    seed="vehicle 2 recovery phrase",
    port=8002,
    endpoint=["http://localhost:8002/submit"]
)

vehicle.include(protocol)

@vehicle.on_event("startup")
async def init(ctx: Context):

    ctx.storage.set("state", "idle")
    ctx.storage.set("vehicle_number", vehicle_number)
    ctx.storage.set("ranking", None)
    ctx.logger.info(f"Starting in state: idle")
    ctx.logger.info(f"Protocol digest: {protocol.digest}")
    ctx.logger.info(f"Agent address: {vehicle.address}")

if __name__ == "__main__":
    vehicle.run()
