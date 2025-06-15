#!/usr/bin/env python3
#config-service/main.py
import json
import os
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Config Server")

class ServiceInstance(BaseModel):
    ip: str
    port: int
    status: str = "UP"
    
    def get_url(self) -> str:
        return f"http://{self.ip}:{self.port}"

class ServiceRegistration(BaseModel):
    service_name: str
    instances: List[ServiceInstance]

services: Dict[str, List[ServiceInstance]] = {}

def initialize_services():
    """Initialize services from config file and environment variables"""
    if os.path.exists("services_config.json"):
        try:
            with open("services_config.json", "r") as f:
                print("Loading services from config file...")
                config = json.load(f)
                for service_name, instances in config.items():
                    services[service_name] = [ServiceInstance(**inst) for inst in instances]
                logger.info(f"Loaded services from config file: {list(services.keys())}")
        except Exception as e:
            logger.error(f"Error loading config file: {e}")
    else:
        logger.warning("No config file found, starting with empty services")

@app.on_event("startup")
async def startup_event():
    initialize_services()
    logger.info(f"Config Server started with services: {list(services.keys())}")

@app.get("/services/{service_name}")
async def get_service_instances(service_name: str):
    if service_name not in services:
        logger.warning(f"Service '{service_name}' not found")
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")
    
    active_instances = [inst for inst in services[service_name] if inst.status == "UP"]
    logger.info(f"Returning {len(active_instances)} active instances for service '{service_name}'")
    return active_instances

@app.post("/services")
async def register_service(registration: ServiceRegistration):
    services[registration.service_name] = registration.instances
    logger.info(f"Registered service '{registration.service_name}' with {len(registration.instances)} instances")
    return {"status": "Service registered successfully"}

@app.get("/services")
async def list_services():
    return services

@app.get("/health")
async def health_check():
    return {"status": "UP", "service": "config-server", "registered_services": list(services.keys())}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8005)