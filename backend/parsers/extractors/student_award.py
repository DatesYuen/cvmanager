"""Student award extractor."""
import re
from typing import List, Dict, Any
from backend.parsers.extractors.base import BaseExtractor


class StudentAwardExtractor(BaseExtractor):
    REQUIRED_FIELDS = {"award_name": 0.35}
    OPTIONAL_FIELDS = {"level": 0.2, "role": 0.2, "award_date": 0.25}

    def extract(self, lines: List[str]) -> List[Dict[str, Any]]:
        results = []
        for line in self._split_entries(lines):
            parsed = self._parse(line)
            if parsed and parsed.get("award_name"):
                parsed["confidence"] = self.calculate_confidence(parsed)
                parsed["raw_text"] = line
                results.append(parsed)
        return results

    def _split_entries(self, lines: List[str]) -> List[str]:
        entries = []
        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                continue
            if line.endswith(("：", ":")) and "获奖" in line:
                continue
            parts = re.split(r'[；;]\s*', line)
            for part in parts:
                part = part.strip().strip("。")
                if part:
                    entries.append(part)
        return entries

    def _parse(self, text: str) -> Dict[str, Any]:
        result = {"award_name": "", "level": "", "role": "", "award_date": ""}
        text = re.sub(r'^[\d]+[.、）)]\s*', '', text).strip()

        # Extract date
        date_match = re.search(r'(\d{4}(?:[.\-/年]\d{1,2}(?:月)?)?)', text)
        if date_match:
            result["award_date"] = date_match.group(1)

        # Extract level: 一等奖/二等奖/金奖/特等奖 etc.
        level_match = re.search(r'([一二三特]等奖|金奖|银奖|铜奖|优秀奖|最佳[^\s，,]*)', text)
        if level_match:
            result["level"] = level_match.group(1)

        # Extract role: 指导教师/指导导师
        role_match = re.search(r'(指导[教导]师|指导老师|指导)', text)
        if role_match:
            result["role"] = role_match.group(1)

        # The rest is award name
        clean = text
        for val in [result["award_date"], result["level"], result["role"]]:
            if val:
                clean = clean.replace(val, "")
        clean = re.sub(r'\d{4}年?', '', clean)
        clean = re.sub(r'(^|[，,\s])年(?=$|[，,\s])', ' ', clean)
        clean = clean.replace("位次1", "").replace("位次 1", "")
        clean = re.sub(r'[，,]{2,}', '，', clean)
        clean = re.sub(r'\s+', ' ', clean)
        clean = clean.replace("指导教师", "").replace("指导老师", "").replace("指导导师", "")
        clean = clean.strip()
        result["award_name"] = clean.strip().strip(',，。.、 ')

        return result
