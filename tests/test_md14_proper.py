"""
Proper MD-14 batch test that extracts and then processes with proper data
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"

print("=" * 80)
print("PROPER MD-14 BATCH TEST")
print("=" * 80)

# Step 1: Upload MD-14 batch
print("\n[STEP 1] Uploading MD-14 batch file...")

md14_batch_file = 'tests/fixtures/TEST_MD14_CORRECTED_BATCH.txt'

with open(md14_batch_file, 'r') as f:
    batch_content = f.read()

upload_resp = requests.post(
    f"{BASE_URL}/api/submissions/upload",
    files={'file': ('md14_batch.txt', batch_content, 'text/plain')}
)

submission_id = upload_resp.json()['submission_id']
print(f"[SUCCESS] Submission uploaded: {submission_id}")

time.sleep(1)

# Step 2: Extract MD-14
print("\n[STEP 2] Extracting MD-14 records...")

extract_resp = requests.post(f"{BASE_URL}/api/submissions/{submission_id}/extract-md14")
extract_data = extract_resp.json()

print(f"[SUCCESS] Extracted {extract_data['extracted_records']} MD-14 records")

# Get the md14_records from extraction
md14_records = extract_data.get('md14_records', [])
print(f"  Records available: {len(md14_records)}")

time.sleep(1)

# Step 3: Process with MD-14 records
print("\n[STEP 3] Processing submission with extracted MD-14 records...")

# Pass the extracted MD-14 records to the process endpoint
process_data = {
    'submission_data': {
        'md14_records': md14_records,
        'form_data': {}  # Empty form_data for MD-14 batch
    }
}

process_resp = requests.post(
    f"{BASE_URL}/api/submissions/{submission_id}/process",
    json=process_data
)

print(f"[SUCCESS] Process endpoint response: {process_resp.status_code}")

if process_resp.status_code != 200:
    print(f"[ERROR] Process failed:")
    print(process_resp.text[:500])
    exit(1)

time.sleep(2)

# Step 4: Get results
print("\n[STEP 4] Retrieving validation results...")

status_resp = requests.get(f"{BASE_URL}/api/submissions/{submission_id}/status")
status = status_resp.json()

print("\nValidation Results:")
for check in status.get('validation_results', []):
    check_type = check.get('check_type', 'Unknown')
    check_status = check.get('status', 'UNKNOWN')
    icon = '✓' if check_status == 'PASS' else '✗' if check_status == 'FAIL' else '⊘'
    print(f"  {icon} {check_type}: {check_status}")

print("\n" + "=" * 80)

# Check results
md14_check = next((c for c in status.get('validation_results', []) if c.get('check_type') == 'MD-14 Validation'), None)
md14_status = md14_check.get('status') if md14_check else 'UNKNOWN'

if md14_status == 'PASS':
    print("✓ TEST PASSED - MD-14 batch validation works correctly!")
else:
    print(f"✗ TEST FAILED - MD-14 validation status: {md14_status}")

print("=" * 80)
