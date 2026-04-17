from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey("persons.id"), unique=True, nullable=False)
    introduction = Column(Text, default="")
    phone = Column(String(50), default="")
    email = Column(String(200), default="")
    address = Column(String(500), default="")

    person = relationship("Person", back_populates="profile")


class Education(Base):
    __tablename__ = "educations"

    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey("persons.id"), nullable=False)
    start_date = Column(String(50), default="")
    end_date = Column(String(50), default="")
    school = Column(String(200), default="")
    major = Column(String(200), default="")
    degree = Column(String(100), default="")

    person = relationship("Person", back_populates="educations")


class WorkExperience(Base):
    __tablename__ = "work_experiences"

    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey("persons.id"), nullable=False)
    start_date = Column(String(50), default="")
    end_date = Column(String(50), default="")
    organization = Column(String(300), default="")
    position = Column(String(200), default="")

    person = relationship("Person", back_populates="work_experiences")
