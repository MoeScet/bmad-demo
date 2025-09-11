"""
Content validation and safety checking service for Q&A entries.
"""
from __future__ import annotations

import re
from typing import List, Tuple, Optional
from dataclasses import dataclass
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class ValidationResult:
    """Result of content validation."""
    is_valid: bool
    safety_level: str
    issues: List[str]
    suggested_safety_level: str
    confidence_score: float


class ContentValidator:
    """Validates Q&A content for safety and appropriateness."""
    
    # Professional-level keywords requiring expert knowledge
    PROFESSIONAL_KEYWORDS = {
        'electrical', 'wiring', 'voltage', 'amperage', 'circuit', 'breaker',
        'motor', 'transmission', 'drive belt', 'coupling', 'capacitor',
        'solenoid', 'valve', 'pump motor', 'control board', 'pcb',
        'continuity', 'multimeter', 'ohm', 'resistance', 'short circuit',
        'ground fault', 'gfci', 'electrical shock', 'live wire'
    }
    
    # Caution-level keywords requiring careful attention
    CAUTION_KEYWORDS = {
        'bleach', 'chemical', 'hot water', 'drain hose', 'water leak',
        'flooding', 'slip hazard', 'heavy lifting', 'moving parts',
        'sharp edges', 'pinch point', 'crush hazard', 'high pressure',
        'steam', 'scalding', 'toxic', 'ventilation', 'gas leak'
    }
    
    # Prohibited content patterns
    PROHIBITED_PATTERNS = [
        r'\b(?:hack|crack|bypass|override)\b.*(?:safety|lock|protection)',
        r'\bdiy\s+electrical\s+repair\b',
        r'\bremove\s+safety\s+features?\b',
        r'\bdisable\s+(?:safety|protection|interlock)\b',
        r'\bunplug.*while.*running\b',
        r'\btouch.*live.*wire\b',
        r'\bforce.*(?:door|lid).*open\b'
    ]
    
    # Safety-promoting patterns
    SAFETY_PATTERNS = [
        r'\bunplug.*(?:before|first)\b',
        r'\bturn\s+off.*(?:power|breaker)\b',
        r'\bcontact.*(?:professional|technician|service)\b',
        r'\bdo\s+not.*(?:touch|handle|attempt)\b',
        r'\bsafety.*(?:first|precaution|warning)\b'
    ]
    
    def validate_content(
        self, 
        question: str, 
        answer: str, 
        keywords: Optional[List[str]] = None
    ) -> ValidationResult:
        """
        Validate Q&A content for safety and appropriateness.
        
        Args:
            question: The question text
            answer: The answer text  
            keywords: Optional list of keywords
            
        Returns:
            ValidationResult with validation status and recommendations
        """
        issues = []
        safety_scores = {'safe': 0, 'caution': 0, 'professional': 0}
        
        # Combine all text for analysis
        combined_text = f"{question} {answer}".lower()
        keyword_text = " ".join(keywords or []).lower()
        full_text = f"{combined_text} {keyword_text}"
        
        # Check for prohibited content
        prohibited_found = self._check_prohibited_content(full_text)
        if prohibited_found:
            issues.extend(prohibited_found)
            return ValidationResult(
                is_valid=False,
                safety_level="rejected",
                issues=issues,
                suggested_safety_level="rejected", 
                confidence_score=1.0
            )
        
        # Analyze safety keywords
        professional_matches = self._find_keyword_matches(full_text, self.PROFESSIONAL_KEYWORDS)
        caution_matches = self._find_keyword_matches(full_text, self.CAUTION_KEYWORDS)
        
        # Score based on keyword matches
        if professional_matches:
            safety_scores['professional'] += len(professional_matches) * 2
            issues.append(f"Contains professional-level topics: {', '.join(professional_matches[:3])}")
            
        if caution_matches:
            safety_scores['caution'] += len(caution_matches)
            issues.append(f"Contains caution-level topics: {', '.join(caution_matches[:3])}")
        
        # Check for safety-promoting language
        safety_promoting = self._find_safety_patterns(answer)
        if safety_promoting:
            # Reduce risk levels if safety language is present
            safety_scores['safe'] += len(safety_promoting)
            safety_scores['caution'] = max(0, safety_scores['caution'] - 1)
            safety_scores['professional'] = max(0, safety_scores['professional'] - 1)
        
        # Analyze answer complexity and risk factors
        complexity_score = self._analyze_complexity(answer)
        if complexity_score > 7:
            safety_scores['professional'] += 1
            issues.append("High complexity procedure detected")
        elif complexity_score > 4:
            safety_scores['caution'] += 1
        
        # Check for specific risk indicators
        risk_indicators = self._check_risk_indicators(answer)
        if risk_indicators:
            safety_scores['professional'] += len(risk_indicators)
            issues.extend([f"Risk indicator: {indicator}" for indicator in risk_indicators])
        
        # Determine final safety level
        suggested_safety_level = self._determine_safety_level(safety_scores)
        confidence_score = self._calculate_confidence(safety_scores, len(issues))
        
        # Content is valid if not prohibited
        is_valid = True
        
        logger.info(
            "Content validation completed",
            service="fast-qa",
            safety_level=suggested_safety_level,
            confidence=confidence_score,
            issues_count=len(issues),
            professional_matches=len(professional_matches),
            caution_matches=len(caution_matches)
        )
        
        return ValidationResult(
            is_valid=is_valid,
            safety_level=suggested_safety_level,
            issues=issues,
            suggested_safety_level=suggested_safety_level,
            confidence_score=confidence_score
        )
    
    def _check_prohibited_content(self, text: str) -> List[str]:
        """Check for prohibited content patterns."""
        violations = []
        for pattern in self.PROHIBITED_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                violations.append(f"Prohibited pattern detected: {pattern}")
        return violations
    
    def _find_keyword_matches(self, text: str, keywords: set) -> List[str]:
        """Find matching keywords in text."""
        found = []
        for keyword in keywords:
            if re.search(r'\b' + re.escape(keyword) + r'\b', text, re.IGNORECASE):
                found.append(keyword)
        return found
    
    def _find_safety_patterns(self, text: str) -> List[str]:
        """Find safety-promoting patterns."""
        found = []
        for pattern in self.SAFETY_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                found.extend(matches)
        return found
    
    def _analyze_complexity(self, answer: str) -> int:
        """Analyze procedural complexity of the answer."""
        complexity_indicators = [
            r'\bstep\s+\d+\b',           # Numbered steps
            r'\b(?:first|then|next|finally)\b',  # Sequence words
            r'\btool\b',                # Tool requirements
            r'\bmeasure\b',             # Measurements needed
            r'\bdisassemble\b',         # Taking apart
            r'\bremove.*\bscrew\b',     # Hardware removal
            r'\btechnician\b',          # Professional recommendation
            r'\bwarning\b',             # Warning indicators
        ]
        
        complexity_score = 0
        for pattern in complexity_indicators:
            matches = len(re.findall(pattern, answer, re.IGNORECASE))
            complexity_score += matches
        
        # Length-based complexity
        if len(answer) > 200:
            complexity_score += 1
        if len(answer) > 400:
            complexity_score += 1
            
        return complexity_score
    
    def _check_risk_indicators(self, answer: str) -> List[str]:
        """Check for specific risk indicators."""
        risk_patterns = {
            'electrical': r'\b(?:electrical|voltage|current|shock)\b',
            'mechanical': r'\b(?:moving\s+parts|crush|pinch)\b',
            'chemical': r'\b(?:chemical|toxic|bleach|acid)\b',
            'thermal': r'\b(?:hot|heat|burn|scald)\b',
            'structural': r'\b(?:heavy|lift|support|structural)\b'
        }
        
        found_risks = []
        for risk_type, pattern in risk_patterns.items():
            if re.search(pattern, answer, re.IGNORECASE):
                found_risks.append(risk_type)
        
        return found_risks
    
    def _determine_safety_level(self, safety_scores: dict) -> str:
        """Determine the appropriate safety level based on scores."""
        max_score = max(safety_scores.values())
        
        if max_score == 0:
            return 'safe'
        
        # Find the category with the highest score
        for level, score in safety_scores.items():
            if score == max_score:
                return level
        
        return 'safe'  # Default fallback
    
    def _calculate_confidence(self, safety_scores: dict, issues_count: int) -> float:
        """Calculate confidence score for the validation."""
        total_score = sum(safety_scores.values())
        
        if total_score == 0:
            return 0.8  # High confidence for clearly safe content
        
        # Higher scores and more issues = higher confidence in classification
        confidence = min(0.5 + (total_score * 0.1) + (issues_count * 0.05), 1.0)
        return round(confidence, 2)


# Service instance
content_validator = ContentValidator()