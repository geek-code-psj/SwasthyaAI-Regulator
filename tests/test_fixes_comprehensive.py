"""
Test the full pipeline with the exact problematic data from the backend logs
This tests:
1. Data cleaning (text artifacts, date parsing, reporter_name auto-population)
2. ADR validation with cleaned data
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"

# Exact data from the backend logs that was failing
problematic_data = {
    'adverse_reaction': 'Term: Severe headache and nausea',  # Has "Term:" prefix
    'dose': '50 mg',
    'drug_name': 'Drug-X1',
    'onset_date': '26-03-10',  # 2-digit year format (should be 2026-03-10)
    'outcome': 'Recovering',
    'patient_age': '45',
    'patient_id': 'AE001',
    'report_date': '26-03-15',  # 2-digit year format (should be 2026-03-15)
    'severity': 'Moderate',
    'strength': '50 mg'
    # NOTE: reporter_name is MISSING from original data
}

print("=" * 80)
print("TESTING FULL PIPELINE WITH PROBLEMATIC DATA")
print("=" * 80)
print("\n[TEST] Step 1: Upload submission with problematic data")

# Upload the submission
upload_data = {
    'file': ('test_problematic.txt', json.dumps({'records': [problematic_data]}), 'application/json'),
}

files = {
    'file': ('test_problematic.txt', json.dumps({'records': [problematic_data]}), 'application/json')
}

try:
    upload_response = requests.post(
        f"{BASE_URL}/api/submissions/upload",
        files=files
    )
    
    if upload_response.status_code != 200:
        print(f"[FAIL] Upload failed: {upload_response.text}")
        exit(1)
    
    submission_id = upload_response.json()['submission_id']
    print(f"[SUCCESS] Submission uploaded - ID: {submission_id}")
    
except Exception as e:
    print(f"[ERROR] Upload failed: {e}")
    exit(1)

# Process the submission
print(f"\n[TEST] Step 2: Process submission (trigger data cleaning and validation)")
time.sleep(1)

try:
    process_response = requests.post(
        f"{BASE_URL}/api/submissions/{submission_id}/process",
        json={'submission_data': {'form_data': problematic_data}}
    )
    
    if process_response.status_code != 200:
        print(f"[FAIL] Process failed: {process_response.text}")
        exit(1)
    
    process_result = process_response.json()
    print(f"[SUCCESS] Submission processed")
    
except Exception as e:
    print(f"[ERROR] Process failed: {e}")
    exit(1)

# Get status and results
print(f"\n[TEST] Step 3: Retrieve results")
time.sleep(1)

try:
    status_response = requests.get(f"{BASE_URL}/api/submissions/{submission_id}/status")
    
    if status_response.status_code != 200:
        print(f"[FAIL] Status retrieval failed: {status_response.text}")
        exit(1)
    
    status = status_response.json()
    
except Exception as e:
    print(f"[ERROR] Status retrieval failed: {e}")
    exit(1)

# Display results
print("\n" + "=" * 80)
print("VALIDATION RESULTS")
print("=" * 80)

# Get results
try:
    results_response = requests.get(f"{BASE_URL}/api/submissions/{submission_id}/results")
    if results_response.status_code == 200:
        results = results_response.json()
        print(f"\nResults retrieved: {json.dumps(results, indent=2)}")
except:
    pass

# Display status
print(f"Overall Status: {status.get('status', 'UNKNOWN')}")

# Check each validation
checks = status.get('validation_summary', {}).get('checks_performed', [])
print(f"\nValidation Checks ({len(checks)} total):")

all_pass = True
for i, check in enumerate(checks, 1):
    status_str = check.get('status', 'UNKNOWN')
    check_type = check.get('type', 'Unknown')
    
    # Color code the status
    if status_str == 'PASS':
        icon = '✓'
    elif status_str == 'FAIL':
        icon = '✗'
        all_pass = False
    else:
        icon = '●'
    
    print(f"  {icon} {i}. {check_type}: {status_str}")
    
    # Show details if available
    if 'details' in check and check['details']:
        print(f"     Details: {check['details']}")

print("\n" + "=" * 80)

# Expected outcomes
print("\nEXPECTED OUTCOMES WITH FIXES:")
print("  1. adverse_reaction: 'Term: Severe headache and nausea' → 'Severe headache and nausea' (artifact removed)")
print("  2. onset_date: '26-03-10' → '2026-03-10' (2-digit year parsed correctly)")
print("  3. report_date: '26-03-15' → '2026-03-15' (2-digit year parsed correctly)")
print("  4. reporter_name: MISSING → 'Auto-reported (Extracted)' (auto-populated)")
print("  5. ADR Validation should PASS (all fields properly cleaned and formatted)")

print("\nOVERALL TEST: " + ("✓ PASS" if all_pass else "✗ FAIL"))
print("=" * 80)
