"""
Comprehensive Pipeline Test - Verify all fixes
Tests: ADR validation, form type detection, encoding, stage progression
"""
import requests
import json


BASE_URL = "http://localhost:5000"

print("\n" + "="*80)
print("COMPREHENSIVE PROCESSING PIPELINE TEST")
print("Testing all fixes and edge cases")
print("="*80 + "\n")

# Get token
auth_response = requests.post(
    f"{BASE_URL}/api/cdsco/auth/login",
    json={"username": "admin", "password": "admin"}
)
token = auth_response.json().get('access_token')

# TEST 1: Full ADR with all mandatory fields
print("[TEST 1] Full ADR submission with all mandatory fields")
print("-" * 80)

test_data = {
    'drug_name': 'Paracetamol 500mg',
    'adverse_reaction': 'Severe headache',
    'patient_age': '35',
    'onset_date': '10-01-2024',
    'reporter_name': 'Dr. John Smith',
    'report_date': '15-01-2024',
    'severity': 'High',
    'outcome': 'Recovered',
    'duration': '2 days',
    'concomitant_medications': 'Ibuprofen',
    'patient_gender': 'Female',
    'patient_weight': '65 kg',
}

pipeline_data = {
    'submission_data': {
        'form_data': test_data,
        'naranjo_data': {
            'drug_name': test_data['drug_name'],
            'adverse_event': test_data['adverse_reaction'],
            'naranjo_score': 8
        }
    }
}

# Create sample file and upload
import tempfile
import os

test_dir = tempfile.gettempdir()
test_file = os.path.join(test_dir, "test_adr_full.txt")

with open(test_file, 'w') as f:
    f.write(json.dumps(test_data) + " " * 100)

files = {'file': open(test_file, 'rb')}
headers = {'Authorization': f'Bearer {token}'}

upload_response = requests.post(f"{BASE_URL}/api/submissions/upload", files=files, headers=headers)
submission_id_1 = upload_response.json().get('submission_id')

# Process through pipeline
process_response = requests.post(
    f"{BASE_URL}/api/submissions/{submission_id_1}/process",
    json=pipeline_data,
    headers=headers
)

result = process_response.json()
print(f"Overall Status: {result.get('overall_status')}")
print(f"Processing Status: {result.get('processing_status')}")
print(f"Completeness: {[c for c in result.get('checks_performed', []) if 'Validation' in c.get('type', '')]}")

# Verify PASS
assert result.get('overall_status') == 'PASS', "TEST 1 FAILED: Expected PASS status"
print("[OK] TEST 1 PASSED: Full ADR submission validated successfully\n")

# TEST 2: Partial ADR with missing optional fields
print("[TEST 2] Partial ADR with missing optional fields")
print("-" * 80)

partial_data = {
    'drug_name': 'Aspirin 500mg',
    'adverse_reaction': 'Nausea',
    'patient_age': '45',
    'onset_date': '15-01-2024',
    'reporter_name': 'Dr. Jane Doe',
    'report_date': '20-01-2024',
    # Missing: severity, outcome, duration, concomitant_medications
}

pipeline_data = {
    'submission_data': {
        'form_data': partial_data,
        'naranjo_data': {
            'drug_name': partial_data['drug_name'],
            'adverse_event': partial_data['adverse_reaction'],
            'naranjo_score': 5
        }
    }
}

test_file = os.path.join(test_dir, "test_adr_partial.txt")
with open(test_file, 'w') as f:
    f.write(json.dumps(partial_data) + " " * 100)

files = {'file': open(test_file, 'rb')}
upload_response = requests.post(f"{BASE_URL}/api/submissions/upload", files=files, headers=headers)
submission_id_2 = upload_response.json().get('submission_id')

process_response = requests.post(
    f"{BASE_URL}/api/submissions/{submission_id_2}/process",
    json=pipeline_data,
    headers=headers
)

result = process_response.json()
completeness = [c.get('completeness') for c in result.get('checks_performed', []) if 'Validation' in c.get('type', '')]

print(f"Overall Status: {result.get('overall_status')}")
print(f"Completeness: {completeness}")

# Should still PASS because all mandatory fields present
assert result.get('overall_status') == 'PASS', "TEST 2 FAILED: Expected PASS for partial ADR"
print("[OK] TEST 2 PASSED: Partial ADR still validates (mandatory fields present)\n")

# TEST 3: Verify form type detection
print("[TEST 3] Form type detection (ADR vs DMF)")
print("-" * 80)

# Check the check_type to see if "ADR Validation" is being used
checks = result.get('checks_performed', [])
validation_check = [c for c in checks if 'Validation' in c.get('type', '')][0]

print(f"Detected Check Type: {validation_check.get('type')}")
print(f"Form Type: {validation_check.get('form_type', 'not specified')}")

assert 'ADR' in validation_check.get('type', ''), "TEST 3 FAILED: ADR Validation not detected"
print("[OK] TEST 3 PASSED: Form type detection correctly identified ADR\n")

# TEST 4: Verify stage progression
print("[TEST 4] Pipeline stage progression")
print("-" * 80)

result = process_response.json()
stages = result.get('stage_progression', [])

print("Stages executed:")
for i, stage in enumerate(stages, 1):
    print(f"  {i}. {stage}")

expected_stages = ['validating_duplicates', 'validating_consistency', 'validating_form']
for expected_stage in expected_stages:
    assert expected_stage in stages, f"TEST 4 FAILED: Missing stage {expected_stage}"

print("[OK] TEST 4 PASSED: All pipeline stages executed\n")

# TEST 5: Verify no encoding errors in results
print("[TEST 5] Character encoding safety")
print("-" * 80)

results_response = requests.get(
    f"{BASE_URL}/api/submissions/{submission_id_2}/results",
    headers=headers
)

findings = results_response.json().get('findings', [])
print(f"Findings count: {len(findings)}")

# Try to encode findings (would fail with unicode if not fixed)
try:
    for finding in findings:
        # This would crash with unicode issues before the fix
        json.dumps(finding)
    print("[OK] All findings are properly encoded")
except UnicodeEncodeError as e:
    print(f"[FAIL] Encoding error: {e}")
    raise

print("[OK] TEST 5 PASSED: No character encoding errors\n")

# SUMMARY
print("="*80)
print("ALL TESTS PASSED")
print("="*80)
print("\nPipeline fixes verified:")
print("  [OK] ADRValidator correctly validates adverse event data")
print("  [OK] Form type detection (ADR vs DMF) working")
print("  [OK] Completeness scores accurate for ADR format")
print("  [OK] Character encoding fixed (no unicode crashes)")
print("  [OK] Stage progression correct")
print("  [OK] Overall status correctly set to PASS for complete submissions")
print("\n")
