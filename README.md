# Microservices - Basic Architecture (Task 1)

This repository contains a basic microservices setup with three services:

1. **facade-service** — handles POST/GET requests from the client.
2. **logging-service** — stores received messages in memory and returns them.
3. **messages-service** — returns a static placeholder message.

##  How to Run (Using FastAPI + Uvicorn)

### 1. Start `logging-service` (port 6000)

```bash
cd micro_basics/logging-service
uvicorn main:app --port 6000
``` 
### 2. Start `messages-service` (port 7000)
```bash
cd micro_basics/messages-service
uvicorn main:app --port 7000
```
### 3. Start `facade-service` (port 5000)
```bash
cd micro_basics/facade-service
uvicorn main:app --port 5000
```