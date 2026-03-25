from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()


class Submission(db.Model):
    """Model for document submissions"""
    __tablename__ = "submissions"
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    submission_type = db.Column(db.String(50), default="form_44")  # form_44, form_md26, etc.
    status = db.Column(db.String(20), default="pending")  # pending, processing, completed, failed
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)
    
    # Processing metadata
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    processing_start_date = db.Column(db.DateTime)
    processing_end_date = db.Column(db.DateTime)
    processing_duration = db.Column(db.Float)  # seconds
    
    # Content extracted
    extracted_text = db.Column(db.Text)
    extracted_tables = db.Column(db.JSON)
    detected_metadata = db.Column(db.JSON)
    
    # Relationships
    anonymized_data = db.relationship("AnonymizedData", backref="submission", uselist=False, cascade="all, delete-orphan")
    summary = db.relationship("Summary", backref="submission", uselist=False, cascade="all, delete-orphan")
    compliance_result = db.relationship("ComplianceResult", backref="submission", uselist=False, cascade="all, delete-orphan")
    audit_logs = db.relationship("AuditLog", backref="submission", cascade="all, delete-orphan")
    
    # Error tracking
    error_message = db.Column(db.Text)
    error_code = db.Column(db.String(20))
    
    # Data retention
    scheduled_deletion = db.Column(db.DateTime)  # When this record will be deleted
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AnonymizedData(db.Model):
    """Model for anonymized submission data"""
    __tablename__ = "anonymized_data"
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    submission_id = db.Column(db.String(36), db.ForeignKey("submissions.id"), nullable=False)
    
    original_text = db.Column(db.Text)
    anonymized_text = db.Column(db.Text, nullable=False)
    
    # Token vault for de-anonymization (encrypted in database)
    token_vault = db.Column(db.JSON)  # Maps tokens to original PII (encrypted)
    
    # PII Statistics
    pii_found = db.Column(db.JSON)  # Count of PII types found and removed
    k_anonymity_score = db.Column(db.Float)
    l_diversity_score = db.Column(db.Float)
    t_closeness_score = db.Column(db.Float)
    
    anonymization_method = db.Column(db.String(50))  # pseudonymization, generalization, suppression
    anonymization_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Summary(db.Model):
    """Model for document summaries"""
    __tablename__ = "summaries"
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    submission_id = db.Column(db.String(36), db.ForeignKey("submissions.id"), nullable=False)
    
    abstract_summary = db.Column(db.Text, nullable=False)
    key_findings = db.Column(db.JSON)  # List of key findings
    critical_data_points = db.Column(db.JSON)  # Important data points
    
    # Summarization metrics
    original_length = db.Column(db.Integer)  # Character count
    summary_length = db.Column(db.Integer)  # Character count
    compression_ratio = db.Column(db.Float)  # summary_length / original_length
    
    model_used = db.Column(db.String(100))  # Model name (e.g., facebook/bart-large-cnn)
    generation_time = db.Column(db.Float)  # seconds
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ComplianceResult(db.Model):
    """Model for compliance validation results"""
    __tablename__ = "compliance_results"
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    submission_id = db.Column(db.String(36), db.ForeignKey("submissions.id"), nullable=False)
    
    # Overall compliance status
    is_compliant = db.Column(db.Boolean, default=False)
    compliance_score = db.Column(db.Float)  # 0-100
    
    # Individual checks (JSON format for flexibility)
    checks_results = db.Column(db.JSON)  # {check_name: {passed: bool, details: str}}
    
    # Specific compliance frameworks
    dpdp_act_2023_compliant = db.Column(db.Boolean)
    ndhm_policy_compliant = db.Column(db.Boolean)
    icmr_guidelines_compliant = db.Column(db.Boolean)
    cdsco_standards_compliant = db.Column(db.Boolean)
    
    # Issues found
    issues = db.Column(db.JSON)  # List of compliance issues
    recommendations = db.Column(db.JSON)  # List of recommendations
    
    validation_date = db.Column(db.DateTime, default=datetime.utcnow)
    validated_by = db.Column(db.String(100))  # User/system that validated
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class AuditLog(db.Model):
    """Model for audit logging"""
    __tablename__ = "audit_logs"
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    submission_id = db.Column(db.String(36), db.ForeignKey("submissions.id"), nullable=False)
    
    action = db.Column(db.String(100), nullable=False)  # e.g., "upload", "anonymize", "summarize"
    action_type = db.Column(db.String(20))  # CREATE, READ, UPDATE, DELETE
    
    user_id = db.Column(db.String(36))
    ip_address = db.Column(db.String(45))  # IPv4 or IPv6
    
    details = db.Column(db.JSON)  # Extra details about the action
    status = db.Column(db.String(20))  # success, failure
    error_message = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class User(db.Model):
    """Model for users (future auth)"""
    __tablename__ = "users"
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    
    role = db.Column(db.String(20), default="viewer")  # admin, reviewer, viewer
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def init_db(app):
    """Initialize database with app context"""
    with app.app_context():
        db.create_all()
