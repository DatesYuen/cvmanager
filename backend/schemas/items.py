from typing import Optional, List
from pydantic import BaseModel


class ProfileBase(BaseModel):
    introduction: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""


class ProfileOut(ProfileBase):
    id: int
    person_id: int

    class Config:
        from_attributes = True


class ProfileUpdate(BaseModel):
    introduction: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None


class EducationBase(BaseModel):
    start_date: str = ""
    end_date: str = ""
    school: str = ""
    major: str = ""
    degree: str = ""


class EducationCreate(EducationBase):
    person_id: int


class EducationOut(EducationBase):
    id: int
    person_id: int

    class Config:
        from_attributes = True


class EducationUpdate(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    school: Optional[str] = None
    major: Optional[str] = None
    degree: Optional[str] = None


class WorkExperienceBase(BaseModel):
    start_date: str = ""
    end_date: str = ""
    organization: str = ""
    position: str = ""


class WorkExperienceCreate(WorkExperienceBase):
    person_id: int


class WorkExperienceOut(WorkExperienceBase):
    id: int
    person_id: int

    class Config:
        from_attributes = True


class WorkExperienceUpdate(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    organization: Optional[str] = None
    position: Optional[str] = None


# Generic item schema with confidence and review_status
class ReviewableBase(BaseModel):
    raw_text: str = ""
    confidence: float = 0.0
    review_status: str = "pending"


class PaperAuthorBase(BaseModel):
    name: str
    order: int = 0
    is_first_author: bool = False
    is_corresponding_author: bool = False


class PaperAuthorOut(PaperAuthorBase):
    id: int

    class Config:
        from_attributes = True


class PaperBase(ReviewableBase):
    title: str = ""
    journal: str = ""
    year: str = ""
    doi: str = ""
    issue: str = ""
    volume: str = ""
    pages: str = ""
    is_first_author: bool = False
    is_corresponding_author: bool = False


class PaperCreate(PaperBase):
    person_id: int
    authors: List[PaperAuthorBase] = []


class PaperUpdate(BaseModel):
    title: Optional[str] = None
    journal: Optional[str] = None
    year: Optional[str] = None
    doi: Optional[str] = None
    issue: Optional[str] = None
    volume: Optional[str] = None
    pages: Optional[str] = None
    is_first_author: Optional[bool] = None
    is_corresponding_author: Optional[bool] = None
    raw_text: Optional[str] = None
    confidence: Optional[float] = None
    review_status: Optional[str] = None
    authors: Optional[List[PaperAuthorBase]] = None


class PaperOut(PaperBase):
    id: int
    person_id: int
    authors: List[PaperAuthorOut] = []

    class Config:
        from_attributes = True


class ProjectBase(ReviewableBase):
    project_type: str = ""
    name: str = ""
    project_number: str = ""
    start_date: str = ""
    end_date: str = ""
    role: str = ""
    amount: str = ""


class ProjectCreate(ProjectBase):
    person_id: int


class ProjectUpdate(BaseModel):
    project_type: Optional[str] = None
    name: Optional[str] = None
    project_number: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    role: Optional[str] = None
    amount: Optional[str] = None
    raw_text: Optional[str] = None
    confidence: Optional[float] = None
    review_status: Optional[str] = None


class ProjectOut(ProjectBase):
    id: int
    person_id: int

    class Config:
        from_attributes = True


class AwardBase(ReviewableBase):
    award_name: str = ""
    project_name: str = ""
    participants: str = ""
    awarding_body: str = ""


class AwardCreate(AwardBase):
    person_id: int


class AwardUpdate(BaseModel):
    award_name: Optional[str] = None
    project_name: Optional[str] = None
    participants: Optional[str] = None
    awarding_body: Optional[str] = None
    raw_text: Optional[str] = None
    confidence: Optional[float] = None
    review_status: Optional[str] = None


class AwardOut(AwardBase):
    id: int
    person_id: int

    class Config:
        from_attributes = True


class PatentApplicantBase(BaseModel):
    name: str
    order: int = 0


class PatentApplicantOut(PatentApplicantBase):
    id: int

    class Config:
        from_attributes = True


class PatentBase(ReviewableBase):
    patent_name: str = ""
    application_number: str = ""
    authorization_number: str = ""
    status: str = ""


class PatentCreate(PatentBase):
    person_id: int
    applicants: List[PatentApplicantBase] = []


class PatentUpdate(BaseModel):
    patent_name: Optional[str] = None
    application_number: Optional[str] = None
    authorization_number: Optional[str] = None
    status: Optional[str] = None
    raw_text: Optional[str] = None
    confidence: Optional[float] = None
    review_status: Optional[str] = None
    applicants: Optional[List[PatentApplicantBase]] = None


class PatentOut(PatentBase):
    id: int
    person_id: int
    applicants: List[PatentApplicantOut] = []

    class Config:
        from_attributes = True


class SoftwareCopyrightBase(ReviewableBase):
    applicant: str = ""
    name: str = ""
    registration_date: str = ""
    registration_number: str = ""


class SoftwareCopyrightCreate(SoftwareCopyrightBase):
    person_id: int


class SoftwareCopyrightUpdate(BaseModel):
    applicant: Optional[str] = None
    name: Optional[str] = None
    registration_date: Optional[str] = None
    registration_number: Optional[str] = None
    raw_text: Optional[str] = None
    confidence: Optional[float] = None
    review_status: Optional[str] = None


class SoftwareCopyrightOut(SoftwareCopyrightBase):
    id: int
    person_id: int

    class Config:
        from_attributes = True


class StudentAwardBase(ReviewableBase):
    award_name: str = ""
    level: str = ""
    role: str = ""
    award_date: str = ""


class StudentAwardCreate(StudentAwardBase):
    person_id: int


class StudentAwardUpdate(BaseModel):
    award_name: Optional[str] = None
    level: Optional[str] = None
    role: Optional[str] = None
    award_date: Optional[str] = None
    raw_text: Optional[str] = None
    confidence: Optional[float] = None
    review_status: Optional[str] = None


class StudentAwardOut(StudentAwardBase):
    id: int
    person_id: int

    class Config:
        from_attributes = True


class ConferenceBase(ReviewableBase):
    name: str = ""
    date: str = ""
    role: str = ""
    website: str = ""


class ConferenceCreate(ConferenceBase):
    person_id: int


class ConferenceUpdate(BaseModel):
    name: Optional[str] = None
    date: Optional[str] = None
    role: Optional[str] = None
    website: Optional[str] = None
    raw_text: Optional[str] = None
    confidence: Optional[float] = None
    review_status: Optional[str] = None


class ConferenceOut(ConferenceBase):
    id: int
    person_id: int

    class Config:
        from_attributes = True


class SpecialIssueBase(ReviewableBase):
    issue_name: str = ""
    journal_name: str = ""
    date: str = ""
    role: str = ""


class SpecialIssueCreate(SpecialIssueBase):
    person_id: int


class SpecialIssueUpdate(BaseModel):
    issue_name: Optional[str] = None
    journal_name: Optional[str] = None
    date: Optional[str] = None
    role: Optional[str] = None
    raw_text: Optional[str] = None
    confidence: Optional[float] = None
    review_status: Optional[str] = None


class SpecialIssueOut(SpecialIssueBase):
    id: int
    person_id: int

    class Config:
        from_attributes = True


class AcademicRoleBase(ReviewableBase):
    title: str = ""
    start_date: str = ""
    end_date: str = ""


class AcademicRoleCreate(AcademicRoleBase):
    person_id: int


class AcademicRoleUpdate(BaseModel):
    title: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    raw_text: Optional[str] = None
    confidence: Optional[float] = None
    review_status: Optional[str] = None


class AcademicRoleOut(AcademicRoleBase):
    id: int
    person_id: int

    class Config:
        from_attributes = True


class AcademicReportBase(ReviewableBase):
    name: str = ""
    report_type: str = ""
    date: str = ""


class AcademicReportCreate(AcademicReportBase):
    person_id: int


class AcademicReportUpdate(BaseModel):
    name: Optional[str] = None
    report_type: Optional[str] = None
    date: Optional[str] = None
    raw_text: Optional[str] = None
    confidence: Optional[float] = None
    review_status: Optional[str] = None


class AcademicReportOut(AcademicReportBase):
    id: int
    person_id: int

    class Config:
        from_attributes = True


class TeachingPlatformBase(ReviewableBase):
    name: str = ""
    issuing_body: str = ""
    approval_date: str = ""
    position: str = ""


class TeachingPlatformCreate(TeachingPlatformBase):
    person_id: int


class TeachingPlatformUpdate(BaseModel):
    name: Optional[str] = None
    issuing_body: Optional[str] = None
    approval_date: Optional[str] = None
    position: Optional[str] = None
    raw_text: Optional[str] = None
    confidence: Optional[float] = None
    review_status: Optional[str] = None


class TeachingPlatformOut(TeachingPlatformBase):
    id: int
    person_id: int

    class Config:
        from_attributes = True


class IndustryStandardBase(ReviewableBase):
    name: str = ""
    publish_date: str = ""
    role: str = ""


class IndustryStandardCreate(IndustryStandardBase):
    person_id: int


class IndustryStandardUpdate(BaseModel):
    name: Optional[str] = None
    publish_date: Optional[str] = None
    role: Optional[str] = None
    raw_text: Optional[str] = None
    confidence: Optional[float] = None
    review_status: Optional[str] = None


class IndustryStandardOut(IndustryStandardBase):
    id: int
    person_id: int

    class Config:
        from_attributes = True
