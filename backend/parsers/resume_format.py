"""Definitions for the project resume format used by the parser."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class SectionDefinition:
    key: str
    headings: tuple[str, ...]
    keywords: tuple[str, ...]


SECTION_DEFINITIONS: tuple[SectionDefinition, ...] = (
    SectionDefinition(
        "profile",
        ("个人简介", "基本信息", "个人信息", "简介", "个人简历"),
        ("个人简介", "基本信息", "个人信息", "简介", "个人简历"),
    ),
    SectionDefinition(
        "paper",
        ("近年发表的主要论文情况有", "论文", "发表论文", "学术论文", "期刊论文", "代表性论文"),
        ("论文", "发表论文", "学术论文", "期刊论文", "发表的论文", "学术成果", "代表性论文", "发表学术论文"),
    ),
    SectionDefinition(
        "project",
        ("主持或参与的项目（代表性）", "主持或参与的项目", "项目", "主要科研项目", "科研项目"),
        ("项目", "科研项目", "主持项目", "参与项目", "课题", "主持的项目", "主要科研项目", "科研课题"),
    ),
    SectionDefinition(
        "award",
        ("科研获奖情况", "获奖情况", "科研获奖", "奖励情况"),
        ("获奖", "奖励", "科研获奖", "荣誉", "获奖情况", "科研奖励"),
    ),
    SectionDefinition(
        "patent",
        ("专利情况", "专利", "发明专利"),
        ("专利", "发明专利", "实用新型", "申请专利"),
    ),
    SectionDefinition(
        "software_copyright",
        ("软件著作权", "软件著作", "软著"),
        ("软著", "软件著作", "计算机软件著作", "软件著作权"),
    ),
    SectionDefinition(
        "student_award",
        ("指导学生获奖", "学生获奖", "指导研究生"),
        ("指导学生", "学生获奖", "指导研究生", "学生竞赛"),
    ),
    SectionDefinition(
        "conference",
        ("承办会议", "学术会议", "主办会议", "组织会议"),
        ("承办会议", "学术会议", "主办会议", "组织会议"),
    ),
    SectionDefinition(
        "special_issue",
        ("承办特刊", "承办专刊", "特刊", "专刊"),
        ("特刊", "专刊", "承办特刊"),
    ),
    SectionDefinition(
        "academic_role",
        ("学术兼职", "学术任职", "社会兼职"),
        ("学术兼职", "兼职", "社会兼职", "学术任职"),
    ),
    SectionDefinition(
        "academic_report",
        ("学术报告", "特邀报告", "受邀报告", "邀请报告"),
        ("学术报告", "特邀报告", "受邀报告", "邀请报告"),
    ),
    SectionDefinition(
        "teaching_platform",
        ("学科及教学平台建设情况", "学科及教学平台建设", "教学平台建设", "平台建设"),
        ("平台建设", "教学平台", "学科建设", "学科及教学平台", "教学平台建设"),
    ),
    SectionDefinition(
        "industry_standard",
        ("行业标准", "参与标准", "标准"),
        ("标准", "行业标准", "参与标准"),
    ),
)

SECTION_ORDER = [definition.key for definition in SECTION_DEFINITIONS]

SECTION_KEYWORDS = {
    definition.key: list(definition.keywords)
    for definition in SECTION_DEFINITIONS
}

_HEADING_ALIASES = {
    re.sub(r"\s+", "", heading): definition.key
    for definition in SECTION_DEFINITIONS
    for heading in definition.headings
}

_LEADING_NUMBER_RE = re.compile(r"^[一二三四五六七八九十\d]+[、.．\s:：）)]+")
_FORBIDDEN_HEADING_TOKENS = ("DOI", "ISSN", "登记号", "申请号", "授权号", "http://", "https://")


def normalize_heading_text(text: str) -> str:
    """Normalize a paragraph for section-heading comparison."""
    clean = _LEADING_NUMBER_RE.sub("", text or "").strip()
    clean = clean.rstrip("：:；;。.")
    return re.sub(r"\s+", "", clean)


def detect_section_heading(text: str, bold: bool = False, level: int = 0) -> Optional[str]:
    """Return the section key when a paragraph is a real section heading."""
    stripped = (text or "").strip()
    if not stripped:
        return None

    if any(token.lower() in stripped.lower() for token in _FORBIDDEN_HEADING_TOKENS):
        return None

    label, tail = _split_heading_label(stripped)
    normalized_label = normalize_heading_text(label)

    if tail and len(tail) > 5 and normalized_label not in _HEADING_ALIASES:
        return None

    if normalized_label in _HEADING_ALIASES and _looks_like_heading(stripped, label, tail, bold, level):
        return _HEADING_ALIASES[normalized_label]

    if not _looks_like_heading(stripped, label, tail, bold, level):
        return None

    return _best_keyword_match(normalized_label, strong_hint=bold or level > 0)


def split_heading_inline_content(text: str) -> str:
    """Return content after a heading colon, if the heading line also contains data."""
    _, tail = _split_heading_label(text or "")
    return tail.strip()


def _split_heading_label(text: str) -> tuple[str, str]:
    clean = _LEADING_NUMBER_RE.sub("", text or "").strip()
    match = re.match(r"^(.{1,40}?)[：:]\s*(.*)$", clean)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return clean, ""


def _looks_like_heading(text: str, label: str, tail: str, bold: bool, level: int) -> bool:
    if len(label) > 40:
        return False
    if tail and len(tail) > 5:
        return True
    if text.rstrip().endswith(("：", ":")):
        return True
    if level > 0:
        return True
    return bold and len(label) <= 24


def _best_keyword_match(text: str, strong_hint: bool = False) -> Optional[str]:
    best: Optional[tuple[int, int, str]] = None

    for section_key, keywords in SECTION_KEYWORDS.items():
        for keyword in keywords:
            normalized_keyword = normalize_heading_text(keyword)
            score = 0
            if text == normalized_keyword:
                score = 300
            elif text.startswith(normalized_keyword):
                score = 220
            elif normalized_keyword in text and len(text) <= len(normalized_keyword) + 20:
                score = 160
            elif strong_hint and normalized_keyword in text:
                score = 80

            if score <= 0:
                continue

            candidate = (score, len(normalized_keyword), section_key)
            if best is None or candidate > best:
                best = candidate

    return best[2] if best else None
