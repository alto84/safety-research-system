# Main Terraform configuration for Safety Research System
# This is the root module that orchestrates all infrastructure components

terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }

  # Backend configuration for state management
  backend "s3" {
    # Configure these values in backend.hcl
    # bucket         = "safety-research-terraform-state"
    # key            = "production/terraform.tfstate"
    # region         = "us-east-1"
    # encrypt        = true
    # dynamodb_table = "terraform-state-lock"
  }
}

# Configure AWS Provider
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "SafetyResearchSystem"
      Environment = var.environment
      ManagedBy   = "Terraform"
      Owner       = var.owner
    }
  }
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

# Local variables
locals {
  name_prefix = "safety-research-${var.environment}"
  common_tags = {
    Project     = "SafetyResearchSystem"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# VPC Module
module "vpc" {
  source = "./modules/vpc"

  environment         = var.environment
  vpc_cidr           = var.vpc_cidr
  availability_zones = slice(data.aws_availability_zones.available.names, 0, 3)
  name_prefix        = local.name_prefix

  tags = local.common_tags
}

# Security Module
module "security" {
  source = "./modules/security"

  environment = var.environment
  vpc_id      = module.vpc.vpc_id
  name_prefix = local.name_prefix

  tags = local.common_tags
}

# RDS (PostgreSQL) Module
module "rds" {
  source = "./modules/rds"

  environment            = var.environment
  vpc_id                = module.vpc.vpc_id
  subnet_ids            = module.vpc.private_subnet_ids
  security_group_ids    = [module.security.rds_security_group_id]
  instance_class        = var.rds_instance_class
  allocated_storage     = var.rds_allocated_storage
  database_name         = var.database_name
  master_username       = var.database_username
  backup_retention_days = var.rds_backup_retention_days
  name_prefix           = local.name_prefix

  tags = local.common_tags
}

# ElastiCache (Redis) Module
module "elasticache" {
  source = "./modules/elasticache"

  environment         = var.environment
  vpc_id             = module.vpc.vpc_id
  subnet_ids         = module.vpc.private_subnet_ids
  security_group_ids = [module.security.redis_security_group_id]
  node_type          = var.redis_node_type
  num_cache_nodes    = var.redis_num_nodes
  name_prefix        = local.name_prefix

  tags = local.common_tags
}

# ECS Cluster Module
module "ecs" {
  source = "./modules/ecs"

  environment        = var.environment
  vpc_id            = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  public_subnet_ids  = module.vpc.public_subnet_ids
  security_group_ids = [module.security.ecs_security_group_id]

  # Application configuration
  app_image         = var.app_image
  app_port          = var.app_port
  cpu               = var.ecs_cpu
  memory            = var.ecs_memory
  desired_count     = var.ecs_desired_count

  # Environment variables
  database_url      = module.rds.connection_string
  redis_url         = module.elasticache.connection_string

  # Secrets ARNs (from AWS Secrets Manager)
  secrets_arns = var.secrets_arns

  name_prefix = local.name_prefix
  tags        = local.common_tags
}

# Monitoring Module
module "monitoring" {
  source = "./modules/monitoring"

  environment         = var.environment
  ecs_cluster_name   = module.ecs.cluster_name
  ecs_service_name   = module.ecs.service_name
  rds_instance_id    = module.rds.instance_id
  redis_cluster_id   = module.elasticache.cluster_id
  alb_arn           = module.ecs.alb_arn

  alarm_email = var.alarm_email
  name_prefix = local.name_prefix

  tags = local.common_tags
}

# Outputs
output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "alb_dns_name" {
  description = "Application Load Balancer DNS name"
  value       = module.ecs.alb_dns_name
}

output "ecs_cluster_name" {
  description = "ECS Cluster name"
  value       = module.ecs.cluster_name
}

output "rds_endpoint" {
  description = "RDS endpoint"
  value       = module.rds.endpoint
  sensitive   = true
}

output "redis_endpoint" {
  description = "Redis endpoint"
  value       = module.elasticache.endpoint
  sensitive   = true
}
