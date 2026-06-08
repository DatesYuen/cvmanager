"""AI review service using OpenAI Responses API structured outputs."""
import json
from typing import Any
from urllib import request, error

from sqlalchemy.orm import Session

from backend.models import AISettings, Paper, Patent, ReviewRecord
from backend.models.paper import PaperAuthor
from backend.models.patent import PatentApplicant
from backend.parsers.extractors.paper import PaperExtractor
from backend.parsers.extractors.project import ProjectExtractor
from backend.parsers.extractors.award import AwardExtractor
from backend.parsers.extractors.patent import PatentExtractor
from backend.parsers.extractors.software_copyright import SoftwareCopyrightExtractor
from backend.parsers.extractors.student_award import StudentAwardExtractor
from backend.parsers.extractors.conference import ConferenceExtractor
from backend.parsers.extractors.special_issue import SpecialIssueExtractor
from backend.parsers.extractors.academic_role import AcademicRoleExtractor
from backend.parsers.extractors.academic_report import AcademicReportExtractor
from backend.parsers.extractors.teaching_platform import TeachingPlatformExtractor
from backend.parsers.extractors.industry_standard import IndustryStandardExtractor
from backend.services.paper_service import derive_paper_role_flags
from backend.services.review_service import ENTITY_MODEL_MAP

DEFAULT_AI_PROMPT_TEMPLATE = """你是一个学术简历信息抽取助手。
请根据给定的原始文本，抽取 {{ text_class }} 类别的结构化信息，并严格返回 JSON。

要求：
1. 只返回 JSON，不要返回 Markdown、解释、注释或额外文本。
2. 字段必须与给定的返回格式一致。
3. 无法确定或原文不存在的字段允许返回空字符串。
4. 不要臆造 DOI、编号、日期、金额等信息。
5. 如果原文中有多个作者或申请人，请使用逗号分隔的字符串返回。
6. 保持原文语言，不要随意翻译专有名词。

类别：
{{ text_class }}

原始文本：
{{ origin_text }}

返回格式：
{{ return_format }}
"""

ENTITY_LABELS = {
    "papers": "论文",
    "projects": "项目",
    "awards": "获奖",
    "patents": "专利",
    "software_copyrights": "软著",
    "student_awards": "指导学生获奖",
    "conferences": "承办会议",
    "special_issues": "承办特刊",
    "academic_roles": "学术兼职",
    "academic_reports": "学术报告",
    "teaching_platforms": "教学平台建设",
    "industry_standards": "行业标准",
}

ENTITY_REVIEW_FIELDS = {
    "papers": ["authors_text", "title", "journal", "year", "doi", "volume", "issue", "pages"],
    "projects": ["project_type", "name", "project_number", "start_date", "end_date", "role", "amount"],
    "awards": ["award_name", "project_name", "participants", "awarding_body"],
    "patents": ["applicants_text", "patent_name", "application_number", "authorization_number", "status"],
    "software_copyrights": ["applicant", "name", "registration_date", "registration_number"],
    "student_awards": ["award_name", "level", "role", "award_date"],
    "conferences": ["name", "date", "role", "website"],
    "special_issues": ["issue_name", "journal_name", "date", "role"],
    "academic_roles": ["title", "start_date", "end_date"],
    "academic_reports": ["name", "report_type", "date"],
    "teaching_platforms": ["name", "issuing_body", "approval_date", "position"],
    "industry_standards": ["name", "publish_date", "role"],
}

EXTRACTOR_MAP = {
    "papers": PaperExtractor,
    "projects": ProjectExtractor,
    "awards": AwardExtractor,
    "patents": PatentExtractor,
    "software_copyrights": SoftwareCopyrightExtractor,
    "student_awards": StudentAwardExtractor,
    "conferences": ConferenceExtractor,
    "special_issues": SpecialIssueExtractor,
    "academic_roles": AcademicRoleExtractor,
    "academic_reports": AcademicReportExtractor,
    "teaching_platforms": TeachingPlatformExtractor,
    "industry_standards": IndustryStandardExtractor,
}


def get_or_create_ai_settings(db: Session) -> AISettings:
    settings = db.query(AISettings).first()
    if not settings:
        settings = AISettings(prompt_template=DEFAULT_AI_PROMPT_TEMPLATE)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    elif not settings.prompt_template:
        settings.prompt_template = DEFAULT_AI_PROMPT_TEMPLATE
        db.commit()
        db.refresh(settings)
    return settings


def get_public_ai_review_config(db: Session) -> dict[str, Any]:
    settings = get_or_create_ai_settings(db)
    return {
        "configured": bool(settings.api_key and settings.response_api_url and settings.model),
        "model": settings.model,
        "ai_review_confidence_threshold": settings.ai_review_confidence_threshold,
        "ai_review_concurrency": settings.ai_review_concurrency,
        "ai_review_retry_count": settings.ai_review_retry_count,
    }


def ai_review_low_confidence_items(db: Session, person_id: int, threshold: float | None = None,
                                   entity_types: list[str] | None = None,
                                   reviewer_id: int | None = None) -> dict[str, Any]:
    settings = get_or_create_ai_settings(db)
    _validate_ai_settings(settings)

    review_threshold = threshold if threshold is not None else settings.ai_review_confidence_threshold
    target_entity_types = entity_types or list(ENTITY_MODEL_MAP.keys())

    reviewed = []
    skipped = []
    failed = []
    total_count = 0

    for entity_type in target_entity_types:
        Model = ENTITY_MODEL_MAP.get(entity_type)
        if not Model:
            continue
        items = db.query(Model).filter(
            Model.person_id == person_id,
            Model.review_status == "pending",
            Model.confidence <= review_threshold,
        ).all()
        total_count += len(items)

        for item in items:
            try:
                ai_data = _review_single_item(settings, entity_type, item)
                _apply_ai_data(item, entity_type, ai_data)
                item.confidence = _calculate_confidence(entity_type, item, ai_data)
                _record_ai_review(db, item, entity_type, reviewer_id, "ai_review_success", "AI review succeeded")
                reviewed.append({"entity_type": entity_type, "entity_id": item.id})
            except Exception as exc:  # noqa: BLE001
                _record_ai_review(db, item, entity_type, reviewer_id, "ai_review_failed", str(exc))
                failed.append({"entity_type": entity_type, "entity_id": item.id, "message": str(exc)})

    db.commit()

    for entity_type in target_entity_types:
        Model = ENTITY_MODEL_MAP.get(entity_type)
        if not Model:
            continue
        count = db.query(Model).filter(
            Model.person_id == person_id,
            Model.review_status == "pending",
            Model.confidence > review_threshold,
        ).count()
        if count:
            skipped.append({"entity_type": entity_type, "count": count})

    return {
        "success": True,
        "total_count": total_count,
        "reviewed_count": len(reviewed),
        "reviewed": reviewed,
        "skipped": skipped,
        "failed": failed,
    }


def ai_review_single_item(db: Session, entity_type: str, entity_id: int,
                          reviewer_id: int | None = None,
                          raw_text_override: str | None = None) -> dict[str, Any]:
    settings = get_or_create_ai_settings(db)
    _validate_ai_settings(settings)
    Model = ENTITY_MODEL_MAP.get(entity_type)
    if not Model:
        raise ValueError("Unsupported entity type")
    item = db.query(Model).get(entity_id)
    if not item:
        raise ValueError("Entity not found")
    if raw_text_override is not None:
        item.raw_text = raw_text_override
    last_error = None
    for attempt in range(settings.ai_review_retry_count + 1):
        try:
            ai_data = _review_single_item(settings, entity_type, item)
            _apply_ai_data(item, entity_type, ai_data)
            item.confidence = _calculate_confidence(entity_type, item, ai_data)
            _record_ai_review(db, item, entity_type, reviewer_id, "ai_review_success", "AI review succeeded")
            db.commit()
            return {"success": True, "total_count": 1, "reviewed_count": 1, "reviewed": [{"entity_type": entity_type, "entity_id": entity_id}], "failed": [], "skipped": []}
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt >= settings.ai_review_retry_count:
                break
    _record_ai_review(db, item, entity_type, reviewer_id, "ai_review_failed", str(last_error))
    db.commit()
    return {"success": True, "total_count": 1, "reviewed_count": 0, "reviewed": [], "failed": [{"entity_type": entity_type, "entity_id": entity_id, "message": str(last_error)}], "skipped": []}


def test_ai_connection(db: Session, sample_text: str, entity_type: str) -> dict[str, Any]:
    settings = get_or_create_ai_settings(db)
    _validate_ai_settings(settings)
    if entity_type not in ENTITY_REVIEW_FIELDS:
        raise ValueError("Unsupported entity type")
    fields = ENTITY_REVIEW_FIELDS[entity_type]
    return_format = json.dumps({field: "" for field in fields}, ensure_ascii=False, indent=2)
    prompt = (
        settings.prompt_template
        .replace("{{ origin_text }}", sample_text or "")
        .replace("{{ text_class }}", ENTITY_LABELS.get(entity_type, entity_type))
        .replace("{{ return_format }}", return_format)
    )
    schema = _build_json_schema(entity_type, fields)
    raw_text = _call_openai_responses_api(settings, prompt, schema)
    parsed = json.loads(raw_text)
    return {"success": True, "message": "AI service call succeeded", "parsed_result": parsed}


def _validate_ai_settings(settings: AISettings) -> None:
    if not settings.api_key:
        raise ValueError("OpenAI API key is not configured")
    if not settings.response_api_url:
        raise ValueError("OpenAI Responses URL is not configured")
    if not settings.model:
        raise ValueError("OpenAI model is not configured")


def _review_single_item(settings: AISettings, entity_type: str, item) -> dict[str, Any]:
    fields = ENTITY_REVIEW_FIELDS[entity_type]
    return_format = json.dumps({field: "" for field in fields}, ensure_ascii=False, indent=2)
    prompt = (
        settings.prompt_template
        .replace("{{ origin_text }}", item.raw_text or "")
        .replace("{{ text_class }}", ENTITY_LABELS.get(entity_type, entity_type))
        .replace("{{ return_format }}", return_format)
    )
    schema = _build_json_schema(entity_type, fields)
    raw_text = _call_openai_responses_api(settings, prompt, schema)
    parsed = json.loads(raw_text)
    return {field: _normalize_ai_value(parsed.get(field, "")) for field in fields}


def _build_json_schema(entity_type: str, fields: list[str]) -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {field: {"type": "string"} for field in fields},
        "required": fields,
        "name": f"{entity_type}_review_result",
        "strict": True,
    }


def _call_openai_responses_api(settings: AISettings, prompt: str, schema: dict[str, Any]) -> str:
    payload = {
        "model": settings.model,
        "input": prompt,
        "text": {
            "format": {
                "type": "json_schema",
                "name": schema["name"],
                "strict": schema["strict"],
                "schema": {
                    "type": schema["type"],
                    "additionalProperties": schema["additionalProperties"],
                    "properties": schema["properties"],
                    "required": schema["required"],
                },
            }
        },
    }
    req = request.Request(
        settings.response_api_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.api_key}",
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"OpenAI request failed: {detail or exc.reason}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"OpenAI request failed: {exc.reason}") from exc

    text_output = body.get("output_text") or _extract_output_text(body)
    if not text_output:
        raise RuntimeError("OpenAI did not return text output")
    return text_output


def _extract_output_text(body: dict[str, Any]) -> str:
    fragments = []
    for item in body.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            text_value = content.get("text")
            if isinstance(text_value, dict):
                text_value = text_value.get("value", "")
            if isinstance(text_value, str) and text_value:
                fragments.append(text_value)
    return "\n".join(fragments).strip()


def _normalize_ai_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value).strip()


def _apply_ai_data(item, entity_type: str, ai_data: dict[str, str]) -> None:
    for field, value in ai_data.items():
        if field in ("authors_text", "applicants_text"):
            continue
        if hasattr(item, field):
            setattr(item, field, value)

    if entity_type == "papers":
        _apply_paper_authors(item, ai_data.get("authors_text", ""))
    if entity_type == "patents":
        _apply_patent_applicants(item, ai_data.get("applicants_text", ""))


def _apply_paper_authors(paper: Paper, authors_text: str) -> None:
    names = [segment.strip() for segment in authors_text.replace("，", ",").split(",") if segment.strip()]
    paper.authors.clear()
    for index, name in enumerate(names):
        is_corresponding = name.endswith("*")
        clean_name = name.rstrip("*").strip()
        if clean_name:
            paper.authors.append(
                PaperAuthor(
                    name=clean_name,
                    order=index,
                    is_first_author=index == 0,
                    is_corresponding_author=is_corresponding,
                )
            )
    flags = derive_paper_role_flags(
        [
            {
                "name": author.name,
                "is_first_author": author.is_first_author,
                "is_corresponding_author": author.is_corresponding_author,
            }
            for author in paper.authors
        ],
        paper.person.name,
        getattr(paper.person, "name_en", ""),
    )
    paper.is_first_author = flags["is_first_author"]
    paper.is_corresponding_author = flags["is_corresponding_author"]


def _apply_patent_applicants(patent: Patent, applicants_text: str) -> None:
    names = [segment.strip() for segment in applicants_text.replace("，", ",").split(",") if segment.strip()]
    patent.applicants.clear()
    for index, name in enumerate(names):
        patent.applicants.append(PatentApplicant(name=name, order=index))


def _calculate_confidence(entity_type: str, item, ai_data: dict[str, str]) -> float:
    extractor = EXTRACTOR_MAP[entity_type]()
    payload = {**ai_data}
    if entity_type == "papers":
        payload["authors"] = [
            {
                "name": author.name,
                "order": author.order,
                "is_first_author": author.is_first_author,
                "is_corresponding_author": author.is_corresponding_author,
            }
            for author in item.authors
        ]
    if entity_type == "patents":
        payload["applicants"] = [{"name": applicant.name, "order": applicant.order} for applicant in item.applicants]
    return extractor.calculate_confidence(payload)


def _record_ai_review(db: Session, item, entity_type: str, reviewer_id: int | None,
                      action: str, comment: str) -> None:
    db.add(
        ReviewRecord(
            entity_type=entity_type,
            entity_id=item.id,
            person_id=item.person_id,
            action=action,
            reviewer_id=reviewer_id,
            comment=comment,
        )
    )
