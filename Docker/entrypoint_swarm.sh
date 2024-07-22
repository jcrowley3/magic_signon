#!/usr/bin/env bash
echo "Cleaning up Python..."
find /app -name "*.pyc" -exec rm -f {} \;

cat << EOF >> /etc/bash.bashrc
alias ls='ls -la'
alias magic-psql="psql -U ${POSTGRES_USER} -h ${POSTGRES_HOSTNAME} -d ${POSTGRES_DB}"
EOF

if [ -f "${ALEMBIC_INI_FILE}" ]; then
    echo "Alembic config file '${ALEMBIC_INI_FILE}' exists, getting Alembic ready..."
    export CONN="sqlalchemy.url = postgresql\:\/\/${POSTGRES_USER}\:${POSTGRES_PASSWORD}\@${POSTGRES_HOSTNAME}\:${POSTGRES_PORT}\/${POSTGRES_DB}"

    # back up original ini file for good measure
    cp ${ALEMBIC_INI_FILE} "${ALEMBIC_INI_FILE}.bak"
    echo "Setting alembic connection string to use env vars for sqlalchemy.url..."

    # replace the connection string with the new connection string
    sed -i "s/sqlalchemy.url.*/$CONN/" ${ALEMBIC_INI_FILE}

    echo "Running alembic migrations..."
    alembic upgrade head
else
    echo "Alembic config file '${ALEMBIC_INI_FILE}' is not set or does not exist, skipping Alembic migrations..."
fi

if [ "${ENV}" == "dev" ]; then
  service cron start
  crontab - <<EOF
# This script adds the IP of the Docker container that is running
# Localstack to this container's DNS resolver
* * * * * /localstack_ip.sh > /localstack_ip.log 2>&1
EOF
else
  # if we're on AWS this is not needed at all
  /bin/rm -f /localstack_ip.sh
fi
service cron status

# TODO decide if we want to use Datadog, e.g.
ddtrace-run uvicorn app.main:app --proxy-headers --host 0.0.0.0 --port 80 --use-colors
# uvicorn app.main:app --reload --proxy-headers --host 0.0.0.0 --port 80 --use-colors
