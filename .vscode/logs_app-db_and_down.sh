#!/bin/bash
trap 'docker-compose down' INT
docker-compose logs -f magic_signon_db magic_signon_api
