import os
import sys
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import logging
from hazelcast_config import HazelcastManager
import argparse
# logging-service/main.py

parser = argparse.ArgumentParser()
parser.add_argument("--port", type=int, default=8002, help="Port to run the service on")
args = parser.parse_args()

# Now you can use:
PORT = args.port

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Logging Service")

hazelcast_manager = None
class LogMessage(BaseModel):
    id: str
    msg: str

class MessageResponse(BaseModel):
    status: str
    message: str = ""

@app.on_event("startup")
async def startup_event():
    """Initialize Hazelcast connection on startup"""
    global hazelcast_manager
    
    port = os.getenv("SERVICE_PORT", "8081")
    instance_name = f"logging-service-{port}"
    
    hazelcast_manager = HazelcastManager(instance_name=instance_name)
    hazelcast_manager.connect()
    
    logger.info(f"Logging Service started on port {port}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup Hazelcast connection on shutdown"""
    if hazelcast_manager:
        hazelcast_manager.disconnect()

@app.post("/log")
async def log_msg(log_message: LogMessage):
    """Store a log message"""
    try:
        port = PORT        
        # Check if message already exists
        print(f"Service {port} - Received message: {log_message.id} -> {log_message.msg}")
        existing_message = hazelcast_manager.get_message(log_message.id)
        if existing_message:
            logger.info(f"Service {port} - Duplicate ignored: {log_message.id}")
            return MessageResponse(status="duplicate", message=f"Message {log_message.id} already exists")
        
        # Store new message
        hazelcast_manager.put_message(log_message.id, log_message.msg)
        logger.info(f"Service {port} - Stored: {log_message.id} -> {log_message.msg}")
        logger.info(f"Service {port} - Total messages in map: {hazelcast_manager.get_map_size()}")
        
        return MessageResponse(status="ok", message=f"Message stored by service on port {port}")
        
    except Exception as e:
        logger.error(f"Error storing message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/log/{message_id}")
async def get_message(message_id: str):
    try:
        port = os.getenv("SERVICE_PORT", "8081")
        message = hazelcast_manager.get_message(message_id)
        
        if message is None:
            logger.warning(f"Service {port} - Message not found: {message_id}")
            raise HTTPException(status_code=404, detail=f"Message {message_id} not found")
        
        logger.info(f"Service {port} - Retrieved: {message_id} -> {message}")
        return {"id": message_id, "message": message}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/all")
async def get_all():
    try:
        port = os.getenv("SERVICE_PORT", "8081")
        all_messages = await hazelcast_manager.get_all_messages()
        
        logger.info(f"Service {port} - Retrieved all messages: {len(all_messages)} items")
        
        return {"messages": list(all_messages.values())}
        
    except Exception as e:
        logger.error(f"Error retrieving all messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)