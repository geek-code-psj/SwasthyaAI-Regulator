"""
ADR Validator Module - Validates Adverse Drug Reaction Reports (Form 44 ADR)
This is distinct from DMF validation and tailored for adverse event submissions
"""

from typing import Dict, List
from enum import Enum


class FieldStatus(Enum):
    """Status of a field validation"""
    PASS = "pass"
    MISSING = "missing"
    INVALID = "invalid"
    INCOMPLETE = "incomplete"
    WARNING = "warning"


class ADRValidator:
    """
    Validates Form 44 ADR (Adverse Drug Reaction) submissions
    According to CDSCO adverse event reporting guidelines

    This validator is specifically for ADVERSE DRUG REACTION REPORTS,
    NOT Drug Master Files (DMF).
    """

    # Mandatory fields for ADR reports
    MANDATORY_FIELDS = {
        'drug_name': {'type': 'string', 'min_length': 2, 'required': True},
        'adverse_reaction': {'type': 'string', 'min_length': 5, 'required': True},
        'patient_age': {'type': 'int', 'min_value': 1, 'max_value': 150, 'required': True},
        'onset_date': {'type': 'string', 'pattern': r'^\d{1,2}[-/]\d{1,2}[-/]\d{2,4}$', 'required': True},
        'reporter_name': {'type': 'string', 'min_length': 3, 'required': True},
        'report_date': {'type': 'string', 'pattern': r'^\d{1,2}[-/]\d{1,2}[-/]\d{2,4}$', 'required': True},
    }

    # Highly recommended fields
    RECOMMENDED_FIELDS = {
        'severity': {'type': 'string', 'required': False},
        'outcome': {'type': 'string', 'required': False},
        'duration': {'type': 'string', 'required': False},
        'concomitant_medications': {'type': 'string', 'required': False},
    }

    # Optional fields
    OPTIONAL_FIELDS = {
        'patient_gender': {'type': 'string', 'required': False},
        'patient_weight': {'type': 'string', 'required': False},
        'medical_history': {'type': 'string', 'required': False},
        'reporter_title': {'type': 'string', 'required': False},
        'reporter_phone': {'type': 'string', 'required': False},
        'reporter_email': {'type': 'string', 'required': False},
    }

    def __init__(self):
        """Initialize ADR validator"""
        pass

    def validate_field(self, field_name: str, value, rules: Dict) -> Dict:
        """Validate a single field against rules"""

        # Check if field is present
        if value is None or (isinstance(value, str) and not value.strip()):
            if rules.get('required', False):
                return {
                    'field': field_name,
                    'status': 'missing',
                    'severity': 'critical',
                    'message': f"Mandatory field missing: {field_name}"
                }
            else:
                return {
                    'field': field_name,
                    'status': 'warning',
                    'severity': 'low',
                    'message': f"Optional field empty: {field_name}"
                }

        # Type validation
        if rules.get('type') == 'int':
            try:
                int_val = int(value) if isinstance(value, str) else value
                # Range validation
                if rules.get('min_value') and int_val < rules['min_value']:
                    return {
                        'field': field_name,
                        'status': 'invalid',
                        'severity': 'high',
                        'message': f"{field_name} must be >= {rules['min_value']}"
                    }
                if rules.get('max_value') and int_val > rules['max_value']:
                    return {
                        'field': field_name,
                        'status': 'invalid',
                        'severity': 'high',
                        'message': f"{field_name} must be <= {rules['max_value']}"
                    }
            except (ValueError, TypeError):
                return {
                    'field': field_name,
                    'status': 'invalid',
                    'severity': 'high',
                    'message': f"{field_name} must be a number"
                }

        # String validation
        if rules.get('type') == 'string':
            if not isinstance(value, str):
                value = str(value)

            # Min length validation
            if rules.get('min_length') and len(value) < rules['min_length']:
                return {
                    'field': field_name,
                    'status': 'invalid',
                    'severity': 'high',
                    'message': f"{field_name} must be at least {rules['min_length']} characters"
                }

        # All validations passed
        return {
            'field': field_name,
            'status': 'pass',
            'severity': 'none',
            'message': f"{field_name} validated successfully"
        }

    def validate_adr(self, form_data: Dict, is_batch: bool = False) -> Dict:
        """
        Validate ADR submission - STRICT MODE: Check all mandatory fields are present and valid
        
        Args:
            form_data: Dictionary with ADR form fields
            is_batch: If True, reporter_name is optional (for batch MD-14 submissions)
        """
        report = {
            'form_type': 'Form 44 - Adverse Drug Reaction Report',
            'overall_status': 'PASS',
            'completeness_score': 0.0,
            'critical_issues': [],
            'warnings': [],
            'recommendations': []
        }

        # Adjust mandatory fields for batch submissions
        mandatory_fields = dict(self.MANDATORY_FIELDS)
        if is_batch:
            # For batch submissions, reporter_name is optional
            mandatory_fields['reporter_name']['required'] = False

        # Validate each mandatory field
        critical_issues = []
        for field_name, rules in mandatory_fields.items():
            value = form_data.get(field_name)
            result = self.validate_field(field_name, value, rules)
            
            if result.get('status') == 'missing' or result.get('status') == 'invalid':
                critical_issues.append(result)
                report['critical_issues'].append(result['message'])

        # Validate recommended fields
        for field_name, rules in self.RECOMMENDED_FIELDS.items():
            value = form_data.get(field_name)
            result = self.validate_field(field_name, value, rules)
            
            if result.get('status') == 'warning':
                report['warnings'].append(result['message'])

        # Calculate completeness
        filled_fields = sum(1 for field in self.MANDATORY_FIELDS if form_data.get(field))
        total_mandatory = len(self.MANDATORY_FIELDS)
        report['completeness_score'] = round((filled_fields / total_mandatory) * 100, 1) if total_mandatory > 0 else 0

        # Determine overall status
        if critical_issues:
            report['overall_status'] = 'FAIL'
            report['recommendations'].append('Please provide all mandatory fields')
        else:
            report['overall_status'] = 'PASS'
            report['recommendations'].append(f'ADR report is valid ({report["completeness_score"]}% complete)')

        return report
