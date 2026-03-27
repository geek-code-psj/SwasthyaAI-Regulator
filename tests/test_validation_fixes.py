#!/usr/bin/env python3
"""
Comprehensive Test Suite for ADR and MD-14 Validation Fixes
Tests field mapping, date normalization, and flexible enum validation
"""

import sys
import os
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../backend'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../backend/modules'))

from modules.adr_validator import ADRValidator
from modules.field_validator import MD14Validator
from enhanced_app import normalize_md14_to_adr, normalize_date_format

# ============================================================================
# TEST FIXTURES
# ============================================================================

def fixture_valid_adr_data():
    """Complete, valid Form 44 ADR submission"""
    return {
        'drug_name': 'Aspirin',
        'adverse_reaction': 'Severe gastric irritation',
        'patient_age': '45',
        'onset_date': '15/03/2026',
        'reporter_name': 'Dr. John Smith',
        'report_date': '20/03/2026',
        'severity': 'Moderate',
        'outcome': 'Recovering',
        'patient_gender': 'M'
    }

def fixture_valid_md14_record():
    """Complete, valid MD-14 record"""
    return {
        'case_id': 'CASE-2026-001',
        'patient_age': '45',
        'patient_gender': 'M',
        'adverse_event_term': 'Severe gastric irritation with bleeding',
        'event_onset_date': '2026-03-15',
        'event_severity': 'Moderate',
        'outcome': 'Recovering',
        'drug_name': 'Aspirin',
        'dose': '500 mg',
        'dechallenge_performed': True,
        'report_date': '2026-03-20'
    }

def fixture_md14_batch():
    """Multiple MD-14 records for batch validation"""
    return [
        {
            'case_id': 'CASE-2026-001',
            'patient_age': '45',
            'patient_gender': 'M',
            'adverse_event_term': 'Severe gastric irritation with bleeding',
            'event_onset_date': '2026-03-15',
            'event_severity': 'Moderate',
            'outcome': 'Recovering',
            'drug_name': 'Aspirin',
            'dose': '500 mg',
            'dechallenge_performed': True,
            'report_date': '2026-03-20'
        },
        {
            'case_id': 'CASE-2026-002',
            'patient_age': '28',
            'patient_gender': 'F',
            'adverse_event_term': 'Allergic reaction with rash',
            'event_onset_date': '03/18/2026',  # Different date format
            'event_severity': 'Mild',
            'outcome': 'Recovered',
            'drug_name': 'Penicillin',
            'dose': '1000 mg',
            'dechallenge_performed': False,
            'report_date': '03/25/2026'
        }
    ]

# ============================================================================
# TEST CASES
# ============================================================================

def test_date_format_normalization():
    """Test that date format normalization works correctly"""
    print("\n[TEST 1] Date Format Normalization")
    print("=" * 60)
    
    test_cases = [
        ('2026-03-15', '2026-03-15'),  # Already correct
        ('15/03/2026', '15/03/2026'),  # Already correct
        ('15-03-2026', '15/03/2026'),  # Should convert dashes to slashes
        ('', ''),  # Empty
    ]
    
    passed = 0
    for input_date, expected_output in test_cases:
        result = normalize_date_format(input_date)
        status = "PASS" if result == expected_output else "FAIL"
        print(f"  [{status}]: '{input_date}' -> '{result}' (expected: '{expected_output}'")
        if result == expected_output:
            passed += 1
    
    print(f"\nResult: {passed}/{len(test_cases)} passed")
    return passed == len(test_cases)

def test_field_mapping():
    """Test MD-14 to ADR field mapping"""
    print("\n[TEST 2] Field Mapping (MD-14 -> ADR)")
    print("=" * 60)
    
    md14_data = {
        'adverse_event_term': 'Test reaction',
        'event_onset_date': '2026-03-15',
        'event_severity': 'Moderate',
        'case_id': 'CASE-001',
        'drug_name': 'Test Drug'
    }
    
    normalized = normalize_md14_to_adr(md14_data)
    
    expected_mappings = [
        ('adverse_reaction', 'Test reaction'),
        ('onset_date', '2026-03-15'),
        ('severity', 'Moderate'),
        ('case_id', 'CASE-001'),  # Pass-through
        ('drug_name', 'Test Drug'),  # Pass-through
    ]
    
    passed = 0
    for field_name, expected_value in expected_mappings:
        actual_value = normalized.get(field_name)
        status = "[PASS]" if actual_value == expected_value else "[FAIL]"
        print(f"  {status}: {field_name} = '{actual_value}' (expected: '{expected_value}')")
        if actual_value == expected_value:
            passed += 1
    
    print(f"\nResult: {passed}/{len(expected_mappings)} passed")
    return passed == len(expected_mappings)

def test_adr_validation_valid_data():
    """Test ADR validator with valid data"""
    print("\n[TEST 3] ADR Validation - Valid Data")
    print("=" * 60)
    
    validator = ADRValidator()
    form_data = fixture_valid_adr_data()
    result = validator.validate_adr(form_data, is_batch=False)
    
    print(f"  Overall Status: {result['overall_status']}")
    print(f"  Completeness: {result['completeness_score']}%")
    print(f"  Critical Issues: {len(result['critical_issues'])}")
    
    if result['critical_issues']:
        for issue in result['critical_issues']:
            print(f"    - {issue}")
    
    is_pass = result['overall_status'] == 'PASS'
    print(f"\nResult: {'[PASS]' if is_pass else '[FAIL]'}")
    return is_pass

def test_adr_validation_batch_mode():
    """Test ADR validator in batch mode (reporter_name optional)"""
    print("\n[TEST 4] ADR Validation - Batch Mode (reporter_name optional)")
    print("=" * 60)
    
    validator = ADRValidator()
    form_data = {
        'drug_name': 'Aspirin',
        'adverse_reaction': 'Gastric irritation',
        'patient_age': '45',
        'onset_date': '2026-03-15',
        'reporter_name': '',  # Empty in batch mode
        'report_date': '2026-03-20'
    }
    
    result = validator.validate_adr(form_data, is_batch=True)
    
    print(f"  Overall Status: {result['overall_status']}")
    print(f"  Completeness: {result['completeness_score']}%")
    print(f"  Critical Issues: {len(result['critical_issues'])}")
    
    if result['critical_issues']:
        for issue in result['critical_issues']:
            print(f"    - {issue}")
    
    is_pass = result['overall_status'] == 'PASS'
    print(f"\nResult: {'[PASS]' if is_pass else '[FAIL]'}")
    return is_pass

def test_adr_validation_missing_field():
    """Test ADR validator with missing mandatory field"""
    print("\n[TEST 5] ADR Validation - Missing Mandatory Field")
    print("=" * 60)
    
    validator = ADRValidator()
    form_data = {
        'drug_name': 'Aspirin',
        # Missing: adverse_reaction
        'patient_age': '45',
        'onset_date': '2026-03-15',
        'reporter_name': 'Dr. Smith',
        'report_date': '2026-03-20'
    }
    
    result = validator.validate_adr(form_data, is_batch=False)
    
    print(f"  Overall Status: {result['overall_status']}")
    print(f"  Critical Issues: {len(result['critical_issues'])}")
    
    if result['critical_issues']:
        for issue in result['critical_issues']:
            print(f"    - {issue}")
    
    is_fail = result['overall_status'] == 'FAIL'
    print(f"\nResult: {'[PASS]' if is_fail else '[FAIL]'} (Expected: FAIL)")
    return is_fail

def test_md14_validation_single_record():
    """Test MD-14 validator with valid record"""
    print("\n[TEST 6] MD-14 Validation - Single Valid Record")
    print("=" * 60)
    
    validator = MD14Validator()
    record = fixture_valid_md14_record()
    result = validator.validate_md14_record(record)
    
    print(f"  Case ID: {result['case_id']}")
    print(f"  Valid: {result['valid']}")
    print(f"  Data Quality Score: {result['data_quality_score']}%")
    print(f"  Errors: {len(result['errors'])}")
    
    if result['errors']:
        for error in result['errors']:
            print(f"    - {error}")
    
    is_valid = result['valid']
    print(f"\nResult: {'[PASS]' if is_valid else '[FAIL]'}")
    return is_valid

def test_md14_validation_flexible_dates():
    """Test MD-14 validator with multiple date formats"""
    print("\n[TEST 7] MD-14 Validation - Flexible Date Formats")
    print("=" * 60)
    
    validator = MD14Validator()
    
    # Test with DD/MM/YYYY format
    record = {
        'case_id': 'CASE-2026-001',
        'patient_age': '45',
        'patient_gender': 'M',
        'adverse_event_term': 'Test reaction',
        'event_onset_date': '15/03/2026',  # DD/MM/YYYY format
        'event_severity': 'Mild',
        'outcome': 'Recovered',
        'drug_name': 'Test Drug',
        'dose': '100 mg',
        'dechallenge_performed': False,
        'report_date': '20/03/2026'  # DD/MM/YYYY format
    }
    
    result = validator.validate_md14_record(record)
    
    print(f"  Date format: DD/MM/YYYY (flexible)")
    print(f"  Valid: {result['valid']}")
    print(f"  Data Quality Score: {result['data_quality_score']}%")
    
    if result['errors']:
        for error in result['errors']:
            print(f"    - {error}")
    
    is_valid = result['valid']
    print(f"\nResult: {'[PASS]' if is_valid else '[FAIL]'}")
    return is_valid

def test_md14_validation_flexible_enum():
    """Test MD-14 validator with flexible enum matching"""
    print("\n[TEST 8] MD-14 Validation - Flexible Enum Matching")
    print("=" * 60)
    
    validator = MD14Validator()
    
    # Test with slightly different enum value
    record = {
        'case_id': 'CASE-2026-001',
        'patient_age': '45',
        'patient_gender': 'M',
        'adverse_event_term': 'Test reaction',
        'event_onset_date': '2026-03-15',
        'event_severity': 'mild',  # lowercase - should normalize to 'Mild'
        'outcome': 'recovered',  # lowercase - should normalize to 'Recovered'
        'drug_name': 'Test Drug',
        'dose': '100 mg',
        'dechallenge_performed': False,
        'report_date': '2026-03-20'
    }
    
    result = validator.validate_md14_record(record)
    
    print(f"  Severity: 'mild' -> normalized")
    print(f"  Outcome: 'recovered' -> normalized")
    print(f"  Valid: {result['valid']}")
    print(f"  Data Quality Score: {result['data_quality_score']}%")
    
    if result['errors']:
        for error in result['errors']:
            print(f"    - {error}")
    
    is_valid = result['valid']
    print(f"\nResult: {'[PASS]' if is_valid else '[FAIL]'}")
    return is_valid

def test_md14_batch_validation():
    """Test MD-14 batch validation with multiple records"""
    print("\n[TEST 9] MD-14 Batch Validation - Multiple Records")
    print("=" * 60)
    
    validator = MD14Validator()
    records = fixture_md14_batch()
    result = validator.validate_md14_batch(records)
    
    print(f"  Total Records: {result['total_records']}")
    print(f"  Valid Records: {result['valid_records']}")
    print(f"  Invalid Records: {result['invalid_records']}")
    print(f"  Overall Status: {result['overall_status']}")
    print(f"  Overall Data Quality: {result['overall_data_quality']}%")
    
    is_pass = result['overall_status'] == 'PASS'
    print(f"\nResult: {'[PASS]' if is_pass else '[FAIL]'}")
    return is_pass

def test_pipeline_integration():
    """Test complete pipeline: MD-14 -> normalize -> ADR validation"""
    print("\n[TEST 10] Pipeline Integration - MD-14 to ADR Full Pipeline")
    print("=" * 60)
    
    # Start with MD-14 record
    md14_record = fixture_valid_md14_record()
    print(f"  Input: MD-14 record (case_id: {md14_record['case_id']})")
    
    # Normalize to ADR format
    normalized = normalize_md14_to_adr(md14_record)
    print(f"  After mapping: {list(normalized.keys())[:5]}... ({len(normalized)} fields)")
    
    # Validate as ADR
    adr_validator = ADRValidator()
    adr_result = adr_validator.validate_adr(normalized, is_batch=True)
    print(f"  ADR Validation Status: {adr_result['overall_status']}")
    print(f"  Completeness: {adr_result['completeness_score']}%")
    
    is_pass = adr_result['overall_status'] == 'PASS'
    print(f"\nResult: {'[PASS]' if is_pass else '[FAIL]'}")
    return is_pass

# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def run_all_tests():
    """Run all test cases and report results"""
    print("\n")
    print("=" * 70)
    print("SWASTHYAAI REGULATOR - VALIDATION FIXES TEST SUITE")
    print("=" * 70)
    
    tests = [
        test_date_format_normalization,
        test_field_mapping,
        test_adr_validation_valid_data,
        test_adr_validation_batch_mode,
        test_adr_validation_missing_field,
        test_md14_validation_single_record,
        test_md14_validation_flexible_dates,
        test_md14_validation_flexible_enum,
        test_md14_batch_validation,
        test_pipeline_integration,
    ]
    
    results = []
    for i, test_func in enumerate(tests, 1):
        try:
            passed = test_func()
            results.append((test_func.__name__, passed))
        except Exception as e:
            print(f"\n[X] ERROR in {test_func.__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append((test_func.__name__, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for test_name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {status}: {test_name}")
    
    print("\n" + "-" * 70)
    print(f"TOTAL: {passed_count}/{total_count} tests passed")
    print("=" * 70 + "\n")
    
    return passed_count == total_count

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
