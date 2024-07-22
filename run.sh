#!/usr/bin/env bash

#
# Magic_ Signon is Yet Another Magical Single Sign-on
#

# Check if the network exists
if ! docker network ls | grep -q auth_network; then
    docker network create auth_network
fi

# Check if the queue services are already up
# if ! docker-compose -f docker-compose-queue.yml ps | grep -q Up; then
#     docker-compose -f docker-compose-queue.yml up -d
# fi

docker-compose up --build
