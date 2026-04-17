"""Section splitter: split resume content by section headings."""
import re
from typing import Dict, List, Any, Optional, Tuple

SECTION_KEYWORDS = {
    "profile": ["个人简介", "基本信息", "个人信息", "简介", "个人简历"],
    "paper": ["论文", "发表论文", "学术论文", "期刊论文", "发表的论文", "学术成果",
              "代表性论文", "发表学术论文"],
    "project": ["项目", "科研项目", "主持项目", "参与项目", "课题", "主持的项目",
                "主要科研项目", "科研课题"],
    "award": ["获奖", "奖励", "科研获奖", "荣誉", "获奖情况", "科研奖励"],
    "patent": ["专利", "发明专利", "实用新型", "申请专利"],
    "software_copyright": ["软著", "软件著作", "计算机软件著作", "软件著作权"],
    "student_award": ["指导学生", "学生获奖", "指导研究生", "学生竞赛"],
    "conference": ["承办会议", "学术会议", "主办会议", "组织会议"],
    "special_issue": ["特刊", "专刊", "承办特刊"],
    "academic_role": ["学术兼职", "兼职", "社会兼职", "学术任职"],
    "academic_report": ["学术报告", "特邀报告", "受邀报告", "邀请报告"],
    "teaching_platform": ["平台建设", "教学平台", "学科建设", "学科及教学平台",
                          "教学平台建设"],
    "industry_standard": ["标准", "行业标准", "参与标准"],
}

# Section display order
SECTION_ORDER = [
    "profile", "paper", "project", "award", "patent",
    "software_copyright", "student_award", "conference",
    "special_issue", "academic_role", "academic_report",
    "teaching_platform", "industry_standard",
]


def _is_section_heading(text: str, bold: bool, level: int) -> str:
    """Check if a paragraph is a section heading. Returns section key or empty string."""
    clean = re.sub(r'[一二三四五六七八九十\d]+[、.．\s:：）)]+', '', text).strip()
    clean = re.sub(r'^[\d]+[\.\s]+', '', clean).strip()
    match = _best_section_match(clean, strong_hint=bold or level > 0)
    return match or ""


def _best_section_match(text: str, strong_hint: bool = False) -> Optional[str]:
    """Pick the most likely section when keywords overlap."""
    best: Optional[Tuple[int, int, str]] = None

    for section_key, keywords in SECTION_KEYWORDS.items():
        for kw in keywords:
            score = 0
            if text == kw:
                score = 300
            elif text.startswith(kw):
                score = 220
            elif kw in text and len(text) <= len(kw) + 20:
                score = 160
            elif strong_hint and kw in text:
                score = 80

            if score <= 0:
                continue

            candidate = (score, len(kw), section_key)
            if best is None or candidate > best:
                best = candidate

    return best[2] if best else None


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
            # Don't add the heading itself as content (unless it contains useful info)
            remaining = text
            for kw in SECTION_KEYWORDS.get(detected, []):
                remaining = remaining.replace(kw, "").strip()
            remaining = re.sub(r'^[一二三四五六七八九十\d]+[、.．\s:：）)]+', '', remaining).strip()
            if remaining and len(remaining) > 5:
                sections[current_section].append(remaining)
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
