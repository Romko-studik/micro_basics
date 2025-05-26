import requests
import random
import logging
from typing import List, Dict, Optional
from fastapi import FastAPI, Request
from uuid import uuid4
import httpx
import asyncio
import logging
app = FastAPI()
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
    
@app.on_event("startup")
async def startup_event():
    """Initialize the ConfigServiceClient on startup"""
    global config_client, logging_client
    config_client = ConfigServiceClient()
    logging_client = LoggingServiceClient(config_client)
    logger.info("Facade Service started and clients initialized")


@app.post("/post")
async def post_msg(request: Request):
    data = await request.json()
    msg_id = str(uuid4())
    payload = {"id": msg_id, "msg": data["msg"]}

    for attempt in range(10):
        try:
            async with httpx.AsyncClient() as client:
                logging_url = logging_client._get_random_instance()+ "/log"
                response = await client.post(logging_url, json=payload, timeout=5)
                response.raise_for_status()  
            logging.info(f"Successfully sent message {msg_id} on attempt {attempt + 1}")
            break
        except httpx.RequestError as e:
            logging.error(f"Attempt {attempt + 1} failed with connection error: {e}")
            if attempt == 9:  
                logging.error(f"All retries failed for message {msg_id}")
            await asyncio.sleep(1)  
        except httpx.HTTPStatusError as e:
            logging.error(f"HTTP error occurred on attempt {attempt + 1}: {e}")
            break 
        except Exception as e:
            logging.error(f"Unexpected error on attempt {attempt + 1}: {e}")
            break

    return {"status": "sent", "id": msg_id}


@app.get("/get")
async def get_msgs():
    async with httpx.AsyncClient() as client:
        logging_get_url = logging_client._get_random_instance() + "/all"
        message_url = config_client.get_service_instances("messages")
        message_url = f"http://{message_url[0]['ip']}:{message_url[0]['port']}/message"
        print(logging_get_url, message_url)
        log_resp = await client.get(logging_get_url)
        msg_resp = await client.get(message_url)

    combined = log_resp.text + "\n---\n" + msg_resp.text
    return {"response": combined}
