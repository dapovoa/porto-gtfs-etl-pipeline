# Bare Metal Installation Guide

This guide is for those who prefer to set up the project manually on their own Linux servers. It provides more control but requires more hands-on configuration.

## Architecture

The recommended setup uses two servers:

-   **DB Server:** A dedicated server for the PostgreSQL database.
-   **ETL Server:** A server to run the Python application (Prefect, FastAPI) and the Nginx web server.

You can install everything on a single server, but separating the database is a good practice for performance and security.

---

## 1. DB Server Setup

First, we'll prepare and configure the database server.

### 1.1. Initial Server Hardening

It's always a good idea to start with some basic security measures.

```bash
# Update all packages
sudo apt update -y && sudo apt upgrade -y

# Configure the firewall to allow SSH and deny other incoming traffic
sudo ufw allow openssh
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw --force enable

# Install fail2ban to protect against brute-force attacks
sudo apt install -y fail2ban

# Disable password-based SSH authentication (optional, but recommended)
# Edit /etc/ssh/sshd_config and set PasswordAuthentication to "no"
# sudo nano /etc/ssh/sshd_config
# sudo systemctl restart ssh
```

### 1.2. Install PostgreSQL

We'll install PostgreSQL 16 from the official PGDG repository to get the latest version.

```bash
# Add the PostgreSQL repository
sudo apt install -y curl ca-certificates
sudo install -d /usr/share/postgresql-common/pgdg
sudo curl -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.asc --fail https://www.postgresql.org/media/keys/ACCC4CF8.asc
. /etc/os-release
sudo sh -c "echo 'deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.asc] https://apt.postgresql.org/pub/repos/apt $VERSION_CODENAME-pgdg main' > /etc/apt/sources.list.d/pgdg.list"

# Install PostgreSQL
sudo apt update -y && sudo apt install -y postgresql-16
```

### 1.3. Configure PostgreSQL

Next, we need to configure PostgreSQL to allow connections from our ETL server.

```bash
# Edit the main configuration file
sudo nano /etc/postgresql/16/main/postgresql.conf
```

Find and set `listen_addresses` to allow remote connections. Replace `<your-db-server-ip>` with the actual IP.

```ini
listen_addresses = '<your-db-server-ip>, localhost'
```

Now, configure access control to specify which clients can connect.

```bash
# Edit the host-based authentication file
sudo nano /etc/postgresql/16/main/pg_hba.conf
```

Add a line to allow the ETL server to connect. Replace `<etl-server-ip>` with its IP address.

```
# TYPE  DATABASE        USER            ADDRESS                 METHOD
host    all             all             <etl-server-ip>/32      scram-sha-256
```

Finally, restart PostgreSQL to apply the changes.

```bash
sudo systemctl restart postgresql
```

### 1.4. Create the Database and User

Log in to PostgreSQL to create the user and database for our application.

```bash
sudo -u postgres psql
```

Run the following SQL commands. Replace `<your-secure-password>` with a strong password.

```sql
CREATE USER etl_user WITH PASSWORD '<your-secure-password>';
CREATE DATABASE stcp_warehouse;
GRANT ALL PRIVILEGES ON DATABASE stcp_warehouse TO etl_user;

-- Connect to the new database to set up schemas
\c stcp_warehouse

CREATE SCHEMA raw;
CREATE SCHEMA analytics;

GRANT ALL ON SCHEMA raw TO etl_user;
GRANT ALL ON SCHEMA analytics TO etl_user;

ALTER DEFAULT PRIVILEGES IN SCHEMA raw GRANT ALL ON TABLES TO etl_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA analytics GRANT ALL ON TABLES TO etl_user;

\q
```

---

## 2. ETL Server Setup

Now, let's configure the server that will run the application code.

### 2.1. Initial Server Hardening

Just like the DB server, we'll start with some basic security.

```bash
# Update all packages
sudo apt update -y && sudo apt upgrade -y

# Configure the firewall
sudo ufw allow openssh
sudo ufw allow 'Nginx Full' # Allow HTTP and HTTPS traffic
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw --force enable
```

### 2.2. Install Dependencies

Install Python, Git, and the PostgreSQL client tools.

```bash
sudo apt install -y python3-venv python3-pip git postgresql-client-16
```

### 2.3. Set Up the Project

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/dapovoa/gtfs-etl-pipeline.git ~/gtfs-app
    cd ~/gtfs-app
    ```

2.  **Create a Python virtual environment:**

    ```bash
    python3 -m venv ~/python-env
    source ~/python-env/bin/activate
    pip install --upgrade pip
    ```

3.  **Install the Python dependencies:**

    ```bash
    pip install -r src/requirements.txt
    ```

4.  **Set up environment variables:** The application needs to know how to connect to the database. The most common way is to create a `.env` file in the `src` directory.

    ```bash
    nano ~/gtfs-app/src/.env
    ```

    Add the following, replacing the values with your own:

    ```
    DB_HOST='<your-db-server-ip>'
    DB_PORT='5432'
    DB_NAME='stcp_warehouse'
    DB_USER='etl_user'
    DB_PASSWORD='<your-secure-password>'
    ```

### 2.4. Run the Initial Pipeline

Before setting up the services, run the main pipeline manually to ensure everything is working and to populate the database.

```bash
cd ~/gtfs-app/src
source ~/python-env/bin/activate
python main_pipeline.py
```

---

## 3. Nginx Setup

We'll use Nginx as a reverse proxy to serve the dashboard and the API.

1.  **Install Nginx:**

    ```bash
    sudo apt install -y nginx
    ```

2.  **Create an Nginx configuration file:**

    ```bash
    sudo nano /etc/nginx/sites-available/gtfs-dashboard
    ```

    Paste the following configuration. Replace `<your-server-domain-or-ip>` with your server's public IP or domain name.

    ```nginx
    server {
        listen 80;
        server_name <your-server-domain-or-ip>;

        # Serve the static dashboard files
        root /var/www/gtfs-dashboard;
        index index.html;

        location / {
            try_files $uri $uri/ =404;
        }

        # Proxy API requests to the FastAPI application
        location /api {
            proxy_pass http://127.0.0.1:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
    ```

3.  **Deploy the dashboard files and enable the site:**

    ```bash
    # Copy the dashboard files to the web root
    sudo cp -r ~/gtfs-app/src/dashboard /var/www/gtfs-dashboard

    # Enable the new configuration
    sudo ln -s /etc/nginx/sites-available/gtfs-dashboard /etc/nginx/sites-enabled/

    # Test and restart Nginx
    sudo nginx -t
    sudo systemctl restart nginx
    ```

---

## 4. Automate with Systemd and Cron

To make sure the API and Prefect server run continuously and the data is updated daily, we'll use `systemd` and `cron`.

### 4.1. API Server Service

Create a `systemd` service to manage the FastAPI application.

```bash
sudo nano /etc/systemd/system/gtfs-api.service
```

Paste the following, replacing `<your-username>` with your actual username.

```ini
[Unit]
Description=GTFS API Server
After=network.target

[Service]
Type=simple
User=<your-username>
Group=<your-username>
WorkingDirectory=/home/<your-username>/gtfs-app/src
Environment="PATH=/home/<your-username>/python-env/bin"
ExecStart=/home/<your-username>/python-env/bin/uvicorn api_server:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 4.2. Prefect Server Service

Create another service for the Prefect server.

```bash
sudo nano /etc/systemd/system/prefect-server.service
```

Paste the following, again replacing `<your-username>` and `<your-etl-server-ip>`.

```ini
[Unit]
Description=Prefect Server
After=network.target

[Service]
Type=simple
User=<your-username>
Group=<your-username>
WorkingDirectory=/home/<your-username>/gtfs-app/src
Environment="PATH=/home/<your-username>/python-env/bin"
ExecStart=/home/<your-username>/python-env/bin/prefect server start --host <your-etl-server-ip> --port 4200
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 4.3. Enable and Start the Services

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now gtfs-api.service
sudo systemctl enable --now prefect-server.service

# Check their status
sudo systemctl status gtfs-api.service
sudo systemctl status prefect-server.service
```

### 4.4. Schedule Daily Updates with Cron

Finally, set up a cron job to run the update script every day.

```bash
# Open the crontab editor
EDITOR=nano crontab -e
```

Add this line to run the script every day at 6 AM.

```cron
0 6 * * * cd /home/<your-username>/gtfs-app/src && /home/<your-username>/python-env/bin/python check_and_update.py >> /var/log/gtfs-update.log 2>&1
```
