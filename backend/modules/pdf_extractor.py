"""
Comprehensive PDF/Document Extraction Module
Handles: text extraction, OCR fallback, validation, cleaning, quality scoring
Fixes: binary junk removal, confidence scoring, smart fallback, extraction validation
"""

import logging
import re
import io
from pathlib import Path
from typing import Dict, Tuple, Optional
import fitz  # PyMuPDF
import pdfplumber
import pytesseract
from PIL import Image

logger = logging.getLogger(__name__)


class ExtractionResult:
    """Structured extraction result"""
    def __init__(self):
        self.text = ""
        self.method = None  # "pymupdf", "ocr", "hybrid", "plaintext"
        self.confidence = 0.0  # 0-1 score
        self.pages_extracted = 0
        self.total_pages = 0
        self.tables = []
        self.images = []
        self.metadata = {}
        self.extraction_quality = "unknown"  # "high", "medium", "low"
        self.error = None
        self.warnings = []
    
    def to_dict(self):
        return {
            "text": self.text,
            "method": self.method,
            "confidence": round(self.confidence, 2),
            "pages_extracted": self.pages_extracted,
            "total_pages": self.total_pages,
            "tables": self.tables,
            "images": self.images,
            "metadata": self.metadata,
            "extraction_quality": self.extraction_quality,
            "error": self.error,
            "warnings": self.warnings
        }


class PDFExtractor:
    """Hybrid PDF extraction with fallback and validation"""
    
    # Minimum meaningful text length per extraction method
    MIN_TEXT_THRESHOLD = 100
    
    # Binary junk detection patterns - HARD REJECTION for these
    BINARY_PATTERNS = [
        r'^%PDF',  # PDF header marker indicates extracted binary content
        r'^\x00{4,}',  # Null byte sequences
        r'^\xff\xd8\xff',  # JPEG header
        r'^\x89PNG',  # PNG header
    ]
    
    # Text cleaning patterns
    NOISE_PATTERNS = [
        (r'[^\x20-\x7E\n\r\u0080-\uFFFF]', ''),  # Remove non-printable ASCII
        (r'\f+', '\n'),  # Form feeds → newlines
        (r'\x00+', ''),  # Null bytes
        (r'\s{3,}', '  '),  # Excessive spaces → double space
        (r'\n{3,}', '\n\n'),  # Excessive newlines → double newline
    ]
    
    @staticmethod
    def extract_document(file_path: str) -> ExtractionResult:
        """
        Main extraction entry point - handles all file types with fallback
        
        PIPELINE:
        1. Detect file type
        2. Try primary extraction method
        3. Validate result (sufficient text, not binary junk)
        4. Fallback if needed
        5. Clean and return structured result
        
        Args:
            file_path: Path to document file
            
        Returns:
            ExtractionResult object with all metadata
        """
        result = ExtractionResult()
        
        try:
            file_ext = Path(file_path).suffix.lower()
            logger.info(f"[EXTRACT] Starting extraction: {Path(file_path).name} ({file_ext})")
            
            # ========== PDF FILES ==========
            if file_ext == '.pdf':
                result = PDFExtractor._extract_pdf(file_path)
            
            # ========== IMAGE FILES ==========
            elif file_ext in ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.gif']:
                result = PDFExtractor._extract_image(file_path)
            
            # ========== TEXT FILES ==========
            elif file_ext in ['.txt', '.docx', '.doc']:
                result = PDFExtractor._extract_text_file(file_path)
            
            else:
                result.error = f"Unsupported file type: {file_ext}"
                result.extraction_quality = "low"
                logger.warning(f"[EXTRACT] Unsupported file type: {file_ext}")
            
            # ========== POST-PROCESSING ==========
            if result.text:
                # Clean extracted text
                result.text = PDFExtractor._clean_text(result.text)
                
                # Validate extraction
                PDFExtractor._validate_extraction(result)
                
                # Calculate confidence if not set
                if result.confidence == 0 and result.method == "pymupdf":
                    result.confidence = PDFExtractor._calculate_text_confidence(result.text)
                
                # HARD REJECTION: If quality is low after cleaning and validation, reject it
                if result.extraction_quality == "low":
                    result.error = "Extraction quality too low - document may be corrupted or unreadable"
                    result.text = ""  # Clear the extracted text
                    logger.warning(f"[EXTRACT] ✗ REJECTED | Quality: {result.extraction_quality} | {result.error}")
                else:
                    logger.info(f"[EXTRACT] ✓ Success | Method: {result.method} | Quality: {result.extraction_quality} | Confidence: {result.confidence:.0%}")
            else:
                result.error = "No text extracted from document"
                result.extraction_quality = "low"
                logger.warning(f"[EXTRACT] No text extracted")
            
            return result
        
        except Exception as e:
            logger.error(f"[EXTRACT] Fatal error: {str(e)}")
            result.error = f"Extraction failed: {str(e)}"
            result.extraction_quality = "low"
            return result
    
    @staticmethod
    def _extract_pdf(file_path: str) -> ExtractionResult:
        """Extract from PDF with smart fallback"""
        result = ExtractionResult()
        
        try:
            # ========================
            # STRATEGY 1: PyMuPDF (fast, good for text PDFs)
            # ========================
            result = PDFExtractor._extract_pdf_pymupdf(file_path)
            
            # Check if extraction was successful
            if result.text and len(result.text.strip()) >= PDFExtractor.MIN_TEXT_THRESHOLD:
                logger.info(f"[PDF] PyMuPDF extraction successful: {len(result.text)} chars")
                return result
            
            # ========================
            # FALLBACK 1: pdfplumber (better layout parsing)
            # ========================
            logger.info(f"[PDF] PyMuPDF insufficient, trying pdfplumber...")
            pdfplumber_result = PDFExtractor._extract_pdf_pdfplumber(file_path)
            
            if pdfplumber_result.text and len(pdfplumber_result.text.strip()) >= PDFExtractor.MIN_TEXT_THRESHOLD:
                logger.info(f"[PDF] pdfplumber extraction successful: {len(pdfplumber_result.text)} chars")
                return pdfplumber_result
            
            # ========================
            # FALLBACK 2: OCR (scanned PDFs)
            # ========================
            logger.info(f"[PDF] Text extraction insufficient, trying OCR...")
            ocr_result = PDFExtractor._extract_pdf_ocr(file_path)
            
            if ocr_result.text and len(ocr_result.text.strip()) >= PDFExtractor.MIN_TEXT_THRESHOLD:
                logger.info(f"[PDF] OCR extraction successful: {len(ocr_result.text)} chars")
                return ocr_result
            
            # ========================
            # ALL METHODS FAILED
            # ========================
            result.text = ""
            result.error = "All extraction methods failed or returned insufficient text"
            result.extraction_quality = "low"
            logger.warning(f"[PDF] All extraction methods failed")
            return result
        
        except Exception as e:
            logger.error(f"[PDF] Error: {str(e)}")
            result.error = str(e)
            return result
    
    @staticmethod
    def _extract_pdf_pymupdf(file_path: str) -> ExtractionResult:
        """PyMuPDF extraction - FAST for text PDFs"""
        result = ExtractionResult()
        result.method = "pymupdf"
        
        try:
            doc = fitz.open(file_path)
            result.total_pages = len(doc)
            text = ""
            
            for page_num, page in enumerate(doc, 1):
                try:
                    page_text = page.get_text()
                    
                    # VALIDATION: Check if page is mostly binary/junk
                    if PDFExtractor._is_binary_junk(page_text):
                        logger.debug(f"[PYMUPDF] Page {page_num} detected as binary/junk, skipping")
                        continue
                    
                    text += page_text + "\n"
                    result.pages_extracted += 1
                
                except Exception as e:
                    logger.warning(f"[PYMUPDF] Error extracting page {page_num}: {str(e)}")
                    result.warnings.append(f"Page {page_num} extraction failed: {str(e)}")
            
            doc.close()
            result.text = text
            
            # Confidence = pages successfully extracted / total
            result.confidence = result.pages_extracted / result.total_pages if result.total_pages > 0 else 0
            result.extraction_quality = PDFExtractor._rate_extraction_quality(result)
            
            logger.info(f"[PYMUPDF] Extracted {result.pages_extracted}/{result.total_pages} pages")
            return result
        
        except Exception as e:
            logger.error(f"[PYMUPDF] Error: {str(e)}")
            result.error = str(e)
            result.extraction_quality = "low"
            return result
    
    @staticmethod
    def _extract_pdf_pdfplumber(file_path: str) -> ExtractionResult:
        """pdfplumber extraction - Better layout parsing"""
        result = ExtractionResult()
        result.method = "pdfplumber"
        
        try:
            with pdfplumber.open(file_path) as pdf:
                result.total_pages = len(pdf.pages)
                text = ""
                
                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        # Extract text
                        page_text = page.extract_text() or ""
                        
                        # Extract tables with standardized CSV-like format
                        tables = page.extract_tables()
                        if tables:
                            for table_idx, table in enumerate(tables):
                                # Standardize table format: CSV-like with | separators
                                table_text = PDFExtractor._standardize_table(table)
                                page_text += "\n\n[TABLE_START]\n" + table_text + "\n[TABLE_END]\n\n"
                                result.tables.append({"page": page_num, "table_index": table_idx, "data": table})
                        
                        # VALIDATION: Check if page is junk
                        if not PDFExtractor._is_binary_junk(page_text):
                            text += page_text + "\n"
                            result.pages_extracted += 1
                    
                    except Exception as e:
                        logger.warning(f"[PDFPLUMBER] Error page {page_num}: {str(e)}")
                        result.warnings.append(f"Page {page_num}: {str(e)}")
            
            result.text = text
            result.confidence = result.pages_extracted / result.total_pages if result.total_pages > 0 else 0
            result.extraction_quality = PDFExtractor._rate_extraction_quality(result)
            
            return result
        
        except Exception as e:
            logger.error(f"[PDFPLUMBER] Error: {str(e)}")
            result.error = str(e)
            return result
    
    @staticmethod
    def _extract_pdf_ocr(file_path: str) -> ExtractionResult:
        """OCR extraction - For scanned PDFs"""
        result = ExtractionResult()
        result.method = "ocr"
        
        try:
            doc = fitz.open(file_path)
            result.total_pages = len(doc)
            text = ""
            ocr_confidences = []
            
            for page_num, page in enumerate(doc, 1):
                try:
                    # Render page to image
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better OCR
                    img_data = pix.tobytes("ppm")
                    img = Image.open(io.BytesIO(img_data))
                    
                    # OCR extraction
                    page_text = pytesseract.image_to_string(img)
                    
                    # Get OCR confidence
                    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
                    confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                    if confidences:
                        page_confidence = sum(confidences) / len(confidences)
                        ocr_confidences.append(page_confidence)
                    
                    if not PDFExtractor._is_binary_junk(page_text):
                        text += page_text + "\n"
                        result.pages_extracted += 1
                
                except Exception as e:
                    logger.warning(f"[OCR] Error page {page_num}: {str(e)}")
                    result.warnings.append(f"Page {page_num} OCR failed: {str(e)}")
            
            doc.close()
            result.text = text
            result.confidence = sum(ocr_confidences) / len(ocr_confidences) / 100 if ocr_confidences else 0
            result.extraction_quality = PDFExtractor._rate_extraction_quality(result)
            
            return result
        
        except Exception as e:
            logger.error(f"[OCR] Error: {str(e)}")
            result.error = str(e)
            return result
    
    @staticmethod
    def _extract_image(file_path: str) -> ExtractionResult:
        """Extract from image using OCR"""
        result = ExtractionResult()
        result.method = "ocr"
        result.total_pages = 1
        
        try:
            img = Image.open(file_path)
            
            # Extract text
            text = pytesseract.image_to_string(img)
            
            # Get confidence
            data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            if confidences:
                result.confidence = sum(confidences) / len(confidences) / 100
                result.pages_extracted = 1
            
            result.text = text
            result.extraction_quality = PDFExtractor._rate_extraction_quality(result)
            
            return result
        
        except Exception as e:
            logger.error(f"[IMAGE] Error: {str(e)}")
            result.error = str(e)
            return result
    
    @staticmethod
    def _extract_text_file(file_path: str) -> ExtractionResult:
        """Extract from plain text file"""
        result = ExtractionResult()
        result.method = "plaintext"
        result.total_pages = 1
        result.pages_extracted = 1
        result.confidence = 1.0
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                result.text = f.read()
            
            result.extraction_quality = PDFExtractor._rate_extraction_quality(result)
            return result
        
        except Exception as e:
            logger.error(f"[TEXT] Error: {str(e)}")
            result.error = str(e)
            return result
    
    @staticmethod
    def _is_binary_junk(text: str) -> bool:
        """Check if extracted text is mostly binary junk or non-readable"""
        if not text or len(text.strip()) < 10:
            return True
        
        # CHECK 1: Binary file header detection (BINARY_PATTERNS - hard rejection)
        text_start = text[:200] if len(text) > 200 else text
        for pattern in PDFExtractor.BINARY_PATTERNS:
            try:
                if re.search(pattern, text_start, re.IGNORECASE):
                    logger.debug(f"[BINARY] Hard rejection - detected pattern: {pattern}")
                    return True
            except:
                pass
        
        # CHECK 2: Explicit %PDF marker at start (hard rejection for corrupted PDFs)
        if text.strip().startswith("%PDF"):
            logger.debug(f"[BINARY] Hard rejection - detected %PDF marker at start")
            return True
        
        # CHECK 3: Count undecodable/control characters (soft threshold)
        # Count control chars (0x00-0x1F except \n\r\t) - these indicate binary data
        control_chars = sum(1 for c in text if ord(c) < 32 and c not in '\n\r\t')
        # Count null/high-control bytes that are definitely binary
        binary_bytes = sum(1 for c in text if ord(c) == 0 or ord(c) in range(1, 9) or ord(c) in range(14, 32))
        
        total = len(text)
        
        # If > 20% control/binary chars, it's likely junk
        binary_ratio = binary_bytes / total if total > 0 else 0
        control_ratio = control_chars / total if total > 0 else 0
        
        is_junk = binary_ratio > 0.2 or control_ratio > 0.2
        if is_junk:
            logger.debug(f"[BINARY] High control chars: binary={binary_ratio:.0%}, control={control_ratio:.0%}")
        
        return is_junk
    
    @staticmethod
    def _clean_text(text: str) -> str:
        """Remove noise, binary junk, and normalize whitespace"""
        if not text:
            return ""
        
        # Apply cleaning patterns
        for pattern, replacement in PDFExtractor.NOISE_PATTERNS:
            text = re.sub(pattern, replacement, text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Remove lines that are mostly special characters
        lines = text.split('\n')
        clean_lines = []
        for line in lines:
            # Keep line if it has meaningful content (>50% alphanumeric or space)
            meaningful = sum(1 for c in line if c.isalnum() or c.isspace())
            if len(line) == 0 or (len(line) > 0 and meaningful / len(line) > 0.5):
                clean_lines.append(line)
        
        return '\n'.join(clean_lines)
    
    @staticmethod
    def _validate_extraction(result: ExtractionResult) -> None:
        """Validate extraction quality and set warnings"""
        if not result.text:
            result.extraction_quality = "low"
            return
        
        text_len = len(result.text.strip())
        
        # Check minimum length
        if text_len < 100:
            result.warnings.append(f"Very short extraction ({text_len} chars)")
            result.extraction_quality = "low"
        elif text_len < 500:
            result.warnings.append(f"Short extraction ({text_len} chars)")
            if result.extraction_quality == "unknown":
                result.extraction_quality = "medium"
        
        # Check page extraction rate
        if result.total_pages > 0:
            extraction_rate = result.pages_extracted / result.total_pages
            if extraction_rate < 0.5:
                result.warnings.append(f"Low page extraction rate ({extraction_rate:.0%})")
    
    @staticmethod
    def _rate_extraction_quality(result: ExtractionResult) -> str:
        """Rate extraction quality as high/medium/low"""
        if result.error or not result.text or len(result.text.strip()) < 100:
            return "low"
        
        # Page extraction rate
        page_rate = result.pages_extracted / result.total_pages if result.total_pages > 0 else 0
        
        # Confidence score
        confidence = result.confidence
        
        if page_rate > 0.9 and confidence > 0.85:
            return "high"
        elif page_rate > 0.75 or confidence > 0.7:
            return "medium"
        else:
            return "low"
    
    @staticmethod
    def _standardize_table(table_data: list) -> str:
        """Convert table data to standardized CSV-like format with pipe separators"""
        if not table_data or len(table_data) == 0:
            return ""
        
        # Convert all cells to strings and sanitize
        rows = []
        for row in table_data:
            sanitized_row = []
            for cell in row:
                if cell is None:
                    sanitized_row.append("")
                else:
                    # Convert to string and remove newlines for proper formatting
                    cell_str = str(cell).replace("\n", " ").replace("\r", " ").strip()
                    sanitized_row.append(cell_str)
            rows.append(sanitized_row)
        
        # Format with pipe separators and consistent spacing
        table_lines = []
        for row in rows:
            # Pipe-separated values: "col1 | col2 | col3"
            line = " | ".join(row)
            table_lines.append(line)
        
        # Add header separator if more than 1 row (markdown-style)
        if len(table_lines) > 1:
            header = table_lines[0]
            # Create separator with dashes matching header
            separator = " | ".join(["---" for _ in rows[0]]) if rows else ""
            return header + "\n" + separator + "\n" + "\n".join(table_lines[1:])
        
        return "\n".join(table_lines)
    
    @staticmethod
    def _calculate_text_confidence(text: str) -> float:
        """Calculate confidence score based on text characteristics"""
        if not text:
            return 0.0
        
        # Count different text characteristics
        total_chars = len(text)
        
        # Alphanumeric characters (higher = better)
        alphanumeric = sum(1 for c in text if c.isalnum())
        alphanumeric_ratio = alphanumeric / total_chars
        
        # Whitespace and structure (should be reasonable)
        whitespace = sum(1 for c in text if c.isspace())
        whitespace_ratio = whitespace / total_chars
        
        # Punctuation (reasonable amount)
        punctuation = sum(1 for c in text if c in '.,;:!?-()[]{}')
        punctuation_ratio = punctuation / total_chars
        
        # Calculate score
        # Good: 60-70% alphanumeric, 20-30% whitespace, 5-15% punctuation
        score = 0.0
        
        if 0.5 < alphanumeric_ratio < 0.8:
            score += 0.4
        elif 0.4 < alphanumeric_ratio < 0.9:
            score += 0.3
        else:
            score += 0.1
        
        if 0.15 < whitespace_ratio < 0.35:
            score += 0.3
        elif 0.1 < whitespace_ratio < 0.4:
            score += 0.2
        else:
            score += 0.1
        
        if 0.01 < punctuation_ratio < 0.2:
            score += 0.3
        else:
            score += 0.1
        
        return min(1.0, score)
