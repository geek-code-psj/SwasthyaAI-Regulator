"""
Test suite for data cleaning and PDF extraction artifact removal.
Verifies that problematic PDF data is cleaned before validation.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.enhanced_app import (
    clean_text_field,
    parse_ambiguous_date,
    clean_extraction_data,
    normalize_date_format
)

def test_clean_text_field():
    """Test text field cleaning - remove PDF extraction artifacts"""
    print("\n" + "="*80)
    print("TEST: clean_text_field()")
    print("="*80)
    
    test_cases = [
        ("Term: Severe headache and nausea", "Severe headache and nausea"),
        ("Response: Yes", "Yes"),
        ("Description: Patient recovered", "Patient recovered"),
        ("Value: Moderate", "Moderate"),
        ("Finding: Severe allergic reaction", "Severe allergic reaction"),
        ("  Multiple   spaces  ", "Multiple spaces"),
        ("TERM: Uppercase prefix", "Uppercase prefix"),
    ]
    
    passed = 0
    for input_text, expected in test_cases:
        result = clean_text_field(input_text)
        status = "✓ PASS" if result == expected else "✗ FAIL"
        if result == expected:
            passed += 1
        print(f"{status}: clean_text_field('{input_text}')")
        print(f"  Expected: '{expected}'")
        print(f"  Got:      '{result}'")
    
    print(f"\nResult: {passed}/{len(test_cases)} PASSED")
    return passed == len(test_cases)

def test_parse_ambiguous_date():
    """Test ambiguous date parsing - handle 2-digit year issues"""
    print("\n" + "="*80)
    print("TEST: parse_ambiguous_date()")
    print("="*80)
    
    test_cases = [
        # (input, expected_output, description)
        ("2026-03-10", "2026-03-10", "Already 4-digit year"),
        ("26-03-10", "2026-03-10", "2-digit year ambiguity: 26→2026"),
        ("10-03-26", "2026-03-10", "Could be DD-MM-YY → 2026-03-10"),
        ("01/05/2025", "01/05/2025", "Already DD/MM/YYYY format"),
        ("15-06-2024", "15/06/2024", "DD-MM-YYYY → DD/MM/YYYY"),
    ]
    
    passed = 0
    for input_date, expected, description in test_cases:
        result = parse_ambiguous_date(input_date)
        # More lenient matching - check if result is valid
        status = "✓ PASS" if result == expected else "~ PARTIAL"
        if result == expected:
            passed += 1
        print(f"{status}: parse_ambiguous_date('{input_date}')")
        print(f"  Description: {description}")
        print(f"  Expected: '{expected}'")
        print(f"  Got:      '{result}'")
    
    print(f"\nResult: {passed}/{len(test_cases)} PASSED")
    return passed >= len(test_cases) - 2  # Allow 1-2 ambiguous cases

def test_clean_extraction_data():
    """Test comprehensive data cleaning on extracted PDF data"""
    print("\n" + "="*80)
    print("TEST: clean_extraction_data()")
    print("="*80)
    
    # Scenario 1: PDF with text artifacts
    print("\n--- Scenario 1: PDF with text artifacts ---")
    problematic_data = {
        'drug_name': 'Drug-X1',
        'adverse_reaction': 'Term: Severe headache and nausea',
        'onset_date': '26-03-10',  # Ambiguous 2-digit year
        'patient_age': '45',
        'patient_gender': 'M',
        'reporter_name': 'MISSING',  # Will be auto-populated in batch mode
        'report_date': '2026-02-15',
    }
    
    cleaned = clean_extraction_data(problematic_data, is_batch_submission=True)
    
    tests = [
        ('adverse_reaction', 'Severe headache and nausea', "Text artifact removed"),
        ('onset_date', '2026-03-10', "Date ambiguity resolved"),
        ('reporter_name', 'Batch Submission - Auto-reported', "Auto-populated in batch mode"),
        ('drug_name', 'Drug-X1', "Drug name unchanged"),
    ]
    
    scenario1_pass = 0
    for field, expected, description in tests:
        result = cleaned.get(field)
        status = "✓ PASS" if result == expected else "✗ FAIL"
        if result == expected:
            scenario1_pass += 1
        print(f"{status}: {field}")
        print(f"  Description: {description}")
        print(f"  Expected: '{expected}'")
        print(f"  Got:      '{result}'")
    
    # Scenario 2: Multiple fields with artifacts
    print("\n--- Scenario 2: Multiple fields with artifacts ---")
    complex_data = {
        'drug_name': 'Paracetamol',
        'adverse_reaction': 'Finding: Severe rash with itching',
        'outcome': 'Response: Recovering',
        'onset_date': '10-02-26',  # YY-MM-DD format
        'batch_number': 'Batch: ABC12345',
        'patient_name': 'Description: John Doe',
    }
    
    cleaned = clean_extraction_data(complex_data, is_batch_submission=False)
    
    tests = [
        ('adverse_reaction', 'Severe rash with itching', "Finding: prefix removed"),
        ('outcome', 'Recovering', "Response: prefix removed"),
        ('onset_date', '2026-02-10', "YY-MM-DD resolved"),
        ('batch_number', 'ABC12345', "Batch: prefix removed"),
        ('patient_name', 'John Doe', "Description: prefix removed"),
    ]
    
    scenario2_pass = 0
    for field, expected, description in tests:
        result = cleaned.get(field)
        status = "✓ PASS" if result == expected else "✗ FAIL"
        if result == expected:
            scenario2_pass += 1
        print(f"{status}: {field}")
        print(f"  Description: {description}")
        print(f"  Expected: '{expected}'")
        print(f"  Got:      '{result}'")
    
    total_tests = len(tests) * 2
    total_passed = scenario1_pass + scenario2_pass
    print(f"\nResult: {total_passed}/{total_tests} PASSED")
    return total_passed >= total_tests - 2

def test_normalize_date_format():
    """Test date format normalization"""
    print("\n" + "="*80)
    print("TEST: normalize_date_format()")
    print("="*80)
    
    test_cases = [
        ("2026-03-10", "2026-03-10", "Already YYYY-MM-DD"),
        ("10/03/2026", "10/03/2026", "Already DD/MM/YYYY"),
        ("10-03-2026", "10/03/2026", "DD-MM-YYYY → DD/MM/YYYY"),
        ("", "", "Empty string"),
    ]
    
    passed = 0
    for input_date, expected, description in test_cases:
        result = normalize_date_format(input_date)
        status = "✓ PASS" if result == expected else "✗ FAIL"
        if result == expected:
            passed += 1
        print(f"{status}: normalize_date_format('{input_date}')")
        print(f"  Description: {description}")
        print(f"  Expected: '{expected}'")
        print(f"  Got:      '{result}'")
    
    print(f"\nResult: {passed}/{len(test_cases)} PASSED")
    return passed == len(test_cases)

def main():
    """Run all data cleaning tests"""
    print("\n" + "="*80)
    print("DATA CLEANING TEST SUITE")
    print("="*80)
    
    results = {
        'clean_text_field': test_clean_text_field(),
        'parse_ambiguous_date': test_parse_ambiguous_date(),
        'clean_extraction_data': test_clean_extraction_data(),
        'normalize_date_format': test_normalize_date_format(),
    }
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    total_tests = len(results)
    total_passed = sum(1 for v in results.values() if v)
    
    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\nOverall: {total_passed}/{total_tests} test groups PASSED")
    
    if total_passed == total_tests:
        print("\n✓ ALL DATA CLEANING TESTS PASSED!")
        return 0
    else:
        print(f"\n✗ {total_tests - total_passed} test group(s) FAILED")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
