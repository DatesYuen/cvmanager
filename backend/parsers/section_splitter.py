"""Section splitter: split resume content by section headings."""
import re
from typing import Dict, List, Any

from backend.parsers.resume_format import (
    SECTION_ORDER,
    detect_section_heading,
    split_heading_inline_content,
)


def _is_section_heading(text: str, bold: bool, level: int) -> str:
    """Check if a paragraph is a section heading. Returns section key or empty string."""
    return detect_section_heading(text, bold, level) or ""


def _is_profile_inline_line(text: str) -> bool:
    """Contact info may appear at the end of the resume without a dedicated heading."""
    patterns = [
        r'(?:电话|手机|Tel|Phone)[：:\s]*[1]\d{10}',
        r'(?:E-?mail|邮箱|Email)[：:\s]*[\w.+-]+@[\w-]+\.[\w.-]+',
        r'(?:联系地址|地址|Address)[：:\s]*\S+',
    ]
    return any(re.search(pattern, text, re.I) for pattern in patterns)


def split_sections(paragraphs: List[Dict[str, Any]],
                   tables: List[Dict[str, Any]] = None) -> Dict[str, List[str]]:
    """Split paragraphs into sections.

    Returns:
        {"profile": ["line1", "line2", ...], "paper": [...], ...}
    """
    sections = {key: [] for key in SECTION_ORDER}
    current_section = "profile"  # Default to profile for initial content

    # Track which table was already used (for education/work tables near profile)
    table_texts = []
    if tables:
        for t in tables:
            for row in t["rows"]:
                table_texts.append("\t".join(row))

    for para in paragraphs:
        text = para["text"]
        bold = para.get("bold", False)
        level = para.get("level", 0)

        detected = _is_section_heading(text, bold, level)
        if detected:
            current_section = detected
            inline_content = split_heading_inline_content(text)
            if inline_content:
                sections[current_section].append(inline_content)
            continue

        if _is_profile_inline_line(text):
            sections["profile"].append(text)
        elif text:
            sections[current_section].append(text)

    # Add table content to profile section (for education/work tables)
    if table_texts and tables:
        for t in tables:
            rows = t["rows"]
            if len(rows) > 0:
                # Check if this looks like an education or work table
                header = "\t".join(rows[0]).lower()
                if any(kw in header for kw in ["学校", "学历", "学位", "专业", "起止"]):
                    for row in rows:
                        sections["profile"].append("EDUCATION_TABLE_ROW:" + "\t".join(row))
                elif any(kw in header for kw in ["单位", "职位", "职务", "工作"]):
                    for row in rows:
                        sections["profile"].append("WORK_TABLE_ROW:" + "\t".join(row))

    return sections
