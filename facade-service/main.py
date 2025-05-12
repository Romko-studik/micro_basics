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

@app.post("/post")
async def post_msg(request: Request):
    data = await request.json()
    msg_id = str(uuid4())
    payload = {"id": msg_id, "msg": data["msg"]}

    for attempt in range(10):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(LOGGING_URL, json=payload, timeout=5)
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
        log_resp = await client.get(LOGGING_GET_URL)
        msg_resp = await client.get(MESSAGE_URL)

    combined = log_resp.text + "\n---\n" + msg_resp.text
    return {"response": combined}
