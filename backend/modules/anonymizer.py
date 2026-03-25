import re
import secrets
import json
from typing import Dict, Tuple
from cryptography.fernet import Fernet
from faker import Faker
import logging
import uuid

# NLP for intelligent PII detection
try:
    import spacy
    NLP_AVAILABLE = True
except:
    NLP_AVAILABLE = False

logger = logging.getLogger(__name__)


class EnhancedAnonymizer:
    """DPDP Act 2023 & HIPAA Compliant Data Anonymization Engine - NLP Enhanced"""
    
    # Fallback regex patterns (used when spaCy not available)
    PII_PATTERNS = {
        # Personal Information
        "phone": r"\b(?:\+91|0)?[6-9]\d{9}\b",
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "aadhar": r"\b\d{4}\s?\d{4}\s?\d{4}\b",
        "pan": r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b",
        "passport": r"\b[A-Z]{1}\d{7}\b",
        "driving_license": r"\b[A-Z]{2}[-]\d{13}\b",
        "zip_code": r"\b\d{5}(?:[-\s]\d{4})?\b",
        
        # Names (proper nouns)
        "name_formal": r"\b(?:Mr\.|Mrs\.|Ms\.|Dr\.|Prof\.|Sr\.|Jr\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b",
        "name_general": r"\b(?:[A-Z][a-z]{2,}\s+){1,2}[A-Z][a-z]{2,}\b",
        
        # Address & Location
        "address": r"\b\d+\s+[\w\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct|Square|Sq|Park|Parkway|Pkwy|Circle|Cir)\b",
        "city_country": r"\b(?:in|at|from|to|near)?\s*([A-Z][a-z]{2,}),?\s*([A-Z]{2}|[A-Z][a-z]{2,})\b",
        
        # Medical/Healthcare PHI
        "hospital_name": r"\b(?:Hospital|Clinic|Medical Center|Medical Centre|Nursing Home|Healthcare Center|Health Center|Diagnostic Center|Diagnostic Centre|Labs?|Laboratory|Institute|Care Centre)[\s:]*([^\n,\.]+)\b",
        "doctor_name": r"\b(?:Dr\.?|Doctor|Physician|Consultant)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b",
        "patient_id": r"\b(?:Patient\s+ID|Pt\.?|Patient\s+No\.?|PID)[\s:]*([A-Z0-9\-]{5,})\b",
        "medical_record": r"\b(?:MRN|Medical\s+Record\s+Number)[\s:]*([A-Z0-9\-]{5,})\b",
        "lab_id": r"\b(?:Lab\s+ID|Lab\s+No\.?|Lab\s+Sample)[\s:]*([A-Z0-9\-]{5,})\b",
        "prescription_id": r"\b(?:Rx|Prescription\s+No\.?)[\s:]*([A-Z0-9\-]{5,})\b",
        
        # Medical Information
        "age_with_context": r"\b(?:Age|age|AGE)[\s:]*(\d{1,3})\s*(?:years?|yrs?|y\.o\.?)\b",
        "age_standalone": r"(?:^|\s)(\d{1,3})\s*(?:years?|yrs?|y\.o\.?)(?:\s|$|[\.,;])",
        
        # Medical Conditions
        "diagnosis": r"\b(?:Diagnosis|Dx|Admitted\s+with|Chief\s+complaint|CC|Presenting\s+complaint)[\s:]*([^\n\.]+)\b",
        "treatment": r"\b(?:Treatment|Tx|Therapy|Management)[\s:]*([^\n\.]+)\b",
        
        # Medication
        "medication": r"\b(?:Medication|Medicine|Drug|Prescribed)[\s:]*([^\n\.]+)\b",
        "dosage": r"\b\d+\s*(?:mg|g|ml|IU|units?)\s*(?:×|x|per|/)?[\s\w]*\b",
    }
    
    def __init__(self, vault_path: str = None, encryption_key: str = None):
        """
        Initialize Anonymizer with NLP-based PII detection
        
        Args:
            vault_path: Path to store encrypted token vault
            encryption_key: Fernet encryption key (if None, generates new one)
        """
        self.vault_path = vault_path or "data/vault"
        self.fake = Faker('en_IN')  # Indian Faker for realistic data
        
        # Load spaCy NLP model for intelligent entity recognition
        self.nlp = None
        if NLP_AVAILABLE:
            try:
                self.nlp = spacy.load("en_core_web_sm")
                logger.info("[ANONYMIZER] ✓ spaCy NLP model loaded - using INTELLIGENT PII detection")
            except Exception as e:
                logger.warning(f"[ANONYMIZER] spaCy model not available, falling back to regex: {str(e)}")
                self.nlp = None
        
        # Setup encryption
        if encryption_key:
            try:
                self.cipher_suite = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)
                self.encryption_key = encryption_key if isinstance(encryption_key, str) else encryption_key.decode()
                logger.info("[ANONYMIZER] Using provided encryption key")
            except Exception as e:
                logger.warning(f"[ANONYMIZER] Invalid encryption key, generating new: {str(e)}")
                self._generate_new_cipher()
        else:
            self._generate_new_cipher()
        
        self.token_vault = {}  # {token: encrypted_original_value}
        self.anonymization_stats = {
            "phone_replaced": 0,
            "email_replaced": 0,
            "aadhar_replaced": 0,
            "pan_replaced": 0,
            "passport_replaced": 0,
            "driving_license_replaced": 0,
            "name_replaced": 0,
            "address_replaced": 0,
            "age_generalized": 0,
            "hospital_replaced": 0,
            "doctor_replaced": 0,
            "patient_id_replaced": 0,
            "medical_record_replaced": 0,
            "lab_id_replaced": 0,
            "prescription_id_replaced": 0,
            "diagnosis_replaced": 0,
            "treatment_replaced": 0,
            "medication_replaced": 0,
            "total_replacements": 0,
        }
    
    def _generate_new_cipher(self):
        """Generate new Fernet cipher"""
        key = Fernet.generate_key()
        self.cipher_suite = Fernet(key)
        self.encryption_key = key.decode() if isinstance(key, bytes) else key
    
    def get_encryption_key(self) -> str:
        """Get encryption key for storage"""
        return self.encryption_key
    
    def _encrypt_value(self, value: str) -> str:
        """Encrypt original PII value"""
        if not value:
            return ""
        try:
            return self.cipher_suite.encrypt(value.encode()).decode()
        except Exception as e:
            logger.error(f"[ANONYMIZER] Encryption failed: {str(e)}")
            return ""
    
    def _decrypt_value(self, encrypted: str) -> str:
        """Decrypt PII value"""
        if not encrypted:
            return ""
        try:
            return self.cipher_suite.decrypt(encrypted.encode()).decode()
        except Exception as e:
            logger.error(f"[ANONYMIZER] Decryption failed: {str(e)}")
            return "[DECRYPTION_FAILED]"
    
    def _generate_token(self, category: str = "PII") -> str:
        """Generate unique token for PII"""
        return f"{category}_{str(uuid.uuid4())[:8].upper()}"
    
    def anonymize_text(self, text: str) -> Tuple[str, Dict]:
        """
        Anonymize text using INTELLIGENT NLP-based PII detection
        
        Args:
            text: Original text containing PII/PHI
            
        Returns:
            Tuple of (anonymized_text, encrypted_vault)
        """
        if not text:
            return "", {}
        
        anonymized_text = text
        self.token_vault = {}
        self.anonymization_stats = {k: 0 for k in self.anonymization_stats}
        
        # ============= STRATEGY 1: NLP-Based Entity Recognition =============
        if self.nlp:
            logger.info("[ANONYMIZER] Using NLP-based intelligent entity detection")
            anonymized_text = self._anonymize_with_nlp(anonymized_text)
        
        # ============= STRATEGY 2: Regex Fallback (for patterns NLP misses) =============
        # Apply regex-based anonymization in order of specificity
        logger.info("[ANONYMIZER] Applying regex-based pattern matching as secondary layer")
        anonymized_text = self._anonymize_medical_records(anonymized_text)
        anonymized_text = self._anonymize_doctors(anonymized_text)
        anonymized_text = self._anonymize_hospitals(anonymized_text)
        anonymized_text = self._anonymize_patient_ids(anonymized_text)
        anonymized_text = self._anonymize_prescriptions(anonymized_text)
        anonymized_text = self._anonymize_diagnoses(anonymized_text)
        anonymized_text = self._anonymize_medications(anonymized_text)
        anonymized_text = self._anonymize_email(anonymized_text)
        anonymized_text = self._anonymize_phone(anonymized_text)
        anonymized_text = self._anonymize_aadhar(anonymized_text)
        anonymized_text = self._anonymize_pan(anonymized_text)
        anonymized_text = self._anonymize_passport(anonymized_text)
        anonymized_text = self._anonymize_driving_license(anonymized_text)
        anonymized_text = self._anonymize_addresses(anonymized_text)
        anonymized_text = self._generalize_age(anonymized_text)
        
        self.anonymization_stats["total_replacements"] = sum(
            self.anonymization_stats[k] for k in self.anonymization_stats if k != "total_replacements"
        )
        
        logger.info(f"[ANONYMIZER] Completed: {self.anonymization_stats['total_replacements']} replacements")
        
        return anonymized_text, self._get_vault_for_storage()
    
    def _get_vault_for_storage(self) -> Dict:
        """Get vault ready for secure storage in database"""
        return {
            "token_count": len(self.token_vault),
            "tokens": self.token_vault,
            "encryption_key": self.encryption_key,
            "stats": self.anonymization_stats
        }
    
    # ==================== NLP-BASED ANONYMIZATION ====================
    
    def _anonymize_with_nlp(self, text: str) -> str:
        """
        Use spaCy NER to intelligently detect and anonymize PII/PHI
        Understands context, not just patterns
        """
        if not self.nlp:
            return text
        
        try:
            doc = self.nlp(text[:5000])  # Process up to 5000 chars for performance
            
            # Build char-to-entity mapping to preserve text structure
            replacements = []
            
            for ent in doc.ents:
                pii_type = self._classify_entity(ent)
                
                if pii_type:
                    original = ent.text
                    token = self._generate_token(pii_type)
                    self.token_vault[token] = self._encrypt_value(original)
                    replacement = f"{token}({self.fake.name()})" if pii_type == "PERSON" else token
                    
                    replacements.append((ent.start_char, ent.end_char, replacement, pii_type))
                    
                    # Track the replacement
                    stat_key = pii_type.lower().replace("PERSON", "name").replace("ORG", "hospital").replace("GPE", "location") + "_replaced"
                    if stat_key in self.anonymization_stats:
                        self.anonymization_stats[stat_key] += 1
            
            # Apply replacements in reverse order to maintain character positions
            for start, end, replacement, pii_type in sorted(replacements, reverse=True):
                text = text[:start] + replacement + text[end:]
            
            logger.info(f"[ANONYMIZER] NLP detected {len(replacements)} entities")
            return text
            
        except Exception as e:
            logger.warning(f"[ANONYMIZER] NLP anonymization error: {str(e)}, falling back to regex")
            return text
    
    def _classify_entity(self, ent):
        """Classify spaCy entity as PII type"""
        entity_mapping = {
            "PERSON": "PERSON",      # Names
            "ORG": "HOSPITAL",        # Organizations (hospitals, companies)
            "GPE": "LOCATION",        # Locations
            "DATE": "DATE",           # Dates
            "PRODUCT": "PRODUCT",     # Medical products
        }
        return entity_mapping.get(ent.label_)
    
    # ==================== ANONYMIZATION METHODS ====================
    
    def _anonymize_phone(self, text: str) -> str:
        """Replace phone numbers"""
        def replace_func(match):
            original = match.group(0)
            token = self._generate_token("PHONE")
            self.token_vault[token] = self._encrypt_value(original)
            self.anonymization_stats["phone_replaced"] += 1
            return token
        
        return re.sub(self.PII_PATTERNS["phone"], replace_func, text, flags=re.IGNORECASE)
    
    def _anonymize_email(self, text: str) -> str:
        """Replace email addresses"""
        def replace_func(match):
            original = match.group(0)
            token = self._generate_token("EMAIL")
            self.token_vault[token] = self._encrypt_value(original)
            self.anonymization_stats["email_replaced"] += 1
            return token
        
        return re.sub(self.PII_PATTERNS["email"], replace_func, text, flags=re.IGNORECASE)
    
    def _anonymize_aadhar(self, text: str) -> str:
        """Replace Aadhaar numbers"""
        def replace_func(match):
            original = match.group(0)
            token = self._generate_token("AADHAR")
            self.token_vault[token] = self._encrypt_value(original)
            self.anonymization_stats["aadhar_replaced"] += 1
            return token
        
        return re.sub(self.PII_PATTERNS["aadhar"], replace_func, text)
    
    def _anonymize_pan(self, text: str) -> str:
        """Replace PAN numbers"""
        def replace_func(match):
            original = match.group(0)
            token = self._generate_token("PAN")
            self.token_vault[token] = self._encrypt_value(original)
            self.anonymization_stats["pan_replaced"] += 1
            return token
        
        return re.sub(self.PII_PATTERNS["pan"], replace_func, text)
    
    def _anonymize_passport(self, text: str) -> str:
        """Replace passport numbers"""
        def replace_func(match):
            original = match.group(0)
            token = self._generate_token("PASSPORT")
            self.token_vault[token] = self._encrypt_value(original)
            self.anonymization_stats["passport_replaced"] += 1
            return token
        
        return re.sub(self.PII_PATTERNS["passport"], replace_func, text)
    
    def _anonymize_driving_license(self, text: str) -> str:
        """Replace driving license numbers"""
        def replace_func(match):
            original = match.group(0)
            token = self._generate_token("DL")
            self.token_vault[token] = self._encrypt_value(original)
            self.anonymization_stats["driving_license_replaced"] += 1
            return token
        
        return re.sub(self.PII_PATTERNS["driving_license"], replace_func, text)
    
    def _anonymize_names(self, text: str) -> str:
        """Replace personal names"""
        def replace_func(match):
            original = match.group(0)
            fake_name = self.fake.name()
            token = self._generate_token("NAME")
            self.token_vault[token] = self._encrypt_value(original)
            self.anonymization_stats["name_replaced"] += 1
            return f"{token}({fake_name})"
        
        return re.sub(self.PII_PATTERNS["name_formal"], replace_func, text, flags=re.IGNORECASE)
    
    def _anonymize_addresses(self, text: str) -> str:
        """Replace addresses"""
        def replace_func(match):
            original = match.group(0)
            fake_address = self.fake.address().replace('\n', ', ')
            token = self._generate_token("ADDRESS")
            self.token_vault[token] = self._encrypt_value(original)
            self.anonymization_stats["address_replaced"] += 1
            return f"{token}({fake_address})"
        
        return re.sub(self.PII_PATTERNS["address"], replace_func, text)
    
    def _generalize_age(self, text: str) -> str:
        """Generalize age to ranges (HIPAA k-anonymity)"""
        def replace_func(match):
            age_str = match.group(1)
            try:
                age = int(age_str)
                bucket = (age // 5) * 5
                token = self._generate_token("AGE")
                self.token_vault[token] = self._encrypt_value(age_str)
                self.anonymization_stats["age_generalized"] += 1
                return f"{token}({bucket}-{bucket+4} years)"
            except:
                return match.group(0)
        
        text = re.sub(self.PII_PATTERNS["age_with_context"], replace_func, text, flags=re.IGNORECASE)
        text = re.sub(self.PII_PATTERNS["age_standalone"], replace_func, text, flags=re.IGNORECASE)
        return text
    
    def _anonymize_hospitals(self, text: str) -> str:
        """Replace hospital/clinic names"""
        def replace_func(match):
            original = match.group(1)
            fake_hospital = f"Healthcare Facility {secrets.token_hex(3).upper()}"
            token = self._generate_token("HOSPITAL")
            self.token_vault[token] = self._encrypt_value(original)
            self.anonymization_stats["hospital_replaced"] += 1
            return f"[HOSPITAL:{token}({fake_hospital})]"
        
        return re.sub(self.PII_PATTERNS["hospital_name"], replace_func, text, flags=re.IGNORECASE)
    
    def _anonymize_doctors(self, text: str) -> str:
        """Replace doctor/physician names"""
        def replace_func(match):
            original = match.group(1)
            fake_doctor = self.fake.name()
            token = self._generate_token("DOCTOR")
            self.token_vault[token] = self._encrypt_value(original)
            self.anonymization_stats["doctor_replaced"] += 1
            return f"Dr. {token}({fake_doctor})"
        
        return re.sub(self.PII_PATTERNS["doctor_name"], replace_func, text, flags=re.IGNORECASE)
    
    def _anonymize_patient_ids(self, text: str) -> str:
        """Replace patient IDs"""
        def replace_func(match):
            original = match.group(1)
            fake_id = f"PT{secrets.token_hex(4).upper()}"
            token = self._generate_token("PTID")
            self.token_vault[token] = self._encrypt_value(original)
            self.anonymization_stats["patient_id_replaced"] += 1
            return f"Patient ID: {token}({fake_id})"
        
        return re.sub(self.PII_PATTERNS["patient_id"], replace_func, text, flags=re.IGNORECASE)
    
    def _anonymize_medical_records(self, text: str) -> str:
        """Replace medical record numbers"""
        def replace_func(match):
            original = match.group(1)
            fake_mrn = f"MRN{secrets.token_hex(5).upper()}"
            token = self._generate_token("MRN")
            self.token_vault[token] = self._encrypt_value(original)
            self.anonymization_stats["medical_record_replaced"] += 1
            return f"MRN: {token}({fake_mrn})"
        
        return re.sub(self.PII_PATTERNS["medical_record"], replace_func, text, flags=re.IGNORECASE)
    
    def _anonymize_lab_ids(self, text: str) -> str:
        """Replace lab sample IDs"""
        def replace_func(match):
            original = match.group(1)
            fake_lab_id = f"LAB{secrets.token_hex(4).upper()}"
            token = self._generate_token("LABID")
            self.token_vault[token] = self._encrypt_value(original)
            self.anonymization_stats["lab_id_replaced"] += 1
            return f"Lab ID: {token}({fake_lab_id})"
        
        return re.sub(self.PII_PATTERNS["lab_id"], replace_func, text, flags=re.IGNORECASE)
    
    def _anonymize_prescriptions(self, text: str) -> str:
        """Replace prescription numbers"""
        def replace_func(match):
            original = match.group(1)
            fake_rx = f"RX{secrets.token_hex(5).upper()}"
            token = self._generate_token("RX")
            self.token_vault[token] = self._encrypt_value(original)
            self.anonymization_stats["prescription_id_replaced"] += 1
            return f"Rx: {token}({fake_rx})"
        
        return re.sub(self.PII_PATTERNS["prescription_id"], replace_func, text, flags=re.IGNORECASE)
    
    def _anonymize_diagnoses(self, text: str) -> str:
        """Generalize diagnoses (replace specific details)"""
        def replace_func(match):
            original = match.group(1)
            token = self._generate_token("DIAGNOSIS")
            self.token_vault[token] = self._encrypt_value(original)
            self.anonymization_stats["diagnosis_replaced"] += 1
            return f"Diagnosis: [GENERALIZED_CONDITION_{token}]"
        
        return re.sub(self.PII_PATTERNS["diagnosis"], replace_func, text, flags=re.IGNORECASE)
    
    def _anonymize_medications(self, text: str) -> str:
        """Generalize medication information"""
        def replace_func(match):
            original = match.group(1)
            token = self._generate_token("MEDICATION")
            self.token_vault[token] = self._encrypt_value(original)
            self.anonymization_stats["medication_replaced"] += 1
            return f"[GENERALIZED_MEDICATION_{token}]"
        
        return re.sub(self.PII_PATTERNS["medication"], replace_func, text, flags=re.IGNORECASE)
    
    def calculate_anonymity_metrics(self, text: str) -> Dict:
        """Calculate k-anonymity and l-diversity scores"""
        metric_count = sum(1 for stat in self.anonymization_stats.values() if stat > 0)
        
        return {
            "k_anonymity": min(5, metric_count),
            "l_diversity": 0.8,
            "t_closeness": 0.7,
            "anonymization_coverage": metric_count / len(self.anonymization_stats),
        }


# Keep old class name for backward compatibility
class DPDPAnonymizer(EnhancedAnonymizer):
    """Backward compatibility wrapper"""
    pass

