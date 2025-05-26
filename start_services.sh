#!/usr/bin/env sh
python3 config-service/main.py 

python3 logging-service/main.py --port 8071 &
python3 logging-service/main.py --port 8072 &
python3 logging-service/main.py --port 8073 &

python3 facade-service/main.py --port 8000 &

python3 messages-service/main.py --port 8010 &
