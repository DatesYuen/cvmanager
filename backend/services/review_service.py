"""Review service: apply review actions and batch approve."""
from sqlalchemy.orm import Session
from backend.models import (ReviewRecord, Paper, Project, Award, Patent,
                            SoftwareCopyright, StudentAward, Conference,
                            SpecialIssue, AcademicRole, AcademicReport,
                            TeachingPlatform, IndustryStandard)
from backend.models.paper import PaperAuthor
from backend.models.patent import PatentApplicant
from backend.schemas.common import ReviewActionRequest, BatchReviewRequest
from backend.services.paper_service import derive_paper_role_flags

ENTITY_MODEL_MAP = {
    "papers": Paper,
    "projects": Project,
    "awards": Award,
    "patents": Patent,
    "software_copyrights": SoftwareCopyright,
    "student_awards": StudentAward,
    "conferences": Conference,
    "special_issues": SpecialIssue,
    "academic_roles": AcademicRole,
    "academic_reports": AcademicReport,
    "teaching_platforms": TeachingPlatform,
    "industry_standards": IndustryStandard,
}


def apply_review_action(db: Session, req: ReviewActionRequest, reviewer_id: int) -> bool:
    Model = ENTITY_MODEL_MAP.get(req.entity_type)
    if not Model:
        return False
    item = db.query(Model).get(req.entity_id)
    if not item:
        return False

    editable_columns = {
        c.name for c in Model.__table__.columns
        if c.name not in ("id", "person_id", "raw_text", "confidence", "review_status")
    }
    if req.updated_fields:
        if req.entity_type == "papers" and "authors_text" in req.updated_fields:
            _update_paper_authors(item, req.updated_fields.get("authors_text", ""))
        if req.entity_type == "patents" and "applicants_text" in req.updated_fields:
            _update_patent_applicants(item, req.updated_fields.get("applicants_text", ""))
        for field, value in req.updated_fields.items():
            if field in editable_columns and not isinstance(value, (dict, list)):
                setattr(item, field, "" if value is None else value)

    item.review_status = "approved" if req.action == "approve" else "rejected"

    record = ReviewRecord(
        entity_type=req.entity_type,
        entity_id=req.entity_id,
        person_id=item.person_id,
        action=req.action,
        reviewer_id=reviewer_id,
        comment=req.comment,
    )
    db.add(record)
    db.commit()
    return True


def batch_approve_by_confidence(db: Session, req: BatchReviewRequest,
                                reviewer_id: int) -> int:
    entity_types = req.entity_types or list(ENTITY_MODEL_MAP.keys())
    count = 0
    for etype in entity_types:
        Model = ENTITY_MODEL_MAP.get(etype)
        if not Model:
            continue
        items = db.query(Model).filter(
            Model.person_id == req.person_id,
            Model.review_status == "pending",
            Model.confidence >= req.confidence_threshold
        ).all()
        for item in items:
            item.review_status = "approved"
            record = ReviewRecord(
                entity_type=etype,
                entity_id=item.id,
                person_id=req.person_id,
                action="approve",
                reviewer_id=reviewer_id,
                comment=f"Auto-approved (confidence >= {req.confidence_threshold})",
            )
            db.add(record)
            count += 1
    db.commit()
    return count


def get_pending_items(db: Session, person_id: int) -> dict:
    result = {}
    ai_status_map = _get_ai_status_map(db, person_id)
    for etype, Model in ENTITY_MODEL_MAP.items():
        items = db.query(Model).filter(
            Model.person_id == person_id,
            Model.review_status == "pending"
        ).all()
        if items:
            result[etype] = [
                _serialize_pending_item(etype, item, Model, ai_status_map.get((etype, item.id)))
                for item in items
            ]
    return result


def _serialize_pending_item(entity_type: str, item, Model, ai_status: dict | None = None) -> dict:
    data = {
        "id": item.id,
        "raw_text": item.raw_text,
        "confidence": item.confidence,
        "review_status": item.review_status,
        **{
            c.name: getattr(item, c.name)
            for c in Model.__table__.columns
            if c.name not in ("id", "person_id", "raw_text", "confidence", "review_status")
        },
    }
    data["ai_review_status"] = ai_status.get("status") if ai_status else "not_reviewed"
    data["ai_review_message"] = ai_status.get("message") if ai_status else ""
    if entity_type == "papers":
        data["authors_text"] = ", ".join(
            f"{author.name}{'*' if author.is_corresponding_author else ''}"
            for author in item.authors
        )
    if entity_type == "patents":
        data["applicants_text"] = ", ".join(applicant.name for applicant in item.applicants)
    return data


def _update_paper_authors(paper, authors_text: str) -> None:
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


def _update_patent_applicants(patent, applicants_text: str) -> None:
    names = [segment.strip() for segment in applicants_text.replace("，", ",").split(",") if segment.strip()]
    patent.applicants.clear()
    for index, name in enumerate(names):
        patent.applicants.append(PatentApplicant(name=name, order=index))


def _get_ai_status_map(db: Session, person_id: int) -> dict:
    records = db.query(ReviewRecord).filter(
        ReviewRecord.person_id == person_id,
        ReviewRecord.action.in_(["ai_review_success", "ai_review_failed"])
    ).order_by(ReviewRecord.reviewed_at.desc()).all()
    status_map = {}
    for record in records:
        key = (record.entity_type, record.entity_id)
        if key not in status_map:
            status_map[key] = {
                "status": "success" if record.action == "ai_review_success" else "failed",
                "message": record.comment or "",
            }
    return status_map
