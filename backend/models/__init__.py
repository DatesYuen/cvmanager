from backend.models.user import User
from backend.models.person import Person
from backend.models.resume import Resume
from backend.models.profile import Profile, Education, WorkExperience
from backend.models.paper import Paper, PaperAuthor
from backend.models.project import Project
from backend.models.award import Award
from backend.models.patent import Patent, PatentApplicant
from backend.models.software_copyright import SoftwareCopyright
from backend.models.student_award import StudentAward
from backend.models.conference import Conference
from backend.models.special_issue import SpecialIssue
from backend.models.academic_role import AcademicRole
from backend.models.academic_report import AcademicReport
from backend.models.teaching_platform import TeachingPlatform
from backend.models.industry_standard import IndustryStandard
from backend.models.attachment import Attachment
from backend.models.attachment_folder import AttachmentFolder
from backend.models.review import ReviewRecord
from backend.models.ai_settings import AISettings
from backend.models.journal_partition import JournalPartition

__all__ = [
    "User", "Person", "Resume",
    "Profile", "Education", "WorkExperience",
    "Paper", "PaperAuthor",
    "Project", "Award",
    "Patent", "PatentApplicant",
    "SoftwareCopyright", "StudentAward",
    "Conference", "SpecialIssue",
    "AcademicRole", "AcademicReport",
    "TeachingPlatform", "IndustryStandard",
    "Attachment", "AttachmentFolder", "ReviewRecord", "AISettings", "JournalPartition",
]
