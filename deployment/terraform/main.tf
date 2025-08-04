# Terraform configuration for N2S Streamlit Server
# Supports AWS, GCP, Azure, and DigitalOcean

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Variables
variable "cloud_provider" {
  description = "Cloud provider (aws, gcp, azure, digitalocean)"
  type        = string
  default     = "aws"
}

variable "instance_type" {
  description = "Instance type/size"
  type        = string
  default     = "t3.medium"
}

variable "region" {
  description = "Deployment region"
  type        = string
  default     = "us-east-1"
}

variable "key_name" {
  description = "SSH key pair name"
  type        = string
}

variable "allowed_cidr_blocks" {
  description = "CIDR blocks allowed to access the server"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

# AWS Provider Configuration
provider "aws" {
  region = var.region
}

# Security Group
resource "aws_security_group" "streamlit_server" {
  name_prefix = "streamlit-server-"
  description = "Security group for N2S Streamlit Server"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.allowed_cidr_blocks
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "streamlit-server-sg"
    Project = "n2s-streamlit-server"
  }
}

# EC2 Instance
resource "aws_instance" "streamlit_server" {
  ami           = "ami-0c7217cdde317cfec" # Ubuntu 24.04 LTS
  instance_type = var.instance_type
  key_name      = var.key_name

  vpc_security_group_ids = [aws_security_group.streamlit_server.id]

  root_block_device {
    volume_type = "gp3"
    volume_size = 20
    encrypted   = true
  }

  user_data = base64encode(templatefile("${path.module}/user-data.sh", {
    github_repo = "https://github.com/miket-llc/n2s-streamlit-server.git"
  }))

  tags = {
    Name = "n2s-streamlit-server"
    Project = "n2s-streamlit-server"
    Environment = "production"
  }
}

# Elastic IP
resource "aws_eip" "streamlit_server" {
  instance = aws_instance.streamlit_server.id
  domain   = "vpc"

  tags = {
    Name = "streamlit-server-eip"
    Project = "n2s-streamlit-server"
  }
}

# Outputs
output "public_ip" {
  value = aws_eip.streamlit_server.public_ip
}

output "public_dns" {
  value = aws_eip.streamlit_server.public_dns
}

output "ssh_command" {
  value = "ssh -i ~/.ssh/${var.key_name}.pem ubuntu@${aws_eip.streamlit_server.public_ip}"
}

output "web_url" {
  value = "http://${aws_eip.streamlit_server.public_ip}/"
}
