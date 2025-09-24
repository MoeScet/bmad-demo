"""
Unit tests for quality validation functionality
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from src.processing.quality_validator import QualityValidator


class TestQualityValidator:
    """Test suite for QualityValidator class"""

    @pytest.fixture
    def validator(self):
        """Create QualityValidator instance for testing"""
        return QualityValidator()

    def test_validator_initialization(self, validator):
        """Test validator initializes correctly"""
        assert validator.settings is not None

    @pytest.mark.asyncio
    async def test_calculate_readability_score_empty_text(self, validator):
        """Test readability score for empty text"""
        score = await validator.calculate_readability_score("")
        assert score == 0.0

        score = await validator.calculate_readability_score(None)
        assert score == 0.0

    @pytest.mark.asyncio
    async def test_calculate_readability_score_short_text(self, validator):
        """Test readability score for text below minimum length"""
        short_text = "Short"
        score = await validator.calculate_readability_score(short_text)
        assert score == 0.0

    @pytest.mark.asyncio
    async def test_calculate_readability_score_good_text(self, validator, quality_test_texts):
        """Test readability score for high quality text"""
        score = await validator.calculate_readability_score(quality_test_texts["high_quality"])
        assert score > 0.7  # Should be high quality

    @pytest.mark.asyncio
    async def test_calculate_readability_score_poor_text(self, validator, quality_test_texts):
        """Test readability score for poor quality text"""
        score = await validator.calculate_readability_score(quality_test_texts["low_quality"])
        assert score < 0.5  # Should be low quality

    @pytest.mark.asyncio
    async def test_calculate_readability_score_ocr_artifacts(self, validator, quality_test_texts):
        """Test readability score for text with OCR artifacts"""
        score = await validator.calculate_readability_score(quality_test_texts["ocr_artifacts"])
        assert score < 0.6  # Should be penalized for artifacts

    @pytest.mark.asyncio
    async def test_calculate_readability_score_factors(self, validator):
        """Test specific factors affecting readability score"""
        # Test excessive special characters
        special_chars_text = "This text has !@#$%^&*() too many special characters !@#$%^&*()"
        score_special = await validator.calculate_readability_score(special_chars_text)

        # Test normal text
        normal_text = "This is normal text with proper sentence structure and good readability."
        score_normal = await validator.calculate_readability_score(normal_text)

        assert score_normal > score_special

    def test_calculate_text_similarity_identical(self, validator):
        """Test text similarity for identical texts"""
        text = "This is a test sentence for similarity calculation."
        similarity = validator._calculate_text_similarity(text, text)
        assert similarity == 1.0

    def test_calculate_text_similarity_different(self, validator):
        """Test text similarity for completely different texts"""
        text1 = "This is about washing machine troubleshooting."
        text2 = "The weather is sunny today with clear skies."
        similarity = validator._calculate_text_similarity(text1, text2)
        assert similarity < 0.3  # Should be very low similarity

    def test_calculate_text_similarity_similar(self, validator):
        """Test text similarity for similar texts"""
        text1 = "Washing machine troubleshooting guide for common problems."
        text2 = "Troubleshooting guide for washing machine common issues."
        similarity = validator._calculate_text_similarity(text1, text2)
        assert 0.5 < similarity < 1.0  # Should be moderately similar

    def test_calculate_text_similarity_empty_input(self, validator):
        """Test text similarity with empty inputs"""
        assert validator._calculate_text_similarity("", "") == 0.0
        assert validator._calculate_text_similarity("text", "") == 0.0
        assert validator._calculate_text_similarity("", "text") == 0.0

    @pytest.mark.asyncio
    async def test_check_for_duplicates_no_duplicates(self, validator, mock_database_session):
        """Test duplicate checking with no duplicates"""
        # Mock database response with different content
        mock_result = Mock()
        mock_result.fetchall.return_value = [
            ("id1", "This is unique content about washing machines."),
            ("id2", "This is completely different content about dryers."),
            ("id3", "Another unique piece of content about maintenance.")
        ]

        with patch('src.processing.quality_validator.get_db_session') as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_database_session
            mock_database_session.execute.return_value = mock_result

            duplicates = await validator.check_for_duplicates("test-correlation")

            assert len(duplicates) == 0

    @pytest.mark.asyncio
    async def test_check_for_duplicates_found(self, validator, mock_database_session):
        """Test duplicate checking with duplicates found"""
        # Mock database response with similar content
        similar_content = "This is very similar content about washing machine troubleshooting steps."
        mock_result = Mock()
        mock_result.fetchall.return_value = [
            ("id1", similar_content),
            ("id2", similar_content + " with slight variation"),  # Very similar
            ("id3", "Completely different content about dryers.")
        ]

        with patch('src.processing.quality_validator.get_db_session') as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_database_session
            mock_database_session.execute.return_value = mock_result

            # Mock settings to have a lower threshold for testing
            validator.settings.DUPLICATE_SIMILARITY_THRESHOLD = 0.8

            duplicates = await validator.check_for_duplicates("test-correlation")

            assert len(duplicates) > 0
            # Should find the similar pair
            duplicate_pair = duplicates[0]
            assert len(duplicate_pair) == 3  # (id1, id2, similarity_score)
            assert duplicate_pair[2] >= 0.8  # Similarity above threshold

    @pytest.mark.asyncio
    async def test_validate_manufacturer_model_valid(self, validator):
        """Test validation of valid manufacturer and model"""
        valid_cases = [
            ("Whirlpool", "WTW5000DW"),
            ("LG", "WM3900HWA"),
            ("Samsung", "WF45R6100AW"),
            ("GE", "GTW465ASNWW")
        ]

        for manufacturer, model in valid_cases:
            result = await validator.validate_manufacturer_model(manufacturer, model)
            assert result is True

    @pytest.mark.asyncio
    async def test_validate_manufacturer_model_invalid(self, validator):
        """Test validation of invalid manufacturer and model"""
        invalid_cases = [
            ("Unknown", "Unknown"),
            ("", ""),
            ("ValidBrand", "X"),  # Too short model
            ("ValidBrand", "Invalid@Model!")  # Invalid characters
        ]

        for manufacturer, model in invalid_cases:
            result = await validator.validate_manufacturer_model(manufacturer, model)
            assert result is False

    @pytest.mark.asyncio
    async def test_generate_quality_report_success(self, validator, mock_database_session):
        """Test successful quality report generation"""
        # Mock database responses
        mock_results = [
            Mock(),  # Total count
            Mock(),  # Content type distribution
            Mock(),  # Manufacturer distribution
            Mock(),  # Quality statistics
            Mock(),  # Low quality count
            Mock()   # Recent additions
        ]

        # Setup mock return values
        mock_results[0].scalar.return_value = 100  # Total content
        mock_results[1].fetchall.return_value = [("troubleshooting", 60), ("maintenance", 40)]
        mock_results[2].fetchall.return_value = [("Whirlpool", 50), ("LG", 30), ("Samsung", 20)]
        mock_results[3].first.return_value = (0.85, 0.3, 0.98)  # avg, min, max quality
        mock_results[4].scalar.return_value = 5  # Low quality count
        mock_results[5].scalar.return_value = 10  # Recent additions

        with patch('src.processing.quality_validator.get_db_session') as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_database_session
            mock_database_session.execute.side_effect = mock_results

            report = await validator.generate_quality_report()

            assert report["total_content_items"] == 100
            assert report["content_type_distribution"]["troubleshooting"] == 60
            assert report["manufacturer_distribution"]["Whirlpool"] == 50
            assert report["quality_metrics"]["average_quality_score"] == 0.85
            assert report["quality_metrics"]["low_quality_items"] == 5
            assert report["recent_activity"]["items_added_last_24h"] == 10
            assert "recommendations" in report
            assert report["health_status"] in ["healthy", "needs_attention"]

    @pytest.mark.asyncio
    async def test_generate_quality_report_with_recommendations(self, validator, mock_database_session):
        """Test quality report generation with recommendations"""
        # Mock data that should trigger recommendations
        mock_results = [
            Mock(),  # Total count
            Mock(),  # Content type distribution
            Mock(),  # Manufacturer distribution
            Mock(),  # Quality statistics
            Mock(),  # Low quality count
            Mock()   # Recent additions
        ]

        # Setup data that should trigger recommendations
        mock_results[0].scalar.return_value = 100
        mock_results[1].fetchall.return_value = [("troubleshooting", 50)]
        mock_results[2].fetchall.return_value = [("Unknown", 20), ("Whirlpool", 80)]  # High unknown count
        mock_results[3].first.return_value = (0.6, 0.2, 0.9)
        mock_results[4].scalar.return_value = 25  # High low-quality count
        mock_results[5].scalar.return_value = 5

        with patch('src.processing.quality_validator.get_db_session') as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_database_session
            mock_database_session.execute.side_effect = mock_results

            report = await validator.generate_quality_report()

            assert len(report["recommendations"]) > 0
            assert report["health_status"] == "needs_attention"
            # Should recommend reviewing low quality items
            assert any("quality scores below" in rec for rec in report["recommendations"])

    @pytest.mark.asyncio
    async def test_generate_quality_report_error(self, validator):
        """Test quality report generation with database error"""
        with patch('src.processing.quality_validator.get_db_session') as mock_get_session:
            mock_get_session.side_effect = Exception("Database connection failed")

            report = await validator.generate_quality_report()

            assert "error" in report
            assert report["health_status"] == "error"
            assert report["generated_at"] is not None

    @pytest.mark.asyncio
    async def test_validate_content_against_queries_success(self, validator):
        """Test content validation against test queries"""
        test_queries = [
            "washing machine won't start",
            "clean lint filter",
            "troubleshooting water leak"
        ]

        # Mock search results
        mock_search_results = [
            {"total_results": 3, "search_time_ms": 150.0, "results": [{"manufacturer": "whirlpool"}]},
            {"total_results": 2, "search_time_ms": 120.0, "results": [{"manufacturer": "lg"}]},
            {"total_results": 1, "search_time_ms": 180.0, "results": [{"manufacturer": "samsung"}]}
        ]

        with patch('src.processing.quality_validator.ContentManager') as mock_manager:
            mock_manager.return_value.search_content.side_effect = mock_search_results

            result = await validator.validate_content_against_queries(
                test_queries,
                expected_manufacturers=["whirlpool", "lg"]
            )

            assert result["test_queries"] == 3
            assert result["successful_searches"] == 3
            assert result["failed_searches"] == 0
            assert result["average_result_count"] == 2.0  # (3+2+1)/3
            assert len(result["query_results"]) == 3

            # Check manufacturer validation
            first_result = result["query_results"][0]
            assert first_result["expected_manufacturer_found"] is True

    @pytest.mark.asyncio
    async def test_validate_content_against_queries_no_results(self, validator):
        """Test content validation with queries returning no results"""
        test_queries = ["nonexistent query"]

        with patch('src.processing.quality_validator.ContentManager') as mock_manager:
            mock_manager.return_value.search_content.return_value = {
                "total_results": 0,
                "search_time_ms": 50.0,
                "results": []
            }

            result = await validator.validate_content_against_queries(test_queries)

            assert result["successful_searches"] == 0
            assert result["failed_searches"] == 1
            assert result["average_result_count"] == 0.0

    @pytest.mark.asyncio
    async def test_validate_content_against_queries_error(self, validator):
        """Test content validation with search errors"""
        test_queries = ["error query"]

        with patch('src.processing.quality_validator.ContentManager') as mock_manager:
            mock_manager.return_value.search_content.side_effect = Exception("Search failed")

            result = await validator.validate_content_against_queries(test_queries)

            assert result["failed_searches"] == 1
            assert result["query_results"][0]["status"] == "error"
            assert "error" in result["query_results"][0]


if __name__ == "__main__":
    pytest.main([__file__])