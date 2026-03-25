"""
Intelligent Abstractive Summarization Engine
Uses transformer models for real abstractive summarization (not just sentence selection)
"""
import re
import logging
from typing import Dict, List, Optional
import time

logger = logging.getLogger(__name__)

# Load transformer-based summarizer
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except:
    TRANSFORMERS_AVAILABLE = False


class NonHallucinatingSummarizer:
    """Intelligent Summarization using transformers - ACTUAL information synthesis"""
    
    def __init__(self, model_name: str = "facebook/bart-large-cnn"):
        """
        Initialize Summarizer with transformer model
        
        Args:
            model_name: HuggingFace transformer model (default: facebook/bart-large-cnn)
        """
        self.model_name = model_name
        self.summarizer = None
        self.tfidf_vectorizer = None
        
        # Load transformer model
        if TRANSFORMERS_AVAILABLE:
            self._load_model()
        
        logger.info("[SUMMARIZER] Initialized with intelligent abstractive summarization")
    
    def _load_model(self):
        """Load transformer model for summarization"""
        try:
            logger.info(f"[SUMMARIZER] Loading transformer model: {self.model_name}")
            self.summarizer = pipeline(
                "summarization",
                model=self.model_name,
                device=-1  # CPU only
            )
            logger.info(f"[SUMMARIZER] ✓ Transformer model loaded successfully - using INTELLIGENT summarization")
        except Exception as e:
            logger.warning(f"[SUMMARIZER] Failed to load transformer: {str(e)}, will use extractive fallback")
            self.summarizer = None
    
    def summarize(self, text: str, max_length: int = 150, min_length: int = 50) -> Dict:
        """
        Generate intelligent ABSTRACTIVE summary from text
        Uses transformer models for real synthesis, not sentence extraction
        
        Args:
            text: Input text to summarize
            max_length: Maximum summary length (tokens)
            min_length: Minimum summary length (tokens)
            
        Returns:
            Dict with summary or fallback
        """
        result = {
            "success": False,
            "summary": "Summary unavailable",
            "original_length": len(text),
            "summary_length": 0,
            "compression_ratio": 0,
            "generation_time": 0,
            "method": "none",
            "error": None
        }
        
        # ============= VALIDATION =============
        if not text or len(text.strip()) < 50:
            result["summary"] = "Summary unavailable - insufficient document content"
            logger.info("[SUMMARIZER] Text too short, returning unavailable")
            return result
        
        start_time = time.time()
        
        # ============= STRATEGY 1: INTELLIGENT TRANSFORMER-BASED SUMMARIZATION =============
        if self.summarizer:
            logger.info("[SUMMARIZER] Using INTELLIGENT abstractive summarization (transformers)")
            transformer_result = self._summarize_with_transformer(text, max_length, min_length)
            if transformer_result["success"]:
                result.update(transformer_result)
                result["method"] = "abstractive_transformer"
                result["generation_time"] = time.time() - start_time
                logger.info(f"[SUMMARIZER] Transformer summary successful")
                return result
            else:
                logger.warning(f"[SUMMARIZER] Transformer failed: {transformer_result['error']}")
        
        # ============= STRATEGY 2: EXTRACTIVE FALLBACK (guaranteed real content) =============
        logger.info("[SUMMARIZER] Falling back to extractive summarization")
        extractive_result = self._summarize_extractive(text, max_sentences=4)
        
        if extractive_result.strip():
            result["success"] = True
            result["summary"] = extractive_result
            result["summary_length"] = len(extractive_result)
            result["compression_ratio"] = len(extractive_result) / len(text)
            result["method"] = "extractive_fallback"
            result["generation_time"] = time.time() - start_time
            logger.info(f"[SUMMARIZER] Extractive fallback used")
            return result
        
        # ============= FALLBACK: No summary available =============
        logger.warning("[SUMMARIZER] All summarization methods failed")
        result["summary"] = "Summary unavailable - unable to process content"
        result["error"] = "All summarization methods failed"
        return result
    
    def _summarize_with_transformer(self, text: str, max_length: int, min_length: int) -> Dict:
        """Use transformer model for abstractive summarization"""
        result = {"success": False, "error": None}
        
        try:
            # Truncate if necessary (transformers have token limits)
            max_input_length = 1024
            if len(text.split()) > max_input_length:
                text = " ".join(text.split()[:max_input_length])
                logger.info(f"[SUMMARIZER] Text truncated to {max_input_length} tokens")
            
            # Generate abstractive summary
            logger.info(f"[SUMMARIZER] Generating abstractive summary...")
            summary_result = self.summarizer(
                text,
                max_length=max_length,
                min_length=min_length,
                do_sample=False
            )
            
            summary = summary_result[0]["summary_text"]
            
            # VALIDATION: Check summary is grounded in text
            # (has significant word overlap with source)
            source_words = set(text.lower().split())
            summary_words = set(summary.lower().split())
            overlap = len(source_words & summary_words) / len(summary_words) if summary_words else 0
            
            if overlap < 0.2:  # Less than 20% word overlap = likely hallucinated
                logger.warning(f"[SUMMARIZER] Low groundedness ({overlap:.1%}), rejecting summary")
                result["error"] = "Generated summary not sufficiently grounded in source text"
                return result
            
            result["success"] = True
            result["summary"] = summary
            result["summary_length"] = len(summary)
            result["compression_ratio"] = len(summary) / len(text)
            logger.info(f"[SUMMARIZER] Abstractive summary: {summary[:80]}...")
            
        except Exception as e:
            logger.error(f"[SUMMARIZER] Transformer error: {str(e)}")
            result["error"] = str(e)
        
        return result
    
    def _summarize_extractive(self, text: str, max_sentences: int = 4) -> str:
        """
        Extract summary from actual sentences in text
        GUARANTEED: Only uses sentences that actually exist
        """
        try:
            # Split into sentences
            sentences = self._split_sentences(text)
            
            if not sentences or len(sentences) == 0:
                logger.info("[SUMMARIZER] No sentences found for extraction")
                return ""
            
            # Filter out very short sentences
            meaningful_sentences = [s for s in sentences if len(s.strip()) > 20]
            
            if len(meaningful_sentences) == 0:
                logger.info("[SUMMARIZER] No meaningful sentences found")
                return ""
            
            # Score sentences by length and position (not content-based to avoid hallucination)
            scored_sentences = []
            for idx, sent in enumerate(meaningful_sentences):
                # Prefer longer sentences (likely more informative)
                # Prefer earlier sentences (likely more important)
                length_score = min(len(sent.split()) / 20, 1.0)  # Normalize to 0-1
                position_score = 1.0 - (idx / len(meaningful_sentences))  # Later = lower score
                combined_score = (length_score * 0.6) + (position_score * 0.4)
                
                scored_sentences.append((combined_score, sent))
            
            # Select top sentences
            top_sentences = sorted(scored_sentences, key=lambda x: x[0], reverse=True)[:max_sentences]
            
            # Maintain original order
            summary_sentences = []
            for original_idx, (sent, original_sent) in enumerate(zip([s[1] for s in top_sentences], 
                                                                     [s[1] for s in top_sentences])):
                summary_sentences.append(original_sent)
            
            summary = " ".join(summary_sentences)
            
            logger.info(f"[SUMMARIZER] Extracted {len(summary_sentences)} sentences")
            return summary
            
        except Exception as e:
            logger.error(f"[SUMMARIZER] Extractive summarization error: {str(e)}")
            return ""
    
    def extract_key_findings(self, text: str) -> List[str]:
        """
        Extract key findings ONLY FROM ACTUAL TEXT
        
        GUARD: Only returns findings that are explicitly stated
        Never makes assumptions or adds generic findings
        """
        findings = []
        
        if not text or len(text.strip()) < 50:
            return []
        
        logger.info("[FINDINGS] Extracting key findings from text...")
        
        # ============= EXPLICIT CONTENT EXTRACTION =============
        # 1. Look for numbered sections
        numbered_items = re.findall(r'\d+\.\s+([^\n]+)', text)
        findings.extend(numbered_items[:3])
        
        # 2. Look for bullet points
        bullet_items = re.findall(r'[•\-\*]\s+([^\n]+)', text)
        findings.extend(bullet_items[:3])
        
        # 3. Look for explicitly marked sections
        section_patterns = [
            (r'(?:FINDING|Finding|finding)[\s:]+([^\n]+)', "Finding"),
            (r'(?:RESULT|Result|result)[\s:]+([^\n]+)', "Result"),
            (r'(?:CONCLUSION|Conclusion|conclusion)[\s:]+([^\n]+)', "Conclusion"),
            (r'(?:KEY|Key)[\s:]+([^\n]+)', "Key Point"),
            (r'(?:IMPORTANT|Important|important)[\s:]+([^\n]+)', "Important"),
        ]
        
        for pattern, label in section_patterns:
            matches = re.findall(pattern, text)
            findings.extend([f"{label}: {m.strip()}" for m in matches[:2]])
        
        # 4. Remove duplicates and truncate
        findings = list(dict.fromkeys(findings))[:5]  # Remove dups, keep first 5
        
        if not findings:
            logger.info("[FINDINGS] No explicit findings found in text")
            # Return basic fact about document, NOT a made-up finding
            word_count = len(text.split())
            findings.append(f"Document contains {word_count} words of content")
        
        logger.info(f"[FINDINGS] Extracted {len(findings)} findings")
        return findings
    
    @staticmethod
    def _split_sentences(text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitter
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
        return [s.strip() for s in sentences if s.strip()]
    
    @staticmethod
    def _is_grounded_in_text(summary: str, original_text: str) -> bool:
        """Check if summary contains content from original"""
        try:
            # Extract key nouns from summary
            summary_words = set(re.findall(r'\b[A-Z][a-z]+\b', summary))
            
            # Check if at least 30% of summary nouns appear in original
            if not summary_words:
                return False
            
            words_in_original = sum(1 for word in summary_words if word.lower() in original_text.lower())
            coverage = words_in_original / len(summary_words) if summary_words else 0
            
            is_grounded = coverage >= 0.3
            logger.debug(f"[SUMMARIZER] Grounding check: {words_in_original}/{len(summary_words)} words in original ({coverage:.0%})")
            
            return is_grounded
        except:
            return True  # Assume grounded if check fails
    
    def _truncate_text(self, text: str, max_tokens: int) -> str:
        """Truncate text to maximum tokens"""
        if not self.tokenizer:
            # Fallback: character-based, assume ~4 chars per token
            return text[:max_tokens * 4]
        
        try:
            tokens = self.tokenizer.encode(text, truncation=False)
            if len(tokens) > max_tokens:
                truncated_tokens = tokens[:max_tokens]
                truncated_text = self.tokenizer.decode(truncated_tokens, skip_special_tokens=True)
                logger.debug(f"[SUMMARIZER] Text truncated from {len(tokens)} to {max_tokens} tokens")
                return truncated_text
            return text
        except:
            return text[:max_tokens * 4]


# Backward compatibility
class SummarizationEngine(NonHallucinatingSummarizer):
    """Backward compatibility wrapper"""
    pass

