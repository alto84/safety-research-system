# Deployment Guide

This guide provides instructions for deploying the Safety Research System to production environments.

---

## Table of Contents

- [Deployment Options](#deployment-options)
- [Prerequisites](#prerequisites)
- [Environment Configuration](#environment-configuration)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Database Setup](#database-setup)
- [Monitoring and Logging](#monitoring-and-logging)
- [Security Configuration](#security-configuration)
- [Performance Tuning](#performance-tuning)
- [Backup and Recovery](#backup-and-recovery)

---

## Deployment Options

### Option 1: Docker Compose (Development/Small-Scale)

- Single server deployment
- Suitable for small teams (< 20 users)
- Easy setup and maintenance

### Option 2: Kubernetes (Production/Enterprise)

- Multi-server deployment
- Highly scalable (1000+ users)
- High availability
- Auto-scaling

### Option 3: Cloud Platforms

- AWS ECS/EKS
- Google Cloud Run/GKE
- Azure Container Instances/AKS

---

## Prerequisites

### Hardware Requirements

**Minimum** (Development):
- CPU: 4 cores
- RAM: 8 GB
- Storage: 50 GB SSD
- Network: 100 Mbps

**Recommended** (Production):
- CPU: 16 cores
- RAM: 64 GB
- Storage: 500 GB SSD
- Network: 1 Gbps
- Load Balancer: NGINX or cloud-native

### Software Requirements

- Docker 20.10+
- Docker Compose 2.0+ (for Docker deployment)
- Kubernetes 1.24+ (for K8s deployment)
- PostgreSQL 14+
- Redis 7.0+
- Python 3.8+

---

## Environment Configuration

### 1. Environment Variables

Create `.env.production`:

```bash
# Application
APP_ENV=production
DEBUG=false
SECRET_KEY=<generate-random-secret-key>

# Database
DATABASE_URL=postgresql://user:password@postgres:5432/safety_research
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Redis Cache
REDIS_URL=redis://redis:6379/0
CACHE_TTL=3600

# LLM Provider
ANTHROPIC_API_KEY=sk-ant-your-production-key
OPENAI_API_KEY=sk-your-production-key-optional

# External APIs
PUBMED_API_KEY=your-pubmed-key
CLINICALTRIALS_API_KEY=your-key

# Storage
STORAGE_BACKEND=s3
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_S3_BUCKET=safety-research-storage
AWS_REGION=us-east-1

# Security
API_KEY_ENCRYPTION_KEY=<generate-encryption-key>
ALLOWED_HOSTS=api.yourdomain.com,*.yourdomain.com
CORS_ORIGINS=https://dashboard.yourdomain.com

# Feature Flags
ENABLE_INTELLIGENT_ROUTING=true
ENABLE_INTELLIGENT_RESOLUTION=true
ENABLE_INTELLIGENT_COMPRESSION=true
ENABLE_INTELLIGENT_AUDIT=true

# Performance
MAX_CONCURRENT_TASKS=20
TASK_TIMEOUT=3600
REQUEST_TIMEOUT=300

# Monitoring
SENTRY_DSN=https://your-sentry-dsn
PROMETHEUS_PORT=9090
LOG_LEVEL=INFO

# Email (for notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-password
```

### 2. Generate Secrets

```bash
# Generate secret key
python -c "import secrets; print(secrets.token_hex(32))"

# Generate encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

---

## Docker Deployment

### 1. Create Dockerfile

```dockerfile
# /Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "300", "app:app"]
```

### 2. Create docker-compose.yml

```yaml
# /docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/safety_research
      - REDIS_URL=redis://redis:6379/0
    env_file:
      - .env.production
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    volumes:
      - ./logs:/app/logs
    networks:
      - safety-net

  postgres:
    image: postgres:14
    environment:
      - POSTGRES_DB=safety_research
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    networks:
      - safety-net

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    networks:
      - safety-net

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    restart: unless-stopped
    networks:
      - safety-net

volumes:
  postgres_data:

networks:
  safety-net:
```

### 3. Deploy

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

---

## Kubernetes Deployment

### 1. Create Deployment

```yaml
# /k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: safety-research-api
  labels:
    app: safety-research
spec:
  replicas: 3
  selector:
    matchLabels:
      app: safety-research
  template:
    metadata:
      labels:
        app: safety-research
    spec:
      containers:
      - name: api
        image: your-registry/safety-research:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: safety-research-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: safety-research-secrets
              key: redis-url
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### 2. Create Service

```yaml
# /k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: safety-research-service
spec:
  selector:
    app: safety-research
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

### 3. Deploy

```bash
# Apply secrets
kubectl create secret generic safety-research-secrets \
  --from-literal=database-url="postgresql://..." \
  --from-literal=redis-url="redis://..." \
  --from-env-file=.env.production

# Deploy application
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# Check status
kubectl get pods
kubectl get services

# View logs
kubectl logs -f deployment/safety-research-api
```

---

## Database Setup

### 1. Initialize Database

```bash
# Create database
createdb -U postgres safety_research

# Run migrations
python manage.py db upgrade

# Create initial admin user
python manage.py create-admin \
  --username admin \
  --email admin@yourdomain.com \
  --password <secure-password>
```

### 2. Database Migrations

```bash
# Create migration
python manage.py db revision --autogenerate -m "Add new table"

# Apply migrations
python manage.py db upgrade

# Rollback
python manage.py db downgrade
```

### 3. Backup

```bash
# Backup database
pg_dump -U postgres safety_research > backup_$(date +%Y%m%d).sql

# Restore database
psql -U postgres safety_research < backup_20251101.sql
```

---

## Monitoring and Logging

### 1. Prometheus Metrics

```python
# Add to app.py
from prometheus_client import Counter, Histogram, Gauge, make_wsgi_app
from werkzeug.middleware.dispatcher import DispatcherMiddleware

# Metrics
cases_total = Counter('cases_total', 'Total cases processed')
case_duration = Histogram('case_duration_seconds', 'Case processing duration')
active_tasks = Gauge('active_tasks', 'Number of active tasks')

# Add metrics endpoint
app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
    '/metrics': make_wsgi_app()
})
```

### 2. Grafana Dashboard

Import dashboard from `/monitoring/grafana-dashboard.json`:

- Cases per hour
- Task success rate
- Average processing time
- System resource usage

### 3. Logging Configuration

```python
# /config/logging.py
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'level': 'INFO'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/safety-research/app.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10,
            'formatter': 'json'
        }
    },
    'loggers': {
        '': {
            'handlers': ['console', 'file'],
            'level': 'INFO'
        }
    }
}
```

---

## Security Configuration

### 1. SSL/TLS

```nginx
# /nginx.conf
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://app:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 2. API Key Management

```python
# Rotate API keys regularly
python manage.py rotate-api-key --user user@example.com

# Revoke API key
python manage.py revoke-api-key --key sk-proj-abc123

# List active keys
python manage.py list-api-keys
```

### 3. Network Security

- Use VPC/private networks
- Restrict database access to app servers only
- Enable firewall rules
- Use secrets management (AWS Secrets Manager, HashiCorp Vault)

---

## Performance Tuning

### 1. Database Optimization

```sql
-- Add indexes
CREATE INDEX idx_cases_status ON cases(status);
CREATE INDEX idx_tasks_case_id ON tasks(case_id);
CREATE INDEX idx_audit_results_task_id ON audit_results(task_id);

-- Analyze tables
ANALYZE cases;
ANALYZE tasks;
```

### 2. Redis Caching

```python
# Cache configuration
CACHE_CONFIG = {
    'reasoning_cache_ttl': 86400,  # 24 hours
    'case_cache_ttl': 3600,  # 1 hour
    'max_cache_size': 1000  # Max entries
}
```

### 3. Worker Pool Configuration

```python
# Adjust based on server resources
WORKER_CONFIG = {
    'max_concurrent_tasks': 20,
    'task_timeout': 3600,
    'worker_threads': 4,
    'enable_parallel_execution': True
}
```

---

## Backup and Recovery

### 1. Automated Backups

```bash
# /scripts/backup.sh
#!/bin/bash

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=/backups

# Database backup
pg_dump -U postgres safety_research | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# File storage backup
tar -czf $BACKUP_DIR/files_$DATE.tar.gz /app/storage

# Upload to S3
aws s3 cp $BACKUP_DIR/db_$DATE.sql.gz s3://safety-research-backups/
aws s3 cp $BACKUP_DIR/files_$DATE.tar.gz s3://safety-research-backups/

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete
```

### 2. Restore Procedure

```bash
# Download from S3
aws s3 cp s3://safety-research-backups/db_20251101.sql.gz .

# Restore database
gunzip db_20251101.sql.gz
psql -U postgres safety_research < db_20251101.sql

# Restore files
tar -xzf files_20251101.tar.gz -C /
```

---

## Health Checks

### Application Health

```bash
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "components": {
    "database": "healthy",
    "redis": "healthy",
    "llm": "healthy"
  }
}
```

### Database Health

```bash
psql -U postgres -c "SELECT 1"
```

### Redis Health

```bash
redis-cli ping
```

---

## Troubleshooting

See `TROUBLESHOOTING.md` for common deployment issues and solutions.

---

## Post-Deployment Checklist

- [ ] SSL certificates configured
- [ ] Database backups automated
- [ ] Monitoring dashboards configured
- [ ] Log aggregation working
- [ ] API keys rotated
- [ ] Security scan completed
- [ ] Load testing performed
- [ ] Disaster recovery plan documented
- [ ] Team trained on operations

---

**Last Updated**: November 1, 2025
