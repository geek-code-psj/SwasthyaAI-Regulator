"""
Consistency Checker Module for SwasthyaAI Regulator
Detects data inconsistencies and logical errors in regulatory submissions
"""

from typing import Dict, List, Tuple
from datetime import datetime
import json

class ConsistencyChecker:
    """
    Validates internal consistency of data across submission fields
    Detects logical conflicts, impossible values, and contradictions
    """
    
    def __init__(self):
        self.issues = []
    
    def check_date_consistency(self, 
                              treatment_date: str, 
                              event_date: str,
                              dechallenge_date: str = None) -> Dict:
        """
        Check temporal consistency of dates
        
        Rules:
        - Adverse event must occur on or after treatment start
        - Dechallenge must occur after event date
        - Temporal relationships must be logical
        """
        issues = []
        
        try:
            # Parse dates (assuming YYYY-MM-DD format)
            treat_dt = datetime.strptime(treatment_date, '%Y-%m-%d') if treatment_date else None
            event_dt = datetime.strptime(event_date, '%Y-%m-%d') if event_date else None
            dechall_dt = datetime.strptime(dechallenge_date, '%Y-%m-%d') if dechallenge_date else None
            
            # Event must be after/on treatment start
            if treat_dt and event_dt and event_dt < treat_dt:
                issues.append({
                    'type': 'TEMPORAL_ERROR',
                    'severity': 'CRITICAL',
                    'message': f"Adverse event ({event_date}) occurred BEFORE treatment started ({treatment_date})",
                    'action': 'VERIFY_DATES',
                    'suggestion': 'Check submission for correct event onset date'
                })
            
            # Reasonable onset window (typically 1 hour to several years)
            if treat_dt and event_dt:
                days_to_onset = (event_dt - treat_dt).days
                hours_to_onset = days_to_onset * 24
                
                if hours_to_onset < 0:
                    issues.append({
                        'type': 'IMPOSSIBLE_ONSET',
                        'severity': 'CRITICAL',
                        'message': 'Event occurred before treatment initiation',
                        'action': 'FLAG_FOR_REVIEW'
                    })
                elif hours_to_onset > (365 * 10):  # More than 10 years
                    issues.append({
                        'type': 'IMPLAUSIBLE_ONSET',
                        'severity': 'MEDIUM',
                        'message': f'Very delayed onset ({days_to_onset} days) - verify causality documentation',
                        'action': 'REQUEST_ADDITIONAL_INFO'
                    })
            
            # Dechallenge before event is impossible
            if dechall_dt and event_dt and dechall_dt < event_dt:
                issues.append({
                    'type': 'IMPOSSIBLE_DECHALLENGE',
                    'severity': 'CRITICAL',
                    'message': 'Dechallenge date before event occurred - logically impossible',
                    'action': 'FLAG_FOR_REVIEW'
                })
            
            # Dechallenge should occur within reasonable time (usually days to weeks)
            if event_dt and dechall_dt:
                dechall_days = (dechall_dt - event_dt).days
                if dechall_days > 365:
                    issues.append({
                        'type': 'DELAYED_DECHALLENGE',
                        'severity': 'HIGH',
                        'message': f'Dechallenge {dechall_days} days after event - verify accuracy',
                        'action': 'REQUEST_CLARIFICATION'
                    })
            
        except ValueError as e:
            issues.append({
                'type': 'DATE_FORMAT_ERROR',
                'severity': 'HIGH',
                'message': f'Invalid date format: {str(e)}',
                'action': 'REQUIRE_CORRECTION'
            })
        
        return {
            'type': 'DATE_CONSISTENCY_CHECK',
            'treatment_date': treatment_date,
            'event_date': event_date,
            'dechallenge_date': dechallenge_date,
            'issues': issues,
            'status': 'PASS' if not issues else 'FAIL'
        }
    
    def check_age_consistency(self, age: int, date_of_birth: str = None, 
                             age_unit: str = 'years') -> Dict:
        """
        Check age consistency and validity
        
        Rules:
        - Age must be non-negative
        - Age must be physically possible (< 150 years)
        - If DOB provided, age must match
        """
        issues = []
        
        try:
            age_int = int(age) if isinstance(age, str) else age
            
            if age_int < 0:
                issues.append({
                    'type': 'NEGATIVE_AGE',
                    'severity': 'CRITICAL',
                    'message': 'Patient age cannot be negative',
                    'action': 'REQUIRE_CORRECTION'
                })
            
            if age_int > 150:
                issues.append({
                    'type': 'IMPOSSIBLE_AGE',
                    'severity': 'HIGH',
                    'message': f'Age {age_int} exceeds realistic lifespan',
                    'action': 'VERIFY_AGE'
                })
            
            # Check age units
            if age_unit.lower() not in ['years', 'months', 'days', 'weeks']:
                issues.append({
                    'type': 'INVALID_AGE_UNIT',
                    'severity': 'HIGH',
                    'message': f'Invalid age unit: {age_unit}',
                    'action': 'CLARIFY_UNIT'
                })
            
            # If DOB provided, calculate and verify
            if date_of_birth:
                try:
                    dob = datetime.strptime(date_of_birth, '%Y-%m-%d')
                    calculated_age = (datetime.now() - dob).days / 365.25
                    
                    if abs(age_int - calculated_age) > 1:  # Allow 1-year discrepancy
                        issues.append({
                            'type': 'AGE_DOB_MISMATCH',
                            'severity': 'HIGH',
                            'message': f'Reported age ({age_int}) does not match DOB (calculated: {int(calculated_age)})',
                            'action': 'VERIFY_DATA'
                        })
                except ValueError:
                    issues.append({
                        'type': 'INVALID_DOB_FORMAT',
                        'severity': 'HIGH',
                        'message': 'Invalid date of birth format (use YYYY-MM-DD)',
                        'action': 'CORRECT_FORMAT'
                    })
        
        except (ValueError, TypeError):
            issues.append({
                'type': 'INVALID_AGE_FORMAT',
                'severity': 'HIGH',
                'message': 'Age must be a valid number',
                'action': 'REQUIRE_CORRECTION'
            })
        
        return {
            'type': 'AGE_CONSISTENCY_CHECK',
            'age': age,
            'age_unit': age_unit,
            'dob': date_of_birth,
            'issues': issues,
            'status': 'PASS' if not issues else 'FAIL'
        }
    
    def check_dose_consistency(self, dose: str, frequency: str, duration_days: int,
                              total_expected_dose: float = None) -> Dict:
        """
        Check dose consistency and cumulative exposure
        
        Rules:
        - Dose must be positive
        - Frequency must be valid
        - Cumulative dose should be reasonable
        """
        issues = []
        
        # Parse dose (e.g., "500mg", "2 tablets", "0.5 units/kg")
        try:
            # Extract numeric value
            dose_value = float(''.join(c for c in dose.split()[0] if c.isdigit() or c == '.'))
            
            if dose_value <= 0:
                issues.append({
                    'type': 'INVALID_DOSE',
                    'severity': 'CRITICAL',
                    'message': 'Dose must be positive',
                    'action': 'REQUIRE_CORRECTION'
                })
            
            # Check frequency validity
            valid_frequencies = ['once daily', 'twice daily', 'three times daily', 'once weekly', 
                               'twice weekly', 'once every 12 hours', 'once monthly', 'as needed']
            
            if not any(vf in frequency.lower() for vf in valid_frequencies):
                issues.append({
                    'type': 'UNCLEAR_FREQUENCY',
                    'severity': 'HIGH',
                    'message': f'Frequency unclear: {frequency}',
                    'action': 'CLARIFY_DOSING_SCHEDULE'
                })
            
            # Calculate cumulative if possible
            if duration_days and dose_value > 0:
                # Simple estimate: assume 1x daily default
                freq_multiplier = 1
                if 'twice' in frequency.lower():
                    freq_multiplier = 2
                elif 'three' in frequency.lower():
                    freq_multiplier = 3
                elif 'weekly' in frequency.lower():
                    freq_multiplier = 1/7
                
                cumulative = dose_value * freq_multiplier * duration_days
                
                if cumulative > 100000:  # Arbitrary high threshold
                    issues.append({
                        'type': 'HIGH_CUMULATIVE_DOSE',
                        'severity': 'MEDIUM',
                        'message': f'High cumulative dose ({cumulative} units over {duration_days} days)',
                        'action': 'VERIFY_DOSING',
                        'cumulative_dose': cumulative
                    })
        
        except (ValueError, IndexError):
            issues.append({
                'type': 'INVALID_DOSE_FORMAT',
                'severity': 'HIGH',
                'message': f'Cannot parse dose: {dose}',
                'action': 'STANDARDIZE_FORMAT'
            })
        
        return {
            'type': 'DOSE_CONSISTENCY_CHECK',
            'dose': dose,
            'frequency': frequency,
            'duration_days': duration_days,
            'issues': issues,
            'status': 'PASS' if not issues else 'FAIL'
        }
    
    def check_naranjo_consistency(self, naranjo_score: int, dechallenge_response: bool,
                                 rechallenge_response: bool) -> Dict:
        """
        Check Naranjo scoring consistency with supporting evidence
        
        Rules:
        - High scores should have strong evidence
        - Dechallenge/rechallenge improve score credibility
        """
        issues = []
        
        if not (0 <= naranjo_score <= 13):
            issues.append({
                'type': 'INVALID_NARANJO_SCORE',
                'severity': 'CRITICAL',
                'message': 'Naranjo score must be between 0 and 13',
                'action': 'RECALCULATE_SCORE'
            })
        
        # Check for weak evidence at high scores
        if naranjo_score >= 9:  # Definitive
            if not dechallenge_response and not rechallenge_response:
                issues.append({
                    'type': 'WEAK_EVIDENCE_HIGH_SCORE',
                    'severity': 'HIGH',
                    'message': 'Score of Definitive (≥9) without dechallenge/rechallenge data',
                    'action': 'REQUEST_ADDITIONAL_EVIDENCE'
                })
        
        # Check for strong evidence at low scores
        if naranjo_score <= 2:  # Doubtful
            if dechallenge_response and rechallenge_response:
                issues.append({
                    'type': 'INCONSISTENT_EVIDENCE',
                    'severity': 'MEDIUM',
                    'message': 'Strong evidence (dechallenge + rechallenge) but score is Doubtful',
                    'action': 'REVIEW_SCORING'
                })
        
        return {
            'type': 'NARANJO_CONSISTENCY_CHECK',
            'naranjo_score': naranjo_score,
            'dechallenge': dechallenge_response,
            'rechallenge': rechallenge_response,
            'issues': issues,
            'status': 'PASS' if not issues else 'FAIL'
        }
    
    def check_gender_consistency(self, gender: str, pregnancy_status: str = None) -> Dict:
        """
        Check gender-specific consistency
        """
        issues = []
        
        valid_genders = ['M', 'F', 'Male', 'Female', 'Other', 'Not specified']
        
        if gender not in valid_genders:
            issues.append({
                'type': 'INVALID_GENDER',
                'severity': 'HIGH',
                'message': f'Invalid gender value: {gender}',
                'action': 'STANDARDIZE_VALUE'
            })
        
        # Check pregnancy status for male patients
        if gender in ['M', 'Male'] and pregnancy_status and pregnancy_status.lower() != 'not applicable':
            issues.append({
                'type': 'IMPOSSIBLE_STATE',
                'severity': 'CRITICAL',
                'message': 'Male patient reported as pregnant - data error',
                'action': 'VERIFY_GENDER_AND_PREGNANCY'
            })
        
        return {
            'type': 'GENDER_CONSISTENCY_CHECK',
            'gender': gender,
            'pregnancy_status': pregnancy_status,
            'issues': issues,
            'status': 'PASS' if not issues else 'FAIL'
        }
    
    def comprehensive_check(self, submission: Dict) -> Dict:
        """
        Run all consistency checks on a submission
        """
        report = {
            'submission_id': submission.get('id'),
            'timestamp': datetime.now().isoformat(),
            'all_checks': [],
            'critical_issues': [],
            'high_priority_issues': [],
            'overall_status': 'PASS',
            'summary': []
        }
        
        # Run date consistency checks
        if all(k in submission for k in ['treatment_start_date', 'event_onset_date']):
            date_check = self.check_date_consistency(
                submission['treatment_start_date'],
                submission['event_onset_date'],
                submission.get('dechallenge_date')
            )
            report['all_checks'].append(date_check)
        
        # Run age checks
        if 'patient_age' in submission:
            age_check = self.check_age_consistency(
                submission['patient_age'],
                submission.get('date_of_birth'),
                submission.get('age_unit', 'years')
            )
            report['all_checks'].append(age_check)
        
        # Run dose checks
        if all(k in submission for k in ['dose', 'frequency', 'duration_days']):
            dose_check = self.check_dose_consistency(
                submission['dose'],
                submission['frequency'],
                submission['duration_days']
            )
            report['all_checks'].append(dose_check)
        
        # Run Naranjo consistency
        if 'naranjo_score' in submission:
            naranjo_check = self.check_naranjo_consistency(
                submission['naranjo_score'],
                submission.get('dechallenge_response', False),
                submission.get('rechallenge_response', False)
            )
            report['all_checks'].append(naranjo_check)
        
        # Run gender checks
        if 'patient_gender' in submission:
            gender_check = self.check_gender_consistency(
                submission['patient_gender'],
                submission.get('pregnancy_status')
            )
            report['all_checks'].append(gender_check)
        
        # Aggregate issues
        for check in report['all_checks']:
            for issue in check.get('issues', []):
                if issue['severity'] == 'CRITICAL':
                    report['critical_issues'].append(issue)
                    report['overall_status'] = 'FAIL'
                elif issue['severity'] == 'HIGH':
                    report['high_priority_issues'].append(issue)
                    if report['overall_status'] != 'FAIL':
                        report['overall_status'] = 'NEEDS_REVIEW'
        
        # Generate summary
        if report['critical_issues']:
            report['summary'].append(f"CRITICAL: {len(report['critical_issues'])} critical issues found")
        if report['high_priority_issues']:
            report['summary'].append(f"HIGH: {len(report['high_priority_issues'])} high-priority issues")
        
        if not report['critical_issues'] and not report['high_priority_issues']:
            report['summary'].append("All consistency checks passed")
        
        return report


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == '__main__':
    checker = ConsistencyChecker()
    
    # Example submission with inconsistencies
    test_submission = {
        'id': 'SUB-001',
        'patient_age': 45,
        'patient_gender': 'M',
        'date_of_birth': '1979-01-15',
        'pregnancy_status': 'Not applicable',
        'treatment_start_date': '2024-01-10',
        'event_onset_date': '2024-01-08',  # Before treatment - ERROR!
        'dechallenge_date': '2024-01-15',
        'dose': '500mg',
        'frequency': 'twice daily',
        'duration_days': 30,
        'naranjo_score': 11,  # High score
        'dechallenge_response': False,
        'rechallenge_response': False  # Weak evidence for high score
    }
    
    result = checker.comprehensive_check(test_submission)
    print(json.dumps(result, indent=2))
