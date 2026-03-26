"""
Duplicate Detection Module for SwasthyaAI Regulator
Identifies duplicate submissions, drug names, applicants, and addresses
"""

import difflib
from typing import Dict, List, Tuple, Set
import re
import json

class DuplicateDetector:
    """
    Detects various types of duplicates in regulatory submissions:
    - Duplicate adverse event submissions
    - Applicant name variations
    - Drug name variations (spelling, abbreviations)
    - Same-day duplicate submissions
    - Address deduplication
    """
    
    def __init__(self, similarity_threshold: float = 0.85):
        """
        Args:
            similarity_threshold: Score (0-1) above which items are considered duplicates
        """
        self.similarity_threshold = similarity_threshold
    
    def normalize_text(self, text: str) -> str:
        """
        Normalize text for comparison:
        - Remove extra whitespace
        - Convert to lowercase
        - Remove non-alphanumeric chars (except spaces)
        """
        if not text:
            return ""
        text = text.lower().strip()
        text = re.sub(r'[^\w\s]', '', text)  # Remove special characters
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
        return text
    
    def fuzzy_match(self, str1: str, str2: str) -> float:
        """
        Calculate similarity score between two strings (0-1)
        Uses SequenceMatcher for fuzzy matching
        """
        norm1 = self.normalize_text(str1)
        norm2 = self.normalize_text(str2)
        
        if not norm1 or not norm2:
            return 0.0
        
        return difflib.SequenceMatcher(None, norm1, norm2).ratio()
    
    def detect_duplicate_drug_names(self, drug_name_1: str, drug_name_2: str) -> Dict:
        """
        Detect if two drug names refer to the same drug
        Handles: spelling variations, abbreviations, generic/brand names
        
        Examples:
            - "Investigational Drug A" vs "Inv Drug A"
            - "Acetaminophen" vs "Paracetamol"
            - "IBP 123" vs "IBP-123"
        """
        similarity = self.fuzzy_match(drug_name_1, drug_name_2)
        
        return {
            'drug_1': drug_name_1,
            'drug_2': drug_name_2,
            'similarity_score': round(similarity, 3),
            'is_duplicate': similarity >= self.similarity_threshold,
            'confidence': 'HIGH' if similarity > 0.95 else 'MEDIUM' if similarity > 0.80 else 'LOW',
            'reason': self._get_match_reason(drug_name_1, drug_name_2, similarity)
        }
    
    def detect_duplicate_applicants(self, applicant_1: Dict, applicant_2: Dict) -> Dict:
        """
        Detect same applicant with name variations
        
        Args:
            applicant_1/2: Dict with 'name', 'email', 'company', 'phone'
        
        Returns:
            Duplicate detection result
        """
        name_similarity = self.fuzzy_match(
            applicant_1.get('name', ''),
            applicant_2.get('name', '')
        )
        
        company_similarity = self.fuzzy_match(
            applicant_1.get('company', ''),
            applicant_2.get('company', '')
        )
        
        # Email exact match is strong indicator
        email_match = (applicant_1.get('email', '').lower() == 
                      applicant_2.get('email', '').lower())
        
        # Phone exact match is strong indicator
        phone_match = (applicant_1.get('phone', '') == 
                      applicant_2.get('phone', ''))
        
        combined_score = (name_similarity + company_similarity) / 2
        
        return {
            'applicant_1': applicant_1.get('name'),
            'applicant_2': applicant_2.get('name'),
            'name_similarity': round(name_similarity, 3),
            'company_similarity': round(company_similarity, 3),
            'email_match': email_match,
            'phone_match': phone_match,
            'combined_score': round(combined_score, 3),
            'is_duplicate': (combined_score >= self.similarity_threshold or 
                            email_match or phone_match),
            'confidence': 'VERY_HIGH' if (email_match or phone_match) else 'HIGH' if combined_score > 0.90 else 'MEDIUM',
            'evidence': {
                'name_variation': name_similarity > 0.75,
                'same_company': company_similarity > 0.80,
                'same_email': email_match,
                'same_phone': phone_match
            }
        }
    
    def detect_duplicate_addresses(self, address_1: str, address_2: str) -> Dict:
        """
        Detect if two addresses refer to same location
        Handles partial matches, different formats
        """
        similarity = self.fuzzy_match(address_1, address_2)
        
        # Extract postal codes
        postal_1 = re.findall(r'\b\d{5,6}\b', address_1)
        postal_2 = re.findall(r'\b\d{5,6}\b', address_2)
        
        postal_match = bool(set(postal_1) & set(postal_2))  # Intersection
        
        return {
            'address_1': address_1,
            'address_2': address_2,
            'similarity_score': round(similarity, 3),
            'postal_code_match': postal_match,
            'is_duplicate': (similarity >= self.similarity_threshold or postal_match),
            'evidence': {
                'text_similarity': similarity,
                'same_postal_code': postal_match
            }
        }
    
    def detect_same_day_duplicates(self, submissions: List[Dict]) -> List[Dict]:
        """
        Detect submissions from same applicant/company on same day
        (Strong indicator of accidental duplicate submission)
        """
        # Group by submission date and applicant
        from collections import defaultdict
        from datetime import datetime
        
        grouped = defaultdict(list)
        duplicates = []
        
        for submission in submissions:
            date_key = submission.get('created_date', '')
            applicant_key = self.normalize_text(submission.get('applicant_name', ''))
            key = (date_key, applicant_key)
            grouped[key].append(submission)
        
        # Find groups with 2+ submissions on same day
        for key, subs in grouped.items():
            if len(subs) > 1:
                for i in range(len(subs) - 1):
                    duplicates.append({
                        'submission_1_id': subs[i].get('id'),
                        'submission_2_id': subs[i+1].get('id'),
                        'applicant': subs[i].get('applicant_name'),
                        'date': key[0],
                        'type': 'SAME_DAY_DUPLICATE',
                        'severity': 'HIGH',
                        'action': 'FLAG_FOR_REVIEW',
                        'evidence': {
                            'same_applicant': True,
                            'same_date': True,
                            'drug_count_diff': abs(
                                len(subs[i].get('drugs', [])) - 
                                len(subs[i+1].get('drugs', []))
                            )
                        }
                    })
        
        return duplicates
    
    def batch_detect_duplicates(self, submissions: List[Dict]) -> Dict:
        """
        Run all duplicate detection checks across all submissions
        
        Returns comprehensive duplicate report
        """
        report = {
            'total_submissions': len(submissions),
            'duplicate_drug_names': [],
            'duplicate_applicants': [],
            'same_day_duplicates': [],
            'summary': {
                'critical_issues': 0,
                'high_priority_issues': 0,
                'medium_priority_issues': 0,
                'recommendations': []
            }
        }
        
        # Check drug names across all submissions
        drugs = set()
        for sub in submissions:
            for drug in sub.get('drugs', []):
                for existing_drug in drugs:
                    match = self.detect_duplicate_drug_names(drug, existing_drug)
                    if match['is_duplicate']:
                        report['duplicate_drug_names'].append(match)
                        report['summary']['high_priority_issues'] += 1
                drugs.add(drug)
        
        # Check applicants
        applicants = []
        for sub in submissions:
            applicant = {
                'name': sub.get('applicant_name'),
                'email': sub.get('applicant_email', ''),
                'company': sub.get('company', ''),
                'phone': sub.get('phone', '')
            }
            for existing_applicant in applicants:
                match = self.detect_duplicate_applicants(applicant, existing_applicant)
                if match['is_duplicate']:
                    report['duplicate_applicants'].append(match)
                    report['summary']['critical_issues'] += 1
            applicants.append(applicant)
        
        # Check same-day duplicates
        report['same_day_duplicates'] = self.detect_same_day_duplicates(submissions)
        report['summary']['critical_issues'] += len(report['same_day_duplicates'])
        
        # Generate recommendations
        if report['summary']['critical_issues'] > 0:
            report['summary']['recommendations'].append(
                "CRITICAL: Review flagged duplicate submissions before processing"
            )
        if report['duplicate_applicants']:
            report['summary']['recommendations'].append(
                "Consolidate applicant records to prevent fraud/manipulation"
            )
        if report['same_day_duplicates']:
            report['summary']['recommendations'].append(
                "Contact applicants to clarify multiple same-day submissions"
            )
        
        return report
    
    @staticmethod
    def _get_match_reason(str1: str, str2: str, similarity: float) -> str:
        """Helper to explain why strings matched"""
        if similarity > 0.98:
            return "Near-identical strings"
        elif similarity > 0.90:
            return "Minor spelling/formatting differences"
        elif similarity > 0.80:
            return "Likely same drug with major variations"
        else:
            return f"Possible match (similarity: {similarity:.1%})"


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == '__main__':
    detector = DuplicateDetector(similarity_threshold=0.85)
    
    # Example 1: Drug name variations
    print("Example 1: Drug Name Duplicates")
    print("-" * 60)
    print(detector.detect_duplicate_drug_names(
        "Investigational Drug X",
        "Inv. Drug X"
    ))
    print()
    
    # Example 2: Applicant duplicates
    print("Example 2: Applicant Duplicates")
    print("-" * 60)
    print(json.dumps(detector.detect_duplicate_applicants(
        {
            'name': 'Dr. Raj Kumar Singh',
            'email': 'raj.kumar@pharma.com',
            'company': 'Pharma Solutions Inc.',
            'phone': '9876543210'
        },
        {
            'name': 'Raj Kumar Singh',
            'email': 'raj.kumar@pharma.com',
            'company': 'Pharma Solutions',
            'phone': '9876543210'
        }
    ), indent=2))
    print()
    
    # Example 3: Batch detection
    print("Example 3: Batch Duplicate Detection")
    print("-" * 60)
    test_submissions = [
        {
            'id': 'SUB-001',
            'applicant_name': 'Dr. Raj Kumar',
            'applicant_email': 'raj@pharma.com',
            'company': 'Pharma Solutions',
            'phone': '9876543210',
            'created_date': '2024-01-15',
            'drugs': ['Drug A', 'Drug B']
        },
        {
            'id': 'SUB-002',
            'applicant_name': 'Raj Kumar',
            'applicant_email': 'raj@pharma.com',
            'company': 'Pharma Solutions Inc',
            'phone': '9876543210',
            'created_date': '2024-01-15',
            'drugs': ['Drug A', 'Drug C']
        }
    ]
    
    print(json.dumps(detector.batch_detect_duplicates(test_submissions), indent=2))
