"""
Debug MD-14 batch submission
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"

# Upload MD-14 batch
print("Uploading MD-14 batch file...")

md14_batch_file = 'tests/fixtures/TEST_MD14_CORRECTED_BATCH.txt'

with open(md14_batch_file, 'r') as f:
    batch_content = f.read()

upload_resp = requests.post(
    f"{BASE_URL}/api/submissions/upload",
    files={'file': ('md14_batch.txt', batch_content, 'text/plain')}
)

print(f"Upload response: {upload_resp.status_code}")
submission_id = upload_resp.json()['submission_id']
print(f"Submission ID: {submission_id}")

time.sleep(1)

# Try to extract MD-14
print("\nExtracting MD-14 records...")
extract_resp = requests.post(f"{BASE_URL}/api/submissions/{submission_id}/extract-md14")
print(f"Extract response: {extract_resp.status_code}")
print(f"Extract content: {extract_resp.text[:500] if extract_resp.text else '(empty)'}")

time.sleep(1)

# Process
print("\nProcessing submission...")
process_resp = requests.post(
    f"{BASE_URL}/api/submissions/{submission_id}/process",
    json={'submission_data': {}}
)
print(f"Process response: {process_resp.status_code}")

time.sleep(2)

# Get status
print("\nGetting status...")
status_resp = requests.get(f"{BASE_URL}/api/submissions/{submission_id}/status")
print(f"Status response: {status_resp.status_code}")
status = status_resp.json()

print("\nStatus data:")
print(json.dumps(status, indent=2))
