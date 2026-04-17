"""Special issue extractor."""
import re
from typing import List, Dict, Any
from backend.parsers.extractors.base import BaseExtractor


class SpecialIssueExtractor(BaseExtractor):
    REQUIRED_FIELDS = {"issue_name": 0.35}
    OPTIONAL_FIELDS = {"journal_name": 0.25, "date": 0.2, "role": 0.2}

    def extract(self, lines: List[str]) -> List[Dict[str, Any]]:
        merged = self._merge_multiline(lines)
        results = []
        for line in merged:
            parsed = self._parse(line)
            if parsed and parsed.get("issue_name"):
                parsed["confidence"] = self.calculate_confidence(parsed)
                parsed["raw_text"] = line
                results.append(parsed)
        return results

    def _parse(self, text: str) -> Dict[str, Any]:
        result = {"issue_name": "", "journal_name": "", "date": "", "role": ""}
        text = re.sub(r'^[\d]+[.、）)]\s*', '', text).strip()

        date_match = re.search(r'(\d{4}(?:[.\-/年]\d{1,2}(?:月)?)?)', text)
        if date_match:
            result["date"] = date_match.group(1)

        role_match = re.search(r'(Guest Editor|客座编辑|编委|主编|副主编|Associate Editor)', text, re.I)
        if role_match:
            result["role"] = role_match.group(1)

        parts = re.split(r'[，,]\s*', text)
        if len(parts) >= 2:
            result["issue_name"] = parts[0].strip()
            result["journal_name"] = parts[1].strip()
        elif len(parts) == 1:
            result["issue_name"] = parts[0].strip()

        return result
