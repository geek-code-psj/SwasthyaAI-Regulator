"""
Test the complete processing pipeline end-to-end
Identify issues and bottlenecks
"""
import requests
import json
import time
import sys
import tempfile
import os

BASE_URL = "http://localhost:5000"

print("\n" + "="*80)
print("PROCESSING PIPELINE TEST")
print("="*80 + "\n")

# Step 1: Get authentication token
print("[STEP 1] Getting authentication token...")
try:
    auth_response = requests.post(
        f"{BASE_URL}/api/cdsco/auth/login",
        json={"username": "admin", "password": "admin"}
    )
    if auth_response.status_code != 200:
        print(f"  FAILED: {auth_response.status_code}")
        print(f"  Response: {auth_response.text}")
        sys.exit(1)

    token = auth_response.json().get('access_token')
    print(f"  SUCCESS: Got token")
except Exception as e:
    print(f"  ERROR: {e}")
    sys.exit(1)

# Step 2: Upload test document
print("\n[STEP 2] Uploading test document...")
try:
    import tempfile
    import os
    test_dir = tempfile.gettempdir()
    test_file = os.path.join(test_dir, "test_form44_pipeline.txt")
    with open(test_file, 'w') as f:
        f.write("""
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
""" + " " * 200)

    files = {'file': open(test_file, 'rb')}
    headers = {'Authorization': f'Bearer {token}'}

    upload_response = requests.post(
        f"{BASE_URL}/api/submissions/upload",
        files=files,
        headers=headers
    )

    if upload_response.status_code != 200:
        print(f"  FAILED: {upload_response.status_code}")
        print(f"  Response: {upload_response.text}")
        sys.exit(1)

    submission_id = upload_response.json().get('submission_id')
    print(f"  SUCCESS: Uploaded document")
    print(f"  Submission ID: {submission_id}")
except Exception as e:
    print(f"  ERROR: {e}")
    sys.exit(1)

# Step 3: Check initial status
print("\n[STEP 3] Checking initial submission status...")
try:
    headers = {'Authorization': f'Bearer {token}'}
    status_response = requests.get(
        f"{BASE_URL}/api/submissions/{submission_id}/status",
        headers=headers
    )

    if status_response.status_code == 200:
        status_data = status_response.json()
        print(f"  Current Status: {status_data.get('status')}")
        print(f"  Validation Results: {len(status_data.get('validation_results', []))}")
    else:
        print(f"  FAILED: {status_response.status_code}")
except Exception as e:
    print(f"  ERROR: {e}")

# Step 4: Extract Form 44 data
print("\n[STEP 4] Extracting Form 44 data...")
try:
    headers = {'Authorization': f'Bearer {token}'}
    extract_response = requests.post(
        f"{BASE_URL}/api/submissions/{submission_id}/extract-form44",
        headers=headers
    )

    if extract_response.status_code == 200:
        extract_data = extract_response.json()
        print(f"  Extraction Status: {extract_data.get('status')}")
        print(f"  Extraction Quality: {extract_data.get('extraction_quality')}")
        print(f"  Fields Extracted: {extract_data.get('extracted_fields')}/{extract_data.get('total_fields')}")
        extracted_form_data = extract_data.get('form44_data', {})
    else:
        print(f"  FAILED: {extract_response.status_code}")
        extracted_form_data = {}
except Exception as e:
    print(f"  ERROR: {e}")
    extracted_form_data = {}

# Step 5: Process through pipeline
print("\n[STEP 5] Processing submission through pipeline...")
try:
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    pipeline_data = {
        'submission_data': {
            'form_data': extracted_form_data,
            'duplicate_candidates': [
                {
                    'id': '001',
                    'drug_name': 'Paracetamol 500mg',
                    'applicant': 'Test Corp',
                    'submission_date': '2024-01-15'
                }
            ],
            'naranjo_data': {
                'drug_name': 'Paracetamol 500mg',
                'adverse_event': 'Severe headache',
                'naranjo_score': 8
            }
        }
    }

    start_time = time.time()
    process_response = requests.post(
        f"{BASE_URL}/api/submissions/{submission_id}/process",
        json=pipeline_data,
        headers=headers
    )
    pipeline_duration = time.time() - start_time

    if process_response.status_code == 200:
        pipeline_report = process_response.json()
        print(f"  Pipeline Execution Time: {pipeline_duration:.2f}s")
        print(f"  Overall Status: {pipeline_report.get('overall_status')}")
        print(f"  Processing Status: {pipeline_report.get('processing_status')}")
        print(f"  Checks Performed: {len(pipeline_report.get('checks_performed', []))}")

        print(f"\n  STAGE PROGRESSION:")
        for i, stage in enumerate(pipeline_report.get('stage_progression', []), 1):
            print(f"    {i}. {stage}")

        print(f"\n  CHECKS PERFORMED:")
        for check in pipeline_report.get('checks_performed', []):
            check_type = check.get('type', 'Unknown')
            status = check.get('status', 'UNKNOWN')
            print(f"    [{status}] {check_type}")
            if status == 'ERROR':
                print(f"      Error: {check.get('error')}")
            if check.get('completeness'):
                print(f"      Completeness: {check.get('completeness')}%")

        if pipeline_report.get('critical_issues'):
            print(f"\n  CRITICAL ISSUES: {len(pipeline_report.get('critical_issues'))}")
            for issue in pipeline_report.get('critical_issues', [])[:3]:
                print(f"    - {issue}")
    else:
        print(f"  FAILED: {process_response.status_code}")
        print(f"  Response: {process_response.text}")
except Exception as e:
    print(f"  ERROR: {e}")

# Step 6: Get final results
print("\n[STEP 6] Retrieving final results...")
try:
    headers = {'Authorization': f'Bearer {token}'}
    results_response = requests.get(
        f"{BASE_URL}/api/submissions/{submission_id}/results",
        headers=headers
    )

    if results_response.status_code == 200:
        results_data = results_response.json()
        print(f"  Total Checks: {results_data.get('total_checks')}")
        print(f"  Passed: {results_data.get('checks_passed')}")
        print(f"  Failed: {results_data.get('checks_failed')}")
        print(f"  Skipped: {results_data.get('checks_skipped')}")
        print(f"  Errored: {results_data.get('checks_errored')}")

        if results_data.get('findings'):
            print(f"\n  FINDINGS:")
            for finding in results_data.get('findings', [])[:3]:
                print(f"    {finding}")
    else:
        print(f"  FAILED: {results_response.status_code}")
except Exception as e:
    print(f"  ERROR: {e}")

print("\n" + "="*80)
print("PIPELINE TEST COMPLETE")
print("="*80 + "\n")
