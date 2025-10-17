#!/bin/bash
# One-click deployment script for STCP GTFS ETL Pipeline with Docker

set -e

echo "Starting STCP GTFS ETL Pipeline with Docker..."

# Check if Docker is installed
if ! [ -x "$(command -v docker)" ]; then
  echo "Error: Docker is not installed." >&2
  exit 1
fi

# Check if docker-compose is installed (modern Docker includes 'compose' as a subcommand)
if ! [ -x "$(command -v docker-compose)" ] && ! [ -x "$(command -v docker compose 2>/dev/null)" ]; then
  echo "Error: neither docker-compose nor docker compose is available." >&2
  exit 1
fi

# Determine which docker-compose command to use
if [ -x "$(command -v docker compose)" ]; then
  COMPOSE_CMD="docker compose"
else
  COMPOSE_CMD="docker-compose"
fi

# Set default values for all variables
export DB_USER=${DB_USER:-etl_user}
export DB_NAME=${DB_NAME:-stcp_warehouse}
export DB_PASSWORD=${DB_PASSWORD:-DbServer123}

echo "Using configuration:"
echo "  DB_USER: $DB_USER"
echo "  DB_NAME: $DB_NAME"
echo "  DB_PASSWORD: ${DB_PASSWORD:0:3}*** (${#DB_PASSWORD} chars)"
echo ""

# Navigate to the project directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

echo "Building and starting all services..."
DB_USER=$DB_USER DB_NAME=$DB_NAME DB_PASSWORD=$DB_PASSWORD $COMPOSE_CMD -f docker/docker-compose.yml up -d --build

echo "Waiting for services to be ready (this may take 1-2 minutes)..."
sleep 60

echo "Running initial ETL process to load data..."
DB_USER=$DB_USER DB_NAME=$DB_NAME DB_PASSWORD=$DB_PASSWORD $COMPOSE_CMD -f docker/docker-compose.yml run --rm etl

echo "STCP GTFS ETL Pipeline deployment completed successfully!"
echo ""
echo "Dashboard is available at: http://localhost"
echo "API Documentation: http://localhost/api/docs"
echo ""
echo "Useful commands:"
echo "  View logs: DB_USER=$DB_USER DB_NAME=$DB_NAME DB_PASSWORD=$DB_PASSWORD $COMPOSE_CMD -f docker/docker-compose.yml logs -f"
echo "  Stop services: DB_USER=$DB_USER DB_NAME=$DB_NAME DB_PASSWORD=$DB_PASSWORD $COMPOSE_CMD -f docker/docker-compose.yml down"
