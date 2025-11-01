# Safety Research System - Terraform Infrastructure

This directory contains Terraform configurations for deploying the Safety Research System to AWS.

## Architecture Overview

The infrastructure includes:

- **VPC**: Multi-AZ Virtual Private Cloud with public and private subnets
- **ECS**: Elastic Container Service for running the application
- **RDS**: PostgreSQL database for persistent storage
- **ElastiCache**: Redis for caching and session management
- **ALB**: Application Load Balancer for traffic distribution
- **CloudWatch**: Monitoring, logging, and alerting
- **Secrets Manager**: Secure storage for sensitive configuration

## Directory Structure

```
terraform/
├── main.tf                 # Root module orchestration
├── variables.tf            # Variable definitions
├── outputs.tf             # Output values
├── backend.hcl            # Backend configuration
├── modules/
│   ├── vpc/               # VPC and networking
│   ├── security/          # Security groups
│   ├── rds/               # PostgreSQL database
│   ├── elasticache/       # Redis cache
│   ├── ecs/               # ECS cluster and services
│   └── monitoring/        # CloudWatch alarms
└── environments/
    ├── dev/               # Development environment
    ├── staging/           # Staging environment
    └── production/        # Production environment
```

## Prerequisites

1. **Terraform**: Install Terraform >= 1.5
   ```bash
   # macOS
   brew install terraform

   # Linux
   wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
   unzip terraform_1.6.0_linux_amd64.zip
   sudo mv terraform /usr/local/bin/
   ```

2. **AWS CLI**: Configure AWS credentials
   ```bash
   aws configure
   ```

3. **S3 Backend**: Create S3 bucket for Terraform state
   ```bash
   aws s3api create-bucket \
     --bucket safety-research-terraform-state \
     --region us-east-1

   aws s3api put-bucket-versioning \
     --bucket safety-research-terraform-state \
     --versioning-configuration Status=Enabled

   aws dynamodb create-table \
     --table-name terraform-state-lock \
     --attribute-definitions AttributeName=LockID,AttributeType=S \
     --key-schema AttributeName=LockID,KeyType=HASH \
     --billing-mode PAY_PER_REQUEST
   ```

## Usage

### Initialize Terraform

```bash
cd infrastructure/terraform
terraform init -backend-config=environments/production/backend.hcl
```

### Plan Deployment

```bash
terraform plan -var-file=environments/production/terraform.tfvars
```

### Apply Infrastructure

```bash
terraform apply -var-file=environments/production/terraform.tfvars
```

### Destroy Infrastructure

```bash
terraform destroy -var-file=environments/production/terraform.tfvars
```

## Environment-Specific Deployment

### Development

```bash
terraform workspace select dev
terraform apply -var-file=environments/dev/terraform.tfvars
```

### Staging

```bash
terraform workspace select staging
terraform apply -var-file=environments/staging/terraform.tfvars
```

### Production

```bash
terraform workspace select production
terraform apply -var-file=environments/production/terraform.tfvars
```

## Secrets Management

Sensitive values should be stored in AWS Secrets Manager:

```bash
# Create database password
aws secretsmanager create-secret \
  --name production/database/master-password \
  --secret-string "YourSecurePassword123!"

# Create API keys
aws secretsmanager create-secret \
  --name production/api/openai-key \
  --secret-string "sk-..."

aws secretsmanager create-secret \
  --name production/api/anthropic-key \
  --secret-string "sk-ant-..."
```

Update `terraform.tfvars` with secret ARNs:

```hcl
secrets_arns = {
  database_password = "arn:aws:secretsmanager:us-east-1:123456789012:secret:production/database/master-password-abc123"
  openai_api_key   = "arn:aws:secretsmanager:us-east-1:123456789012:secret:production/api/openai-key-xyz789"
  anthropic_api_key = "arn:aws:secretsmanager:us-east-1:123456789012:secret:production/api/anthropic-key-def456"
}
```

## Cost Estimation

Approximate monthly costs for production environment:

| Service | Configuration | Monthly Cost |
|---------|--------------|--------------|
| ECS (4 tasks) | 2 vCPU, 4GB RAM | $120 |
| RDS (PostgreSQL) | db.r6g.xlarge | $500 |
| ElastiCache (Redis) | cache.r6g.large x 3 | $400 |
| ALB | Standard | $25 |
| NAT Gateway | 3 AZs | $100 |
| Data Transfer | ~1TB | $90 |
| **Total** | | **~$1,235/month** |

> Note: Costs vary based on usage. Use AWS Cost Calculator for precise estimates.

## Security Considerations

1. **Encryption at Rest**: All data encrypted (RDS, EBS, S3)
2. **Encryption in Transit**: TLS 1.2+ enforced
3. **Network Isolation**: Private subnets for all data services
4. **Access Control**: IAM roles with least privilege
5. **Secret Management**: AWS Secrets Manager for all secrets
6. **Audit Logging**: CloudTrail enabled for all API calls
7. **VPC Flow Logs**: Network traffic logging enabled

## Monitoring and Alerts

CloudWatch alarms are configured for:

- ECS task health
- RDS CPU/memory/connections
- Redis CPU/memory
- ALB target health
- Application errors (5xx)
- High latency (P95 > 5s)

Alerts are sent to the email specified in `alarm_email` variable.

## Backup and Disaster Recovery

1. **RDS Backups**:
   - Automated daily backups
   - 90-day retention (production)
   - Point-in-time recovery enabled

2. **Application State**:
   - Stateless application design
   - Session data in Redis (replicated)

3. **Disaster Recovery Plan**:
   - Multi-AZ deployment
   - Cross-region replication (optional)
   - Automated failover

## Scaling

### Horizontal Scaling (ECS)

```bash
# Update desired count
terraform apply -var="ecs_desired_count=8"
```

### Vertical Scaling (RDS)

```bash
# Update instance class
terraform apply -var="rds_instance_class=db.r6g.2xlarge"
```

## Troubleshooting

### Common Issues

1. **State Lock Error**
   ```bash
   # Force unlock (use with caution)
   terraform force-unlock <lock-id>
   ```

2. **Resource Already Exists**
   ```bash
   # Import existing resource
   terraform import aws_s3_bucket.example my-bucket-name
   ```

3. **Insufficient Permissions**
   - Ensure IAM user/role has necessary permissions
   - Review CloudTrail logs for denied actions

## Maintenance

### State Management

```bash
# List resources in state
terraform state list

# Show specific resource
terraform state show aws_ecs_cluster.main

# Move resource in state
terraform state mv aws_instance.old aws_instance.new

# Remove resource from state
terraform state rm aws_instance.example
```

### Upgrading Terraform

```bash
# Check for updates
terraform version

# Upgrade providers
terraform init -upgrade
```

## CI/CD Integration

This infrastructure is designed to work with GitHub Actions:

```yaml
- name: Terraform Apply
  run: |
    cd infrastructure/terraform
    terraform init -backend-config=environments/production/backend.hcl
    terraform apply -var-file=environments/production/terraform.tfvars -auto-approve
```

## Support

For issues or questions:
- Internal: #safety-research-infra Slack channel
- Email: infra-team@safety-research.example.com
- Docs: https://docs.safety-research.example.com/infrastructure

## References

- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS ECS Best Practices](https://docs.aws.amazon.com/AmazonECS/latest/bestpracticesguide/)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
