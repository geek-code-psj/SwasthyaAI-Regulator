from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from werkzeug.utils import secure_filename
import os
import logging
from datetime import datetime, timedelta
import uuid

from config import get_config
from models import db, init_db, Submission, AnonymizedData, Summary, ComplianceResult, AuditLog
from modules.ocr_engine import OCREngine
from modules.anonymizer import DPDPAnonymizer
from modules.summarizer import SummarizationEngine
from modules.compliance_validator import ComplianceValidator


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app(config=None):
    """Flask application factory"""
    app = Flask(__name__)
    
    # Load configuration
    if config is None:
        config = get_config()
    app.config.from_object(config)
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)
    jwt = JWTManager(app)
    
    # Create upload folder
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["ANONYMIZATION_VAULT_PATH"], exist_ok=True)
    
    # Initialize database
    with app.app_context():
        init_db(app)
    
    # Initialize AI engines
    ocr_engine = OCREngine(language=app.config.get("OCR_LANGUAGE", "eng"))
    anonymizer = DPDPAnonymizer(vault_path=app.config.get("ANONYMIZATION_VAULT_PATH"))
    summarizer = SummarizationEngine(model_name=app.config.get("SUMMARIZATION_MODEL"))
    compliance_validator = ComplianceValidator()
    
    # ==================== HEALTH CHECK ====================
    @app.route("/api/health", methods=["GET"])
    def health_check():
        """Health check endpoint"""
        return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()}), 200
    
    # ==================== AUTHENTICATION ====================
    @app.route("/api/auth/token", methods=["POST"])
    def get_token():
        """Get JWT token (simplified, no real auth yet)"""
        try:
            # In production, validate username/password
            token = create_access_token(
                identity="test_user",
                expires_delta=timedelta(hours=24)
            )
            return jsonify({"access_token": token}), 200
        except Exception as e:
            logger.error(f"Token generation error: {str(e)}")
            return jsonify({"error": str(e)}), 500
    
    # ==================== SUBMISSION ENDPOINTS ====================
    @app.route("/api/submissions/upload", methods=["POST"])
    @jwt_required()
    def upload_document():
        """Upload and process document"""
        try:
            # Validate file presence
            if "file" not in request.files:
                return jsonify({"error": "No file provided"}), 400
            
            file = request.files["file"]
            if file.filename == "":
                return jsonify({"error": "No file selected"}), 400
            
            # Validate file type
            if not allowed_file(file.filename):
                return jsonify({"error": "File type not allowed"}), 400
            
            # Generate submission ID
            submission_id = str(uuid.uuid4())
            
            # Save uploaded file
            filename = secure_filename(f"{submission_id}_{file.filename}")
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(file_path)
            
            # Create submission record
            submission = Submission(
                id=submission_id,
                filename=filename,
                original_filename=file.filename,
                submission_type=request.form.get("type", "form_44"),
                file_path=file_path,
                file_size=os.path.getsize(file_path),
                status="processing"
            )
            db.session.add(submission)
            db.session.commit()
            
            # Log audit
            log_audit(submission_id, "upload", "CREATE", "success")
            
            logger.info(f"Document uploaded: {submission_id}")
            
            return jsonify({
                "submission_id": submission_id,
                "status": "processing",
                "message": "Document uploaded successfully, processing started"
            }), 202
            
        except Exception as e:
            logger.error(f"Upload error: {str(e)}")
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/submissions/<submission_id>/status", methods=["GET"])
    @jwt_required()
    def get_submission_status(submission_id):
        """Get submission processing status"""
        try:
            submission = Submission.query.get(submission_id)
            if not submission:
                return jsonify({"error": "Submission not found"}), 404
            
            return jsonify({
                "submission_id": submission_id,
                "status": submission.status,
                "created_at": submission.created_at.isoformat(),
                "processing_duration": submission.processing_duration,
                "error_message": submission.error_message
            }), 200
            
        except Exception as e:
            logger.error(f"Status check error: {str(e)}")
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/submissions/<submission_id>/process", methods=["POST"])
    @jwt_required()
    def process_submission(submission_id):
        """Process submission (OCR + Anonymization + Summarization + Compliance)"""
        try:
            submission = Submission.query.get(submission_id)
            if not submission:
                return jsonify({"error": "Submission not found"}), 404
            
            start_time = datetime.utcnow()
            
            # Step 1: OCR extraction
            logger.info(f"Processing submission {submission_id} - OCR extraction")
            ocr_result = ocr_engine.extract_from_pdf(submission.file_path)
            
            if ocr_result.get("error"):
                submission.status = "failed"
                submission.error_message = ocr_result["error"]
                submission.error_code = "OCR_ERROR"
                db.session.commit()
                return jsonify({"error": f"OCR failed: {ocr_result['error']}"}), 500
            
            extracted_text = ocr_engine.clean_extracted_text(ocr_result["text"])
            submission.extracted_text = extracted_text
            submission.extracted_tables = ocr_result.get("tables", [])
            submission.detected_metadata = ocr_result.get("metadata", {})
            
            # Step 2: Anonymization
            logger.info(f"Processing submission {submission_id} - Anonymization")
            anonymized_text, token_vault = anonymizer.anonymize_text(extracted_text)
            anonymity_metrics = anonymizer.calculate_anonymity_metrics(anonymized_text)
            
            # Save anonymized data
            anon_data = AnonymizedData(
                submission_id=submission_id,
                original_text=extracted_text,
                anonymized_text=anonymized_text,
                token_vault=token_vault,
                pii_found=anonymizer.anonymization_stats,
                k_anonymity_score=anonymity_metrics.get("k_anonymity", 0),
                l_diversity_score=anonymity_metrics.get("l_diversity", 0),
                t_closeness_score=anonymity_metrics.get("t_closeness", 0)
            )
            db.session.add(anon_data)
            
            # Step 3: Summarization
            logger.info(f"Processing submission {submission_id} - Summarization")
            summary_result = summarizer.summarize(anonymized_text)
            
            if summary_result.get("success"):
                key_findings = summarizer.extract_key_findings(anonymized_text)
                summary_obj = Summary(
                    submission_id=submission_id,
                    abstract_summary=summary_result["summary"],
                    key_findings=key_findings.get("key_findings", []),
                    original_length=summary_result["original_length"],
                    summary_length=summary_result["summary_length"],
                    compression_ratio=summary_result["compression_ratio"],
                    generation_time=summary_result["generation_time"],
                    model_used=summarizer.model_name
                )
                db.session.add(summary_obj)
            
            # Step 4: Compliance Validation
            logger.info(f"Processing submission {submission_id} - Compliance Validation")
            compliance_result = compliance_validator.validate_all(
                extracted_text,
                anonymized_text,
                anonymizer.anonymization_stats
            )
            
            compliance_obj = ComplianceResult(
                submission_id=submission_id,
                is_compliant=compliance_result["is_compliant"],
                compliance_score=compliance_result["overall_score"],
                checks_results=compliance_result["check_results"],
                dpdp_act_2023_compliant=compliance_result["framework_compliance"].get("dpdp_act_2023", False),
                ndhm_policy_compliant=compliance_result["framework_compliance"].get("ndhm_policy", False),
                icmr_guidelines_compliant=compliance_result["framework_compliance"].get("icmr_guidelines", False),
                cdsco_standards_compliant=compliance_result["framework_compliance"].get("cdsco_standards", False),
                issues=compliance_result.get("issues", []),
                recommendations=compliance_result.get("recommendations", [])
            )
            db.session.add(compliance_obj)
            
            # Update submission status
            end_time = datetime.utcnow()
            submission.status = "completed"
            submission.processing_start_date = start_time
            submission.processing_end_date = end_time
            submission.processing_duration = (end_time - start_time).total_seconds()
            
            db.session.commit()
            
            # Log audit
            log_audit(submission_id, "process", "CREATE", "success")
            
            logger.info(f"Submission {submission_id} processed successfully in {submission.processing_duration:.2f}s")
            
            return jsonify({
                "submission_id": submission_id,
                "status": "completed",
                "processing_duration": submission.processing_duration,
                "compliance_score": compliance_result["overall_score"],
                "is_compliant": compliance_result["is_compliant"]
            }), 200
            
        except Exception as e:
            logger.error(f"Processing error: {str(e)}")
            submission.status = "failed"
            submission.error_message = str(e)
            submission.error_code = "PROCESSING_ERROR"
            db.session.commit()
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/submissions/<submission_id>/results", methods=["GET"])
    @jwt_required()
    def get_results(submission_id):
        """Get processing results"""
        try:
            submission = Submission.query.get(submission_id)
            if not submission:
                return jsonify({"error": "Submission not found"}), 404
            
            results = {
                "submission_id": submission_id,
                "status": submission.status,
                "extracted_metadata": submission.detected_metadata,
                "anonymized_data": None,
                "summary": None,
                "compliance": None
            }
            
            if submission.anonymized_data:
                results["anonymized_data"] = {
                    "anonymized_text": submission.anonymized_data.anonymized_text[:500] + "...",
                    "pii_stats": submission.anonymized_data.pii_found,
                    "k_anonymity": submission.anonymized_data.k_anonymity_score
                }
            
            if submission.summary:
                results["summary"] = {
                    "abstract": submission.summary.abstract_summary,
                    "key_findings": submission.summary.key_findings,
                    "compression_ratio": submission.summary.compression_ratio
                }
            
            if submission.compliance_result:
                results["compliance"] = {
                    "is_compliant": submission.compliance_result.is_compliant,
                    "score": submission.compliance_result.compliance_score,
                    "frameworks": {
                        "dpdp": submission.compliance_result.dpdp_act_2023_compliant,
                        "ndhm": submission.compliance_result.ndhm_policy_compliant,
                        "icmr": submission.compliance_result.icmr_guidelines_compliant,
                        "cdsco": submission.compliance_result.cdsco_standards_compliant
                    },
                    "issues": submission.compliance_result.issues,
                    "recommendations": submission.compliance_result.recommendations
                }
            
            return jsonify(results), 200
            
        except Exception as e:
            logger.error(f"Results retrieval error: {str(e)}")
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/submissions", methods=["GET"])
    @jwt_required()
    def list_submissions():
        """List all submissions"""
        try:
            page = request.args.get("page", 1, type=int)
            per_page = request.args.get("per_page", 10, type=int)
            
            submissions = Submission.query.paginate(page=page, per_page=per_page)
            
            return jsonify({
                "submissions": [
                    {
                        "id": s.id,
                        "filename": s.original_filename,
                        "status": s.status,
                        "created_at": s.created_at.isoformat(),
                        "processing_duration": s.processing_duration
                    } for s in submissions.items
                ],
                "total": submissions.total,
                "pages": submissions.pages,
                "current_page": page
            }), 200
            
        except Exception as e:
            logger.error(f"List error: {str(e)}")
            return jsonify({"error": str(e)}), 500
    
    # ==================== UTILITY FUNCTIONS ====================
    def allowed_file(filename):
        """Check if file type is allowed"""
        return "." in filename and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]
    
    def log_audit(submission_id, action, action_type, status):
        """Log audit trail"""
        try:
            audit = AuditLog(
                submission_id=submission_id,
                action=action,
                action_type=action_type,
                status=status,
                ip_address=request.remote_addr
            )
            db.session.add(audit)
            db.session.commit()
        except Exception as e:
            logger.warning(f"Audit logging failed: {str(e)}")
    
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)
