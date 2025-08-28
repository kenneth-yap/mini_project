import asyncio
import json
from uagents import Protocol, Context
from handler import *
from ranking import get_lowest_ranked_vehicle
import time

# Digital Twin TCP endpoint
DT_HOST = "127.0.0.1"
DT_BASE_PORT = 5000  # base port for vehicle 1

protocol = Protocol()


# ============================================================
# Digital Twin Client (used by Vehicle side)
# ============================================================
class DigitalTwinClient:
    """Async TCP client for communicating with Digital Twin"""

    def __init__(self, vehicle_number: int, host=DT_HOST, base_port=DT_BASE_PORT):
        self.host = host
        self.port = base_port + (vehicle_number - 1)
        self.vehicle_number = vehicle_number

    async def send_request(self, request: dict, timeout=20):
        """Send a JSON request to DT and await JSON response"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[VehicleAgent] [{timestamp}] Connecting to DT at {self.host}:{self.port}")
        print(f"[VehicleAgent] [{timestamp}] Sending request: {request}")
        
        reader = None
        writer = None
        
        try:
            # Establish connection
            reader, writer = await asyncio.open_connection(self.host, self.port)
            print(f"[VehicleAgent] [{timestamp}] TCP connection established")
            
            # Send request
            msg = json.dumps(request) + "\n"
            writer.write(msg.encode())
            await writer.drain()
            print(f"[VehicleAgent] [{timestamp}] Request sent: {msg.strip()}")

            # Wait for response with timeout
            print(f"[VehicleAgent] [{timestamp}] Waiting for response (timeout={timeout}s)...")
            data = await asyncio.wait_for(reader.readline(), timeout=timeout)
            
            if not data:
                print(f"[VehicleAgent] [{timestamp}] ERROR: No data received from DT")
                return None
                
            response_str = data.decode().strip()
            print(f"[VehicleAgent] [{timestamp}] Raw response received: {response_str}")
            
            try:
                response = json.loads(response_str)
                print(f"[VehicleAgent] [{timestamp}] Parsed response: {response}")
                return response
            except json.JSONDecodeError as e:
                print(f"[VehicleAgent] [{timestamp}] ERROR: Invalid JSON response: {e}")
                print(f"[VehicleAgent] [{timestamp}] Raw data was: {response_str}")
                return None
                
        except asyncio.TimeoutError:
            print(f"[VehicleAgent] [{timestamp}] ERROR: Timeout waiting for DT response")
            return None
        except ConnectionRefusedError:
            print(f"[VehicleAgent] [{timestamp}] ERROR: Connection refused to {self.host}:{self.port}")
            return None
        except Exception as e:
            print(f"[VehicleAgent] [{timestamp}] ERROR: Exception communicating with DT: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            # Clean up connection
            if writer:
                try:
                    writer.close()
                    await writer.wait_closed()
                    print(f"[VehicleAgent] [{timestamp}] TCP connection closed")
                except Exception as e:
                    print(f"[VehicleAgent] [{timestamp}] Error closing connection: {e}")

    async def get_ranking(self):
        print(f"[VehicleAgent] Getting ranking for vehicle {self.vehicle_number}")
        resp = await self.send_request({"type": "request_ranking"})
        
        if resp and resp.get("type") == "ranking_response":
            ranking = resp.get("ranking")
            print(f"[VehicleAgent] Successfully got ranking: {ranking}")
            return ranking
        else:
            print(f"[VehicleAgent] Failed to get ranking. Response was: {resp}")
            return None

    async def assign_task(self, assigned: bool, ranking: int):
        print(f"[VehicleAgent] Assigning task for vehicle {self.vehicle_number}: assigned={assigned}, ranking={ranking}")
        resp = await self.send_request(
            {"type": "assign_task", "assigned": assigned, "ranking": ranking}
        )
        
        if resp and resp.get("type") == "task_result":
            print(f"[VehicleAgent] Successfully got task result: {resp}")
            return resp
        else:
            print(f"[VehicleAgent] Failed to get task result. Response was: {resp}")
            return None

# ============================================================
# Vehicle-side Protocol Handlers
# ============================================================

@protocol.on_message(model=RequestRanking, replies={ProvideRanking})
async def handle_ranking_request(ctx: Context, sender: str, msg: RequestRanking):
    state = ctx.storage.get("state")
    if state != "idle":
        ctx.logger.warning(f"Busy state ({state}), ignoring ranking request.")
        return

    ctx.storage.set("state", "busy")

    vehicle_number = ctx.storage.get("vehicle_number")
    ctx.logger.info(f"Processing ranking request for vehicle {vehicle_number}")

    # Initialize DT client dynamically per vehicle
    dt_client = DigitalTwinClient(vehicle_number)

    ctx.logger.info(f"Requesting ranking from Digital Twin for vehicle {vehicle_number}")
    ranking = await dt_client.get_ranking()

    if ranking is None:
        ctx.logger.warning("No ranking received from Digital Twin.")
        ctx.storage.set("state", "idle")
        return

    ctx.logger.info(f"Got ranking {ranking} from Digital Twin")

    await ctx.send(
        sender,
        ProvideRanking(vehicle_number=vehicle_number, ranking=ranking),
    )

    ctx.storage.set("state", "idle")


@protocol.on_message(model=AssignTask, replies={TaskResponse})
async def handle_assignment(ctx: Context, sender: str, msg: AssignTask):
    state = ctx.storage.get("state")
    if state != "idle":
        ctx.logger.warning(f"Already assigned or busy. Current state: {state}")
        return

    ctx.logger.info(f"Assigned task, delegating to Digital Twin.")
    ctx.storage.set("state", "assigned")

    vehicle_number = ctx.storage.get("vehicle_number")
    ctx.logger.info(f"Processing task assignment for vehicle {vehicle_number}")

    dt_client = DigitalTwinClient(vehicle_number)

    # Ask DT to assign task to simulator
    ctx.logger.info(f"Requesting task assignment from DT: assigned=True, ranking={msg.ranking}")
    result = await dt_client.assign_task(True, msg.ranking)

    if result is None:
        ctx.logger.warning("No task result received from Digital Twin.")
        can_complete = False
    else:
        can_complete = result.get("can_complete", False)
        ctx.logger.info(f"Digital Twin reported task result: {result}")
        ctx.logger.info(f"Task can_complete: {can_complete}")

    ctx.storage.set("state", "busy")
    await ctx.send(
        sender,
        TaskResponse(vehicle_number=vehicle_number, can_complete=can_complete),
    )
    ctx.storage.set("state", "idle")


@protocol.on_message(model=RejectTask)
async def handle_rejection(ctx: Context, sender: str, msg: RejectTask):
    ctx.logger.info(f"Vehicle {msg.vehicle_number} was rejected.")
    ctx.storage.set("state", "idle")


# ============================================================
# Manager-side Protocol Handlers
# ============================================================
@protocol.on_message(model=ProvideRanking)
async def handle_ranking_response(ctx: Context, sender: str, msg: ProvideRanking):
    ctx.logger.info(f"Received ranking {msg.ranking} from vehicle {msg.vehicle_number}")

    rankings = ctx.storage.get("rankings") or {}
    rankings[msg.vehicle_number] = (sender, msg.ranking)
    ctx.storage.set("rankings", rankings)

    # Example: decide once we have 2 vehicles responding
    if len(rankings) >= 2:
        best_vehicle = get_lowest_ranked_vehicle(rankings)
        ctx.logger.info(f"Best vehicle selected: {best_vehicle}")

        for vnum, (addr, rnk) in rankings.items():
            if vnum == best_vehicle:
                ctx.logger.info(f"Assigning task to vehicle {vnum} with ranking {rnk}")
                await ctx.send(addr, AssignTask(vehicle_number=vnum, ranking=rnk))
            else:
                ctx.logger.info(f"Rejecting vehicle {vnum}")
                await ctx.send(addr, RejectTask(vehicle_number=vnum))

        ctx.storage.set("rankings", {})


@protocol.on_message(model=TaskResponse)
async def handle_task_response(ctx: Context, sender: str, msg: TaskResponse):
    if msg.can_complete:
        ctx.logger.info(f"Vehicle {msg.vehicle_number} successfully completed the task!")
    else:
        ctx.logger.info(f"Vehicle {msg.vehicle_number} FAILED to complete the task.")