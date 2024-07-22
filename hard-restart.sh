#!/usr/bin/env bash

# delete 'postgresDB-data' folder from root directory
echo "Deleting 'postgresDB-data' folder from root directory..."
rm -rf postgresDB-data

# sleep 10

# bring down and delete containers
echo "Bringing down and deleting containers..."
docker-compose down

# remove unused/dangling images
echo "Removing unused/dangling images..."
docker image prune -a

# run run.sh
echo "Running run.sh..."
./run.sh
