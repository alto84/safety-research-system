-- Database initialization script for Safety Research System
-- This script is run automatically when the PostgreSQL container starts

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search

-- Create enum types
CREATE TYPE case_priority AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL');
CREATE TYPE case_status AS ENUM ('SUBMITTED', 'PROCESSING', 'COMPLETED', 'FAILED', 'CANCELLED');
CREATE TYPE task_status AS ENUM ('PENDING', 'IN_PROGRESS', 'COMPLETED', 'FAILED', 'RETRYING');
CREATE TYPE audit_status AS ENUM ('PASSED', 'FAILED', 'CRITICAL');

-- Cases table
CREATE TABLE IF NOT EXISTS cases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id VARCHAR(255) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    question TEXT NOT NULL,
    priority case_priority NOT NULL DEFAULT 'MEDIUM',
    status case_status NOT NULL DEFAULT 'SUBMITTED',
    context JSONB DEFAULT '{}',
    data_sources TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_by VARCHAR(255),
    INDEX idx_case_id (case_id),
    INDEX idx_status (status),
    INDEX idx_priority (priority),
    INDEX idx_created_at (created_at)
);

-- Tasks table
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id VARCHAR(255) UNIQUE NOT NULL,
    case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
    task_type VARCHAR(100) NOT NULL,
    description TEXT,
    input_data JSONB DEFAULT '{}',
    output_data JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    status task_status NOT NULL DEFAULT 'PENDING',
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    INDEX idx_task_id (task_id),
    INDEX idx_case_id (case_id),
    INDEX idx_status (status),
    INDEX idx_task_type (task_type)
);

-- Audit results table
CREATE TABLE IF NOT EXISTS audit_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    audit_id VARCHAR(255) UNIQUE NOT NULL,
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    status audit_status NOT NULL,
    issues JSONB DEFAULT '[]',
    passed_checks JSONB DEFAULT '[]',
    failed_checks JSONB DEFAULT '[]',
    recommendations JSONB DEFAULT '[]',
    summary TEXT,
    confidence_score FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    auditor_type VARCHAR(100),
    INDEX idx_audit_id (audit_id),
    INDEX idx_task_id (task_id),
    INDEX idx_status (status)
);

-- Evidence table
CREATE TABLE IF NOT EXISTS evidence (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    evidence_id VARCHAR(255) UNIQUE NOT NULL,
    case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    source VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    quality_score FLOAT,
    relevance_score FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_evidence_id (evidence_id),
    INDEX idx_case_id (case_id),
    INDEX idx_task_id (task_id),
    INDEX idx_source (source)
);

-- Reports table
CREATE TABLE IF NOT EXISTS reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id VARCHAR(255) UNIQUE NOT NULL,
    case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    summary TEXT,
    findings JSONB DEFAULT '[]',
    recommendations JSONB DEFAULT '[]',
    confidence_level VARCHAR(50),
    limitations TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_report_id (report_id),
    INDEX idx_case_id (case_id)
);

-- Metrics table for monitoring
CREATE TABLE IF NOT EXISTS metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name VARCHAR(255) NOT NULL,
    metric_value FLOAT NOT NULL,
    labels JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_metric_name (metric_name),
    INDEX idx_timestamp (timestamp)
);

-- API logs table
CREATE TABLE IF NOT EXISTS api_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    endpoint VARCHAR(500) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER,
    response_time_ms INTEGER,
    user_agent TEXT,
    ip_address INET,
    request_body JSONB,
    response_body JSONB,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_endpoint (endpoint),
    INDEX idx_status_code (status_code),
    INDEX idx_created_at (created_at)
);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for cases table
CREATE TRIGGER update_cases_updated_at
    BEFORE UPDATE ON cases
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create views for common queries
CREATE OR REPLACE VIEW case_summary AS
SELECT
    c.id,
    c.case_id,
    c.title,
    c.priority,
    c.status,
    c.created_at,
    COUNT(DISTINCT t.id) as total_tasks,
    COUNT(DISTINCT CASE WHEN t.status = 'COMPLETED' THEN t.id END) as completed_tasks,
    COUNT(DISTINCT CASE WHEN t.status = 'FAILED' THEN t.id END) as failed_tasks,
    COUNT(DISTINCT ar.id) as total_audits,
    COUNT(DISTINCT CASE WHEN ar.status = 'PASSED' THEN ar.id END) as passed_audits
FROM cases c
LEFT JOIN tasks t ON c.id = t.case_id
LEFT JOIN audit_results ar ON t.id = ar.task_id
GROUP BY c.id, c.case_id, c.title, c.priority, c.status, c.created_at;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO safetyuser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO safetyuser;

-- Insert sample data for testing
INSERT INTO cases (case_id, title, question, priority, context) VALUES
    ('CASE-TEST-001', 'Test Case - Drug X Hepatotoxicity', 'Is there a causal relationship between Drug X and hepatotoxicity?', 'HIGH', '{"drug_name": "Drug X", "adverse_event": "Hepatotoxicity"}'::jsonb)
ON CONFLICT (case_id) DO NOTHING;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_cases_created_at_desc ON cases (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at_desc ON tasks (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_results_created_at_desc ON audit_results (created_at DESC);

-- Full text search index
CREATE INDEX IF NOT EXISTS idx_cases_question_trgm ON cases USING gin (question gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_cases_title_trgm ON cases USING gin (title gin_trgm_ops);

COMMENT ON TABLE cases IS 'Main cases table storing safety assessment cases';
COMMENT ON TABLE tasks IS 'Tasks associated with cases, executed by worker agents';
COMMENT ON TABLE audit_results IS 'Audit results from auditor agents validating task outputs';
COMMENT ON TABLE evidence IS 'Evidence collected during case processing';
COMMENT ON TABLE reports IS 'Final reports generated for cases';
