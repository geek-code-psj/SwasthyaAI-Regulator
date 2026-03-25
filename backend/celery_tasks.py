"""
Celery tasks for background processing of regulatory documents
Handles asynchronous OCR, anonymization, summarization, and compliance validation
"""

from celery import Celery, Task
from datetime import datetime
import logging
from flask import current_app

from backend.models import db, Submission
from backend.modules.ocr_engine import OCREngine
from backend.modules.anonymizer import DPDPAnonymizer
from backend.modules.summarizer import SummarizationEngine
from backend.modules.compliance_validator import ComplianceValidator

logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery(__name__)


class FlaskTask(Task):
    """Make celery tasks work with Flask apps"""
    def __call__(self, *args, **kwargs):
        with current_app.app_context():
            return self.run(*args, **kwargs)


def init_celery(app):
    """Initialize Celery with Flask app"""
    celery_app.config_from_object(app.config)
    celery_app.Task = FlaskTask
    return celery_app


@celery_app.task(bind=True, max_retries=3)
def process_document(self, submission_id):
    """
    Process submitted document through complete pipeline
    
    Pipeline steps:
    1. OCR extraction from PDF/image
    2. Text anonymization (DPDP-compliant)
    3. Executive summary generation
    4. Multi-framework compliance validation
    
    Args:
        submission_id: UUID of submission to process
        
    Returns:
        Result dict with processing status and scores
    """
    try:
        logger.info(f"Starting document processing for submission: {submission_id}")
        
        submission = Submission.query.get(submission_id)
        if not submission:
            logger.error(f"Submission not found: {submission_id}")
            return {"error": "Submission not found", "submission_id": submission_id}
        
        # Initialize AI engines
        ocr_engine = OCREngine()
        anonymizer = DPDPAnonymizer()
        summarizer = SummarizationEngine()
        compliance_validator = ComplianceValidator()
        
        # Step 1: OCR Extraction
        logger.info(f"Step 1/4: OCR extraction for {submission_id}")
        submission.status = "extracting_text"
        db.session.commit()
        
        ocr_result = ocr_engine.extract_from_pdf(submission.file_path)
        if ocr_result.get("error"):
            raise Exception(f"OCR failed: {ocr_result['error']}")
        
        extracted_text = ocr_engine.clean_extracted_text(ocr_result["text"])
        submission.extracted_text = extracted_text
        submission.extracted_tables = ocr_result.get("tables", [])
        submission.detected_metadata = ocr_result.get("metadata", {})
        db.session.commit()
        
        # Step 2: Anonymization
        logger.info(f"Step 2/4: Anonymization for {submission_id}")
        submission.status = "anonymizing"
        db.session.commit()
        
        anonymized_text, token_vault = anonymizer.anonymize_text(extracted_text)
        anonymity_metrics = anonymizer.calculate_anonymity_metrics(anonymized_text)
        
        # Step 3: Summarization
        logger.info(f"Step 3/4: Summarization for {submission_id}")
        submission.status = "summarizing"
        db.session.commit()
        
        summary_result = summarizer.summarize(anonymized_text)
        key_findings = summarizer.extract_key_findings(anonymized_text) if summary_result.get("success") else {}
        
        # Step 4: Compliance Validation
        logger.info(f"Step 4/4: Compliance validation for {submission_id}")
        submission.status = "validating_compliance"
        db.session.commit()
        
        compliance_result = compliance_validator.validate_all(
            extracted_text,
            anonymized_text,
            anonymizer.anonymization_stats
        )
        
        # Update submission with results
        submission.status = "completed"
        submission.processing_end_date = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"Document processing completed for submission: {submission_id}")
        
        return {
            "submission_id": submission_id,
            "status": "completed",
            "ocr_stats": {
                "extracted_length": len(extracted_text),
                "tables_found": len(ocr_result.get("tables", []))
            },
            "anonymization_stats": anonymizer.anonymization_stats,
            "anonymity_metrics": anonymity_metrics,
            "summary_compression": summary_result.get("compression_ratio", 0) if summary_result.get("success") else 0,
            "compliance_score": compliance_result.get("overall_score", 0),
            "is_compliant": compliance_result.get("is_compliant", False)
        }
        
    except Exception as exc:
        logger.error(f"Error processing document {submission_id}: {str(exc)}")
        submission = Submission.query.get(submission_id)
        if submission:
            submission.status = "failed"
            submission.error_message = str(exc)
            submission.error_code = "PROCESSING_ERROR"
            db.session.commit()
        
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


@celery_app.task
def extract_text_only(submission_id):
    """Extract text from document (OCR only)"""
    try:
        submission = Submission.query.get(submission_id)
        if not submission:
            return {"error": "Submission not found"}
        
        ocr_engine = OCREngine()
        ocr_result = ocr_engine.extract_from_pdf(submission.file_path)
        
        if ocr_result.get("error"):
            return {"error": f"OCR failed: {ocr_result['error']}"}
        
        submission.extracted_text = ocr_engine.clean_extracted_text(ocr_result["text"])
        submission.extracted_tables = ocr_result.get("tables", [])
        db.session.commit()
        
        return {
            "submission_id": submission_id,
            "status": "success",
            "text_length": len(submission.extracted_text),
            "tables_found": len(submission.extracted_tables)
        }
    except Exception as e:
        logger.error(f"Error extracting text from {submission_id}: {str(e)}")
        return {"error": str(e)}


@celery_app.task
def anonymize_text_only(submission_id):
    """Anonymize extracted text (Anonymization only)"""
    try:
        submission = Submission.query.get(submission_id)
        if not submission or not submission.extracted_text:
            return {"error": "Submission or extracted text not found"}
        
        anonymizer = DPDPAnonymizer()
        anonymized_text, token_vault = anonymizer.anonymize_text(submission.extracted_text)
        anonymity_metrics = anonymizer.calculate_anonymity_metrics(anonymized_text)
        
        return {
            "submission_id": submission_id,
            "status": "success",
            "pii_statistics": anonymizer.anonymization_stats,
            "k_anonymity": anonymity_metrics.get("k_anonymity", 0),
            "l_diversity": anonymity_metrics.get("l_diversity", 0),
            "t_closeness": anonymity_metrics.get("t_closeness", 0)
        }
    except Exception as e:
        logger.error(f"Error anonymizing text for {submission_id}: {str(e)}")
        return {"error": str(e)}


@celery_app.task
def summarize_document(submission_id):
    """Generate summary of document"""
    try:
        submission = Submission.query.get(submission_id)
        if not submission or not submission.extracted_text:
            return {"error": "Submission or extracted text not found"}
        
        summarizer = SummarizationEngine()
        summary_result = summarizer.summarize(submission.extracted_text)
        
        if not summary_result.get("success"):
            return {"error": "Summarization failed"}
        
        key_findings = summarizer.extract_key_findings(submission.extracted_text)
        
        return {
            "submission_id": submission_id,
            "status": "success",
            "summary_length": summary_result.get("summary_length", 0),
            "compression_ratio": summary_result.get("compression_ratio", 0),
            "generation_time": summary_result.get("generation_time", 0),
            "key_findings_count": len(key_findings.get("key_findings", []))
        }
    except Exception as e:
        logger.error(f"Error summarizing document {submission_id}: {str(e)}")
        return {"error": str(e)}


@celery_app.task
def validate_compliance(submission_id):
    """Validate compliance of document"""
    try:
        submission = Submission.query.get(submission_id)
        if not submission:
            return {"error": "Submission not found"}
        
        validator = ComplianceValidator()
        result = validator.validate_all(
            submission.extracted_text or "",
            submission.anonymized_data.anonymized_text if submission.anonymized_data else "",
            submission.anonymized_data.pii_found if submission.anonymized_data else {}
        )
        
        return {
            "submission_id": submission_id,
            "status": "success",
            "compliance_score": result.get("overall_score", 0),
            "is_compliant": result.get("is_compliant", False),
            "framework_compliance": result.get("framework_compliance", {}),
            "issues_count": len(result.get("issues", [])),
            "recommendations_count": len(result.get("recommendations", []))
        }
    except Exception as e:
        logger.error(f"Error validating compliance for {submission_id}: {str(e)}")
        return {"error": str(e)}


@celery_app.task
def cleanup_old_submissions(days=90):
    """Clean up old submissions based on retention policy"""
    try:
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        old_submissions = Submission.query.filter(
            Submission.created_at < cutoff_date,
            Submission.status == "completed"
        ).all()
        
        count = len(old_submissions)
        
        for submission in old_submissions:
            # Delete associated files
            if submission.file_path and os.path.exists(submission.file_path):
                os.remove(submission.file_path)
            
            # Delete database records (cascading)
            db.session.delete(submission)
        
        db.session.commit()
        logger.info(f"Cleanup: Deleted {count} old submissions from before {cutoff_date}")
        
        return {"status": "success", "deleted_count": count}
    
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        return {"error": str(e)}


# Periodic tasks configuration
@celery_app.task
def periodic_cleanup():
    """Periodic task to clean up old data"""
    cleanup_old_submissions.delay(days=90)


@celery_app.task
def health_check():
    """Celery health check task"""
    logger.info("Celery health check - OK")
    return {"status": "healthy"}
