from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base


class Patent(Base):
    __tablename__ = "patents"

    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey("persons.id"), nullable=False)
    patent_name = Column(String(500), default="")
    application_number = Column(String(100), default="")
    authorization_number = Column(String(100), default="")
    status = Column(String(50), default="")
    raw_text = Column(Text, default="")
    confidence = Column(Float, default=0.0)
    review_status = Column(String(20), default="pending")

    person = relationship("Person", back_populates="patents")
    applicants = relationship("PatentApplicant", back_populates="patent", cascade="all, delete-orphan",
                              order_by="PatentApplicant.order")


class PatentApplicant(Base):
    __tablename__ = "patent_applicants"

    id = Column(Integer, primary_key=True, index=True)
    patent_id = Column(Integer, ForeignKey("patents.id"), nullable=False)
    name = Column(String(100), nullable=False)
    order = Column(Integer, default=0)

    patent = relationship("Patent", back_populates="applicants")
