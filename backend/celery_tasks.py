"""
Celery tasks for background processing of regulatory documents
Handles asynchronous 4-phase pipeline: Extract → Anonymize → Summarize → Validate
"""

from celery import Celery, Task, group, chain
from datetime import datetime
import logging
import os
import json
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


# ============================================================================
# PHASE 1: OCR EXTRACTION TASK
# ============================================================================

@celery_app.task(bind=True, name='celery_tasks.task_extract_document')
def task_extract_document(self, submission_id):
    """
    PHASE 1: Extract text from document
    
    Args:
        submission_id: Unique submission identifier
        
    Returns:
        Dict with extraction result
    """
    try:
        logger.info(f"[EXTRACT] Starting extraction for {submission_id}")
        
        submission = Submission.query.get(submission_id)
        if not submission:
            logger.error(f"[EXTRACT] Submission not found: {submission_id}")
            return {'success': False, 'error': 'Submission not found'}
        
        # Update status
        submission.status = 'extracting_text'
        db.session.commit()
        
        # Extract using OCR engine
        ocr_engine = OCREngine()
        ocr_result = ocr_engine.extract_from_pdf(submission.file_path)
        
        if ocr_result.get('error'):
            logger.error(f"[EXTRACT] OCR failed for {submission_id}: {ocr_result['error']}")
            return {'success': False, 'error': ocr_result['error']}
        
        extracted_text = ocr_engine.clean_extracted_text(ocr_result['text'])
        
        # Store extraction results
        submission.extracted_text = extracted_text
        submission.extraction_quality = ocr_result.get('quality', 'unknown')
        submission.extracted_tables = ocr_result.get('tables', [])
        submission.detected_metadata = ocr_result.get('metadata', {})
        db.session.commit()
        
        logger.info(f"[EXTRACT] ✓ Success for {submission_id}: {len(extracted_text)} chars")
        
        return {
            'success': True,
            'text': extracted_text,
            'quality': ocr_result.get('quality', 'unknown'),
            'tables_found': len(ocr_result.get('tables', [])),
            'extraction_time': ocr_result.get('extraction_time', 0)
        }
    
    except Exception as e:
        logger.error(f"[EXTRACT] Exception for {submission_id}: {str(e)}")
        return {'success': False, 'error': f"Extraction error: {str(e)}"}


# ============================================================================
# PHASE 2: ANONYMIZATION TASK
# ============================================================================

@celery_app.task(bind=True, name='celery_tasks.task_anonymize_text')
def task_anonymize_text(self, submission_id, extracted_text=None):
    """
    PHASE 2: Anonymize PII from text
    
    Args:
        submission_id: Unique submission identifier
        extracted_text: Text to anonymize (if None, use stored extraction)
        
    Returns:
        Dict with anonymization result
    """
    try:
        logger.info(f"[ANONYMIZE] Starting for {submission_id}")
        
        submission = Submission.query.get(submission_id)
        if not submission:
            logger.error(f"[ANONYMIZE] Submission not found: {submission_id}")
            return {'success': False, 'error': 'Submission not found'}
        
        # Use provided text or stored extraction
        text_to_anonymize = extracted_text or submission.extracted_text
        if not text_to_anonymize:
            logger.error(f"[ANONYMIZE] No text to anonymize for {submission_id}")
            return {'success': False, 'error': 'No extracted text found'}
        
        # Update status
        submission.status = 'anonymizing'
        db.session.commit()
        
        # Anonymize text
        anonymizer = DPDPAnonymizer()
        anonymized_text, token_vault = anonymizer.anonymize_text(text_to_anonymize)
        anonymity_metrics = anonymizer.calculate_anonymity_metrics(anonymized_text)
        
        # Store anonymization results
        submission.anonymized_text = anonymized_text
        submission.pii_found = anonymizer.anonymization_stats
        submission.k_anonymity_score = anonymity_metrics.get('k_anonymity', 0)
        submission.l_diversity_score = anonymity_metrics.get('l_diversity', 0)
        submission.t_closeness_score = anonymity_metrics.get('t_closeness', 0)
        db.session.commit()
        
        pii_count = len(anonymizer.anonymization_stats)
        logger.info(f"[ANONYMIZE] ✓ Complete for {submission_id}: {pii_count} PII types detected")
        
        return {
            'success': True,
            'anonymized_text': anonymized_text,
            'pii_stats': anonymizer.anonymization_stats,
            'total_replacements': sum(anonymizer.anonymization_stats.values()) if anonymizer.anonymization_stats else 0,
            'k_anonymity': anonymity_metrics.get('k_anonymity', 0),
            'l_diversity': anonymity_metrics.get('l_diversity', 0),
            't_closeness': anonymity_metrics.get('t_closeness', 0)
        }
    
    except Exception as e:
        logger.error(f"[ANONYMIZE] Exception for {submission_id}: {str(e)}")
        return {'success': False, 'error': f"Anonymization error: {str(e)}"}


# ============================================================================
# PHASE 3: SUMMARIZATION TASK
# ============================================================================

@celery_app.task(bind=True, name='celery_tasks.task_summarize_text')
def task_summarize_text(self, submission_id, extracted_text=None):
    """
    PHASE 3: Generate summary from text
    
    Args:
        submission_id: Unique submission identifier
        extracted_text: Text to summarize (if None, use stored extraction)
        
    Returns:
        Dict with summary and findings
    """
    try:
        logger.info(f"[SUMMARIZE] Starting for {submission_id}")
        
        submission = Submission.query.get(submission_id)
        if not submission:
            logger.error(f"[SUMMARIZE] Submission not found: {submission_id}")
            return {'success': False, 'error': 'Submission not found'}
        
        # Use provided text or stored extraction
        text_to_summarize = extracted_text or submission.extracted_text
        if not text_to_summarize:
            logger.error(f"[SUMMARIZE] No text to summarize for {submission_id}")
            return {'success': False, 'error': 'No extracted text found'}
        
        # Update status
        submission.status = 'summarizing'
        db.session.commit()
        
        # Summarize text
        summarizer = SummarizationEngine()
        summary_result = summarizer.summarize(text_to_summarize)
        
        if not summary_result.get('success'):
            logger.warning(f"[SUMMARIZE] Summarization failed for {submission_id}")
            return {
                'success': False,
                'error': 'Summarization failed',
                'key_findings': []
            }
        
        key_findings = summarizer.extract_key_findings(text_to_summarize)
        
        # Store summary results
        submission.summary = summary_result.get('summary', '')
        submission.key_findings = key_findings.get('key_findings', [])
        submission.compression_ratio = summary_result.get('compression_ratio', 0)
        db.session.commit()
        
        logger.info(f"[SUMMARIZE] ✓ Complete for {submission_id}: {len(submission.key_findings)} findings")
        
        return {
            'success': True,
            'summary': summary_result.get('summary', ''),
            'compression_ratio': summary_result.get('compression_ratio', 0),
            'generation_time': summary_result.get('generation_time', 0),
            'key_findings': key_findings.get('key_findings', [])
        }
    
    except Exception as e:
        logger.error(f"[SUMMARIZE] Exception for {submission_id}: {str(e)}")
        return {'success': False, 'error': f"Summarization error: {str(e)}", 'key_findings': []}


# ============================================================================
# PHASE 4: COMPLIANCE VALIDATION TASK
# ============================================================================

@celery_app.task(bind=True, name='celery_tasks.task_validate_compliance')
def task_validate_compliance(self, submission_id):
    """
    PHASE 4: Validate compliance with 4 frameworks
    
    Args:
        submission_id: Unique submission identifier
        
    Returns:
        Dict with compliance result
    """
    try:
        logger.info(f"[COMPLIANCE] Starting for {submission_id}")
        
        submission = Submission.query.get(submission_id)
        if not submission:
            logger.error(f"[COMPLIANCE] Submission not found: {submission_id}")
            return {'success': False, 'error': 'Submission not found'}
        
        if not submission.extracted_text or not submission.anonymized_text:
            logger.error(f"[COMPLIANCE] Missing required data for {submission_id}")
            return {'success': False, 'error': 'Missing extraction or anonymization data'}
        
        # Update status
        submission.status = 'validating_compliance'
        db.session.commit()
        
        # Validate compliance
        validator = ComplianceValidator()
        compliance_result = validator.validate_all(
            submission.extracted_text,
            submission.anonymized_text,
            submission.pii_found or {}
        )
        
        # Store compliance results
        submission.compliance_score = compliance_result.get('overall_score', 0)
        submission.is_compliant = compliance_result.get('is_compliant', False)
        submission.compliance_details = compliance_result
        db.session.commit()
        
        logger.info(f"[COMPLIANCE] ✓ Complete for {submission_id}: Score={compliance_result.get('overall_score', 0)}")
        
        return {
            'success': True,
            'compliance_score': compliance_result.get('overall_score', 0),
            'is_compliant': compliance_result.get('is_compliant', False),
            'compliance_details': compliance_result
        }
    
    except Exception as e:
        logger.error(f"[COMPLIANCE] Exception for {submission_id}: {str(e)}")
        return {'success': False, 'error': f"Compliance validation error: {str(e)}"}


# ============================================================================
# ORCHESTRATION: COMPLETE PIPELINE
# ============================================================================

@celery_app.task(bind=True, max_retries=3, name='celery_tasks.process_document')
def process_document(self, submission_id):
    """
    ORCHESTRATION: Process submitted document through complete 4-phase pipeline
    
    Pipeline:
    1. PHASE 1: Extract text from PDF/image
    2. PHASE 2: Anonymize PII (DPDP-compliant)
    3. PHASE 3: Generate summary and findings
    4. PHASE 4: Validate compliance (4 frameworks)
    
    Args:
        submission_id: UUID of submission to process
        
    Returns:
        Result dict with processing status and all phase results
    """
    try:
        logger.info(f"[PIPELINE] Starting complete processing for {submission_id}")
        
        submission = Submission.query.get(submission_id)
        if not submission:
            logger.error(f"[PIPELINE] Submission not found: {submission_id}")
            return {
                'success': False,
                'error': 'Submission not found',
                'submission_id': submission_id
            }
        
        # ========== PHASE 1: EXTRACT ==========
        logger.info(f"[PIPELINE] Phase 1/4: Extracting text...")
        extract_result = task_extract_document(submission_id)
        
        if not extract_result.get('success'):
            logger.error(f"[PIPELINE] Extraction failed for {submission_id}")
            submission.status = 'failed'
            submission.error_message = extract_result.get('error', 'Extraction failed')
            submission.error_stage = 'extraction'
            db.session.commit()
            return {
                'success': False,
                'stage': 'extraction',
                'error': extract_result.get('error', 'Extraction failed'),
                'submission_id': submission_id
            }
        
        extracted_text = extract_result['text']
        logger.info(f"[PIPELINE] ✓ Phase 1 complete: {len(extracted_text)} chars extracted")
        
        # ========== PHASE 2: ANONYMIZE ==========
        logger.info(f"[PIPELINE] Phase 2/4: Anonymizing...")
        anon_result = task_anonymize_text(submission_id, extracted_text)
        
        if not anon_result.get('success'):
            logger.error(f"[PIPELINE] Anonymization failed for {submission_id}")
            submission.status = 'failed'
            submission.error_message = anon_result.get('error', 'Anonymization failed')
            submission.error_stage = 'anonymization'
            db.session.commit()
            return {
                'success': False,
                'stage': 'anonymization',
                'error': anon_result.get('error', 'Anonymization failed'),
                'submission_id': submission_id
            }
        
        anonymized_text = anon_result['anonymized_text']
        logger.info(f"[PIPELINE] ✓ Phase 2 complete: {anon_result.get('total_replacements', 0)} replacements")
        
        # ========== PHASE 3: SUMMARIZE ==========
        logger.info(f"[PIPELINE] Phase 3/4: Summarizing...")
        summary_result = task_summarize_text(submission_id, extracted_text)
        
        if not summary_result.get('success'):
            logger.warning(f"[PIPELINE] Summarization failed for {submission_id}, continuing...")
            summary_result = {
                'success': True,
                'summary': 'Summary generation unavailable',
                'key_findings': [],
                'compression_ratio': 0
            }
        
        logger.info(f"[PIPELINE] ✓ Phase 3 complete: {len(summary_result.get('key_findings', []))} findings")
        
        # ========== PHASE 4: VALIDATE ==========
        logger.info(f"[PIPELINE] Phase 4/4: Validating compliance...")
        compliance_result = task_validate_compliance(submission_id)
        
        if not compliance_result.get('success'):
            logger.warning(f"[PIPELINE] Compliance validation failed for {submission_id}")
            compliance_result = {
                'success': True,
                'compliance_score': 0,
                'is_compliant': False,
                'compliance_details': {}
            }
        
        logger.info(f"[PIPELINE] ✓ Phase 4 complete: Score={compliance_result.get('compliance_score', 0)}")
        
        # ========== FINALIZE ==========
        submission.status = 'completed'
        submission.processing_end_date = datetime.utcnow()
        submission.error_message = None
        submission.error_stage = None
        db.session.commit()
        
        logger.info(f"[PIPELINE] ✓✓✓ Complete for {submission_id}")
        
        return {
            'success': True,
            'submission_id': submission_id,
            'status': 'completed',
            'extraction': {
                'quality': extract_result.get('quality'),
                'tables_found': extract_result.get('tables_found'),
                'extraction_time': extract_result.get('extraction_time')
            },
            'anonymization': {
                'pii_types': list(anon_result.get('pii_stats', {}).keys()),
                'total_replacements': anon_result.get('total_replacements'),
                'k_anonymity': anon_result.get('k_anonymity'),
                'l_diversity': anon_result.get('l_diversity'),
                't_closeness': anon_result.get('t_closeness')
            },
            'summarization': {
                'compression_ratio': summary_result.get('compression_ratio'),
                'findings_count': len(summary_result.get('key_findings', [])),
                'generation_time': summary_result.get('generation_time')
            },
            'compliance': {
                'score': compliance_result.get('compliance_score'),
                'is_compliant': compliance_result.get('is_compliant')
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"[PIPELINE] Fatal exception for {submission_id}: {str(exc)}")
        submission = Submission.query.get(submission_id)
        if submission:
            submission.status = 'failed'
            submission.error_message = str(exc)
            submission.error_stage = 'pipeline'
            db.session.commit()
        
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)

# ============================================================================
# UTILITY TASKS FOR PARTIAL PROCESSING
# ============================================================================

@celery_app.task
def extract_text_only(submission_id):
    """Extract text from document (Phase 1 only)"""
    return task_extract_document(submission_id)


@celery_app.task
def anonymize_text_only(submission_id):
    """Anonymize extracted text (Phase 2 only)"""
    return task_anonymize_text(submission_id)


@celery_app.task
def summarize_document(submission_id):
    """Generate summary of document (Phase 3 only)"""
    return task_summarize_text(submission_id)


@celery_app.task
def validate_compliance(submission_id):
    """Validate compliance of document (Phase 4 only)"""
    return task_validate_compliance(submission_id)



# ============================================================================
# MAINTENANCE TASKS
# ============================================================================

@celery_app.task
def cleanup_old_submissions(days=90):
    """Clean up old submissions based on retention policy"""
    try:
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        old_submissions = Submission.query.filter(
            Submission.created_at < cutoff_date,
            Submission.status == "completed"
        ).all()
        
        count = len(old_submissions)
        
        for submission in old_submissions:
            # Delete associated files
            if submission.file_path and os.path.exists(submission.file_path):
                try:
                    os.remove(submission.file_path)
                except Exception as e:
                    logger.warning(f"Could not delete file {submission.file_path}: {str(e)}")
            
            # Delete database records (cascading)
            db.session.delete(submission)
        
        db.session.commit()
        logger.info(f"[CLEANUP] Deleted {count} old submissions from before {cutoff_date}")
        
        return {"status": "success", "deleted_count": count}
    
    except Exception as e:
        logger.error(f"[CLEANUP] Error during cleanup: {str(e)}")
        return {"error": str(e)}


# ============================================================================
# PERIODIC TASKS
# ============================================================================

@celery_app.task
def periodic_cleanup():
    """Periodic task to clean up old data (runs daily)"""
    logger.info("[PERIODIC] Running cleanup task")
    cleanup_old_submissions.delay(days=90)


@celery_app.task
def health_check():
    """Celery health check task (runs hourly)"""
    logger.info("[HEALTH] Celery health check - OK")
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
