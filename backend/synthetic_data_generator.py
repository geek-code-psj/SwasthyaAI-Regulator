"""
Synthetic Data Generator for SwasthyaAI Regulator
Generates 100+ realistic SAE narratives, Form 44 samples, and inspection notes
Used for demo/testing when real CDSCO data unavailable

CDSCO Requirement: System must work with messy, real-world data
"""

import json
import random
from datetime import datetime, timedelta
from typing import List, Dict

class SyntheticDataGenerator:
    """Generate realistic but fake regulatory data"""
    
    def __init__(self):
        self.first_names = [
            "Ramesh", "Priya", "Arjun", "Meera", "Rohan", "Anjali", "Vikram", "Deepa",
            "Aditya", "Neha", "Sanjay", "Pooja", "Rajesh", "Shruti", "Nikhil", "Isha"
        ]
        self.last_names = [
            "Yadav", "Sharma", "Patel", "Kumar", "Singh", "Khan", "Gupta", "Verma",
            "Reddy", "Desai", "Nair", "Iyer", "Mishra", "Chopra", "Bhat", "Saxena"
        ]
        
        self.cities = {
            "Delhi": "NCR Region, India",
            "Gurgaon": "NCR Region, India",
            "Mumbai": "Western Region, India",
            "Bangalore": "Southern Region, India",
            "Hyderabad": "South-Central Region, India",
            "Kolkata": "Eastern Region, India",
        }
        
        self.hospitals = {
            "AIIMS New Delhi": "Tier-1 Public Hospital",
            "Max Super Specialty": "Tier-3 Private Hospital",
            "Apollo Hospital": "Tier-3 Private Hospital",
            "Fortis Healthcare": "Tier-3 Private Hospital",
            "Government Medical College": "Tier-2 Government Hospital",
        }
        
        self.event_terms = [
            ("Acute Myocardial Infarction", "10002681", 5),  # event, meddra, ctcae
            ("Anaphylaxis", "10002198", 4),
            ("Severe Hepatotoxicity", "10061254", 3),
            ("Stevens-Johnson Syndrome", "10042316", 4),
            ("Acute Kidney Injury", "10001041", 3),
            ("Cerebral Hemorrhage", "10008190", 5),
            ("Septic Shock", "10040560", 4),
            ("Acute Respiratory Distress", "10001052", 4),
        ]
        
        self.medications = [
            "Investigational Drug A (IND-2024-001)",
            "Investigational Drug B (IND-2024-002)",
            "Investigational Drug C (IND-2024-003)",
            "Novel Immunotherapy (MOA-2024-001)",
            "Biologic Agent (BIO-2024-001)",
        ]
    
    def generate_patient_record(self) -> Dict:
        """Generate synthetic patient demographics"""
        return {
            "patient_name": f"{random.choice(self.first_names)} {random.choice(self.last_names)}",
            "age": random.randint(18, 75),
            "gender": random.choice(["M", "F"]),
            "aadhaar": f"{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}",
            "phone": f"9{random.randint(100000000, 999999999)}",
            "address": f"House {random.randint(1, 100)}, {random.choice(list(self.cities.keys()))}, India",
        }
    
    def generate_sae_narrative(self, patient: Dict) -> Dict:
        """Generate synthetic SAE case narrative"""
        event_term, meddra_code, ctcae_grade = random.choice(self.event_terms)
        onset_days = random.randint(1, 30)
        medication = random.choice(self.medications)
        hospital = random.choice(list(self.hospitals.keys()))
        
        # Synthetic narrative
        narratives = [
            f"Patient {patient['patient_name']}, {patient['age']}-year-old {patient['gender']}, "
            f"enrolled in Phase III trial of {medication}. "
            f"Event ({event_term}) occurred {onset_days} days post-dose. "
            f"Clinical presentation: Severe symptoms requiring {random.choice(['hospitalization', 'ICU admission', 'urgent intervention'])}. "
            f"Management at {hospital}. Outcome: {random.choice(['Recovered', 'Ongoing', 'Fatal'])}.",
            
            f"{event_term} reported in {patient['age']}-year-old receiving {medication} ({onset_days} days from second dose). "
            f"Medical history: {random.choice(['Hypertension', 'Diabetes', 'Asthma', 'No significant PMH'])}. "
            f"Temporal relationship strong. Similar cases reported in literature.",
            
            f"Serious adverse event: {event_term}. Patient: {patient['patient_name']} ({patient['age']} yrs). "
            f"Trial drug: {medication}. Duration to event: {onset_days} days. "
            f"Treated at {hospital}. De-challenge status: {random.choice(['Not applicable - fatal', 'Drug continued', 'Drug stopped, symptoms resolved'])}.",
        ]
        
        return {
            "case_id": f"CASE_2024_{random.randint(1, 999):03d}",
            "patient_name": patient['patient_name'],
            "patient_age": patient['age'],
            "event_term_raw": event_term,
            "event_term_meddra": event_term,
            "meddra_code": meddra_code,
            "ctcae_grade": ctcae_grade,
            "onset_days": onset_days,
            "medication": medication,
            "hospital": hospital,
            "narrative": random.choice(narratives),
            "outcome": random.choice(["FATAL", "RECOVERED", "RECOVERING"]) if ctcae_grade == 5 else random.choice(["RECOVERED", "RECOVERING"]),
        }
    
    def generate_form44_sample(self) -> Dict:
        """Generate synthetic Form 44 (IND application form) data"""
        sections = {
            "applicant_details": {
                "company_name": f"BioPharma Company {random.randint(1, 999):03d}",
                "registration_no": f"REG/2024/{random.randint(1, 999):03d}",
                "contact_person": f"{random.choice(self.first_names)} {random.choice(self.last_names)}",
                "email": f"contact@biopharma{random.randint(1, 999)}.com",
                "phone": f"011-{random.randint(40000000, 49999999)}",
            },
            "drug_substance": {
                "generic_name": f"Experimental Compound -{random.choice(['A', 'B', 'C'])}-{random.randint(100, 999)}",
                "therapeutic_category": random.choice(["Oncology", "Cardiology", "Immunology", "Virology"]),
                "route_of_administration": random.choice(["Oral", "IV", "IM", "SC"]),
                "proposed_indication": "Treatment of [Disease] in [Patient population]",
                "chemical_structure": "Available in Section 2.3.1",
                "purity": f"{random.randint(95, 99)}.8%",
            },
            "nonclinical_data": {
                "pharmacology_studies": "Completed (see Section 3.2)",
                "toxicology_studies": "Completed per ICH M3(R2)",
                "genotoxicity": "Non-genotoxic (Ames test negative)",
                "reproductive_toxicity": random.choice(["Category C", "Category D", "Not tested"]),
            },
            "clinical_data_summary": {
                "phase_i_completed": "Yes" if random.random() > 0.2 else "No",
                "phase_i_subjects": random.randint(20, 100),
                "phase_ii_planned": "Yes",
                "phase_ii_subjects_planned": random.randint(200, 500),
            },
            "safety_summary": {
                "adverse_events_phase_i": random.randint(1, 10),
                "serious_adverse_events": random.randint(0, 2),
                "discontinuations_due_ae": random.randint(0, 3),
            },
            "form44_status": {
                "completion_percentage": random.randint(70, 100),
                "critical_sections_missing": random.randint(0, 3),
                "inconsistencies_found": random.randint(0, 2),
            }
        }
        
        return {
            "form_type": "Form 44 (IND Application)",
            "submission_date": (datetime.now() - timedelta(days=random.randint(1, 90))).strftime("%Y-%m-%d"),
            "applicant_name": sections["applicant_details"]["company_name"],
            "data": sections
        }
    
    def generate_inspection_note(self) -> Dict:
        """Generate synthetic inspection note (handwritten → OCR)"""
        site_issues = [
            "Temp in cold rm was 12C. Shld be 2-8C. Staff sed log book lost.",
            "Found unapproved suppliers in QA list. Not in approved list. Action needed.",
            "Manufacturing floor: Contamination risk. Cleanroom class not maintained. Temp/Humidity OOS.",
            "Documentation: 5 batches missing batch records. Cannot verify manufacturing steps.",
            "Equipment: Calibration certs expired for 3 instruments. Last cert Jan 2023.",
            "Personnel: 2 staff lack required GMP training. Training plans not current.",
            "Microbial testing: Failed standards for endotoxins. Batch B09 needs investigation.",
            "Stability data missing for Q9, Q12 months. Only available: Q3, Q6.",
        ]
        
        return {
            "inspection_id": f"INS_2024_{random.randint(1, 999):03d}",
            "inspection_date": (datetime.now() - timedelta(days=random.randint(1, 60))).strftime("%Y-%m-%d"),
            "facility_name": random.choice(list(self.hospitals.values())),
            "location": random.choice(list(self.cities.keys())),
            "inspector_name": f"{random.choice(self.first_names)} {random.choice(self.last_names)}",
            "raw_ocr_text": random.choice(site_issues),
            "finding_type": random.choice(["Critical", "Major", "Minor"]),
            "regulatory_reference": "Schedule M, Part I",
        }
    
    def generate_batch(self, count: int = 10) -> List[Dict]:
        """Generate batch of synthetic cases"""
        batch = []
        for i in range(count):
            patient = self.generate_patient_record()
            sae = self.generate_sae_narrative(patient)
            batch.append({
                "index": i + 1,
                "patient": patient,
                "sae": sae,
                "form44": self.generate_form44_sample(),
                "inspection": self.generate_inspection_note(),
            })
        return batch


# ============ USAGE ============
if __name__ == "__main__":
    generator = SyntheticDataGenerator()
    
    # Generate 10 cases (can scale to 100+)
    print("Generating 10 synthetic regulatory cases...\n")
    
    batch = generator.generate_batch(count=10)
    
    for case in batch:
        print(f"\n{'='*80}")
        print(f"CASE {case['index']}")
        print(f"{'='*80}")
        
        print(f"\n👤 PATIENT: {case['patient']['patient_name']}, Age {case['patient']['age']}")
        print(f"\n🏥 SAE: {case['sae']['event_term_raw']} (MedDRA: {case['sae']['meddra_code']})")
        print(f"    Onset: {case['sae']['onset_days']} days post-dose")
        print(f"    Outcome: {case['sae']['outcome']}")
        
        print(f"\n📋 FORM 44: {case['form44']['applicant_name']}")
        print(f"    Completion: {case['form44']['data']['form44_status']['completion_percentage']}%")
        
        print(f"\n🔍 INSPECTION: {case['inspection']['inspection_date']}")
        print(f"    Finding: {case['inspection']['finding_type']} - {case['inspection']['raw_ocr_text'][:60]}...")
    
    # Save all cases to JSON for API testing
    with open('synthetic_data_batch.json', 'w') as f:
        json.dump(batch, f, indent=2)
    
    print(f"\n\n✅ Generated {len(batch)} cases → synthetic_data_batch.json")
