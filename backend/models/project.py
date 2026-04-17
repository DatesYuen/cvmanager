from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey("persons.id"), nullable=False)
    project_type = Column(String(200), default="")
    name = Column(String(500), default="")
    project_number = Column(String(100), default="")
    start_date = Column(String(50), default="")
    end_date = Column(String(50), default="")
    role = Column(String(100), default="")
    amount = Column(String(50), default="")
    raw_text = Column(Text, default="")
    confidence = Column(Float, default=0.0)
    review_status = Column(String(20), default="pending")

    person = relationship("Person", back_populates="projects")
