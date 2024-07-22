#!/bin/bash
trap 'docker-compose down' INT
docker-compose logs -f localstack
