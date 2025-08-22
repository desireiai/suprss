#!/bin/bash
# backend/docker-entrypoint.sh

set -e

echo "Starting SUPRSS Backend..."

# Attendre que PostgreSQL soit prêt
echo "Waiting for PostgreSQL..."
while ! nc -z postgres 5432; do
  sleep 1
done
echo "PostgreSQL is ready!"

# Attendre que Redis soit prêt
echo "Waiting for Redis..."
while ! nc -z redis 6379; do
  sleep 1
done
echo "Redis is ready!"


# Lancer l'application
echo "Starting FastAPI application..."
exec "$@"