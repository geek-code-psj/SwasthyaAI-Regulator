#!/usr/bin/env python3
"""
End-to-End Test: MD-14 Batch Submission with Full Validation Pipeline
Tests the complete system with the corrected batch data (5 cases)
"""

import requests
import json
import time
import sys

BASE_URL = "http://localhost:5000/api"

def print_header(title):
    """Print formatted header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")

def print_section(title):
    """Print formatted section"""
    print(f"\n[{title}]")
    print("-" * 80)

def format_json(data):
    """Pretty print JSON"""
    return json.dumps(data, indent=2)

def test_submission_creation():
    """Step 1: Directly upload MD-14 batch file (returns submission_id)"""
    print_section("STEP 1: Upload MD-14 Batch File")
    
    try:
        file_path = 'tests/fixtures/TEST_MD14_CORRECTED_BATCH.txt'
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                f'{BASE_URL}/submissions/upload',
                files=files
            )
        
        if response.status_code == 200:
            result = response.json()
            submission_id = result.get('submission_id')
            print(f"[SUCCESS] File uploaded")
            print(f"  Submission ID: {submission_id}")
            print(f"  File name: {result.get('filename')}")
            print(f"  Status: {result.get('status')}")
            return submission_id
        else:
            print(f"[ERROR] Upload failed: {response.status_code}")
            print(response.text[:300])
            return None
    except Exception as e:
        print(f"[ERROR] Upload error: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_md14_extraction(submission_id):
    """Step 2: Extract MD-14 records"""
    print_section("STEP 2: Extract MD-14 Records from Batch")
    
    if not submission_id:
        print("[ERROR] No submission ID")
        return None
    
    try:
        response = requests.post(
            f'{BASE_URL}/submissions/{submission_id}/extract-md14'
        )
        
        if response.status_code == 200:
            result = response.json()
            records = result.get('md14_records', [])
            print(f"[SUCCESS] Extracted {len(records)} MD-14 records\n")
            
            # Display each record
            for i, record in enumerate(records, 1):
                print(f"Record {i}: Case ID {record.get('case_id')}")
                print(f"  Patient: Age {record.get('patient_age')}, Gender {record.get('patient_gender')}")
                print(f"  Adverse Event: {record.get('adverse_event_term')}")
                print(f"  Severity: {record.get('event_severity')} | Outcome: {record.get('outcome')}")
                print(f"  Drug: {record.get('drug_name')} ({record.get('dose')})")
                print(f"  Dechallenge: {record.get('dechallenge_performed')}")
                print(f"  Onset: {record.get('event_onset_date')} | Report: {record.get('report_date')}")
                print()
            
            return records
        else:
            print(f"[ERROR] Extraction failed: {response.status_code}")
            print(response.text[:200])
            return None
    except Exception as e:
        print(f"[ERROR] Extraction error: {e}")
        return None

def test_md14_validation(submission_id, md14_records):
    """Step 3: Validate MD-14 batch"""
    print_section("STEP 3: Validate MD-14 Batch")
    
    if not submission_id or not md14_records:
        print("[ERROR] Missing submission ID or records")
        return None
    
    try:
        data = {'submission_data': {'md14_records': md14_records}}
        response = requests.post(
            f'{BASE_URL}/submissions/{submission_id}/process',
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"[SUCCESS] Process completed\n")
            
            # Extract validation results
            checks = result.get('checks_performed', [])
            print(f"Validation Checks Performed: {len(checks)}\n")
            
            for check in checks:
                check_type = check.get('type')
                status = check.get('status')
                status_icon = "[PASS]" if status == 'PASS' else "[FAIL]" if status == 'FAIL' else "[INFO]"
                
                print(f"{status_icon} {check_type}: {status}")
                
                if check.get('critical_issues'):
                    for issue in check['critical_issues']:
                        print(f"       - {issue}")
                
                if check.get('data_quality_score') is not None:
                    print(f"       Data Quality: {check['data_quality_score']}%")
                
                if check.get('records_validated'):
                    print(f"       Records Validated: {check['records_validated']}")
            
            print(f"\nOverall Status: {result.get('overall_status')}")
            return result
        else:
            print(f"[ERROR] Processing failed: {response.status_code}")
            print(response.text[:300])
            return None
    except Exception as e:
        print(f"[ERROR] Processing error: {e}")
        return None

def test_summary(result):
    """Display test summary"""
    if not result:
        print("\n[ERROR] No results to summarize")
        return
    
    print_section("TEST SUMMARY")
    
    checks = result.get('checks_performed', [])
    overall = result.get('overall_status')
    
    print(f"Overall Status: {overall}")
    print(f"Total Checks: {len(checks)}\n")
    
    # Count results
    passed = sum(1 for c in checks if c.get('status') == 'PASS')
    failed = sum(1 for c in checks if c.get('status') == 'FAIL')
    
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if result.get('critical_issues'):
        print(f"\nCritical Issues: {len(result['critical_issues'])}")
        for issue in result['critical_issues']:
            print(f"  - {issue}")
    
    print("\n" + "="*80)
    if overall == 'PASS':
        print("  [SUCCESS] All validations PASSED!")
    else:
        print("  [WARNING] Some validations need review")
    print("="*80)

def main():
    """Run complete test pipeline"""
    print_header("END-TO-END TEST: MD-14 Batch Submission with Validation")
    print("Testing SwasthyaAI Regulator with 5-case corrected batch\n")
    
    # Step 1: Upload file (creates submission)
    submission_id = test_submission_creation()
    if not submission_id:
        print("\n[ABORT] Failed to upload file and create submission")
        sys.exit(1)
    
    # Small delay
    time.sleep(0.5)
    
    # Step 2: Extract records
    md14_records = test_md14_extraction(submission_id)
    if not md14_records:
        print("\n[ABORT] Failed to extract records")
        sys.exit(1)
    
    # Small delay
    time.sleep(0.5)
    
    # Step 3: Process and validate
    result = test_md14_validation(submission_id, md14_records)
    if not result:
        print("\n[ABORT] Failed to process submission")
        sys.exit(1)
    
    # Display summary
    test_summary(result)
    
    # Final status
    print("\n[COMPLETE] End-to-end test finished successfully!")
    sys.exit(0)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Test stopped by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
