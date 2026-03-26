"""Full integration test simulating user journey"""
import requests
import json
import time
from colorama import init, Fore, Style

init(autoreset=True)
BASE_URL = "http://localhost:5000"

def simulate_user_journey():
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"USER JOURNEY TEST - Full Processing Pipeline")
    print(f"{'='*70}{Style.RESET_ALL}\n")
    
    # 1. AUTHENTICATION
    print(f"{Fore.BLUE}[Step 1] User authenticates...{Style.RESET_ALL}")
    try:
        auth_response = requests.post(f"{BASE_URL}/api/auth/token", json={'username': 'test_user'})
        if auth_response.status_code != 200:
            print(f"{Fore.RED}✗ Auth failed: {auth_response.text}")
            return False
        token = auth_response.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        print(f"{Fore.GREEN}✓ Authenticated successfully{Style.RESET_ALL}\n")
    except Exception as e:
        print(f"{Fore.RED}✗ Connection error: {e}")
        return False
    
    # 2. UPLOAD DOCUMENT
    print(f"{Fore.BLUE}[Step 2] User uploads document...{Style.RESET_ALL}")
    try:
        files = {'file': ('form44.pdf', b'Form 44 Test Document')}
        upload_response = requests.post(
            f"{BASE_URL}/api/submissions/upload",
            files=files,
            headers=headers
        )
        if upload_response.status_code != 200:
            print(f"{Fore.RED}✗ Upload failed: {upload_response.text}")
            return False
        
        submission_data = upload_response.json()
        submission_id = submission_data['submission_id']
        print(f"{Fore.GREEN}✓ Document uploaded{Style.RESET_ALL}")
        print(f"  Submission ID: {submission_id}")
        print(f"  Initial Status: {submission_data['status']}\n")
    except Exception as e:
        print(f"{Fore.RED}✗ Upload error: {e}")
        return False
    
    # 3. CHECK INITIAL STATUS
    print(f"{Fore.BLUE}[Step 3] Checking initial status...{Style.RESET_ALL}")
    try:
        status_response = requests.get(
            f"{BASE_URL}/api/submissions/{submission_id}/status",
            headers=headers
        )
        initial_status = status_response.json()['status']
        print(f"{Fore.GREEN}✓ Status check successful{Style.RESET_ALL}")
        print(f"  Current Status: {initial_status}\n")
    except Exception as e:
        print(f"{Fore.RED}✗ Status check error: {e}")
        return False
    
    # 4. TRIGGER PROCESSING
    print(f"{Fore.BLUE}[Step 4] User clicks 'Process Now'...{Style.RESET_ALL}")
    try:
        process_response = requests.post(
            f"{BASE_URL}/api/submissions/{submission_id}/process",
            json={'submission_data': {}},
            headers=headers
        )
        if process_response.status_code != 200:
            print(f"{Fore.RED}✗ Processing failed: {process_response.text}")
            return False
        
        process_data = process_response.json()
        final_status = process_data.get('processing_status', 'unknown')
        
        print(f"{Fore.GREEN}✓ Processing completed{Style.RESET_ALL}")
        print(f"  Final Status: {final_status}")
        
        # Show stage progression
        print(f"\n{Fore.YELLOW}  Stage Progression:{Style.RESET_ALL}")
        stages = process_data.get('stage_progression', [])
        for i, stage in enumerate(stages):
            progress = int((i + 1) / len(stages) * 100)
            marker = "→" if i < len(stages) - 1 else "✓"
            print(f"    {marker} {stage:30} ({progress}%)")
        
        # Show validation results
        print(f"\n{Fore.YELLOW}  Validation Results:{Style.RESET_ALL}")
        checks = process_data.get('checks_performed', [])
        for check in checks:
            status_code = check.get('status', 'UNKNOWN')
            check_type = check.get('type', 'Unknown')
            
            if status_code == 'PASS':
                symbol = f"{Fore.GREEN}✓{Style.RESET_ALL}"
            elif status_code == 'FAIL':
                symbol = f"{Fore.RED}✗{Style.RESET_ALL}"
            elif status_code == 'SKIPPED':
                symbol = f"{Fore.YELLOW}⊘{Style.RESET_ALL}"
            else:
                symbol = f"{Fore.YELLOW}?{Style.RESET_ALL}"
            
            print(f"    {symbol} {check_type:30} -> {status_code}")
        
        # Critical issues
        if process_data.get('critical_issues'):
            print(f"\n{Fore.RED}  Critical Issues:{Style.RESET_ALL}")
            for issue in process_data['critical_issues']:
                print(f"    • {issue}")
        
        print()
        
    except Exception as e:
        print(f"{Fore.RED}✗ Processing error: {e}")
        return False
    
    # 5. VERIFY FINAL STATUS
    print(f"{Fore.BLUE}[Step 5] Verifying final status in database...{Style.RESET_ALL}")
    try:
        final_status_response = requests.get(
            f"{BASE_URL}/api/submissions/{submission_id}/status",
            headers=headers
        )
        db_status = final_status_response.json()['status']
        print(f"{Fore.GREEN}✓ Final verification{Style.RESET_ALL}")
        print(f"  Database Status: {db_status}")
        print(f"  Response Status: {final_status}")
        print(f"  Match: {'✓ YES' if db_status == final_status else '✗ NO'}\n")
    except Exception as e:
        print(f"{Fore.RED}✗ Verification error: {e}")
        return False
    
    # RESULTS SUMMARY
    print(f"{Fore.CYAN}{'='*70}")
    if final_status == 'completed':
        print(f"{Fore.GREEN}✓ SUCCESS - Processing completed all validations{Style.RESET_ALL}")
    elif final_status == 'failed':
        print(f"{Fore.YELLOW}⚠ VALIDATION FAILED - Some checks did not pass{Style.RESET_ALL}")
        print(f"  User should review the critical issues above")
    else:
        print(f"{Fore.RED}✗ UNKNOWN STATUS - {final_status}{Style.RESET_ALL}")
    print(f"{'='*70}{Style.RESET_ALL}\n")
    
    return True

if __name__ == '__main__':
    success = simulate_user_journey()
    exit(0 if success else 1)
