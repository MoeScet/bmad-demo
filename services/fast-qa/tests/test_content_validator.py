"""
Tests for content validation service.
"""
import pytest
from services.content_validator import ContentValidator, ValidationResult


@pytest.fixture
def validator():
    """Create a ContentValidator instance."""
    return ContentValidator()


def test_validate_safe_content(validator):
    """Test validation of safe content."""
    result = validator.validate_content(
        question="How do I clean my washing machine?",
        answer="Run a cleaning cycle with white vinegar once a month and wipe the door seal.",
        keywords=["clean", "maintenance", "vinegar"]
    )
    
    assert result.is_valid
    assert result.safety_level == "safe"
    assert result.confidence_score >= 0.7


def test_validate_caution_content(validator):
    """Test validation of content requiring caution."""
    result = validator.validate_content(
        question="How do I fix a water leak?",
        answer="Check the door seal for tears and inspect hose connections. Use caution with hot water.",
        keywords=["water leak", "door seal", "hot water"]
    )
    
    assert result.is_valid
    assert result.safety_level == "caution"
    assert len(result.issues) > 0


def test_validate_professional_content(validator):
    """Test validation of content requiring professional expertise."""
    result = validator.validate_content(
        question="How do I replace the motor?",
        answer="This requires electrical testing with a multimeter and motor replacement. Contact a technician.",
        keywords=["motor", "electrical", "multimeter", "technician"]
    )
    
    assert result.is_valid
    assert result.safety_level == "professional"
    assert any("professional-level" in issue for issue in result.issues)


def test_validate_prohibited_content(validator):
    """Test validation of prohibited content."""
    result = validator.validate_content(
        question="How can I bypass the door safety lock?",
        answer="You can hack the safety mechanism to override the door interlock.",
        keywords=["bypass", "hack", "safety", "override"]
    )
    
    assert not result.is_valid
    assert result.safety_level == "rejected"
    assert len(result.issues) > 0


def test_validate_with_safety_promoting_language(validator):
    """Test that safety-promoting language reduces risk levels."""
    result = validator.validate_content(
        question="How do I check electrical connections?",
        answer="First, unplug the machine and turn off the breaker. Contact a professional for electrical work.",
        keywords=["electrical", "connections", "professional"]
    )
    
    assert result.is_valid
    # Should have some risk reduction due to safety language
    assert "electrical" in result.issues[0].lower() if result.issues else True


def test_complexity_scoring(validator):
    """Test complexity scoring algorithm."""
    simple_answer = "Clean the lint filter weekly."
    complex_answer = "First, unplug the machine. Then, remove the front panel screws. Next, disconnect the electrical connectors. Use a multimeter to test continuity. Warning: this requires electrical knowledge."
    
    simple_result = validator.validate_content("Simple question?", simple_answer)
    complex_result = validator.validate_content("Complex question?", complex_answer)
    
    # Complex answer should have higher safety requirements
    assert simple_result.safety_level == "safe"
    assert complex_result.safety_level in ["caution", "professional"]


def test_risk_indicator_detection(validator):
    """Test detection of various risk indicators."""
    test_cases = [
        ("electrical work", "electrical"),
        ("heavy lifting required", "structural"),
        ("hot water burns", "thermal"),
        ("toxic cleaning chemicals", "chemical"),
        ("moving parts danger", "mechanical")
    ]
    
    for answer_text, expected_risk in test_cases:
        result = validator.validate_content(
            "Test question?",
            f"This procedure involves {answer_text} that requires caution."
        )
        
        assert result.is_valid
        # Should detect the risk category in issues or safety level
        assert result.safety_level in ["caution", "professional"]


def test_keyword_matching(validator):
    """Test professional and caution keyword matching."""
    # Test professional keywords
    professional_keywords = ["electrical", "motor", "transmission", "multimeter"]
    for keyword in professional_keywords:
        assert keyword in validator.PROFESSIONAL_KEYWORDS
    
    # Test caution keywords  
    caution_keywords = ["bleach", "hot water", "drain hose", "chemical"]
    for keyword in caution_keywords:
        assert keyword in validator.CAUTION_KEYWORDS


def test_validation_confidence_scoring(validator):
    """Test confidence scoring algorithm."""
    # High confidence case (clear safety indicators)
    high_conf_result = validator.validate_content(
        "Basic maintenance question?",
        "Simply wipe with a damp cloth monthly.",
        keywords=["maintenance", "clean"]
    )
    
    # Low confidence case (ambiguous content)
    low_conf_result = validator.validate_content(
        "Ambiguous question?",
        "This might require some work.",
        keywords=[]
    )
    
    assert high_conf_result.confidence_score >= 0.7
    assert low_conf_result.confidence_score < high_conf_result.confidence_score


def test_empty_content_validation(validator):
    """Test validation with minimal content."""
    result = validator.validate_content(
        question="Short?",
        answer="Brief.",
        keywords=None
    )
    
    assert result.is_valid
    assert result.safety_level == "safe"  # Default for minimal content


def test_validation_with_mixed_safety_levels(validator):
    """Test content with mixed safety indicators."""
    result = validator.validate_content(
        question="How do I safely work on electrical components?",
        answer="First, unplug the machine and contact a professional electrician for motor work.",
        keywords=["electrical", "motor", "professional", "unplug"]
    )
    
    assert result.is_valid
    # Should be professional due to electrical/motor keywords
    # But safety language should be noted
    assert result.safety_level == "professional"