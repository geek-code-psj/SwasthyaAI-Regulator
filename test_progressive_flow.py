"""Test progressive status updates in processing pipeline"""
import requests
import json
import time
from colorama import init, Fore, Style

init(autoreset=True)
BASE_URL = "http://localhost:5000"

def test_progressive_processing():
    """Test that processing updates status progressively"""
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"Test: Progressive Status Updates During Processing")
    print(f"{'='*60}{Style.RESET_ALL}\n")
    
    # 1. Get auth token
    print(f"{Fore.BLUE}1. Getting auth token...{Style.RESET_ALL}")
    auth_response = requests.post(f"{BASE_URL}/api/auth/token")
    if auth_response.status_code != 200:
        print(f"{Fore.RED}✗ Failed to get auth token: {auth_response.text}")
        return
    
    token = auth_response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    print(f"{Fore.GREEN}✓ Got auth token{Style.RESET_ALL}")
    
    # 2. Create a test submission
    print(f"\n{Fore.BLUE}2. Creating test submission...{Style.RESET_ALL}")
    files = {'file': ('test.txt', b'Test document content')}
    upload_response = requests.post(
        f"{BASE_URL}/api/submissions/upload",
        files=files,
        headers=headers
    )
    if upload_response.status_code != 200:
        print(f"{Fore.RED}✗ Failed to upload: {upload_response.text}")
        return
    
    submission_id = upload_response.json()['submission_id']
    print(f"{Fore.GREEN}✓ Created submission: {submission_id}{Style.RESET_ALL}")
    
    # 3. Trigger processing
    print(f"\n{Fore.BLUE}3. Starting processing...{Style.RESET_ALL}")
    process_response = requests.post(
        f"{BASE_URL}/api/submissions/{submission_id}/process",
        json={'submission_data': {}},
        headers=headers
    )
    if process_response.status_code != 200:
        print(f"{Fore.RED}✗ Failed to process: {process_response.text}")
        return
    
    print(f"{Fore.GREEN}✓ Processing response received{Style.RESET_ALL}")
    
    # 4. Display stage progression from response
    process_data = process_response.json()
    print(f"\n{Fore.YELLOW}Processing stages completed:{Style.RESET_ALL}")
    if 'stage_progression' in process_data:
        for i, stage in enumerate(process_data['stage_progression']):
            progress = (i + 1) / len(process_data['stage_progression']) * 100
            print(f"  {i+1}. {stage:30} ({progress:.0f}%)")
    
    # 5. Check final status
    final_status = process_data.get('processing_status', 'unknown')
    final_report = process_data.get('overall_status', 'UNKNOWN')
    print(f"\n{Fore.YELLOW}Final Result:{Style.RESET_ALL}")
    print(f"  Status: {final_status}")
    print(f"  Overall: {final_report}")
    
    # 6. Display checks performed
    print(f"\n{Fore.YELLOW}Validation Checks:{Style.RESET_ALL}")
    for check in process_data.get('checks_performed', []):
        status_color = Fore.GREEN if check.get('status') == 'PASS' else Fore.RED if check.get('status') == 'FAIL' else Fore.YELLOW
        print(f"  {status_color}✓ {check.get('type'):30} -> {check.get('status')}{Style.RESET_ALL}")
    
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"Test Complete!")
    print(f"{'='*60}{Style.RESET_ALL}\n")

if __name__ == '__main__':
    try:
        test_progressive_processing()
    except Exception as e:
        print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
