import asyncio
from fastapi import FastAPI
from hazelcast_config import HazelcastManager
import json
import uvicorn
import argparse
import logging
import socket, os
import consul
app = FastAPI()
messages = {}

hz_manager = HazelcastManager(instance_name="messages-service")
hz_manager.connect()
parser = argparse.ArgumentParser()
parser.add_argument("--port", type=int, default=8010, help="Port to run the service on")
args = parser.parse_args()
PORT = args.port
logger = logging.getLogger("messages-service")

def register_service(service_name, port):
    service_id = f"{service_name}-{port}"
    local_ip = socket.gethostbyname(socket.gethostname())
    c.agent.service.register(
        name=service_name,
        service_id=service_id,
        address=local_ip,
        port=port,
        check={
            "http": f"http://{local_ip}:{port}/health",
            "interval": "10s",
            "timeout": "5s",
            "DeregisterCriticalServiceAfter": "1m"
        }
    )

@app.on_event("startup")
async def startup_event():
    global c
    c = consul.Consul()
    register_service("messages-service", PORT)
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

@app.on_event("shutdown")
async def shutdown_event():
    try:
        c.agent.service.deregister(f"logging-service-{PORT}")
        print(f"Deregistered logging-service-{PORT}")
    except Exception as e:
        print(f"Failed to deregister: {e}")


@app.get("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)