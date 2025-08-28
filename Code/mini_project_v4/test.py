import asyncio
import json
import time

async def test_direct():
    print(f"[TEST] {time.strftime('%H:%M:%S')} Connecting to DT...")
    reader, writer = await asyncio.open_connection('127.0.0.1', 5001)
    
    request = {"type": "assign_task", "assigned": True, "ranking": 99}
    msg = json.dumps(request) + "\n"
    
    print(f"[TEST] {time.strftime('%H:%M:%S')} Sending: {request}")
    writer.write(msg.encode())
    await writer.drain()
    
    print(f"[TEST] {time.strftime('%H:%M:%S')} Waiting for response...")
    response = await reader.readline()
    
    print(f"[TEST] {time.strftime('%H:%M:%S')} Got: {response.decode().strip()}")
    
    writer.close()
    await writer.wait_closed()

asyncio.run(test_direct())