from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base


class TeachingPlatform(Base):
    __tablename__ = "teaching_platforms"

    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey("persons.id"), nullable=False)
    name = Column(String(500), default="")
    issuing_body = Column(String(300), default="")
    approval_date = Column(String(50), default="")
    position = Column(String(200), default="")
    raw_text = Column(Text, default="")
    confidence = Column(Float, default=0.0)
    review_status = Column(String(20), default="pending")

    person = relationship("Person", back_populates="teaching_platforms")
