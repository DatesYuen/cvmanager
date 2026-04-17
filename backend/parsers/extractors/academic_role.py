"""Academic role extractor."""
import re
from typing import List, Dict, Any
from backend.parsers.extractors.base import BaseExtractor


class AcademicRoleExtractor(BaseExtractor):
    REQUIRED_FIELDS = {"title": 0.5}
    OPTIONAL_FIELDS = {"start_date": 0.25, "end_date": 0.25}

    def extract(self, lines: List[str]) -> List[Dict[str, Any]]:
        merged = self._merge_multiline(lines)
        results = []
        for line in merged:
            parsed = self._parse(line)
            if parsed and parsed.get("title"):
                parsed["confidence"] = self.calculate_confidence(parsed)
                parsed["raw_text"] = line
                results.append(parsed)
        return results

    def _parse(self, text: str) -> Dict[str, Any]:
        result = {"title": "", "start_date": "", "end_date": ""}
        text = re.sub(r'^[\d]+[.、）)]\s*', '', text).strip()
        text = text.strip('；;')

        # Full Chinese date range:
        # 2024年6月1日至2026年5月31日，《AI & Materials》期刊副主编
        full_date = r'\d{4}年(?:\d{1,2}月)?(?:\d{1,2}日)?'
        date_range_match = re.search(
            rf'({full_date})\s*(?:至|到|[-—~～])\s*({full_date}|至今|今|现在)',
            text,
        )
        if date_range_match:
            result["start_date"] = date_range_match.group(1)
            result["end_date"] = date_range_match.group(2)
            text = text[:date_range_match.start()] + text[date_range_match.end():]
        else:
            # Single year / year-month prefix:
            # 2016年，山东省科协国家级科技思想库决策咨询专家。
            single_date_match = re.match(
                rf'^({full_date}|(?:\d{{4}}(?:[.\-/年]\d{{1,2}}(?:月)?)?))\s*[，,。.\s]+(.*)$',
                text,
            )
            if single_date_match:
                result["start_date"] = single_date_match.group(1)
                text = single_date_match.group(2)

        title = text.strip().strip(',，。.、 ')
        title = re.sub(r'^(?:当选|担任|受聘为|任)\s*', '', title)
        result["title"] = title
        return result
