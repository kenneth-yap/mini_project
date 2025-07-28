from uagents import Agent, Context, Model

# Defines a simple message structure using the Model class from uAgents. 
class Message(Model):
    message: str

# It runs on port 8000 and listens for messages at the specified endpoint.
alice = Agent(name="alice", 
              seed="sigmar recovery phrase", 
              port=8000, 
              endpoint=["http://localhost:8000/submit"])

# Bob's address
BOB_ADDRESS = 'agent1q0mau8vkmg78xx0sh8cyl4tpl4ktx94pqp2e94cylu6haugt2hd7j9vequ7'

# Alice sends a message at interval
@alice.on_interval(period=5.0)
async def send_message(ctx: Context):
    await ctx.send(BOB_ADDRESS, Message(message="Bob the Builder!"))

# Alice handling incoming messages
@alice.on_message(model=Message)
async def alice_message_handler(ctx: Context, sender: str, msg: Message):
    ctx.logger.info(f"Received message: {msg.message}")

# Starts the agent
if __name__ == "__main__":
    alice.run()


'''
from uagents import Agent, Context, Model
 
# It runs on port 8000 and listens for messages at the specified endpoint.
alice = Agent(name="alice", seed="alice_seed_phrase", endpoint=["http://localhost:8000/submit"], port="8000")
 
# Defines a simple message structure using the Model class from uAgents. 
class Message(Model):
    message : str

# Alice sends a message at interval
# @alice.on_interval(period=3.0) : 3.0 represents every 3 seconds
BOB_ADDRESS = '<INSERT BOB ADDRESS>'
@alice.on_interval(period=3.0)
async def send_message(ctx: Context): 
    await ctx.send(BOB_ADDRESS, Message(message="Hello there Bob!"))

# Alice handling incoming messages
@alice.on_message(model=Message)
async def print_message(ctx: Context, msg : Message):
    ctx.logger.info(f"Message received: {msg.message}")

# Starts the agent
if __name__ == "__main__":
    # Needs to be the agent's name
    alice.run()
'''
