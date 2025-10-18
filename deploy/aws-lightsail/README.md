# AWS Lightsail Deployment

This is the production-ready deployment option, using Terraform and Ansible to automatically set up the entire infrastructure on AWS Lightsail.

## How It Works

The setup creates two AWS Lightsail instances that work together:

-   **DB Server:** A small instance running PostgreSQL 16. It's configured for security and only allows access from the ETL server over a private network.
-   **ETL Server:** A micro instance that handles everything else:
    -   Runs the Prefect orchestration engine.
    -   Serves the FastAPI application.
    -   Hosts the Nginx web server and dashboard.
    -   Is accessible to the public.

This architecture is designed to be cost-effective (around $19/month at the time of writing) and secure.

## Prerequisites

You'll need a few tools on your local machine to manage the deployment:

-   Terraform
-   Ansible
-   AWS CLI (recommended)

If you're on Ubuntu, you can install them like this:

```bash
# Terraform
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install terraform

# Ansible & AWS CLI
pip install ansible awscli
```

You also need to configure your AWS credentials:

```bash
aws configure
```

## Setup Steps

1.  **SSH Key:** Generate an SSH key pair that will be used to access the Lightsail instances.

    ```bash
    ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_aws -C "aws-lightsail"
    ```

    If you use a different name, make sure to update the `ssh_public_key_path` variable in `terraform/main.tf`.

2.  **Configuration:** Create a secrets file for Ansible to use.

    ```bash
    cp ansible/secrets.yml.example ansible/secrets.yml
    nano ansible/secrets.yml
    ```

    You'll need to fill in a secure password for the database user. You can generate one with `openssl rand -base64 32`.

## Deployment

A deployment script is included to automate the process:

```bash
# From the aws-lightsail directory, run the script:
./deploy.sh
```

This script does everything:
1.  Initializes Terraform.
2.  Creates the AWS Lightsail instances and networking.
3.  Waits for the instances to be ready.
4.  Runs an Ansible playbook to configure both servers, install the software, and clone the project repository.
5.  Starts the services and runs the initial ETL pipeline.

The whole process usually takes about 10-15 minutes.

## Accessing the Application

Once the deployment is complete, the script will output the IP address of the ETL server.

-   **Dashboard:** `http://<etl-server-ip>`
-   **API Docs:** `http://<etl-server-ip>/api/docs`
-   **Prefect UI:** `http://<etl-server-ip>:4200`

## Managing the Infrastructure

-   **Updating the Application:** SSH into the ETL server, pull the latest code from Git, and restart the services.

    ```bash
    ssh -i ~/.ssh/id_ed25519_aws ubuntu@<etl-server-ip>
    cd /home/ubuntu/gtfs-app
    git pull origin main
    sudo systemctl restart gtfs-api prefect-server
    ```

-   **Destroying the Infrastructure:** When you no longer need the deployment, you can tear it down completely with Terraform.

    ```bash
    cd terraform
    terraform destroy
    ```

This will remove all the resources created on AWS.

## Security

This deployment includes several security best practices out-of-the-box:
-   SSH password authentication is disabled (key-based only).
-   A UFW firewall is configured on both servers.
-   `fail2ban` is installed to prevent brute-force attacks.
-   The database is only accessible from the ETL server's private IP.