# Deployment Runbook - Safety Research System

This runbook provides step-by-step procedures for deploying and operating the Safety Research System in production.

## Quick Reference

| Environment | URL | AWS Account | Region |
|-------------|-----|-------------|--------|
| Development | http://localhost:8000 | Local | N/A |
| Staging | https://staging.safety-research.example.com | 123456789012 | us-east-1 |
| Production | https://safety-research.example.com | 987654321098 | us-east-1 |

## Table of Contents

1. [Pre-Deployment](#pre-deployment)
2. [Deployment Procedures](#deployment-procedures)
3. [Rollback Procedures](#rollback-procedures)
4. [Common Operations](#common-operations)
5. [Troubleshooting](#troubleshooting)
6. [Emergency Procedures](#emergency-procedures)

---

## Pre-Deployment

### Prerequisites

- [ ] AWS CLI configured with appropriate credentials
- [ ] Docker installed and running
- [ ] Kubectl configured (if using Kubernetes)
- [ ] Terraform installed (for infrastructure changes)
- [ ] Access to AWS Secrets Manager
- [ ] Access to GitHub repository
- [ ] VPN connection to production network (if required)

### Pre-Deployment Checklist

```bash
# 1. Verify AWS credentials
aws sts get-caller-identity

# 2. Verify you're on the correct git branch
git branch --show-current

# 3. Ensure all changes are committed
git status

# 4. Pull latest changes
git pull origin main

# 5. Run tests locally
pytest tests/ -v

# 6. Build Docker image locally
docker build -t safety-research-system:test .

# 7. Run security scan
docker run --rm aquasec/trivy image safety-research-system:test
```

---

## Deployment Procedures

### Standard Deployment (Staging/Production)

#### Step 1: Create Backup

```bash
# Create database backup
./scripts/backup.sh production

# Verify backup was created
aws s3 ls s3://safety-research-backups/production/database/
```

#### Step 2: Build and Push Docker Image

```bash
# Login to container registry
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Build image
docker build -t ghcr.io/your-org/safety-research-system:$(git rev-parse --short HEAD) .

# Tag as latest
docker tag ghcr.io/your-org/safety-research-system:$(git rev-parse --short HEAD) \
           ghcr.io/your-org/safety-research-system:production-latest

# Push images
docker push ghcr.io/your-org/safety-research-system:$(git rev-parse --short HEAD)
docker push ghcr.io/your-org/safety-research-system:production-latest
```

#### Step 3: Deploy Application

```bash
# Run deployment script
./scripts/deploy.sh production

# Or deploy manually using AWS CLI
aws ecs update-service \
    --cluster safety-research-production \
    --service safety-research-api \
    --force-new-deployment \
    --region us-east-1

# Wait for deployment
aws ecs wait services-stable \
    --cluster safety-research-production \
    --services safety-research-api \
    --region us-east-1
```

#### Step 4: Verify Deployment

```bash
# Check health endpoint
curl https://safety-research.example.com/health

# Expected response:
# {"status":"healthy","timestamp":"...","version":"0.1.0"}

# Check service status
aws ecs describe-services \
    --cluster safety-research-production \
    --services safety-research-api \
    --region us-east-1

# Run smoke tests
pytest tests/ -v -k smoke
```

#### Step 5: Monitor

```bash
# Watch CloudWatch logs
aws logs tail /aws/ecs/safety-research-production --follow

# Check metrics in Grafana
# https://grafana.safety-research.example.com

# Monitor error rates
# Should be < 0.1% for 5xx errors
```

### Database Migration Deployment

When deploying changes that include database migrations:

```bash
# 1. Create backup (CRITICAL)
./scripts/backup.sh production

# 2. Connect to database (use bastion host or SSM Session Manager)
aws ssm start-session --target <bastion-instance-id>

# 3. Test migration on restored backup first
# Create test database from backup
# Run migration: alembic upgrade head
# Verify data integrity

# 4. Run migration on production
alembic upgrade head

# 5. Verify migration
alembic current

# 6. Deploy application
./scripts/deploy.sh production
```

### Infrastructure Changes (Terraform)

```bash
# 1. Navigate to terraform directory
cd infrastructure/terraform

# 2. Initialize Terraform
terraform init -backend-config=environments/production/backend.hcl

# 3. Select workspace
terraform workspace select production

# 4. Plan changes
terraform plan -var-file=environments/production/terraform.tfvars -out=tfplan

# 5. Review plan carefully
# Look for any destroy operations or unexpected changes

# 6. Apply changes
terraform apply tfplan

# 7. Verify infrastructure
aws ecs describe-clusters --clusters safety-research-production
```

---

## Rollback Procedures

### Application Rollback

```bash
# Option 1: Use rollback script (recommended)
./scripts/rollback.sh production

# Option 2: Manual rollback
# Get previous task definition
aws ecs list-task-definitions \
    --family-prefix safety-research-production-api \
    --sort DESC \
    --max-items 2

# Update service with previous task definition
aws ecs update-service \
    --cluster safety-research-production \
    --service safety-research-api \
    --task-definition <previous-task-definition-arn>

# Wait for rollback
aws ecs wait services-stable \
    --cluster safety-research-production \
    --services safety-research-api
```

### Database Rollback

```bash
# 1. Stop application
aws ecs update-service \
    --cluster safety-research-production \
    --service safety-research-api \
    --desired-count 0

# 2. Restore from RDS snapshot
aws rds restore-db-instance-from-db-snapshot \
    --db-instance-identifier safety-research-production-db-restored \
    --db-snapshot-identifier <snapshot-id>

# 3. Update DNS or application config to point to restored database

# 4. Restart application
aws ecs update-service \
    --cluster safety-research-production \
    --service safety-research-api \
    --desired-count 4
```

---

## Common Operations

### Scaling

#### Horizontal Scaling (Add more tasks)

```bash
# Scale up
aws ecs update-service \
    --cluster safety-research-production \
    --service safety-research-api \
    --desired-count 8

# Scale down
aws ecs update-service \
    --cluster safety-research-production \
    --service safety-research-api \
    --desired-count 2
```

#### Vertical Scaling (Increase task resources)

```bash
# Update task definition with more CPU/memory
# Then update service to use new task definition
aws ecs update-service \
    --cluster safety-research-production \
    --service safety-research-api \
    --task-definition <new-task-definition>
```

### Viewing Logs

```bash
# Tail application logs
aws logs tail /aws/ecs/safety-research-production --follow

# Filter for errors
aws logs filter-pattern /aws/ecs/safety-research-production \
    --filter-pattern "ERROR"

# Export logs to S3
aws logs create-export-task \
    --log-group-name /aws/ecs/safety-research-production \
    --from $(date -d '1 day ago' +%s)000 \
    --to $(date +%s)000 \
    --destination s3://safety-research-logs/exports
```

### Updating Secrets

```bash
# Update secret in Secrets Manager
aws secretsmanager update-secret \
    --secret-id production/api/openai-key \
    --secret-string "sk-new-key..."

# Force new deployment to pick up new secrets
aws ecs update-service \
    --cluster safety-research-production \
    --service safety-research-api \
    --force-new-deployment
```

### Database Maintenance

```bash
# Connect to database
aws ssm start-session --target <bastion-instance-id>

# Run VACUUM
psql -h <db-endpoint> -U safetyuser -d safety_research -c "VACUUM ANALYZE;"

# Check database size
psql -h <db-endpoint> -U safetyuser -d safety_research -c "\l+"

# Check table sizes
psql -h <db-endpoint> -U safetyuser -d safety_research -c "\dt+"
```

---

## Troubleshooting

### Application Won't Start

**Symptoms**: ECS tasks keep restarting, never reach RUNNING state

**Diagnosis**:
```bash
# Check task status
aws ecs describe-tasks \
    --cluster safety-research-production \
    --tasks <task-id>

# Check container logs
aws logs tail /aws/ecs/safety-research-production --follow
```

**Common Causes**:
1. **Port already in use**: Check security groups, task definition
2. **Secrets not accessible**: Verify IAM role permissions
3. **Database connection failed**: Check security groups, credentials
4. **Health check failing**: Review health check endpoint

**Resolution**:
```bash
# Fix issue in code/config
# Build new image
# Deploy with fix
./scripts/deploy.sh production
```

### High Error Rate

**Symptoms**: CloudWatch alarms for high 5xx errors

**Diagnosis**:
```bash
# Check error logs
aws logs filter-pattern /aws/ecs/safety-research-production \
    --filter-pattern "ERROR" \
    --start-time $(date -d '1 hour ago' +%s)000

# Check ALB metrics
aws cloudwatch get-metric-statistics \
    --namespace AWS/ApplicationELB \
    --metric-name HTTPCode_Target_5XX_Count \
    --dimensions Name=LoadBalancer,Value=<alb-arn> \
    --start-time $(date -d '1 hour ago' --iso-8601) \
    --end-time $(date --iso-8601) \
    --period 300 \
    --statistics Sum
```

**Common Causes**:
1. **Database connection pool exhausted**: Increase pool size
2. **Timeout errors**: Increase timeout values
3. **Dependency failure**: Check external API status
4. **Memory leak**: Check memory metrics, restart tasks

### Database Connection Issues

**Symptoms**: "Connection refused" or "Too many connections"

**Diagnosis**:
```bash
# Check active connections
psql -h <db-endpoint> -U safetyuser -c \
    "SELECT count(*) FROM pg_stat_activity;"

# Check max connections
psql -h <db-endpoint> -U safetyuser -c \
    "SHOW max_connections;"
```

**Resolution**:
```bash
# Terminate idle connections
psql -h <db-endpoint> -U safetyuser -c \
    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity
     WHERE state = 'idle' AND state_change < NOW() - INTERVAL '1 hour';"

# Or increase max_connections in RDS parameter group
aws rds modify-db-parameter-group \
    --db-parameter-group-name safety-research-production \
    --parameters "ParameterName=max_connections,ParameterValue=200,ApplyMethod=immediate"
```

### Performance Degradation

**Symptoms**: Slow response times, high latency

**Diagnosis**:
```bash
# Check RDS performance insights
# https://console.aws.amazon.com/rds/performance-insights

# Check slow queries
psql -h <db-endpoint> -U safetyuser -c \
    "SELECT query, calls, total_time, mean_time
     FROM pg_stat_statements
     ORDER BY mean_time DESC LIMIT 10;"

# Check cache hit rate
redis-cli -h <redis-endpoint> INFO stats
```

**Resolution**:
1. Add database indexes
2. Optimize slow queries
3. Increase cache TTL
4. Scale up infrastructure

---

## Emergency Procedures

### Complete Service Outage

1. **Assess the situation**
   ```bash
   # Check all components
   curl https://safety-research.example.com/health
   aws ecs describe-services --cluster safety-research-production
   ```

2. **Notify stakeholders**
   - Post in #incidents Slack channel
   - Update status page
   - Page on-call engineer if not already involved

3. **Attempt quick fixes**
   ```bash
   # Restart tasks
   aws ecs update-service \
       --cluster safety-research-production \
       --service safety-research-api \
       --force-new-deployment
   ```

4. **If quick fix doesn't work, rollback**
   ```bash
   ./scripts/rollback.sh production
   ```

5. **If rollback doesn't work, restore from backup**
   ```bash
   # Follow database rollback procedure
   # See "Database Rollback" section
   ```

### Data Breach / Security Incident

1. **Immediate actions**
   - Isolate affected systems
   - Preserve evidence (don't delete logs)
   - Notify security team immediately

2. **Containment**
   ```bash
   # Block suspicious IPs
   aws wafv2 create-ip-set ...

   # Rotate all credentials
   ./scripts/rotate-secrets.sh production all

   # Force all users to re-authenticate
   # Invalidate all JWT tokens
   ```

3. **Investigation**
   - Review CloudTrail logs
   - Review application logs
   - Review database audit logs

4. **Recovery**
   - Patch vulnerability
   - Deploy fix
   - Monitor for continued attacks

---

## Contact Information

### On-Call Rotation

| Week | Primary | Secondary |
|------|---------|-----------|
| Current | John Doe (+1-555-0100) | Jane Smith (+1-555-0101) |

### Escalation Path

1. **On-Call Engineer** → 15 minutes
2. **Engineering Manager** → 30 minutes
3. **VP Engineering** → 1 hour
4. **CTO** → 2 hours

### External Contacts

- AWS Support: Use AWS Console (Enterprise Support)
- Database Consultant: consulting@dbexperts.com
- Security Team: security@safety-research.example.com

---

**Last Updated**: 2025-11-01
**Version**: 1.0
**Owner**: DevOps Team
