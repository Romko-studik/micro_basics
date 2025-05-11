from fastapi import FastAPI, Request
from uuid import uuid4
import httpx
import asyncio

app = FastAPI()
LOGGING_URL = "http://localhost:6000/log"
LOGGING_GET_URL = "http://localhost:6000/all"
MESSAGE_URL = "http://localhost:7000/message"

@app.post("/post")
async def post_msg(request: Request):
    data = await request.json()
    msg_id = str(uuid4())
    payload = {"id": msg_id, "msg": data["msg"]}

    for attempt in range(3):
        try:
            async with httpx.AsyncClient() as client:
                await client.post(LOGGING_URL, json=payload)
            break
        except httpx.RequestError:
            await asyncio.sleep(1)  # Retry delay

    return {"status": "sent", "id": msg_id}

@app.get("/get")
async def get_msgs():
    async with httpx.AsyncClient() as client:
        log_resp = await client.get(LOGGING_GET_URL)
        msg_resp = await client.get(MESSAGE_URL)

    combined = log_resp.text + "\n---\n" + msg_resp.text
    return {"response": combined}


### micro_basics/logging-service/main.py


### micro_basics/messages-service/main.p