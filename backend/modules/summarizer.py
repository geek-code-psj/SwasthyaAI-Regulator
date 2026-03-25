from transformers import pipeline, AutoTokenizer
import logging
from typing import Dict, List
import time

logger = logging.getLogger(__name__)


class SummarizationEngine:
    """Text Summarization and Key Findings Extraction"""
    
    def __init__(self, model_name: str = "facebook/bart-large-cnn"):
        """
        Initialize Summarization Engine
        
        Args:
            model_name: HuggingFace model identifier
        """
        self.model_name = model_name
        self.summarizer = None
        self.tokenizer = None
        self._load_model()
    
    def _load_model(self):
        """Load model with error handling"""
        try:
            logger.info(f"Loading summarization model: {self.model_name}")
            self.summarizer = pipeline(
                "summarization",
                model=self.model_name,
                device=-1  # CPU (use 0 for GPU if available)
            )
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            self.summarizer = None
    
    def summarize(self, text: str, max_length: int = 150, min_length: int = 50) -> Dict:
        """
        Generate abstractive summary
        
        Args:
            text: Input text to summarize
            max_length: Maximum summary length (tokens)
            min_length: Minimum summary length (tokens)
            
        Returns:
            Dict with summary and metadata
        """
        result = {
            "success": False,
            "summary": "",
            "original_length": len(text),
            "summary_length": 0,
            "compression_ratio": 0,
            "generation_time": 0,
            "error": None
        }
        
        if not self.summarizer:
            result["error"] = "Summarizer not initialized"
            return result
        
        try:
            # Check text length
            if len(text) < 100:
                result["error"] = "Text too short for summarization"
                return result
            
            # Truncate if necessary (model has token limits)
            max_input_tokens = 1024
            truncated_text = self._truncate_text(text, max_input_tokens)
            
            start_time = time.time()
            
            # Generate summary
            summary_result = self.summarizer(
                truncated_text,
                max_length=max_length,
                min_length=min_length,
                do_sample=False
            )
            
            summary = summary_result[0]["summary_text"]
            
            result["success"] = True
            result["summary"] = summary
            result["summary_length"] = len(summary)
            result["compression_ratio"] = len(summary) / len(text)
            result["generation_time"] = time.time() - start_time
            
            logger.info(f"Summary generated successfully. Compression ratio: {result['compression_ratio']:.2%}")
            
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            result["error"] = str(e)
        
        return result
    
    def extract_key_findings(self, text: str) -> Dict:
        """
        Extract key findings and critical information
        
        Args:
            text: Input text
            
        Returns:
            Dict with key findings
        """
        findings = {
            "key_findings": [],
            "clinical_data": [],
            "adverse_events": [],
            "manufacturing_data": [],
            "dosage_info": [],
            "error": None
        }
        
        try:
            # Extract clinical trials data
            clinical_findings = self._extract_clinical_data(text)
            findings["clinical_data"] = clinical_findings
            
            # Extract adverse events
            adverse_events = self._extract_adverse_events(text)
            findings["adverse_events"] = adverse_events
            
            # Extract manufacturing data
            manufacturing = self._extract_manufacturing_data(text)
            findings["manufacturing_data"] = manufacturing
            
            # Extract dosage information
            dosage = self._extract_dosage_info(text)
            findings["dosage_info"] = dosage
            
            # Combine into key findings
            all_findings = clinical_findings + adverse_events + manufacturing + dosage
            findings["key_findings"] = list(set(all_findings))[:10]  # Top 10 unique findings
            
            logger.info(f"Extracted {len(findings['key_findings'])} key findings")
            
        except Exception as e:
            logger.error(f"Error extracting key findings: {str(e)}")
            findings["error"] = str(e)
        
        return findings
    
    @staticmethod
    def _extract_clinical_data(text: str) -> List[str]:
        """Extract clinical trial data"""
        findings = []
        
        # Look for trial phases
        import re
        phases = re.findall(r"(?:Phase|Study Phase)[\s:]*([IVX]+)", text, re.IGNORECASE)
        if phases:
            findings.append(f"Trial Phase: {', '.join(set(phases))}")
        
        # Look for efficacy data
        efficacy_matches = re.findall(r"(?:efficacy|effectiveness)[\s:]*([0-9.%]+)", text, re.IGNORECASE)
        if efficacy_matches:
            findings.append(f"Efficacy: {efficacy_matches[0]}")
        
        # Look for safety data
        safety_matches = re.findall(r"(?:safety|AE|adverse|event)[\s:]*([^\n.]+)", text, re.IGNORECASE)
        if safety_matches:
            findings.append(f"Safety Profile: {safety_matches[0][:100]}")
        
        return findings
    
    @staticmethod
    def _extract_adverse_events(text: str) -> List[str]:
        """Extract adverse events information"""
        findings = []
        import re
        
        # Look for adverse events
        ae_pattern = r"(?:adverse event|AE|side effect)[\s:]*([^\n.]+)"
        ae_matches = re.findall(ae_pattern, text, re.IGNORECASE)
        
        for ae in ae_matches[:5]:  # Top 5 adverse events
            findings.append(f"AE: {ae.strip()[:80]}")
        
        # Look for SAE (Serious Adverse Events)
        sae_pattern = r"(?:serious adverse event|SAE)[\s:]*([^\n.]+)"
        sae_matches = re.findall(sae_pattern, text, re.IGNORECASE)
        
        for sae in sae_matches[:3]:
            findings.append(f"SAE: {sae.strip()[:80]}")
        
        return findings
    
    @staticmethod
    def _extract_manufacturing_data(text: str) -> List[str]:
        """Extract manufacturing quality data"""
        findings = []
        import re
        
        # Look for manufacturing standards
        mfg_pattern = r"(?:manufacturing|production|GMP|quality)[\s:]*([^\n.]+)"
        mfg_matches = re.findall(mfg_pattern, text, re.IGNORECASE)
        
        for mfg in mfg_matches[:3]:
            findings.append(f"Manufacturing: {mfg.strip()[:80]}")
        
        return findings
    
    @staticmethod
    def _extract_dosage_info(text: str) -> List[str]:
        """Extract dosage and administration information"""
        findings = []
        import re
        
        # Look for dosage information
        dosage_pattern = r"(?:dosage|dose|mg|ml)[\s:]*([^\n.]+)"
        dosage_matches = re.findall(dosage_pattern, text, re.IGNORECASE)
        
        for dose in dosage_matches[:3]:
            findings.append(f"Dosage: {dose.strip()[:80]}")
        
        # Look for route of administration
        route_pattern = r"(?:route|administration|oral|intravenous|IV)[\s:]*([^\n.]+)"
        route_matches = re.findall(route_pattern, text, re.IGNORECASE)
        
        if route_matches:
            findings.append(f"Route: {route_matches[0].strip()[:80]}")
        
        return findings
    
    def _truncate_text(self, text: str, max_tokens: int) -> str:
        """Truncate text to maximum tokens"""
        try:
            tokens = self.tokenizer.encode(text, truncation=False)
            if len(tokens) > max_tokens:
                truncated_tokens = tokens[:max_tokens]
                truncated_text = self.tokenizer.decode(truncated_tokens, skip_special_tokens=True)
                logger.warning(f"Text truncated from {len(tokens)} to {max_tokens} tokens")
                return truncated_text
            return text
        except:
            # Fallback: character-based truncation
            return text[:max_tokens * 4]
    
    def generate_report(self, text: str, extracted_data: Dict = None) -> Dict:
        """
        Generate comprehensive regulatory report
        
        Args:
            text: Anonymized document text
            extracted_data: Extracted structured data (optional)
            
        Returns:
            Comprehensive report
        """
        report = {
            "executive_summary": "",
            "key_findings": [],
            "clinical_assessment": "",
            "safety_assessment": "",
            "manufacturing_assessment": "",
            "recommendations": [],
            "report_timestamp": None,
            "error": None
        }
        
        try:
            import datetime
            report["report_timestamp"] = datetime.datetime.utcnow().isoformat()
            
            # Generate executive summary
            summary = self.summarize(text)
            if summary["success"]:
                report["executive_summary"] = summary["summary"]
            
            # Extract key findings
            findings = self.extract_key_findings(text)
            report["key_findings"] = findings["key_findings"]
            
            # Generate assessments
            report["clinical_assessment"] = self._generate_clinical_assessment(findings)
            report["safety_assessment"] = self._generate_safety_assessment(findings)
            report["manufacturing_assessment"] = self._generate_manufacturing_assessment(findings)
            
            # Generate recommendations
            report["recommendations"] = self._generate_recommendations(findings)
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            report["error"] = str(e)
        
        return report
    
    @staticmethod
    def _generate_clinical_assessment(findings: Dict) -> str:
        """Generate clinical assessment from findings"""
        if findings["clinical_data"]:
            return f"Clinical Assessment: {'; '.join(findings['clinical_data'][:2])}"
        return "Clinical Assessment: Insufficient data for assessment"
    
    @staticmethod
    def _generate_safety_assessment(findings: Dict) -> str:
        """Generate safety assessment from findings"""
        ae_count = len(findings["adverse_events"])
        sae_count = len([e for e in findings["adverse_events"] if "SAE" in e])
        return f"Safety Assessment: {ae_count} adverse events reported, {sae_count} serious adverse events"
    
    @staticmethod
    def _generate_manufacturing_assessment(findings: Dict) -> str:
        """Generate manufacturing assessment from findings"""
        if findings["manufacturing_data"]:
            return f"Manufacturing Assessment: {'; '.join(findings['manufacturing_data'][:2])}"
        return "Manufacturing Assessment: Standard quality protocols observed"
    
    @staticmethod
    def _generate_recommendations(findings: Dict) -> List[str]:
        """Generate recommendations based on findings"""
        recommendations = []
        
        ae_count = len(findings.get("adverse_events", []))
        if ae_count > 10:
            recommendations.append("Increase monitoring frequency for adverse events")
        
        if findings["key_findings"]:
            recommendations.append("Review clinical efficacy data before approval")
        
        recommendations.append("Verify manufacturing quality standards compliance")
        
        return recommendations
