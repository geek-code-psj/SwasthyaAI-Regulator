"""Test processing with valid Form 44 data"""
import requests
import json
from colorama import init, Fore, Style

init(autoreset=True)
BASE_URL = "http://localhost:5000"

def test_with_valid_data():
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"TEST: Processing with VALID Form 44 Data")
    print(f"{'='*70}{Style.RESET_ALL}\n")
    
    # 1. Authenticate
    print(f"{Fore.BLUE}[Step 1] Getting auth token...{Style.RESET_ALL}")
    auth_response = requests.post(f"{BASE_URL}/api/auth/token", json={'username': 'test_user'})
    token = auth_response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    print(f"{Fore.GREEN}✓ Authenticated{Style.RESET_ALL}\n")
    
    # 2. Upload
    print(f"{Fore.BLUE}[Step 2] Uploading document...{Style.RESET_ALL}")
    files = {'file': ('form44_valid.pdf', b'Valid Form 44 Document')}
    upload_response = requests.post(
        f"{BASE_URL}/api/submissions/upload",
        files=files,
        headers=headers
    )
    submission_id = upload_response.json()['submission_id']
    print(f"{Fore.GREEN}✓ Uploaded: {submission_id}{Style.RESET_ALL}\n")
    
    # 3. Process WITH VALID FORM DATA
    print(f"{Fore.BLUE}[Step 3] Processing with valid Form 44 data...{Style.RESET_ALL}")
    
    # Create valid form data matching Form44Validator requirements
    valid_form_data = {
        # Section 1: Applicant Information
        'applicant_name': 'PharmaCorp India Pvt Ltd',
        'applicant_address': '123 Medical Street, Bangalore, India - 560001',
        'applicant_phone': '9876543210',
        'applicant_email': 'contact@pharmacorp.com',
        'drug_name': 'Aspirin',
        'drug_code': 'ASP-001',
        
        # Section 2: Drug Information
        'drug_strength': '500mg',
        'dosage_form': 'Tablet',
        'route_of_administration': 'Oral',
        'manufacturing_process': 'Synthesized through acetylation of salicylic acid using acetic anhydride in controlled conditions. Quality control at each step ensures purity.',
        
        # Section 3: Preclinical & Stability
        'clinical_data_available': True,
        'animal_toxicity_data': True,
        'stability_data': '24 months',
        'retest_period': '24 months',
        
        # Section 4: Safety & Efficacy
        'adverse_events_reported': False,
        'safety_database_size': 5000,
        'serious_adverse_events': 2,
        'contraindications': 'Hypersensitivity to salicylates or NSAIDs. Do not use in patients with active gastrointestinal bleeding.',
        'precautions': 'Use with caution in patients with renal impairment or gastrointestinal ulcers. Monitor for signs of bleeding.'
    }
    
    process_response = requests.post(
        f"{BASE_URL}/api/submissions/{submission_id}/process",
        json={'submission_data': {'form_data': valid_form_data}},
        headers=headers
    )
    
    process_data = process_response.json()
    final_status = process_data.get('processing_status', 'unknown')
    
    print(f"{Fore.GREEN}✓ Processing complete{Style.RESET_ALL}\n")
    
    # Display results
    print(f"{Fore.YELLOW}Results:{Style.RESET_ALL}")
    print(f"  Final Status: {final_status}")
    
    print(f"\n{Fore.YELLOW}Stage Progression:{Style.RESET_ALL}")
    for i, stage in enumerate(process_data.get('stage_progression', [])):
        progress = int((i + 1) / len(process_data.get('stage_progression', [])) * 100)
        print(f"  → {stage:30} ({progress}%)")
    
    print(f"\n{Fore.YELLOW}Validation Checks:{Style.RESET_ALL}")
    for check in process_data.get('checks_performed', []):
        status = check.get('status', 'UNKNOWN')
        check_type = check.get('type', 'Unknown')
        
        if status == 'PASS':
            symbol = f"{Fore.GREEN}✓{Style.RESET_ALL}"
        elif status == 'FAIL':
            symbol = f"{Fore.RED}✗{Style.RESET_ALL}"
        elif status == 'SKIPPED':
            symbol = f"{Fore.YELLOW}⊘{Style.RESET_ALL}"
        else:
            symbol = "?"
        
        print(f"  {symbol} {check_type:30} -> {status}")
    
    # Result summary
    print(f"\n{Fore.CYAN}{'='*70}")
    if final_status == 'completed':
        print(f"{Fore.GREEN}✓✓✓ SUCCESS! All validations passed! ✓✓✓{Style.RESET_ALL}")
        print(f"\nThe submission is now ready for regulatory review.")
    else:
        print(f"{Fore.YELLOW}⚠ Validation Failed{Style.RESET_ALL}")
        if process_data.get('critical_issues'):
            print(f"\n{Fore.RED}Issues:{Style.RESET_ALL}")
            for issue in process_data['critical_issues']:
                print(f"  • {issue}")
    print(f"{'='*70}{Style.RESET_ALL}\n")

if __name__ == '__main__':
    test_with_valid_data()
