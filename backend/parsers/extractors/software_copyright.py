"""Software copyright extractor."""
import re
from typing import List, Dict, Any
from backend.parsers.extractors.base import BaseExtractor


class SoftwareCopyrightExtractor(BaseExtractor):
    REQUIRED_FIELDS = {"name": 0.3, "applicant": 0.25}
    OPTIONAL_FIELDS = {"registration_number": 0.25, "registration_date": 0.2}

    def extract(self, lines: List[str]) -> List[Dict[str, Any]]:
        merged = self._merge_multiline(lines)
        results = []
        for line in merged:
            parsed = self._parse_sc(line)
            if parsed and parsed.get("name"):
                parsed["confidence"] = self.calculate_confidence(parsed)
                parsed["raw_text"] = line
                results.append(parsed)
        return results

    def _parse_sc(self, text: str) -> Dict[str, Any]:
        result = {"applicant": "", "name": "", "registration_date": "", "registration_number": ""}

        text = re.sub(r'^[\d]+[.、）)]\s*', '', text).strip()

        # Extract registration number
        reg_match = re.search(r'(?:软件著作权?登记号|著作权登记号|登记号)[：:\s]*([A-Z0-9]+)', text, re.I)
        if reg_match:
            result["registration_number"] = reg_match.group(1)

        # Extract date: YYYY年M月D日
        date_match = re.search(r'(\d{4}年\d{1,2}月\d{1,2}日)', text)
        if date_match:
            result["registration_date"] = date_match.group(1)

        clean = text
        if result["registration_date"]:
            clean = clean[:clean.find(result["registration_date"])].strip().rstrip(',，。.')
        elif result["registration_number"]:
            idx = clean.find("登记号")
            if idx < 0:
                idx = clean.find(result["registration_number"])
            if idx > 0:
                clean = clean[:idx].strip().rstrip(',，。.')

        applicants, name = self._split_applicants_and_name(clean)
        result["applicant"] = "，".join(applicants)
        result["name"] = name

        return result

    def _split_applicants_and_name(self, text: str) -> tuple[list[str], str]:
        parts = [part.strip() for part in re.split(r'[，,]\s*', text) if part.strip()]
        applicants = []
        name_parts = []
        reached_name = False

        for part in parts:
            if not reached_name and self._looks_like_applicant(part):
                applicants.append(part)
                continue
            reached_name = True
            name_parts.append(part)

        if applicants and name_parts:
            return applicants, "，".join(name_parts).strip("，,。.;； ")

        fallback = re.match(r'^(.{2,80}?)[。．]\s*(.+)$', text)
        if fallback:
            applicants = [item.strip() for item in re.split(r'[，,、]\s*', fallback.group(1)) if item.strip()]
            return applicants, fallback.group(2).strip("，,。.;； ")

        return applicants, "，".join(name_parts or parts).strip("，,。.;； ")

    def _looks_like_applicant(self, text: str) -> bool:
        value = text.strip()
        if re.fullmatch(r'[\u4e00-\u9fff]{2,4}(?:等)?', value):
            return True
        if any(keyword in value for keyword in ("大学", "学院", "公司", "研究院", "实验室")):
            return True
        return False
