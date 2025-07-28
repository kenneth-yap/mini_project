from uagents import Agent, Context
from vehicle_protocol import protocol


vehicle_number = 1

vehicle = Agent(
    name=f"vehicle{vehicle_number}",
    seed="vehicle 1 recovery phrase",
    port=8001,
    endpoint=["http://localhost:8001/submit"]
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
