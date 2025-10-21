# Docker Deployment [![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)](https://www.docker.com/) [![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql)](https://www.postgresql.org/) [![Nginx](https://img.shields.io/badge/Nginx-alpine-009639?logo=nginx)](https://nginx.org/)

This is the quickest and easiest way to get the entire project running on your local machine. It uses Docker to manage all the services.

## Prerequisites

You'll need Docker Engine (v20.10+) and Docker Compose (v2.0+).

If you're on Ubuntu, you can follow these steps to install them:

```bash
# Add Docker's official GPG key
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to your Apt sources
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update

# Install Docker Engine and Compose
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add your user to the docker group to run commands without sudo
sudo usermod -aG docker $USER
```

After running `usermod`, you'll need to log out and back in, or run `newgrp docker` for the changes to take effect.

## Quick Start

A deploy script is included to make things simple.

```bash
# From the root of the project, run the script:
./deploy/docker/deploy.sh
```

This script uses the default settings in the `docker-compose.yml` file and starts all services. It will also trigger the initial data pipeline run.

Once it's finished, you can access the application:
- **Dashboard:** [http://localhost](http://localhost)
- **API Docs:** [http://localhost/api/docs](http://localhost/api/docs)

## How It Works

The Docker setup runs four containers that work together:

- `db`: The PostgreSQL database where all the data is stored.
- `etl`: A short-lived container that runs the data processing pipeline and then stops.
- `api`: The FastAPI server that provides the REST API.
- `nginx`: The web server that serves the dashboard and acts as a reverse proxy for the API.

## Managing the Services

Once the services are up and running, you might want to manage them. The best place to run these commands is from the project's **root directory**, to avoid any confusion with file paths.

Here are the most common commands:

```bash
# To see what all the services are doing in real-time
docker compose -f deploy/docker/docker-compose.yml logs -f

# To stop everything
docker compose -f deploy/docker/docker-compose.yml down

# To stop everything and delete the database data
docker compose -f deploy/docker/docker-compose.yml down -v

# To rebuild the images and restart the services
docker compose -f deploy/docker/docker-compose.yml up -d --build

# To manually run the ETL process again
docker compose -f deploy/docker/docker-compose.yml run --rm etl
```

## A Note on Security

The default configuration is fine for local development. If you plan to use this in a production environment, make sure to:
- Change the default database password in the `.env` file or as an environment variable.
- Never commit sensitive credentials to version control.
