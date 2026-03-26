#!/usr/bin/env python3
"""
Test Results Endpoint - Verify Full Pipeline with Results Display
Tests: Upload -> Extract -> Process -> Get Results
"""

import requests
import json
import os
from pathlib import Path

BASE_URL = "http://localhost:5000/api"

def test_full_pipeline_with_results():
    """Test the complete pipeline and verify results are returned"""
    
    print("\n" + "="*80)
    print("TEST: Full Pipeline with Results Display")
    print("="*80)
    
    # Step 1: Get auth token
    print("\n[1] Getting authentication token...")
    login_response = requests.post(f"{BASE_URL}/auth/login", json={
        'username': 'regulator',
        'password': 'secure123'
    })
    
    if login_response.status_code != 200:
        print(f"✗ Login failed: {login_response.status_code}")
        return
    
    token = login_response.json().get('access_token')
    print(f"✓ Token obtained: {token[:30]}...")
    
    # Step 2: Create test PDF file
    print("\n[2] Creating sample Form 44 PDF...")
    pdf_path = "backend/uploads/test_form44_sample.pdf"
    os.makedirs("backend/uploads", exist_ok=True)
    
    # Create a simple text file as test (we'll treat it as PDF)
    form44_text = """
    FORM 44 - NOTIFICATION OF ADVERSE REACTION
    
    Drug Name: Aspirin
    Batch Number: ASP-2024-001
    Manufacturing Date: 01/15/2024
    Expiration Date: 01/15/2027
    
    Adverse Reaction: Severe gastric bleeding
    Patient Age: 65
    Patient Gender: Male
    
    Onset Date: 02/20/2024
    Duration: 3 days
    Severity: Severe
    Outcome: Hospitalized
    
    Medical History: Previous ulcers
    Concomitant Medications: Warfarin, Metformin
    
    Reporter Name: Dr. James Smith
    Reporter Phone: 555-0123
    Report Date: 02/25/2024
    """
    
    with open(pdf_path, 'w') as f:
        f.write(form44_text)
    print(f"✓ Sample Form 44 created at {pdf_path}")
    
    # Step 3: Upload file
    print("\n[3] Uploading Form 44 document...")
    headers = {'Authorization': f'Bearer {token}'}
    
    with open(pdf_path, 'rb') as f:
        files = {'file': (Path(pdf_path).name, f, 'application/pdf')}
        upload_response = requests.post(
            f"{BASE_URL}/submissions/upload",
            files=files,
            headers=headers
        )
    
    if upload_response.status_code not in [200, 201]:
        print(f"✗ Upload failed: {upload_response.status_code}")
        print(f"  Response: {upload_response.text}")
        return
    
    submission_id = upload_response.json().get('submission_id')
    print(f"✓ File uploaded successfully")
    print(f"  Submission ID: {submission_id}")
    
    # Step 4: Extract form data from PDF
    print("\n[4] Extracting Form 44 fields from PDF...")
    extract_response = requests.post(
        f"{BASE_URL}/submissions/{submission_id}/extract-form44",
        json={},
        headers=headers
    )
    
    if extract_response.status_code != 200:
        print(f"✗ Extraction failed: {extract_response.status_code}")
        print(f"  Response: {extract_response.text}")
        return
    
    extraction_result = extract_response.json()
    form44_data = extraction_result.get('form44_data', {})
    print(f"✓ Extraction completed")
    print(f"  Extracted fields: {extraction_result.get('extracted_fields', 0)}/{extraction_result.get('total_fields', 0)}")
    
    # Step 5: Process submission with extracted data
    print("\n[5] Processing submission through validators...")
    process_request = {
        'submission_data': {
            'form_data': form44_data,
            'duplicate_candidates': [],
            'md14_records': [],
            'naranjo_data': {
                'drug_name': form44_data.get('drug_name', 'Unknown'),
                'adverse_event': form44_data.get('adverse_reaction', 'Unknown'),
                'naranjo_score': 8
            }
        }
    }
    
    process_response = requests.post(
        f"{BASE_URL}/submissions/{submission_id}/process",
        json=process_request,
        headers=headers
    )
    
    if process_response.status_code != 200:
        print(f"✗ Processing failed: {process_response.status_code}")
        print(f"  Response: {process_response.text}")
        return
    
    process_result = process_response.json()
    print(f"✓ Processing completed")
    print(f"  Status: {process_result.get('processing_status', 'Unknown')}")
    print(f"  Checks performed: {len(process_result.get('checks_performed', []))}")
    
    # Step 6: Get detailed results (NEW ENDPOINT)
    print("\n[6] Retrieving detailed validation results...")
    results_response = requests.get(
        f"{BASE_URL}/submissions/{submission_id}/results",
        headers=headers
    )
    
    if results_response.status_code != 200:
        print(f"✗ Results retrieval failed: {results_response.status_code}")
        print(f"  Response: {results_response.text}")
        print("\n  NOTE: Ensure /api/submissions/{id}/results endpoint was added!")
        return
    
    results = results_response.json()
    print(f"✓ Results retrieved successfully")
    
    # Display results
    print("\n" + "-"*80)
    print("VALIDATION RESULTS SUMMARY")
    print("-"*80)
    print(f"Submission ID: {results.get('submission_id')}")
    print(f"Filename: {results.get('filename')}")
    print(f"Final Status: {results.get('status')}")
    print(f"Total Checks: {results.get('total_checks')}")
    print(f"  Passed: {results.get('checks_passed')}")
    print(f"  Failed: {results.get('checks_failed')}")
    print(f"  Skipped: {results.get('checks_skipped')}")
    
    print("\nFINDINGS:")
    for finding in results.get('findings', []):
        print(f"  • {finding}")
    
    print("\nRECOMMENDATIONS:")
    for rec in results.get('recommendations', []):
        print(f"  → {rec}")
    
    print("\nDETAILED VALIDATION RESULTS:")
    for check in results.get('validation_results', []):
        status_symbol = "✓" if check['status'] == 'PASS' else "✗" if check['status'] == 'FAIL' else "⊗"
        print(f"  {status_symbol} {check['check_type']}: {check['status']}")
        if check.get('details'):
            details_str = json.dumps(check['details'], indent=4)
            for line in details_str.split('\n')[1:-1]:  # Skip outer braces
                if line.strip():
                    print(f"      {line}")
    
    print("\n" + "="*80)
    print("TEST PASSED: Full pipeline working with results display!")
    print("="*80)

if __name__ == '__main__':
    try:
        test_full_pipeline_with_results()
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
