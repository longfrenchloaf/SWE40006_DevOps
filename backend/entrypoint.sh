#!/bin/bash
echo "--- Backend Entrypoint Debug ---"
echo "Received arguments: $@"
echo "DB_HOST=$DB_HOST"
echo "DB_USER=$DB_USER" # Check this value!
echo "DB_PASSWORD=$DB_PASSWORD" # Check this value (be careful in logs)
echo "DB_NAME=$DB_NAME"
echo "DB_PORT=$DB_PORT"
echo "DB_SSLMODE=$DB_SSLMODE"
echo "--- End Backend Entrypoint Debug ---"

# Execute the original command passed to the entrypoint (python billing.py)
exec "$@"