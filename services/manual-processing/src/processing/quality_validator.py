"""
Quality validation and assurance for processed manual content
"""

import asyncio
import logging
import re
from typing import Dict, Any, List, Tuple
from collections import Counter
from difflib import SequenceMatcher

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..config.settings import get_settings
from shared.python.database.connection import get_db_session
from shared.python.models.manual_content import ManualContent

logger = logging.getLogger(__name__)


class QualityValidator:
    """
    Quality validation and assurance for manual content processing
    """

    def __init__(self):
        self.settings = get_settings()

    async def calculate_readability_score(self, text: str) -> float:
        """
        Calculate readability/quality score for text content

        Args:
            text: Text content to evaluate

        Returns:
            Quality score between 0.0 and 1.0
        """
        if not text or len(text.strip()) < self.settings.MIN_TEXT_LENGTH:
            return 0.0

        score = 1.0

        # Text length factor
        text_length = len(text.strip())
        if text_length < 100:
            score -= 0.2
        elif text_length > 2000:
            score -= 0.1

        # Word count and average word length
        words = text.split()
        if not words:
            return 0.0

        avg_word_length = sum(len(word) for word in words) / len(words)
        if avg_word_length < 3:  # Very short words might indicate OCR issues
            score -= 0.2
        elif avg_word_length > 8:  # Very long words might indicate concatenation issues
            score -= 0.1

        # Check for excessive special characters
        special_chars = len(re.findall(r'[^\w\s.,!?;:\'"()-]', text))
        if special_chars / len(text) > 0.05:  # More than 5% special characters
            score -= 0.3

        # Check for proper sentence structure
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if sentences:
            avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
            if 3 <= avg_sentence_length <= 50:  # Reasonable sentence length
                score += 0.1
            else:
                score -= 0.2

        # Check for alphabetic character ratio
        alpha_chars = len(re.findall(r'[a-zA-Z]', text))
        alpha_ratio = alpha_chars / len(text) if text else 0
        if alpha_ratio < 0.5:  # Less than 50% alphabetic characters
            score -= 0.2

        # Check for repeated patterns (might indicate extraction errors)
        lines = text.split('\n')
        if len(set(lines)) < len(lines) * 0.8:  # More than 20% duplicate lines
            score -= 0.2

        # Check for meaningful content keywords
        meaningful_keywords = [
            'troubleshooting', 'problem', 'issue', 'error', 'solution',
            'maintenance', 'cleaning', 'service', 'repair',
            'safety', 'warning', 'caution', 'danger',
            'installation', 'setup', 'configuration',
            'washer', 'washing', 'machine', 'appliance'
        ]

        text_lower = text.lower()
        keyword_count = sum(1 for keyword in meaningful_keywords if keyword in text_lower)
        if keyword_count > 0:
            score += min(0.2, keyword_count * 0.05)

        return max(0.0, min(1.0, score))

    async def check_for_duplicates(self, correlation_id: str) -> List[Tuple[str, str, float]]:
        """
        Check for duplicate content in the database

        Args:
            correlation_id: Request correlation ID

        Returns:
            List of (content_id_1, content_id_2, similarity_score) tuples for duplicates
        """
        try:
            duplicates = []

            async with get_db_session() as session:
                # Get recent content for duplicate checking
                result = await session.execute(
                    select(ManualContent.id, ManualContent.content)
                    .order_by(ManualContent.created_at.desc())
                    .limit(100)  # Check last 100 items for performance
                )
                content_items = result.fetchall()

                # Compare content pairwise
                for i, (id1, content1) in enumerate(content_items):
                    for j, (id2, content2) in enumerate(content_items[i + 1:], i + 1):
                        similarity = self._calculate_text_similarity(content1, content2)

                        if similarity >= self.settings.DUPLICATE_SIMILARITY_THRESHOLD:
                            duplicates.append((str(id1), str(id2), similarity))
                            logger.warning(
                                f"Duplicate content detected: {id1} <-> {id2} (similarity: {similarity:.3f})",
                                extra={'correlation_id': correlation_id}
                            )

                return duplicates

        except Exception as e:
            logger.error(
                f"Duplicate check failed: {str(e)}",
                extra={'correlation_id': correlation_id}
            )
            return []

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two text strings

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score between 0.0 and 1.0
        """
        if not text1 or not text2:
            return 0.0

        # Use SequenceMatcher for basic text similarity
        matcher = SequenceMatcher(None, text1.lower().strip(), text2.lower().strip())
        return matcher.ratio()

    async def validate_manufacturer_model(self, manufacturer: str, model_series: str) -> bool:
        """
        Validate manufacturer and model series against known patterns

        Args:
            manufacturer: Manufacturer name
            model_series: Model series

        Returns:
            Validation result
        """
        # Known manufacturers
        known_manufacturers = [
            'whirlpool', 'lg', 'samsung', 'ge', 'kenmore',
            'maytag', 'bosch', 'electrolux', 'frigidaire'
        ]

        manufacturer_valid = (
            manufacturer.lower() in known_manufacturers or
            manufacturer.lower() != 'unknown'
        )

        # Basic model validation (should contain letters and numbers)
        model_pattern = re.compile(r'^[A-Za-z0-9\-_]+$')
        model_valid = (
            model_pattern.match(model_series) and
            model_series.lower() != 'unknown' and
            len(model_series) >= 3
        )

        return manufacturer_valid and model_valid

    async def generate_quality_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive quality report for all content

        Returns:
            Quality report with metrics and recommendations
        """
        try:
            async with get_db_session() as session:
                # Basic statistics
                total_count_result = await session.execute(
                    select(func.count(ManualContent.id))
                )
                total_content = total_count_result.scalar()

                # Content type distribution
                content_type_result = await session.execute(
                    select(ManualContent.content_type, func.count(ManualContent.id))
                    .group_by(ManualContent.content_type)
                )
                content_types = dict(content_type_result.fetchall())

                # Manufacturer distribution
                manufacturer_result = await session.execute(
                    select(ManualContent.manufacturer, func.count(ManualContent.id))
                    .group_by(ManualContent.manufacturer)
                )
                manufacturers = dict(manufacturer_result.fetchall())

                # Quality score statistics
                quality_stats_result = await session.execute(
                    select(
                        func.avg(ManualContent.confidence_score),
                        func.min(ManualContent.confidence_score),
                        func.max(ManualContent.confidence_score)
                    )
                )
                avg_quality, min_quality, max_quality = quality_stats_result.first()

                # Low quality content count
                low_quality_result = await session.execute(
                    select(func.count(ManualContent.id))
                    .where(ManualContent.confidence_score < self.settings.MIN_READABILITY_SCORE)
                )
                low_quality_count = low_quality_result.scalar()

                # Recent activity (last 24 hours)
                from datetime import datetime, timedelta
                recent_cutoff = datetime.utcnow() - timedelta(days=1)
                recent_result = await session.execute(
                    select(func.count(ManualContent.id))
                    .where(ManualContent.created_at >= recent_cutoff)
                )
                recent_additions = recent_result.scalar()

                # Generate recommendations
                recommendations = []

                if low_quality_count > 0:
                    recommendations.append(
                        f"Consider reviewing {low_quality_count} items with quality scores below {self.settings.MIN_READABILITY_SCORE}"
                    )

                if 'Unknown' in manufacturers and manufacturers['Unknown'] > total_content * 0.1:
                    recommendations.append(
                        f"High number of unknown manufacturers ({manufacturers['Unknown']}) - consider improving metadata extraction"
                    )

                unknown_models = sum(1 for mfg, count in manufacturers.items() if 'unknown' in mfg.lower())
                if unknown_models > 0:
                    recommendations.append(
                        "Consider improving model series extraction from content"
                    )

                return {
                    "generated_at": datetime.utcnow().isoformat(),
                    "total_content_items": total_content,
                    "content_type_distribution": content_types,
                    "manufacturer_distribution": manufacturers,
                    "quality_metrics": {
                        "average_quality_score": round(float(avg_quality or 0), 3),
                        "min_quality_score": round(float(min_quality or 0), 3),
                        "max_quality_score": round(float(max_quality or 0), 3),
                        "low_quality_items": low_quality_count,
                        "low_quality_threshold": self.settings.MIN_READABILITY_SCORE
                    },
                    "recent_activity": {
                        "items_added_last_24h": recent_additions
                    },
                    "recommendations": recommendations,
                    "health_status": "healthy" if low_quality_count < total_content * 0.1 else "needs_attention"
                }

        except Exception as e:
            logger.error(f"Failed to generate quality report: {str(e)}")
            return {
                "generated_at": datetime.utcnow().isoformat(),
                "error": str(e),
                "health_status": "error"
            }

    async def validate_content_against_queries(
        self,
        test_queries: List[str],
        expected_manufacturers: List[str] = None
    ) -> Dict[str, Any]:
        """
        Validate search accuracy against known test queries

        Args:
            test_queries: List of test queries to validate
            expected_manufacturers: Expected manufacturers for validation

        Returns:
            Validation results
        """
        results = {
            "test_queries": len(test_queries),
            "successful_searches": 0,
            "failed_searches": 0,
            "average_result_count": 0.0,
            "query_results": []
        }

        try:
            from .content_manager import ContentManager
            content_manager = ContentManager()

            total_results = 0

            for query in test_queries:
                try:
                    search_result = await content_manager.search_content(
                        query=query,
                        max_results=5
                    )

                    result_count = search_result.get('total_results', 0)
                    total_results += result_count

                    query_result = {
                        "query": query,
                        "result_count": result_count,
                        "search_time_ms": search_result.get('search_time_ms', 0),
                        "status": "success" if result_count > 0 else "no_results"
                    }

                    if result_count > 0:
                        results["successful_searches"] += 1
                        # Check if expected manufacturer appears in results
                        if expected_manufacturers:
                            found_manufacturers = [
                                r.get('manufacturer', '').lower()
                                for r in search_result.get('results', [])
                            ]
                            expected_found = any(
                                exp.lower() in found_manufacturers
                                for exp in expected_manufacturers
                            )
                            query_result["expected_manufacturer_found"] = expected_found
                    else:
                        results["failed_searches"] += 1

                    results["query_results"].append(query_result)

                except Exception as e:
                    results["failed_searches"] += 1
                    results["query_results"].append({
                        "query": query,
                        "status": "error",
                        "error": str(e)
                    })

            results["average_result_count"] = (
                total_results / len(test_queries) if test_queries else 0.0
            )

            return results

        except Exception as e:
            logger.error(f"Query validation failed: {str(e)}")
            results["error"] = str(e)
            return results