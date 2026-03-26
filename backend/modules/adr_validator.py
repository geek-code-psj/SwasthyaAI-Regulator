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

    def validate_adr(self, form_data: Dict) -> Dict:
        """
        Validate complete ADR submission

        Args:
            form_data: Dictionary with form fields

        Returns:
            Validation report with field-by-field results
        """
        report = {
            'form_type': 'Form 44 - Adverse Drug Reaction Report',
            'overall_status': 'PASS',
            'completeness_score': 0.0,
            'mandatory_fields_status': [],
            'recommended_fields_status': [],
            'optional_fields_status': [],
            'critical_issues': [],
            'high_priority_issues': [],
            'medium_priority_issues': [],
            'recommendations': []
        }

        # Validate mandatory fields
        mandatory_passed = 0
        mandatory_total = len(self.MANDATORY_FIELDS)

        for field_name, rules in self.MANDATORY_FIELDS.items():
            value = form_data.get(field_name)
            validation = self.validate_field(field_name, value, rules)

            report['mandatory_fields_status'].append(validation)

            if validation['status'] == 'pass':
                mandatory_passed += 1
            elif validation['severity'] == 'critical':
                report['critical_issues'].append(validation['message'])
                report['overall_status'] = 'FAIL'
            elif validation['severity'] == 'high':
                report['high_priority_issues'].append(validation['message'])

        # Validate recommended fields
        recommended_passed = 0
        recommended_total = len(self.RECOMMENDED_FIELDS)

        for field_name, rules in self.RECOMMENDED_FIELDS.items():
            value = form_data.get(field_name)
            validation = self.validate_field(field_name, value, rules)

            report['recommended_fields_status'].append(validation)

            if validation['status'] == 'pass':
                recommended_passed += 1

        # Validate optional fields
        optional_passed = 0
        optional_total = len(self.OPTIONAL_FIELDS)

        for field_name, rules in self.OPTIONAL_FIELDS.items():
            value = form_data.get(field_name)
            validation = self.validate_field(field_name, value, rules)

            report['optional_fields_status'].append(validation)

            if validation['status'] == 'pass':
                optional_passed += 1

        # Calculate completeness score (weighted)
        # Mandatory: 70%, Recommended: 20%, Optional: 10%
        if mandatory_total > 0:
            mandatory_score = (mandatory_passed / mandatory_total) * 70
        else:
            mandatory_score = 0

        if recommended_total > 0:
            recommended_score = (recommended_passed / recommended_total) * 20
        else:
            recommended_score = 0

        if optional_total > 0:
            optional_score = (optional_passed / optional_total) * 10
        else:
            optional_score = 0

        report['completeness_score'] = round(
            mandatory_score + recommended_score + optional_score, 1
        )

        # Set recommendations
        if mandatory_passed < mandatory_total:
            missing_mandatory = [
                f['field'] for f in report['mandatory_fields_status']
                if f['status'] != 'pass'
            ]
            report['recommendations'].append(
                f"Complete mandatory fields: {', '.join(missing_mandatory[:3])}"
            )

        if report['completeness_score'] >= 90:
            report['recommendations'].append("ADR report is complete and ready for review")
        elif report['completeness_score'] >= 70:
            report['recommendations'].append(
                f"ADR report is {report['completeness_score']}% complete. Add recommended fields if possible."
            )
        else:
            report['recommendations'].append("Critical fields missing. Cannot process without mandatory information.")

        return report
