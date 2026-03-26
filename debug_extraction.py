#!/usr/bin/env python3
"""
Debug PDF Extraction - Check what text is being extracted
"""

import requests
import json
import os
from pathlib import Path

BASE_URL = "http://localhost:5000/api"

def debug_extraction():
    """Debug the extraction process"""
    
    print("\n" + "="*80)
    print("DEBUG: PDF Extraction Process")
    print("="*80)
    
    # Authenticate
    login_response = requests.post(f"{BASE_URL}/auth/login", json={
        'username': 'regulator',
        'password': 'secure123'
    })
    
    token = login_response.json().get('access_token')
    headers = {'Authorization': f'Bearer {token}'}
    
    # Create test PDF with clear content
    pdf_path = "backend/uploads/debug_form44.pdf"
    os.makedirs("backend/uploads", exist_ok=True)
    
    form44_text = """FORM 44 - NOTIFICATION OF ADVERSE REACTION

Drug Name: Paracetamol
Batch Number: PAR-2024-15423
Manufacturing Date: 15/01/2024
Expiration Date: 14/01/2027
Strength: 500mg

Patient Age: 45
Patient Gender: Female
Patient Weight: 65 kg

Adverse Reaction: Severe hepatic toxicity
Date of Onset: 22/02/2024
Duration: 7 days
Severity: Severe
Outcome: Hospitalized
"""
    
    with open(pdf_path, 'w') as f:
        f.write(form44_text)
    print(f"✓ Created debug Form 44 file")
    print(f"  Content preview:\n{form44_text[:200]}...")
    
    # Upload file
    with open(pdf_path, 'rb') as f:
        files = {'file': (Path(pdf_path).name, f)}
        upload_response = requests.post(
            f"{BASE_URL}/submissions/upload",
            files=files,
            headers=headers
        )
    
    submission_id = upload_response.json().get('submission_id')
    print(f"\n✓ File uploaded: {submission_id}")
    
    # Extract
    extract_response = requests.post(
        f"{BASE_URL}/submissions/{submission_id}/extract-form44",
        json={},
        headers=headers
    )
    
    if extract_response.status_code != 200:
        print(f"✗ Extraction failed: {extract_response.status_code}")
        print(f"  Error: {extract_response.text}")
        return
    
    result = extract_response.json()
    
    print(f"\n[EXTRACTION RESULTS]")
    print(f"  Extracted fields: {result.get('extracted_fields')}/{result.get('total_fields')}")
    print(f"  Quality: {result.get('extraction_quality')}")
    print(f"  Message: {result.get('message')}")
    
    print(f"\n[EXTRACTED TEXT PREVIEW]")
    preview = result.get('extracted_text_preview', '')
    print(f"  Preview length: {len(preview)} chars")
    print(f"  Preview:\n{preview}")
    
    print(f"\n[FORM 44 DATA EXTRACTED]")
    form44_data = result.get('form44_data', {})
    print(f"  Total keys in dict: {len(form44_data)}")
    print(f"  Non-empty values: {sum(1 for v in form44_data.values() if v)}")
    
    print(f"\n[EXTRACTED FIELDS]")
    for key, value in form44_data.items():
        if value:
            print(f"  ✓ {key}: {value}")
    
    empty_fields = [k for k, v in form44_data.items() if not v]
    if empty_fields:
        print(f"\n[EMPTY FIELDS]")
        for field in empty_fields[:10]:
            print(f"  □ {field}")

if __name__ == '__main__':
    try:
        debug_extraction()
    except Exception as e:
        print(f"\n✗ Debug failed: {e}")
        import traceback
        traceback.print_exc()
