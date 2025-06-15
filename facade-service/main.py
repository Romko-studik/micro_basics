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

app = FastAPI()
#facade-service/main.py
LOGGING_URL = "http://localhost:6000/log"
LOGGING_GET_URL = "http://localhost:6000/all"
MESSAGE_URL = "http://localhost:7000/message"

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


@app.on_event("startup")
async def startup_event():
    """Initialize the ConfigServiceClient on startup"""
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
    logging_url = logging_client._get_random_instance()+ "/log"
    # Send to Logging Service
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(logging_url, json=payload)
            response.raise_for_status()
            logger.info(f"Logged message {msg_id} to logging service")
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to log message: {e}")
            return {"error": "Failed to log message", "details": str(e)}
    # Send to Hazelcast Queue
    hazelcast_manager.queue.put(json.dumps(payload))
    logger.info(f"Enqueued message {payload}")
    return {"status": "queued", "id": msg_id}


@app.get("/get")
async def get_msgs():
    async with httpx.AsyncClient() as client:
        logging_get_url = logging_client._get_random_instance()
        if not logging_get_url:
            return {"error": "No logging instance available"}

        message_url = message_client.get_message_service_url()
        if not message_url:
            return {"error": "No message service instance available"}

        log_resp =await client.get(logging_get_url + "/all")
        msg_resp =await client.get(message_url)

    combined = log_resp.text + "\n---\n" + msg_resp.text
    return {"response": combined}




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")