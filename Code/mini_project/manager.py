from uagents import Agent, Context, Model
from ranking import get_lowest_ranked_vehicle

# Defines a simple message structure using the Model class from uAgents. 
class Message(Model):
    message: str
    vehicle_number: int
    ranking: int

# It runs on port 8000 and listens for messages at the specified endpoint.
manager = Agent(name="manager", 
              seed="manager recovery phrase", 
              port=8000, 
              endpoint=["http://localhost:8000/submit"])

vehicle_addresses = {
    1: 'agent1q03ndjvw6z8ke3h80x0f6mezwnhxrxapwzlfmgwrr7kzneucef9lzdqqxp6',
    2: 'agent1qtazd65qr6ss3g2l4h0m04q5g7kj8y4fwf4f989tyxntd2mgnyr7wrgzy6d',
    3: 'agent1q0lw72pj974rt4z5ea29zxqm32mpcjwqyexj6mwx8mady6l8ueafkxzvzr2',
}

TOTAL_VEHICLES = len(vehicle_addresses)

ranking_all = {}
responses_received = set()

# Options
# Interval tasks: .on_interval()
# Handle messages: .on_message()
# Answer queries: .on_query()
# Triggered by event: .on_event()

@manager.on_event('startup')
async def send_message(ctx: Context):
    # global ranking_sent
    # if not ranking_sent:
    for vehicle_number, address in vehicle_addresses.items():
        await ctx.send(address, Message( # check await
            message="What is your number?",
            vehicle_number=0,
            ranking=0
        ))
    ctx.logger.info("Request messages sent to all vehicles.")

# At the top of your file:
task_assigned_vehicle = None

@manager.on_message(model=Message)
async def manager_message_handler(ctx: Context, sender: str, msg: Message):
    global task_assigned_vehicle

    if msg.message == "I can complete the task.":
        ctx.logger.info(f"Vehicle {task_assigned_vehicle} has completed the task!")

    elif msg.message == "I cannot complete the task.":
        ctx.logger.info(f"Vehicle {task_assigned_vehicle} could not complete the task")

    else:
        ranking_all[msg.vehicle_number] = msg.ranking
        responses_received.add(msg.vehicle_number)
        ctx.logger.info(f"Received ranking: Vehicle {msg.vehicle_number} => Rank {msg.ranking}")

        if len(responses_received) == TOTAL_VEHICLES:
            task_assigned_vehicle = get_lowest_ranked_vehicle(ranking_all)
            ctx.logger.info(f"The vehicle with the lowest ranking is: Vehicle {task_assigned_vehicle}")

            await ctx.send(vehicle_addresses[task_assigned_vehicle], Message( # type: ignore
                message="You are appointed for the task!",
                vehicle_number=task_assigned_vehicle, # type: ignore
                ranking=ranking_all[task_assigned_vehicle]
            ))

            for vehicle_number, address in vehicle_addresses.items():
                if vehicle_number != task_assigned_vehicle:
                    await ctx.send(address, Message(
                        message="You have not been selected for the task.",
                        vehicle_number=vehicle_number,
                        ranking=ranking_all[vehicle_number]
                    )) # accept/reject message
# Starts the agent
if __name__ == "__main__":
    manager.run()
