# Production Environment Configuration

environment = "production"
aws_region  = "us-east-1"
owner       = "safety-research-team"

# VPC Configuration
vpc_cidr = "10.0.0.0/16"

# Database Configuration
database_name               = "safety_research_prod"
database_username           = "safetyuser"
rds_instance_class         = "db.r6g.xlarge"
rds_allocated_storage      = 500
rds_backup_retention_days  = 90

# Redis Configuration
redis_node_type = "cache.r6g.large"
redis_num_nodes = 3

# ECS Configuration
app_image        = "ghcr.io/your-org/safety-research-system:latest"
app_port         = 8000
ecs_cpu          = 2048
ecs_memory       = 4096
ecs_desired_count = 4

# Monitoring
alarm_email = "alerts@safety-research.example.com"

# Feature Flags
enable_monitoring = true
enable_backup     = true
enable_multi_az   = true
