from uagents import Agent, Context, Model
from random_number_generator import generate_unique_random_number, generate_random_number

# Defines a simple message structure using the Model class from uAgents. 
class Message(Model):
    message: str
    vehicle_number: int
    ranking: int

# It runs on port 8001 and listens for messages at the specified endpoint.
vehicle1 = Agent(name="vehicle1", 
            seed="vehicle 1 recovery phrase", 
            port=8001, 
            endpoint=["http://localhost:8001/submit"])

# Assign vehicle number
vehicle_number_local = 1

# Receives a random number
ranking_local = generate_unique_random_number()
print(f"Vehicle 1 got: {ranking_local}")

# Bob handling incoming messages
@vehicle1.on_message(model=Message)
async def vehicle_message_handler(ctx: Context, sender: str, msg: Message):

    if msg.message == "What is your number?":
        # Respond with ranking info
        await ctx.send(sender, Message(
            message=f"Ranking of Vehicle {vehicle_number_local} is {ranking_local}", 
            vehicle_number=vehicle_number_local, 
            ranking=ranking_local
        ))
    
    elif msg.message == "You have not been selected for the task.":
        ctx.logger.info(f"I was not selected!")
    
    elif msg.message == "You are appointed for the task!":
        ctx.logger.info(f"I was selected!")

        # Generate task success/failure response based on random number parity
        task_number = generate_random_number()
        ctx.logger.info(f"Generated number for task: {task_number}")

        if task_number % 2 == 0:
            response_msg = "I can complete the task."
            ctx.logger.info(f"The task can be completed.")
        else:
            response_msg = "I cannot complete the task."
            ctx.logger.info(f"The task cannot be completed.")

        await ctx.send(sender, Message(
            message=response_msg,
            vehicle_number=vehicle_number_local,
            ranking=ranking_local
        ))

# Starts the agent
if __name__ == "__main__":
    vehicle1.run()