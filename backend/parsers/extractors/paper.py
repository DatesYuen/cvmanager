"""Paper extractor: robust multi-format academic paper citation parser."""
import re
from typing import List, Dict, Any
from backend.parsers.extractors.base import BaseExtractor


class PaperExtractor(BaseExtractor):
    REQUIRED_FIELDS = {"title": 0.3, "journal": 0.25, "authors": 0.2}
    OPTIONAL_FIELDS = {"year": 0.1, "volume": 0.05, "issue": 0.05, "pages": 0.05,
                       "doi": 0.05}

    # Common Chinese/English separators between author list and title
    AUTHOR_TITLE_SEPS = ['. ', '。', '．']

    def extract(self, lines: List[str]) -> List[Dict[str, Any]]:
        merged = self._merge_multiline(lines)
        results = []
        for line in merged:
            parsed = self._parse_citation(line)
            if parsed and self._is_valid_citation(parsed, line):
                parsed["confidence"] = self.calculate_confidence(parsed)
                parsed["raw_text"] = line
                results.append(parsed)
        return results

    def _is_valid_citation(self, parsed: Dict[str, Any], raw_line: str) -> bool:
        stripped = raw_line.strip()
        if not stripped or stripped.endswith(("：", ":")) or len(stripped) < 15:
            return False
        if not parsed.get("title"):
            return False
        return bool(
            parsed.get("authors")
            or parsed.get("journal")
            or parsed.get("year")
            or parsed.get("doi")
        )

    def _parse_citation(self, text: str) -> Dict[str, Any]:
        result = {"title": "", "journal": "", "year": "", "doi": "",
                  "issue": "", "volume": "", "pages": "", "authors": []}

        # Remove trailing classification markers like （CCF A）（中科院二区）
        clean = re.sub(r'[（(]\s*(?:CCF\s*[A-C]|中科院[一二三四五]区|SCI|EI|SSCI|CSSCI|北大核心)[）)]\s*$', '', text).strip()

        # Extract DOI
        doi_match = re.search(r'(?:doi:\s*|https?://doi\.org/)?(10\.\d{4,9}/[^\s,，]+)', clean, re.I)
        if doi_match:
            result["doi"] = re.sub(r'[\s\]\)）.,，。；;]+$', '', doi_match.group(1).strip())
            clean = clean[:doi_match.start()].strip().rstrip(',，.')

        # Extract ISSN (remove it, not needed as field)
        clean = re.sub(r'ISSN\s*[\d-]+[,，\s]*', '', clean).strip()

        marker_parsed = self._parse_j_marker(clean, result["doi"])
        if marker_parsed:
            return marker_parsed

        comma_parsed = self._parse_comma_delimited(clean, result["doi"])
        if comma_parsed:
            return comma_parsed

        # Try to split authors from the rest
        authors_str, remaining = self._split_authors(clean)

        if authors_str:
            result["authors"] = self._parse_authors(authors_str)

        if not remaining:
            return result

        # Parse the remaining part: Title. Journal, Year, Vol(Issue): Pages
        # or: Title. Conference, Publisher:Year, Pages

        # Try pattern: Title. Journal/Conference. Year, Vol(Issue): Pages
        # or: Title. Journal, Year, Vol(Issue): Pages

        # Extract year
        year_match = re.search(r'[,，.\s]\s*((?:19|20)\d{2})\s*[,，.]', remaining)
        if year_match:
            result["year"] = year_match.group(1)

        # Extract volume(issue): pages pattern
        vol_match = re.search(r'(\d+)\s*\((\d+)\)\s*[：:]\s*([\d]+-[\d]+)', remaining)
        if vol_match:
            result["volume"] = vol_match.group(1)
            result["issue"] = vol_match.group(2)
            result["pages"] = vol_match.group(3)
        else:
            # Try Volume YYYY pattern
            vol_match2 = re.search(r'Volume\s+(\d+)', remaining, re.I)
            if vol_match2:
                result["volume"] = vol_match2.group(1)

            # Try pages: NNN-NNN
            pages_match = re.search(r'[,，:：]\s*(\d+)\s*[-–]\s*(\d+)\s*[.。]?\s*$', remaining)
            if pages_match:
                result["pages"] = f"{pages_match.group(1)}-{pages_match.group(2)}"
            elif not vol_match:
                pages_match2 = re.search(r'(\d+)\s*[-–]\s*(\d+)', remaining)
                if pages_match2:
                    result["pages"] = f"{pages_match2.group(1)}-{pages_match2.group(2)}"

            # Try issue
            issue_match = re.search(r'(\d+)\s*\((\d+)\)', remaining)
            if issue_match:
                result["volume"] = issue_match.group(1)
                result["issue"] = issue_match.group(2)

        # Split title and journal
        title, journal = self._split_title_journal(remaining, result["year"])
        result["title"] = title
        result["journal"] = journal

        return result

    def _parse_j_marker(self, text: str, doi: str = "") -> Dict[str, Any] | None:
        match = re.search(r'\[J\]\s*[,，]\s*([^,，]+)(?:[,，]\s*((?:19|20)\d{2}))?', text, re.I)
        if not match:
            return None

        before_marker = text[:match.start()].strip().rstrip(",，.。")
        journal = match.group(1).strip().rstrip(".。")
        year = match.group(2) or ""
        if not year:
            year_match = re.search(r'(?:19|20)\d{2}', text[match.end():])
            year = year_match.group(0) if year_match else ""

        tokens = [token.strip().strip(".。") for token in re.split(r'[,，]\s*', before_marker) if token.strip()]
        if len(tokens) < 2 or not journal:
            return None

        title_start = None
        for idx, token in enumerate(tokens):
            if not self._looks_like_author_name(token.rstrip("*")):
                title_start = idx
                break
        if title_start is None:
            title_start = max(0, len(tokens) - 1)

        authors = self._parse_authors(", ".join(tokens[:title_start])) if title_start > 0 else []
        title = ",".join(tokens[title_start:]).strip()
        if not title:
            return None

        result = {
            "title": title,
            "journal": journal,
            "year": year,
            "doi": doi,
            "issue": "",
            "volume": "",
            "pages": "",
            "authors": authors,
        }
        trailing = text[match.end():]
        vol_issue = re.search(r'(\d+)\s*\((\d+)\)', trailing)
        if vol_issue:
            result["volume"] = vol_issue.group(1)
            result["issue"] = vol_issue.group(2)
        else:
            volume = re.search(r'Volume\s+(\d+)|\bVol\.?\s*(\d+)', trailing, re.I)
            if volume:
                result["volume"] = volume.group(1) or volume.group(2) or ""
        pages = re.search(r'(\d+)\s*[-–]\s*(\d+)', trailing)
        if pages:
            result["pages"] = f"{pages.group(1)}-{pages.group(2)}"
        return result

    def _parse_comma_delimited(self, text: str, doi: str = "") -> Dict[str, Any] | None:
        tokens = [token.strip().strip(".。") for token in re.split(r'[,，]\s*', text) if token.strip()]
        if len(tokens) < 5:
            return None

        year_idx = next((idx for idx, token in enumerate(tokens) if re.fullmatch(r'(19|20)\d{2}', token)), -1)
        if year_idx < 2:
            return None

        journal_idx = year_idx - 1
        title_start = None
        for idx in range(journal_idx):
            if not self._looks_like_author_name(tokens[idx].rstrip('*')):
                title_start = idx
                break

        if title_start is None or title_start == 0 or title_start >= journal_idx:
            return None

        authors_tokens = tokens[:title_start]
        title_tokens = tokens[title_start:journal_idx]
        journal = tokens[journal_idx].strip().rstrip('.')
        title = ",".join(title_tokens).strip()
        title = re.sub(r'\[J\]', '', title, flags=re.I).strip()

        if not title or not journal:
            return None

        result = {
            "title": title,
            "journal": journal,
            "year": tokens[year_idx],
            "doi": doi,
            "issue": "",
            "volume": "",
            "pages": "",
            "authors": self._parse_authors(", ".join(authors_tokens)),
        }

        trailing = tokens[year_idx + 1:]
        if trailing:
            first = trailing[0]
            vol_issue = re.fullmatch(r'(\d+)\((\d+)\)', first)
            if vol_issue:
                result["volume"] = vol_issue.group(1)
                result["issue"] = vol_issue.group(2)
                trailing = trailing[1:]
            elif re.fullmatch(r'Volume\s+\d+', first, re.I):
                result["volume"] = re.sub(r'Volume\s+', '', first, flags=re.I)
                trailing = trailing[1:]

        if trailing:
            candidate = trailing[0]
            if re.fullmatch(r'\d+\s*[-–]\s*\d+', candidate):
                result["pages"] = candidate.replace(" ", "")
            elif re.fullmatch(r'\d{4,}', candidate):
                result["pages"] = candidate

        return result

    def _split_authors(self, text: str):
        """Split author list from the rest of the citation."""
        # Strategy: find the separator between authors and title
        # Authors are typically: Name1, Name2, Name3. Title...
        # or: Name1, Name2, Name3, Title. Journal...

        # Pattern 1: authors end with period before title
        # Look for the pattern: [name list]. [Title starts with capital or Chinese]

        # Try splitting at first '. ' that's after author names
        # Authors are comma-separated names (Chinese or English)

        # English author pattern: FirstName LastName (or F. LastName)
        # Chinese author pattern: 2-4 Chinese chars

        best_split = None

        # Try each potential separator position
        for sep in ['. ', '。', '．']:
            pos = text.find(sep)
            while pos > 0:
                before = text[:pos].strip()
                after = text[pos + len(sep):].strip()

                # Check if 'before' looks like author list
                if self._looks_like_authors(before) and len(after) > 10:
                    if best_split is None or pos < best_split[0]:
                        best_split = (pos, before, after)
                    break

                pos = text.find(sep, pos + 1)

        # Also try comma-separated where authors end and title begins
        # This handles: Author1, Author2, Title. Journal...
        if best_split is None:
            # Try to find where author names end
            comma_positions = [m.start() for m in re.finditer(r'[,，]\s*', text)]
            for cp in comma_positions:
                before = text[:cp].strip()
                after = text[cp + 1:].strip().lstrip(',， ')
                if self._looks_like_authors(before) and not self._looks_like_author_name(after[:20]):
                    # after starts with title, not another author
                    best_split = (cp, before, after)
                    break

        if best_split:
            return best_split[1], best_split[2]
        return None, text

    def _looks_like_authors(self, text: str) -> bool:
        """Check if text looks like a list of author names."""
        # Split by comma
        names = re.split(r'[,，]\s*', text)
        if len(names) < 1:
            return False
        valid = sum(1 for n in names if self._looks_like_author_name(n.strip()))
        return valid >= len(names) * 0.5 and valid >= 1

    def _looks_like_author_name(self, text: str) -> bool:
        """Check if text looks like a single author name."""
        text = text.strip().rstrip('*')
        if not text:
            return False
        # Chinese name: 2-4 Chinese chars
        if re.match(r'^[\u4e00-\u9fff]{2,5}$', text):
            return True
        if any(token in text for token in ["[J]", "]", "http", "doi", "/"]):
            return False
        parts = [part for part in text.replace(".", " ").split() if part]
        if 2 <= len(parts) <= 4 and all(re.fullmatch(r"[A-Za-z][A-Za-z\-']*", part) for part in parts):
            return True
        if 2 <= len(parts) <= 4 and all(re.fullmatch(r"[A-Za-z]\.?", part) for part in parts):
            return True
        return False

    def _parse_authors(self, text: str) -> List[Dict[str, Any]]:
        """Parse author string into list of author dicts."""
        names = re.split(r'[,，]\s*', text)
        authors = []
        for i, name in enumerate(names):
            name = name.strip()
            if not name:
                continue
            is_corresponding = '*' in name
            name = name.replace('*', '').strip()
            authors.append({
                "name": name,
                "order": i,
                "is_first_author": i == 0,
                "is_corresponding_author": is_corresponding,
            })
        return authors

    def _split_title_journal(self, text: str, year: str) -> tuple:
        """Split remaining text into title and journal."""
        # Remove year and volume/issue/pages info
        clean = text
        if year:
            # Remove from year onwards for journal extraction
            pass

        # Try to find journal by looking for period/comma separations after title
        # Common patterns:
        # 1. Title. Journal, Year...
        # 2. Title. Journal. Year...
        # 3. Title, Journal, Year...

        # Find all period positions
        parts = re.split(r'[.。]\s*', clean, maxsplit=3)

        if len(parts) >= 2:
            title_candidate = parts[0].strip()
            # Remove [J] marker from title
            title_candidate = re.sub(r'\[J\]', '', title_candidate).strip()
            journal_part = parts[1].strip()

            # Clean journal: remove year and numbers
            journal_clean = re.sub(r'[,，]\s*(19|20)\d{2}.*$', '', journal_part).strip()
            journal_clean = re.sub(r'\d+\(\d+\).*$', '', journal_clean).strip()
            journal_clean = journal_clean.rstrip(',，.:：')

            if len(title_candidate) > 5 and len(journal_clean) > 2:
                return title_candidate, journal_clean

        # Fallback: everything before year is title+journal
        if year:
            idx = clean.find(year)
            if idx > 0:
                before_year = clean[:idx].rstrip(',，. ')
                # Try to split at last period or comma
                for sep in ['. ', '。', '．', ', ']:
                    last_sep = before_year.rfind(sep)
                    if last_sep > 0:
                        title = before_year[:last_sep].strip()
                        title = re.sub(r'\[J\]', '', title).strip()
                        journal = before_year[last_sep + len(sep):].strip()
                        if len(title) > 5 and len(journal) > 2:
                            return title, journal

        return clean, ""
