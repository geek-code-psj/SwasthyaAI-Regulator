"""
Debug test to see the actual response structure
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"

# Exact problematic data
form44_data = {
    'adverse_reaction': 'Term: Severe headache and nausea',
    'dose': '50 mg',
    'drug_name': 'Drug-X1',
    'onset_date': '26-03-10',
    'outcome': 'Recovering',
    'patient_age': '45',
    'patient_id': 'AE001',
    'report_date': '26-03-15',
    'severity': 'Moderate',
    'strength': '50 mg'
}

print("Creating test submission...")

# Upload
upload_response = requests.post(
    f"{BASE_URL}/api/submissions/upload",
    files={'file': ('test.txt', json.dumps(form44_data), 'application/json')}
)

submission_id = upload_response.json()['submission_id']
print(f"Submission ID: {submission_id}")

time.sleep(1)

# Process
print("\nProcessing...")
requests.post(
    f"{BASE_URL}/api/submissions/{submission_id}/process",
    json={'submission_data': {'form_data': form44_data}}
)

time.sleep(2)

# Get status
print("\nFetching status...")
status_response = requests.get(f"{BASE_URL}/api/submissions/{submission_id}/status")
status_data = status_response.json()

print("\n[RAW STATUS RESPONSE]")
print(json.dumps(status_data, indent=2))

# Get results
print("\n[FETCHING RESULTS]")
try:
    results_response = requests.get(f"{BASE_URL}/api/submissions/{submission_id}/results")
    if results_response.status_code == 200:
        results_data = results_response.json()
        print("[RAW RESULTS RESPONSE]")
        print(json.dumps(results_data, indent=2))
except:
    print("[Results endpoint not available]")

# Get analysis
print("\n[FETCHING ANALYSIS]")
try:
    analysis_response = requests.get(f"{BASE_URL}/api/submissions/{submission_id}/analysis")
    if analysis_response.status_code == 200:
        analysis_data = analysis_response.json()
        print("[RAW ANALYSIS RESPONSE]")
        print(json.dumps(analysis_data, indent=2))
except:
    print("[Analysis endpoint not available]")
