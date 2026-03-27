"""
Quick test of Form 44 extraction fixes
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from enhanced_app import Form44Parser

print("\n" + "=" * 70)
print("FORM 44 EXTRACTION - QUICK VALIDATION TEST")
print("=" * 70)

# Test 1: Real Form 44 data with minimum content
print("\n[TEST 1] Real Form 44 data extraction:")
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
print(f"  Extracted {len(result)} fields:")
for key, val in result.items():
    print(f"    - {key}: {val}")

extracted_count = sum(1 for v in result.values() if v)
print(f"  Status: {extracted_count} non-empty fields extracted")

# Test 2: Short/empty text rejection
print("\n[TEST 2] Short text rejection:")
short = "Drug Name: Test"
result = Form44Parser.parse_text(short)
print(f"  Input < 100 chars: returned {len(result)} fields (expected 0)")
assert len(result) == 0, "Failed: should reject short text"
print("  Status: PASS - rejected short text as expected")

# Test 3: Invalid format rejection
print("\n[TEST 3] Invalid age format rejection:")
invalid_age = "Patient Age: very old\nMore text here to make it 100+ chars longgggggggg" + " " * 100
result = Form44Parser.parse_text(invalid_age)
age = result.get('patient_age')
if age:
    print(f"  Extracted age: {age}")
    assert age.isdigit(), f"Failed: non-numeric age '{age}' was accepted"
    print("  Status: PASS - accepted only numeric age")
else:
    print(f"  No age extracted")
    print("  Status: PASS - rejected invalid age format")

# Test 4: Valid format acceptance
print("\n[TEST 4] Valid format acceptance:")
valid = "Patient Age: 45\nMore text here to make it longer and longer and longer than 100 chars to pass validation" + " " * 50
result = Form44Parser.parse_text(valid)
age = result.get('patient_age')
print(f"  Extracted age: {age}")
assert age == '45', f"Failed: expected '45', got '{age}'"
print("  Status: PASS - accepted valid numeric age")

print("\n" + "=" * 70)
print("ALL TESTS PASSED")
print("=" * 70 + "\n")
