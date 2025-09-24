"""
Text cleaning and normalization utilities for PDF content
"""

import re
import logging
from typing import Dict, Any


logger = logging.getLogger(__name__)


class TextCleaner:
    """
    Text cleaning and normalization for PDF extracted content
    """

    def __init__(self):
        # Common OCR and PDF extraction artifacts to clean
        self.artifact_patterns = [
            # Remove page numbers and headers/footers patterns
            (r'^(?:page\s*\d+|\d+\s*$)', ''),
            # Remove common header/footer separators
            (r'^[-=_]{3,}$', ''),
            # Fix broken words (common in PDF extraction)
            (r'(\w)-\s+(\w)', r'\1\2'),
            # Remove standalone single characters (OCR artifacts) but preserve common words
            (r'\b[bcdfghjklmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZ]\b', ''),
            # Clean up bullet points and list markers
            (r'^[•·▪▫‣⁃]\s*', '• '),
            # Normalize quotation marks
            (r'[""''„‚«»]', '"'),
            # Remove excessive punctuation
            (r'[.]{3,}', '...'),
            (r'[-]{2,}', '--'),
            # Remove header/footer separators (more specific)
            (r'^===+$', ''),
            (r'^---+$', ''),
        ]

        # Patterns for section detection
        self.section_patterns = [
            r'^(troubleshooting|problem|issue|error)',
            r'^(maintenance|cleaning|service)',
            r'^(safety|warning|caution)',
            r'^(warranty|guarantee)',
            r'^(installation|setup)',
            r'^(specifications|features)',
        ]

    def clean_text(self, text: str) -> str:
        """
        Clean and normalize extracted PDF text

        Args:
            text: Raw text from PDF extraction

        Returns:
            Cleaned and normalized text
        """
        if not text:
            return ""

        cleaned = text

        # Basic cleaning
        cleaned = self._remove_artifacts(cleaned)
        cleaned = self._normalize_whitespace(cleaned)
        cleaned = self._fix_encoding_issues(cleaned)
        cleaned = self._standardize_formatting(cleaned)

        return cleaned.strip()

    def _remove_artifacts(self, text: str) -> str:
        """Remove common PDF extraction artifacts"""
        for pattern, replacement in self.artifact_patterns:
            text = re.sub(pattern, replacement, text, flags=re.MULTILINE | re.IGNORECASE)
        return text

    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace and line breaks"""
        # Replace tabs with spaces
        text = text.replace('\t', ' ')

        # First, normalize multiple consecutive newlines to exactly two newlines (paragraph break)
        text = re.sub(r'\n\s*\n\s*(\n\s*)*', '\n\n', text)

        # Replace single newlines with spaces (but preserve paragraph breaks)
        text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)

        # Replace multiple spaces with single space
        text = re.sub(r'[ ]+', ' ', text)

        return text

    def _fix_encoding_issues(self, text: str) -> str:
        """Fix common encoding issues in PDF text"""
        encoding_fixes = [
            # Common Unicode issues
            ('â€™', "'"),
            ('â€œ', '"'),
            ('â€', '"'),
            ('â€"', '--'),
            ('â€¢', '•'),
            # Fix degree symbols
            ('Â°', '°'),
            # Fix trademark symbols
            ('â„¢', '™'),
            ('Â®', '®'),
        ]

        for bad, good in encoding_fixes:
            text = text.replace(bad, good)

        return text

    def _standardize_formatting(self, text: str) -> str:
        """Standardize text formatting"""
        # Standardize section headers
        for pattern in self.section_patterns:
            text = re.sub(
                f'({pattern})',
                lambda m: m.group(1).title(),
                text,
                flags=re.IGNORECASE | re.MULTILINE
            )

        # Standardize measurements and units
        text = re.sub(r'(\d+)\s*(inches?|in\.?)', r'\1 inches', text, flags=re.IGNORECASE)
        text = re.sub(r'(\d+)\s*(feet?|ft\.?)', r'\1 feet', text, flags=re.IGNORECASE)
        text = re.sub(r'(\d+)\s*(pounds?|lbs?\.?)', r'\1 lbs', text, flags=re.IGNORECASE)

        # Standardize temperatures
        text = re.sub(r'(\d+)\s*degrees?\s*f(?:ahrenheit)?', r'\1°F', text, flags=re.IGNORECASE)
        text = re.sub(r'(\d+)\s*degrees?\s*c(?:elsius)?', r'\1°C', text, flags=re.IGNORECASE)

        return text

    def extract_section_title(self, text: str) -> str:
        """
        Extract a section title from the beginning of text

        Args:
            text: Text chunk

        Returns:
            Extracted section title or generated title
        """
        lines = text.split('\n')
        first_line = lines[0].strip()

        # If first line looks like a title (short, title case)
        if (len(first_line) < 100 and
            len(first_line.split()) <= 8 and
            any(word[0].isupper() for word in first_line.split())):
            return first_line

        # Look for section patterns
        for pattern in self.section_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                # Extract the line containing the match
                line_start = text.rfind('\n', 0, match.start()) + 1
                line_end = text.find('\n', match.end())
                if line_end == -1:
                    line_end = len(text)
                return text[line_start:line_end].strip()

        # Generate title from first few words
        words = text.split()[:10]
        title = ' '.join(words)

        # Truncate at sentence boundary if possible
        sentence_end = re.search(r'[.!?]', title)
        if sentence_end:
            title = title[:sentence_end.start() + 1]

        return title if len(title) <= 100 else title[:97] + "..."

    def validate_text_quality(self, text: str) -> float:
        """
        Validate text quality and return a score 0-1

        Args:
            text: Text to validate

        Returns:
            Quality score (0.0 = poor, 1.0 = excellent)
        """
        if not text or len(text.strip()) < 10:
            return 0.0

        score = 1.0

        # Penalize excessive special characters (OCR artifacts)
        special_char_ratio = len(re.findall(r'[^\w\s.,!?;:\'"()-]', text)) / len(text)
        if special_char_ratio > 0.1:
            score -= 0.3

        # Penalize excessive short words (OCR fragmentation)
        words = text.split()
        if words:
            short_word_ratio = len([w for w in words if len(w) <= 2]) / len(words)
            if short_word_ratio > 0.3:
                score -= 0.2

        # Penalize text that's mostly numbers or symbols
        alpha_ratio = len(re.findall(r'[a-zA-Z]', text)) / len(text)
        if alpha_ratio < 0.5:
            score -= 0.3

        # Reward proper sentence structure
        sentences = re.split(r'[.!?]+', text)
        if len(sentences) > 1:
            avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
            if 5 <= avg_sentence_length <= 30:  # Reasonable sentence length
                score += 0.1

        return max(0.0, min(1.0, score))