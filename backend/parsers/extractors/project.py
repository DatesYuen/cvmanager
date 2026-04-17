"""Project extractor: parse research project entries."""
import re
from typing import List, Dict, Any

from backend.parsers.extractors.base import BaseExtractor


class ProjectExtractor(BaseExtractor):
    REQUIRED_FIELDS = {"name": 0.3, "project_type": 0.2}
    OPTIONAL_FIELDS = {
        "project_number": 0.1,
        "start_date": 0.1,
        "end_date": 0.1,
        "role": 0.1,
        "amount": 0.1,
    }

    ROLE_PATTERNS = [
        r'项目主持人',
        r'课题主持人',
        r'项目负责人',
        r'课题负责人',
        r'关键技术负责人',
        r'学术骨干',
        r'课题第[一二三四五六七八九十\d]+位',
        r'项目主持',
        r'主持人',
        r'负责人',
        r'主持',
        r'参加',
        r'参与',
    ]

    TYPE_KEYWORDS = {
        "国家重点研发计划": "国家重点研发计划",
        "国家重点基础研究计划": "国家重点基础研究计划",
        "国家自然科学基金": "国家自然科学基金",
        "国家石化工业软件攻关课题": "国家石化工业软件攻关课题",
        "工业与信息化部攻关项目": "工业与信息化部攻关项目",
        "山东省重点研发计划": "山东省重点研发计划",
        "山东省自然科学基金": "山东省自然科学基金",
        "横向项目": "横向项目",
        "中国国家博士后基金项目": "中国国家博士后基金项目",
        "教育部": "教育部项目",
    }

    def extract(self, lines: List[str]) -> List[Dict[str, Any]]:
        results = []
        for entry in self._split_entries(lines):
            parsed = self._parse_project(entry)
            if parsed and parsed.get("name") and not self._is_heading_only(parsed):
                parsed["confidence"] = self.calculate_confidence(parsed)
                parsed["raw_text"] = entry
                results.append(parsed)
        return results

    def _split_entries(self, lines: List[str]) -> List[str]:
        entries: List[str] = []
        current = ""

        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                continue
            if line.endswith(("：", ":")) and len(line) <= 40:
                continue

            if self._looks_like_project_entry(line):
                if current:
                    entries.append(current.strip())
                current = line
            else:
                if current:
                    current = f"{current} {line}"
                else:
                    current = line

        if current:
            entries.append(current.strip())

        return entries

    def _looks_like_project_entry(self, line: str) -> bool:
        project_type_keywords = ["国家", "省", "市", "部", "工业", "基金", "计划", "攻关", "横向项目"]
        if re.match(r'^[\d]+[.、）)]\s*', line):
            return True
        if re.match(r'^\d{4}', line):
            return True
        if any(line.startswith(kw) for kw in project_type_keywords):
            return True
        if "：" in line or ":" in line:
            return True
        if re.search(r'\d{4}.*[-—~～至到].*(?:\d{4}|至今|今)', line):
            return True
        return False

    def _parse_project(self, text: str) -> Dict[str, Any]:
        result = {
            "project_type": "",
            "name": "",
            "project_number": "",
            "start_date": "",
            "end_date": "",
            "role": "",
            "amount": "",
        }

        text = re.sub(r'^[\d]+[.、）)]\s*', '', text).strip().strip("；;")

        amount_match = re.search(r'(?:[（(]\s*)?(\d+(?:\.\d+)?)\s*万(?:元)?(?:\s*[）)])?', text)
        if amount_match and amount_match.group(1):
            result["amount"] = amount_match.group(1) + "万"
            text = text[:amount_match.start()] + text[amount_match.end():]

        number_matches = list(
            re.finditer(
                r'[（(]\s*(?:No\.?\s*)?([A-Za-z0-9][A-Za-z0-9._\-()]*\d[A-Za-z0-9._\-()]*)\s*[）)]',
                text,
            )
        )
        if number_matches:
            def number_score(match):
                candidate = match.group(1)
                return (1 if re.search(r'[A-Za-z]', candidate) else 0, len(candidate))

            best_number = max(number_matches, key=number_score)
            result["project_number"] = best_number.group(1)
            text = text[:best_number.start()] + text[best_number.end():]

        date_match = re.search(
            r'(\d{4}(?:[.\-/年]\d{1,2}(?:[.\-/月]\d{1,2})?)?)\s*[-—~～至到]\s*'
            r'(\d{4}(?:[.\-/年]\d{1,2}(?:[.\-/月]\d{1,2})?)?|至今|今)',
            text,
        )
        if date_match:
            result["start_date"] = date_match.group(1)
            result["end_date"] = date_match.group(2)
            text = text[:date_match.start()] + " " + text[date_match.end():]

        for pattern in self.ROLE_PATTERNS:
            role_match = re.search(pattern, text)
            if role_match:
                result["role"] = role_match.group(0)
                text = text[:role_match.start()] + text[role_match.end():]
                break

        text = re.sub(
            r'(课题第[一二三四五六七八九十\d]+位|位次\d+|项目主持人|课题主持人|项目负责人|负责人|主持人|主持|参加|参与)',
            '',
            text,
        )

        text = re.sub(r'[（(]\s*(?:在研|已结题|结题)\s*[）)]', '', text)
        text = re.sub(r'\s+', ' ', text).strip(" ,，。.；;")

        type_name_match = re.match(r'^(.*?)[：:]\s*(.+)$', text)
        if type_name_match:
            result["project_type"] = re.sub(r'^\d{4}\s*', '', type_name_match.group(1).strip())
            result["name"] = type_name_match.group(2).strip(" ,，。.；;")
        else:
            result["name"] = text

        if not result["project_type"]:
            for keyword, mapped in self.TYPE_KEYWORDS.items():
                if keyword in text:
                    result["project_type"] = mapped
                    break

        if not result["project_number"]:
            loose_number = re.search(
                r'\b([A-Za-z]{1,10}[A-Za-z0-9._\-]*\d[A-Za-z0-9._\-]*)\b',
                result["name"],
            )
            if loose_number and len(loose_number.group(1)) >= 6:
                result["project_number"] = loose_number.group(1)

        if result["project_number"]:
            result["name"] = result["name"].replace(result["project_number"], "").strip(" ,，。.；;()（）")

        result["name"] = re.sub(r'[，,]{2,}', '，', result["name"]).strip(" ,，。.；;")

        return result

    def _is_heading_only(self, parsed: Dict[str, Any]) -> bool:
        return (
            not parsed.get("project_type")
            and not parsed.get("project_number")
            and not parsed.get("start_date")
            and not parsed.get("end_date")
            and not parsed.get("amount")
            and parsed.get("name", "").endswith("：")
        )
