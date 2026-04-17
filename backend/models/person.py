from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base


class Person(Base):
    __tablename__ = "persons"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    name_en = Column(String(100), default="")
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    resumes = relationship("Resume", back_populates="person", cascade="all, delete-orphan")
    profile = relationship("Profile", back_populates="person", uselist=False, cascade="all, delete-orphan")
    educations = relationship("Education", back_populates="person", cascade="all, delete-orphan")
    work_experiences = relationship("WorkExperience", back_populates="person", cascade="all, delete-orphan")
    papers = relationship("Paper", back_populates="person", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="person", cascade="all, delete-orphan")
    awards = relationship("Award", back_populates="person", cascade="all, delete-orphan")
    patents = relationship("Patent", back_populates="person", cascade="all, delete-orphan")
    software_copyrights = relationship("SoftwareCopyright", back_populates="person", cascade="all, delete-orphan")
    student_awards = relationship("StudentAward", back_populates="person", cascade="all, delete-orphan")
    conferences = relationship("Conference", back_populates="person", cascade="all, delete-orphan")
    special_issues = relationship("SpecialIssue", back_populates="person", cascade="all, delete-orphan")
    academic_roles = relationship("AcademicRole", back_populates="person", cascade="all, delete-orphan")
    academic_reports = relationship("AcademicReport", back_populates="person", cascade="all, delete-orphan")
    teaching_platforms = relationship("TeachingPlatform", back_populates="person", cascade="all, delete-orphan")
    industry_standards = relationship("IndustryStandard", back_populates="person", cascade="all, delete-orphan")
