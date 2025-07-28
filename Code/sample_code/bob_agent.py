from uagents import Agent, Context, Model

# Defines a simple message structure using the Model class from uAgents. 
class Message(Model):
    message: str

# It runs on port 8001 and listens for messages at the specified endpoint.
bob = Agent(name="bob", 
            seed="bob recovery phrase", 
            port=8001, 
            endpoint=["http://localhost:8001/submit"])

# Bob handling incoming messages
@bob.on_message(model=Message)
async def bob_message_handler(ctx: Context, sender: str, msg: Message):
    ctx.logger.info(f"Received message: {msg.message}")
    await ctx.send(sender, Message(message="We can fix this!"))

# Starts the agent
if __name__ == "__main__":
    bob.run()