"""Base extractor class with confidence calculation."""
from typing import List, Dict, Any


class BaseExtractor:
    """Base class for all content extractors."""

    # Override in subclasses: fields and their weights for confidence
    REQUIRED_FIELDS: Dict[str, float] = {}  # field_name -> weight
    OPTIONAL_FIELDS: Dict[str, float] = {}  # field_name -> weight

    def extract(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Extract structured items from text lines.

        Returns list of dicts, each containing extracted fields plus 'confidence' and 'raw_text'.
        """
        raise NotImplementedError

    def calculate_confidence(self, result: Dict[str, Any]) -> float:
        """Calculate confidence score based on how many fields were successfully extracted."""
        score = 0.0
        max_score = sum(self.REQUIRED_FIELDS.values()) + sum(self.OPTIONAL_FIELDS.values())

        for field, weight in self.REQUIRED_FIELDS.items():
            val = result.get(field, "")
            if val and str(val).strip():
                score += weight

        for field, weight in self.OPTIONAL_FIELDS.items():
            val = result.get(field, "")
            if val and str(val).strip():
                score += weight

        return min(score / max_score, 1.0) if max_score > 0 else 0.0

    def _merge_multiline(self, lines: List[str]) -> List[str]:
        """Merge lines that belong together (e.g., project info spanning multiple lines).

        Heuristic: if a line starts with a number, date, or keyword, it's a new entry.
        Otherwise, it's a continuation of the previous entry.
        """
        import re
        if not lines:
            return []

        merged = []
        current = lines[0]

        for line in lines[1:]:
            # Check if this line starts a new entry
            is_new = False
            stripped = line.strip()

            # Numbered entries: 1. or 1、 or (1) or [1]
            if re.match(r'^[\d]+[.、）)\]]\s*', stripped):
                is_new = True
            # Starts with a date-like pattern
            elif re.match(r'^\d{4}[.\-年/]', stripped):
                is_new = True
            # Starts with Chinese name pattern (for patents, papers)
            elif re.match(r'^[\u4e00-\u9fff]{2,5}\s*[,，.。．]', stripped):
                is_new = True
            # Starts with English name pattern
            elif re.match(r"^[A-Z][A-Za-z.'-]+(?:\s+[A-Z][A-Za-z.'-]*|[,;，；])", stripped):
                is_new = True
            # Empty line means new entry
            elif not stripped:
                is_new = True

            if is_new:
                if current.strip():
                    merged.append(current.strip())
                current = stripped
            else:
                current = current + " " + stripped

        if current.strip():
            merged.append(current.strip())

        return merged
