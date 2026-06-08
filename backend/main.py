from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from backend.database import engine, Base, SessionLocal
from backend.models import *  # noqa: F401, F403 - import all models for table creation
from backend.services.auth_service import hash_password
from backend.config import DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD
from backend.services.journal_partition_service import import_partition_workbook, apply_partition_to_paper_data

from backend.routers import auth, users, persons, resumes, reviews, attachments, export, ai_agent, profile, external, showcase
from backend.routers.entity_crud import register_entity, create_entity_router, ENTITY_REGISTRY

from backend.models.paper import Paper
from backend.models.project import Project
from backend.models.award import Award
from backend.models.patent import Patent
from backend.models.software_copyright import SoftwareCopyright
from backend.models.student_award import StudentAward
from backend.models.conference import Conference
from backend.models.special_issue import SpecialIssue
from backend.models.academic_role import AcademicRole
from backend.models.academic_report import AcademicReport
from backend.models.teaching_platform import TeachingPlatform
from backend.models.industry_standard import IndustryStandard

from backend.schemas.items import (
    PaperOut, PaperCreate, PaperUpdate,
    ProjectOut, ProjectCreate, ProjectUpdate,
    AwardOut, AwardCreate, AwardUpdate,
    PatentOut, PatentCreate, PatentUpdate,
    SoftwareCopyrightOut, SoftwareCopyrightCreate, SoftwareCopyrightUpdate,
    StudentAwardOut, StudentAwardCreate, StudentAwardUpdate,
    ConferenceOut, ConferenceCreate, ConferenceUpdate,
    SpecialIssueOut, SpecialIssueCreate, SpecialIssueUpdate,
    AcademicRoleOut, AcademicRoleCreate, AcademicRoleUpdate,
    AcademicReportOut, AcademicReportCreate, AcademicReportUpdate,
    TeachingPlatformOut, TeachingPlatformCreate, TeachingPlatformUpdate,
    IndustryStandardOut, IndustryStandardCreate, IndustryStandardUpdate,
)

# Register all entity types
register_entity("papers", Paper, PaperOut, PaperCreate, PaperUpdate)
register_entity("projects", Project, ProjectOut, ProjectCreate, ProjectUpdate)
register_entity("awards", Award, AwardOut, AwardCreate, AwardUpdate)
register_entity("patents", Patent, PatentOut, PatentCreate, PatentUpdate)
register_entity("software_copyrights", SoftwareCopyright, SoftwareCopyrightOut, SoftwareCopyrightCreate, SoftwareCopyrightUpdate)
register_entity("student_awards", StudentAward, StudentAwardOut, StudentAwardCreate, StudentAwardUpdate)
register_entity("conferences", Conference, ConferenceOut, ConferenceCreate, ConferenceUpdate)
register_entity("special_issues", SpecialIssue, SpecialIssueOut, SpecialIssueCreate, SpecialIssueUpdate)
register_entity("academic_roles", AcademicRole, AcademicRoleOut, AcademicRoleCreate, AcademicRoleUpdate)
register_entity("academic_reports", AcademicReport, AcademicReportOut, AcademicReportCreate, AcademicReportUpdate)
register_entity("teaching_platforms", TeachingPlatform, TeachingPlatformOut, TeachingPlatformCreate, TeachingPlatformUpdate)
register_entity("industry_standards", IndustryStandard, IndustryStandardOut, IndustryStandardCreate, IndustryStandardUpdate)

app = FastAPI(title="CV Manager", version="1.0.0",
              description="Academic Resume Management System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(persons.router)
app.include_router(resumes.router)
app.include_router(reviews.router)
app.include_router(attachments.router)
app.include_router(export.router)
app.include_router(ai_agent.router)
app.include_router(external.router)
app.include_router(profile.router)
app.include_router(showcase.router)

# Include entity CRUD routers
for entity_name in ENTITY_REGISTRY:
    app.include_router(create_entity_router(entity_name))


# Stats endpoint for dashboard
@app.get("/api/stats")
def get_stats():
    db = SessionLocal()
    try:
        from backend.models.person import Person
        from backend.models.user import User as UserModel
        stats = {
            "persons": db.query(Person).count(),
            "users": db.query(UserModel).count(),
            "papers": db.query(Paper).count(),
            "projects": db.query(Project).count(),
            "patents": db.query(Patent).count(),
            "awards": db.query(Award).count(),
            "pending_reviews": sum(
                db.query(M).filter(M.review_status == "pending").count()
                for M in [Paper, Project, Award, Patent, SoftwareCopyright,
                          StudentAward, Conference, SpecialIssue, AcademicRole,
                          AcademicReport, TeachingPlatform, IndustryStandard]
            ),
        }
        return stats
    finally:
        db.close()


@app.on_event("startup")
def on_startup():
    # Create tables
    Base.metadata.create_all(bind=engine)
    _migrate_patent_schema()
    _import_journal_partitions()

    # Create default admin user
    db = SessionLocal()
    try:
        from backend.models.user import User as UserModel
        admin = db.query(UserModel).filter(UserModel.username == DEFAULT_ADMIN_USERNAME).first()
        if not admin:
            admin = UserModel(
                username=DEFAULT_ADMIN_USERNAME,
                password_hash=hash_password(DEFAULT_ADMIN_PASSWORD),
                display_name="Administrator",
                role="admin",
                permissions={},
                is_active=True,
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()


def _migrate_patent_schema():
    with engine.begin() as conn:
        columns = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info(patents)").fetchall()}
        if not columns:
            patent_columns = set()
        else:
            patent_columns = columns

            if "application_number" not in patent_columns:
                conn.exec_driver_sql("ALTER TABLE patents ADD COLUMN application_number VARCHAR(100) DEFAULT ''")
            if "authorization_number" not in patent_columns:
                conn.exec_driver_sql("ALTER TABLE patents ADD COLUMN authorization_number VARCHAR(100) DEFAULT ''")

            if "patent_number" in patent_columns:
                conn.exec_driver_sql(
                    """
                    UPDATE patents
                    SET application_number = CASE
                        WHEN (application_number IS NULL OR application_number = '')
                             AND patent_number LIKE '%.%' THEN patent_number
                        ELSE application_number
                    END,
                        authorization_number = CASE
                        WHEN (authorization_number IS NULL OR authorization_number = '')
                             AND patent_number NOT LIKE '%.%'
                             AND patent_number != '' THEN patent_number
                        ELSE authorization_number
                    END
                    WHERE patent_number IS NOT NULL AND patent_number != ''
                    """
                )

        person_columns = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info(persons)").fetchall()}
        if person_columns and "name_en" not in person_columns:
            conn.exec_driver_sql("ALTER TABLE persons ADD COLUMN name_en VARCHAR(100) DEFAULT ''")

        paper_columns = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info(papers)").fetchall()}
        if paper_columns:
            if "is_first_author" not in paper_columns:
                conn.exec_driver_sql("ALTER TABLE papers ADD COLUMN is_first_author BOOLEAN DEFAULT 0")
            if "is_corresponding_author" not in paper_columns:
                conn.exec_driver_sql("ALTER TABLE papers ADD COLUMN is_corresponding_author BOOLEAN DEFAULT 0")
            if "cas_partition" not in paper_columns:
                conn.exec_driver_sql("ALTER TABLE papers ADD COLUMN cas_partition VARCHAR(20) DEFAULT '未收录'")
            if "is_top_journal" not in paper_columns:
                conn.exec_driver_sql("ALTER TABLE papers ADD COLUMN is_top_journal BOOLEAN DEFAULT 0")
            if "issn" not in paper_columns:
                conn.exec_driver_sql("ALTER TABLE papers ADD COLUMN issn VARCHAR(50) DEFAULT ''")
            if "eissn" not in paper_columns:
                conn.exec_driver_sql("ALTER TABLE papers ADD COLUMN eissn VARCHAR(50) DEFAULT ''")
            if "impact_factor" not in paper_columns:
                conn.exec_driver_sql("ALTER TABLE papers ADD COLUMN impact_factor FLOAT")
            if "source_type" not in paper_columns:
                conn.exec_driver_sql("ALTER TABLE papers ADD COLUMN source_type VARCHAR(20) DEFAULT '未知'")
            if "citation_count" not in paper_columns:
                conn.exec_driver_sql("ALTER TABLE papers ADD COLUMN citation_count INTEGER")
            if "citation_note" not in paper_columns:
                conn.exec_driver_sql("ALTER TABLE papers ADD COLUMN citation_note VARCHAR(300) DEFAULT ''")
            if "impact_factor" in paper_columns:
                conn.exec_driver_sql("UPDATE papers SET impact_factor = NULL WHERE impact_factor = ''")
            if "citation_count" in paper_columns:
                conn.exec_driver_sql("UPDATE papers SET citation_count = NULL WHERE citation_count = ''")

        ai_columns = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info(ai_settings)").fetchall()}
        if ai_columns:
            if "ai_review_concurrency" not in ai_columns:
                conn.exec_driver_sql("ALTER TABLE ai_settings ADD COLUMN ai_review_concurrency INTEGER DEFAULT 2")
            if "ai_review_retry_count" not in ai_columns:
                conn.exec_driver_sql("ALTER TABLE ai_settings ADD COLUMN ai_review_retry_count INTEGER DEFAULT 1")

        attachment_columns = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info(attachments)").fetchall()}
        if attachment_columns and "folder_id" not in attachment_columns:
            conn.exec_driver_sql("ALTER TABLE attachments ADD COLUMN folder_id INTEGER")


def _import_journal_partitions():
    db = SessionLocal()
    try:
        import_partition_workbook(db)
        for paper in db.query(Paper).all():
            data = {
                "journal": paper.journal,
                "doi": paper.doi,
                "cas_partition": paper.cas_partition,
                "is_top_journal": paper.is_top_journal,
                "issn": paper.issn,
                "eissn": paper.eissn,
                "impact_factor": paper.impact_factor,
                "source_type": paper.source_type,
            }
            before = dict(data)
            apply_partition_to_paper_data(db, data)
            if data != before:
                for field, value in data.items():
                    if hasattr(paper, field):
                        setattr(paper, field, value)
        db.commit()
    finally:
        db.close()
