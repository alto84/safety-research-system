# Secrets Management Guide

This document outlines best practices for managing secrets and sensitive configuration in the Safety Research System.

## Table of Contents

1. [Overview](#overview)
2. [Secret Types](#secret-types)
3. [Environment-Based Secrets](#environment-based-secrets)
4. [Secret Storage Options](#secret-storage-options)
5. [Best Practices](#best-practices)
6. [Rotation Procedures](#rotation-procedures)
7. [Emergency Response](#emergency-response)

## Overview

The Safety Research System uses multiple layers of security for managing secrets:

1. **Environment Variables**: For runtime configuration
2. **Secret Management Services**: For production secrets (AWS Secrets Manager, HashiCorp Vault, etc.)
3. **Encrypted Configuration**: For sensitive config files
4. **Key Management**: For encryption keys and certificates

## Secret Types

### Critical Secrets (Rotate Monthly)

- Database passwords
- Redis passwords
- JWT signing keys
- API keys for LLM providers (OpenAI, Anthropic)
- Service-to-service authentication tokens

### Sensitive Secrets (Rotate Quarterly)

- External API keys (PubMed, Clinical Trials)
- Monitoring service credentials
- Backup encryption keys

### Configuration Secrets (Review Annually)

- SSL/TLS certificates
- SSH keys
- Application configuration tokens

## Environment-Based Secrets

### Development

```bash
# Use .env file (NEVER commit to git)
cp .env.example .env

# Edit with development values
DATABASE_URL=postgresql://devuser:devpass@localhost:5432/safety_dev
REDIS_URL=redis://localhost:6379/0
```

### Staging

```bash
# Use environment variables or secret manager
export DATABASE_URL=$(aws secretsmanager get-secret-value --secret-id staging/db/url --query SecretString --output text)
export REDIS_URL=$(aws secretsmanager get-secret-value --secret-id staging/redis/url --query SecretString --output text)
```

### Production

**NEVER use plain environment variables or .env files in production!**

Use a proper secret management service:

- AWS Secrets Manager
- HashiCorp Vault
- Google Secret Manager
- Azure Key Vault

## Secret Storage Options

### Option 1: AWS Secrets Manager (Recommended for AWS)

```bash
# Store secret
aws secretsmanager create-secret \
    --name production/database/url \
    --secret-string "postgresql://user:pass@host:5432/db"

# Retrieve secret
aws secretsmanager get-secret-value \
    --secret-id production/database/url \
    --query SecretString \
    --output text
```

**Application Integration:**

```python
import boto3
import json

def get_secret(secret_name):
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

# Usage
db_config = get_secret('production/database/config')
DATABASE_URL = db_config['url']
```

### Option 2: HashiCorp Vault (Cloud-Agnostic)

```bash
# Store secret
vault kv put secret/production/database url="postgresql://..."

# Retrieve secret
vault kv get -field=url secret/production/database
```

**Application Integration:**

```python
import hvac

client = hvac.Client(url='https://vault.example.com', token=os.getenv('VAULT_TOKEN'))
secret = client.secrets.kv.v2.read_secret_version(path='production/database')
DATABASE_URL = secret['data']['data']['url']
```

### Option 3: Kubernetes Secrets (for K8s Deployments)

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: safety-research-secrets
type: Opaque
stringData:
  database-url: postgresql://user:pass@host:5432/db
  redis-url: redis://:pass@host:6379/0
  openai-api-key: sk-...
```

**Mount as environment variables:**

```yaml
env:
  - name: DATABASE_URL
    valueFrom:
      secretKeyRef:
        name: safety-research-secrets
        key: database-url
```

### Option 4: Docker Secrets (for Docker Swarm)

```bash
# Create secret
echo "postgresql://..." | docker secret create db_url -

# Use in service
docker service create \
  --name safety-research \
  --secret db_url \
  safety-research-system:latest
```

## Best Practices

### 1. Never Commit Secrets to Git

```bash
# Add to .gitignore
.env
.env.*
!.env.example
secrets/
*.key
*.pem
credentials.json
```

### 2. Use Secret Scanning

Enable pre-commit hooks:

```bash
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
```

### 3. Principle of Least Privilege

- Each service gets only the secrets it needs
- Use separate credentials for different environments
- Limit secret access by IAM roles/policies

### 4. Encrypt Secrets at Rest

```bash
# Use SOPS for file-based secrets
sops -e secrets.yaml > secrets.enc.yaml

# Decrypt for deployment
sops -d secrets.enc.yaml > secrets.yaml
```

### 5. Audit Secret Access

- Enable CloudTrail for AWS Secrets Manager
- Monitor secret access patterns
- Alert on unusual access

## Rotation Procedures

### Database Credentials

```bash
# 1. Create new credentials
aws rds modify-db-instance \
    --db-instance-identifier safety-research-prod \
    --master-user-password NewSecurePassword123!

# 2. Update secret in Secrets Manager
aws secretsmanager update-secret \
    --secret-id production/database/url \
    --secret-string "postgresql://user:NewSecurePassword123!@..."

# 3. Restart application (rolling restart)
kubectl rollout restart deployment/safety-research-app

# 4. Verify connectivity
curl https://api.safety-research.example.com/health

# 5. Revoke old credentials (if using dual-user setup)
```

### API Keys (LLM Providers)

```bash
# 1. Generate new API key from provider dashboard
# 2. Update secret
aws secretsmanager update-secret \
    --secret-id production/openai/api-key \
    --secret-string "sk-new-key..."

# 3. Rolling restart
kubectl rollout restart deployment/safety-research-app

# 4. Revoke old key from provider dashboard
```

### JWT Signing Keys

```bash
# 1. Generate new key
openssl rand -hex 32 > new_jwt_secret.txt

# 2. Implement key rotation (support both old and new for transition)
# 3. Update secret
# 4. After transition period, remove old key
```

## Emergency Response

### Secret Leak Detected

**Immediate Actions (< 1 hour):**

1. **Revoke compromised secrets immediately**
   ```bash
   # Disable API key
   # Rotate database passwords
   # Invalidate JWT tokens
   ```

2. **Assess impact**
   - Which secrets were exposed?
   - For how long?
   - Who had access?

3. **Rotate all related secrets**
   ```bash
   ./scripts/emergency-rotate.sh --all
   ```

4. **Review access logs**
   ```bash
   aws cloudtrail lookup-events \
       --lookup-attributes AttributeKey=ResourceName,AttributeValue=secret-name
   ```

**Short-term Actions (< 24 hours):**

1. Conduct security audit
2. Review and update access policies
3. Implement additional monitoring
4. Document incident

**Long-term Actions (< 1 week):**

1. Improve secret scanning in CI/CD
2. Enhanced monitoring and alerting
3. Security training for team
4. Update incident response procedures

### Automated Secret Rotation Script

```bash
#!/bin/bash
# scripts/rotate-secrets.sh

set -e

ENVIRONMENT=$1
SECRET_TYPE=$2

echo "Rotating $SECRET_TYPE secrets for $ENVIRONMENT environment"

case $SECRET_TYPE in
  database)
    # Rotate database credentials
    ./scripts/rotate-db-creds.sh $ENVIRONMENT
    ;;
  api-keys)
    # Rotate API keys
    ./scripts/rotate-api-keys.sh $ENVIRONMENT
    ;;
  jwt)
    # Rotate JWT keys
    ./scripts/rotate-jwt-keys.sh $ENVIRONMENT
    ;;
  all)
    # Rotate all secrets
    ./scripts/rotate-db-creds.sh $ENVIRONMENT
    ./scripts/rotate-api-keys.sh $ENVIRONMENT
    ./scripts/rotate-jwt-keys.sh $ENVIRONMENT
    ;;
  *)
    echo "Unknown secret type: $SECRET_TYPE"
    exit 1
    ;;
esac

echo "Secret rotation completed successfully"
```

## Secret Validation

### Pre-deployment Checks

```python
# config/validate_secrets.py

import os
import sys

REQUIRED_SECRETS = [
    'DATABASE_URL',
    'REDIS_URL',
    'SECRET_KEY',
    'OPENAI_API_KEY',
    'ANTHROPIC_API_KEY',
]

def validate_secrets():
    missing = []
    for secret in REQUIRED_SECRETS:
        value = os.getenv(secret)
        if not value or value.startswith('${'):
            missing.append(secret)

    if missing:
        print(f"ERROR: Missing required secrets: {', '.join(missing)}")
        sys.exit(1)

    print("✓ All required secrets are configured")

if __name__ == '__main__':
    validate_secrets()
```

## Compliance Considerations

### HIPAA/GDPR Requirements

1. **Encryption**: All secrets must be encrypted at rest and in transit
2. **Access Logging**: All secret access must be logged and auditable
3. **Retention**: Secrets must be retained according to compliance requirements
4. **Destruction**: Securely destroy secrets when no longer needed

### Audit Trail

```bash
# Query secret access logs
aws cloudtrail lookup-events \
    --lookup-attributes AttributeKey=EventName,AttributeValue=GetSecretValue \
    --start-time 2024-01-01 \
    --end-time 2024-12-31 \
    --output json > secret-access-audit.json
```

## References

- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [AWS Secrets Manager Best Practices](https://docs.aws.amazon.com/secretsmanager/latest/userguide/best-practices.html)
- [HashiCorp Vault Documentation](https://www.vaultproject.io/docs)
- [NIST Special Publication 800-57](https://csrc.nist.gov/publications/detail/sp/800-57-part-1/rev-5/final)
