import asyncio
from fastapi import FastAPI
from hazelcast_config import HazelcastManager
import json
import uvicorn
import argparse
import logging

app = FastAPI()
messages = {}

hz_manager = HazelcastManager(instance_name="messages-service")
hz_manager.connect()
parser = argparse.ArgumentParser()
parser.add_argument("--port", type=int, default=8010, help="Port to run the service on")
args = parser.parse_args()
PORT = args.port
logger = logging.getLogger("messages-service")


@app.on_event("startup")
async def startup_event():
    loop = asyncio.get_running_loop()
    
    async def consume():
        while True:
            try:
                future = hz_manager.queue.take()  # hazelcast.future.Future
                item = await loop.run_in_executor(None, future.result)  # run blocking .result() in thread
                msg = json.loads(item)
                messages[msg['id']] = msg['msg']
                print(f"[{hz_manager.instance_name}] Stored: {msg}")
            except Exception as e:
                print(f"Error taking from queue: {e}")
                await asyncio.sleep(1)

    asyncio.create_task(consume())


@app.get("/message")
def get_messages():
    return {"messages": list(messages.values())}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)