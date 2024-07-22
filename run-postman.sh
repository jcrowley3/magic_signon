#!/usr/bin/env bash
set -e
docker exec -it magic_signon_api /app/tests/postman.sh
