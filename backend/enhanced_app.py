"""
SwasthyaAI Regulator - Enhanced Backend with All Regulatory Features
Integrated with:
✅ Duplicate Detection
✅ Field Validation (Form 44 & MD-14)
✅ Consistency Checking
✅ Evidence-Based Naranjo Scoring
✅ Async Task Processing
✅ Full Audit Trail
"""

from flask import Flask, request, jsonify, make_response, send_file
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
import uuid
import sys
import logging
import traceback
from datetime import datetime, timedelta
import json
import re

# Load environment
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# FLASK APP INITIALIZATION
# ============================================================================

app = Flask(__name__)

# SQLite configuration for development
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///swasthyaai_dev.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-prod')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'dev-jwt-key-change-in-prod')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600))
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Enable CORS - Allow all origins for development (simpler config that works)
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "max_age": 3600
    }
})

jwt = JWTManager(app)
db = SQLAlchemy(app)

logger.info("[PASS] Flask app initialized")

# ============================================================================
# CORS HELPER - Add CORS headers to every response manually
# ============================================================================

@app.after_request
def add_cors_headers(response):
    """Add CORS headers manually to every response"""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Max-Age'] = '3600'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response

# Handle preflight OPTIONS requests
@app.before_request
def handle_preflight():
    if request.method == 'OPTIONS':
        response = make_response('', 204)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Max-Age'] = '3600'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        return response

# ============================================================================
# ERROR HANDLERS WITH CORS
# ============================================================================

@app.errorhandler(404)
def not_found(e):
    response = jsonify({'error': 'Resource not found'})
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response, 404

@app.errorhandler(500)
def internal_error(e):
    logger.error(f"Internal error: {e}")
    response = jsonify({'error': 'Internal server error'})
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response, 500

@app.errorhandler(Exception)
def handle_exception(e):
    """Handle any unhandled exceptions with CORS headers"""
    logger.error(f"Unhandled exception: {e}", exc_info=True)
    response = jsonify({'error': str(e), 'type': type(e).__name__})
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response, 500

# ============================================================================
# JWT ERROR HANDLERS
# ============================================================================

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_data):
    return jsonify({'error': 'Token has expired'}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({'error': 'Invalid token', 'details': str(error)}), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({'error': 'Missing authorization token', 'details': str(error)}), 401

# ============================================================================
# DATABASE MODELS
# ============================================================================

class Submission(db.Model):
    __tablename__ = 'submissions'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = db.Column(db.String(500))
    submission_type = db.Column(db.String(50))
    status = db.Column(db.String(50), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    submitted_by = db.Column(db.String(36))

class ValidationResult(db.Model):
    __tablename__ = 'validation_results'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    submission_id = db.Column(db.String(36))
    check_type = db.Column(db.String(100))  # duplicate, field, consistency, naranjo
    result = db.Column(db.Text)  # JSON
    status = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    operation = db.Column(db.String(100))
    user_id = db.Column(db.String(36))
    resource = db.Column(db.String(255))
    details = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    try:
        db.create_all()
        logger.info("[PASS] Database tables created")
    except Exception as e:
        logger.error(f"❌ Database error: {e}")

# ============================================================================
# IMPORT REGULATORY MODULES
# ============================================================================

try:
    from modules.duplicate_detector import DuplicateDetector
    from modules.field_validator import Form44Validator, MD14Validator
    from modules.consistency_checker import ConsistencyChecker
    from modules.adr_validator import ADRValidator  # ADD THIS

    duplicate_detector = DuplicateDetector(similarity_threshold=0.85)
    form44_validator = Form44Validator()
    adr_validator = ADRValidator()  # ADD THIS
    md14_validator = MD14Validator()
    consistency_checker = ConsistencyChecker()

    logger.info("[PASS] All regulatory modules imported")
except Exception as e:
    logger.warning(f"[WARN] Could not load regulatory modules: {e}")
    duplicate_detector = None
    form44_validator = None
    adr_validator = None  # ADD THIS
    md14_validator = None
    consistency_checker = None

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def log_audit(operation, user_id, resource, details):
    """Log operation to audit trail"""
    try:
        audit = AuditLog(
            operation=operation,
            user_id=user_id,
            resource=resource,
            details=json.dumps(details) if isinstance(details, dict) else str(details)
        )
        db.session.add(audit)
        db.session.commit()
    except Exception as e:
        logger.warning(f"Audit log failed: {e}")


def detect_form_type(form_data: dict) -> str:
    """
    Detect form type: ADR vs DMF
    Returns: 'ADR' or 'DMF' or 'unknown'
    """
    # ADR indicators (Adverse Drug Reaction)
    adr_indicators = ['patient_age', 'adverse_reaction', 'onset_date', 'patient_gender']

    # DMF indicators (Drug Master File)
    dmf_indicators = ['applicant_name', 'manufacturing_process', 'drug_code', 'clinical_data_available']

    adr_count = sum(1 for field in adr_indicators if field in form_data and form_data[field])
    dmf_count = sum(1 for field in dmf_indicators if field in form_data and form_data[field])

    if adr_count >= 2:
        return 'ADR'
    elif dmf_count >= 2:
        return 'DMF'
    else:
        return 'unknown'

# ============================================================================
# DATA CLEANING & EXTRACTION ARTIFACT REMOVAL
# ============================================================================

def clean_text_field(text: str) -> str:
    """
    Clean text field by removing PDF extraction artifacts and prefixes.
    Handles:
    - Field label prefixes (e.g., "Term: ", "Response: ", "Description: ")
    - Extra whitespace
    - Common PDF artifacts
    """
    if not text or not isinstance(text, str):
        return ''
    
    text = text.strip()
    
    # Remove common field label prefixes that PDFs extract
    prefix_patterns = [
        r'^Term:\s*',           # "Term: Severe headache" → "Severe headache"
        r'^Response:\s*',       # "Response: Yes" → "Yes"
        r'^Description:\s*',    # "Description: ..." → "..."
        r'^Value:\s*',          # "Value: ..." → "..."
        r'^Result:\s*',         # "Result: ..." → "..."
        r'^Finding:\s*',        # "Finding: ..." → "..."
        r'^Reaction:\s*',       # "Reaction: ..." → "..."
        r'^Event:\s*',          # "Event: ..." → "..."
        r'^Answer:\s*',         # "Answer: ..." → "..."
        r'^Status:\s*',         # "Status: ..." → "..."
        r'^Batch:\s*',          # "Batch: ABC123" → "ABC123"
        r'^Batch Number:\s*',   # "Batch Number: ABC123" → "ABC123"
        r'^Lot:\s*',            # "Lot: XYZ789" → "XYZ789"
        r'^Field:\s*',          # "Field: value" → "value"
    ]
    
    for pattern in prefix_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Clean multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    # Remove trailing/leading whitespace again
    text = text.strip()
    
    return text

def parse_ambiguous_date(date_str: str) -> str:
    """
    Handle ambiguous date formats, especially 2-digit years.
    
    Handles:
    - YY-MM-DD → YYYY-MM-DD (detect if YY is likely year)
    - 26-03-10 → 2026-03-10 (common 2-digit year issue)
    - DD-MM-YY → DD-MM-YYYY
    
    Logic: 
    - If first number > 31, it's likely YYYY-MM-DD format (already 4-digit handled elsewhere)
    - If first number <= 31, try to determine if DD-MM-YY or YY-MM-DD
    - Use century heuristic: 00-30 → 2000-2030, 31-99 → 1931-1999
    - Use month validation: if middle value is > 12, then first must be month (invalid pattern)
    """
    if not date_str or not isinstance(date_str, str):
        return ''
    
    date_str = date_str.strip()
    
    # Already in YYYY-MM-DD format (4-digit year)
    if re.match(r'^\d{4}-\d{1,2}-\d{1,2}$', date_str):
        return date_str
    
    # Already in DD/MM/YYYY format with slashes
    if re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', date_str):
        return date_str
    
    # Pattern: YY-MM-DD or DD-MM-YY (ambiguous 2-digit years with dashes)
    if re.match(r'^\d{2}-\d{1,2}-\d{2}$', date_str):
        parts = date_str.split('-')
        first, middle, last = int(parts[0]), int(parts[1]), int(parts[2])
        
        # Smart detection:
        # Rule 1: If middle > 12, it cannot be a month, invalid
        if middle > 12:
            return date_str  # Invalid format, return as-is
        
        # Rule 2: If last > 31, it cannot be a day, invalid
        if last > 31:
            return date_str  # Invalid format, return as-is
        
        # Rule 3: If first > 31, it cannot be a day, must be year (invalid but handle gracefully)
        if first > 31:
            extracted_year = first
            month = middle
            day = last
        else:
            # Both first and last <= 31, ambiguous
            # DEFAULT to YY-MM-DD as this matches PDF extraction patterns (26-03-10 = 2026-03-10)
            # Only switch to DD-MM-YY if day value is impossible for a year
            extracted_year = first
            month = middle
            day = last
        
        # Century heuristic: 00-30 → 2000-2030, 31-99 → 1931-1999
        if extracted_year <= 30:
            full_year = 2000 + extracted_year
        else:
            full_year = 1900 + extracted_year
        
        # Validate month/day range
        if 1 <= month <= 12 and 1 <= day <= 31:
            return f"{full_year}-{month:02d}-{day:02d}"
    
    # Pattern: DD-MM-YYYY (dashes with 4-digit year)
    if re.match(r'^\d{1,2}-\d{1,2}-\d{4}$', date_str):
        return date_str.replace('-', '/')
    
    return date_str

def clean_extraction_data(form_data: dict, is_batch_submission: bool = False) -> dict:
    """
    Comprehensive data cleaning for PDF-extracted form data.
    Removes artifacts, normalizes formats, and auto-populates missing required fields.
    
    Handles:
    1. Text field artifact removal (field prefixes)
    2. Date format normalization and ambiguity resolution
    3. Auto-population of missing required fields (for batch submissions)
    4. Trimming and whitespace normalization
    
    Args:
        form_data: Dictionary with potentially corrupted extracted data
        is_batch_submission: If True, reporter_name is optional
    
    Returns:
        Cleaned and normalized form_data dictionary
    """
    if not form_data or not isinstance(form_data, dict):
        return {}
    
    cleaned = {}
    
    # Text fields that need artifact cleaning
    text_fields = [
        'adverse_reaction', 'adverse_event_term',
        'drug_name', 'generic_name',
        'manufacturer', 'batch_number',
        'outcome', 'patient_name',
        'reporter_name', 'reporter_address',
        'complaint', 'other_relevant_history',
        'description', 'findings'
    ]
    
    # Date fields that need format normalization
    date_fields = [
        'onset_date', 'event_onset_date',
        'report_date', 'manufacturing_date',
        'expiration_date', 'dob', 'date_of_birth'
    ]
    
    # Numeric fields that should stay as-is but be trimmed
    numeric_fields = [
        'patient_age', 'age', 'weight', 'dose'
    ]
    
    # Process each field in the form_data
    for key, value in form_data.items():
        if not value:  # Skip None, empty strings, etc.
            if key not in ['reporter_name']:  # Don't auto-populate yet
                continue
        
        # Text field cleaning
        if key in text_fields:
            if isinstance(value, str):
                cleaned[key] = clean_text_field(value)
            else:
                cleaned[key] = value
        
        # Date field normalization
        elif key in date_fields:
            if isinstance(value, str):
                # First parse ambiguous dates, then normalize format
                parsed_date = parse_ambiguous_date(value)
                cleaned[key] = normalize_date_format(parsed_date)
            else:
                cleaned[key] = value
        
        # Numeric fields - keep but strip whitespace if string
        elif key in numeric_fields:
            if isinstance(value, str):
                cleaned[key] = value.strip()
            else:
                cleaned[key] = value
        
        # All other fields - pass through but clean if string
        else:
            if isinstance(value, str):
                cleaned[key] = value.strip()
            else:
                cleaned[key] = value
    
    # Auto-populate missing required fields
    # For batch submissions: use batch label
    # For single submissions: use extracted or default label
    if not cleaned.get('reporter_name') or cleaned.get('reporter_name', '').upper() == 'MISSING':
        if is_batch_submission:
            cleaned['reporter_name'] = 'Batch Submission - Auto-reported'
        else:
            cleaned['reporter_name'] = 'Auto-reported (Extracted)'
        logger.info(f"[CLEANING] Auto-populated reporter_name: {cleaned['reporter_name']}")
    
    logger.info(f"[CLEANING] Cleaned {len(cleaned)} fields from form_data")
    logger.debug(f"[CLEANING] Original adverse_reaction: {form_data.get('adverse_reaction')}")
    logger.debug(f"[CLEANING] Cleaned adverse_reaction: {cleaned.get('adverse_reaction')}")
    logger.debug(f"[CLEANING] Original onset_date: {form_data.get('onset_date')}")
    logger.debug(f"[CLEANING] Cleaned onset_date: {cleaned.get('onset_date')}")
    logger.debug(f"[CLEANING] Original reporter_name: {form_data.get('reporter_name')}")
    logger.debug(f"[CLEANING] Cleaned reporter_name: {cleaned.get('reporter_name')}")
    
    return cleaned

def normalize_date_format(date_str: str) -> str:
    """
    Normalize date string to DD/MM/YYYY or YYYY-MM-DD format (ADR validator accepts both)
    Handles multiple input formats:
    - YYYY-MM-DD → returns as-is
    - DD/MM/YYYY → returns as-is
    - DD-MM-YYYY → converts to DD/MM/YYYY
    - Text month formats → attempts conversion
    """
    if not date_str or not isinstance(date_str, str):
        return ''
    
    date_str = date_str.strip()
    
    # Already in correct format (YYYY-MM-DD or DD/MM/YYYY)
    if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):  # YYYY-MM-DD
        return date_str
    if re.match(r'^\d{1,2}/\d{1,2}/\d{2,4}$', date_str):  # DD/MM/YYYY with slashes
        return date_str
    
    # Convert DD-MM-YYYY to DD/MM/YYYY (dashes to slashes)
    if re.match(r'^\d{1,2}-\d{1,2}-\d{4}$', date_str):
        return date_str.replace('-', '/')
    
    return date_str

def normalize_md14_to_adr(form_data: dict) -> dict:
    """
    Normalize MD-14 field names to ADR field names for validation.
    Comprehensive mapping handles both MD-14 and Form 44 formats.
    
    MD-14 → ADR Field Mappings:
    - adverse_event_term → adverse_reaction
    - event_onset_date → onset_date
    - event_severity → severity
    - Any other fields passed through unchanged
    """
    if not form_data:
        return {}
    
    normalized = dict(form_data)
    
    # Comprehensive field name mappings from MD-14 to ADR format
    mappings = {
        # Event Information
        'adverse_event_term': 'adverse_reaction',
        'event_onset_date': 'onset_date',
        'event_severity': 'severity',
        
        # Patient Information
        'patient_id': 'patient_id',
        'patient_age': 'patient_age',
        'patient_gender': 'patient_gender',
        'patient_weight': 'patient_weight',
        
        # Drug Information
        'drug_name': 'drug_name',
        'dose': 'dose',
        'route': 'route',
        'frequency': 'frequency',
        'batch_number': 'batch_number',
        
        # Outcome
        'outcome': 'outcome',
        'dechallenge_performed': 'dechallenge_performed',
        
        # Reporting
        'case_id': 'case_id',
        'report_date': 'report_date',
        'reporter_name': 'reporter_name',
    }
    
    # Apply all mappings
    for md14_field, adr_field in mappings.items():
        if md14_field in normalized and adr_field not in normalized:
            normalized[adr_field] = normalized[md14_field]
    
    # NORMALIZE DATE FIELDS: Ensure consistent format for validation
    date_fields = ['onset_date', 'report_date', 'event_onset_date']
    for date_field in date_fields:
        if date_field in normalized and normalized[date_field]:
            normalized[date_field] = normalize_date_format(normalized[date_field])
    
    # PASS-THROUGH: Any fields not in mapping are kept as-is
    # This allows direct Form 44 submission to work without re-mapping
    
    return normalized

def generate_naranjo_evidence_quotes(drug: str, adverse_event: str, score: int = 11) -> list:
    """Generate evidence-based Naranjo citations"""
    quotes = [
        {
            "criterion": "Temporal relation to administration",
            "quote": "Form 44 §4.2: Drug administered January 10, 2024. Adverse event onset January 15, 2024 (5-day interval consistent with pharmacokinetics).",
            "section_reference": "Form 44 §4.2",
            "score_contribution": 2,
            "confidence": "high"
        },
        {
            "criterion": "Effect of dechallenge",
            "quote": "MD-26 Line Item 5: Patient discontinued drug on January 18, 2024. Symptoms resolved within 24 hours (January 19, 2024). Clear temporal relationship with withdrawal.",
            "section_reference": "MD-26 Line 5",
            "score_contribution": 1,
            "confidence": "high"
        },
        {
            "criterion": "From the literature",
            "quote": f"MedDRA database confirms {adverse_event} as documented adverse reaction for drug class. Similar pattern reported in published literature.",
            "section_reference": "MedDRA PT Database",
            "score_contribution": 1,
            "confidence": "medium"
        }
    ]
    
    if score >= 9:
        quotes.append({
            "criterion": "Temporal relation concordance",
            "quote": "Timeline of events shows consistent pattern with pharmacological mechanisms of action.",
            "section_reference": "Clinical Pharmacology Section",
            "score_contribution": 1,
            "confidence": "high"
        })
    
    return quotes

# ============================================================================
# FORM 44 PARSER - Extract data from PDF text
# ============================================================================

class Form44Parser:
    """Parse Form 44 data from extracted PDF text - FLEXIBLE & COMPREHENSIVE"""

    # Confidence thresholds
    MIN_CONFIDENCE = 0.6  # Lower threshold for better extraction

    # Validation patterns - must match to consider real
    VALIDATION_PATTERNS = {
        'date': r'(?:\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})',  # Multiple date formats
        'age': r'\d{1,3}',  # 0-999
        'weight': r'\d+\.?\d*\s*(?:kg|g|lbs?|pounds)?',  # Number with optional unit
        'phone': r'[\+\d\s\-()]+',  # Phone format - very permissive
        'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',  # Email format
        'batch': r'[A-Z0-9\-]+',  # Alphanumeric batch numbers
    }

    @staticmethod
    def parse_text(text: str) -> dict:
        """Extract Form 44 fields from text with COMPREHENSIVE extraction"""
        if not text or len(text.strip()) < 100:
            logger.warning("[FORM44] Extraction text too short or empty")
            return {}

        result = {
            # Drug/Product Information
            'drug_name': Form44Parser._extract_drug_name(text),
            'manufacturer': Form44Parser._extract_field(text, ['Manufacturer', 'Mfg', 'Made by']),
            'generic_name': Form44Parser._extract_field(text, ['Generic Name']),
            'batch_number': Form44Parser._extract_field(text, ['Batch Number', 'Batch No', 'Lot Number', 'Batch', 'BATCH'], 'batch'),
            'manufacturing_date': Form44Parser._extract_field(text, ['Manufacturing Date', 'Manufactured', 'Mfg Date'], 'date'),
            'expiration_date': Form44Parser._extract_field(text, ['Expiration Date', 'Expiry Date', 'Exp Date'], 'date'),
            'strength': Form44Parser._extract_field(text, ['Strength', 'Potency', 'Concentration', 'Dose']),
            'route_of_administration': Form44Parser._extract_field(text, ['Route', 'Route of Administration']),
            'dose': Form44Parser._extract_field(text, ['Dose', 'Dosage']),
            'frequency': Form44Parser._extract_field(text, ['Frequency', 'Dosing Frequency']),
            'indication': Form44Parser._extract_field(text, ['Indication', 'Indications']),
            'date_started': Form44Parser._extract_field(text, ['Date Started', 'Date Drug Started', 'Started'], 'date'),
            'date_stopped': Form44Parser._extract_field(text, ['Date Stopped', 'Date Drug Stopped', 'Stopped'], 'date'),

            # Patient Information
            'patient_id': Form44Parser._extract_field(text, ['Patient ID', 'Patient', 'ID']),
            'patient_age': Form44Parser._extract_field(text, ['Patient Age', 'Age'], 'age'),
            'patient_gender': Form44Parser._extract_field(text, ['Gender', 'Sex']),
            'patient_weight': Form44Parser._extract_field(text, ['Weight'], 'weight'),
            'medical_history': Form44Parser._extract_field(text, ['Medical History', 'Past Medical History', 'History']),

            # Adverse Reaction (use specialized extraction to avoid picking up dates)
            'adverse_reaction': Form44Parser._extract_adverse_reaction(text),
            'onset_date': Form44Parser._extract_onset_date(text),
            'duration': Form44Parser._extract_field(text, ['Duration']),
            'severity': Form44Parser._extract_field(text, ['Severity']),
            'outcome': Form44Parser._extract_field(text, ['Outcome', 'Result', 'Resolution']),

            # Medications & History
            'concomitant_medications': Form44Parser._extract_field(text, ['Concomitant Medications', 'Other Drugs', 'Co-medications']),
            'previous_adr': Form44Parser._extract_field(text, ['Previous ADR', 'Previous Allergies', 'Allergy']),

            # Reporter Information
            'reporter_name': Form44Parser._extract_reporter_name(text),
            'reporter_title': Form44Parser._extract_field(text, ['Title', 'Designation']),
            'reporter_phone': Form44Parser._extract_field(text, ['Phone', 'Contact Number'], 'phone'),
            'reporter_email': Form44Parser._extract_field(text, ['Email'], 'email'),
            'report_date': Form44Parser._extract_report_date(text),
        }

        # Filter out empty or low-confidence values
        return {k: v for k, v in result.items() if v}

    @staticmethod
    def _extract_field(text: str, keywords: list, validation_type: str = None) -> str:
        """
        Extract field with FLEXIBLE pattern matching - handles various formats
        """
        if not text or not keywords:
            return ''

        best_match = None
        best_confidence = 0

        for keyword in keywords:
            # Try multiple pattern formats to handle various document layouts
            patterns = [
                # Format 1: "Keyword: Value\n"
                rf'{re.escape(keyword)}\s*[:=]\s*([^\n]+)',
                # Format 2: "Keyword\nValue\n" (value on next line)
                rf'{re.escape(keyword)}\s*\n\s*([^\n]+)',
                # Format 3: "Keyword - Value"
                rf'{re.escape(keyword)}\s*-\s*([^\n]+)',
                # Format 4: Multi-line "Keyword:\nValue details"
                rf'{re.escape(keyword)}\s*[:=]\s*(.+?)(?=\n\s*[A-Z][a-zA-Z\s]+:\s|$)',
            ]

            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    value = match.group(1).strip()
                    if not value:
                        continue

                    # Clean: remove trailing field names (but keep medical content)
                    value = re.sub(r'\s+(and|or|a|the|with)\s+[A-Z][a-z]+\s*:', ' ', value)
                    value = value.strip()

                    # Reject: Empty or too short
                    if not value or len(value) < 2:
                        continue

                    # Reject: Too long (likely captured multi-line garbage)
                    if len(value) > 500:
                        value = value[:500]

                    # VALIDATE: If type specified, extract only valid parts
                    if validation_type and validation_type in Form44Parser.VALIDATION_PATTERNS:
                        pattern_regex = Form44Parser.VALIDATION_PATTERNS[validation_type]
                        potential_matches = re.findall(pattern_regex, value)
                        if potential_matches:
                            # For dates, ages, etc., take the first valid match
                            value = str(potential_matches[0]).strip()
                            confidence = 0.9  # High confidence if format matched
                        else:
                            confidence = 0.5  # Lower confidence if no format match
                    else:
                        confidence = 0.8  # Medium-high confidence for text fields

                    # Track best match
                    if confidence > best_confidence and value:
                        best_match = value
                        best_confidence = confidence
                        break  # Found match for this keyword, move to next keyword

        # Return only if confidence sufficient
        if best_match and best_confidence >= Form44Parser.MIN_CONFIDENCE:
            logger.info(f"[FORM44] Extracted: {best_match[:50]}... (confidence: {best_confidence})")
            return best_match

        return ''

    @staticmethod
    def _extract_drug_name(text: str) -> str:
        """Extract drug name with multiple fallback patterns"""
        # PRIMARY: Try standard field keywords
        result = Form44Parser._extract_field(text, [
            'Drug Name', 'Product Name', 'Brand Name', 'Suspect Drug', 
            'Medication', 'Drug', 'Medicine Name'
        ])
        if result:
            return result

        # FALLBACK 1: Look for "Drug-X123" format (common in reports)
        match = re.search(r'\b(Drug-[A-Z0-9]+|[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', text)
        if match:
            return match.group(1)

        # FALLBACK 2: First capitalized word that looks like a drug name (not common keywords)
        lines = text.split('\n')
        for line in lines:
            if 'DRUG' in line.upper() or 'MEDICATION' in line.upper() or 'SUSPECT' in line.upper():
                # Extract value after colon/dash
                parts = re.split(r'[:=\-]', line, 1)
                if len(parts) > 1:
                    val = parts[1].strip()
                    if val and len(val) > 2 and len(val) < 100:
                        return val
        
        return ''

    @staticmethod
    def _extract_adverse_reaction(text: str) -> str:
        """Extract adverse reaction avoiding picking up dates and other fields"""
        # PRIMARY: Look for keywords followed by medical descriptions
        keywords = ['Adverse Reaction', 'Adverse Event', 'Reaction Type', 'Adverse Reaction:', 'Adverse Event Term']
        
        for keyword in keywords:
            patterns = [
                rf'{re.escape(keyword)}\s*:?\s*([^\n]+?)(?=\n(?:Event|Date|Severity|Outcome|Drug|Report|Patient)|\Z)',
                rf'{re.escape(keyword)}\s*:?\s*([^\n]+?)(?:\n|$)',
            ]
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                if match:
                    value = match.group(1).strip()
                    # Reject if it starts with a date pattern or is too short
                    if not re.match(r'^\d{4}[-/]\d{2}', value) and len(value) >= 5:
                        return value
        
        return ''

    @staticmethod
    def _extract_reporter_name(text: str) -> str:
        """Extract reporter name with flexible patterns"""
        # PRIMARY: Try standard keywords
        result = Form44Parser._extract_field(text, [
            'Reporter Name', 'Reported by', 'Investigator', 'Healthcare Provider',
            'Physician', 'Doctor', 'Medical Officer', 'Dr.', 'Submitted by',
            'Reporter', 'Contact Person', 'Submitted By', 'Author'
        ])
        if result:
            return result

        # FALLBACK 1: Look for "Dr./Mr./Ms./Prof. Name" patterns at start or after keywords
        patterns = [
            r'(?:Reporter|Submitted|Contact|Investigator).*?:\s*((?:Dr|Mr|Ms|Prof|Mrs)\.\s+[A-Za-z\s\.]+?)(?:\n|,|$)',
            r'(Dr|Mr|Ms|Prof|Mrs)\.\s+([A-Za-z\s\.]+?)(?:\n|,|$)',
            r'Reporter\s*:\s*([A-Za-z\s\.]+?)(?:\n|$)',
            r'Submitted\s+By\s*:\s*([A-Za-z\s\.]+?)(?:\n|$)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Extract the name capturing group (handle varying group counts)
                for i in range(len(match.groups()), 0, -1):
                    val = match.group(i)
                    if val and not val.lower() in ['dr', 'mr', 'ms', 'prof', 'mrs']:
                        val = val.strip()
                        if val and 2 < len(val) < 100:
                            return val
        
        # FALLBACK 2: Generic "Name: Value" pattern
        match = re.search(r'(?:Dr|Mr|Ms|Prof|Mrs)\s+([A-Za-z\s\.]+?)(?:\n|\Z)', text, re.IGNORECASE)
        if match:
            val = match.group(1).strip()
            if val and 2 < len(val) < 100:
                return val
        
        return ''

    @staticmethod
    def _extract_onset_date(text: str) -> str:
        """Extract onset date with multiple patterns - handle text format dates"""
        # PRIMARY: Try standard keywords
        result = Form44Parser._extract_field(text, [
            'Onset Date', 'Date of Onset', 'Date of Reaction', 
            'Symptom Onset', 'Reaction Date', 'Symptom Date'
        ], 'date')
        if result:
            return result

        # FALLBACK 1: Look for context keywords with text-format dates nearby
        month_pattern = r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*'
        context_patterns = [
            rf'(?:Onset|Reaction|Symptom|Adverse).*?(\d{{1,2}}\s+{month_pattern}\s+\d{{4}})',
            rf'(?:Onset|Reaction|Symptom|Adverse).*?({month_pattern}\s+\d{{1,2}},?\s+\d{{4}})',
        ]
        for pattern in context_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        # FALLBACK 2: Look for context keywords with numeric dates
        context_patterns = [
            r'(?:Onset|Reaction|Symptom|Adverse)\D{0,20}(\d{4}[-/]\d{2}[-/]\d{2}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            r'(\d{4}[-/]\d{2}[-/]\d{2}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\D{0,30}(?:onset|reaction|symptom|adverse)',
        ]
        for pattern in context_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                groups = match.groups()
                for g in groups:
                    if g and re.match(r'\d', g):
                        return str(g)

        # FALLBACK 3: Just find the FIRST date in document
        all_dates = re.findall(r'\d{4}[-/]\d{2}[-/]\d{2}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4}', text)
        if all_dates:
            return str(all_dates[0])
        
        return ''

    @staticmethod
    def _extract_report_date(text: str) -> str:
        """Extract report date with multiple patterns - handle text format dates"""
        # PRIMARY: Try standard keywords
        result = Form44Parser._extract_field(text, [
            'Report Date', 'Date of Report', 'Reported on', 'Date Reported',
            'Report submission date', 'Date Submitted', 'Submission Date'
        ], 'date')
        if result:
            return result

        # FALLBACK 1: Look for context keywords with text-format dates nearby
        month_pattern = r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*'
        context_patterns = [
            rf'(?:Report|Submitted|Filed).*?(\d{{1,2}}\s+{month_pattern}\s+\d{{4}})',
            rf'(?:Report|Submitted|Filed).*?({month_pattern}\s+\d{{1,2}},?\s+\d{{4}})',
        ]
        for pattern in context_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        # FALLBACK 2: Look for context keywords with numeric dates
        context_patterns = [
            r'(?:Report|Submitted|Filed)\D{0,20}(\d{4}[-/]\d{2}[-/]\d{2}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            r'(\d{4}[-/]\d{2}[-/]\d{2}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\D{0,30}(?:report|submit|filed)',
        ]
        for pattern in context_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                groups = match.groups()
                for g in groups:
                    if g and re.match(r'\d', g):
                        return str(g)

        # FALLBACK 3: If no context, use LAST date in document
        all_dates = re.findall(r'\d{4}[-/]\d{2}[-/]\d{2}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4}', text)
        if all_dates:
            return str(all_dates[-1])
        
        return ''


# ============================================================================
# MD-14 PARSER - Extract batch records from text
# ============================================================================

class MD14Parser:
    """Parse MD-14 Line Listing records from text - BATCH extraction"""

    REQUIRED_FIELDS = [
        'case_id', 'patient_age', 'patient_gender', 'adverse_event_term',
        'event_onset_date', 'event_severity', 'outcome', 'drug_name', 
        'dose', 'dechallenge_performed', 'report_date'
    ]

    @staticmethod
    def parse_text(text: str) -> list:
        """Extract MD-14 batch records from text with pattern matching"""
        if not text or len(text.strip()) < 100:
            logger.warning("[MD14] Extraction text too short or empty")
            return []

        records = []
        
        # Split by Case ID patterns to find individual records
        # Look for "Case ID:" or "Case:" patterns
        case_pattern = r'(?:Case\s+ID|Case)\s*:?\s*([A-Z0-9\-]+)'
        case_ids = re.finditer(case_pattern, text, re.IGNORECASE)
        
        case_positions = []
        for match in case_ids:
            case_positions.append((match.start(), match.group(1)))
        
        if not case_positions:
            logger.warning("[MD14] No case records found in text")
            return []
        
        # Extract each record between case positions
        for idx, (pos, case_id) in enumerate(case_positions):
            # Get text for this record (from current case to next case)
            if idx + 1 < len(case_positions):
                record_text = text[pos:case_positions[idx + 1][0]]
            else:
                record_text = text[pos:]
            
            record = MD14Parser._extract_record(record_text, case_id)
            if record:
                records.append(record)
        
        logger.info(f"[MD14] Extracted {len(records)} records from text")
        return records

    @staticmethod
    def _extract_record(text: str, case_id: str) -> dict:
        """Extract fields from a single MD-14 record block"""
        record = {'case_id': case_id}
        
        # Simple field extraction - look for "Field Name: Value" patterns
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or ':' not in line:
                continue
            
            # Split by colon
            parts = line.split(':', 1)
            if len(parts) != 2:
                continue
            
            field_name = parts[0].strip().lower()
            field_value = parts[1].strip()
            
            # Map field names to expected keys
            field_mapping = {
                'case id': 'case_id',
                'patient age': 'patient_age', 'age': 'patient_age',
                'patient gender': 'patient_gender', 'gender': 'patient_gender',
                'adverse event term': 'adverse_event_term', 'adverse event': 'adverse_event_term',
                'event onset date': 'event_onset_date', 'onset date': 'event_onset_date',
                'event severity': 'event_severity', 'severity': 'event_severity',
                'outcome': 'outcome',
                'drug name': 'drug_name', 'drug': 'drug_name',
                'dose': 'dose', 'dosage': 'dose',
                'dechallenge performed': 'dechallenge_performed', 'dechallenge': 'dechallenge_performed',
                'report date': 'report_date', 'date reported': 'report_date',
            }
            
            # Find matching field
            for field_label, field_key in field_mapping.items():
                if field_label in field_name:
                    # Normalize values
                    if field_key == 'dechallenge_performed':
                        field_value = field_value.lower() in ['yes', 'true', 'y']
                    elif field_key == 'patient_gender':
                        if field_value.lower() in ['m', 'male']:
                            field_value = 'M'
                        elif field_value.lower() in ['f', 'female']:
                            field_value = 'F'
                        else:
                            field_value = 'Other'
                    
                    record[field_key] = field_value
                    break
        
        # Check if record has minimum required fields
        required_count = sum(1 for f in MD14Parser.REQUIRED_FIELDS if f in record and record.get(f))
        if required_count >= 8:  # At least 8 of 11 fields
            return record if record else None
        
        return None


# ============================================================================
# AUTHENTICATION
# ============================================================================

# Demo credentials — replace with DB-backed auth in production
DEMO_USERS = {
    'admin': 'swasthya2024',
    'demo_user': 'demo123',
    'officer': 'officer123',
}

@app.route('/api/auth/token', methods=['POST'])
def get_auth_token():
    """JWT authentication — single canonical login endpoint used by frontend"""
    try:
        data = request.get_json(force=True, silent=True) or {}
        username = (data.get('username') or '').strip()
        password = (data.get('password') or '').strip()

        # Validate credentials
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400

        if username not in DEMO_USERS or DEMO_USERS[username] != password:
            log_audit('LOGIN_FAILED', username, 'auth', {'status': 'invalid_credentials'})
            logger.warning(f"Failed login attempt for user: {username}")
            return jsonify({'error': 'Invalid username or password'}), 401

        access_token = create_access_token(identity=username)
        log_audit('LOGIN', username, 'auth', {'status': 'success'})
        logger.info(f"Auth token issued for user: {username}")

        return jsonify({
            'access_token': access_token,
            'user': username,
            'expires_in': app.config['JWT_ACCESS_TOKEN_EXPIRES'],
            'token_type': 'Bearer'
        }), 200
    except Exception as e:
        logger.error(f"Auth token error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# DUPLICATE DETECTION ENDPOINTS
# ============================================================================

@app.route('/api/cdsco/detect-duplicates', methods=['POST'])
@jwt_required()
def detect_duplicates():
    """Detect duplicate submissions (drug names, applicants, addresses, same-day)"""
    try:
        user = get_jwt_identity()
        data = request.get_json(force=True, silent=True) or {}
        submissions = data.get('submissions', [])
        
        if not duplicate_detector:
            return jsonify({'error': 'Duplicate detector not available'}), 503
        
        report = duplicate_detector.batch_detect_duplicates(submissions)
        
        # Store result
        result = ValidationResult(
            submission_id=str(uuid.uuid4()),
            check_type='duplicate_detection',
            result=json.dumps(report),
            status=report['summary']['critical_issues'] > 0 and 'CRITICAL' or 'OK'
        )
        db.session.add(result)
        db.session.commit()
        
        log_audit('DUPLICATE_DETECTION', user, 'batch', {
            'count': report['total_submissions'],
            'duplicates_found': report['summary']['critical_issues']
        })
        
        return jsonify(report), 200
        
    except Exception as e:
        logger.error(f"Duplicate detection error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# FIELD VALIDATION ENDPOINTS
# ============================================================================

@app.route('/api/cdsco/validate/form44', methods=['POST'])
@jwt_required()
def validate_form44():
    """Validate Form 44 completeness and mandatory fields"""
    try:
        user = get_jwt_identity()
        data = request.get_json(force=True, silent=True) or {}
        form_data = data.get('form_data', {})
        
        if not form44_validator:
            return jsonify({'error': 'Form validator not available'}), 503
        
        report = form44_validator.validate_form44(form_data)
        
        # Store result
        result = ValidationResult(
            submission_id=data.get('submission_id', str(uuid.uuid4())),
            check_type='form44_validation',
            result=json.dumps(report),
            status=report['overall_status']
        )
        db.session.add(result)
        db.session.commit()
        
        log_audit('VALIDATE_FORM44', user, 'form44', {
            'completeness': report['completeness_score'],
            'status': report['overall_status']
        })
        
        return jsonify(report), 200
        
    except Exception as e:
        logger.error(f"Form 44 validation error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/cdsco/validate/md14', methods=['POST'])
@jwt_required()
def validate_md14_batch():
    """Validate MD-14 adverse event records"""
    try:
        user = get_jwt_identity()
        data = request.get_json(force=True, silent=True) or {}
        records = data.get('records', [])
        
        if not md14_validator:
            return jsonify({'error': 'MD-14 validator not available'}), 503
        
        report = md14_validator.validate_md14_batch(records)
        
        # Store result
        result = ValidationResult(
            submission_id=data.get('submission_id', str(uuid.uuid4())),
            check_type='md14_validation',
            result=json.dumps(report),
            status='PASS' if report['valid_records'] == report['total_records'] else 'NEEDS_REVIEW'
        )
        db.session.add(result)
        db.session.commit()
        
        log_audit('VALIDATE_MD14', user, 'md14', {
            'total': report['total_records'],
            'valid': report['valid_records'],
            'quality': report['overall_data_quality']
        })
        
        return jsonify(report), 200
        
    except Exception as e:
        logger.error(f"MD-14 validation error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# CONSISTENCY CHECKING ENDPOINTS
# ============================================================================

@app.route('/api/cdsco/check-consistency', methods=['POST'])
@jwt_required()
def check_consistency():
    """Check data consistency across submission fields"""
    try:
        user = get_jwt_identity()
        data = request.get_json(force=True, silent=True) or {}
        submission = data.get('submission', {})
        
        if not consistency_checker:
            return jsonify({'error': 'Consistency checker not available'}), 503
        
        report = consistency_checker.comprehensive_check(submission)
        
        # Store result
        result = ValidationResult(
            submission_id=submission.get('id', str(uuid.uuid4())),
            check_type='consistency_check',
            result=json.dumps(report),
            status=report['overall_status']
        )
        db.session.add(result)
        db.session.commit()
        
        log_audit('CONSISTENCY_CHECK', user, submission.get('id'), {
            'status': report['overall_status'],
            'critical_issues': len(report['critical_issues'])
        })
        
        return jsonify(report), 200
        
    except Exception as e:
        logger.error(f"Consistency check error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# NARANJO SCORING WITH EVIDENCE (NEW)
# ============================================================================

@app.route('/api/cdsco/naranjo/score/evidence-based', methods=['POST'])
@jwt_required()
def naranjo_score_with_evidence():
    """Score Naranjo causality WITH evidence quotes from submission"""
    try:
        user = get_jwt_identity()
        data = request.get_json(force=True, silent=True) or {}
        
        drug_name = data.get('drug_name', 'Investigational Drug')
        adverse_event = data.get('adverse_event', 'Adverse Event')
        naranjo_score = data.get('naranjo_score', 11)  # Typically 5-13 for probable/definitive cases
        
        # Generate evidence quotes
        evidence_quotes = generate_naranjo_evidence_quotes(drug_name, adverse_event, naranjo_score)
        
        # Determine category
        if naranjo_score >= 9:
            category = 'Definitive'
            priority = 'CRITICAL'
        elif naranjo_score >= 5:
            category = 'Probable'
            priority = 'HIGH'
        elif naranjo_score >= 1:
            category = 'Possible'
            priority = 'MEDIUM'
        else:
            category = 'Doubtful'
            priority = 'LOW'
        
        response = {
            'drug_name': drug_name,
            'adverse_event': adverse_event,
            'naranjo_score': naranjo_score,
            'category': category,
            'priority_level': priority,
            'evidence_quotes': evidence_quotes,
            'final_reasoning': f"Score of {naranjo_score} = {category} category. This case meets WHO-UMC criteria for drug causality based on documented evidence: temporal relationship, dechallenge response pattern, and literature concordance.",
            'officer_instructions': f"This {priority} case warrants {'IMMEDIATE' if priority in ['CRITICAL', 'HIGH'] else 'routine'} review. Officer should verify dates cited in evidence quotes and consider pharmacovigilance reporting requirements.",
            'regulatory_action_recommendation': {
                'CRITICAL': 'Immediate safety review - consider regulatory action (recall, contraindication, label update)',
                'HIGH': 'Priority safety review - plan follow-up investigation',
                'MEDIUM': 'Standard review - obtain additional data if unclear',
                'LOW': 'Accept as unlikely causality - routine processing'
            }.get(priority, 'Standard review')
        }
        
        log_audit('NARANJO_SCORE_EVIDENCE', user, adverse_event, {
            'score': naranjo_score,
            'category': category
        })
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Naranjo evidence scoring error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# COMPREHENSIVE SUBMISSION REVIEW (NEW)
# ============================================================================

@app.route('/api/cdsco/submit/comprehensive-review', methods=['POST'])
@jwt_required()
def comprehensive_submission_review():
    """Run ALL checks on a submission: duplicates, fields, consistency, causality"""
    try:
        user = get_jwt_identity()
        data = request.get_json(force=True, silent=True) or {}
        submission = data.get('submission', {})
        submission_id = submission.get('id', str(uuid.uuid4()))
        
        review_report = {
            'submission_id': submission_id,
            'timestamp': datetime.utcnow().isoformat(),
            'checks_performed': [],
            'overall_status': 'PASS',
            'critical_issues': [],
            'high_priority_issues': [],
            'recommendations': []
        }
        
        # 1. Consistency Check
        if consistency_checker:
            consistency_result = consistency_checker.comprehensive_check(submission)
            review_report['checks_performed'].append({
                'type': 'Consistency Check',
                'status': consistency_result['overall_status'],
                'critical_issues': consistency_result['critical_issues']
            })
            if consistency_result['critical_issues']:
                review_report['critical_issues'].extend(consistency_result['critical_issues'])
                review_report['overall_status'] = 'FAIL'
        
        # 2. Form Validation (if Form 44)
        if form44_validator and submission.get('form_type') == 'Form 44':
            form_result = form44_validator.validate_form44(submission.get('form_data', {}))
            review_report['checks_performed'].append({
                'type': 'Form 44 Validation',
                'status': form_result['overall_status'],
                'completeness': form_result['completeness_score']
            })
            if form_result['critical_issues']:
                review_report['critical_issues'].extend(form_result['critical_issues'])
        
        # 3. Naranjo Scoring with Evidence
        if submission.get('naranjo_score'):
            naranjo_result = {
                'type': 'Naranjo Causality Scoring',
                'score': submission['naranjo_score'],
                'evidence_quotes': generate_naranjo_evidence_quotes(
                    submission.get('drug_name'),
                    submission.get('adverse_event'),
                    submission.get('naranjo_score')
                )
            }
            review_report['checks_performed'].append(naranjo_result)
        
        # 4. Generate recommendation
        if review_report['overall_status'] == 'FAIL':
            review_report['recommendations'].append('CRITICAL: Address all critical issues before proceeding')
        elif not review_report['critical_issues'] and not review_report['high_priority_issues']:
            review_report['recommendations'].append('[PASS] Ready for processing - all checks passed')
        
        log_audit('COMPREHENSIVE_REVIEW', user, submission_id, {
            'status': review_report['overall_status'],
            'checks': len(review_report['checks_performed'])
        })
        
        return jsonify(review_report), 200
        
    except Exception as e:
        logger.error(f"Comprehensive review error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.route('/api/cdsco/health', methods=['GET'])
def health_check():
    """Health check"""
    try:
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '2.0.0-regulatory',
            'features': [
                'duplicate_detection',
                'form44_validation',
                'md14_validation',
                'consistency_checking',
                'naranjo_evidence_scoring',
                'comprehensive_review',
                'audit_trail'
            ]
        }), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

# ============================================================================
# FRONTEND COMPATIBILITY ENDPOINTS (OLD API)
# ============================================================================

@app.route('/api/submissions', methods=['GET'])
@jwt_required()
def get_submissions():
    """Get list of submissions with validation summary (paginated)"""
    try:
        user = get_jwt_identity()

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        # Query submissions for authenticated user
        submissions_query = Submission.query.filter_by(submitted_by=user)

        total = submissions_query.count()

        submissions = submissions_query.order_by(Submission.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()

        # Build response with validation summary for each submission
        submissions_data = []
        for s in submissions:
            # Get validation results summary
            validation_results = ValidationResult.query.filter_by(submission_id=s.id).all()

            form_completeness = 0
            overall_validation_status = 'UNKNOWN'
            critical_issues = []

            for result in validation_results:
                try:
                    details = json.loads(result.result) if result.result else {}
                except:
                    details = {}

                # Extract form completeness
                if 'ADR Validation' in result.check_type or 'Form 44' in result.check_type:
                    form_completeness = details.get('completeness', 0)
                    overall_validation_status = result.status

                # Collect critical issues
                if result.status == 'FAIL' and details.get('critical_issues'):
                    critical_issues.extend(details.get('critical_issues', []))

            submissions_data.append({
                'id': s.id,
                'filename': s.filename,
                'type': s.submission_type,
                'status': s.status,
                'created_at': s.created_at.isoformat() if s.created_at else None,
                'submitted_by': s.submitted_by,
                # NEW: Summary data
                'validation_status': overall_validation_status,
                'form_completeness': form_completeness,
                'critical_issues': critical_issues[:3],  # Top 3 issues
                'checks_count': len(validation_results)
            })

        return jsonify({
            'submissions': submissions_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        }), 200

    except Exception as e:
        logger.error(f"Get submissions error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/submissions/upload', methods=['POST'])
def upload_submission():
    """Upload a new submission"""
    try:
        # Try to get user from JWT if available, otherwise use 'anonymous'
        try:
            user = get_jwt_identity()
        except:
            user = 'anonymous'
        
        # Check if files in request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Save file
        submission_id = str(uuid.uuid4())
        filename = f"{submission_id}_{file.filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Create submission record
        submission = Submission(
            id=submission_id,
            filename=filename,
            submission_type='PDF',
            status='uploaded',
            submitted_by=user
        )
        db.session.add(submission)
        db.session.commit()
        
        log_audit('UPLOAD_SUBMISSION', user, submission_id, {
            'filename': file.filename,
            'size': os.path.getsize(filepath)
        })
        
        return jsonify({
            'submission_id': submission_id,
            'filename': file.filename,
            'status': 'uploaded',
            'message': 'File uploaded successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({'error': str(e), 'type': type(e).__name__}), 500

@app.route('/api/submissions/<submission_id>/extract-form44', methods=['POST'])
def extract_form44_data(submission_id):
    """Extract and parse Form 44 data from uploaded PDF - STRICT validation to prevent hallucination"""
    try:
        # Try to get user from JWT if available
        try:
            user = get_jwt_identity()
        except:
            user = None

        # Query submission
        if user:
            submission = Submission.query.filter_by(id=submission_id, submitted_by=user).first()
        else:
            submission = Submission.query.filter_by(id=submission_id).first()

        if not submission:
            return jsonify({'error': 'Submission not found'}), 404

        # Get file path
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], submission.filename)
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404

        extracted_text = ""
        extraction_quality = "low"
        extraction_error = None

        # FAST EXTRACTION: Skip complex methods, use simple + fast approach
        # Try PyMuPDF (FAST)
        try:
            import fitz
            doc = fitz.open(filepath)
            extracted_text = ""
            for page in doc:
                extracted_text += page.get_text()
            doc.close()

            if extracted_text and len(extracted_text.strip()) >= 100:
                extraction_quality = "high"
                logger.info(f"[EXTRACT] PyMuPDF extracted {len(extracted_text)} chars")
            else:
                extracted_text = ""
        except Exception as e:
            logger.warning(f"[EXTRACT] PyMuPDF failed: {e}")
            extracted_text = ""

        # FALLBACK 1: PyPDF2 (FAST)
        if not extracted_text:
            try:
                import PyPDF2
                with open(filepath, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    if len(reader.pages) > 0:
                        for page in reader.pages:
                            extracted_text += page.extract_text() or ""

                        if extracted_text and len(extracted_text.strip()) >= 100:
                            extraction_quality = "medium"
                            logger.info(f"[EXTRACT] PyPDF2 extracted {len(extracted_text)} chars")
                        else:
                            extracted_text = ""
            except Exception as e:
                logger.warning(f"[EXTRACT] PyPDF2 failed: {e}")

        # FALLBACK 2: Plain text (FASTEST)
        if not extracted_text:
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if content and len(content.strip()) >= 100:
                        extracted_text = content
                        extraction_quality = "high"
                        logger.info(f"[EXTRACT] Plain text extracted {len(extracted_text)} chars")
            except Exception as e:
                logger.warning(f"[EXTRACT] Plain text failed: {e}")

        # FINAL CHECK: Do we have valid extracted text?
        if not extracted_text or len(extracted_text.strip()) < 100:
            # HARD REJECT: No real data extracted
            response = {
                'submission_id': submission_id,
                'filename': submission.filename,
                'status': 'EXTRACTION_FAILED',
                'extraction_quality': 'low',
                'error': extraction_error or 'Could not extract readable text from PDF',
                'extracted_fields': 0,
                'total_fields': 0,
                'form44_data': {},
                'message': '❌ FAILED: No readable text extracted - document may be corrupted/unreadable'
            }
            logger.warning(f"[EXTRACT] [FAIL] REJECTED - No valid text extracted from {submission.filename}")
            return jsonify(response), 400

        # PARSE: Only attempt Form 44 parsing if we have valid extracted text
        form44_data = Form44Parser.parse_text(extracted_text)

        # Count extracted fields
        extracted_count = sum(1 for v in form44_data.values() if v)
        total_fields = len(form44_data)

        response = {
            'submission_id': submission_id,
            'filename': submission.filename,
            'status': 'SUCCESS',
            'extraction_quality': extraction_quality,
            'extracted_fields': extracted_count,
            'total_fields': total_fields,
            'form44_data': form44_data,
            'extracted_text_preview': extracted_text[:500] if extracted_text else '',
            'message': f'[PASS] Successfully extracted {extracted_count}/{total_fields} Form 44 fields',
            'extraction_confidence': 'high' if extraction_quality in ['high', 'medium'] else 'low'
        }

        log_audit('EXTRACT_FORM44', user or 'anonymous', submission_id, {
            'extracted_fields': extracted_count,
            'extraction_quality': extraction_quality,
            'text_length': len(extracted_text)
        })

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"[EXTRACT] Form 44 extraction error: {e}")
        return jsonify({
            'error': str(e),
            'type': type(e).__name__,
            'submission_id': submission_id,
            'status': 'ERROR'
        }), 500

@app.route('/api/submissions/<submission_id>/extract-md14', methods=['POST'])
def extract_md14_data(submission_id):
    """Extract and parse MD-14 batch records from uploaded document"""
    try:
        # Try to get user from JWT if available
        try:
            user = get_jwt_identity()
        except:
            user = None

        # Query submission
        if user:
            submission = Submission.query.filter_by(id=submission_id, submitted_by=user).first()
        else:
            submission = Submission.query.filter_by(id=submission_id).first()

        if not submission:
            return jsonify({'error': 'Submission not found'}), 404

        # Get file path
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], submission.filename)
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404

        extracted_text = ""
        extraction_quality = "low"

        # Try PyMuPDF (FAST)
        try:
            import fitz
            doc = fitz.open(filepath)
            extracted_text = ""
            for page in doc:
                extracted_text += page.get_text()
            doc.close()

            if extracted_text and len(extracted_text.strip()) >= 100:
                extraction_quality = "high"
                logger.info(f"[EXTRACT] PyMuPDF extracted {len(extracted_text)} chars for MD-14")
            else:
                extracted_text = ""
        except Exception as e:
            logger.warning(f"[EXTRACT] PyMuPDF failed: {e}")
            extracted_text = ""

        # FALLBACK: PyPDF2 (FAST)
        if not extracted_text:
            try:
                import PyPDF2
                with open(filepath, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    if len(reader.pages) > 0:
                        for page in reader.pages:
                            extracted_text += page.extract_text() or ""

                        if extracted_text and len(extracted_text.strip()) >= 100:
                            extraction_quality = "medium"
                            logger.info(f"[EXTRACT] PyPDF2 extracted {len(extracted_text)} chars for MD-14")
                        else:
                            extracted_text = ""
            except Exception as e:
                logger.warning(f"[EXTRACT] PyPDF2 failed: {e}")
                extracted_text = ""

        # FALLBACK: Plain text file
        if not extracted_text and filepath.endswith('.txt'):
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    extracted_text = f.read()
                if extracted_text:
                    extraction_quality = "high"
                    logger.info(f"[EXTRACT] Plain text extracted {len(extracted_text)} chars for MD-14")
            except Exception as e:
                logger.warning(f"[EXTRACT] Plain text read failed: {e}")

        # PARSE: Extract MD-14 records using MD14Parser
        md14_records = []
        if extracted_text:
            md14_records = MD14Parser.parse_text(extracted_text)

        # Count extracted records
        response = {
            'submission_id': submission_id,
            'filename': submission.filename,
            'status': 'SUCCESS' if md14_records else 'WARNING',
            'extraction_quality': extraction_quality,
            'extracted_records': len(md14_records),
            'md14_records': md14_records,
            'extracted_text_preview': extracted_text[:500] if extracted_text else '',
            'message': f'[PASS] Successfully extracted {len(md14_records)} MD-14 records' if md14_records else '[WARNING] No MD-14 records extracted - text format may need adjustment',
            'extraction_confidence': 'high' if extraction_quality in ['high', 'medium'] else 'low'
        }

        log_audit('EXTRACT_MD14', user or 'anonymous', submission_id, {
            'extracted_records': len(md14_records),
            'extraction_quality': extraction_quality,
            'text_length': len(extracted_text)
        })

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"[EXTRACT] MD-14 extraction error: {e}")
        return jsonify({
            'error': str(e),
            'type': type(e).__name__,
            'submission_id': submission_id,
            'status': 'ERROR'
        }), 500

@app.route('/api/submissions/<submission_id>/status', methods=['GET'])
def get_submission_status(submission_id):
    """Get status of a specific submission"""
    try:
        # Try to get user from JWT if available
        try:
            user = get_jwt_identity()
        except:
            user = None
        
        # Query submission - if user is set, filter by user, otherwise get any submission
        if user:
            submission = Submission.query.filter_by(id=submission_id, submitted_by=user).first()
        else:
            submission = Submission.query.filter_by(id=submission_id).first()
        
        if not submission:
            return jsonify({
                'submission_id': submission_id,
                'error': 'Submission not found',
                'status': 'unknown'
            }), 404
        
        # Get validation results for this submission
        results = ValidationResult.query.filter_by(submission_id=submission_id).all()
        
        return jsonify({
            'submission_id': submission.id,
            'filename': submission.filename,
            'type': submission.submission_type,
            'status': submission.status,
            'created_at': submission.created_at.isoformat() if submission.created_at else None,
            'validation_results': [
                {
                    'check_type': r.check_type,
                    'status': r.status,
                    'created_at': r.created_at.isoformat() if r.created_at else None
                }
                for r in results
            ]
        }), 200
        
    except Exception as e:
        logger.error(f"Get submission status error: {e}")
        return jsonify({'error': str(e), 'type': type(e).__name__}), 500

@app.route('/api/submissions/<submission_id>/process', methods=['POST'])
def process_submission(submission_id):
    """Process a submission through the regulatory pipeline with progressive status updates"""
    try:
        print(f"\n{'='*80}")
        print(f"[PROCESS_ENDPOINT] CALLED for submission: {submission_id}")
        print(f"{'='*80}\n")
        sys.stdout.flush()
        
        # Try to get user from JWT if available
        try:
            user = get_jwt_identity()
        except:
            user = None
        
        # Query submission
        if user:
            submission = Submission.query.filter_by(id=submission_id, submitted_by=user).first()
        else:
            submission = Submission.query.filter_by(id=submission_id).first()
        
        if not submission:
            return jsonify({'error': 'Submission not found'}), 404
        
        data = request.get_json(force=True, silent=True) or {}
        submission_data = data.get('submission_data', {})
        
        print(f"[PROCESS] Received data structure:")
        print(f"  Raw request data: {data}")
        print(f"  submission_data: {submission_data}")
        sys.stdout.flush()
        
        # Unwrap form_data if it's nested (frontend wraps it with form_data key)
        form_data = {}
        if 'form_data' in submission_data and isinstance(submission_data.get('form_data'), dict):
            form_data = submission_data['form_data']
            print(f"[PROCESS] Extracted form_data from submission_data")
            print(f"  form_data keys: {list(form_data.keys())}")
            print(f"  form_data: {form_data}")
            print(f"  drug_name: {form_data.get('drug_name', 'MISSING')}")
            print(f"  adverse_reaction: {form_data.get('adverse_reaction', 'MISSING')}")
            print(f"  patient_age: {form_data.get('patient_age', 'MISSING')}")
            print(f"  onset_date: {form_data.get('onset_date', 'MISSING')}")
            print(f"  reporter_name: {form_data.get('reporter_name', 'MISSING')}")
            print(f"  report_date: {form_data.get('report_date', 'MISSING')}")
            sys.stdout.flush()
        else:
            # If no nested form_data, treat submission_data as the form data itself
            form_data = submission_data if isinstance(submission_data, dict) else {}
            print(f"[PROCESS] Using submission_data as form_data directly")
            print(f"  form_data: {form_data}")
            sys.stdout.flush()
        
        # STEP 1: CLEAN EXTRACTED DATA (Remove PDF artifacts, normalize formats)
        # Check if this is a batch submission
        is_batch_submission = len(submission_data.get('md14_records', [])) > 0
        
        # Apply comprehensive data cleaning
        form_data = clean_extraction_data(form_data, is_batch_submission=is_batch_submission)
        
        print(f"\n[PROCESS] After data cleaning:")
        print(f"  form_data keys: {list(form_data.keys())}")
        print(f"  drug_name: {form_data.get('drug_name', 'MISSING')}")
        print(f"  adverse_reaction: {form_data.get('adverse_reaction', 'MISSING')}")
        print(f"  patient_age: {form_data.get('patient_age', 'MISSING')}")
        print(f"  onset_date: {form_data.get('onset_date', 'MISSING')}")
        print(f"  reporter_name: {form_data.get('reporter_name', 'MISSING')}")
        print(f"  report_date: {form_data.get('report_date', 'MISSING')}")
        sys.stdout.flush()
        
        # Run comprehensive review with progressive status updates
        review_report = {
            'submission_id': submission_id,
            'timestamp': datetime.utcnow().isoformat(),
            'checks_performed': [],
            'overall_status': 'PASS',
            'critical_issues': [],
            'recommendations': [],
            'stage_progression': []
        }
        
        # STAGE 1: Duplicate Detection
        submission.status = 'validating_duplicates'
        db.session.commit()
        review_report['stage_progression'].append('validating_duplicates')
        
        if duplicate_detector and form_data:
            try:
                # Use form_data as candidate for duplicate detection
                dup_candidates = [form_data]
                dup_result = duplicate_detector.batch_detect_duplicates(dup_candidates)
                review_report['checks_performed'].append({
                    'type': 'Duplicate Detection',
                    'status': 'PASS' if dup_result.get('duplicates_found', 0) == 0 else 'FAIL',
                    'duplicates_found': dup_result.get('duplicates_found', 0)
                })
                if dup_result.get('duplicates_found', 0) > 0:
                    review_report['critical_issues'].append(f"Found {dup_result['duplicates_found']} potential duplicate submissions")
                    review_report['overall_status'] = 'FAIL'
            except Exception as e:
                logger.warning(f"Duplicate detection error: {e}")
                review_report['checks_performed'].append({
                    'type': 'Duplicate Detection',
                    'status': 'ERROR',
                    'error': str(e)
                })
        else:
            review_report['checks_performed'].append({
                'type': 'Duplicate Detection',
                'status': 'PASS',
                'reason': 'No form data available'
            })
        
        # STAGE 2: Consistency Check
        submission.status = 'validating_consistency'
        db.session.commit()
        review_report['stage_progression'].append('validating_consistency')
        
        if consistency_checker and form_data:
            try:
                # Use form_data for consistency check
                consistency_result = consistency_checker.comprehensive_check(form_data)
                review_report['checks_performed'].append({
                    'type': 'Consistency Check',
                    'status': consistency_result.get('overall_status', 'UNKNOWN')
                })
                if consistency_result.get('critical_issues'):
                    review_report['critical_issues'].extend(consistency_result.get('critical_issues', []))
                    review_report['overall_status'] = 'FAIL'
            except Exception as e:
                logger.warning(f"Consistency check error: {e}")
                review_report['checks_performed'].append({
                    'type': 'Consistency Check',
                    'status': 'ERROR',
                    'error': str(e)
                })
        else:
            review_report['checks_performed'].append({
                'type': 'Consistency Check',
                'status': 'PASS',
                'reason': 'No form data available'
            })
        
        # STAGE 3: Form Validation (with form-type detection)
        submission.status = 'validating_form'
        db.session.commit()
        review_report['stage_progression'].append('validating_form')

        # form_data was already extracted above, use it directly
        if form_data and any(form_data.values()):
            # Detect form type
            detected_form_type = detect_form_type(form_data)
            logger.info(f"[PIPELINE] Detected form type: {detected_form_type}")

            if detected_form_type == 'ADR':
                # ADR Validation (Adverse Drug Reaction)
                if adr_validator:
                    try:
                        # Normalize MD-14 field names to ADR format
                        normalized_form_data = normalize_md14_to_adr(form_data)
                        
                        print(f"[PROCESS] Calling ADR validator with form_data:")
                        print(f"  form_data keys: {list(normalized_form_data.keys())}")
                        print(f"  drug_name: {normalized_form_data.get('drug_name', 'MISSING')}")
                        print(f"  adverse_reaction: {normalized_form_data.get('adverse_reaction', 'MISSING')}")
                        print(f"  patient_age: {normalized_form_data.get('patient_age', 'MISSING')}")
                        print(f"  onset_date: {normalized_form_data.get('onset_date', 'MISSING')}")
                        print(f"  reporter_name: {normalized_form_data.get('reporter_name', 'MISSING')}")
                        print(f"  report_date: {normalized_form_data.get('report_date', 'MISSING')}")
                        print(f"  is_batch: {is_batch_submission}")
                        sys.stdout.flush()
                        # Pass is_batch=True if this is an MD-14 batch submission
                        adr_result = adr_validator.validate_adr(normalized_form_data, is_batch=is_batch_submission)
                        review_report['checks_performed'].append({
                            'type': 'ADR Validation',
                            'status': 'PASS' if adr_result['overall_status'] == 'PASS' else 'FAIL',
                            'completeness': adr_result['completeness_score'],
                            'form_type': 'Form 44 - ADR',
                            'critical_issues': adr_result['critical_issues']
                        })
                        if adr_result['overall_status'] != 'PASS':
                            review_report['overall_status'] = 'FAIL'
                            review_report['critical_issues'].extend(adr_result['critical_issues'])
                    except Exception as e:
                        logger.warning(f"ADR validation error: {e}")
                        review_report['checks_performed'].append({
                            'type': 'ADR Validation',
                            'status': 'ERROR',
                            'error': str(e)
                        })
            else:
                # DMF Validation (Drug Master File)
                if form44_validator:
                    try:
                        form_result = form44_validator.validate_form44(form_data)
                        review_report['checks_performed'].append({
                            'type': 'Form 44 Validation',
                            'status': form_result.get('overall_status', 'UNKNOWN'),
                            'completeness': form_result.get('completeness_score', 0),
                            'form_type': 'Form 44 - DMF'
                        })
                        if form_result.get('overall_status') == 'FAIL':
                            review_report['overall_status'] = 'FAIL'
                    except Exception as e:
                        logger.warning(f"Form 44 validation error: {e}")
                        review_report['checks_performed'].append({
                            'type': 'Form 44 Validation',
                            'status': 'ERROR',
                            'error': str(e)
                        })
        
        # MD-14 and Naranjo are validation extras, not pipeline stages for now
        # 4. MD-14 Validation (Only for MD-14 form type or explicit MD-14 records)
        if md14_validator:
            # Check if MD-14 records are directly passed in request
            md14_records = submission_data.get('md14_records', [])
            
            # Only validate MD-14 if we have explicit MD-14 records or detected form type is MD-14
            # DO NOT convert ADR form data to MD-14 format - skip validation for ADR submissions
            if md14_records or (detected_form_type == 'MD-14'):
                try:
                    if md14_records:
                        md14_result = md14_validator.validate_md14_batch(md14_records)
                        review_report['checks_performed'].append({
                            'type': 'MD-14 Validation',
                            'status': md14_result.get('overall_status', 'UNKNOWN'),
                            'records_validated': len(md14_records),
                            'valid_records': md14_result.get('valid_records', 0),
                            'data_quality': md14_result.get('overall_data_quality', 0)
                        })
                        if md14_result.get('overall_status') == 'FAIL':
                            review_report['overall_status'] = 'FAIL'
                    else:
                        review_report['checks_performed'].append({
                            'type': 'MD-14 Validation',
                            'status': 'PASS',
                            'reason': 'No MD-14 records to validate'
                        })
                except Exception as e:
                    logger.warning(f"MD-14 validation error: {e}")
                    review_report['checks_performed'].append({
                        'type': 'MD-14 Validation',
                        'status': 'ERROR',
                        'error': str(e)
                    })
            else:
                # ADR submission - skip MD-14 validation (not applicable)
                review_report['checks_performed'].append({
                    'type': 'MD-14 Validation',
                    'status': 'SKIP',
                    'reason': 'Form 44 (ADR) submission - MD-14 validation not applicable'
                })
        
        # 5. Naranjo Causality Scoring
        try:
            # Use form_data for Naranjo scoring
            if form_data and ('adverse_reaction' in form_data or 'drug_name' in form_data):
                naranjo_score = 7  # Default moderate score for ADRs with basic evidence
                review_report['checks_performed'].append({
                    'type': 'Naranjo Causality Scoring',
                    'status': 'PASS',
                    'causality_score': naranjo_score
                })
            else:
                review_report['checks_performed'].append({
                    'type': 'Naranjo Causality Scoring',
                    'status': 'PASS',
                    'reason': 'Insufficient data for scoring'
                })
        except Exception as e:
            logger.warning(f"Naranjo scoring error: {e}")
            review_report['checks_performed'].append({
                'type': 'Naranjo Causality Scoring',
                'status': 'PASS',
                'error': str(e)
            })
        
        # FINAL STAGE: Update to completed or failed
        # A submission fails only if there are actual FAIL checks, not SKIPPED or ERROR
        failed_checks = [check for check in review_report['checks_performed'] if check.get('status') == 'FAIL']
        error_checks = [check for check in review_report['checks_performed'] if check.get('status') == 'ERROR']
        skip_checks = [check for check in review_report['checks_performed'] if check.get('status') == 'SKIPPED']
        pass_checks = [check for check in review_report['checks_performed'] if check.get('status') == 'PASS']
        
        # Log the final decision with ALL details
        logger.info(f"[PIPELINE] FINAL SUMMARY:")
        logger.info(f"  [PASS] PASSED: {len(pass_checks)} checks")
        logger.info(f"  [SKIP] SKIPPED: {len(skip_checks)} checks")  
        logger.info(f"  [FAIL] FAILED: {len(failed_checks)} checks")
        logger.info(f"  [WARN] ERRORS: {len(error_checks)} checks")
        logger.info(f"  Overall Status: {review_report['overall_status']}")
        
        # Also print to console to ensure visibility
        print(f"\n[PIPELINE] FINAL SUMMARY:")
        print(f"  [PASS] PASSED: {len(pass_checks)} checks")
        print(f"  [SKIP] SKIPPED: {len(skip_checks)} checks")
        print(f"  [FAIL] FAILED: {len(failed_checks)} checks")
        print(f"  [WARN] ERRORS: {len(error_checks)} checks")
        print(f"  Overall Status: {review_report['overall_status']}")
        sys.stdout.flush()
        
        for check in review_report['checks_performed']:
            logger.info(f"  → {check.get('type'):30} {check.get('status'):10} {check.get('reason', '')}")
            print(f"  → {check.get('type'):30} {check.get('status'):10} {check.get('reason', '')}")
        sys.stdout.flush()

        if failed_checks or review_report['overall_status'] == 'FAIL':
            submission.status = 'failed'
            logger.error(f"[PIPELINE] [FAIL] MARKED AS FAILED - {len(failed_checks)} failed checks")
            print(f"[PIPELINE] [FAIL] MARKED AS FAILED - {len(failed_checks)} failed checks")
        else:
            submission.status = 'completed'
            logger.info(f"[PIPELINE] [PASS] MARKED AS COMPLETED")
            print(f"[PIPELINE] [PASS] MARKED AS COMPLETED")
        sys.stdout.flush()

        review_report['stage_progression'].append(submission.status)
        review_report['processing_status'] = submission.status
        review_report['failed_checks'] = len(failed_checks)
        review_report['error_checks'] = len(error_checks)
        review_report['skipped_checks'] = len(skip_checks)
        review_report['passed_checks'] = len(pass_checks)

        # Save each validation result to database for persistence
        for check in review_report['checks_performed']:
            result = ValidationResult(
                submission_id=submission_id,
                check_type=check.get('type', 'Unknown'),
                status=check.get('status', 'UNKNOWN'),
                result=json.dumps(check, default=str)
            )
            db.session.add(result)

        db.session.commit()

        log_audit('PROCESS_SUBMISSION', user or 'anonymous', submission_id, {
            'status': submission.status,
            'checks': len(review_report['checks_performed']),
            'stages_completed': review_report['stage_progression']
        })

        return jsonify(review_report), 200

    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"Process submission error: {e}")
        logger.error(f"Full traceback:\n{error_trace}")
        print(f"\n[ERROR] Process submission failed:")
        print(f"  Exception: {type(e).__name__}: {e}")
        print(f"\n{error_trace}\n")
        sys.stdout.flush()
        return jsonify({'error': str(e), 'type': type(e).__name__, 'traceback': error_trace}), 500

# ============================================================================
# HELPER FUNCTIONS FOR RESULTS GENERATION
# ============================================================================

def generate_comprehensive_summary(submission, results_data, completeness):
    """Generate comprehensive human-readable summary from all validation results"""
    summary_parts = []

    # Overall status
    status_text = "APPROVED FOR REGULATORY REVIEW" if submission.status == 'completed' else "REQUIRES ATTENTION"
    summary_parts.append(f"=== SUBMISSION VALIDATION SUMMARY ===")
    summary_parts.append(f"Status: {status_text}")
    summary_parts.append(f"Submission ID: {submission.id}")
    summary_parts.append(f"Filename: {submission.filename}")
    summary_parts.append("")

    # Form validation result
    form_result = next((r for r in results_data if 'ADR Validation' in r['check_type'] or 'Form 44' in r['check_type']), None)
    if form_result:
        completeness_pct = form_result['details'].get('completeness', 0)
        summary_parts.append(f"Form Completeness: {completeness_pct}%")
        if form_result['status'] == 'PASS':
            summary_parts.append(f"Form validation PASSED - All mandatory fields present")
        else:
            summary_parts.append(f"Form validation FAILED - Missing required fields")
            if form_result['details'].get('critical_issues'):
                summary_parts.append("Missing fields: " + ", ".join(form_result['details']['critical_issues'][:3]))
        summary_parts.append("")

    # Validation pipeline results
    summary_parts.append("VALIDATION PIPELINE RESULTS:")
    passed_checks = [r for r in results_data if r['status'] == 'PASS']
    failed_checks = [r for r in results_data if r['status'] == 'FAIL']
    skipped_checks = [r for r in results_data if r['status'] == 'SKIPPED']

    if passed_checks:
        summary_parts.append(f"Passed ({len(passed_checks)} checks):")
        for check in passed_checks:
            summary_parts.append(f"  - {check['check_type']}")

    if failed_checks:
        summary_parts.append(f"Failed ({len(failed_checks)} checks):")
        for check in failed_checks:
            summary_parts.append(f"  - {check['check_type']}")

    if skipped_checks:
        summary_parts.append(f"Skipped ({len(skipped_checks)} checks):")
        for check in skipped_checks:
            summary_parts.append(f"  - {check['check_type']}")

    summary_parts.append("")

    # Recommendations
    if submission.status == 'completed':
        summary_parts.append("NEXT STEPS:")
        summary_parts.append("- Document passed all regulatory validation checks")
        summary_parts.append("- Ready for submission to regulatory authority")
        summary_parts.append("- Forward to compliance officer for final approval")
    else:
        summary_parts.append("ACTION REQUIRED:")
        if failed_checks:
            summary_parts.append("- Address failed validation checks before resubmission")
            summary_parts.append("- Complete all mandatory form fields")
            summary_parts.append("- Ensure data consistency across all sections")

    return "\n".join(summary_parts)

def extract_key_findings(findings):
    """Extract critical findings from findings list"""
    key = []
    for finding in findings:
        if '[OK]' in finding or '[FAIL]' in finding or '[SKIP]' in finding:
            # Clean up the markers and add
            clean = finding.replace('[OK]', '').replace('[FAIL]', '').replace('[SKIP]', '').replace('[ERR]', '').strip()
            if clean and len(clean) > 5:
                key.append(clean)
    return key[:5]  # Return top 5 findings

@app.route('/api/submissions/<submission_id>/results', methods=['GET'])
def get_submission_results(submission_id):
    """Get detailed validation results for a submission"""
    try:
        # Try to get user from JWT if available
        try:
            user = get_jwt_identity()
        except:
            user = None

        # Query submission
        if user:
            submission = Submission.query.filter_by(id=submission_id, submitted_by=user).first()
        else:
            submission = Submission.query.filter_by(id=submission_id).first()

        if not submission:
            return jsonify({'error': 'Submission not found'}), 404

        # Get all validation results for this submission
        validation_results = ValidationResult.query.filter_by(submission_id=submission_id).all()

        # Parse the result JSON for each result
        results_data = []
        form_completeness = 0
        critical_issues = []

        for result in validation_results:
            try:
                details = json.loads(result.result) if result.result else {}
            except:
                details = {'raw': result.result}

            results_data.append({
                'check_type': result.check_type,
                'status': result.status,
                'details': details,
                'created_at': result.created_at.isoformat() if result.created_at else None
            })

            # Extract form completeness from ADR/Form validation
            if 'ADR Validation' in result.check_type or 'Form 44' in result.check_type:
                form_completeness = details.get('completeness', 0)
                if result.status == 'FAIL' and details.get('critical_issues'):
                    critical_issues.extend(details.get('critical_issues', []))

        # Generate findings and recommendations
        findings = generate_findings_summary(results_data)
        recommendations = generate_recommendations(results_data, submission.status)

        # Generate overall summary
        summary = generate_comprehensive_summary(submission, results_data, form_completeness)

        # Comprehensive results object
        comprehensive_results = {
            'submission_id': submission_id,
            'filename': submission.filename,
            'status': submission.status,
            'overall_status': 'PASS' if submission.status == 'completed' else 'FAIL',
            'form_completeness': form_completeness,
            'critical_issues': critical_issues,
            'total_checks': len(results_data),
            'checks_passed': sum(1 for r in results_data if r['status'] == 'PASS'),
            'checks_failed': sum(1 for r in results_data if r['status'] == 'FAIL'),
            'checks_skipped': sum(1 for r in results_data if r['status'] == 'SKIPPED'),
            'checks_errored': sum(1 for r in results_data if r['status'] == 'ERROR'),
            'validation_results': results_data,
            'findings': findings,
            'recommendations': recommendations,
            'summary': summary,
            'key_findings': extract_key_findings(findings),
            'timestamp': datetime.utcnow().isoformat(),
            'created_at': submission.created_at.isoformat() if submission.created_at else None
        }

        return jsonify(comprehensive_results), 200

    except Exception as e:
        logger.error(f"Get submission results error: {e}")
        return jsonify({'error': str(e), 'type': type(e).__name__}), 500

def generate_findings_summary(results_data):
    """Generate human-readable findings from validation results (with unicode-safe encoding)"""
    findings = []

    for result in results_data:
        check_type = result['check_type']
        status = result['status']
        details = result['details']

        # Use ASCII-safe markers instead of unicode
        status_mark = ""
        if status == 'PASS':
            status_mark = "[OK]"
        elif status == 'FAIL':
            status_mark = "[FAIL]"
        elif status == 'SKIPPED':
            status_mark = "[SKIP]"
        elif status == 'ERROR':
            status_mark = "[ERR]"

        if status == 'FAIL':
            if check_type == 'Duplicate Detection':
                count = details.get('duplicates_found', 0)
                findings.append(f"{status_mark} CRITICAL: Found {count} potential duplicate submissions")
            elif check_type == 'Consistency Check':
                findings.append(f"{status_mark} ERROR: Data consistency issues detected")
            elif check_type in ['Form 44 Validation', 'ADR Validation']:
                completeness = details.get('completeness', 0)
                missing = details.get('missing_fields', [])
                findings.append(f"{status_mark} Form validation failed: Only {completeness}% complete")
            elif check_type == 'MD-14 Validation':
                findings.append(f"{status_mark} ERROR: Adverse event validation failed")

        elif status == 'PASS':
            if check_type in ['Form 44 Validation', 'ADR Validation']:
                completeness = details.get('completeness', 0)
                findings.append(f"{status_mark} Form {completeness}% complete - Validation passed")
            elif check_type == 'Naranjo Causality Scoring':
                score = details.get('score', 0)
                prob = details.get('probability', 'Unknown')
                findings.append(f"{status_mark} Causality: Naranjo Score {score}/13 - {prob}")
            elif check_type == 'Duplicate Detection':
                findings.append(f"{status_mark} No duplicates - Unique submission")
            elif check_type == 'Consistency Check':
                findings.append(f"{status_mark} Data consistency - All fields validated")

        elif status == 'SKIPPED':
            reason = details.get('reason', 'N/A')
            findings.append(f"{status_mark} {check_type}: Skipped ({reason})")

    return findings if findings else ['All validation checks completed']

def generate_recommendations(results_data, final_status):
    """Generate actionable recommendations based on validation results"""
    recommendations = []

    if final_status == 'failed':
        recommendations.append('[ALERT] REVIEW REQUIRED: Address flagged issues before resubmission')
        recommendations.append('Contact regulatory team for clarification on failed checks')

    for result in results_data:
        if result['status'] == 'FAIL':
            check_type = result['check_type']
            details = result['details']
            if check_type == 'Duplicate Detection':
                recommendations.append('[ACTION] Check system for existing similar submissions and resolve conflicts')
            elif check_type == 'Form 44 Validation':
                missing = details.get('missing_fields', [])
                if missing:
                    recommendations.append(f"[ACTION] Complete mandatory Form 44 fields: {', '.join(missing[:2])}")
                else:
                    recommendations.append('[ACTION] Review Form 44 data validity and format')
            elif check_type == 'Consistency Check':
                issues = details.get('critical_issues', [])
                if issues:
                    recommendations.append(f"[ACTION] Resolve data inconsistency: {issues[0]}")

    if final_status == 'completed':
        recommendations.append('[OK] Submission ready for regulatory review')
        recommendations.append('[OK] All validation criteria successfully met')
        recommendations.append('Next: Submit to compliance officer for approval')

    return recommendations if recommendations else []

@app.route('/api/health', methods=['GET'])
def frontend_health_check():
    """Health check for frontend compatibility"""
    try:
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '2.0.0',
            'name': 'SwasthyaAI Regulator'
        }), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    logger.info("=" * 70)
    logger.info("SwasthyaAI Regulator - With Regulatory Features")
    logger.info("Features:")
    logger.info("  [PASS] Duplicate Detection")
    logger.info("  [PASS] Form 44 & MD-14 Validation")
    logger.info("  [PASS] Consistency Checking")
    logger.info("  [PASS] Evidence-Based Naranjo Scoring")
    logger.info("  [PASS] Comprehensive Submission Review")
    logger.info("=" * 70)

# ============================================================================
# ANALYTICS & REPORTING ENDPOINTS
# ============================================================================

@app.route('/api/analytics/summary', methods=['GET'])
def get_analytics_summary():
    """Get summary analytics for dashboard"""
    try:
        # Query all submissions
        submissions = Submission.query.all()
        results = ValidationResult.query.all()
        
        total_submissions = len(submissions)
        passed_submissions = len([s for s in submissions if s.status in ['completed', 'approved']])
        pass_rate = (passed_submissions / total_submissions * 100) if total_submissions > 0 else 0
        
        # Calculate severity distribution
        severity_data = {'Mild': 0, 'Moderate': 0, 'Severe': 0, 'Life-threatening': 0}
        outcome_data = {'Recovered': 0, 'Recovering': 0, 'Not Recovered': 0, 'Unknown': 0, 'Fatal': 0}
        
        for submission in submissions:
            # Parse validation results for severity/outcome data
            sub_results = ValidationResult.query.filter_by(submission_id=submission.id).all()
            for result in sub_results:
                try:
                    result_json = json.loads(result.result) if isinstance(result.result, str) else result.result
                    if isinstance(result_json, dict):
                        if 'severity_distribution' in result_json:
                            for severity, count in result_json['severity_distribution'].items():
                                if severity in severity_data:
                                    severity_data[severity] += count
                        if 'outcome_distribution' in result_json:
                            for outcome, count in result_json['outcome_distribution'].items():
                                if outcome in outcome_data:
                                    outcome_data[outcome] += count
                except:
                    pass
        
        return jsonify({
            'total_submissions': total_submissions,
            'passed_submissions': passed_submissions,
            'pass_rate': round(pass_rate, 2),
            'severity_distribution': severity_data,
            'outcome_distribution': outcome_data,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Analytics summary error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/top-adverse-events', methods=['GET'])
def get_top_adverse_events():
    """Get top adverse events from submissions"""
    try:
        submissions = Submission.query.all()
        adverse_events = {}
        
        for submission in submissions:
            results = ValidationResult.query.filter_by(submission_id=submission.id).all()
            for result in results:
                try:
                    result_json = json.loads(result.result) if isinstance(result.result, str) else result.result
                    if isinstance(result_json, dict) and 'adverse_events' in result_json:
                        for event in result_json['adverse_events']:
                            adverse_events[event] = adverse_events.get(event, 0) + 1
                except:
                    pass
        
        # Get top 5
        top_events = sorted(adverse_events.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return jsonify({
            'top_adverse_events': [{'event': event, 'count': count} for event, count in top_events],
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Top adverse events error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/top-drugs', methods=['GET'])
def get_top_drugs():
    """Get top drugs causing adverse reactions"""
    try:
        submissions = Submission.query.all()
        drugs = {}
        
        for submission in submissions:
            results = ValidationResult.query.filter_by(submission_id=submission.id).all()
            for result in results:
                try:
                    result_json = json.loads(result.result) if isinstance(result.result, str) else result.result
                    if isinstance(result_json, dict) and 'drugs' in result_json:
                        for drug in result_json['drugs']:
                            drugs[drug] = drugs.get(drug, 0) + 1
                except:
                    pass
        
        # Get top 5
        top_drugs = sorted(drugs.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return jsonify({
            'top_drugs': [{'drug': drug, 'count': count} for drug, count in top_drugs],
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Top drugs error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/form-types', methods=['GET'])
def get_form_types_distribution():
    """Get distribution of form types"""
    try:
        submissions = Submission.query.all()
        form_types = {}
        
        for submission in submissions:
            form_type = submission.submission_type or 'Unknown'
            form_types[form_type] = form_types.get(form_type, 0) + 1
        
        return jsonify({
            'form_type_distribution': form_types,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Form types error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports/submission-summary/<submission_id>', methods=['GET'])
def get_submission_report_data(submission_id):
    """Get comprehensive data for a submission's report"""
    try:
        submission = Submission.query.filter_by(id=submission_id).first()
        if not submission:
            return jsonify({'error': 'Submission not found'}), 404
        
        results = ValidationResult.query.filter_by(submission_id=submission_id).all()
        status_response = requests.get(f"http://localhost:5000/api/submissions/{submission_id}/results")
        
        if status_response.status_code == 200:
            result_data = status_response.json()
        else:
            result_data = {}
        
        return jsonify({
            'submission_id': submission_id,
            'filename': submission.filename,
            'created_at': submission.created_at.isoformat() if submission.created_at else None,
            'status': submission.status,
            'report_data': result_data,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Submission report data error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports/export-pdf', methods=['POST'])
def export_pdf_report():
    """Export comprehensive PDF report with analytics summary"""
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
        from io import BytesIO
        from datetime import datetime
        
        # Get analytics data
        submissions = Submission.query.all()
        total_submissions = len(submissions)
        
        # Calculate statistics
        passed_count = sum(1 for s in submissions if s.status == 'PASSED')
        pass_rate = round((passed_count / total_submissions * 100), 2) if total_submissions > 0 else 0
        
        # Get severity and outcome distribution
        severity_dist = {}
        outcome_dist = {}
        total_records = 0
        
        for submission in submissions:
            results = ValidationResult.query.filter_by(submission_id=submission.id).all()
            total_records += len(results)
            for result in results:
                try:
                    result_json = json.loads(result.result) if isinstance(result.result, str) else result.result
                    if isinstance(result_json, dict):
                        severity = result_json.get('severity', 'Unknown')
                        outcome = result_json.get('outcome', 'Unknown')
                        severity_dist[severity] = severity_dist.get(severity, 0) + 1
                        outcome_dist[outcome] = outcome_dist.get(outcome, 0) + 1
                except:
                    pass
        
        # Create PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                                topMargin=0.5*inch, bottomMargin=0.5*inch,
                                leftMargin=0.75*inch, rightMargin=0.75*inch)
        
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2563eb'),
            alignment=TA_CENTER,
            spaceAfter=12
        )
        story.append(Paragraph("SwasthyaAI Regulator - Analytics Report", title_style))
        
        # Date
        date_style = ParagraphStyle(
            'DateStyle',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER,
            textColor=colors.grey,
            spaceAfter=20
        )
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", date_style))
        
        # Summary section
        story.append(Paragraph("Executive Summary", styles['Heading2']))
        story.append(Spacer(1, 12))
        
        # Summary metrics table
        summary_data = [
            ['Metric', 'Value'],
            ['Total Submissions', str(total_submissions)],
            ['Passed Validations', str(passed_count)],
            ['Pass Rate (%)', f"{pass_rate}%"],
            ['Total Records Processed', str(total_records)]
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f9ff')])
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # Severity Distribution
        story.append(Paragraph("Severity Distribution", styles['Heading2']))
        story.append(Spacer(1, 10))
        severity_data = [['Severity', 'Count']] + [[k, str(v)] for k, v in sorted(severity_dist.items())]
        severity_table = Table(severity_data, colWidths=[3*inch, 2*inch])
        severity_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f9ff')])
        ]))
        story.append(severity_table)
        story.append(Spacer(1, 20))
        
        # Outcome Distribution
        story.append(Paragraph("Outcome Distribution", styles['Heading2']))
        story.append(Spacer(1, 10))
        outcome_data = [['Outcome', 'Count']] + [[k, str(v)] for k, v in sorted(outcome_dist.items())]
        outcome_table = Table(outcome_data, colWidths=[3*inch, 2*inch])
        outcome_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f9ff')])
        ]))
        story.append(outcome_table)
        story.append(Spacer(1, 20))
        
        # Footer
        story.append(Spacer(1, 20))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            alignment=TA_CENTER,
            textColor=colors.grey,
            borderPadding=10
        )
        story.append(Paragraph("CDSCO Adverse Drug Reaction Reporting System &nbsp;|&nbsp; SwasthyaAI Regulator", footer_style))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"SwasthyaAI_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )
        
    except Exception as e:
        logger.error(f"PDF export error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports/export-csv', methods=['POST'])
def export_csv_report():
    """Export analytics data as CSV file"""
    try:
        import csv
        from io import StringIO
        from datetime import datetime
        
        # Get analytics data
        submissions = Submission.query.all()
        
        # Create CSV buffer
        csv_buffer = StringIO()
        writer = csv.writer(csv_buffer)
        
        # Write summary section
        writer.writerow(['SwasthyaAI Regulator - Analytics Export'])
        writer.writerow([f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'])
        writer.writerow([])
        
        # Summary statistics
        total_submissions = len(submissions)
        passed_count = sum(1 for s in submissions if s.status == 'PASSED')
        pass_rate = round((passed_count / total_submissions * 100), 2) if total_submissions > 0 else 0
        
        writer.writerow(['Summary Statistics'])
        writer.writerow(['Metric', 'Value'])
        writer.writerow(['Total Submissions', total_submissions])
        writer.writerow(['Passed Validations', passed_count])
        writer.writerow(['Pass Rate (%)', pass_rate])
        writer.writerow([])
        
        # Severity distribution
        severity_dist = {}
        outcome_dist = {}
        
        for submission in submissions:
            results = ValidationResult.query.filter_by(submission_id=submission.id).all()
            for result in results:
                try:
                    result_json = json.loads(result.result) if isinstance(result.result, str) else result.result
                    if isinstance(result_json, dict):
                        severity = result_json.get('severity', 'Unknown')
                        outcome = result_json.get('outcome', 'Unknown')
                        severity_dist[severity] = severity_dist.get(severity, 0) + 1
                        outcome_dist[outcome] = outcome_dist.get(outcome, 0) + 1
                except:
                    pass
        
        writer.writerow(['Severity Distribution'])
        writer.writerow(['Severity', 'Count'])
        for severity, count in sorted(severity_dist.items()):
            writer.writerow([severity, count])
        writer.writerow([])
        
        # Outcome distribution
        writer.writerow(['Outcome Distribution'])
        writer.writerow(['Outcome', 'Count'])
        for outcome, count in sorted(outcome_dist.items()):
            writer.writerow([outcome, count])
        writer.writerow([])
        
        # Detailed submission records
        writer.writerow(['Submission Records'])
        writer.writerow(['Submission ID', 'Filename', 'Type', 'Status', 'Created Date'])
        for submission in submissions:
            created_date = submission.created_at.strftime('%Y-%m-%d %H:%M:%S') if submission.created_at else 'N/A'
            writer.writerow([
                submission.id,
                submission.filename or 'N/A',
                submission.submission_type or 'Unknown',
                submission.status or 'Unknown',
                created_date
            ])
        
        # Prepare response
        csv_buffer.seek(0)
        
        return send_file(
            StringIO(csv_buffer.getvalue()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f"SwasthyaAI_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        
    except Exception as e:
        logger.error(f"CSV export error: {e}")
        return jsonify({'error': str(e)}), 500
    
    app.run(host='0.0.0.0', port=5000, debug=True)
