"""Resume service: orchestrates DOCX parsing, extraction, and diff-based DB updates."""
from sqlalchemy.orm import Session

from backend.models import (
    Person, Resume, Profile, Education, WorkExperience,
    Paper, PaperAuthor, Project, Award, Patent, PatentApplicant,
    SoftwareCopyright, StudentAward, Conference, SpecialIssue,
    AcademicRole, AcademicReport, TeachingPlatform, IndustryStandard,
)
from backend.parsers.docx_reader import read_docx
from backend.parsers.section_splitter import split_sections
from backend.parsers.diff_engine import diff_items

from backend.parsers.extractors.profile import ProfileExtractor
from backend.parsers.extractors.paper import PaperExtractor
from backend.parsers.extractors.project import ProjectExtractor
from backend.parsers.extractors.patent import PatentExtractor
from backend.parsers.extractors.software_copyright import SoftwareCopyrightExtractor
from backend.parsers.extractors.award import AwardExtractor
from backend.parsers.extractors.student_award import StudentAwardExtractor
from backend.parsers.extractors.conference import ConferenceExtractor
from backend.parsers.extractors.special_issue import SpecialIssueExtractor
from backend.parsers.extractors.academic_role import AcademicRoleExtractor
from backend.parsers.extractors.academic_report import AcademicReportExtractor
from backend.parsers.extractors.teaching_platform import TeachingPlatformExtractor
from backend.parsers.extractors.industry_standard import IndustryStandardExtractor
from backend.services.paper_service import derive_paper_role_flags, enrich_paper_data
from backend.config import ENABLE_PUBLIC_PAPER_LOOKUP_ON_PARSE


def parse_resume(db: Session, resume: Resume, person: Person):
    """Parse a DOCX resume and store extracted data, using diff for updates."""
    doc_data = read_docx(resume.file_path)
    sections = split_sections(doc_data["paragraphs"], doc_data["tables"])

    # Parse profile section
    _parse_profile(db, person, sections.get("profile", []))

    # Parse all entity sections with diff-based updates
    extractors = {
        "paper": (PaperExtractor(), Paper, _save_papers),
        "project": (ProjectExtractor(), Project, _save_simple_items),
        "award": (AwardExtractor(), Award, _save_simple_items),
        "patent": (PatentExtractor(), Patent, _save_patents),
        "software_copyright": (SoftwareCopyrightExtractor(), SoftwareCopyright, _save_simple_items),
        "student_award": (StudentAwardExtractor(), StudentAward, _save_simple_items),
        "conference": (ConferenceExtractor(), Conference, _save_simple_items),
        "special_issue": (SpecialIssueExtractor(), SpecialIssue, _save_simple_items),
        "academic_role": (AcademicRoleExtractor(), AcademicRole, _save_simple_items),
        "academic_report": (AcademicReportExtractor(), AcademicReport, _save_simple_items),
        "teaching_platform": (TeachingPlatformExtractor(), TeachingPlatform, _save_simple_items),
        "industry_standard": (IndustryStandardExtractor(), IndustryStandard, _save_simple_items),
    }

    for section_key, (extractor, Model, saver) in extractors.items():
        lines = sections.get(section_key, [])
        if not lines:
            continue

        new_items = extractor.extract(lines)
        if not new_items:
            continue
        if section_key == "paper":
            for item in new_items:
                item.update(derive_paper_role_flags(item.get("authors", []), person.name, person.name_en))
                item.update(enrich_paper_data(
                    db,
                    item,
                    fetch_external=ENABLE_PUBLIC_PAPER_LOOKUP_ON_PARSE,
                ))

        # Get existing items for diff
        existing = db.query(Model).filter(Model.person_id == person.id).all()
        old_items = [{"raw_text": getattr(e, "raw_text", ""), "id": e.id} for e in existing]

        diff = diff_items(old_items, new_items)

        saver(db, person.id, Model, diff)

    db.commit()


def _parse_profile(db: Session, person: Person, lines: list):
    """Parse and save profile, education, work experience."""
    extractor = ProfileExtractor()
    data = extractor.extract(lines)

    # Update or create profile
    profile = db.query(Profile).filter(Profile.person_id == person.id).first()
    if not profile:
        profile = Profile(person_id=person.id)
        db.add(profile)

    profile.introduction = data.get("introduction", "")
    if data.get("phone"):
        profile.phone = data["phone"]
    if data.get("email"):
        profile.email = data["email"]
    if data.get("address"):
        profile.address = data["address"]

    # Update education entries
    if data.get("educations"):
        # Replace all education entries
        db.query(Education).filter(Education.person_id == person.id).delete()
        for edu in data["educations"]:
            db.add(Education(person_id=person.id, **edu))

    # Update work experience entries
    if data.get("work_experiences"):
        db.query(WorkExperience).filter(WorkExperience.person_id == person.id).delete()
        for work in data["work_experiences"]:
            db.add(WorkExperience(person_id=person.id, **work))

    db.flush()


def _save_papers(db: Session, person_id: int, Model, diff: dict):
    """Save paper items with author relationships."""
    # Add new papers
    for item in diff["added"]:
        authors_data = item.pop("authors", [])
        paper = Paper(person_id=person_id, **{k: v for k, v in item.items()
                                               if k in _get_columns(Paper)})
        db.add(paper)
        db.flush()
        for a in authors_data:
            db.add(PaperAuthor(paper_id=paper.id, **a))

    # Update modified papers
    for old, new in diff["modified"]:
        if "id" in old:
            paper = db.query(Paper).get(old["id"])
            if paper:
                authors_data = new.pop("authors", [])
                for k, v in new.items():
                    if k in _get_columns(Paper) and k != "id":
                        setattr(paper, k, v)
                paper.review_status = "pending"  # Re-review modified items
                # Update authors
                db.query(PaperAuthor).filter(PaperAuthor.paper_id == paper.id).delete()
                for a in authors_data:
                    db.add(PaperAuthor(paper_id=paper.id, **a))


def _save_patents(db: Session, person_id: int, Model, diff: dict):
    """Save patent items with applicant relationships."""
    for item in diff["added"]:
        applicants_data = item.pop("applicants", [])
        patent = Patent(person_id=person_id, **{k: v for k, v in item.items()
                                                 if k in _get_columns(Patent)})
        db.add(patent)
        db.flush()
        for a in applicants_data:
            db.add(PatentApplicant(patent_id=patent.id, **a))

    for old, new in diff["modified"]:
        if "id" in old:
            patent = db.query(Patent).get(old["id"])
            if patent:
                applicants_data = new.pop("applicants", [])
                for k, v in new.items():
                    if k in _get_columns(Patent) and k != "id":
                        setattr(patent, k, v)
                patent.review_status = "pending"
                db.query(PatentApplicant).filter(PatentApplicant.patent_id == patent.id).delete()
                for a in applicants_data:
                    db.add(PatentApplicant(patent_id=patent.id, **a))


def _save_simple_items(db: Session, person_id: int, Model, diff: dict):
    """Save items without nested relationships."""
    columns = _get_columns(Model)

    for item in diff["added"]:
        obj = Model(person_id=person_id, **{k: v for k, v in item.items() if k in columns})
        db.add(obj)

    for old, new in diff["modified"]:
        if "id" in old:
            obj = db.query(Model).get(old["id"])
            if obj:
                for k, v in new.items():
                    if k in columns and k != "id":
                        setattr(obj, k, v)
                obj.review_status = "pending"


def _get_columns(Model) -> set:
    return {c.name for c in Model.__table__.columns} - {"id", "person_id"}
