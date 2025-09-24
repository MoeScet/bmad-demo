"""
Unit tests for text cleaning and normalization
"""

import pytest
from src.processing.text_cleaner import TextCleaner


class TestTextCleaner:
    """Test suite for TextCleaner class"""

    @pytest.fixture
    def cleaner(self):
        """Create TextCleaner instance for testing"""
        return TextCleaner()

    def test_cleaner_initialization(self, cleaner):
        """Test cleaner initializes correctly"""
        assert cleaner.artifact_patterns is not None
        assert cleaner.section_patterns is not None
        assert len(cleaner.artifact_patterns) > 0
        assert len(cleaner.section_patterns) > 0

    def test_clean_text_empty_input(self, cleaner):
        """Test cleaning empty or None input"""
        assert cleaner.clean_text("") == ""
        assert cleaner.clean_text(None) == ""

    def test_clean_text_whitespace_normalization(self, cleaner):
        """Test whitespace and line break normalization"""
        test_cases = [
            # Multiple spaces
            ("This  has   multiple    spaces", "This has multiple spaces"),
            # Single line breaks within paragraphs
            ("Line one\nLine two", "Line one Line two"),
            # Preserve paragraph breaks
            ("Paragraph one\n\nParagraph two", "Paragraph one\n\nParagraph two"),
            # Mixed whitespace
            ("Text\t\twith\t\ttabs", "Text with tabs"),
        ]

        for input_text, expected in test_cases:
            result = cleaner.clean_text(input_text)
            assert expected in result or result.strip() == expected.strip()

    def test_clean_text_encoding_fixes(self, cleaner):
        """Test common encoding issue fixes"""
        test_cases = [
            ("Itâ€™s working", "It's working"),
            ("â€œQuotedâ€ text", '"Quoted" text'),
            ("Temperature: 100Â°F", "Temperature: 100°F"),
            ("Brandâ„¢ name", "Brand™ name"),
        ]

        for input_text, expected in test_cases:
            result = cleaner.clean_text(input_text)
            assert expected in result

    def test_clean_text_broken_words_fix(self, cleaner):
        """Test broken word rejoining"""
        input_text = "This is a bro- ken word that should be fixed"
        result = cleaner.clean_text(input_text)
        assert "broken" in result
        assert "bro- ken" not in result

    def test_clean_text_bullet_point_normalization(self, cleaner):
        """Test bullet point standardization"""
        test_cases = [
            ("• First item", "• First item"),
            ("· Second item", "• Second item"),
            ("▪ Third item", "• Third item"),
        ]

        for input_text, expected in test_cases:
            result = cleaner.clean_text(input_text)
            assert "• " in result

    def test_clean_text_measurement_standardization(self, cleaner):
        """Test measurement unit standardization"""
        test_cases = [
            ("24 inches tall", "24 inches"),
            ("5 feet wide", "5 feet"),
            ("10 lbs weight", "10 lbs"),
            ("Temperature 75 degrees f", "75°F"),
            ("Hot water 40 degrees celsius", "40°C"),
        ]

        for input_text, expected_contains in test_cases:
            result = cleaner.clean_text(input_text)
            assert expected_contains in result

    def test_extract_section_title_first_line(self, cleaner):
        """Test section title extraction from first line"""
        text = "Troubleshooting Guide\nThis section covers common problems..."
        title = cleaner.extract_section_title(text)
        assert title == "Troubleshooting Guide"

    def test_extract_section_title_pattern_matching(self, cleaner):
        """Test section title extraction using patterns"""
        test_cases = [
            ("Some intro text\nTroubleshooting steps\nMore content", "Troubleshooting"),
            ("Content\nMaintenance schedule\nDetails", "Maintenance"),
            ("Text\nSafety warnings\nMore text", "Safety"),
        ]

        for text, expected_contains in test_cases:
            title = cleaner.extract_section_title(text)
            assert expected_contains.lower() in title.lower()

    def test_extract_section_title_fallback(self, cleaner):
        """Test section title fallback to first words"""
        text = "This is just regular content without any special section indicators."
        title = cleaner.extract_section_title(text)

        # Should be first few words, truncated if necessary
        assert len(title) <= 100
        assert "This is just regular" in title

    def test_extract_section_title_sentence_boundary(self, cleaner):
        """Test section title respects sentence boundaries"""
        text = "This is a sentence. This is another sentence with more content."
        title = cleaner.extract_section_title(text)

        # Should stop at sentence boundary
        assert title == "This is a sentence."

    def test_validate_text_quality_empty_text(self, cleaner):
        """Test quality validation with empty/short text"""
        assert cleaner.validate_text_quality("") == 0.0
        assert cleaner.validate_text_quality("short") == 0.0
        assert cleaner.validate_text_quality("a") == 0.0

    def test_validate_text_quality_good_text(self, cleaner):
        """Test quality validation with good text"""
        good_text = """
        This is a well-formed paragraph about washing machine troubleshooting.
        The content includes proper sentences with good structure.
        Each sentence has reasonable length and contains meaningful information.
        """
        score = cleaner.validate_text_quality(good_text)
        assert score > 0.5  # Should be reasonably high quality

    def test_validate_text_quality_poor_text(self, cleaner):
        """Test quality validation with poor quality text"""
        poor_cases = [
            # Excessive special characters
            "This@@@@text###has$$$too%%%many^^^special&&&characters!!!",
            # Too many short words
            "a b c d e f g h i j k l m n o p q r s t u v w x y z",
            # Mostly numbers/symbols
            "123456789 !@#$%^&*() 987654321 []{}\\|;:'\",.<>?/",
            # Repetitive content
            "Same line\nSame line\nSame line\nSame line\nSame line\n",
        ]

        for poor_text in poor_cases:
            score = cleaner.validate_text_quality(poor_text)
            assert score < 0.5  # Should be low quality

    def test_validate_text_quality_alphabetic_ratio(self, cleaner):
        """Test quality validation considers alphabetic character ratio"""
        # Text with low alphabetic ratio
        low_alpha = "123 456 789 !@# $%^ &*( )_+ 12345"
        score_low = cleaner.validate_text_quality(low_alpha)

        # Text with high alphabetic ratio
        high_alpha = "This text has mostly alphabetic characters with some numbers 123"
        score_high = cleaner.validate_text_quality(high_alpha)

        assert score_high > score_low

    def test_validate_text_quality_sentence_structure(self, cleaner):
        """Test quality validation considers sentence structure"""
        # Good sentence structure
        good_sentences = "This is sentence one. Here is sentence two. Final sentence here."
        score_good = cleaner.validate_text_quality(good_sentences)

        # Poor sentence structure (no punctuation)
        poor_sentences = "this is all one long run on sentence without any punctuation marks"
        score_poor = cleaner.validate_text_quality(poor_sentences)

        assert score_good > score_poor

    def test_validate_text_quality_meaningful_keywords(self, cleaner):
        """Test quality validation rewards meaningful keywords"""
        # Text with meaningful keywords
        meaningful_text = "Troubleshooting washing machine problems requires maintenance and safety precautions."
        score_meaningful = cleaner.validate_text_quality(meaningful_text)

        # Generic text without keywords
        generic_text = "This is just some random text without any specific domain keywords."
        score_generic = cleaner.validate_text_quality(generic_text)

        assert score_meaningful > score_generic

    def test_validate_text_quality_word_length_distribution(self, cleaner):
        """Test quality validation considers word length distribution"""
        # Text with very short words (OCR artifacts)
        short_words = "a b c d e f g h i j k l m n o p q r s t u v w"
        score_short = cleaner.validate_text_quality(short_words)

        # Text with very long words (concatenation issues)
        long_words = "verylongwordthatmightbeconcatenatedduetoocrissues anotherveryverylongwordhere"
        score_long = cleaner.validate_text_quality(long_words)

        # Text with normal word lengths
        normal_words = "This text has normal word lengths that are appropriate for reading"
        score_normal = cleaner.validate_text_quality(normal_words)

        assert score_normal > score_short
        assert score_normal > score_long

    def test_remove_artifacts_page_numbers(self, cleaner):
        """Test removal of page number artifacts"""
        text_with_page_nums = "page 1\nContent here\n5\nMore content"
        result = cleaner.clean_text(text_with_page_nums)

        # Page numbers should be removed
        assert "page 1" not in result.lower()

    def test_remove_artifacts_header_footer_separators(self, cleaner):
        """Test removal of header/footer separators"""
        text_with_separators = "Content\n---\nMore content\n======\nFinal content"
        result = cleaner.clean_text(text_with_separators)

        # Separators should be removed
        assert "---" not in result
        assert "======" not in result

    def test_standardize_formatting_section_headers(self, cleaner):
        """Test standardization of section headers"""
        text = "troubleshooting section\nmaintenance information\nsafety warnings"
        result = cleaner.clean_text(text)

        # Headers should be title cased
        assert "Troubleshooting" in result
        assert "Maintenance" in result
        assert "Safety" in result


if __name__ == "__main__":
    pytest.main([__file__])