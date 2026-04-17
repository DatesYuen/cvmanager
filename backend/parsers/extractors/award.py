"""Award extractor."""
import re
from typing import List, Dict, Any
from backend.parsers.extractors.base import BaseExtractor


class AwardExtractor(BaseExtractor):
    REQUIRED_FIELDS = {"award_name": 0.4}
    OPTIONAL_FIELDS = {"project_name": 0.2, "participants": 0.2, "awarding_body": 0.2}

    def extract(self, lines: List[str]) -> List[Dict[str, Any]]:
        merged = self._merge_multiline(lines)
        results = []
        for line in merged:
            parsed = self._parse_award(line)
            if parsed and parsed.get("award_name"):
                parsed["confidence"] = self.calculate_confidence(parsed)
                parsed["raw_text"] = line
                results.append(parsed)
        return results

    def _parse_award(self, text: str) -> Dict[str, Any]:
        result = {"award_name": "", "project_name": "", "participants": "", "awarding_body": ""}

        text = re.sub(r'^[\d]+[.、）)]\s*', '', text).strip()

        # Try to find award name patterns
        # Common: AwardName，ProjectName，Participants
        # or: AwardName：ProjectName（Participants）
        parts = re.split(r'[，,]\s*', text)

        if len(parts) >= 1:
            result["award_name"] = parts[0].strip()

        if len(parts) >= 2:
            # Check if second part is project name or participants
            second = parts[1].strip()
            if self._looks_like_participants(second):
                result["participants"] = second
            else:
                result["project_name"] = second

        if len(parts) >= 3:
            remaining = "，".join(parts[2:])
            if not result["participants"]:
                result["participants"] = remaining

        return result

    def _looks_like_participants(self, text: str) -> bool:
        """Check if text looks like a list of person names."""
        names = re.split(r'[、/\s]+', text)
        person_count = sum(1 for n in names if re.match(r'^[\u4e00-\u9fff]{2,4}$', n.strip()))
        return person_count >= 2
