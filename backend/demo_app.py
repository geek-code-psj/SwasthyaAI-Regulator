"""
Minimal Flask Backend for SwasthyaAI Regulator Demo
This is a simplified version for demonstration purposes
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
import os
import logging
from datetime import datetime, timedelta
import uuid
import json
import sqlite3

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'demo-secret-key'
app.config['JWT_SECRET_KEY'] = 'demo-jwt-secret'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)

# Enable CORS
CORS(app)

# Initialize JWT
jwt = JWTManager(app)

# Simple in-memory database for demo
submissions_db = {}
anonymization_sample = {
    "summary": "This document contains healthcare information that has been processed through DPDP-compliant anonymization. All personally identifiable information has been removed or masked.",
    "pii_stats": {"names": 3, "addresses": 2, "phone_numbers": 1, "emails": 2},
    "anonymized_text": "Patient [PERSON_1] presented with symptoms consistent with Form 44 requirements. Address: [ADDRESS_1]. Contact: [EMAIL_1]. The medical records were reviewed and processed according to NDHM standards. Compliance validation completed successfully against DPDP Act 2023, NDHM Policy, ICMR Guidelines, and CDSCO Standards."
}

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "operational",
        "application": "SwasthyaAI Regulator Demo Backend",
        "version": "1.0.0"
    })

@app.route('/api/auth/token', methods=['POST'])
def get_token():
    """Get JWT token (demo - no credentials needed)"""
    try:
        token = create_access_token(identity='demo_user')
        return jsonify({
            "access_token": token,
            "token_type": "Bearer",
            "status": "success"
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/submissions/upload', methods=['POST'])
@jwt_required()
def upload_file():
    """Simulate file upload"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        submission_id = str(uuid.uuid4())
        submission_type = request.form.get('type', 'form_44')
        
        # Simulate submission storage
        submissions_db[submission_id] = {
            'id': submission_id,
            'filename': file.filename,
            'type': submission_type,
            'status': 'processing',
            'created_at': datetime.utcnow().isoformat(),
            'processing_progress': 0,
            'current_stage': 'extracting_text'
        }
        
        logger.info(f"Document uploaded: {submission_id}")
        
        return jsonify({
            "submission_id": submission_id,
            "status": "processing",
            "message": "Document uploaded successfully, processing started"
        }), 202
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/submissions/<submission_id>/status', methods=['GET'])
@jwt_required()
def get_status(submission_id):
    """Get submission processing status"""
    try:
        if submission_id not in submissions_db:
            return jsonify({"error": "Submission not found"}), 404
        
        sub = submissions_db[submission_id]
        
        # Simulate processing progress
        if sub['status'] == 'processing':
            progress = sub.get('processing_progress', 0)
            if progress < 100:
                progress += 25
                submissions_db[submission_id]['processing_progress'] = progress
                
                # Simulate stage progression
                stages = ['extracting_text', 'anonymizing', 'summarizing', 'validating_compliance']
                stage_index = int(progress / 25) - 1
                if stage_index < len(stages):
                    submissions_db[submission_id]['current_stage'] = stages[stage_index]
            else:
                submissions_db[submission_id]['status'] = 'completed'
        
        return jsonify({
            "submission_id": submission_id,
            "status": submissions_db[submission_id]['status'],
            "created_at": submissions_db[submission_id]['created_at'],
            "processing_duration": sub.get('processing_progress', 0) / 25 * 8,
            "current_stage": submissions_db[submission_id].get('current_stage', 'completed')
        }), 200
        
    except Exception as e:
        logger.error(f"Status check error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/submissions/<submission_id>/results', methods=['GET'])
@jwt_required()
def get_results(submission_id):
    """Get processing results"""
    try:
        if submission_id not in submissions_db:
            return jsonify({"error": "Submission not found"}), 404
        
        sub = submissions_db[submission_id]
        
        return jsonify({
            "submission_id": submission_id,
            "status": sub['status'],
            "filename": sub['filename'],
            "summary": anonymization_sample['summary'],
            "pii_stats": anonymization_sample['pii_stats'],
            "anonymized_text": anonymization_sample['anonymized_text'],
            "key_findings": [
                "All personally identifiable information successfully anonymized",
                "Document complies with DPDP Act 2023 requirements",
                "Health data formatted according to NDHM standards",
                "Research ethics compliance verified per ICMR guidelines",
                "Pharmaceutical data meets CDSCO documentation standards"
            ],
            "compliance_status": {
                "is_compliant": True,
                "score": 90,
                "frameworks": {
                    "DPDP": {"compliant": True, "score": 94},
                    "NDHM": {"compliant": True, "score": 89},
                    "ICMR": {"compliant": True, "score": 92},
                    "CDSCO": {"compliant": True, "score": 87}
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Results retrieval error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/submissions', methods=['GET'])
@jwt_required()
def list_submissions():
    """List all submissions"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        all_subs = list(submissions_db.values())
        
        return jsonify({
            "submissions": all_subs[(page-1)*per_page:page*per_page],
            "total": len(all_subs),
            "page": page,
            "per_page": per_page
        }), 200
        
    except Exception as e:
        logger.error(f"List submissions error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 SwasthyaAI Regulator - Backend API (Demo Mode)")
    print("="*60)
    print("✅ API running on http://localhost:5000")
    print("📋 Documentation: http://localhost:5000/api")
    print("🔒 JWT authentication enabled")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
