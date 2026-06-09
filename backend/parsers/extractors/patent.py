"""Patent extractor: parse patent entries."""
import re
from typing import List, Dict, Any, Tuple

from backend.parsers.extractors.base import BaseExtractor


class PatentExtractor(BaseExtractor):
    REQUIRED_FIELDS = {"patent_name": 0.35, "application_number": 0.3, "applicants": 0.2}
    OPTIONAL_FIELDS = {"status": 0.1, "authorization_number": 0.05}

    NUMBER_PATTERN = r'(?:CN\s*)?\d{9,}(?:\.[A-Z0-9]+)*[A-Z]?|PCT-CN[-\d]+|[A-Z]{2,6}\d{6,}(?:\.[A-Z0-9]+)*'

    def extract(self, lines: List[str]) -> List[Dict[str, Any]]:
        results = []
        for line in self._split_entries(lines):
            parsed = self._parse_patent(line)
            if parsed and parsed.get("patent_name"):
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
            if line.endswith(("：", ":")) and "专利" in line:
                continue
            entries.append(line)
        return entries

    def _parse_patent(self, text: str) -> Dict[str, Any]:
        result = {
            "patent_name": "",
            "application_number": "",
            "authorization_number": "",
            "status": "",
            "applicants": [],
        }

        text = re.sub(r'^[\d]+[.、）)]\s*', '', text).strip().strip("；;")

        application_match = re.search(
            r'(?:申请号|国际申请号|意大利申请号)[：:\s]*'
            rf'({self.NUMBER_PATTERN})',
            text,
            re.I,
        )
        if application_match:
            result["application_number"] = self._normalize_number(application_match.group(1))

        authorization_match = re.search(
            r'(?:授权号|专利授权号|公开号)[：:\s]*'
            rf'({self.NUMBER_PATTERN})',
            text,
            re.I,
        )
        if authorization_match:
            result["authorization_number"] = self._normalize_number(authorization_match.group(1))

        if not result["application_number"] and not result["authorization_number"]:
            loose_numbers = [
                self._normalize_number(match.group(1))
                for match in re.finditer(rf'({self.NUMBER_PATTERN})', text, re.I)
            ]
            if len(loose_numbers) == 1 and not result["application_number"] and not result["authorization_number"]:
                number = loose_numbers[0]
                if "CN" in number.upper() or not number.isdigit():
                    result["authorization_number"] = number
                else:
                    result["application_number"] = number
            else:
                for number in loose_numbers:
                    if not result["application_number"] and ('.' in number or number.isdigit()):
                        result["application_number"] = number
                    elif not result["authorization_number"]:
                        result["authorization_number"] = number

        status_match = re.search(r'状态[：:\s]*(已授权|授权|公开|实审|申请中)|(?<!申请)(已授权|授权|公开|实审|申请中)(?!号)', text)
        if status_match:
            result["status"] = status_match.group(1) or status_match.group(2)
        elif result["authorization_number"]:
            result["status"] = "授权"

        clean = re.sub(
            r'(?:申请号|专利授权号|授权号|公开号|国际申请号|意大利申请号)[：:\s]*'
            rf'{self.NUMBER_PATTERN}',
            '',
            text,
            flags=re.I,
        )
        for value in [result["application_number"], result["authorization_number"]]:
            if value:
                clean = clean.replace(value, "")
        if result["status"]:
            clean = re.sub(r'[，,\s]*状态[：:\s]*' + re.escape(result["status"]) + r'\s*', '', clean)
            clean = re.sub(r'[，,\s]*' + re.escape(result["status"]) + r'\s*', '', clean)
        clean = re.sub(r'[，,\s]*(?:状态[：:\s]*)?(已授权|授权|公开|实审|申请中)(?!号)\s*', '', clean)
        clean = clean.strip("，,。.;； ")

        applicants, title = self._split_people_and_title(clean)
        result["applicants"] = [{"name": name, "order": idx} for idx, name in enumerate(applicants)]
        result["patent_name"] = title

        return result

    def _normalize_number(self, value: str) -> str:
        number = re.sub(r'\s+', '', value or '').strip('，,。.;； ')
        while True:
            repeated_suffix = re.match(r'^(.+\.([A-Z0-9]+))\.\2$', number, re.I)
            if not repeated_suffix:
                break
            number = repeated_suffix.group(1)
        return number

    def _split_people_and_title(self, text: str) -> Tuple[List[str], str]:
        period_split = re.match(r'^(.{2,80}?)[.．]\s*(.+)$', text)
        if period_split:
            people = [p.strip() for p in re.split(r'[，,、]\s*', period_split.group(1)) if p.strip()]
            if people and all(self._is_person_name(name) for name in people):
                return people, period_split.group(2).strip("，,。.;； ")

        parts = [part.strip() for part in re.split(r'[，,]\s*', text) if part.strip()]
        applicants: List[str] = []
        title_parts: List[str] = []
        reached_title = False

        for part in parts:
            if not reached_title and self._is_person_name(part):
                applicants.append(part)
                continue
            reached_title = True
            title_parts.append(part)

        return applicants, "，".join(title_parts).strip("，,。.;； ")

    def _is_person_name(self, text: str) -> bool:
        text = text.strip()
        if re.match(r'^[\u4e00-\u9fff]{2,4}$', text):
            return True
        if re.match(r'^[A-Z][a-z]+\s+[A-Z]', text, re.I):
            return True
        return False
