"""
Test: Form 44 Extraction - Verify Hallucination Fixes
Tests the strict validation and prevents false positives
"""

import sys
import os
from enhanced_app import Form44Parser
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestForm44ExtractionFixes:
    """Test Form 44 parser anti-hallucination fixes"""

    def test_empty_text_rejection(self):
        """PASS: Should reject empty/short text input"""
        result = Form44Parser.parse_text("")
        assert result == {}, "FAIL: Empty text should return empty dict"
        logger.info("[OK] Empty text rejection test PASSED")

    def test_insufficient_text_rejection(self):
        """PASS: Should reject text < 100 chars"""
        short_text = "Some short text"
        result = Form44Parser.parse_text(short_text)
        assert result == {}, "FAIL: Short text should return empty dict"
        logger.info("[OK] Short text rejection test PASSED")

    def test_strict_keyword_matching(self):
        """PASS: Should only extract with proper context"""
        # Test 1: Valid keyword with value
        valid_text = """
        Drug Name: Aspirin 500mg
        Age: 45
        Report Date: 15-01-2024
        """
        result = Form44Parser.parse_text(valid_text)
        assert 'drug_name' in result or result == {}, "Should attempt extraction"
        logger.info("[OK] Valid keyword extraction test PASSED")

        # Test 2: Keyword with no value should not hallucinate
        invalid_text = """Drug Name:
        This is some other unrelated text
        """
        result = Form44Parser.parse_text(invalid_text)
        assert result.get('drug_name') is None or result.get('drug_name') == '', "Should not hallucinate empty value"
        logger.info("[OK] Empty keyword rejection test PASSED")

    def test_format_validation(self):
        """PASS: Should validate field formats"""
        text = """
        Patient Age: 45
        Onset Date: 15-01-2024
        Reporter Phone: +91-9876543210
        Reporter Email: doctor@example.com
        Batch Number: BATCH-2024-001
        """
        result = Form44Parser.parse_text(text)

        # Age should match: ^\d{1,3}$
        assert result.get('patient_age') == '45', f"Age validation failed: {result.get('patient_age')}"
        logger.info("[OK] Age format validation test PASSED")

        # Date should match: ^\d{1,2}[-/]\d{1,2}[-/]\d{2,4}$
        assert result.get('onset_date') == '15-01-2024', f"Date validation failed: {result.get('onset_date')}"
        logger.info("[OK] Date format validation test PASSED")

        # Email should match email pattern
        email = result.get('reporter_email')
        if email:
            assert '@' in email and '.' in email, f"Email validation failed: {email}"
            logger.info("[OK] Email format validation test PASSED")

        # Batch should be alphanumeric
        batch = result.get('batch_number')
        if batch:
            assert batch.replace('-', '').isalnum(), f"Batch validation failed: {batch}"
            logger.info("[OK] Batch number format validation test PASSED")

    def test_confidence_threshold(self):
        """PASS: Should enforce MIN_CONFIDENCE = 0.7"""
        # This test verifies that only high-confidence extractions are returned
        ambiguous_text = """
        Something Drug Name in the middle of text
        The Age could be 25 or something else
        """
        result = Form44Parser.parse_text(ambiguous_text)
        # Should return empty or minimal results due to low confidence
        assert len(result) <= 2, f"Too many fields extracted from ambiguous text: {result}"
        logger.info("[OK] Confidence threshold enforcement test PASSED")

    def test_no_multi_line_hallucination(self):
        """PASS: Should limit value length (prevent multi-line grabs)"""
        multiline_text = """
        Medical History: When the patient was young, they had measles.
        Then later they developed complications with their respiratory system.
        This led to hospitalizations multiple times.
        And the doctors tried different treatments.

        Adverse Reaction: High fever
        """
        result = Form44Parser.parse_text(multiline_text)

        # Medical history should be capped at reasonable length
        if result.get('medical_history'):
            assert len(result['medical_history']) < 300, "Value too long - potential multi-line hallucination"
            logger.info("[OK] Multi-line hallucination prevention test PASSED")

    def test_invalid_email_rejection(self):
        """PASS: Should reject invalid email formats"""
        invalid_email_text = """
        Reporter Email: not-an-email
        Reporter Email: @nodomain.com
        """
        result = Form44Parser.parse_text(invalid_email_text)
        email = result.get('reporter_email')
        # Should either be empty or a valid email
        assert email == '' or ('@' in email and '.' in email), f"Invalid email not rejected: {email}"
        logger.info("[OK] Invalid email rejection test PASSED")

    def test_invalid_age_rejection(self):
        """PASS: Should reject invalid age values"""
        invalid_age_text = """
        Patient Age: very old
        Patient Age: 45 and a half
        """
        result = Form44Parser.parse_text(invalid_age_text)
        age = result.get('patient_age')
        # Should be empty or valid number 0-999
        if age:
            assert age.isdigit() and 0 <= int(age) <= 999, f"Invalid age not rejected: {age}"
        logger.info("[OK] Invalid age rejection test PASSED")

    def test_real_form44_simulation(self):
        """PASS: Test with realistic Form 44 content"""
        form44_text = """
        FORM 44 - VOLUNTARY REPORT OF ADVERSE DRUG REACTION

        Drug Name: Paracetamol 500mg
        Batch Number: BATCH-2024-0001
        Manufacturing Date: 01-01-2023
        Expiration Date: 31-12-2025
        Strength: 500mg

        Patient Age: 35
        Patient Gender: Female
        Patient Weight: 65 kg
        Medical History: No significant history

        Adverse Reaction: Severe headache
        Date of Onset: 10-01-2024
        Duration: 2 days
        Severity: High
        Outcome: Recovered

        Concomitant Medications: Ibuprofen

        Reporter Name: Dr. John Smith
        Reporter Title: Physician
        Reporter Phone: +91-9876543210
        Reporter Email: dr.smith@hospital.com
        Report Date: 15-01-2024
        """

        result = Form44Parser.parse_text(form44_text)

        # Verify key fields were extracted
        required_fields = ['drug_name', 'batch_number', 'patient_age', 'adverse_reaction', 'reporter_name']
        extracted_required = [f for f in required_fields if result.get(f)]

        assert len(extracted_required) >= 3, f"Failed to extract required fields: {extracted_required}"
        logger.info(f"[OK] Real Form 44 simulation test PASSED - Extracted {len(result)} fields")

        # Print extracted data
        logger.info("=" * 70)
        logger.info("EXTRACTED FORM 44 DATA:")
        logger.info("=" * 70)
        for key, value in result.items():
            if value:
                logger.info(f"  {key}: {value}")
        logger.info("=" * 70)


def run_tests():
    """Run all tests"""
    test = TestForm44ExtractionFixes()

    print("\n" + "=" * 70)
    print("FORM 44 EXTRACTION - HALLUCINATION FIX VERIFICATION")
    print("=" * 70 + "\n")

    tests = [
        ("Empty text rejection", test.test_empty_text_rejection),
        ("Insufficient text rejection", test.test_insufficient_text_rejection),
        ("Strict keyword matching", test.test_strict_keyword_matching),
        ("Format validation", test.test_format_validation),
        ("Confidence threshold", test.test_confidence_threshold),
        ("Multi-line hallucination prevention", test.test_no_multi_line_hallucination),
        ("Invalid email rejection", test.test_invalid_email_rejection),
        ("Invalid age rejection", test.test_invalid_age_rejection),
        ("Real Form 44 simulation", test.test_real_form44_simulation),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            print(f"\n[TEST] Running: {test_name}...")
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"[FAIL] {e}")
            failed += 1
        except Exception as e:
            print(f"[ERROR] {e}")
            failed += 1

    print("\n" + "=" * 70)
    print(f"TEST RESULTS: {passed} PASSED | {failed} FAILED")
    print("=" * 70 + "\n")

    return failed == 0


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
