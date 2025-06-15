#!/usr/bin/env bash
# start_services.sh
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color
rm -rf logs/*  # Clear previous logs
# Array to store PIDs
PIDS=()

# Function to cleanup background processes on exit
cleanup() {
    echo -e "\n${YELLOW}Stopping all services...${NC}"
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            echo "Stopping process $pid"
            kill "$pid"
        fi
    done
    
    # Give time for graceful shutdown
    sleep 3
    
    # Force kill remaining processes
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            echo "Force killing process $pid"
            kill -9 "$pid"
        fi
    done
    
    echo -e "${GREEN}All services stopped${NC}"
}

trap cleanup EXIT INT TERM
# Function to cleanup ports
cleanup_ports() {
  for port in 8005 8071 8072 8073 8010 8011 8001; do
    pid=$(lsof -t -i :$port 2>/dev/null || true)  # Ignore errors and non-zero exit
    if [[ -n "$pid" ]]; then
      echo "Killing process $pid on port $port"
      kill -9 $pid
    fi
  done
}



# Function to check if port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${RED}Port $port is already in use!${NC}"
        echo "Please stop the process using port $port or choose a different port"
        exit 1
    fi
}

# Function to start a service with env var or CLI port arg
start_service() {
    local service_name="$1"
    local cmd="$2"
    local port="$3"

    echo -e "${YELLOW}Checking port $port for $service_name...${NC}"
    check_port "$port"

    echo -e "${YELLOW}Starting $service_name on port $port...${NC}"

    local logfile="logs/${service_name// /_}.log"  # e.g. logs/Config_Service.log
    mkdir -p logs

    if [[ "$cmd" == *"--port"* ]]; then
        bash -c "$cmd" > "$logfile" 2>&1 &
    else
        SERVICE_PORT=$port bash -c "$cmd" > "$logfile" 2>&1 &
    fi

    local pid=$!
    PIDS+=($pid)

    echo -e "${GREEN}Started $service_name (PID: $pid), logging to $logfile${NC}"

    sleep 4

    if kill -0 "$pid" 2>/dev/null; then
        echo -e "${GREEN}✓ $service_name is running${NC}"
    else
        echo -e "${RED}✗ $service_name failed to start${NC}"
        exit 1
    fi
}


echo -e "${GREEN}=== Starting Microservices ===${NC}"

# Check if required files exist
for file in services_config.json hazelcast_config.py; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}Error: $file not found${NC}"
        exit 1
    fi
done

# Start services in order
echo -e "${YELLOW}Cleaning up ports...${NC}"
cleanup_ports
podman run --replace -d --name hazelcast -p 5701:5701 hazelcast/hazelcast:latest 
echo -e "${GREEN}Started Hazelcast in Podman${NC}"
start_service "Config Service" "python3 config-service/main.py" 8005

start_service "Logging Service 1" "python3 logging-service/main.py --port 8071" 8071
start_service "Logging Service 2" "python3 logging-service/main.py --port 8072" 8072
start_service "Logging Service 3" "python3 logging-service/main.py --port 8073" 8073

start_service "Messages Service 1" "python3 messages-service/main.py" 8010
start_service "Messages Service 2" "python3 messages-service/main.py --port 8011" 8011

start_service "Facade Service" "python3 facade-service/main.py" 8001

echo -e "\n${GREEN}=== All Services Started ===${NC}"

echo -e "${YELLOW}Services running:${NC}"
echo "- Config Service:    http://localhost:8005"
echo "- Facade Service:    http://localhost:8001"
echo "- Logging Service 1: http://localhost:8071"
echo "- Logging Service 2: http://localhost:8072"
echo "- Logging Service 3: http://localhost:8073"
echo "- Messages Service 1:  http://localhost:8010"
echo "- Messages Service 2: http://localhost:8011"

echo -e "\n${YELLOW}Running processes:${NC}"
for pid in "${PIDS[@]}"; do
    if kill -0 "$pid" 2>/dev/null; then
        echo "PID: $pid"
    fi
done

echo -e "\n${GREEN}Press Ctrl+C to stop all services${NC}"

# Monitor processes and exit if any dies
while true; do
    sleep 5
    for i in "${!PIDS[@]}"; do
        pid=${PIDS[$i]}
        if ! kill -0 "$pid" 2>/dev/null; then
            echo -e "${RED}Process $pid has exited unexpectedly. Stopping all services.${NC}"
            exit 1
        fi
    done
done
