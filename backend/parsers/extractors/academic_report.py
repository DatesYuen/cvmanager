"""Academic report extractor."""
import re
from typing import List, Dict, Any
from backend.parsers.extractors.base import BaseExtractor


class AcademicReportExtractor(BaseExtractor):
    REQUIRED_FIELDS = {"name": 0.4}
    OPTIONAL_FIELDS = {"report_type": 0.3, "date": 0.3}

    def extract(self, lines: List[str]) -> List[Dict[str, Any]]:
        merged = self._merge_multiline(lines)
        results = []
        for line in merged:
            parsed = self._parse(line)
            if parsed and parsed.get("name"):
                parsed["confidence"] = self.calculate_confidence(parsed)
                parsed["raw_text"] = line
                results.append(parsed)
        return results

    def _parse(self, text: str) -> Dict[str, Any]:
        result = {"name": "", "report_type": "", "date": ""}
        text = re.sub(r'^[\d]+[.、）)]\s*', '', text).strip()

        date_match = re.search(r'(\d{4}(?:[.\-/年]\d{1,2}(?:月)?)?)', text)
        if date_match:
            result["date"] = date_match.group(1)

        type_match = re.search(r'(特邀报告|邀请报告|主旨报告|Keynote|Invited Talk|大会报告|学术报告)', text, re.I)
        if type_match:
            result["report_type"] = type_match.group(1)

        clean = text
        for val in [result["date"], result["report_type"]]:
            if val:
                clean = clean.replace(val, "")
        result["name"] = clean.strip().strip(',，。.、 ')

        return result
