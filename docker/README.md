# Docker Deployment Guide

## Overview

This guide provides instructions for deploying the STCP GTFS ETL Pipeline using Docker containers. The containerized deployment includes all necessary components: PostgreSQL database, ETL processing service, API server, and Nginx web server.

## Prerequisites

- Docker Engine (version 20.10 or higher)
- Docker Compose Plugin (version 2.0 or higher)

### Install Docker on Ubuntu

```bash
# Add Docker's official GPG key
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update

# Install Docker Engine, containerd, and Docker Compose
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add your user to the docker group
sudo usermod -aG docker $USER
```

> **Note:** Log out and back in for the group changes to take effect, or run `newgrp docker`.

## Quick Deployment

### 1. Set Environment Variables (Optional)

Default values are provided for quick testing. For production, set custom values:

```bash
export DB_PASSWORD='your_secure_password_here'  # default: DbServer123
export DB_USER='etl_user'                       # default: etl_user  
export DB_NAME='stcp_warehouse'                 # default: stcp_warehouse

# Deploy the application
./docker/deploy.sh
```

The script starts all services and runs the initial data load.

### 2. Access the Application

Once deployment is complete, access the application at:

- **Dashboard:** http://localhost
- **API Documentation:** http://localhost/api/docs

## Architecture

The Docker deployment creates 4 containers in a single Docker network:

- `stcp-postgres`: PostgreSQL database (port 5432, internal only)
- `stcp-etl`: ETL process for GTFS data processing
- `stcp-api`: FastAPI web server (port 8000)
- `stcp-nginx`: Nginx for dashboard frontend (port 80)

All containers communicate via the internal `stcp_network` Docker network.

## Configuration

All variables are optional and have default values for quick testing. The most important one to change for production is `DB_PASSWORD` (default: `DbServer123`).

## Management Commands

```bash
# View logs for all services
DB_USER=$DB_USER DB_NAME=$DB_NAME DB_PASSWORD=$DB_PASSWORD docker compose -f docker/docker-compose.yml logs -f

# View logs for specific service
DB_USER=$DB_USER DB_NAME=$DB_NAME DB_PASSWORD=$DB_PASSWORD docker compose -f docker/docker-compose.yml logs -f api

# Stop all services
DB_USER=$DB_USER DB_NAME=$DB_NAME DB_PASSWORD=$DB_PASSWORD docker compose -f docker/docker-compose.yml down

# Stop and remove volumes (deletes data!)
DB_USER=$DB_USER DB_NAME=$DB_NAME DB_PASSWORD=$DB_PASSWORD docker compose -f docker/docker-compose.yml down -v

# Restart services
DB_USER=$DB_USER DB_NAME=$DB_NAME DB_PASSWORD=$DB_PASSWORD docker compose -f docker/docker-compose.yml restart

# Rebuild and restart
DB_USER=$DB_USER DB_NAME=$DB_NAME DB_PASSWORD=$DB_PASSWORD docker compose -f docker/docker-compose.yml up -d --build

# Run ETL manually
DB_USER=$DB_USER DB_NAME=$DB_NAME DB_PASSWORD=$DB_PASSWORD docker compose -f docker/docker-compose.yml run --rm etl
```

## Data Persistence

Data persists in Docker volumes. To reset all data:
```bash
docker compose -f docker/docker-compose.yml down -v
```

## Security

For production deployments:
- Change default database password
- Use strong, unique passwords
- Never commit passwords to version control
- See [../SECURITY.md](../SECURITY.md) for complete guidelines

## Troubleshooting

### Port Already in Use
If ports 80 or 8000 are already in use:
```bash
# Check what's using the port
sudo lsof -i :80
sudo lsof -i :8000

# Stop other services or modify docker-compose.yml to use different ports
```

### Permission Denied
If you get permission errors:
```bash
# Add your user to docker group
sudo usermod -aG docker $USER
# Log out and back in for changes to take effect
```

### Database Connection Issues
```bash
# Check if PostgreSQL is healthy
docker compose -f docker/docker-compose.yml ps

# View database logs
docker compose -f docker/docker-compose.yml logs db
```

