-- PostgreSQL Schema for SwasthyaAI Regulator
-- DPDP Act 2023, NDHM, ICMR, CDSCO Compliant
-- Audit Trail & Token Vault Enabled
-- Run: psql -U postgres -d swasthyaai < 001_init_postgresql.sql

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ===== CORE TABLES =====

CREATE TABLE IF NOT EXISTS submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename TEXT NOT NULL,
    original_filename TEXT,
    submission_type VARCHAR(50),
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    submitted_by UUID,
    version INT DEFAULT 1,
    metadata JSONB,
    CONSTRAINT valid_status CHECK (status IN ('pending', 'processing', 'completed', 'error'))
);

CREATE TABLE IF NOT EXISTS anonymized_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    submission_id UUID NOT NULL REFERENCES submissions(id) ON DELETE CASCADE,
    original_text TEXT,
    pseudonymized_text TEXT,
    generalized_text TEXT,
    k_anonymity_k_value INT,
    k_anonymity_status VARCHAR(20),
    k_anonymity_message TEXT,
    quasi_identifiers JSONB,
    compliance_score FLOAT,
    compliance_breakdown JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_by UUID
);

CREATE TABLE IF NOT EXISTS sae_cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    submission_id UUID NOT NULL REFERENCES submissions(id) ON DELETE CASCADE,
    case_id VARCHAR(100),
    event_term VARCHAR(500),
    meddra_code VARCHAR(20),
    severity_grade INT,
    severity_description VARCHAR(100),
    naranjo_score INT,
    naranjo_probability VARCHAR(50),
    naranjo_breakdown JSONB,
    outcome VARCHAR(50),
    priority_score INT,
    priority_level VARCHAR(50),
    priority_reasoning TEXT,
    is_duplicate BOOLEAN DEFAULT FALSE,
    duplicate_of UUID REFERENCES sae_cases(id),
    duplicate_confidence FLOAT,
    raw_narrative TEXT,
    extracted_fields JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP,
    reviewed_by UUID
);

CREATE TABLE IF NOT EXISTS compliance_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    submission_id UUID NOT NULL REFERENCES submissions(id) ON DELETE CASCADE,
    dpdp_score FLOAT,
    ndhm_score FLOAT,
    icmr_score FLOAT,
    cdsco_score FLOAT,
    overall_compliance_score FLOAT,
    risk_level VARCHAR(50),
    detailed_assessment JSONB,
    missing_items JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assessed_by UUID
);

-- ===== ENCRYPTION & TOKEN VAULT =====

CREATE TABLE IF NOT EXISTS token_vault (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    submission_id UUID NOT NULL REFERENCES submissions(id) ON DELETE CASCADE,
    token VARCHAR(100),
    encrypted_value TEXT,
    category VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    purged_at TIMESTAMP NULL,
    purge_reason VARCHAR(255),
    purged_by UUID
);

CREATE TABLE IF NOT EXISTS encryption_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    submission_id UUID NOT NULL REFERENCES submissions(id) ON DELETE CASCADE,
    key_data BYTEA,
    algorithm VARCHAR(50) DEFAULT 'Fernet',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    rotated_at TIMESTAMP NULL,
    is_active BOOLEAN DEFAULT TRUE
);

-- ===== AUDIT TRAIL (MANDATORY FOR DPDP ACT 2023) =====

CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    action VARCHAR(100),
    entity_type VARCHAR(50),
    entity_id UUID,
    submission_id UUID REFERENCES submissions(id) ON DELETE CASCADE,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    details JSONB,
    status VARCHAR(20),
    error_message TEXT NULL
);

CREATE TABLE IF NOT EXISTS data_access_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    submission_id UUID NOT NULL REFERENCES submissions(id) ON DELETE CASCADE,
    requester_id UUID,
    request_type VARCHAR(50),
    reason VARCHAR(255),
    status VARCHAR(50),
    approved_by UUID,
    approved_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    completion_details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===== INDEXES FOR PERFORMANCE =====

CREATE INDEX IF NOT EXISTS idx_submissions_status ON submissions(status);
CREATE INDEX IF NOT EXISTS idx_submissions_created_at ON submissions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_submissions_submitted_by ON submissions(submitted_by);

CREATE INDEX IF NOT EXISTS idx_anonymized_submission ON anonymized_data(submission_id);
CREATE INDEX IF NOT EXISTS idx_anonymized_compliance ON anonymized_data(compliance_score);

CREATE INDEX IF NOT EXISTS idx_sae_submission ON sae_cases(submission_id);
CREATE INDEX IF NOT EXISTS idx_sae_naranjo ON sae_cases(naranjo_score);
CREATE INDEX IF NOT EXISTS idx_sae_priority ON sae_cases(priority_score DESC);
CREATE INDEX IF NOT EXISTS idx_sae_is_duplicate ON sae_cases(is_duplicate);

CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_token_submission ON token_vault(submission_id);
CREATE INDEX IF NOT EXISTS idx_token_purged ON token_vault(purged_at) WHERE purged_at IS NOT NULL;

-- ===== VIEWS FOR REPORTING =====

CREATE OR REPLACE VIEW submission_status_dashboard AS
SELECT
    s.status,
    COUNT(*) as submission_count,
    AVG(CAST(anon.compliance_score AS FLOAT)) as avg_compliance_score,
    COUNT(CASE WHEN anon.k_anonymity_status = 'FAIL' THEN 1 END) as k_anonymity_failures
FROM submissions s
LEFT JOIN anonymized_data anon ON s.id = anon.submission_id
GROUP BY s.status;

CREATE OR REPLACE VIEW case_priority_ranking AS
SELECT
    sc.id,
    sc.case_id,
    sc.event_term,
    sc.severity_grade,
    sc.naranjo_score,
    sc.priority_score,
    sc.priority_level,
    s.submission_type,
    s.created_at
FROM sae_cases sc
JOIN submissions s ON sc.submission_id = s.id
ORDER BY sc.priority_score DESC;

CREATE OR REPLACE VIEW compliance_scorecard AS
SELECT
    s.id,
    s.filename,
    cr.dpdp_score,
    cr.ndhm_score,
    cr.icmr_score,
    cr.cdsco_score,
    cr.overall_compliance_score,
    cr.risk_level
FROM submissions s
LEFT JOIN compliance_results cr ON s.id = cr.submission_id;

-- ===== TRIGGERS FOR AUDIT TRAIL =====

CREATE OR REPLACE FUNCTION audit_changes()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_log (
        action,
        entity_type,
        entity_id,
        details,
        status
    ) VALUES (
        TG_OP,
        TG_TABLE_NAME,
        COALESCE(NEW.id, OLD.id),
        jsonb_build_object(
            'old_data', to_jsonb(OLD),
            'new_data', to_jsonb(NEW),
            'changed_at', CURRENT_TIMESTAMP
        ),
        'SUCCESS'
    );
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Create triggers for important tables
DROP TRIGGER IF EXISTS audit_submissions ON submissions;
CREATE TRIGGER audit_submissions
AFTER INSERT OR UPDATE OR DELETE ON submissions
FOR EACH ROW EXECUTE FUNCTION audit_changes();

DROP TRIGGER IF EXISTS audit_anonymized_data ON anonymized_data;
CREATE TRIGGER audit_anonymized_data
AFTER INSERT OR UPDATE ON anonymized_data
FOR EACH ROW EXECUTE FUNCTION audit_changes();

DROP TRIGGER IF EXISTS audit_token_vault ON token_vault;
CREATE TRIGGER audit_token_vault
AFTER INSERT OR DELETE ON token_vault
FOR EACH ROW EXECUTE FUNCTION audit_changes();

DROP TRIGGER IF EXISTS audit_sae_cases ON sae_cases;
CREATE TRIGGER audit_sae_cases
AFTER INSERT OR UPDATE ON sae_cases
FOR EACH ROW EXECUTE FUNCTION audit_changes();

-- ===== INITIALIZATION DATA =====

-- Verify setup
SELECT 'PostgreSQL Schema Initialized Successfully' as status;
