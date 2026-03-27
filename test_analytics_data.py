#!/usr/bin/env python
"""Quick test to populate analytics with sample data"""

import requests
import json
import time

BASE_URL = 'http://localhost:5000'

# Sample Form 44 (ADR) data
sample_form44 = """
FORM - 44
Adverse Event Report

ReportID: REP-2026-001
PatientName: John Doe
Age: 45
Gender: Male
ReportedDate: 15-03-2026

DrugName: Aspirin
DoseForm: Tablet
Strength: 500mg
Route: Oral
Frequency: Twice Daily
Duration: 30 days

AdverseEvent: Severe Headache
EventOnsetDate: 20-02-2026
Severity: Severe
Outcome: Recovered
Concomitant: Paracetamol

ReporterName: Dr. Smith
ReporterContact: smith@hospital.com
"""

# Sample MD-14 (Medical Device) data
sample_md14 = """
MD-14 Form

DeviceID: DEV-2026-001
DeviceName: Blood Pressure Monitor
Manufacturer: MediTech Inc
Batch: BT202601

IncidentDate: 18-03-2026
IncidentType: Device Malfunction
Severity: Moderate
Outcome: No Patient Impact

Description: Device showed inconsistent readings
PatientsAffected: 1
ReporterName: Dr. Johnson
ReporterContact: johnson@clinic.com
"""

print("[TEST] Populating analytics with sample submissions...")

# Create test submissions
submissions = [
    ("form44_test1.txt", sample_form44, "Form44"),
    ("md14_test1.txt", sample_md14, "MD14"),
]

for filename, content, form_type in submissions:
    try:
        # Upload file
        files = {'file': (filename, content)}
        data = {'submission_type': form_type}
        
        upload_response = requests.post(
            f'{BASE_URL}/api/submissions/upload',
            files=files,
            data=data,
            headers={'Accept': 'application/json'}
        )
        
        if upload_response.status_code == 200:
            result = upload_response.json()
            submission_id = result.get('submission_id')
            print(f"✓ Uploaded {filename}: {submission_id}")
            
            # Wait a moment for processing
            time.sleep(1)
            
            # Process the submission
            process_response = requests.post(
                f'{BASE_URL}/api/submissions/{submission_id}/process',
                headers={'Accept': 'application/json'}
            )
            
            if process_response.status_code == 200:
                print(f"✓ Processed {filename}")
            else:
                print(f"✗ Failed to process {filename}: {process_response.status_code}")
                print(f"  Response: {process_response.text}")
        else:
            print(f"✗ Failed to upload {filename}: {upload_response.status_code}")
            print(f"  Response: {upload_response.text}")
            
    except Exception as e:
        print(f"✗ Error with {filename}: {e}")

# Check analytics after submissions
time.sleep(2)
print("\n[TEST] Checking analytics data...")

analytics_endpoints = [
    '/api/analytics/summary',
    '/api/analytics/top-adverse-events',
    '/api/analytics/form-types'
]

for endpoint in analytics_endpoints:
    try:
        response = requests.get(f'{BASE_URL}{endpoint}')
        if response.status_code == 200:
            data = response.json()
            print(f"\n{endpoint}:")
            print(json.dumps(data, indent=2))
        else:
            print(f"\n✗ {endpoint}: {response.status_code}")
    except Exception as e:
        print(f"\n✗ {endpoint}: {e}")

print("\n[TEST] Complete!")
