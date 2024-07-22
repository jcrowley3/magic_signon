#!/usr/bin/env bash

# build and push localstack so that we can run it on Docker Swarm

docker build \
  --platform linux/amd64 \
  --file Docker/Dockerfile.localstack_localhost \
  --tag magic_signon/localstack:latest .

docker push magic_signon/localstack:latest
