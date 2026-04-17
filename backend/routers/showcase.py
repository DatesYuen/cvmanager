from typing import Any
import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from backend.database import SessionLocal
from backend.models import (
    Person, Profile, Education, WorkExperience, Attachment,
    Paper, Project, Award, Patent, SoftwareCopyright,
    StudentAward, Conference, SpecialIssue, AcademicRole,
    AcademicReport, TeachingPlatform, IndustryStandard,
)

router = APIRouter(prefix="/api/showcase", tags=["showcase"])

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


@router.get("/persons")
def list_showcase_persons():
    db = SessionLocal()
    try:
        persons = db.query(Person).order_by(Person.updated_at.desc()).all()
        return [
            {
                "id": person.id,
                "name": person.name,
                "name_en": person.name_en,
                "updated_at": person.updated_at,
            }
            for person in persons
        ]
    finally:
        db.close()


@router.get("/persons/{person_id}")
def get_showcase_person(person_id: int):
    db = SessionLocal()
    try:
        person = db.query(Person).get(person_id)
        if not person:
            raise HTTPException(status_code=404, detail="Person not found")

        profile = db.query(Profile).filter(Profile.person_id == person_id).first()
        educations = db.query(Education).filter(Education.person_id == person_id).all()
        work_exps = db.query(WorkExperience).filter(WorkExperience.person_id == person_id).all()

        payload = {
            "person": {
                "id": person.id,
                "name": person.name,
                "name_en": person.name_en,
                "updated_at": person.updated_at,
            },
            "profile": {
                "introduction": profile.introduction if profile else "",
                "phone": profile.phone if profile else "",
                "email": profile.email if profile else "",
                "address": profile.address if profile else "",
            },
            "educations": [_serialize_simple(item) for item in educations],
            "work_experiences": [_serialize_simple(item) for item in work_exps],
            "items": {},
        }

        for entity_type, Model in ENTITY_MODEL_MAP.items():
            items = db.query(Model).filter(
                Model.person_id == person_id,
                Model.review_status == "approved",
            ).all()
            payload["items"][entity_type] = [_serialize_reviewable_item(db, entity_type, item) for item in items]

        return payload
    finally:
        db.close()


@router.get("/attachments")
def list_showcase_attachments(entity_type: str, entity_id: int):
    db = SessionLocal()
    try:
        _ensure_entity_visible(db, entity_type, entity_id)
        attachments = db.query(Attachment).filter(
            Attachment.entity_type == entity_type,
            Attachment.entity_id == entity_id,
        ).all()
        return [
            {
                "id": attachment.id,
                "entity_type": attachment.entity_type,
                "entity_id": attachment.entity_id,
                "original_filename": attachment.original_filename,
                "uploaded_at": attachment.uploaded_at,
            }
            for attachment in attachments
        ]
    finally:
        db.close()


@router.get("/attachments/download/{attachment_id}")
def download_showcase_attachment(attachment_id: int):
    db = SessionLocal()
    try:
        attachment = db.query(Attachment).get(attachment_id)
        if not attachment:
            raise HTTPException(status_code=404, detail="Attachment not found")
        _ensure_entity_visible(db, attachment.entity_type, attachment.entity_id)
        if not os.path.exists(attachment.file_path):
            raise HTTPException(status_code=404, detail="File not found on disk")
        return FileResponse(attachment.file_path, filename=attachment.original_filename)
    finally:
        db.close()


def _serialize_simple(item) -> dict[str, Any]:
    return {column.name: getattr(item, column.name) for column in item.__table__.columns if column.name != "person_id"}


def _serialize_reviewable_item(db, entity_type: str, item) -> dict[str, Any]:
    data = {
        column.name: getattr(item, column.name)
        for column in item.__table__.columns
        if column.name not in ("person_id", "raw_text", "confidence", "review_status")
    }
    if entity_type == "papers":
        data["authors"] = [
            {
                "name": author.name,
                "order": author.order,
                "is_first_author": author.is_first_author,
                "is_corresponding_author": author.is_corresponding_author,
            }
            for author in item.authors
        ]
    if entity_type == "patents":
        data["applicants"] = [
            {"name": applicant.name, "order": applicant.order}
            for applicant in item.applicants
        ]
    data["attachments"] = [
        {
            "id": attachment.id,
            "original_filename": attachment.original_filename,
            "uploaded_at": attachment.uploaded_at,
        }
        for attachment in db.query(Attachment).filter(
            Attachment.entity_type == entity_type,
            Attachment.entity_id == item.id,
        ).all()
    ]
    return data


def _ensure_entity_visible(db, entity_type: str, entity_id: int) -> None:
    Model = ENTITY_MODEL_MAP.get(entity_type)
    if not Model:
        raise HTTPException(status_code=404, detail="Entity not found")
    item = db.query(Model).get(entity_id)
    if not item or item.review_status != "approved":
        raise HTTPException(status_code=404, detail="Entity not found")
