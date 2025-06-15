import requests
import random
import logging
from typing import List, Dict, Optional
from fastapi import FastAPI, Request
from uuid import uuid4
import httpx
import asyncio
import logging
from hazelcast_config import HazelcastManager
import json
import consul
import socket, os
app = FastAPI()
#facade-service/main.py
LOGGING_URL = "http://localhost:6000/log"
LOGGING_GET_URL = "http://localhost:6000/all"
MESSAGE_URL = "http://localhost:7000/message"
PORT = 8001
# Set up logging to output errors
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConfigServiceClient:
    def __init__(self, config_server_url: str = "http://localhost:8005"):
        self.config_server_url = config_server_url
    
    def get_service_instances(self, service_name: str) -> List[Dict]:
        try:
            url = f"{self.config_server_url}/services/{service_name}"
            print(f"{self.config_server_url}/services/{service_name}")
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            
            instances = response.json()
            logger.info(f"Retrieved {len(instances)} instances for service '{service_name}'")
            return instances
            
        except Exception as e:
            logger.error(f"Error getting service instances: {e}")
            return []


class LoggingServiceClient:
    def __init__(self, config_client: ConfigServiceClient):
        self.config_client = config_client
    
    def _get_random_instance(self) -> Optional[str]:
        instances = self.config_client.get_service_instances("logging")
        if not instances:
            return None
        
        active_instances = [inst for inst in instances if inst.get("status") == "UP"]
        if not active_instances:
            return None
        
        selected = random.choice(active_instances)
        url = f"http://{selected['ip']}:{selected['port']}"
        logger.info(f"Selected logging service instance: {url}")
        return url
    

class MassageServiceClient:
    def __init__(self, config_client: ConfigServiceClient):
        self.config_client = config_client
    
    def get_message_service_url(self) -> Optional[str]:
        instances = self.config_client.get_service_instances("messages")
        if not instances:
            return None
        
        active_instances = [inst for inst in instances if inst.get("status") == "UP"]
        if not active_instances:
            return None
        
        selected = random.choice(active_instances)
        url = f"http://{selected['ip']}:{selected['port']}/message"
        logger.info(f"Selected message service instance: {url}")
        return url

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


def get_instances(service_name):
    c = consul.Consul()
    # повертає health info, фільтруємо `passing`
    _, nodes = c.health.service(service_name, passing=True)
    return [(n["Service"]["Address"], n["Service"]["Port"]) for n in nodes]


def pick_random(service_name):
    inst = get_instances(service_name)
    return random.choice(inst) if inst else (None, None)

@app.on_event("startup")
async def startup_event():
    global c
    c = consul.Consul()
    """Initialize the ConfigServiceClient on startup"""
    register_service("facade-service", PORT)
    global config_client, logging_client, hazelcast_manager, message_client
    config_client = ConfigServiceClient()
    logging_client = LoggingServiceClient(config_client)
    message_client = MassageServiceClient(config_client)
    logger.info("Facade Service started and clients initialized")
    hazelcast_manager = HazelcastManager(instance_name="facade-service") 
    hazelcast_manager.connect()
    logger.info("Connected to Hazelcast cluster for distributed storage")


@app.post("/post")
async def post_msg(request: Request):
    data = await request.json()
    msg_id = str(uuid4())
    payload = {"id": msg_id, "msg": data["msg"]}

    # Send to Hazelcast Queue
    hazelcast_manager.queue.put(json.dumps(payload))
    logger.info(f"Enqueued message {payload}")
    return {"status": "queued", "id": msg_id}


@app.get("/get")
async def get_msgs():
    # логінг
    host, port = pick_random("logging-service")
    log_url = f"http://{host}:{port}/all"
    # messages
    host2, port2 = pick_random("messages-service")
    msg_url = f"http://{host2}:{port2}/message"
    # виконуємо HTTP
    async with httpx.AsyncClient() as client:
        log_resp = await client.get(log_url)
        msg_resp = await client.get(msg_url)
    return {"logs": log_resp.json(), "messages": msg_resp.json()}

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
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")