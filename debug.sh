#!/usr/bin/env bash

# Check if the network exists
if ! docker network ls | grep -q auth_network; then
    docker network create auth_network
fi

# Check if the queue services are already up
# if ! docker-compose -f docker-compose-queue.yml ps | grep -q Up; then
#     docker-compose -f docker-compose.debug.yml up -d
# fi

docker-compose -f docker-compose.debug.yml up --build -d
