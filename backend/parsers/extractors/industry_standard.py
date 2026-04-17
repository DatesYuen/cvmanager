"""Industry standard extractor."""
import re
from typing import List, Dict, Any

from backend.parsers.extractors.base import BaseExtractor


class IndustryStandardExtractor(BaseExtractor):
    REQUIRED_FIELDS = {"name": 0.4}
    OPTIONAL_FIELDS = {"publish_date": 0.3, "role": 0.3}

    def extract(self, lines: List[str]) -> List[Dict[str, Any]]:
        results = []
        for line in self._split_entries(lines):
            parsed = self._parse(line)
            if parsed and parsed.get("name"):
                parsed["confidence"] = self.calculate_confidence(parsed)
                parsed["raw_text"] = line
                results.append(parsed)
        return results

    def _split_entries(self, lines: List[str]) -> List[str]:
        entries: List[str] = []
        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                continue
            if line.endswith(("：", ":")) and "标准" in line:
                continue
            if any(token in line for token in ["联系电话", "E-mail", "Email", "联系地址"]):
                continue
            entries.append(line)
        return entries

    def _parse(self, text: str) -> Dict[str, Any]:
        result = {"name": "", "publish_date": "", "role": ""}
        text = re.sub(r'^[\d]+[.、）)]\s*', '', text).strip()
        text = re.sub(r'^行业标准[：:]\s*', '', text).strip()

        date_match = re.search(r'(\d{4}(?:[.\-/年]\d{1,2}(?:月)?(?:[.\-/]\d{1,2})?)?)', text)
        if date_match:
            result["publish_date"] = date_match.group(1)

        role_match = re.search(r'(主持|参与|第[一二三四五\d]+起草人?|主要起草人|起草人|参编)', text)
        if role_match:
            result["role"] = role_match.group(1)

        clean = text
        for value in [result["publish_date"], result["role"]]:
            if value:
                clean = clean.replace(value, "")
        result["name"] = clean.strip().strip(',，。.、 ')

        return result
