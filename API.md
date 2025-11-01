# REST API Documentation

## Overview

The Safety Research System exposes a REST API for submitting safety cases, monitoring progress, and retrieving results. This API enables integration with external systems such as safety databases, case management systems, and dashboards.

**Base URL**: `http://localhost:8000/api/v1`

**Authentication**: API Key (Bearer token)

**Content-Type**: `application/json`

---

## Table of Contents

- [Authentication](#authentication)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Endpoints](#endpoints)
  - [Cases](#cases)
  - [Tasks](#tasks)
  - [Agents](#agents)
  - [System](#system)
- [Webhooks](#webhooks)
- [Code Examples](#code-examples)

---

## Authentication

All API requests require authentication using an API key passed in the `Authorization` header.

### Obtaining an API Key

```bash
# Contact system administrator to provision API key
# Or use the CLI to generate one:
python -m safety_research_system generate-api-key --user "your-username"
```

### Using the API Key

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     http://localhost:8000/api/v1/cases
```

### Example Headers

```json
{
  "Authorization": "Bearer sk-proj-abc123xyz789...",
  "Content-Type": "application/json",
  "Accept": "application/json"
}
```

---

## Error Handling

### Error Response Format

All errors return a consistent JSON structure:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid case priority: 'CRITICAL'. Must be one of: LOW, MEDIUM, HIGH, URGENT",
    "details": {
      "field": "priority",
      "allowed_values": ["LOW", "MEDIUM", "HIGH", "URGENT"]
    },
    "request_id": "req_abc123xyz"
  }
}
```

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Missing or invalid API key |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource conflict (e.g., duplicate case) |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | System overloaded or maintenance |

### Error Codes

| Code | Description |
|------|-------------|
| `VALIDATION_ERROR` | Request validation failed |
| `AUTHENTICATION_ERROR` | Invalid or missing API key |
| `AUTHORIZATION_ERROR` | Insufficient permissions |
| `NOT_FOUND` | Resource not found |
| `RATE_LIMIT_EXCEEDED` | Too many requests |
| `SYSTEM_ERROR` | Internal system error |
| `AGENT_ERROR` | Agent execution error |
| `AUDIT_FAILED` | Audit validation failed |

---

## Rate Limiting

API requests are rate-limited to prevent abuse:

- **Default**: 100 requests per minute per API key
- **Burst**: 200 requests per minute for short bursts

### Rate Limit Headers

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1234567890
```

### Rate Limit Exceeded Response

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Please retry after 60 seconds.",
    "retry_after": 60
  }
}
```

---

## Endpoints

### Cases

#### Create Case

Submit a new safety research case to the system.

**Endpoint**: `POST /cases`

**Request Body**:

```json
{
  "title": "T-DXd Pneumonitis Risk Assessment",
  "description": "Evaluate pneumonitis risk factors for trastuzumab deruxtecan in HER2+ breast cancer patients",
  "question": "What are the primary risk factors for developing pneumonitis in patients treated with T-DXd?",
  "priority": "HIGH",
  "context": {
    "drug_name": "trastuzumab deruxtecan",
    "adverse_event": "pneumonitis",
    "indication": "HER2+ breast cancer",
    "population": "adult patients"
  },
  "data_sources": ["pubmed", "clinical_trials_db", "faers"],
  "submitter": "safety_scientist_001",
  "metadata": {
    "regulatory_deadline": "2025-12-31",
    "clinical_significance": "high"
  }
}
```

**Response**: `201 Created`

```json
{
  "case_id": "case_abc123xyz",
  "status": "submitted",
  "title": "T-DXd Pneumonitis Risk Assessment",
  "priority": "HIGH",
  "created_at": "2025-11-01T10:00:00Z",
  "estimated_completion": "2025-11-01T12:00:00Z",
  "tasks": [],
  "links": {
    "self": "/api/v1/cases/case_abc123xyz",
    "status": "/api/v1/cases/case_abc123xyz/status",
    "tasks": "/api/v1/cases/case_abc123xyz/tasks"
  }
}
```

**Example cURL**:

```bash
curl -X POST http://localhost:8000/api/v1/cases \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "T-DXd Pneumonitis Risk Assessment",
    "question": "What are the primary risk factors for T-DXd pneumonitis?",
    "priority": "HIGH",
    "context": {
      "drug_name": "trastuzumab deruxtecan",
      "adverse_event": "pneumonitis"
    },
    "data_sources": ["pubmed"]
  }'
```

---

#### Get Case

Retrieve details of a specific case.

**Endpoint**: `GET /cases/{case_id}`

**Response**: `200 OK`

```json
{
  "case_id": "case_abc123xyz",
  "title": "T-DXd Pneumonitis Risk Assessment",
  "description": "Evaluate pneumonitis risk factors...",
  "status": "in_progress",
  "priority": "HIGH",
  "question": "What are the primary risk factors...",
  "submitter": "safety_scientist_001",
  "assigned_sme": "senior_safety_expert_01",
  "context": {
    "drug_name": "trastuzumab deruxtecan",
    "adverse_event": "pneumonitis"
  },
  "data_sources": ["pubmed", "clinical_trials_db"],
  "tasks": [
    {
      "task_id": "task_lit_001",
      "task_type": "literature_review",
      "status": "completed",
      "assigned_agent": "LiteratureAgent"
    },
    {
      "task_id": "task_stats_001",
      "task_type": "statistical_analysis",
      "status": "in_progress",
      "assigned_agent": "StatisticsAgent"
    }
  ],
  "progress": {
    "total_tasks": 2,
    "completed_tasks": 1,
    "failed_tasks": 0,
    "in_progress_tasks": 1
  },
  "created_at": "2025-11-01T10:00:00Z",
  "updated_at": "2025-11-01T10:30:00Z",
  "estimated_completion": "2025-11-01T12:00:00Z"
}
```

**Example cURL**:

```bash
curl http://localhost:8000/api/v1/cases/case_abc123xyz \
  -H "Authorization: Bearer YOUR_API_KEY"
```

---

#### List Cases

Retrieve a paginated list of cases.

**Endpoint**: `GET /cases`

**Query Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `status` | string | all | Filter by status: `submitted`, `in_progress`, `completed`, `requires_human_review` |
| `priority` | string | all | Filter by priority: `LOW`, `MEDIUM`, `HIGH`, `URGENT` |
| `submitter` | string | - | Filter by submitter ID |
| `from_date` | ISO 8601 | - | Cases created after this date |
| `to_date` | ISO 8601 | - | Cases created before this date |
| `page` | integer | 1 | Page number (1-indexed) |
| `per_page` | integer | 20 | Results per page (max 100) |
| `sort` | string | `created_at` | Sort field: `created_at`, `updated_at`, `priority` |
| `order` | string | `desc` | Sort order: `asc`, `desc` |

**Response**: `200 OK`

```json
{
  "cases": [
    {
      "case_id": "case_abc123xyz",
      "title": "T-DXd Pneumonitis Risk Assessment",
      "status": "in_progress",
      "priority": "HIGH",
      "created_at": "2025-11-01T10:00:00Z",
      "progress": {
        "completed_tasks": 1,
        "total_tasks": 2
      }
    },
    {
      "case_id": "case_def456uvw",
      "title": "Checkpoint Inhibitor Hepatotoxicity",
      "status": "completed",
      "priority": "MEDIUM",
      "created_at": "2025-10-30T14:00:00Z",
      "progress": {
        "completed_tasks": 3,
        "total_tasks": 3
      }
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total_pages": 5,
    "total_items": 87,
    "has_next": true,
    "has_prev": false
  },
  "links": {
    "self": "/api/v1/cases?page=1",
    "next": "/api/v1/cases?page=2",
    "last": "/api/v1/cases?page=5"
  }
}
```

**Example cURL**:

```bash
curl "http://localhost:8000/api/v1/cases?status=in_progress&priority=HIGH&page=1" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

---

#### Get Case Status

Get real-time status of a case (lightweight endpoint).

**Endpoint**: `GET /cases/{case_id}/status`

**Response**: `200 OK`

```json
{
  "case_id": "case_abc123xyz",
  "status": "in_progress",
  "progress": {
    "total_tasks": 2,
    "completed_tasks": 1,
    "failed_tasks": 0,
    "in_progress_tasks": 1,
    "percentage": 50
  },
  "current_task": {
    "task_id": "task_stats_001",
    "task_type": "statistical_analysis",
    "status": "in_progress",
    "started_at": "2025-11-01T10:15:00Z"
  },
  "estimated_completion": "2025-11-01T12:00:00Z",
  "updated_at": "2025-11-01T10:30:00Z"
}
```

---

#### Get Case Report

Retrieve the final report for a completed case.

**Endpoint**: `GET /cases/{case_id}/report`

**Response**: `200 OK`

```json
{
  "case_id": "case_abc123xyz",
  "title": "T-DXd Pneumonitis Risk Assessment",
  "report": {
    "executive_summary": "Analysis of 45 studies identified 5 primary risk factors...",
    "findings_by_task": {
      "literature_review": {
        "summary": "Systematic review identified...",
        "key_findings": {
          "conclusion": "Grade 3+ ILD occurs in 10-15% of patients",
          "confidence": "Moderate - based on 45 studies",
          "source_count": 45
        }
      },
      "statistical_analysis": {
        "summary": "Meta-analysis shows...",
        "key_findings": {
          "conclusion": "Pooled incidence rate: 12.3% (95% CI: 10.1-14.8%)",
          "confidence": "Moderate",
          "heterogeneity": "I²=45%"
        }
      }
    },
    "overall_assessment": "T-DXd pneumonitis risk is 10-15% based on clinical trial data...",
    "recommendations": [
      "Baseline pulmonary function testing for high-risk patients",
      "Monthly clinical monitoring for early symptom detection",
      "Immediate treatment interruption upon symptom onset"
    ],
    "confidence_level": "Moderate - additional real-world evidence would strengthen findings",
    "limitations": [
      "Most studies excluded patients with baseline ILD",
      "Follow-up duration varied across trials (3-24 months)",
      "Limited data on biomarker-guided prevention"
    ]
  },
  "metadata": {
    "completion_date": "2025-11-01T12:00:00Z",
    "tasks_completed": 2,
    "compression_ratio": 87.5,
    "total_execution_time_seconds": 7200
  }
}
```

---

#### Update Case

Update case metadata or priority.

**Endpoint**: `PATCH /cases/{case_id}`

**Request Body**:

```json
{
  "priority": "URGENT",
  "assigned_sme": "expert_safety_lead_05",
  "metadata": {
    "regulatory_deadline": "2025-11-15"
  }
}
```

**Response**: `200 OK`

```json
{
  "case_id": "case_abc123xyz",
  "status": "in_progress",
  "priority": "URGENT",
  "assigned_sme": "expert_safety_lead_05",
  "updated_at": "2025-11-01T10:45:00Z"
}
```

---

#### Cancel Case

Cancel a case that is in progress.

**Endpoint**: `DELETE /cases/{case_id}`

**Response**: `200 OK`

```json
{
  "case_id": "case_abc123xyz",
  "status": "cancelled",
  "message": "Case cancelled successfully",
  "cancelled_at": "2025-11-01T11:00:00Z"
}
```

---

### Tasks

#### List Tasks for Case

Get all tasks associated with a case.

**Endpoint**: `GET /cases/{case_id}/tasks`

**Response**: `200 OK`

```json
{
  "case_id": "case_abc123xyz",
  "tasks": [
    {
      "task_id": "task_lit_001",
      "task_type": "literature_review",
      "status": "completed",
      "assigned_agent": "LiteratureAgent",
      "created_at": "2025-11-01T10:00:00Z",
      "completed_at": "2025-11-01T10:15:00Z",
      "execution_time_seconds": 900,
      "retry_count": 0,
      "audit_result": {
        "status": "passed",
        "issues_count": 0
      }
    },
    {
      "task_id": "task_stats_001",
      "task_type": "statistical_analysis",
      "status": "in_progress",
      "assigned_agent": "StatisticsAgent",
      "created_at": "2025-11-01T10:15:00Z",
      "retry_count": 0
    }
  ]
}
```

---

#### Get Task Details

Retrieve detailed information about a specific task.

**Endpoint**: `GET /tasks/{task_id}`

**Response**: `200 OK`

```json
{
  "task_id": "task_lit_001",
  "task_type": "literature_review",
  "status": "completed",
  "case_id": "case_abc123xyz",
  "assigned_agent": "LiteratureAgent",
  "input_data": {
    "query": "What are risk factors for T-DXd pneumonitis?",
    "data_sources": ["pubmed"]
  },
  "output_summary": {
    "summary": "Systematic review identified 45 studies...",
    "key_findings": {
      "conclusion": "Grade 3+ ILD occurs in 10-15% of patients",
      "confidence": "Moderate",
      "source_count": 45
    }
  },
  "audit_history": [
    {
      "audit_id": "audit_001",
      "auditor": "LiteratureAuditor",
      "status": "passed",
      "timestamp": "2025-11-01T10:15:00Z",
      "issues_count": 0
    }
  ],
  "created_at": "2025-11-01T10:00:00Z",
  "completed_at": "2025-11-01T10:15:00Z",
  "execution_time_seconds": 900,
  "retry_count": 0
}
```

---

#### Retry Failed Task

Retry a failed task (requires human approval).

**Endpoint**: `POST /tasks/{task_id}/retry`

**Request Body**:

```json
{
  "reason": "Updated data source credentials",
  "approved_by": "safety_lead_001"
}
```

**Response**: `200 OK`

```json
{
  "task_id": "task_stats_001",
  "status": "pending",
  "retry_count": 1,
  "message": "Task queued for retry"
}
```

---

### Agents

#### List Available Agents

Get list of registered worker and auditor agents.

**Endpoint**: `GET /agents`

**Response**: `200 OK`

```json
{
  "workers": [
    {
      "agent_id": "literature_agent_001",
      "agent_type": "LiteratureAgent",
      "version": "1.0.0",
      "task_types": ["literature_review"],
      "status": "active",
      "current_load": 2,
      "max_concurrent_tasks": 5
    },
    {
      "agent_id": "statistics_agent_001",
      "agent_type": "StatisticsAgent",
      "version": "1.0.0",
      "task_types": ["statistical_analysis"],
      "status": "active",
      "current_load": 1,
      "max_concurrent_tasks": 3
    }
  ],
  "auditors": [
    {
      "agent_id": "literature_auditor_001",
      "agent_type": "LiteratureAuditor",
      "version": "1.0.0",
      "task_types": ["literature_review"],
      "status": "active"
    },
    {
      "agent_id": "statistics_auditor_001",
      "agent_type": "StatisticsAuditor",
      "version": "1.0.0",
      "task_types": ["statistical_analysis"],
      "status": "active"
    }
  ]
}
```

---

#### Get Agent Metrics

Get performance metrics for an agent.

**Endpoint**: `GET /agents/{agent_id}/metrics`

**Response**: `200 OK`

```json
{
  "agent_id": "literature_agent_001",
  "agent_type": "LiteratureAgent",
  "metrics": {
    "tasks_completed": 127,
    "tasks_failed": 3,
    "success_rate": 97.7,
    "average_execution_time_seconds": 875,
    "audit_pass_rate": 94.5,
    "average_retry_count": 0.15
  },
  "period": {
    "from": "2025-10-01T00:00:00Z",
    "to": "2025-11-01T00:00:00Z"
  }
}
```

---

### System

#### Health Check

Check system health and component status.

**Endpoint**: `GET /health`

**Response**: `200 OK`

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "components": {
    "orchestrator": "healthy",
    "task_executor": "healthy",
    "audit_engine": "healthy",
    "resolution_engine": "healthy",
    "database": "healthy",
    "llm_integration": "healthy"
  },
  "uptime_seconds": 345600,
  "timestamp": "2025-11-01T10:00:00Z"
}
```

---

#### System Metrics

Get system-wide performance metrics.

**Endpoint**: `GET /system/metrics`

**Response**: `200 OK`

```json
{
  "cases": {
    "total": 127,
    "submitted": 5,
    "in_progress": 12,
    "completed": 105,
    "requires_human_review": 3,
    "cancelled": 2
  },
  "tasks": {
    "total": 381,
    "pending": 8,
    "in_progress": 15,
    "completed": 345,
    "failed": 13
  },
  "performance": {
    "average_case_duration_seconds": 7200,
    "average_task_duration_seconds": 900,
    "audit_pass_rate": 92.1,
    "compression_ratio_average": 85.3
  },
  "period": {
    "from": "2025-10-01T00:00:00Z",
    "to": "2025-11-01T00:00:00Z"
  }
}
```

---

## Webhooks

Configure webhooks to receive real-time notifications about case and task events.

### Register Webhook

**Endpoint**: `POST /webhooks`

**Request Body**:

```json
{
  "url": "https://your-system.com/webhooks/safety-research",
  "events": [
    "case.created",
    "case.completed",
    "case.requires_review",
    "task.completed",
    "task.failed"
  ],
  "secret": "whsec_your_webhook_secret"
}
```

**Response**: `201 Created`

```json
{
  "webhook_id": "wh_abc123xyz",
  "url": "https://your-system.com/webhooks/safety-research",
  "events": ["case.created", "case.completed", "case.requires_review"],
  "status": "active",
  "created_at": "2025-11-01T10:00:00Z"
}
```

### Webhook Event Format

```json
{
  "event": "case.completed",
  "timestamp": "2025-11-01T12:00:00Z",
  "data": {
    "case_id": "case_abc123xyz",
    "status": "completed",
    "title": "T-DXd Pneumonitis Risk Assessment"
  },
  "signature": "sha256=..."
}
```

### Webhook Events

| Event | Description |
|-------|-------------|
| `case.created` | New case submitted |
| `case.started` | Case processing started |
| `case.completed` | Case completed successfully |
| `case.requires_review` | Case requires human review |
| `case.failed` | Case processing failed |
| `task.started` | Task execution started |
| `task.completed` | Task completed successfully |
| `task.failed` | Task execution failed |
| `task.audit_failed` | Task failed audit validation |

---

## Code Examples

### Python (using requests)

```python
import requests
import json

API_KEY = "sk-proj-your-api-key"
BASE_URL = "http://localhost:8000/api/v1"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Create a case
case_data = {
    "title": "T-DXd Pneumonitis Risk Assessment",
    "question": "What are the primary risk factors for T-DXd pneumonitis?",
    "priority": "HIGH",
    "context": {
        "drug_name": "trastuzumab deruxtecan",
        "adverse_event": "pneumonitis"
    },
    "data_sources": ["pubmed"]
}

response = requests.post(
    f"{BASE_URL}/cases",
    headers=headers,
    json=case_data
)

case = response.json()
case_id = case["case_id"]
print(f"Created case: {case_id}")

# Poll for completion
import time

while True:
    response = requests.get(
        f"{BASE_URL}/cases/{case_id}/status",
        headers=headers
    )
    status_data = response.json()

    print(f"Status: {status_data['status']} ({status_data['progress']['percentage']}%)")

    if status_data["status"] in ["completed", "requires_human_review", "failed"]:
        break

    time.sleep(30)  # Poll every 30 seconds

# Get final report
if status_data["status"] == "completed":
    response = requests.get(
        f"{BASE_URL}/cases/{case_id}/report",
        headers=headers
    )
    report = response.json()
    print(json.dumps(report, indent=2))
```

### JavaScript (using fetch)

```javascript
const API_KEY = 'sk-proj-your-api-key';
const BASE_URL = 'http://localhost:8000/api/v1';

const headers = {
  'Authorization': `Bearer ${API_KEY}`,
  'Content-Type': 'application/json'
};

// Create a case
async function createCase() {
  const caseData = {
    title: 'T-DXd Pneumonitis Risk Assessment',
    question: 'What are the primary risk factors for T-DXd pneumonitis?',
    priority: 'HIGH',
    context: {
      drug_name: 'trastuzumab deruxtecan',
      adverse_event: 'pneumonitis'
    },
    data_sources: ['pubmed']
  };

  const response = await fetch(`${BASE_URL}/cases`, {
    method: 'POST',
    headers: headers,
    body: JSON.stringify(caseData)
  });

  const caseObj = await response.json();
  console.log('Created case:', caseObj.case_id);

  return caseObj.case_id;
}

// Poll for completion
async function waitForCompletion(caseId) {
  while (true) {
    const response = await fetch(
      `${BASE_URL}/cases/${caseId}/status`,
      { headers: headers }
    );

    const status = await response.json();
    console.log(`Status: ${status.status} (${status.progress.percentage}%)`);

    if (['completed', 'requires_human_review', 'failed'].includes(status.status)) {
      break;
    }

    await new Promise(resolve => setTimeout(resolve, 30000)); // Wait 30s
  }
}

// Get report
async function getReport(caseId) {
  const response = await fetch(
    `${BASE_URL}/cases/${caseId}/report`,
    { headers: headers }
  );

  const report = await response.json();
  console.log(JSON.stringify(report, null, 2));
}

// Run
(async () => {
  const caseId = await createCase();
  await waitForCompletion(caseId);
  await getReport(caseId);
})();
```

### cURL Examples

```bash
# Create case
curl -X POST http://localhost:8000/api/v1/cases \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "T-DXd Pneumonitis Risk Assessment",
    "question": "What are risk factors for T-DXd pneumonitis?",
    "priority": "HIGH",
    "context": {"drug_name": "trastuzumab deruxtecan"},
    "data_sources": ["pubmed"]
  }'

# Get case status
curl http://localhost:8000/api/v1/cases/case_abc123xyz/status \
  -H "Authorization: Bearer YOUR_API_KEY"

# Get case report
curl http://localhost:8000/api/v1/cases/case_abc123xyz/report \
  -H "Authorization: Bearer YOUR_API_KEY"

# List all cases
curl "http://localhost:8000/api/v1/cases?status=in_progress&page=1" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

---

## API Changelog

### Version 1.0.0 (Current)

- Initial release
- Case submission and retrieval
- Task monitoring
- Agent metrics
- Webhook support

### Planned Features

- GraphQL API endpoint
- Streaming SSE for real-time updates
- Batch case submission
- Advanced filtering and search
- API usage analytics

---

## Support

For API support, please contact:
- **Email**: api-support@safety-research-system.com
- **Documentation**: https://docs.safety-research-system.com
- **Status Page**: https://status.safety-research-system.com

---

**Last Updated**: November 1, 2025
**API Version**: 1.0.0
