"""Conference extractor."""
import re
from typing import List, Dict, Any

from backend.parsers.extractors.base import BaseExtractor


class ConferenceExtractor(BaseExtractor):
    REQUIRED_FIELDS = {"name": 0.4}
    OPTIONAL_FIELDS = {"date": 0.2, "role": 0.2, "website": 0.2}

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
        current = ""

        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                continue
            if line.endswith(("：", ":")) and "会议" in line:
                continue
            if re.fullmatch(r'https?://\S+', line):
                if current:
                    current = f"{current} {line}"
                continue
            if current:
                entries.append(current)
            current = line

        if current:
            entries.append(current)

        return entries

    def _parse(self, text: str) -> Dict[str, Any]:
        result = {"name": "", "date": "", "role": "", "website": ""}
        text = re.sub(r'^[\d]+[.、）)]\s*', '', text).strip()

        url_match = re.search(r'(https?://[^\s,，]+)', text)
        if url_match:
            result["website"] = url_match.group(1)
            text = text[:url_match.start()] + text[url_match.end():]

        date_match = re.search(r'(\d{4}(?:[.\-/年]\d{1,2}(?:月)?(?:[.\-/]\d{1,2})?)?)', text)
        if date_match:
            result["date"] = date_match.group(1)

        role_match = re.search(
            r'(大会主席|主席|共同主席|组织者|程序委员|副主席|秘书长|'
            r'General Chair|Conference Chair|Program Committee Chair|Workshop Chair|'
            r'Program Chair|Guest Chair)',
            text,
            re.I,
        )
        if role_match:
            result["role"] = role_match.group(1)

        clean = text
        for val in [result["date"], result["role"], result["website"]]:
            if val:
                clean = clean.replace(val, "")
        clean = re.sub(r'[()（）]', '', clean)
        result["name"] = clean.strip().strip(',，。.、 ')

        return result
