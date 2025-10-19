terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

provider "local" {}

variable "aws_region" {
  description = "AWS region for Lightsail instances"
  type        = string
  default     = "eu-west-3"
}

variable "availability_zone" {
  description = "Availability zone within the region"
  type        = string
  default     = "eu-west-3a"
}

variable "ssh_public_key_path" {
  description = "Path to SSH public key for instance access"
  type        = string
  default     = "~/.ssh/id_ed25519_aws.pub"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "gtfs-etl"
}

# Import SSH key pair
resource "aws_lightsail_key_pair" "main" {
  name       = "${var.project_name}-key"
  public_key = file(pathexpand(var.ssh_public_key_path))
}

# ETL Server - Small plan ($12/month: 2GB RAM, 2vCPU, 60GB SSD)
resource "aws_lightsail_instance" "etl_server" {
  name              = "${var.project_name}-etl-server"
  availability_zone = var.availability_zone
  blueprint_id      = "ubuntu_24_04"
  bundle_id         = "small_3_0"
  key_pair_name     = aws_lightsail_key_pair.main.name

  user_data = <<-EOT
    #!/bin/bash
    # Wait for cloud-init to stabilize
    sleep 30

    # System updates
    apt-get update
    DEBIAN_FRONTEND=noninteractive apt-get upgrade -y

    # Remove snapd to save resources
    systemctl stop snapd
    apt-get purge snapd -y
    rm -rf /var/cache/snapd/

    # Basic security tools
    apt-get install -y curl wget unzip python3 python3-pip

    # Set hostname
    hostnamectl set-hostname etl-server

    # Signal completion
    touch /var/lib/cloud/instance/user-data-finished
  EOT

  tags = {
    Project = var.project_name
    Role    = "etl"
  }
}

# Database Server - Small plan ($12/month: 2GB RAM, 2vCPU, 60GB SSD)
resource "aws_lightsail_instance" "db_server" {
  name              = "${var.project_name}-db-server"
  availability_zone = var.availability_zone
  blueprint_id      = "ubuntu_24_04"
  bundle_id         = "small_3_0"
  key_pair_name     = aws_lightsail_key_pair.main.name

  user_data = <<-EOT
    #!/bin/bash
    # Wait for cloud-init to stabilize
    sleep 30

    # System updates
    apt-get update
    DEBIAN_FRONTEND=noninteractive apt-get upgrade -y

    # Remove snapd to save resources
    systemctl stop snapd
    apt-get purge snapd -y
    rm -rf /var/cache/snapd/

    # Basic security tools
    apt-get install -y curl wget unzip python3 python3-pip

    # Set hostname
    hostnamectl set-hostname db-server

    # Signal completion
    touch /var/lib/cloud/instance/user-data-finished
  EOT

  tags = {
    Project = var.project_name
    Role    = "database"
  }
}

# Static IP for ETL Server
resource "aws_lightsail_static_ip" "etl_ip" {
  name = "${var.project_name}-etl-ip"
}

resource "aws_lightsail_static_ip_attachment" "etl_ip_attach" {
  static_ip_name = aws_lightsail_static_ip.etl_ip.name
  instance_name  = aws_lightsail_instance.etl_server.name
}

# Static IP for Database Server
resource "aws_lightsail_static_ip" "db_ip" {
  name = "${var.project_name}-db-ip"
}

resource "aws_lightsail_static_ip_attachment" "db_ip_attach" {
  static_ip_name = aws_lightsail_static_ip.db_ip.name
  instance_name  = aws_lightsail_instance.db_server.name
}

# Generate Ansible inventory file
resource "local_file" "ansible_inventory" {
  content = templatefile("${path.module}/../ansible/hosts.tftpl", {
    db_server_ip  = aws_lightsail_static_ip.db_ip.ip_address
    etl_server_ip = aws_lightsail_static_ip.etl_ip.ip_address
  })

  filename = "${path.module}/../ansible/hosts.ini"

  depends_on = [
    aws_lightsail_static_ip_attachment.etl_ip_attach,
    aws_lightsail_static_ip_attachment.db_ip_attach,
  ]
}

# Outputs
output "etl_server_ip" {
  description = "Public IP address of the ETL server"
  value       = aws_lightsail_static_ip.etl_ip.ip_address
}

output "db_server_ip" {
  description = "Public IP address of the database server"
  value       = aws_lightsail_static_ip.db_ip.ip_address
}

output "next_steps" {
  description = "Next steps for deployment"
  value       = <<-EOT

    Infrastructure created successfully!

    Next steps:
    1. Wait 2-3 minutes for instances to complete initialization
    2. Configure secrets in ansible/secrets.yml
    3. Run Ansible playbook: cd ../ansible && ansible-playbook -i hosts.ini playbook.yml
    4. Access dashboard at: http://${aws_lightsail_static_ip.etl_ip.ip_address}

  EOT
}
