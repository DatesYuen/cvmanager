from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base


class Award(Base):
    __tablename__ = "awards"

    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey("persons.id"), nullable=False)
    award_name = Column(String(500), default="")
    project_name = Column(String(500), default="")
    participants = Column(Text, default="")
    awarding_body = Column(String(300), default="")
    raw_text = Column(Text, default="")
    confidence = Column(Float, default=0.0)
    review_status = Column(String(20), default="pending")

    person = relationship("Person", back_populates="awards")
