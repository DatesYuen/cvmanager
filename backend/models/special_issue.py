from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base


class SpecialIssue(Base):
    __tablename__ = "special_issues"

    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey("persons.id"), nullable=False)
    issue_name = Column(String(500), default="")
    journal_name = Column(String(300), default="")
    date = Column(String(50), default="")
    role = Column(String(100), default="")
    raw_text = Column(Text, default="")
    confidence = Column(Float, default=0.0)
    review_status = Column(String(20), default="pending")

    person = relationship("Person", back_populates="special_issues")
