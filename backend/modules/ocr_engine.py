import pytesseract
from PIL import Image
import pdfplumber
import PyPDF2
import logging
from typing import Dict, List, Tuple
import re

logger = logging.getLogger(__name__)


class OCREngine:
    """Hybrid OCR and Layout Parsing Engine"""
    
    def __init__(self, language: str = "eng"):
        """
        Initialize OCR Engine
        
        Args:
            language: Tesseract language code (e.g., 'eng', 'hin')
        """
        self.language = language
        self.pytesseract_config = f"--psm 6 -l {language}"
    
    def extract_from_pdf(self, pdf_path: str) -> Dict:
        """
        Extract text and layout information from PDF
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dict with extracted text, tables, and metadata
        """
        result = {
            "text": "",
            "tables": [],
            "pages": [],
            "metadata": {},
            "error": None
        }
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                result["metadata"] = {
                    "total_pages": len(pdf.pages),
                    "pdf_info": pdf.metadata
                }
                
                for page_num, page in enumerate(pdf.pages, 1):
                    page_data = {
                        "page_number": page_num,
                        "text": page.extract_text() or "",
                        "tables": self._extract_tables(page),
                        "images": self._detect_images(page)
                    }
                    result["pages"].append(page_data)
                    result["text"] += page_data["text"] + "\n"
                    result["tables"].extend(page_data["tables"])
            
            logger.info(f"Successfully extracted text from PDF: {pdf_path}")
            return result
            
        except Exception as e:
            logger.error(f"Error extracting from PDF {pdf_path}: {str(e)}")
            result["error"] = str(e)
            return result
    
    def extract_from_image(self, image_path: str) -> Dict:
        """
        Extract text from image using Tesseract
        
        Args:
            image_path: Path to image file
            
        Returns:
            Dict with extracted text and confidence
        """
        result = {
            "text": "",
            "confidence": 0,
            "error": None
        }
        
        try:
            image = Image.open(image_path)
            
            # Extract text
            text = pytesseract.image_to_string(image, config=self.pytesseract_config)
            
            # Get confidence
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            confidence = sum(confidences) / len(confidences) if confidences else 0
            
            result["text"] = text
            result["confidence"] = confidence
            
            logger.info(f"Successfully extracted text from image: {image_path} (Confidence: {confidence:.2f}%)")
            return result
            
        except Exception as e:
            logger.error(f"Error extracting from image {image_path}: {str(e)}")
            result["error"] = str(e)
            return result
    
    def _extract_tables(self, page) -> List[Dict]:
        """Extract tables from PDF page"""
        tables = []
        try:
            page_tables = page.extract_tables()
            if page_tables:
                for table_idx, table in enumerate(page_tables):
                    tables.append({
                        "table_id": f"table_{table_idx}",
                        "data": table,
                        "bbox": page.find_tables()[table_idx].bbox if hasattr(page, 'find_tables') else None
                    })
        except Exception as e:
            logger.warning(f"Error extracting tables: {str(e)}")
        return tables
    
    def _detect_images(self, page) -> List[Dict]:
        """Detect images in PDF page"""
        images = []
        try:
            page_images = page.images
            if page_images:
                for img_idx, img in enumerate(page_images):
                    images.append({
                        "image_id": f"image_{img_idx}",
                        "bbox": img.get("bbox", None),
                        "height": img.get("height", None),
                        "width": img.get("width", None)
                    })
        except Exception as e:
            logger.warning(f"Error detecting images: {str(e)}")
        return images
    
    def clean_extracted_text(self, text: str) -> str:
        """
        Clean and normalize extracted text
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove control characters
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t\r')
        
        # Normalize line breaks
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        return text.strip()
    
    def extract_form_fields(self, text: str) -> Dict:
        """
        Extract structured form fields from text
        
        Args:
            text: Extracted text from form
            
        Returns:
            Dict of form fields
        """
        fields = {
            "drug_name": self._extract_field(text, r"(?:Drug Name:|Drug:)[\s:]*([^\n]+)"),
            "clinical_trial_id": self._extract_field(text, r"(?:Clinical Trial ID|CT ID)[\s:]*([A-Z0-9\-]+)"),
            "manufacturer": self._extract_field(text, r"(?:Manufacturer|Company)[\s:]*([^\n]+)"),
            "submission_date": self._extract_field(text, r"(?:Date of Submission|Submission Date)[\s:]*([^\n]+)"),
            "indication": self._extract_field(text, r"(?:Indication|Therapeutic Area)[\s:]*([^\n]+)"),
        }
        return {k: v for k, v in fields.items() if v}
    
    @staticmethod
    def _extract_field(text: str, pattern: str) -> str:
        """Extract field using regex pattern"""
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else None
