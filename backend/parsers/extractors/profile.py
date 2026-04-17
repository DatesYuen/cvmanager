"""Profile extractor: personal info, education, work experience."""
import re
from typing import List, Dict, Any
from backend.parsers.extractors.base import BaseExtractor


class ProfileExtractor(BaseExtractor):

    def extract(self, lines: List[str]) -> Dict[str, Any]:
        """Extract profile info. Returns a single dict (not list) since there's only one profile."""
        result = {
            "introduction": "",
            "phone": "",
            "email": "",
            "address": "",
            "educations": [],
            "work_experiences": [],
        }

        intro_lines = []
        current_block = "introduction"
        for line in lines:
            cleaned_line = self._clean_text(line)

            if self._is_education_heading(cleaned_line):
                current_block = "education"
                continue

            if self._is_work_heading(cleaned_line):
                current_block = "work"
                continue

            if line.startswith("EDUCATION_TABLE_ROW:"):
                row = line.replace("EDUCATION_TABLE_ROW:", "").split("\t")
                edu = self._parse_education_row(row)
                if edu:
                    result["educations"].append(edu)
                continue

            if line.startswith("WORK_TABLE_ROW:"):
                row = line.replace("WORK_TABLE_ROW:", "").split("\t")
                work = self._parse_work_row(row)
                if work:
                    result["work_experiences"].append(work)
                continue

            # Try to extract phone
            phone_match = re.search(r'(?:电话|手机|Tel|Phone)[：:\s]*([1]\d{10}|\d{3,4}[-\s]?\d{7,8})', line, re.I)
            if phone_match:
                result["phone"] = phone_match.group(1).strip()
                continue

            # Try to extract email
            email_match = re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', line)
            if email_match:
                result["email"] = email_match.group(0)
                if not result["phone"]:
                    # Check if there's also a phone on the same line
                    ph = re.search(r'[1]\d{10}|\d{3,4}[-\s]?\d{7,8}', line)
                    if ph:
                        result["phone"] = ph.group(0)
                continue

            # Try to extract address
            addr_match = re.search(r'(?:地址|Address)[：:\s]*(.*)', line, re.I)
            if addr_match:
                result["address"] = addr_match.group(1).strip()
                continue

            # Try inline education
            edu = self._parse_education_line(cleaned_line)
            if edu:
                result["educations"].append(edu)
                continue

            # Try inline work experience
            work = self._parse_work_line(cleaned_line)
            if work:
                result["work_experiences"].append(work)
                continue

            if current_block == "introduction" and cleaned_line:
                intro_lines.append(cleaned_line)

        result["introduction"] = "\n".join(intro_lines)
        return result

    def _parse_education_row(self, row: List[str]) -> Dict[str, str]:
        """Parse a table row into education fields."""
        if len(row) < 3:
            return None
        # Skip header rows
        if any(kw in "".join(row) for kw in ["起止时间", "学校", "学历"]):
            return None

        result = {"start_date": "", "end_date": "", "school": "", "major": "", "degree": ""}
        # Try to find date range
        for cell in row:
            date_match = re.search(r'(\d{4}[.\-/年]\d{0,2}[月]?)\s*[-—~至到]\s*(\d{4}[.\-/年]?\d{0,2}[月]?)', cell)
            if date_match:
                result["start_date"] = date_match.group(1)
                result["end_date"] = date_match.group(2)
                break

        remaining = [c for c in row if c and not re.search(r'\d{4}.*[-—~至]', c)]
        for cell in remaining:
            if any(kw in cell for kw in ["大学", "学院", "University", "College", "学校"]):
                result["school"] = cell
            elif any(kw in cell for kw in ["博士", "硕士", "学士", "本科", "PhD", "Master", "Bachelor"]):
                result["degree"] = cell
            elif not result["major"]:
                result["major"] = cell

        return self._clean_row_result(result) if result["school"] else None

    def _parse_work_row(self, row: List[str]) -> Dict[str, str]:
        if len(row) < 2:
            return None
        if any(kw in "".join(row) for kw in ["起止时间", "单位", "职务"]):
            return None

        result = {"start_date": "", "end_date": "", "organization": "", "position": ""}
        for cell in row:
            date_match = re.search(r'(\d{4}[.\-/年]\d{0,2}[月]?)\s*[-—~至到]\s*(\d{4}[.\-/年]?\d{0,2}[月]?|至今|今)', cell)
            if date_match:
                result["start_date"] = date_match.group(1)
                result["end_date"] = date_match.group(2)
                break

        remaining = [c for c in row if c and not re.search(r'\d{4}.*[-—~至]', c)]
        for cell in remaining:
            if any(kw in cell for kw in ["教授", "副教授", "讲师", "工程师", "主任", "院长", "主持"]):
                result["position"] = cell
            elif not result["organization"]:
                result["organization"] = cell

        return self._clean_row_result(result) if result["organization"] else None

    def _parse_education_line(self, line: str) -> Dict[str, str]:
        m = re.match(
            r'(\d{4}[.\-/年]\d{0,2}[月]?)\s*(?:[-—~至到]+\s*)(\d{4}[.\-/年]?\d{0,2}[月]?|至今|今)'
            r'[,，\s]+(.*?)[,，\s]+(.*?)[,，\s]+(.*)',
            line
        )
        if m:
            return self._clean_row_result({
                "start_date": m.group(1),
                "end_date": m.group(2),
                "school": m.group(3).strip(),
                "major": m.group(4).strip(),
                "degree": m.group(5).strip(),
            })
        return None

    def _parse_work_line(self, line: str) -> Dict[str, str]:
        m = re.match(
            r'(\d{4}[.\-/年]\d{0,2}[月]?)\s*(?:[-—~至到]+\s*)(\d{4}[.\-/年]?\d{0,2}[月]?|至今|今)'
            r'[,，\s]+(.*?)[,，\s]+(.*)',
            line
        )
        if m:
            org = m.group(3).strip()
            pos = m.group(4).strip()
            if any(kw in org for kw in ["大学", "学院", "公司", "研究"]):
                return self._clean_row_result({
                    "start_date": m.group(1),
                    "end_date": m.group(2),
                    "organization": org,
                    "position": pos,
                })
        return None

    def _clean_text(self, text: str) -> str:
        return text.strip().strip("；;")

    def _clean_row_result(self, result: Dict[str, str]) -> Dict[str, str]:
        return {key: self._clean_text(value) for key, value in result.items()}

    def _is_education_heading(self, line: str) -> bool:
        return line.rstrip("：:") in {"学习经历", "教育经历"}

    def _is_work_heading(self, line: str) -> bool:
        return line.rstrip("：:") in {"工作经历", "任职经历"}
