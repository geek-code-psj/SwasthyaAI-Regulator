"""
Field Validator Module for SwasthyaAI Regulator
Validates Form 44 and MD-14 completeness and mandatory field requirements
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import re

class FieldStatus(Enum):
    """Status of a field validation"""
    PASS = "pass"
    MISSING = "missing"
    INVALID = "invalid"
    INCOMPLETE = "incomplete"
    WARNING = "warning"

@dataclass
class FieldValidation:
    """Result of a single field validation"""
    field_name: str
    status: FieldStatus
    message: str
    severity: str  # 'critical', 'high', 'medium', 'low'
    suggestion: str = None

class Form44Validator:
    """
    Validates Form 44 (Drug Master File - DMF) submissions
    According to CDSCO guidelines
    """
    
    # Mandatory fields in Form 44
    SECTION_1_FIELDS = {
        'applicant_name': {'type': 'string', 'min_length': 5},
        'applicant_address': {'type': 'string', 'min_length': 10},
        'applicant_phone': {'type': 'string', 'pattern': r'^\d{10}$'},
        'applicant_email': {'type': 'string', 'pattern': r'^[\w\.-]+@[\w\.-]+\.\w+$'},
        'drug_name': {'type': 'string', 'min_length': 3},
        'drug_code': {'type': 'string', 'min_length': 3}
    }
    
    SECTION_2_FIELDS = {
        'drug_strength': {'type': 'string', 'required': True},
        'dosage_form': {'type': 'string', 'enum': ['Tablet', 'Capsule', 'Solution', 'Suspension', 'Powder', 'Injection', 'Other']},
        'route_of_administration': {'type': 'string', 'enum': ['Oral', 'IV', 'IM', 'SC', 'Topical', 'Inhalation', 'Other']},
        'manufacturing_process': {'type': 'string', 'min_length': 50}
    }
    
    SECTION_3_FIELDS = {
        'clinical_data_available': {'type': 'boolean', 'required': True},
        'animal_toxicity_data': {'type': 'boolean', 'required': True},
        'stability_data': {'type': 'string', 'enum': ['12 months', '18 months', '24 months', '36 months']},
        'retest_period': {'type': 'string', 'min_length': 5}
    }
    
    SECTION_4_FIELDS = {
        'adverse_events_reported': {'type': 'boolean', 'required': True},
        'safety_database_size': {'type': 'integer', 'min_value': 0},
        'serious_adverse_events': {'type': 'integer', 'min_value': 0},
        'contraindications': {'type': 'string', 'min_length': 10},
        'precautions': {'type': 'string', 'min_length': 10}
    }
    
    def __init__(self):
        self.all_fields = {
            'Section 1: Applicant Information': self.SECTION_1_FIELDS,
            'Section 2: Drug Information': self.SECTION_2_FIELDS,
            'Section 3: Preclinical & Stability': self.SECTION_3_FIELDS,
            'Section 4: Safety & Efficacy': self.SECTION_4_FIELDS
        }
    
    def validate_field(self, field_name: str, value: any, rules: Dict) -> FieldValidation:
        """Validate a single field against rules"""
        
        # Check if field is present
        if value is None or (isinstance(value, str) and not value.strip()):
            if rules.get('required', True):
                return FieldValidation(
                    field_name=field_name,
                    status=FieldStatus.MISSING,
                    message=f"Mandatory field missing: {field_name}",
                    severity='critical',
                    suggestion=f"Provide {field_name}"
                )
            else:
                return FieldValidation(
                    field_name=field_name,
                    status=FieldStatus.WARNING,
                    message=f"Optional field empty: {field_name}",
                    severity='low'
                )
        
        # Type validation
        if rules.get('type'):
            expected_type = rules['type']
            if expected_type == 'string' and not isinstance(value, str):
                return FieldValidation(
                    field_name=field_name,
                    status=FieldStatus.INVALID,
                    message=f"{field_name} must be text, got {type(value).__name__}",
                    severity='high'
                )
            elif expected_type == 'integer' and not isinstance(value, int):
                return FieldValidation(
                    field_name=field_name,
                    status=FieldStatus.INVALID,
                    message=f"{field_name} must be number, got {type(value).__name__}",
                    severity='high'
                )
            elif expected_type == 'boolean' and not isinstance(value, bool):
                return FieldValidation(
                    field_name=field_name,
                    status=FieldStatus.INVALID,
                    message=f"{field_name} must be yes/no, got {value}",
                    severity='high'
                )
        
        # Length validation
        if isinstance(value, str):
            if rules.get('min_length') and len(value) < rules['min_length']:
                return FieldValidation(
                    field_name=field_name,
                    status=FieldStatus.INCOMPLETE,
                    message=f"{field_name} too short (min: {rules['min_length']} chars)",
                    severity='medium',
                    suggestion=f"Expand description to at least {rules['min_length']} characters"
                )
        
        # Enum validation
        if rules.get('enum'):
            if value not in rules['enum']:
                return FieldValidation(
                    field_name=field_name,
                    status=FieldStatus.INVALID,
                    message=f"{field_name} must be one of: {', '.join(rules['enum'])}",
                    severity='high',
                    suggestion=f"Select from: {', '.join(rules['enum'])}"
                )
        
        # Pattern (regex) validation
        if rules.get('pattern'):
            import re
            if not re.match(rules['pattern'], str(value)):
                return FieldValidation(
                    field_name=field_name,
                    status=FieldStatus.INVALID,
                    message=f"{field_name} format incorrect",
                    severity='high',
                    suggestion=f"Check {field_name} format"
                )
        
        # Value range validation
        if isinstance(value, (int, float)):
            if rules.get('min_value') is not None and value < rules['min_value']:
                return FieldValidation(
                    field_name=field_name,
                    status=FieldStatus.INVALID,
                    message=f"{field_name} must be >= {rules['min_value']}",
                    severity='high'
                )
        
        # All validations passed
        return FieldValidation(
            field_name=field_name,
            status=FieldStatus.PASS,
            message=f"{field_name} validated",
            severity='none'
        )
    
    def validate_form44(self, form_data: Dict) -> Dict:
        """
        Validate complete Form 44 submission
        
        Args:
            form_data: Dictionary with form fields
        
        Returns:
            Validation report with field-by-field results
        """
        report = {
            'form_type': 'Form 44 - Drug Master File',
            'overall_status': 'PASS',
            'completeness_score': 0.0,
            'sections': {},
            'critical_issues': [],
            'high_priority_issues': [],
            'medium_priority_issues': [],
            'recommendations': []
        }
        
        total_fields = 0
        passed_fields = 0
        
        # Validate each section
        for section_name, fields in self.all_fields.items():
            section_result = {
                'status': 'PASS',
                'fields': []
            }
            
            for field_name, rules in fields.items():
                total_fields += 1
                value = form_data.get(field_name)
                
                validation = self.validate_field(field_name, value, rules)
                
                section_result['fields'].append({
                    'field_name': field_name,
                    'status': validation.status.value,
                    'message': validation.message,
                    'severity': validation.severity,
                    'suggestion': validation.suggestion
                })
                
                # Track issues
                if validation.status == FieldStatus.PASS:
                    passed_fields += 1
                elif validation.severity == 'critical':
                    report['critical_issues'].append(validation.message)
                    section_result['status'] = 'FAIL'
                elif validation.severity == 'high':
                    report['high_priority_issues'].append(validation.message)
                    section_result['status'] = 'INCOMPLETE'
                elif validation.severity == 'medium':
                    report['medium_priority_issues'].append(validation.message)
                
                # Add suggestion if provided
                if validation.suggestion:
                    report['recommendations'].append({
                        'field': field_name,
                        'action': validation.suggestion
                    })
            
            report['sections'][section_name] = section_result
            
            # Section-level status
            if section_result['status'] == 'FAIL':
                report['overall_status'] = 'FAIL'
            elif report['overall_status'] == 'PASS' and section_result['status'] == 'INCOMPLETE':
                report['overall_status'] = 'INCOMPLETE'
        
        # Calculate completeness score
        report['completeness_score'] = round((passed_fields / total_fields) * 100, 1) if total_fields > 0 else 0
        
        # Set overall status based on completeness
        if report['critical_issues']:
            report['overall_status'] = 'FAIL'
        elif report['completeness_score'] < 80:
            report['overall_status'] = 'INCOMPLETE'
        elif report['high_priority_issues']:
            report['overall_status'] = 'NEEDS_REVIEW'
        else:
            report['overall_status'] = 'PASS'
        
        return report


class MD14Validator:
    """
    Validates MD-14 (Line Listing of Adverse Events) submissions
    FLEXIBLE MODE: Accepts multiple date formats, normalizes enum values
    """
    
    REQUIRED_FIELDS = {
        'case_id': {'type': 'string', 'min_length': 3},
        'patient_age': {'type': 'integer', 'min_value': 0, 'max_value': 150},
        'patient_gender': {'type': 'string', 'enum': ['M', 'F', 'Other']},
        'adverse_event_term': {'type': 'string', 'min_length': 5},
        'event_onset_date': {'type': 'date', 'formats': [r'^\d{4}-\d{2}-\d{2}$', r'^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$']},
        'event_severity': {'type': 'string', 'enum': ['Mild', 'Moderate', 'Severe', 'Life-threatening', 'Fatal']},
        'outcome': {'type': 'string', 'enum': ['Recovered', 'Recovering', 'Not Recovered', 'Fatal', 'Unknown']},
        'drug_name': {'type': 'string', 'min_length': 3},
        'dose': {'type': 'string', 'min_length': 2},
        'dechallenge_performed': {'type': 'boolean'},
        'report_date': {'type': 'date', 'formats': [r'^\d{4}-\d{2}-\d{2}$', r'^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$']}
    }
    
    def __init__(self):
        pass
    
    @staticmethod
    def is_valid_date(date_str, formats=None):
        """
        Check if string matches any date format pattern
        Flexible: accepts YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY, etc.
        """
        if not date_str or not isinstance(date_str, str):
            return False
        
        if formats is None:
            # Default flexible date matching
            formats = [
                r'^\d{4}-\d{2}-\d{2}$',      # YYYY-MM-DD
                r'^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$',  # DD/MM/YYYY or MM/DD/YYYY
            ]
        
        for pattern in formats:
            if re.match(pattern, date_str.strip()):
                return True
        return False
    
    @staticmethod
    def normalize_enum_value(value, enum_options):
        """
        Normalize enum value - try exact match, then case-insensitive, then substring
        """
        if not value:
            return None
        
        value_str = str(value).strip()
        
        # Exact match
        if value_str in enum_options:
            return value_str
        
        # Case-insensitive match
        for option in enum_options:
            if option.lower() == value_str.lower():
                return option
        
        # Substring match (first word of value matches option)
        words = value_str.split()
        if words:
            for word in words:
                for option in enum_options:
                    if word.lower() == option.lower():
                        return option
        
        # Return original if no match (will fail validation separately)
        return None
    
    def validate_md14_record(self, record: Dict) -> Dict:
        """
        Validate a single MD-14 record (adverse event line item)
        FLEXIBLE: Handles multiple formats, normalizes values
        """
        result = {
            'case_id': record.get('case_id'),
            'valid': True,
            'errors': [],
            'warnings': [],
            'data_quality_score': 0.0
        }
        
        valid_fields = 0
        
        for field, rules in self.REQUIRED_FIELDS.items():
            value = record.get(field)
            
            # Boolean fields: accept True/False or truthy/falsy values
            if rules.get('type') == 'boolean':
                if value is not None:  # Boolean can be True or False, just needs to exist
                    valid_fields += 1
                else:
                    result['valid'] = False
                    result['errors'].append(f"Missing mandatory field: {field}")
                continue
            
            # Basic presence check for non-boolean fields
            if not value:
                result['valid'] = False
                result['errors'].append(f"Missing mandatory field: {field}")
                continue
            
            # Type validation for integers
            if rules.get('type') == 'integer':
                try:
                    int_val = int(value)
                    if rules.get('min_value') is not None and int_val < rules['min_value']:
                        result['valid'] = False
                        result['errors'].append(f"{field} must be >= {rules['min_value']}")
                    elif rules.get('max_value') is not None and int_val > rules['max_value']:
                        result['valid'] = False
                        result['errors'].append(f"{field} must be <= {rules['max_value']}")
                    else:
                        valid_fields += 1
                except (ValueError, TypeError):
                    result['valid'] = False
                    result['errors'].append(f"{field} must be a number (got: {value})")
            
            # Enum validation - FLEXIBLE with normalization
            elif rules.get('enum'):
                normalized = self.normalize_enum_value(value, rules['enum'])
                if normalized:
                    valid_fields += 1
                else:
                    result['valid'] = False
                    result['errors'].append(f"{field} must be one of: {', '.join(rules['enum'])} (got: {value})")
            
            # Date format validation - FLEXIBLE with multiple formats
            elif rules.get('type') == 'date':
                formats = rules.get('formats', [r'^\d{4}-\d{2}-\d{2}$', r'^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$'])
                if self.is_valid_date(str(value), formats):
                    valid_fields += 1
                else:
                    result['valid'] = False
                    result['errors'].append(f"{field} must be a valid date format (got: {value})")
            
            else:
                valid_fields += 1
        
        # Calculate data quality
        result['data_quality_score'] = round((valid_fields / len(self.REQUIRED_FIELDS)) * 100, 1)
        
        # Add warnings for edge cases
        if record.get('event_severity') == 'Fatal' and record.get('outcome') != 'Fatal':
            result['warnings'].append("Fatal severity recorded but outcome is not Fatal - verify consistency")
        
        if record.get('dechallenge_performed') and not record.get('dechallenge_response'):
            result['warnings'].append("Dechallenge performed but no response documented")
        
        return result
    
    def validate_md14_batch(self, records: List[Dict]) -> Dict:
        """
        Validate multiple MD-14 records - STRICT MODE
        """
        report = {
            'form_type': 'MD-14 - Line Listing of Adverse Events',
            'total_records': len(records),
            'valid_records': 0,
            'invalid_records': 0,
            'overall_data_quality': 0.0,
            'overall_status': 'FAIL',  # Default FAIL, only PASS if valid
            'records': [],
            'summary': {
                'most_common_ae': '',
                'severity_distribution': {},
                'outcome_distribution': {},
                'critical_safety_signals': []
            }
        }
        
        # Empty records = FAIL
        if not records:
            return report
        
        quality_scores = []
        adverse_events = {}
        severities = {}
        outcomes = {}
        
        for record in records:
            validation = self.validate_md14_record(record)
            report['records'].append(validation)
            
            if validation['valid']:
                report['valid_records'] += 1
            else:
                report['invalid_records'] += 1
            
            quality_scores.append(validation['data_quality_score'])
            
            # Stats collection
            ae = record.get('adverse_event_term', 'Unknown')
            adverse_events[ae] = adverse_events.get(ae, 0) + 1
            
            severity = record.get('event_severity', 'Unknown')
            severities[severity] = severities.get(severity, 0) + 1
            
            outcome = record.get('outcome', 'Unknown')
            outcomes[outcome] = outcomes.get(outcome, 0) + 1
        
        # Calculate overall quality
        report['overall_data_quality'] = round(sum(quality_scores) / len(quality_scores), 1) if quality_scores else 0
        
        # Generate summary
        if adverse_events:
            report['summary']['most_common_ae'] = max(adverse_events, key=adverse_events.get)
        
        report['summary']['severity_distribution'] = severities
        report['summary']['outcome_distribution'] = outcomes
        
        # STRICT: Pass/Fail based on valid record percentage
        valid_percentage = (report['valid_records'] / report['total_records'] * 100) if report['total_records'] > 0 else 0
        
        if valid_percentage >= 60:  # At least 60% of records must be valid
            report['overall_status'] = 'PASS'
        else:
            report['overall_status'] = 'FAIL'
        
        return report


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == '__main__':
    # Example Form 44 validation
    print("=" * 70)
    print("Form 44 Validation Example")
    print("=" * 70)
    
    validator_44 = Form44Validator()
    
    test_form_44 = {
        'applicant_name': 'Dr. Raj Kumar Singh',
        'applicant_address': '123 Pharma Street, Delhi, India 110001',
        'applicant_phone': '9876543210',
        'applicant_email': 'raj@pharma.com',
        'drug_name': 'Investigational Drug X',
        'drug_code': 'IDX-001',
        'drug_strength': '500mg',
        'dosage_form': 'Tablet',
        'route_of_administration': 'Oral',
        'manufacturing_process': 'Detailed manufacturing process description...',
        'clinical_data_available': True,
        'animal_toxicity_data': True,
        'stability_data': '24 months',
        'retest_period': '12 months',
        'adverse_events_reported': True,
        'safety_database_size': 500,
        'serious_adverse_events': 5,
        'contraindications': 'Pregnancy, lactation, renal impairment',
        'precautions': 'Monitor liver function, avoid with CYP3A4 inhibitors'
    }
    
    result_44 = validator_44.validate_form44(test_form_44)
    print(json.dumps(result_44, indent=2))
    
    # Example MD-14 validation
    print("\n" + "=" * 70)
    print("MD-14 Validation Example")
    print("=" * 70)
    
    validator_14 = MD14Validator()
    
    test_md14_records = [
        {
            'case_id': 'CASE-001',
            'patient_age': 45,
            'patient_gender': 'M',
            'adverse_event_term': 'Severe neutropenia',
            'event_onset_date': '2024-01-15',
            'event_severity': 'Severe',
            'outcome': 'Recovered',
            'drug_name': 'Drug A',
            'dose': '500mg daily',
            'dechallenge_performed': True,
            'dechallenge_response': 'Improved',
            'report_date': '2024-01-20'
        }
    ]
    
    result_14 = validator_14.validate_md14_batch(test_md14_records)
    print(json.dumps(result_14, indent=2))
