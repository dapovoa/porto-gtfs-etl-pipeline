#!/bin/bash

set -e

echo "=========================================="
echo "GTFS ETL Pipeline - AWS Lightsail Deploy"
echo "=========================================="
echo ""

# Check prerequisites
command -v terraform >/dev/null 2>&1 || { echo "Error: terraform is not installed. Install from https://www.terraform.io/downloads"; exit 1; }
command -v ansible >/dev/null 2>&1 || { echo "Error: ansible is not installed. Run: pip install ansible"; exit 1; }

# Check if secrets.yml exists
if [ ! -f "ansible/secrets.yml" ]; then
    echo "Error: ansible/secrets.yml not found"
    echo "Please copy ansible/secrets.yml.example to ansible/secrets.yml and configure your credentials"
    exit 1
fi

# Check if SSH key exists
if [ ! -f ~/.ssh/id_ed25519_aws ]; then
    echo "Error: SSH key not found at ~/.ssh/id_ed25519_aws"
    echo "Please create your SSH key pair or update the path in terraform/main.tf"
    exit 1
fi

echo "Step 1: Initializing Terraform"
cd terraform
terraform init

echo ""
echo "Step 2: Planning infrastructure changes"
terraform plan

echo ""
read -p "Do you want to proceed with infrastructure creation? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Deployment cancelled"
    exit 0
fi

echo ""
echo "Step 3: Creating AWS infrastructure"
terraform apply -auto-approve

echo ""
echo "Step 4: Waiting for instances to complete initialization (2 minutes)"
sleep 120

echo ""
echo "Step 5: Running Ansible playbook to configure servers"
cd ../ansible

# Run Ansible playbook
ansible-playbook -i hosts.ini playbook.yml

echo ""
echo "=========================================="
echo "Deployment completed successfully!"
echo "=========================================="
echo ""

# Get the ETL server IP from Terraform output
cd ../terraform
ETL_IP=$(terraform output -raw etl_server_ip)

echo "Access your dashboard at: http://$ETL_IP"
echo "Prefect UI available at: http://$ETL_IP:4200"
echo ""
echo "To destroy the infrastructure later, run:"
echo "  cd terraform && terraform destroy"
echo ""
