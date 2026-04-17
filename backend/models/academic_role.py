from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base


class AcademicRole(Base):
    __tablename__ = "academic_roles"

    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey("persons.id"), nullable=False)
    title = Column(String(500), default="")
    start_date = Column(String(50), default="")
    end_date = Column(String(50), default="")
    raw_text = Column(Text, default="")
    confidence = Column(Float, default=0.0)
    review_status = Column(String(20), default="pending")

    person = relationship("Person", back_populates="academic_roles")
