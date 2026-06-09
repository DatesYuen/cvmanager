"""Teaching platform extractor."""
import re
from typing import List, Dict, Any

from backend.parsers.extractors.base import BaseExtractor


class TeachingPlatformExtractor(BaseExtractor):
    REQUIRED_FIELDS = {"name": 0.35}
    OPTIONAL_FIELDS = {"issuing_body": 0.25, "approval_date": 0.2, "position": 0.2}

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
        return [
            line.strip()
            for line in lines
            if line.strip() and not (line.strip().endswith(("：", ":")) and "平台" in line)
        ]

    def _parse(self, text: str) -> Dict[str, Any]:
        result = {"name": "", "issuing_body": "", "approval_date": "", "position": ""}
        text = re.sub(r'^[\d]+[.、）)]\s*', '', text).strip()
        text = re.sub(r'^(?:学科及教学情况|学科及教学平台建设情况)[：:]\s*', '', text).strip()

        date_match = re.search(r'(\d{4}\s*年\s*\d{1,2}\s*月|\d{4}(?:[.\-/年]\d{1,2}(?:月)?)?)', text)
        if date_match:
            result["approval_date"] = re.sub(r'\s+', '', date_match.group(1))

        position_match = re.search(
            r'(学科建设负责人|专业负责人|负责人|主任|副主任|成员|骨干|带头人|执行院长)',
            text,
        )
        if position_match:
            result["position"] = position_match.group(1)

        parts = [part.strip() for part in re.split(r'[，,]\s*', text) if part.strip()]
        if parts:
            result["name"] = parts[0]
        for part in parts[1:]:
            if any(keyword in part for keyword in ["部", "厅", "局", "委", "院", "教育", "学位委员会"]):
                result["issuing_body"] = part
                break

        return result
