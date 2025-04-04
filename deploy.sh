#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Swahili Voice Clone Zero-Downtime Deployment Script ===${NC}"

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    exit 1
fi

# Function to get container health status
check_health() {
    local container_name=$1
    local max_attempts=30
    local attempt=1

    echo "Checking container health..."
    while [ $attempt -le $max_attempts ]
    do
        if docker ps --filter "name=$container_name" --format "{{.Status}}" | grep -q "Up"; then
            echo -e "\n${GREEN}Container started successfully!${NC}"
            return 0
        fi
        echo -n "."
        sleep 2
        ((attempt++))
    done
    echo -e "\n${RED}Container startup logs:${NC}"
    docker logs $container_name
    return 1
}

# Clean up any existing containers with the same name pattern
echo -e "${BLUE}Cleaning up old containers...${NC}"
docker ps -a | grep 'swahili-voice-clone-' | awk '{print $1}' | xargs -r docker rm -f

# Build new image
echo -e "${BLUE}Building new swahili-voice-clone image...${NC}"
if ! docker build -t swahili-voice-clone:new .; then
    echo -e "${RED}Failed to build image${NC}"
    exit 1
fi

# Start new container
echo -e "${BLUE}Starting new container...${NC}"
if ! docker run -d \
    --name "swahili-voice-clone-blue" \
    --restart unless-stopped \
    -p 7000:80 \
    --env-file .env \
    swahili-voice-clone:new \
    gunicorn \
    -w 3 \
    -k uvicorn.workers.UvicornWorker \
    --preload \
    --timeout 300 \
    --graceful-timeout 300 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --access-logfile - \
    main:app \
    --bind 0.0.0.0:80; then

    echo -e "${RED}Failed to start new container${NC}"
    exit 1
fi

# Wait for new container to be healthy
echo -e "${BLUE}Waiting for new container to be ready...${NC}"
sleep 5  # Give the container some time to start up

if check_health "swahili-voice-clone-blue"; then
    echo -e "${GREEN}New container is healthy!${NC}"

    # Tag the successful deployment
    docker tag swahili-voice-clone:new swahili-voice-clone:latest
    docker rmi swahili-voice-clone:new 2>/dev/null

    echo -e "${GREEN}=== Deployment Successful ===${NC}"
    echo -e "${BLUE}Container Details:${NC}"
    docker ps -f name="swahili-voice-clone-blue"
else
    echo -e "${RED}New container failed health check. Rolling back...${NC}"
    docker stop "swahili-voice-clone-blue" 2>/dev/null
    docker rm "swahili-voice-clone-blue" 2>/dev/null
    docker rmi swahili-voice-clone:new 2>/dev/null
    echo -e "${RED}Deployment failed.${NC}"
    exit 1
fi
