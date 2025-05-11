from fastapi import FastAPI, Request

app = FastAPI()
log_store = {}

@app.post("/log")
async def log_msg(request: Request):
    data = await request.json()
    msg_id = data["id"]
    msg = data["msg"]

    if msg_id not in log_store:
        log_store[msg_id] = msg
        print(f"Stored: {msg_id} -> {msg}")
    else:
        print(f"Duplicate ignored: {msg_id}")

    return {"status": "ok"}

@app.get("/all")
async def get_all():
    return {"messages": list(log_store.values())}
