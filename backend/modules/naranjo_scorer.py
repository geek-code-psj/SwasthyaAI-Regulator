"""
Naranjo Algorithm for Causality Assessment in Pharmacovigilance
Scores: 0-13 (higher = more probable causality)
Output: Naranjo score + Probability (Unrelated/Unlikely/Possible/Probable)

CDSCO mandates Naranjo for SAE assessment.
"""

import re
import logging
from typing import Dict, Optional
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class NaranjoProb(Enum):
    """Naranjo probability categories"""
    UNRELATED = "Unrelated"
    UNLIKELY = "Unlikely"
    POSSIBLE = "Possible"
    PROBABLE = "Probable"


@dataclass
class NaranjoScore:
    """Naranjo assessment result"""
    total_score: int  # 0-13
    probability: str  # Unrelated/Unlikely/Possible/Probable
    scoring_breakdown: Dict[str, int] = None
    reasoning: str = ""
    version: str = "Standard Naranjo 1981"
    
    def __post_init__(self):
        if self.scoring_breakdown is None:
            self.scoring_breakdown = {}


class NaranjoScorer:
    """
    Naranjo Causality Algorithm for SAE assessment.
    
    Questions (10 main + 1 bonus):
    1. Temporal: When did event occur relative to drug dose?
    2. Dose-response: Does severity correlate with dose?
    3. Prior knowledge: Known reaction with this drug?
    4. De-challenge: Did event resolve after stopping drug?
    5. Re-challenge: Did event recur on re-exposure?
    6. Alternative causes: Could another factor explain event?
    7. Adverse reaction history: Prior allergies?
    8. Blood/body fluid test: Drug detected in lab?
    9. Dose-response relation: Quantitative correlation?
    10. Previous literature: Similar reports in literature?
    11. Bonus: Temporal relation >3 months (negative)
    """
    
    def __init__(self):
        self.keywords = {
            # --- TEMPORAL RELATIONSHIP (IMPROVED WITH REGEX PATTERNS) ---
            "onset_immediate": ["immediately", "at the time", "during", "concurrent", "same day", "concurrent"],
            "onset_2days": ["2 days", "48 hours", "day 1", "day 2", "within 48", "post-", "post dose", "hours post", "days post", "hours after"],
            "onset_5_30days": ["5 days", "1 week", "2 weeks", "3 weeks", "4 weeks", "month", "week"],
            
            # --- DOSE RESPONSE ---
            "dose_increase": ["dose increased", "higher dose", "when dose increased", "dose escalation"],
            "dose_therapeutic": ["therapeutic dose", "standard dose", "recommended dose"],
            
            # --- PRIOR KNOWLEDGE ---
            "known_reaction": ["known", "reported", "documented", "literature", "case report", "fda", "similar"],
            
            # --- DE-CHALLENGE ---
            "stopped_drug": ["stopped", "discontinued", "withdrew", "cessation", "stopped medication", "able to stop", "cessation", "discontinuation", "withdrawal"],
            "resolved": ["resolved", "improved", "recovered", "symptom disappeared", "remitted"],
            
            # --- RE-CHALLENGE ---
            "restarted_drug": ["restarted", "re-exposed", "re-challenged", "reintroduced", "rechallenge"],
            "recurred": ["recurred", "reappeared", "happened again", "repeated", "returned"],
            
            # --- ALTERNATIVE CAUSES ---
            "alternative_cause": ["infection", "disease", "allergy", "condition", "pre-existing", "comorbidity"],
            
            # --- SEVERITY ---
            "death": ["death", "died", "fatal", "expired", "deceased", "passing"],
            "disability": ["disability", "permanent", "loss of function", "permanent damage"],
            "hospitalization": ["hospitalized", "admission", "admitted", "hospitalization"],
        }
    
    
    def score_narrative(self, narrative: str) -> NaranjoScore:
        """
        Score an SAE narrative using Naranjo algorithm.
        
        Args:
            narrative: SAE case description (text)
        
        Returns:
            NaranjoScore with total score (0-13) + probability
        """
        
        narrative_lower = narrative.lower()
        scores = {
            "temporal_relationship": 0,
            "dose_response": 0,
            "prior_knowledge": 0,
            "de_challenge": 0,
            "re_challenge": 0,
            "alternative_causes": 0,
            "adverse_history": 0,
            "body_fluid_test": 0,
            "previous_literature": 0,
            "temporal_extended": 0,
        }
        
        explanation_parts = []
        
        # Q1: TEMPORAL RELATIONSHIP (0, +1, or +2)
        # Check with regex for temporal patterns like "48 hours post-dose", "2 days after", etc
        temporal_score = 0
        temp_reasoning = "Temporal relationship: uncertain"
        
        # Check for strong temporal relationship (2-4 days)
        if re.search(r'(?:2|3|4)\s+days?\s+(?:post|after|following)', narrative_lower) or \
           re.search(r'48\s+hours', narrative_lower) or \
           self._contains_keywords(narrative_lower, self.keywords["onset_2days"]):
            temporal_score = 2
            temp_reasoning = "Strong temporal relationship (onset 2-4 days post-dose): +2"
        
        # Check for moderate temporal relationship (5-30 days)
        elif re.search(r'(?:5|6|7|8|9|10|14|21|30)\s+(?:days?|weeks?)', narrative_lower) or \
             self._contains_keywords(narrative_lower, self.keywords["onset_5_30days"]):
            temporal_score = 1
            temp_reasoning = "Reasonable temporal relationship (onset 5-30 days post-dose): +1"
        
        # Check for immediate relationship
        elif self._contains_keywords(narrative_lower, self.keywords["onset_immediate"]):
            temporal_score = 1
            temp_reasoning = "Immediate onset suggests strong relationship: +1"
        
        scores["temporal_relationship"] = temporal_score
        explanation_parts.append(f"1. Temporal relationship: {temp_reasoning}")
        
        
        # Q2: DOSE-RESPONSE (0 or +1)
        if self._contains_keywords(narrative_lower, self.keywords["dose_increase"]):
            scores["dose_response"] = 1
            dose_reasoning = "Dose-response relationship evident: +1"
        else:
            scores["dose_response"] = 0
            dose_reasoning = "No clear dose-response relationship: 0"
        
        explanation_parts.append(f"2. Dose-response: {dose_reasoning}")
        
        # Q3: PRIOR KNOWLEDGE (0 or +1)
        if self._contains_keywords(narrative_lower, self.keywords["known_reaction"]) or \
           re.search(r'(?:similar|known|reported|documented|literature|fda)', narrative_lower):
            scores["prior_knowledge"] = 1
            prior_reasoning = "Known adverse reaction with this drug or similar drugs: +1"
        else:
            scores["prior_knowledge"] = 0
            prior_reasoning = "No prior knowledge of this reaction: 0"
        
        explanation_parts.append(f"3. Prior knowledge: {prior_reasoning}")
        
        
        # Q4: DE-CHALLENGE (0, +1, or +2)
        if self._contains_keywords(narrative_lower, self.keywords["stopped_drug"]):
            if self._contains_keywords(narrative_lower, self.keywords["resolved"]):
                scores["de_challenge"] = 2
                dechallenge_reasoning = "Event resolved after drug cessation: +2"
            else:
                scores["de_challenge"] = 1
                dechallenge_reasoning = "Drug stopped but unclear if resolved: +1"
        else:
            scores["de_challenge"] = 0
            dechallenge_reasoning = "No de-challenge data: 0"
        
        explanation_parts.append(f"4. De-challenge (stopped drug): {dechallenge_reasoning}")
        
        # Q5: RE-CHALLENGE (0, +1, or +2)
        if self._contains_keywords(narrative_lower, self.keywords["restarted_drug"]):
            if self._contains_keywords(narrative_lower, self.keywords["recurred"]):
                scores["re_challenge"] = 2
                rechallenge_reasoning = "Event recurred on re-exposure (strongest evidence): +2"
            else:
                scores["re_challenge"] = 1
                rechallenge_reasoning = "Drug re-exposed but unclear if recurred: +1"
        else:
            scores["re_challenge"] = 0
            rechallenge_reasoning = "No re-challenge data: 0"
        
        explanation_parts.append(f"5. Re-challenge: {rechallenge_reasoning}")
        
        # Q6: ALTERNATIVE CAUSES (-1 or 0)
        # Check for explicit alternative causes (infection, disease, etc)
        if re.search(r'(?:infection|disease|condition|comorbid|pre-existing|history)', narrative_lower) and \
           not re.search(r'(?:no.*alternative|no.*comorbid|clear.*drug)', narrative_lower):
            scores["alternative_causes"] = -1
            alt_reasoning = "Alternative cause identified (reduces causality): -1"
        # But if narrative says NO alternative causes, don't penalize
        elif re.search(r'(?:no.*alternative|no significant.*cause|clear drug|temporal relationship)', narrative_lower):
            scores["alternative_causes"] = 0
            alt_reasoning = "No significant alternative cause identified: 0"
        else:
            scores["alternative_causes"] = 0
            alt_reasoning = "Alternative cause assessment unclear: 0"
        
        explanation_parts.append(f"6. Alternative causes: {alt_reasoning}")
        
        
        # Q7: ADVERSE REACTION HISTORY (0 or +1)
        if re.search(r"(allerg|sensitive|prior|history)", narrative_lower):
            scores["adverse_history"] = 1
            history_reasoning = "History of similar adverse reactions: +1"
        else:
            scores["adverse_history"] = 0
            history_reasoning = "No significant prior adverse history: 0"
        
        explanation_parts.append(f"7. Adverse history: {history_reasoning}")
        
        # Q8: BODY FLUID TEST (0 or +1)
        if re.search(r"(blood|urine|lab|test|detected|concentration|plasma|serum)", narrative_lower):
            scores["body_fluid_test"] = 1
            fluid_reasoning = "Drug or metabolite detected in body fluids: +1"
        else:
            scores["body_fluid_test"] = 0
            fluid_reasoning = "No body fluid testing mentioned: 0"
        
        explanation_parts.append(f"8. Body fluid test: {fluid_reasoning}")
        
        # Q11: EXTENDED TEMPORAL RELATION >3 MONTHS (-1 or 0)
        if re.search(r"(\b3\s+months|\b90\s+days|quarter|3 months|90 days)", narrative_lower):
            scores["temporal_extended"] = -1
            extended_reasoning = "Temporal relationship >3 months (negative factor): -1"
        else:
            scores["temporal_extended"] = 0
            extended_reasoning = "Temporal relationship within 3 months: 0"
        
        explanation_parts.append(f"9. Extended temporal (>3mo): {extended_reasoning}")
        
        # === CALCULATE TOTAL SCORE ===
        total_score = sum(scores.values())
        total_score = max(0, min(total_score, 13))  # Clamp to 0-13 range
        
        # === DETERMINE PROBABILITY ===
        if total_score >= 9:
            probability = NaranjoProb.PROBABLE.value
        elif total_score >= 5:
            probability = NaranjoProb.POSSIBLE.value
        elif total_score >= 1:
            probability = NaranjoProb.UNLIKELY.value
        else:
            probability = NaranjoProb.UNRELATED.value
        
        # === COMPREHENSIVE REASONING ===
        reasoning = "\n".join(explanation_parts) + f"\n\n**Total Score: {total_score}/13**\n**Probability: {probability}**"
        
        logger.info(f"[NARANJO-SCORER] Narrative scored: {total_score}/13 → {probability}")
        
        return NaranjoScore(
            total_score=total_score,
            probability=probability,
            scoring_breakdown=scores,
            reasoning=reasoning
        )
    
    
    def _contains_keywords(self, text: str, keywords: list) -> bool:
        """Check if text contains any of the keywords"""
        return any(keyword in text for keyword in keywords)
    
    
    def score_from_fields(
        self,
        temporal_relationship_days: Optional[int] = None,
        dose_correlated: Optional[bool] = None,
        known_reaction: Optional[bool] = None,
        event_resolved_after_dechallenge: Optional[bool] = None,
        event_recurred_on_rechallenge: Optional[bool] = None,
        alternative_cause_identified: Optional[bool] = None,
    ) -> NaranjoScore:
        """
        Alternative scoring method using structured fields (not narrative parsing).
        Useful when SAE data is already semi-structured.
        """
        
        scores = {
            "temporal_relationship": 0,
            "dose_response": 0,
            "prior_knowledge": 0,
            "de_challenge": 0,
            "re_challenge": 0,
            "alternative_causes": 0,
            "adverse_history": 0,
            "body_fluid_test": 0,
            "previous_literature": 0,
            "temporal_extended": 0,
        }
        
        # Score temporal relationship
        if temporal_relationship_days is not None:
            if 2 <= temporal_relationship_days <= 4:
                scores["temporal_relationship"] = 2
            elif 5 <= temporal_relationship_days <= 30:
                scores["temporal_relationship"] = 1
            elif temporal_relationship_days > 90:
                scores["temporal_extended"] = -1
        
        # Score dose-response
        if dose_correlated is True:
            scores["dose_response"] = 1
        
        # Score prior knowledge
        if known_reaction is True:
            scores["prior_knowledge"] = 1
        
        # Score de-challenge
        if event_resolved_after_dechallenge is True:
            scores["de_challenge"] = 2
        
        # Score re-challenge
        if event_recurred_on_rechallenge is True:
            scores["re_challenge"] = 2
        
        # Score alternative causes
        if alternative_cause_identified is True:
            scores["alternative_causes"] = -1
        
        total_score = sum(scores.values())
        total_score = max(0, min(total_score, 13))
        
        if total_score >= 9:
            probability = NaranjoProb.PROBABLE.value
        elif total_score >= 5:
            probability = NaranjoProb.POSSIBLE.value
        elif total_score >= 1:
            probability = NaranjoProb.UNLIKELY.value
        else:
            probability = NaranjoProb.UNRELATED.value
        
        reasoning = f"Structured field assessment: Score {total_score}/13 → {probability}"
        
        return NaranjoScore(
            total_score=total_score,
            probability=probability,
            scoring_breakdown=scores,
            reasoning=reasoning
        )
