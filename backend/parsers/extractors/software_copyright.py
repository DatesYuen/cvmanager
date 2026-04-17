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
        reg_match = re.search(r'(?:软件著作权?登记号|登记号)[：:]\s*(\d+SR\d+)', text)
        if reg_match:
            result["registration_number"] = reg_match.group(1)

        # Extract date: YYYY年M月D日
        date_match = re.search(r'(\d{4}年\d{1,2}月\d{1,2}日)', text)
        if date_match:
            result["registration_date"] = date_match.group(1)

        # Split applicant and name
        # Pattern: Applicants.，SoftwareName(Version)，Date，RegNo
        # First, remove date and reg number parts
        clean = text
        if result["registration_date"]:
            clean = clean[:clean.find(result["registration_date"])].strip().rstrip(',，。.')
        elif result["registration_number"]:
            idx = clean.find("登记号")
            if idx < 0:
                idx = clean.find(result["registration_number"])
            if idx > 0:
                clean = clean[:idx].strip().rstrip(',，。.')

        # Split by period or 。 to separate applicants from software name
        # Applicants end with . or 。, then software name follows
        parts = re.split(r'[.。．]\s*[,，]?\s*', clean, maxsplit=1)
        if len(parts) >= 2:
            result["applicant"] = parts[0].strip()
            result["name"] = parts[1].strip().rstrip(',，。.')
        else:
            # Try comma split: last non-name part is the software name
            comma_parts = re.split(r'[，,]\s*', clean)
            applicants = []
            sw_name = ""
            for p in comma_parts:
                p = p.strip()
                if re.match(r'^[\u4e00-\u9fff]{2,4}$', p):
                    applicants.append(p)
                elif not sw_name and len(p) > 5:
                    sw_name = p
                    break
                else:
                    applicants.append(p)

            result["applicant"] = "，".join(applicants)
            result["name"] = sw_name

        # Clean version info from name
        result["name"] = re.sub(r'[（(]V[.\d]+[）)]', '', result["name"]).strip()

        return result
