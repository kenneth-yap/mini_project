import asyncio
from uagents import Protocol, Context
from handler import *
from ranking import get_lowest_ranked_vehicle
from random_number_generator import generate_random_number
from paho.mqtt.client import Client as MQTTClient

MQTT_BROKER = "localhost"
MQTT_PORT = 1883

protocol = Protocol()

class MQTTRankingReceiver:
    def __init__(self, vehicle_number: int):
        self.vehicle_number = vehicle_number
        self.topic = f"vehicle/{vehicle_number}/ranking"
        self.client = MQTTClient()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.loop = asyncio.get_event_loop()
        self.ranking_future = None

    def start(self):
        self.client.connect(MQTT_BROKER, MQTT_PORT)
        self.client.loop_start()  # background thread

    def on_connect(self, client, userdata, flags, rc):
        print(f"MQTT connected with result code {rc}")
        client.subscribe(self.topic)

    def on_message(self, client, userdata, msg):
        message = msg.payload.decode()
        print(f"MQTT message received on {msg.topic}: {message}")
        if self.ranking_future and not self.ranking_future.done():
            try:
                ranking = int(message)
                self.loop.call_soon_threadsafe(self.ranking_future.set_result, ranking)
            except Exception:
                self.loop.call_soon_threadsafe(self.ranking_future.set_result, None)

    async def get_ranking(self, timeout=10):
        self.ranking_future = self.loop.create_future()
        try:
            ranking = await asyncio.wait_for(self.ranking_future, timeout=timeout)
            return ranking
        except asyncio.TimeoutError:
            return None

# This will be set on first use, after reading vehicle_number from context
mqtt_receiver = None

@protocol.on_message(model=ProvideRanking)
async def handle_ranking_response(ctx: Context, sender: str, msg: ProvideRanking):
    state = ctx.storage.get("state")
    if state != "waiting_for_responses":
        ctx.logger.warning(f"Unexpected ranking in state {state}. Ignoring.")
        return

    ranking_all = ctx.storage.get("ranking_all")
    responses_received = ctx.storage.get("responses_received")
    vehicle_addresses = ctx.storage.get("vehicle_addresses")
    TOTAL_VEHICLES = ctx.storage.get("TOTAL_VEHICLES")

    ranking_all[msg.vehicle_number] = msg.ranking
    responses_received.append(msg.vehicle_number)

    ctx.storage.set("ranking_all", ranking_all)
    ctx.storage.set("responses_received", responses_received)

    if len(responses_received) == TOTAL_VEHICLES:
        ctx.logger.info(f"Collected rankings from all vehicles: {ranking_all}")

        task_assigned_vehicle = get_lowest_ranked_vehicle(ranking_all)
        ctx.logger.info(f"Assigning task to Vehicle {task_assigned_vehicle}")
        ctx.storage.set("task_assigned_vehicle", task_assigned_vehicle)

        for vehicle_number, address in vehicle_addresses.items():
            if vehicle_number == task_assigned_vehicle:
                await ctx.send(address, AssignTask(
                    vehicle_number=vehicle_number,
                    ranking=ranking_all[vehicle_number]
                ))
            else:
                await ctx.send(address, RejectTask(vehicle_number=vehicle_number))

        ctx.storage.set("state", "waiting_for_task_completion")

@protocol.on_message(model=TaskResponse)
async def handle_task_response(ctx: Context, sender: str, msg: TaskResponse):
    state = ctx.storage.get("state")
    if state != "waiting_for_task_completion":
        ctx.logger.warning(f"Ignoring task response in state {state}")
        return

    if msg.can_complete:
        ctx.logger.info(f"Vehicle {msg.vehicle_number} completed the task successfully.")
    else:
        ctx.logger.info(f"Vehicle {msg.vehicle_number} could not complete the task.")

    ctx.storage.set("state", "idle")

@protocol.on_message(model=RequestRanking, replies={ProvideRanking})
async def handle_ranking_request(ctx: Context, sender: str, _: RequestRanking):
    global mqtt_receiver

    state = ctx.storage.get("state")
    if state != "idle":
        ctx.logger.warning(f"Busy state ({state}), ignoring ranking request.")
        return

    ctx.storage.set("state", "busy")

    vehicle_number = ctx.storage.get("vehicle_number")

    # Instantiate mqtt_receiver once
    if mqtt_receiver is None:
        mqtt_receiver = MQTTRankingReceiver(vehicle_number)
        mqtt_receiver.start()

    ctx.logger.info(f"Waiting for ranking via MQTT on topic vehicle/{vehicle_number}/ranking ...")

    ranking = await mqtt_receiver.get_ranking(timeout=10)

    if ranking is None:
        ctx.logger.warning("No ranking received via MQTT in time.")
        ctx.storage.set("state", "idle")
        return

    ctx.logger.info(f"Received ranking {ranking} via MQTT")

    await ctx.send(sender, ProvideRanking(
        vehicle_number=vehicle_number,
        ranking=ranking
    ))

    ctx.storage.set("state", "idle")

@protocol.on_message(model=RejectTask)
async def handle_rejection(ctx: Context, sender: str, msg: RejectTask):
    ctx.logger.info(f"Vehicle {msg.vehicle_number} was rejected.")
    ctx.storage.set("state", "idle")

@protocol.on_message(model=AssignTask, replies={TaskResponse})
async def handle_assignment(ctx: Context, sender: str, msg: AssignTask):
    state = ctx.storage.get("state")
    if state != "idle":
        ctx.logger.warning(f"Already assigned or busy. Current state: {state}")
        return

    ctx.logger.info(f"Assigned task. Moving to assigned state.")
    ctx.storage.set("state", "assigned")

    task_number = generate_random_number()
    can_complete = task_number % 2 == 0
    ctx.logger.info(f"Generated task number {task_number}, success: {can_complete}")

    vehicle_number = ctx.storage.get("vehicle_number")

    ctx.storage.set("state", "busy")
    await ctx.send(sender, TaskResponse(
        vehicle_number=vehicle_number,
        can_complete=can_complete
    ))
    ctx.storage.set("state", "idle")
